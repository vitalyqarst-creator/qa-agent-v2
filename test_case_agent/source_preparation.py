from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowBaseline,
    SourceRowExtractionSpec,
    build_source_row_baseline,
    load_extraction_spec,
    resolve_xhtml_table_cells_at_locators,
)


SOURCE_PREPARATION_CACHE_VERSION = 3
SOURCE_EVIDENCE_PROFILE_VERSION = 1
PARITY_PROFILE_VERSION = 1
MOCKUP_INSPECTION_PROFILE_VERSION = 1
FIELD_TABLE_SEMANTICS_PROFILE_VERSION = 1
BASELINE_PLACEHOLDER = "__SOURCE_ROW_BASELINE_OUTPUT__"
FORBIDDEN_SEMANTIC_INPUT_PARTS = (
    "/test-cases/",
    "/work/stage-handoffs/",
    "/work/review-cycles/",
)
REQUIREMENT_CODE_RE = re.compile(
    r"\b(?P<prefix>BSR|GSR|DIT|REQ)\s+(?P<number>\d+(?:\.\d+)*)\b",
    flags=re.IGNORECASE,
)
EXPECTED_SOURCE_ROLES = {
    "main_ft_docx": "main-ft-docx",
    "main_ft_xhtml": "main-ft-xhtml",
    "main_ft_pdf": "main-ft-pdf",
    "package_notes": "mandatory-package-context",
}
SOURCE_ROLE_MANIFEST_BINDING_COMPATIBILITY = {
    "approved-clarification": frozenset({"approved-clarification", "not-used"}),
    "main-ft-xhtml": frozenset({"assertion-source"}),
    "main-ft-docx": frozenset({"semantic-source-of-truth"}),
    "main-ft-pdf": frozenset({"structural-visual-parity", "not-used"}),
    "support": frozenset({"supporting-material", "not-used"}),
    "mandatory-package-context": frozenset({"supporting-material", "not-used"}),
    "external-vendor-reference": frozenset({"supporting-material", "not-used"}),
    "mockup": frozenset({"mockup", "not-used"}),
}


class SourcePreparationError(ValueError):
    pass


@dataclass(frozen=True)
class SourcePreparationResult:
    cache_key: str
    cache_hit: bool
    input_file_count: int
    input_bytes: int
    candidate_count: int
    component_digests: Mapping[str, str]
    duration_ms: int
    output_context: Path
    output_baseline: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "reused" if self.cache_hit else "built",
            "cache_key": self.cache_key,
            "cache_hit": self.cache_hit,
            "input_file_count": self.input_file_count,
            "input_bytes": self.input_bytes,
            "candidate_count": self.candidate_count,
            "component_digests": dict(self.component_digests),
            "duration_ms": self.duration_ms,
            "output_context": str(self.output_context),
            "output_baseline": str(self.output_baseline),
        }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _under(root: Path, value: str | Path, *, label: str) -> Path:
    path = (Path(value) if Path(value).is_absolute() else root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SourcePreparationError(f"{label} escapes repository root: {path}") from exc
    return path


def _repo_relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _ensure_nonsemantic_input(relative: str, *, label: str) -> None:
    normalized = "/" + relative.replace("\\", "/").strip("/").casefold() + "/"
    if any(part.casefold() in normalized for part in FORBIDDEN_SEMANTIC_INPUT_PARTS):
        raise SourcePreparationError(
            f"{label} cannot use prior TC/handoff/review-cycle evidence: {relative}"
        )


def _read_json(path: Path, *, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourcePreparationError(f"cannot read {label} {path}: {exc}") from exc


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = _read_json(path, label=label)
    if not isinstance(payload, dict):
        raise SourcePreparationError(f"{label} must be a JSON object: {path}")
    return payload


def _exact_fields(
    payload: Mapping[str, Any],
    *,
    required: set[str],
    label: str,
) -> None:
    missing = sorted(required - set(payload))
    unknown = sorted(set(payload) - required)
    if missing or unknown:
        raise SourcePreparationError(
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}"
        )


def _validated_role_manifest_binding(
    item: Mapping[str, Any],
    *,
    label: str,
) -> tuple[str, str]:
    role = item.get("role")
    binding = item.get("manifest_binding")
    if not isinstance(role, str) or not role.strip():
        raise SourcePreparationError(f"{label}.role is required")
    if role != role.strip():
        raise SourcePreparationError(f"{label}.role must not contain surrounding whitespace")
    if not isinstance(binding, str) or not binding.strip():
        raise SourcePreparationError(f"{label}.manifest_binding is required")
    if binding != binding.strip():
        raise SourcePreparationError(
            f"{label}.manifest_binding must not contain surrounding whitespace"
        )
    allowed = SOURCE_ROLE_MANIFEST_BINDING_COMPATIBILITY.get(role)
    if allowed is None:
        if binding != "not-used":
            raise SourcePreparationError(
                f"{label} unknown role requires manifest_binding=not-used: {role}"
            )
    elif binding not in allowed:
        raise SourcePreparationError(
            f"{label} role/manifest_binding mismatch: {role} cannot use {binding}"
        )
    return role, binding


def _source_registry(context: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_sources = context.get("sources")
    if not isinstance(raw_sources, list):
        raise SourcePreparationError("context.sources must be an array")
    sources: list[dict[str, Any]] = []
    source_paths: list[str] = []
    for index, item in enumerate(raw_sources):
        if not isinstance(item, Mapping):
            raise SourcePreparationError(f"context.sources[{index}] must be an object")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            raise SourcePreparationError(f"context.sources[{index}].path is required")
        _validated_role_manifest_binding(item, label=f"context.sources[{index}]")
        sources.append(dict(item))
        source_paths.append(path.strip())
    if len(source_paths) != len(set(source_paths)):
        raise SourcePreparationError("context.sources paths must be unique")
    for key in ("main_ft_docx", "main_ft_xhtml"):
        if not isinstance(context.get(key), str) or not str(context[key]).strip():
            raise SourcePreparationError(f"context.{key} is required")
    for key, expected_role in EXPECTED_SOURCE_ROLES.items():
        value = context.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise SourcePreparationError(f"context.{key} must be a non-empty path")
        matches = [
            item
            for item in sources
            if item.get("path") == value and item.get("role") == expected_role
        ]
        if len(matches) != 1:
            raise SourcePreparationError(
                f"context.{key} must have exactly one sources entry with role {expected_role}"
            )
    return tuple(sources)


def _mockup_registry(context: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_mockups = context.get("mockups", [])
    if not isinstance(raw_mockups, list):
        raise SourcePreparationError("context.mockups must be an array")
    mockups: list[dict[str, Any]] = []
    paths: list[str] = []
    for index, item in enumerate(raw_mockups):
        if not isinstance(item, Mapping):
            raise SourcePreparationError(f"context.mockups[{index}] must be an object")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            raise SourcePreparationError(f"context.mockups[{index}].path is required")
        role, _binding = _validated_role_manifest_binding(
            item,
            label=f"context.mockups[{index}]",
        )
        if role != "mockup":
            raise SourcePreparationError(f"context.mockups[{index}].role must equal mockup")
        paths.append(path.strip())
        mockups.append(dict(item))
    if len(paths) != len(set(paths)):
        raise SourcePreparationError("context.mockups paths must be unique")
    return tuple(mockups)


def _registered_inputs(context: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    sources = _source_registry(context)
    mockups = _mockup_registry(context)
    extraction_spec = context.get("source_row_extraction_spec")
    if not isinstance(extraction_spec, str) or not extraction_spec.strip():
        raise SourcePreparationError("context.source_row_extraction_spec is required")
    values: list[tuple[str, str]] = [
        (extraction_spec.strip(), "source-row-extraction-spec")
    ]
    values.extend((str(item["path"]), str(item["role"])) for item in sources)
    values.extend((str(item["path"]), "mockup") for item in mockups)
    bounded = context.get("bounded_evidence")
    if bounded is not None and not isinstance(bounded, Mapping):
        raise SourcePreparationError("context.bounded_evidence must be an object")
    if isinstance(bounded, Mapping):
        for name, value in sorted(bounded.items(), key=lambda item: str(item[0])):
            if not isinstance(name, str) or not isinstance(value, str) or not value.strip():
                raise SourcePreparationError(
                    "context.bounded_evidence entries must map names to paths"
                )
            values.append((value.strip(), f"bounded-evidence-{name}"))
    paths = [path for path, _ in values]
    if len(paths) != len(set(paths)):
        raise SourcePreparationError("registered input paths must be unique")
    return tuple(values)


def _fingerprint_inputs(
    root: Path,
    context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    fingerprints: list[dict[str, Any]] = []
    for relative, role in _registered_inputs(context):
        _ensure_nonsemantic_input(relative, label="registered input")
        path = _under(root, relative, label="registered input")
        if not path.is_file():
            raise SourcePreparationError(f"registered input is missing: {relative}")
        fingerprints.append(
            {
                "path": _repo_relative(root, path),
                "role": role,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    fingerprints.sort(key=lambda item: (item["path"], item["role"]))
    return tuple(fingerprints)


def _validate_selected_xhtml(
    *,
    context: Mapping[str, Any],
    spec: SourceRowExtractionSpec,
    fingerprints: Sequence[Mapping[str, Any]],
) -> None:
    selected_path = context.get("main_ft_xhtml")
    if selected_path != spec.selected_xhtml.relative_path:
        raise SourcePreparationError(
            "context.main_ft_xhtml must match extraction spec.selected_xhtml.relative_path"
        )
    matches = [item for item in fingerprints if item.get("path") == selected_path]
    if len(matches) != 1 or matches[0].get("role") != "main-ft-xhtml":
        raise SourcePreparationError("selected XHTML fingerprint is missing or has the wrong role")
    if matches[0].get("sha256") != spec.selected_xhtml.sha256:
        raise SourcePreparationError("selected XHTML hash does not match extraction spec")


def _key_template(context: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(context))
    payload.pop("source_cache", None)
    payload.pop("source_row_baseline", None)
    return payload


def _context_for_digest(context: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(context))
    payload.pop("source_cache", None)
    payload.pop("source_row_baseline", None)
    return payload


def _cache_key(
    *,
    context: Mapping[str, Any],
    fingerprints: Sequence[Mapping[str, Any]],
) -> str:
    return _canonical_sha256(
        {
            "contract": "source-preparation-v3",
            "builder_version": SOURCE_PREPARATION_CACHE_VERSION,
            "source_evidence_profile_version": SOURCE_EVIDENCE_PROFILE_VERSION,
            "parity_profile_version": PARITY_PROFILE_VERSION,
            "mockup_inspection_profile_version": MOCKUP_INSPECTION_PROFILE_VERSION,
            "field_table_semantics_profile_version": (
                FIELD_TABLE_SEMANTICS_PROFILE_VERSION
            ),
            "template": _key_template(context),
            "inputs": list(fingerprints),
        }
    )


def _extract_requirement_codes(value: str) -> list[str]:
    return list(
        dict.fromkeys(
            f"{match.group('prefix').upper()} {match.group('number')}"
            for match in REQUIREMENT_CODE_RE.finditer(value)
        )
    )


def _parity_codes_by_locator(context: Mapping[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    parity = context.get("parity", [])
    if not isinstance(parity, list):
        raise SourcePreparationError("context.parity must be an array")
    for index, item in enumerate(parity):
        if not isinstance(item, Mapping):
            raise SourcePreparationError(f"context.parity[{index}] must be an object")
        locator = item.get("xhtml_locator")
        code = item.get("requirement_code")
        if not isinstance(locator, str) or not locator.strip():
            raise SourcePreparationError(f"context.parity[{index}].xhtml_locator is required")
        if not isinstance(code, str) or not code.strip():
            raise SourcePreparationError(f"context.parity[{index}].requirement_code is required")
        result.setdefault(locator.strip(), []).append(code.strip())
    return {key: list(dict.fromkeys(values)) for key, values in result.items()}


def _refresh_source_rows(
    *,
    repo_root: Path,
    context: Mapping[str, Any],
    baseline: SourceRowBaseline,
) -> dict[str, Any]:
    result = copy.deepcopy(dict(context))
    rows = result.get("source_rows")
    if not isinstance(rows, list) or not rows:
        raise SourcePreparationError("context.source_rows must be a non-empty array")
    candidates = {item.canonical_xpath: item for item in baseline.candidates}
    parity_codes = _parity_codes_by_locator(context)
    orphan_parity_locators = sorted(set(parity_codes) - set(candidates))
    if orphan_parity_locators:
        raise SourcePreparationError(
            "parity entries reference locators outside the current baseline: "
            + ", ".join(orphan_parity_locators)
        )
    mapped: set[str] = set()
    row_ids: set[str] = set()
    refreshed: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        if not isinstance(item, Mapping):
            raise SourcePreparationError(f"context.source_rows[{index}] must be an object")
        row = copy.deepcopy(dict(item))
        row_id = row.get("source_row_id")
        if not isinstance(row_id, str) or not row_id.strip():
            raise SourcePreparationError(f"context.source_rows[{index}].source_row_id is required")
        if row_id in row_ids:
            raise SourcePreparationError(f"duplicate source_row_id: {row_id}")
        row_ids.add(row_id)
        locator = row.get("source_locator")
        if not isinstance(locator, str) or not locator.strip():
            raise SourcePreparationError(f"context.source_rows[{index}].source_locator is required")
        locator = locator.strip()
        candidate = candidates.get(locator)
        if candidate is None:
            raise SourcePreparationError(
                f"source row locator is not present in current baseline: {locator}"
            )
        if locator in mapped:
            raise SourcePreparationError(f"duplicate source row locator: {locator}")
        mapped.add(locator)
        expected_values = {
            "source_path": baseline.selected_xhtml.relative_path,
            "bounded_source_text": candidate.bounded_source_text,
            "source_context_class": candidate.source_context_class,
            "candidate_id": candidate.candidate_id,
        }
        for key, expected in expected_values.items():
            if key in row and row[key] != expected:
                raise SourcePreparationError(f"{row_id} has stale {key}")
            row[key] = expected
        literal_codes = _extract_requirement_codes(candidate.bounded_source_text)
        current_codes = list(
            dict.fromkeys([*literal_codes, *parity_codes.get(locator, [])])
        )
        prior_codes = row.get("requirement_codes_hint")
        if prior_codes is not None:
            if not isinstance(prior_codes, list) or prior_codes != current_codes:
                raise SourcePreparationError(
                    f"{row_id} requirement_codes_hint does not match XHTML/parity bindings"
                )
        source_ref_codes = set(_extract_requirement_codes(str(row.get("source_ref", ""))))
        if source_ref_codes - set(current_codes):
            raise SourcePreparationError(f"source_ref codes are stale for {row_id}")
        row["requirement_codes_hint"] = current_codes
        refreshed.append(row)
    missing = sorted(set(candidates) - mapped)
    if missing:
        raise SourcePreparationError(
            "context source rows do not cover current baseline candidates: " + ", ".join(missing)
        )
    result["source_rows"] = _attach_field_table_semantics(
        repo_root=repo_root,
        context=result,
        baseline=baseline,
        rows=refreshed,
    )
    result["source_row_baseline"] = BASELINE_PLACEHOLDER
    return result


def _nonempty_contract_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourcePreparationError(f"{label} must be non-empty text")
    return value.strip()


def _attach_field_table_semantics(
    *,
    repo_root: Path,
    context: Mapping[str, Any],
    baseline: SourceRowBaseline,
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Attach package-declared field properties to exact physical XHTML cells."""

    declarations = context.get("source_table_column_semantics", [])
    if not isinstance(declarations, list):
        raise SourcePreparationError(
            "context.source_table_column_semantics must be an array"
        )
    refreshed = [copy.deepcopy(dict(row)) for row in rows]
    if not declarations:
        return refreshed

    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in refreshed
    }
    sources_by_path = {
        str(item.get("path")): item
        for item in context.get("sources", [])
        if isinstance(item, Mapping)
    }
    xhtml_path = _under(
        repo_root,
        baseline.selected_xhtml.relative_path,
        label="selected XHTML for field table semantics",
    )
    resolved_rows = resolve_xhtml_table_cells_at_locators(
        xhtml_path=xhtml_path,
        canonical_xpaths=tuple(
            dict.fromkeys(
                str(rows_by_id[row_id]["source_locator"])
                for declaration_index, declaration in enumerate(declarations)
                if isinstance(declaration, Mapping)
                for row_id in (
                    [str(declaration.get("header_source_row_id", ""))]
                    + [
                        str(item)
                        for item in declaration.get("target_source_row_ids", [])
                    ]
                )
                if row_id in rows_by_id
            )
        ),
    )
    allowed_values = {
        "requiredness": {"required", "optional"},
        "editability": {"editable", "read-only"},
    }
    seen_tables: set[str] = set()
    claimed_properties: set[tuple[str, str]] = set()
    source_text_cache: dict[str, str] = {}
    for declaration_index, declaration in enumerate(declarations):
        label = f"source_table_column_semantics[{declaration_index}]"
        if not isinstance(declaration, Mapping):
            raise SourcePreparationError(f"{label} must be an object")
        _exact_fields(
            declaration,
            required={
                "table_id",
                "header_source_row_id",
                "target_source_row_ids",
                "columns",
            },
            label=label,
        )
        table_id = _nonempty_contract_text(
            declaration.get("table_id"), label=f"{label}.table_id"
        )
        if table_id in seen_tables:
            raise SourcePreparationError(f"duplicate table semantics id: {table_id}")
        seen_tables.add(table_id)
        header_row_id = _nonempty_contract_text(
            declaration.get("header_source_row_id"),
            label=f"{label}.header_source_row_id",
        )
        target_row_ids = declaration.get("target_source_row_ids")
        if (
            not isinstance(target_row_ids, list)
            or not target_row_ids
            or any(not isinstance(item, str) or not item.strip() for item in target_row_ids)
            or len(target_row_ids) != len(set(target_row_ids))
        ):
            raise SourcePreparationError(
                f"{label}.target_source_row_ids must be non-empty and unique"
            )
        target_row_ids = [str(item) for item in target_row_ids]
        if header_row_id in target_row_ids:
            raise SourcePreparationError(f"{label} header cannot be a target row")
        unknown_rows = sorted(
            {header_row_id, *target_row_ids} - set(rows_by_id)
        )
        if unknown_rows:
            raise SourcePreparationError(
                f"{label} references unknown source rows: {unknown_rows}"
            )
        header_locator = str(rows_by_id[header_row_id]["source_locator"])
        header_cells = resolved_rows.get(header_locator)
        if header_cells is None:
            raise SourcePreparationError(f"{label} header row is not a resolved table row")
        columns = declaration.get("columns")
        if not isinstance(columns, list) or not columns:
            raise SourcePreparationError(f"{label}.columns must be a non-empty array")
        for row_id in target_row_ids:
            row = rows_by_id[row_id]
            if "physical_table_cells" in row:
                raise SourcePreparationError(
                    f"{row_id} contains stale derived physical_table_cells"
                )
            cells = resolved_rows[str(row["source_locator"])]
            row["physical_table_cells"] = [
                {
                    "physical_column_index": cell.physical_column_index,
                    "source_cell_locator": cell.canonical_xpath,
                    "element_kind": cell.element_kind,
                    "bounded_source_text": cell.bounded_source_text,
                }
                for cell in cells
            ]
        seen_column_properties: set[str] = set()
        seen_column_indices: set[int] = set()
        for column_index, column in enumerate(columns):
            column_label = f"{label}.columns[{column_index}]"
            if not isinstance(column, Mapping):
                raise SourcePreparationError(f"{column_label} must be an object")
            _exact_fields(
                column,
                required={
                    "property",
                    "physical_column_index",
                    "expected_header",
                    "value_mapping",
                    "interpretation_source",
                    "interpretation_source_fragment",
                },
                label=column_label,
            )
            property_name = _nonempty_contract_text(
                column.get("property"), label=f"{column_label}.property"
            )
            if property_name not in allowed_values:
                raise SourcePreparationError(
                    f"{column_label}.property is unsupported: {property_name}"
                )
            physical_index = column.get("physical_column_index")
            if not isinstance(physical_index, int) or isinstance(physical_index, bool) or physical_index < 1:
                raise SourcePreparationError(
                    f"{column_label}.physical_column_index must be a positive integer"
                )
            if property_name in seen_column_properties or physical_index in seen_column_indices:
                raise SourcePreparationError(
                    f"{label}.columns properties and physical indices must be unique"
                )
            seen_column_properties.add(property_name)
            seen_column_indices.add(physical_index)
            if physical_index > len(header_cells):
                raise SourcePreparationError(
                    f"{column_label} exceeds the physical header cell count"
                )
            header_cell = header_cells[physical_index - 1]
            expected_header = _nonempty_contract_text(
                column.get("expected_header"),
                label=f"{column_label}.expected_header",
            )
            if header_cell.bounded_source_text != expected_header:
                raise SourcePreparationError(
                    f"{column_label} header mismatch: expected={expected_header!r}, "
                    f"actual={header_cell.bounded_source_text!r}"
                )
            mapping = column.get("value_mapping")
            if (
                not isinstance(mapping, Mapping)
                or not mapping
                or any(not isinstance(key, str) or not key.strip() for key in mapping)
                or any(value not in allowed_values[property_name] for value in mapping.values())
            ):
                raise SourcePreparationError(
                    f"{column_label}.value_mapping is invalid for {property_name}"
                )
            interpretation_source = _nonempty_contract_text(
                column.get("interpretation_source"),
                label=f"{column_label}.interpretation_source",
            )
            source_registration = sources_by_path.get(interpretation_source)
            if source_registration is None or source_registration.get("role") not in {
                "mandatory-package-context",
                "support",
            }:
                raise SourcePreparationError(
                    f"{column_label}.interpretation_source must be registered supporting material"
                )
            interpretation_fragment = _nonempty_contract_text(
                column.get("interpretation_source_fragment"),
                label=f"{column_label}.interpretation_source_fragment",
            )
            if interpretation_source not in source_text_cache:
                source_path = _under(
                    repo_root,
                    interpretation_source,
                    label=f"{column_label}.interpretation_source",
                )
                try:
                    source_text_cache[interpretation_source] = source_path.read_text(
                        encoding="utf-8"
                    )
                except (OSError, UnicodeError) as exc:
                    raise SourcePreparationError(
                        f"cannot read {column_label}.interpretation_source: {exc}"
                    ) from exc
            if interpretation_fragment not in source_text_cache[interpretation_source]:
                raise SourcePreparationError(
                    f"{column_label}.interpretation_source_fragment is stale"
                )
            for row_id in target_row_ids:
                row = rows_by_id[row_id]
                locator = str(row["source_locator"])
                cells = resolved_rows.get(locator)
                if cells is None or physical_index > len(cells):
                    raise SourcePreparationError(
                        f"{row_id} lacks physical column {physical_index} for {property_name}"
                    )
                key = (row_id, property_name)
                if key in claimed_properties:
                    raise SourcePreparationError(
                        f"duplicate field-property binding: {row_id}/{property_name}"
                    )
                claimed_properties.add(key)
                cell = cells[physical_index - 1]
                source_value = cell.bounded_source_text
                if source_value not in mapping:
                    raise SourcePreparationError(
                        f"{row_id} has unmapped {property_name} value {source_value!r}"
                    )
                field_properties = row.setdefault("field_properties", {})
                if not isinstance(field_properties, dict) or property_name in field_properties:
                    raise SourcePreparationError(
                        f"{row_id} contains stale derived field_properties"
                    )
                normalized_value = str(mapping[source_value])
                field_properties[property_name] = {
                    "property_id": (
                        f"FP-{row_id}-{property_name.upper()}-"
                        f"{normalized_value.upper()}"
                    ),
                    "table_id": table_id,
                    "physical_column_index": physical_index,
                    "normalized_value": normalized_value,
                    "source_value": source_value,
                    "source_cell_locator": cell.canonical_xpath,
                    "header_source_row_id": header_row_id,
                    "header_value": expected_header,
                    "header_cell_locator": header_cell.canonical_xpath,
                    "interpretation_source": interpretation_source,
                    "interpretation_source_fragment": interpretation_fragment,
                }
    return refreshed


def _inline_bounded_evidence(
    *,
    root: Path,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    bounded = context.get("bounded_evidence")
    if not isinstance(bounded, Mapping):
        return {}
    result: dict[str, Any] = {}
    registered_sources = {
        str(item.get("path"))
        for item in context.get("sources", [])
        if isinstance(item, Mapping)
    }
    for name, relative in sorted(bounded.items(), key=lambda item: str(item[0])):
        path = _under(root, str(relative), label=f"bounded evidence {name}")
        payload = _read_json_object(path, label=f"bounded evidence {name}")
        source_path = payload.get("source_path")
        source_sha256 = payload.get("source_sha256")
        fragments = payload.get("fragments")
        if not isinstance(source_path, str) or source_path not in registered_sources:
            raise SourcePreparationError(
                f"bounded evidence {name} must bind a registered source_path"
            )
        source_file = _under(root, source_path, label=f"bounded evidence {name} source")
        if source_sha256 != _sha256_file(source_file):
            raise SourcePreparationError(f"bounded evidence {name} source hash mismatch")
        if not isinstance(fragments, list) or not fragments:
            raise SourcePreparationError(
                f"bounded evidence {name}.fragments must be a non-empty array"
            )
        for index, fragment in enumerate(fragments):
            if not isinstance(fragment, Mapping):
                raise SourcePreparationError(
                    f"bounded evidence {name}.fragments[{index}] must be an object"
                )
            locator = fragment.get("source_locator")
            text = fragment.get("exact_source_text")
            digest = fragment.get("exact_source_text_sha256")
            if not isinstance(locator, str) or not locator.strip():
                raise SourcePreparationError(
                    f"bounded evidence {name}.fragments[{index}] needs source_locator"
                )
            if not isinstance(text, str) or not text.strip():
                raise SourcePreparationError(
                    f"bounded evidence {name}.fragments[{index}] needs exact_source_text"
                )
            if digest != _sha256_bytes(text.encode("utf-8")):
                raise SourcePreparationError(
                    f"bounded evidence {name}.fragments[{index}] text hash mismatch"
                )
        result[str(name)] = payload
    return result


def _fingerprints_for_roles(
    fingerprints: Sequence[Mapping[str, Any]],
    roles: set[str],
) -> list[dict[str, Any]]:
    return [dict(item) for item in fingerprints if str(item.get("role")) in roles]


def _component_digests(
    *,
    context: Mapping[str, Any],
    baseline: SourceRowBaseline,
    fingerprints: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    source_roles = set(EXPECTED_SOURCE_ROLES.values())
    source_roles.update(
        str(item.get("role"))
        for item in context.get("sources", [])
        if isinstance(item, Mapping)
    )
    main_ft_roles = {"main-ft-docx", "main-ft-xhtml", "main-ft-pdf"}
    bounded_roles = {
        str(item.get("role"))
        for item in fingerprints
        if str(item.get("role", "")).startswith("bounded-evidence-")
    }
    scope_digest = _canonical_sha256(_key_template(context))
    return {
        "source_selection_sha256": _canonical_sha256(
            {
                "profile_version": SOURCE_EVIDENCE_PROFILE_VERSION,
                "main_ft_docx": context.get("main_ft_docx"),
                "main_ft_xhtml": context.get("main_ft_xhtml"),
                "main_ft_pdf": context.get("main_ft_pdf"),
                "package_notes": context.get("package_notes"),
                "sources": context.get("sources", []),
                "inputs": _fingerprints_for_roles(fingerprints, source_roles),
            }
        ),
        "xhtml_baseline_sha256": baseline.digest,
        "parity_sha256": _canonical_sha256(
            {
                "profile_version": PARITY_PROFILE_VERSION,
                "parity": context.get("parity", []),
                "bounded_evidence_inline": context.get("bounded_evidence_inline", {}),
                "inputs": _fingerprints_for_roles(
                    fingerprints, main_ft_roles | bounded_roles
                ),
            }
        ),
        "mockup_inventory_sha256": _canonical_sha256(
            {
                "profile_version": MOCKUP_INSPECTION_PROFILE_VERSION,
                "scope_sha256": scope_digest,
                "mockups": context.get("mockups", []),
                "mockup_locators": context.get("mockup_locators", []),
                "inputs": _fingerprints_for_roles(
                    fingerprints, main_ft_roles | {"mockup"}
                ),
            }
        ),
        "bounded_context_sha256": _canonical_sha256(_context_for_digest(context)),
    }


def _write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _publish(path: Path, content: bytes, *, allow_overwrite: bool) -> None:
    if path.is_file():
        if path.read_bytes() == content:
            return
        if not allow_overwrite:
            raise SourcePreparationError(f"output exists with different content: {path}")
    _write_atomic(path, content)


def _assert_publishable(path: Path, content: bytes, *, allow_overwrite: bool) -> None:
    if path.exists() and not path.is_file():
        raise SourcePreparationError(f"output path is not a file: {path}")
    if path.is_file() and path.read_bytes() != content and not allow_overwrite:
        raise SourcePreparationError(f"output exists with different content: {path}")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _cache_entry(cache_root: Path, cache_key: str) -> Path:
    entry = (cache_root / cache_key).resolve()
    try:
        entry.relative_to(cache_root.resolve())
    except ValueError as exc:
        raise SourcePreparationError("cache entry resolves outside cache root") from exc
    return entry


def _load_cache_entry(
    *,
    entry: Path,
    cache_key: str,
    spec: SourceRowExtractionSpec,
    fingerprints: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], SourceRowBaseline, dict[str, Any]] | None:
    if not entry.exists():
        return None
    if not entry.is_dir():
        raise SourcePreparationError(f"cache entry is not a directory: {entry}")
    manifest_path = entry / "manifest.json"
    context_path = entry / "context.json"
    baseline_path = entry / "baseline.json"
    if not (manifest_path.is_file() and context_path.is_file() and baseline_path.is_file()):
        raise SourcePreparationError(f"cache entry is incomplete: {entry}")
    manifest = _read_json_object(manifest_path, label="source preparation cache manifest")
    _exact_fields(
        manifest,
        required={
            "version",
            "cache_key",
            "profiles",
            "inputs",
            "candidate_count",
            "component_digests",
            "artifacts",
        },
        label="source preparation cache manifest",
    )
    if manifest.get("version") != SOURCE_PREPARATION_CACHE_VERSION:
        raise SourcePreparationError("cache manifest version mismatch")
    if manifest.get("cache_key") != cache_key:
        raise SourcePreparationError("cache manifest key mismatch")
    expected_profiles = {
        "source_evidence": SOURCE_EVIDENCE_PROFILE_VERSION,
        "parity": PARITY_PROFILE_VERSION,
        "mockup_inspection": MOCKUP_INSPECTION_PROFILE_VERSION,
        "field_table_semantics": FIELD_TABLE_SEMANTICS_PROFILE_VERSION,
    }
    if manifest.get("profiles") != expected_profiles:
        raise SourcePreparationError("cache manifest profile versions mismatch")
    if manifest.get("inputs") != list(fingerprints):
        raise SourcePreparationError("cache manifest input fingerprints mismatch")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise SourcePreparationError("cache manifest artifacts must be an object")
    _exact_fields(artifacts, required={"context", "baseline"}, label="cache artifacts")
    for name, path in (("context", context_path), ("baseline", baseline_path)):
        artifact = artifacts.get(name)
        if not isinstance(artifact, Mapping):
            raise SourcePreparationError(f"cache artifact {name} must be an object")
        _exact_fields(
            artifact,
            required={"path", "sha256", "size_bytes"},
            label=f"cache artifact {name}",
        )
        if artifact.get("path") != path.name:
            raise SourcePreparationError(f"cache artifact {name} path mismatch")
        if artifact.get("sha256") != _sha256_file(path):
            raise SourcePreparationError(f"cache artifact {name} hash mismatch")
        if artifact.get("size_bytes") != path.stat().st_size:
            raise SourcePreparationError(f"cache artifact {name} size mismatch")
    cached_context = _read_json_object(context_path, label="cached bounded context")
    baseline_payload = _read_json_object(baseline_path, label="cached source row baseline")
    try:
        baseline = SourceRowBaseline.from_dict(baseline_payload)
    except ValueError as exc:
        raise SourcePreparationError(f"cached source row baseline is invalid: {exc}") from exc
    if baseline.selected_xhtml != spec.selected_xhtml:
        raise SourcePreparationError("cached baseline selected XHTML mismatch")
    if baseline.extraction_spec_sha256 != spec.digest:
        raise SourcePreparationError("cached baseline extraction spec mismatch")
    if manifest.get("candidate_count") != baseline.candidate_count:
        raise SourcePreparationError("cache manifest candidate count mismatch")
    components = _component_digests(
        context=cached_context,
        baseline=baseline,
        fingerprints=fingerprints,
    )
    if manifest.get("component_digests") != components:
        raise SourcePreparationError("cache component digests mismatch")
    source_cache = cached_context.get("source_cache")
    if not isinstance(source_cache, Mapping) or source_cache != {
        "version": SOURCE_PREPARATION_CACHE_VERSION,
        "cache_key": cache_key,
        "input_fingerprints": list(fingerprints),
        "component_digests": components,
    }:
        raise SourcePreparationError("cached context source_cache binding mismatch")
    if cached_context.get("source_row_baseline") != BASELINE_PLACEHOLDER:
        raise SourcePreparationError("cached context baseline placeholder mismatch")
    return cached_context, baseline, manifest


def _remove_temporary_cache_dir(path: Path, *, cache_root: Path, cache_key: str) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    if resolved.parent != cache_root.resolve() or not resolved.name.startswith(f".{cache_key}."):
        raise SourcePreparationError(f"refusing to remove unexpected cache temp path: {resolved}")
    shutil.rmtree(resolved)


def _publish_cache_entry(
    *,
    cache_root: Path,
    entry: Path,
    cache_key: str,
    context_bytes: bytes,
    baseline_bytes: bytes,
    manifest_bytes: bytes,
) -> None:
    temporary = Path(tempfile.mkdtemp(prefix=f".{cache_key}.", dir=cache_root))
    try:
        _write_atomic(temporary / "context.json", context_bytes)
        _write_atomic(temporary / "baseline.json", baseline_bytes)
        _write_atomic(temporary / "manifest.json", manifest_bytes)
        try:
            os.rename(temporary, entry)
        except OSError:
            if not entry.exists():
                raise
    finally:
        _remove_temporary_cache_dir(temporary, cache_root=cache_root, cache_key=cache_key)


def prepare_bounded_scope_context(
    *,
    repo_root: Path,
    context_template: Path,
    cache_dir: Path,
    output_context: Path,
    output_baseline: Path,
    allow_overwrite: bool = False,
) -> SourcePreparationResult:
    started = time.perf_counter_ns()
    root = repo_root.resolve()
    template_path = _under(root, context_template, label="context template")
    _ensure_nonsemantic_input(
        _repo_relative(root, template_path),
        label="context template",
    )
    cache_root = _under(root, cache_dir, label="cache dir")
    context_output = _under(root, output_context, label="context output")
    baseline_output = _under(root, output_baseline, label="baseline output")
    context = _read_json_object(template_path, label="bounded context template")
    extraction_value = context.get("source_row_extraction_spec")
    if not isinstance(extraction_value, str) or not extraction_value.strip():
        raise SourcePreparationError("context.source_row_extraction_spec is required")
    extraction_path = _under(root, extraction_value, label="source row extraction spec")
    try:
        spec = load_extraction_spec(extraction_path)
    except ValueError as exc:
        raise SourcePreparationError(f"source row extraction spec is invalid: {exc}") from exc
    fingerprints = _fingerprint_inputs(root, context)
    _validate_selected_xhtml(context=context, spec=spec, fingerprints=fingerprints)
    protected_inputs = {
        template_path,
        extraction_path,
        *(_under(root, item["path"], label="fingerprinted input") for item in fingerprints),
    }
    if context_output == baseline_output:
        raise SourcePreparationError("context and baseline outputs must be different files")
    for label, output in (
        ("context output", context_output),
        ("baseline output", baseline_output),
    ):
        if output in protected_inputs:
            raise SourcePreparationError(f"{label} aliases a protected source/input file")
        if _is_within(output, cache_root):
            raise SourcePreparationError(f"{label} must stay outside the cache directory")
    inline_evidence = _inline_bounded_evidence(root=root, context=context)
    declared_inline = context.get("bounded_evidence_inline")
    if declared_inline is not None and declared_inline != inline_evidence:
        raise SourcePreparationError(
            "context.bounded_evidence_inline must match registered bounded evidence files"
        )
    cache_key = _cache_key(context=context, fingerprints=fingerprints)
    cache_root.mkdir(parents=True, exist_ok=True)
    entry = _cache_entry(cache_root, cache_key)
    loaded = _load_cache_entry(
        entry=entry,
        cache_key=cache_key,
        spec=spec,
        fingerprints=fingerprints,
    )
    cache_hit = loaded is not None
    if loaded is None:
        try:
            baseline = build_source_row_baseline(repo_root=root, spec=spec)
        except ValueError as exc:
            raise SourcePreparationError(f"cannot build source row baseline: {exc}") from exc
        try:
            prepared = _refresh_source_rows(
                repo_root=root,
                context=context,
                baseline=baseline,
            )
        except ValueError as exc:
            if isinstance(exc, SourcePreparationError):
                raise
            raise SourcePreparationError(
                f"cannot bind field table semantics: {exc}"
            ) from exc
        if inline_evidence:
            prepared["bounded_evidence_inline"] = inline_evidence
        components = _component_digests(
            context=prepared,
            baseline=baseline,
            fingerprints=fingerprints,
        )
        prepared["source_cache"] = {
            "version": SOURCE_PREPARATION_CACHE_VERSION,
            "cache_key": cache_key,
            "input_fingerprints": list(fingerprints),
            "component_digests": components,
        }
        context_bytes = json.dumps(
            prepared, ensure_ascii=False, indent=2
        ).encode("utf-8") + b"\n"
        baseline_bytes = json.dumps(
            baseline.to_dict(), ensure_ascii=False, indent=2
        ).encode("utf-8") + b"\n"
        manifest = {
            "version": SOURCE_PREPARATION_CACHE_VERSION,
            "cache_key": cache_key,
            "profiles": {
                "source_evidence": SOURCE_EVIDENCE_PROFILE_VERSION,
                "parity": PARITY_PROFILE_VERSION,
                "mockup_inspection": MOCKUP_INSPECTION_PROFILE_VERSION,
                "field_table_semantics": FIELD_TABLE_SEMANTICS_PROFILE_VERSION,
            },
            "inputs": list(fingerprints),
            "candidate_count": baseline.candidate_count,
            "component_digests": components,
            "artifacts": {
                "context": {
                    "path": "context.json",
                    "sha256": _sha256_bytes(context_bytes),
                    "size_bytes": len(context_bytes),
                },
                "baseline": {
                    "path": "baseline.json",
                    "sha256": _sha256_bytes(baseline_bytes),
                    "size_bytes": len(baseline_bytes),
                },
            },
        }
        _publish_cache_entry(
            cache_root=cache_root,
            entry=entry,
            cache_key=cache_key,
            context_bytes=context_bytes,
            baseline_bytes=baseline_bytes,
            manifest_bytes=json.dumps(
                manifest, ensure_ascii=False, indent=2
            ).encode("utf-8") + b"\n",
        )
        loaded = _load_cache_entry(
            entry=entry,
            cache_key=cache_key,
            spec=spec,
            fingerprints=fingerprints,
        )
        if loaded is None:
            raise SourcePreparationError("cache entry was not published")
    cached_context, baseline, manifest = loaded
    materialized_context = copy.deepcopy(cached_context)
    materialized_context["source_row_baseline"] = _repo_relative(root, baseline_output)
    context_bytes = json.dumps(
        materialized_context, ensure_ascii=False, indent=2
    ).encode("utf-8") + b"\n"
    baseline_bytes = (entry / "baseline.json").read_bytes()
    _assert_publishable(context_output, context_bytes, allow_overwrite=allow_overwrite)
    _assert_publishable(baseline_output, baseline_bytes, allow_overwrite=allow_overwrite)
    # Publish the referent first so a crash cannot leave a new context pointing
    # at an older baseline. Both targets were checked before either write.
    _publish(baseline_output, baseline_bytes, allow_overwrite=allow_overwrite)
    _publish(context_output, context_bytes, allow_overwrite=allow_overwrite)
    return SourcePreparationResult(
        cache_key=cache_key,
        cache_hit=cache_hit,
        input_file_count=len(fingerprints),
        input_bytes=sum(int(item["size_bytes"]) for item in fingerprints),
        candidate_count=baseline.candidate_count,
        component_digests=dict(manifest["component_digests"]),
        duration_ms=(time.perf_counter_ns() - started) // 1_000_000,
        output_context=context_output,
        output_baseline=baseline_output,
    )


__all__ = [
    "FIELD_TABLE_SEMANTICS_PROFILE_VERSION",
    "SOURCE_PREPARATION_CACHE_VERSION",
    "SOURCE_ROLE_MANIFEST_BINDING_COMPATIBILITY",
    "SourcePreparationError",
    "SourcePreparationResult",
    "prepare_bounded_scope_context",
]
