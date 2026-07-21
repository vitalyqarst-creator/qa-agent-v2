from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR_TEXT = str(ROOT_DIR)
sys.path[:] = [entry for entry in sys.path if entry != ROOT_DIR_TEXT]
sys.path.insert(0, ROOT_DIR_TEXT)

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_SOURCE_SUFFIXES = {".docx", ".xhtml", ".pdf"}
PRIMARY_SOURCE_BINDINGS = {
    ".docx": ("main-ft-docx", "semantic-source-of-truth"),
    ".xhtml": ("main-ft-xhtml", "assertion-source"),
    ".pdf": ("main-ft-pdf", "structural-visual-parity"),
}
SCOPE_INPUT_BINDINGS = {
    "support": ("supporting-material", "support"),
    "approved-clarification": ("approved-clarification", "support"),
    "mandatory-package-context": ("supporting-material", "package-notes"),
    "external-vendor-reference": (
        "supporting-material",
        "work/vendor-references",
    ),
    "mockup": ("mockup", "mockups"),
}
DEPENDENCY_KINDS = {
    "field",
    "dictionary",
    "external-requirement",
    "integration",
    "other",
}
DEPENDENCY_RESOLUTIONS = {
    "declared",
    "approved-alias",
    "source-provided",
    "external-dynamic",
    "scope-excluded",
    "missing",
}
SCHEMA_V2_CONFIG_FIELDS = {
    "schema_version",
    "benchmark_id",
    "ft_root",
    "ft_slug",
    "scope_slug",
    "source_files",
    "scope_inputs",
    "expected_sha256",
    "source_preparation",
    "outputs",
    "observation_root",
    "recorder_entrypoint",
    "production_wrapper",
    "measurement_mode",
}
SCHEMA_V2_OPTIONAL_CONFIG_FIELDS = {"semantic_sharding"}
SEMANTIC_SHARDING_FIELDS = {
    "mode",
    "max_included_rows",
    "max_source_rows",
    "max_shards",
    "max_semantic_weight",
}
SOURCE_ONLY_FORBIDDEN_FIELDS = {
    "atomic_statement_inventory",
    "atomic_statements",
    "bounded_evidence_inline",
    "compiled_scope",
    "coverage_gaps",
    "coverage_matrix",
    "handoff_artifacts",
    "latest_artifacts",
    "previous_results",
    "prior_results",
    "review_cycle",
    "review_findings",
    "reviewer_findings",
    "reviewer_output",
    "scope_clarification_requests",
    "scope_contract",
    "scope_coverage_gaps",
    "scope_gap_review",
    "semantic_design",
    "semantic_design_plan",
    "source_cache",
    "source_row_baseline",
    "test_design_plan",
    "workflow_state",
    "writer_findings",
    "writer_output",
}
SOURCE_ONLY_FORBIDDEN_PATH_MARKERS = (
    "work/stage-handoffs/",
    "work/review-cycles/",
    "work/full-process-observation/",
    "test-cases/",
)
SOURCE_ONLY_REQUIRED_TOP_LEVEL_FIELDS = {
    "canonical_test_cases",
    "dependency_aliases",
    "dependency_gap_gate",
    "ft_slug",
    "main_ft_docx",
    "main_ft_pdf",
    "main_ft_xhtml",
    "mockup_locators",
    "mockups",
    "package_id",
    "parity",
    "request_summary",
    "scope_boundary",
    "scope_execution_facts",
    "scope_slug",
    "section_id",
    "source_row_extraction_spec",
    "source_rows",
    "sources",
    "version",
}
SOURCE_ONLY_OPTIONAL_TOP_LEVEL_FIELDS = {
    "approved_clarifications",
    "bounded_evidence",
    "dependency_alias_provenance",
    "dictionary_inventory",
    "external_dictionary_bindings",
    "expected_dependencies",
    "package_notes",
    "source_table_column_semantics",
}
SOURCE_ENTRY_FIELDS = {
    "path",
    "role",
    "manifest_binding",
    "selection_reason",
    "version_or_date",
    "notes",
}
MOCKUP_ENTRY_FIELDS = SOURCE_ENTRY_FIELDS | {"screen_name"}
SOURCE_ROW_REQUIRED_FIELDS = {
    "source_row_id",
    "field_or_action",
    "source_ref",
    "source_locator",
    "in_scope_hint",
}
SOURCE_ROW_OPTIONAL_FIELDS = {
    "bounded_source_text",
    "candidate_id",
    "context_relation_required",
    "requirement_codes_hint",
    "source_context_class",
    "source_path",
}


class BootstrapError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScopeInput:
    path: Path
    role: str
    manifest_binding: str


@dataclass(frozen=True)
class BootstrapPlan:
    schema_version: int
    repo_root: Path
    config_path: Path
    config_sha256: str
    benchmark_id: str
    ft_root: Path
    ft_slug: str
    scope_slug: str
    source_files: tuple[Path, ...]
    scope_inputs: tuple[ScopeInput, ...]
    expected_sha256: tuple[tuple[Path, str], ...]
    observation_root: Path
    run_dir: Path
    timer: Path
    receipt: Path
    recorder_entrypoint: Path
    production_wrapper: Path
    context_template: Path | None
    source_preparation_cache: Path | None
    prepared_context: Path | None
    source_row_baseline: Path | None
    source_preparation_summary: Path | None
    runtime_dir: Path
    handoff_dir: Path | None
    cycle_dir: Path | None
    final_artifact: Path | None
    execution_summary: Path
    request_started_epoch_ms: int
    codex_turn_id: str
    request_start_source: str
    semantic_sharding_mode: str = "auto"
    semantic_shard_max_included_rows: int = 10
    semantic_shard_max_source_rows: int = 16
    semantic_shard_max_shards: int = 10
    semantic_shard_max_weight: int = 24
    routing_preflight_breakdown: tuple[dict[str, Any], ...] = ()


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _write_text_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _resolve_under(base: Path, candidate: Path, *, label: str) -> Path:
    resolved_base = base.resolve()
    resolved = (candidate if candidate.is_absolute() else resolved_base / candidate).resolve()
    try:
        resolved.relative_to(resolved_base)
    except ValueError as exc:
        raise BootstrapError(f"{label} escapes {resolved_base}: {resolved}") from exc
    return resolved


def _required_string(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BootstrapError(f"config field {field!r} must be a non-empty string")
    return value.strip()


def _safe_id(value: str, *, label: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise BootstrapError(f"{label} contains unsupported path characters: {value!r}")
    return value


def _load_config(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read bootstrap config {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BootstrapError("bootstrap config must be a JSON object")
    if payload.get("schema_version") not in {1, 2}:
        raise BootstrapError("bootstrap config schema_version must be 1 or 2")
    if payload.get("measurement_mode") != "observational":
        raise BootstrapError("bootstrap config measurement_mode must be observational")
    return payload, hashlib.sha256(raw).hexdigest()


def _required_object(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise BootstrapError(f"config field {field!r} must be an object")
    return value


def _exact_fields(
    payload: Mapping[str, Any], *, required: set[str], label: str
) -> None:
    missing = sorted(required - set(payload))
    unknown = sorted(set(payload) - required)
    if missing or unknown:
        raise BootstrapError(
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}"
        )


def _allowed_fields(
    payload: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    label: str,
) -> None:
    missing = sorted(required - set(payload))
    unknown = sorted(set(payload) - required - optional)
    if missing or unknown:
        raise BootstrapError(
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_sha256_inventory(
    payload: Mapping[str, Any],
    *,
    repo_root: Path,
    expected_paths: Sequence[Path],
) -> tuple[tuple[Path, str], ...]:
    raw = payload.get("expected_sha256")
    if not isinstance(raw, Mapping):
        raise BootstrapError("config field 'expected_sha256' must be an object")
    expected = {_repo_relative(repo_root, path): path for path in expected_paths}
    actual: dict[str, str] = {}
    for path, digest in raw.items():
        if not isinstance(path, str) or not path.strip():
            raise BootstrapError("expected_sha256 keys must be non-empty strings")
        normalized = path.replace("\\", "/")
        if path != normalized or normalized.startswith(("/", "./", "../")):
            raise BootstrapError(
                "expected_sha256 keys must be canonical repo-relative POSIX paths"
            )
        if normalized in actual:
            raise BootstrapError(f"duplicate expected_sha256 path: {normalized}")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise BootstrapError(
                f"expected_sha256[{normalized!r}] must be a lowercase SHA-256 digest"
            )
        actual[normalized] = digest
    missing = sorted(set(expected) - set(actual))
    unknown = sorted(set(actual) - set(expected))
    if missing or unknown:
        raise BootstrapError(
            "expected_sha256 inventory mismatch: "
            f"missing={missing or 'none'}, unknown={unknown or 'none'}"
        )
    result: list[tuple[Path, str]] = []
    for relative in sorted(expected):
        path = expected[relative]
        digest = actual[relative]
        observed = _sha256(path)
        if observed != digest:
            raise BootstrapError(
                f"checked-in SHA-256 mismatch for {relative}: "
                f"expected={digest}, observed={observed}"
            )
        result.append((path, digest))
    return tuple(result)


def _scope_inputs(
    *, payload: Mapping[str, Any], ft_root: Path, exact_items: bool = False
) -> tuple[ScopeInput, ...]:
    raw_inputs = payload.get("scope_inputs", [])
    if not isinstance(raw_inputs, list):
        raise BootstrapError("config scope_inputs must be an array")
    result: list[ScopeInput] = []
    seen: set[Path] = set()
    for index, item in enumerate(raw_inputs):
        if not isinstance(item, Mapping):
            raise BootstrapError(f"scope_inputs[{index}] must be an object")
        if exact_items:
            _exact_fields(
                item,
                required={"path", "role", "manifest_binding"},
                label=f"scope_inputs[{index}]",
            )
        raw_path = item.get("path")
        role = item.get("role")
        binding = item.get("manifest_binding")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise BootstrapError(f"scope_inputs[{index}].path must be non-empty")
        if role not in SCOPE_INPUT_BINDINGS:
            raise BootstrapError(
                f"scope_inputs[{index}].role must be one of "
                f"{sorted(SCOPE_INPUT_BINDINGS)}"
            )
        expected_binding, location_kind = SCOPE_INPUT_BINDINGS[str(role)]
        if binding != expected_binding:
            raise BootstrapError(
                f"scope_inputs[{index}].manifest_binding must equal "
                f"{expected_binding!r} for role {role!r}"
            )
        path = _resolve_under(
            ft_root, Path(raw_path), label=f"scope_inputs[{index}].path"
        )
        if location_kind == "package-notes":
            expected = (ft_root / "AGENT-NOTES.md").resolve()
            if path != expected:
                raise BootstrapError(
                    f"mandatory package context must equal {expected}: {path}"
                )
        else:
            expected_root = (ft_root / location_kind).resolve()
            try:
                path.relative_to(expected_root)
            except ValueError as exc:
                raise BootstrapError(
                    f"scope input role {role!r} must stay under "
                    f"{expected_root}: {path}"
                ) from exc
        if not path.is_file():
            raise BootstrapError(f"configured scope input does not exist: {path}")
        if path in seen:
            raise BootstrapError(f"duplicate scope input path: {path}")
        seen.add(path)
        result.append(
            ScopeInput(
                path=path,
                role=str(role),
                manifest_binding=str(binding),
            )
        )
    return tuple(result)


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise BootstrapError(f"{label} must be a JSON object: {path}")
    return payload


def _repo_relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _registry_entries(
    payload: Mapping[str, Any], *, field: str, label: str
) -> dict[str, tuple[str, str]]:
    raw = payload.get(field)
    if not isinstance(raw, list):
        raise BootstrapError(f"{label}.{field} must be an array")
    result: dict[str, tuple[str, str]] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise BootstrapError(f"{label}.{field}[{index}] must be an object")
        path = item.get("path")
        role = item.get("role")
        binding = item.get("manifest_binding")
        if not all(isinstance(value, str) and value.strip() for value in (path, role, binding)):
            raise BootstrapError(
                f"{label}.{field}[{index}] requires path, role and manifest_binding"
            )
        normalized = str(path).replace("\\", "/")
        if normalized in result:
            raise BootstrapError(f"duplicate {label}.{field} path: {normalized}")
        result[normalized] = (str(role), str(binding))
    return result


def _require_non_empty_string(value: Any, *, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise BootstrapError(f"{label} must be a non-empty string")


def _require_string_array(value: Any, *, label: str) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise BootstrapError(f"{label} must be an array of non-empty strings")


def _require_string_mapping(value: Any, *, label: str) -> None:
    if not isinstance(value, Mapping):
        raise BootstrapError(f"{label} must be an object")
    for key, item in value.items():
        _require_non_empty_string(key, label=f"{label} key")
        _require_non_empty_string(item, label=f"{label}[{key!r}]")


def _validate_source_only_schema(context: Mapping[str, Any]) -> None:
    _allowed_fields(
        context,
        required=SOURCE_ONLY_REQUIRED_TOP_LEVEL_FIELDS,
        optional=SOURCE_ONLY_OPTIONAL_TOP_LEVEL_FIELDS,
        label="bounded context template top-level",
    )
    if context.get("version") != 1:
        raise BootstrapError("bounded context template version must equal 1")
    for field in (
        "ft_slug",
        "scope_slug",
        "section_id",
        "package_id",
        "request_summary",
        "canonical_test_cases",
        "main_ft_docx",
        "main_ft_xhtml",
        "main_ft_pdf",
        "source_row_extraction_spec",
    ):
        _require_non_empty_string(
            context.get(field), label=f"bounded context template.{field}"
        )
    if "package_notes" in context:
        _require_non_empty_string(
            context["package_notes"],
            label="bounded context template.package_notes",
        )
    if type(context.get("dependency_gap_gate")) is not bool:
        raise BootstrapError(
            "bounded context template.dependency_gap_gate must be boolean"
        )

    for field, allowed in (
        ("sources", SOURCE_ENTRY_FIELDS),
        ("mockups", MOCKUP_ENTRY_FIELDS),
    ):
        items = context.get(field)
        if not isinstance(items, list):
            raise BootstrapError(f"bounded context template.{field} must be an array")
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                raise BootstrapError(
                    f"bounded context template.{field}[{index}] must be an object"
                )
            _allowed_fields(
                item,
                required={"path", "role", "manifest_binding"},
                optional=allowed - {"path", "role", "manifest_binding"},
                label=f"bounded context template.{field}[{index}]",
            )
            for key, value in item.items():
                _require_non_empty_string(
                    value,
                    label=f"bounded context template.{field}[{index}].{key}",
                )

    _require_string_array(
        context.get("mockup_locators"),
        label="bounded context template.mockup_locators",
    )
    boundary = context.get("scope_boundary")
    if not isinstance(boundary, Mapping):
        raise BootstrapError("bounded context template.scope_boundary must be an object")
    _exact_fields(
        boundary,
        required={"target", "include", "exclude"},
        label="bounded context template.scope_boundary",
    )
    _require_non_empty_string(
        boundary.get("target"), label="bounded context template.scope_boundary.target"
    )
    for field in ("include", "exclude"):
        _require_string_array(
            boundary.get(field),
            label=f"bounded context template.scope_boundary.{field}",
        )

    _require_string_mapping(
        context.get("dependency_aliases"),
        label="bounded context template.dependency_aliases",
    )
    if "dependency_alias_provenance" in context:
        _require_string_mapping(
            context["dependency_alias_provenance"],
            label="bounded context template.dependency_alias_provenance",
        )

    dictionaries = context.get("dictionary_inventory", [])
    if not isinstance(dictionaries, list):
        raise BootstrapError(
            "bounded context template.dictionary_inventory must be an array"
        )
    dictionary_fields = {
        "dictionary_id",
        "name",
        "source_path",
        "source_location",
        "values",
        "active_values",
        "archived_values",
        "entries",
    }
    for index, dictionary in enumerate(dictionaries):
        if not isinstance(dictionary, Mapping):
            raise BootstrapError(
                f"bounded context template.dictionary_inventory[{index}] must be an object"
            )
        _exact_fields(
            dictionary,
            required=dictionary_fields,
            label=f"bounded context template.dictionary_inventory[{index}]",
        )
        for field in ("dictionary_id", "name", "source_path", "source_location"):
            _require_non_empty_string(
                dictionary.get(field),
                label=f"bounded context template.dictionary_inventory[{index}].{field}",
            )
        for field in ("values", "active_values", "archived_values"):
            _require_string_array(
                dictionary.get(field),
                label=f"bounded context template.dictionary_inventory[{index}].{field}",
            )
        entries = dictionary.get("entries")
        if not isinstance(entries, list):
            raise BootstrapError(
                "bounded context template.dictionary_inventory"
                f"[{index}].entries must be an array"
            )
        for entry_index, entry in enumerate(entries):
            label = (
                "bounded context template.dictionary_inventory"
                f"[{index}].entries[{entry_index}]"
            )
            if not isinstance(entry, Mapping):
                raise BootstrapError(f"{label} must be an object")
            _exact_fields(
                entry,
                required={"value", "internal_code", "archived"},
                label=label,
            )
            _require_non_empty_string(entry.get("value"), label=f"{label}.value")
            _require_non_empty_string(
                entry.get("internal_code"), label=f"{label}.internal_code"
            )
            if type(entry.get("archived")) is not bool:
                raise BootstrapError(f"{label}.archived must be boolean")

    external_dictionaries = context.get("external_dictionary_bindings", [])
    if not isinstance(external_dictionaries, list):
        raise BootstrapError(
            "bounded context template.external_dictionary_bindings must be an array"
        )
    external_fields = {
        "dictionary_name",
        "binding_type",
        "provider",
        "reference_path",
        "reference_url",
        "source_row_ids",
        "query_parameters",
        "authority",
        "authority_ref",
    }
    for index, binding in enumerate(external_dictionaries):
        label = f"bounded context template.external_dictionary_bindings[{index}]"
        if not isinstance(binding, Mapping):
            raise BootstrapError(f"{label} must be an object")
        _exact_fields(binding, required=external_fields, label=label)
        for field in (
            "dictionary_name",
            "binding_type",
            "provider",
            "reference_path",
            "reference_url",
            "authority",
            "authority_ref",
        ):
            _require_non_empty_string(binding.get(field), label=f"{label}.{field}")
        if binding.get("binding_type") != "external-dynamic-dictionary":
            raise BootstrapError(
                f"{label}.binding_type must equal external-dynamic-dictionary"
            )
        if binding.get("authority") != "user-confirmed":
            raise BootstrapError(f"{label}.authority must equal user-confirmed")
        if re.fullmatch(r"CLR-[A-Z0-9-]+", str(binding.get("authority_ref", ""))) is None:
            raise BootstrapError(f"{label}.authority_ref must be a stable CLR-* identifier")
        if not str(binding.get("reference_url", "")).startswith("https://"):
            raise BootstrapError(f"{label}.reference_url must be HTTPS")
        _require_string_array(
            binding.get("source_row_ids"), label=f"{label}.source_row_ids"
        )
        _require_string_mapping(
            binding.get("query_parameters"), label=f"{label}.query_parameters"
        )

    facts = context.get("scope_execution_facts")
    if not isinstance(facts, Mapping):
        raise BootstrapError(
            "bounded context template.scope_execution_facts must be an object"
        )
    _exact_fields(
        facts,
        required={
            "version",
            "bounded_scope_kind",
            "expected_testable_assertion_count",
            "expected_tc_count",
            "internal_package_count",
            "has_heterogeneous_integrations",
            "has_large_dictionary",
            "mockups_ready",
            "standard_profile_reasons",
        },
        label="bounded context template.scope_execution_facts",
    )
    if facts.get("version") != 1:
        raise BootstrapError(
            "bounded context template.scope_execution_facts.version must equal 1"
        )
    _require_non_empty_string(
        facts.get("bounded_scope_kind"),
        label="bounded context template.scope_execution_facts.bounded_scope_kind",
    )
    if type(facts.get("internal_package_count")) is not int or facts.get(
        "internal_package_count"
    ) < 1:
        raise BootstrapError(
            "bounded context template.scope_execution_facts.internal_package_count "
            "must be a positive integer"
        )
    for field in (
        "has_heterogeneous_integrations",
        "has_large_dictionary",
        "mockups_ready",
    ):
        if type(facts.get(field)) is not bool:
            raise BootstrapError(
                f"bounded context template.scope_execution_facts.{field} must be boolean"
            )
    _require_string_array(
        facts.get("standard_profile_reasons"),
        label=(
            "bounded context template.scope_execution_facts.standard_profile_reasons"
        ),
    )

    rows = context.get("source_rows")
    if not isinstance(rows, list):
        raise BootstrapError("bounded context template.source_rows must be an array")
    for index, row in enumerate(rows):
        label = f"bounded context template.source_rows[{index}]"
        if not isinstance(row, Mapping):
            raise BootstrapError(f"{label} must be an object")
        _allowed_fields(
            row,
            required=SOURCE_ROW_REQUIRED_FIELDS,
            optional=SOURCE_ROW_OPTIONAL_FIELDS,
            label=label,
        )
        for field in SOURCE_ROW_REQUIRED_FIELDS | (
            SOURCE_ROW_OPTIONAL_FIELDS
            - {"context_relation_required", "requirement_codes_hint"}
        ):
            if field in row:
                _require_non_empty_string(row[field], label=f"{label}.{field}")
        if "requirement_codes_hint" in row:
            _require_string_array(
                row["requirement_codes_hint"],
                label=f"{label}.requirement_codes_hint",
            )
        if "context_relation_required" in row and type(
            row["context_relation_required"]
        ) is not bool:
            raise BootstrapError(f"{label}.context_relation_required must be boolean")

    expected_dependencies = context.get("expected_dependencies", [])
    if not isinstance(expected_dependencies, list):
        raise BootstrapError(
            "bounded context template.expected_dependencies must be an array"
        )
    known_row_ids = {
        str(row.get("source_row_id")) for row in rows if isinstance(row, Mapping)
    }
    expected_dependency_fields = {
        "kind",
        "name",
        "source_row_ids",
        "resolution",
        "target_source_row_ids",
        "exact_source_fragments",
    }
    for index, dependency in enumerate(expected_dependencies):
        label = f"bounded context template.expected_dependencies[{index}]"
        if not isinstance(dependency, Mapping):
            raise BootstrapError(f"{label} must be an object")
        _exact_fields(
            dependency,
            required=expected_dependency_fields,
            label=label,
        )
        if dependency.get("kind") not in DEPENDENCY_KINDS:
            raise BootstrapError(f"{label}.kind is invalid")
        _require_non_empty_string(dependency.get("name"), label=f"{label}.name")
        if dependency.get("resolution") not in DEPENDENCY_RESOLUTIONS:
            raise BootstrapError(f"{label}.resolution is invalid")
        for field in (
            "source_row_ids",
            "target_source_row_ids",
            "exact_source_fragments",
        ):
            _require_string_array(dependency.get(field), label=f"{label}.{field}")
        source_ids = dependency["source_row_ids"]
        target_ids = dependency["target_source_row_ids"]
        if not source_ids:
            raise BootstrapError(f"{label}.source_row_ids must not be empty")
        if set(source_ids) - known_row_ids or set(target_ids) - known_row_ids:
            raise BootstrapError(f"{label} links unknown source rows")
        if len(source_ids) != len(set(source_ids)) or len(target_ids) != len(
            set(target_ids)
        ):
            raise BootstrapError(f"{label} row ids must be unique")
        if not dependency["exact_source_fragments"]:
            raise BootstrapError(
                f"{label}.exact_source_fragments must not be empty"
            )

    parity = context.get("parity")
    if not isinstance(parity, list):
        raise BootstrapError("bounded context template.parity must be an array")
    parity_fields = {
        "requirement_code",
        "docx_locator",
        "xhtml_locator",
        "pdf_locator",
        "status",
    }
    for index, item in enumerate(parity):
        label = f"bounded context template.parity[{index}]"
        if not isinstance(item, Mapping):
            raise BootstrapError(f"{label} must be an object")
        _exact_fields(item, required=parity_fields, label=label)
        for field, value in item.items():
            _require_non_empty_string(value, label=f"{label}.{field}")


def _validate_source_only_template(
    context: Mapping[str, Any], *, canonical_test_cases: str
) -> None:
    def visit(value: Any, path: tuple[str, ...]) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                normalized_key = key.lower().replace("-", "_")
                if normalized_key in SOURCE_ONLY_FORBIDDEN_FIELDS:
                    raise BootstrapError(
                        "bounded context template is not source-only: "
                        f"forbidden field {'.'.join((*path, key))}"
                    )
                visit(child, (*path, key))
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, (*path, str(index)))
            return
        if not isinstance(value, str):
            return
        normalized = value.replace("\\", "/")
        if path == ("canonical_test_cases",) and normalized == canonical_test_cases:
            return
        normalized_lower = normalized.lower()
        if any(
            marker in normalized_lower for marker in SOURCE_ONLY_FORBIDDEN_PATH_MARKERS
        ):
            raise BootstrapError(
                "bounded context template is not source-only: prior-result path "
                f"at {'.'.join(path)}: {value}"
            )

    visit(context, ())
    _validate_source_only_schema(context)
    facts = context.get("scope_execution_facts")
    if isinstance(facts, Mapping):
        for field in ("expected_testable_assertion_count", "expected_tc_count"):
            if facts.get(field) is not None:
                raise BootstrapError(
                    "bounded context template cannot pin prior-result-derived "
                    f"scope_execution_facts.{field}"
                )


def _bounded_evidence_paths(
    context: Mapping[str, Any], *, repo_root: Path
) -> tuple[tuple[str, Path], ...]:
    raw = context.get("bounded_evidence")
    if raw is None:
        return ()
    if not isinstance(raw, Mapping) or set(raw) != {
        "docx",
        "pdf",
        "xhtml_boundary",
    }:
        raise BootstrapError(
            "bounded context template.bounded_evidence must contain exactly "
            "docx, pdf and xhtml_boundary"
        )
    result: list[tuple[str, Path]] = []
    for name in ("docx", "pdf", "xhtml_boundary"):
        value = raw.get(name)
        if not isinstance(value, str) or not value.strip():
            raise BootstrapError(f"bounded_evidence.{name} must be a path")
        path = _resolve_under(
            repo_root,
            Path(value),
            label=f"bounded context template.bounded_evidence.{name}",
        )
        if path.suffix.lower() != ".json" or not path.is_file():
            raise BootstrapError(
                f"bounded_evidence.{name} must be an existing JSON file"
            )
        payload = _read_json_object(path, label=f"bounded evidence {name}")
        if not all(
            field in payload
            for field in ("source_path", "source_sha256", "fragments")
        ):
            raise BootstrapError(
                f"bounded_evidence.{name} misses its source/hash/fragments binding"
            )
        result.append((name, path))
    return tuple(result)


def _validate_context_template_registry(
    *,
    repo_root: Path,
    ft_root: Path,
    ft_slug: str,
    scope_slug: str,
    source_files: Sequence[Path],
    scope_inputs: Sequence[ScopeInput],
    context_template: Path,
    final_artifact: Path,
) -> tuple[Path, tuple[tuple[str, Path], ...]]:
    context = _read_json_object(context_template, label="bounded context template")
    if context.get("ft_slug") != ft_slug or context.get("scope_slug") != scope_slug:
        raise BootstrapError(
            "bounded context template ft_slug/scope_slug does not match bootstrap config"
        )
    expected_canonical = _repo_relative(ft_root, final_artifact)
    _validate_source_only_template(
        context, canonical_test_cases=expected_canonical
    )

    expected_sources = {
        _repo_relative(repo_root, path): PRIMARY_SOURCE_BINDINGS[path.suffix.lower()]
        for path in source_files
    }
    expected_mockups: dict[str, tuple[str, str]] = {}
    package_notes: list[Path] = []
    for item in scope_inputs:
        target = (
            expected_mockups if item.role == "mockup" else expected_sources
        )
        target[_repo_relative(repo_root, item.path)] = (
            item.role,
            item.manifest_binding,
        )
        if item.role == "mandatory-package-context":
            package_notes.append(item.path)

    package_notes_path = (ft_root / "AGENT-NOTES.md").resolve()
    if package_notes_path.is_file():
        if package_notes != [package_notes_path]:
            raise BootstrapError(
                "schema v2 must register the existing FT AGENT-NOTES.md exactly once"
            )
        if context.get("package_notes") != _repo_relative(
            repo_root, package_notes_path
        ):
            raise BootstrapError("bounded context template package_notes path mismatch")
    elif package_notes or "package_notes" in context:
        raise BootstrapError(
            "bounded context template cannot register package_notes when "
            "FT AGENT-NOTES.md is absent"
        )
    actual_sources = _registry_entries(
        context, field="sources", label="bounded context template"
    )
    actual_mockups = _registry_entries(
        context, field="mockups", label="bounded context template"
    )
    if actual_sources != expected_sources:
        raise BootstrapError(
            "bounded context template sources registry does not exactly match "
            "configured source_files/scope_inputs"
        )
    if actual_mockups != expected_mockups:
        raise BootstrapError(
            "bounded context template mockups registry does not exactly match "
            "configured mockup scope_inputs"
        )

    suffix_keys = {
        ".docx": "main_ft_docx",
        ".xhtml": "main_ft_xhtml",
        ".pdf": "main_ft_pdf",
    }
    for path in source_files:
        key = suffix_keys[path.suffix.lower()]
        if context.get(key) != _repo_relative(repo_root, path):
            raise BootstrapError(f"bounded context template {key} path mismatch")
    canonical = context.get("canonical_test_cases")
    if canonical != expected_canonical:
        raise BootstrapError(
            "bounded context template canonical_test_cases does not match "
            "configured final_artifact"
        )
    raw_spec = context.get("source_row_extraction_spec")
    if not isinstance(raw_spec, str) or not raw_spec.strip():
        raise BootstrapError(
            "bounded context template source_row_extraction_spec is required"
        )
    extraction_spec = _resolve_under(
        repo_root,
        Path(raw_spec),
        label="bounded context template source_row_extraction_spec",
    )
    if extraction_spec.parent != context_template.parent or not extraction_spec.is_file():
        raise BootstrapError(
            "source_row_extraction_spec must be an existing sibling of the "
            "source-only context template"
        )
    return extraction_spec, _bounded_evidence_paths(context, repo_root=repo_root)


def _validate_fresh_execution_targets(plan: BootstrapPlan) -> None:
    if plan.schema_version != 2:
        raise BootstrapError("--execute requires bootstrap config schema_version 2")
    _verify_config_snapshot(plan)
    required = {
        "handoff_dir": plan.handoff_dir,
        "cycle_dir": plan.cycle_dir,
        "final_artifact": plan.final_artifact,
    }
    for label, path in required.items():
        if path is None:
            raise BootstrapError(f"schema v2 execution target {label} is missing")
        if path.exists():
            raise BootstrapError(f"fresh execution target already exists: {path}")
    assert plan.context_template is not None
    assert plan.final_artifact is not None
    _validate_context_template_registry(
        repo_root=plan.repo_root,
        ft_root=plan.ft_root,
        ft_slug=plan.ft_slug,
        scope_slug=plan.scope_slug,
        source_files=plan.source_files,
        scope_inputs=plan.scope_inputs,
        context_template=plan.context_template,
        final_artifact=plan.final_artifact,
    )
    _verify_pinned_input_hashes(plan)


def _verify_pinned_input_hashes(plan: BootstrapPlan) -> None:
    if plan.schema_version != 2:
        return
    if not plan.expected_sha256:
        raise BootstrapError("schema v2 expected_sha256 inventory is missing")
    for path, expected in plan.expected_sha256:
        observed = _sha256(path)
        if observed != expected:
            raise BootstrapError(
                f"checked-in SHA-256 mismatch for {_repo_relative(plan.repo_root, path)}: "
                f"expected={expected}, observed={observed}"
            )


def _verify_config_snapshot(plan: BootstrapPlan) -> None:
    observed = _sha256(plan.config_path)
    if observed != plan.config_sha256:
        raise BootstrapError(
            "bootstrap config SHA-256 changed after resolve: "
            f"expected={plan.config_sha256}, observed={observed}"
        )


def resolve_plan(
    *,
    repo_root: Path,
    config_path: Path,
    request_started_epoch_ms: int,
    codex_turn_id: str,
    request_start_source: str = "codex-request-metadata",
) -> BootstrapPlan:
    routing_components: list[dict[str, Any]] = []
    root = repo_root.resolve()
    if not root.is_dir():
        raise BootstrapError(f"repo root does not exist: {root}")
    if type(request_started_epoch_ms) is not int or request_started_epoch_ms <= 0:
        raise BootstrapError("request_started_epoch_ms must be a positive integer")
    turn_id = _safe_id(codex_turn_id.strip(), label="codex_turn_id")
    if request_start_source not in {
        "codex-request-metadata",
        "controller-job-start",
    }:
        raise BootstrapError("unsupported request_start_source")
    routing_components.append(
        {
            "component": "request-metadata-read",
            "duration_ms": "unavailable",
            "status": "included-in-residual",
            "notes": (
                "root-turn metadata is read before bootstrap; its exact duration "
                "is not passed to the executor"
            ),
        }
    )
    routing_components.extend(
        (
            {
                "component": "instruction-loading",
                "duration_ms": "unavailable",
                "status": "included-in-residual",
                "notes": (
                    "mandatory root pre-bootstrap instructions are loaded before "
                    "bootstrap; their elapsed time remains in the phase residual"
                ),
            },
            {
                "component": "environment-probe",
                "duration_ms": "unavailable",
                "status": "included-in-residual",
                "notes": (
                    "root pre-bootstrap environment inspection or saved-probe reuse "
                    "is not separately timed and remains in the phase residual"
                ),
            },
        )
    )
    component_started = time.perf_counter_ns()
    config = _resolve_under(root, config_path, label="config")
    payload, config_sha256 = _load_config(config)
    schema_version = int(payload["schema_version"])
    if schema_version == 2:
        _allowed_fields(
            payload,
            required=SCHEMA_V2_CONFIG_FIELDS,
            optional=SCHEMA_V2_OPTIONAL_CONFIG_FIELDS,
            label="schema-v2 bootstrap config",
        )

    semantic_sharding_mode = "auto"
    semantic_shard_max_included_rows = 10
    semantic_shard_max_source_rows = 16
    semantic_shard_max_shards = 10
    semantic_shard_max_weight = 24
    semantic_sharding = payload.get("semantic_sharding")
    if semantic_sharding is not None:
        if schema_version != 2 or not isinstance(semantic_sharding, Mapping):
            raise BootstrapError("semantic_sharding must be a schema-v2 object")
        _exact_fields(
            semantic_sharding,
            required=SEMANTIC_SHARDING_FIELDS,
            label="schema-v2 bootstrap config.semantic_sharding",
        )
        semantic_sharding_mode = semantic_sharding.get("mode")
        if semantic_sharding_mode not in {"off", "auto", "on"}:
            raise BootstrapError("semantic_sharding.mode is invalid")
        for field in (
            "max_included_rows",
            "max_source_rows",
            "max_shards",
            "max_semantic_weight",
        ):
            value = semantic_sharding.get(field)
            if type(value) is not int or value <= 0:
                raise BootstrapError(f"semantic_sharding.{field} must be positive")
        semantic_shard_max_included_rows = semantic_sharding["max_included_rows"]
        semantic_shard_max_source_rows = semantic_sharding["max_source_rows"]
        semantic_shard_max_shards = semantic_sharding["max_shards"]
        semantic_shard_max_weight = semantic_sharding["max_semantic_weight"]

    benchmark_id = _safe_id(
        _required_string(payload, "benchmark_id"), label="benchmark_id"
    )
    scope_slug = _safe_id(_required_string(payload, "scope_slug"), label="scope_slug")
    ft_root = _resolve_under(
        root, Path(_required_string(payload, "ft_root")), label="ft_root"
    )
    expected_fts_root = (root / "fts").resolve()
    if ft_root.parent != expected_fts_root or not ft_root.is_dir():
        raise BootstrapError(
            f"ft_root must be one existing direct child of {expected_fts_root}: {ft_root}"
        )
    ft_slug = ft_root.name
    configured_ft_slug = _required_string(payload, "ft_slug")
    if configured_ft_slug != ft_slug:
        raise BootstrapError(
            f"configured ft_slug {configured_ft_slug!r} does not match ft_root {ft_slug!r}"
        )
    routing_components.append(
        {
            "component": "ft-config-selection",
            "duration_ms": (time.perf_counter_ns() - component_started) // 1_000_000,
            "status": "measured",
        }
    )

    component_started = time.perf_counter_ns()
    raw_sources = payload.get("source_files")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise BootstrapError("config source_files must be a non-empty array")
    source_files: list[Path] = []
    expected_source_root = (ft_root / "source").resolve()
    for index, item in enumerate(raw_sources):
        if not isinstance(item, str) or not item.strip():
            raise BootstrapError(f"source_files[{index}] must be a non-empty string")
        source = _resolve_under(ft_root, Path(item), label=f"source_files[{index}]")
        try:
            source.relative_to(expected_source_root)
        except ValueError as exc:
            raise BootstrapError(
                f"primary source file must stay under {expected_source_root}: {source}"
            ) from exc
        if not source.is_file():
            raise BootstrapError(f"configured source file does not exist: {source}")
        source_files.append(source)
    suffixes = {path.suffix.lower() for path in source_files}
    if suffixes != REQUIRED_SOURCE_SUFFIXES:
        raise BootstrapError(
            "source_files must contain exactly one DOCX, one XHTML and one PDF; "
            f"found suffixes={sorted(suffixes)}"
        )
    if len(source_files) != len(REQUIRED_SOURCE_SUFFIXES):
        raise BootstrapError("source_files must contain exactly three primary FT files")
    if len({path.parent for path in source_files}) != 1 or len(
        {path.stem for path in source_files}
    ) != 1:
        raise BootstrapError(
            "DOCX, XHTML and PDF must be matching files in one source directory"
        )
    scope_inputs = _scope_inputs(
        payload=payload,
        ft_root=ft_root,
        exact_items=schema_version == 2,
    )
    routing_components.append(
        {
            "component": "source-registry-check",
            "duration_ms": (time.perf_counter_ns() - component_started) // 1_000_000,
            "status": "measured",
        }
    )

    component_started = time.perf_counter_ns()
    observation_root = _resolve_under(
        ft_root,
        Path(_required_string(payload, "observation_root")),
        label="observation_root",
    )
    expected_work_root = (ft_root / "work").resolve()
    expected_observation_root = (expected_work_root / "full-process-observation").resolve()
    if observation_root != expected_observation_root:
        raise BootstrapError(
            "observation_root must be "
            f"{expected_observation_root}, got {observation_root}"
        )
    run_dir = observation_root / turn_id
    if run_dir.exists():
        raise BootstrapError(f"fresh observation run directory already exists: {run_dir}")

    recorder_entrypoint = _resolve_under(
        root,
        Path(_required_string(payload, "recorder_entrypoint")),
        label="recorder_entrypoint",
    )
    production_wrapper = _resolve_under(
        root,
        Path(_required_string(payload, "production_wrapper")),
        label="production_wrapper",
    )
    for label, path in (
        ("recorder_entrypoint", recorder_entrypoint),
        ("production_wrapper", production_wrapper),
    ):
        if not path.is_file():
            raise BootstrapError(f"{label} does not exist: {path}")
    if recorder_entrypoint != (root / "scripts" / "workflow_wall_clock.py").resolve():
        raise BootstrapError("recorder_entrypoint must be scripts/workflow_wall_clock.py")
    if production_wrapper != (
        root / "scripts" / "run_standard_production_iteration.py"
    ).resolve():
        raise BootstrapError(
            "production_wrapper must be scripts/run_standard_production_iteration.py"
        )

    runtime_dir = run_dir / "runtime"
    execution_summary = run_dir / "full-process-execution-summary.json"
    context_template: Path | None = None
    source_preparation_cache: Path | None = None
    prepared_context: Path | None = None
    source_row_baseline: Path | None = None
    source_preparation_summary: Path | None = None
    handoff_dir: Path | None = None
    cycle_dir: Path | None = None
    final_artifact: Path | None = None
    expected_sha256: tuple[tuple[Path, str], ...] = ()
    hash_duration_ms = 0
    workspace_duration_ms: int | None = None
    if schema_version == 2:
        preparation = _required_object(payload, "source_preparation")
        _exact_fields(
            preparation,
            required={"context_template", "cache_dir"},
            label="config source_preparation",
        )
        outputs = _required_object(payload, "outputs")
        _exact_fields(
            outputs,
            required={"handoff_dir", "cycle_dir", "final_artifact"},
            label="config outputs",
        )
        context_template = _resolve_under(
            root,
            Path(_required_string(preparation, "context_template")),
            label="source_preparation.context_template",
        )
        if not context_template.is_file():
            raise BootstrapError(
                f"configured bounded context template does not exist: {context_template}"
            )
        try:
            context_template.relative_to(config.parent.resolve())
        except ValueError as exc:
            raise BootstrapError(
                "schema v2 context template must stay under the checked-in "
                f"config directory {config.parent.resolve()}"
            ) from exc
        source_preparation_cache = _resolve_under(
            root,
            Path(_required_string(preparation, "cache_dir")),
            label="source_preparation.cache_dir",
        )
        expected_cache = (
            root / ".codex-temp" / "source-preparation-cache"
        ).resolve()
        if source_preparation_cache != expected_cache:
            raise BootstrapError(
                "source_preparation.cache_dir must equal canonical protected cache "
                f"path {_repo_relative(root, expected_cache)}"
            )
        prepared_context = run_dir / "source-preparation" / "prepared-bounded-context.json"
        source_row_baseline = run_dir / "source-preparation" / "source-row-baseline.json"
        source_preparation_summary = run_dir / "source-preparation" / "summary.json"

        handoff_dir = _resolve_under(
            ft_root,
            Path(_required_string(outputs, "handoff_dir")),
            label="outputs.handoff_dir",
        )
        expected_handoff_root = (ft_root / "work" / "stage-handoffs").resolve()
        if handoff_dir.parent != expected_handoff_root or not re.fullmatch(
            r"[0-9]{2,}-[A-Za-z0-9][A-Za-z0-9._-]*", handoff_dir.name
        ):
            raise BootstrapError(
                "outputs.handoff_dir must be one fresh NN...-<scope-slug> directory "
                f"directly under {expected_handoff_root}"
            )
        cycle_dir = _resolve_under(
            ft_root,
            Path(_required_string(outputs, "cycle_dir")),
            label="outputs.cycle_dir",
        )
        expected_cycle_root = (ft_root / "work" / "review-cycles").resolve()
        if cycle_dir.parent != expected_cycle_root:
            raise BootstrapError(
                "outputs.cycle_dir must be one direct child of "
                f"{expected_cycle_root}"
            )
        _safe_id(cycle_dir.name, label="outputs.cycle_dir name")
        final_artifact = _resolve_under(
            ft_root,
            Path(_required_string(outputs, "final_artifact")),
            label="outputs.final_artifact",
        )
        expected_test_case_root = (ft_root / "test-cases").resolve()
        if (
            final_artifact.parent != expected_test_case_root
            or final_artifact.suffix.lower() != ".md"
        ):
            raise BootstrapError(
                "outputs.final_artifact must be one Markdown file directly under "
                f"{expected_test_case_root}"
            )
        extraction_spec, bounded_evidence = _validate_context_template_registry(
            repo_root=root,
            ft_root=ft_root,
            ft_slug=ft_slug,
            scope_slug=scope_slug,
            source_files=source_files,
            scope_inputs=scope_inputs,
            context_template=context_template,
            final_artifact=final_artifact,
        )
        workspace_duration_ms = (
            time.perf_counter_ns() - component_started
        ) // 1_000_000
        hash_started = time.perf_counter_ns()
        expected_sha256 = _expected_sha256_inventory(
            payload,
            repo_root=root,
            expected_paths=(
                *source_files,
                *(item.path for item in scope_inputs),
                context_template,
                extraction_spec,
                *(path for _name, path in bounded_evidence),
            ),
        )
        hash_duration_ms = (time.perf_counter_ns() - hash_started) // 1_000_000
    if workspace_duration_ms is None:
        workspace_duration_ms = (
            time.perf_counter_ns() - component_started
        ) // 1_000_000
    routing_components.append(
        {
            "component": "workspace-check",
            "duration_ms": workspace_duration_ms,
            "status": "measured",
        }
    )
    routing_components.append(
        {
            "component": "hash-verification",
            "duration_ms": hash_duration_ms,
            "status": "measured" if schema_version == 2 else "not-applicable",
        }
    )
    routing_components.append(
        {
            "component": "external-backend-wait",
            "duration_ms": 0,
            "status": "not-applicable",
            "notes": "backend wait is attributed to the later model stage",
        }
    )
    routing_components.append(
        {
            "component": "other-orchestration",
            "duration_ms": "unavailable",
            "status": "pending-residual",
            "notes": (
                "resolved from the completed routing-preflight phase duration in "
                "the reconciled timing report"
            ),
        }
    )

    return BootstrapPlan(
        schema_version=schema_version,
        repo_root=root,
        config_path=config,
        config_sha256=config_sha256,
        benchmark_id=benchmark_id,
        ft_root=ft_root,
        ft_slug=ft_slug,
        scope_slug=scope_slug,
        source_files=tuple(source_files),
        scope_inputs=scope_inputs,
        expected_sha256=expected_sha256,
        observation_root=observation_root,
        run_dir=run_dir,
        timer=run_dir / "workflow-performance.json",
        receipt=run_dir / "bootstrap-receipt.json",
        recorder_entrypoint=recorder_entrypoint,
        production_wrapper=production_wrapper,
        context_template=context_template,
        source_preparation_cache=source_preparation_cache,
        prepared_context=prepared_context,
        source_row_baseline=source_row_baseline,
        source_preparation_summary=source_preparation_summary,
        runtime_dir=runtime_dir,
        handoff_dir=handoff_dir,
        cycle_dir=cycle_dir,
        final_artifact=final_artifact,
        execution_summary=execution_summary,
        request_started_epoch_ms=request_started_epoch_ms,
        codex_turn_id=turn_id,
        request_start_source=request_start_source,
        semantic_sharding_mode=semantic_sharding_mode,
        semantic_shard_max_included_rows=semantic_shard_max_included_rows,
        semantic_shard_max_source_rows=semantic_shard_max_source_rows,
        semantic_shard_max_shards=semantic_shard_max_shards,
        semantic_shard_max_weight=semantic_shard_max_weight,
        routing_preflight_breakdown=tuple(routing_components),
    )


def _relative(plan: BootstrapPlan, path: Path) -> str:
    return path.relative_to(plan.repo_root).as_posix()


def plan_payload(plan: BootstrapPlan) -> dict[str, Any]:
    fixed_arguments = [
        "--repo-root",
        ".",
        "--runtime-dir",
        _relative(plan, plan.runtime_dir),
        "--timer",
        _relative(plan, plan.timer),
        "--measurement-mode",
        "observational",
        "--semantic-sharding",
        plan.semantic_sharding_mode,
        "--semantic-shard-max-included-rows",
        str(plan.semantic_shard_max_included_rows),
        "--semantic-shard-max-source-rows",
        str(plan.semantic_shard_max_source_rows),
        "--semantic-shard-max-shards",
        str(plan.semantic_shard_max_shards),
        "--semantic-shard-max-weight",
        str(plan.semantic_shard_max_weight),
    ]
    required_dynamic_arguments = [
        "--context",
        "--handoff-dir",
        "--cycle-dir",
        "--final-artifact",
    ]
    execution: dict[str, Any] | None = None
    if plan.schema_version == 2:
        assert plan.context_template is not None
        assert plan.source_preparation_cache is not None
        assert plan.prepared_context is not None
        assert plan.source_row_baseline is not None
        assert plan.source_preparation_summary is not None
        assert plan.handoff_dir is not None
        assert plan.cycle_dir is not None
        assert plan.final_artifact is not None
        fixed_arguments.extend(
            [
                "--context",
                _relative(plan, plan.prepared_context),
                "--handoff-dir",
                _relative(plan, plan.handoff_dir),
                "--cycle-dir",
                _relative(plan, plan.cycle_dir),
                "--final-artifact",
                _relative(plan, plan.final_artifact),
            ]
        )
        for item in plan.scope_inputs:
            if item.role == "mockup":
                fixed_arguments.extend(("--image", _relative(plan, item.path)))
        required_dynamic_arguments = []
        execution = {
            "source_preparation": {
                "context_template": _relative(plan, plan.context_template),
                "cache_dir": _relative(plan, plan.source_preparation_cache),
                "prepared_context": _relative(plan, plan.prepared_context),
                "source_row_baseline": _relative(plan, plan.source_row_baseline),
                "summary": _relative(plan, plan.source_preparation_summary),
            },
            "outputs": {
                "runtime_dir": _relative(plan, plan.runtime_dir),
                "handoff_dir": _relative(plan, plan.handoff_dir),
                "cycle_dir": _relative(plan, plan.cycle_dir),
                "final_artifact": _relative(plan, plan.final_artifact),
                "execution_summary": _relative(plan, plan.execution_summary),
            },
        }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "config_schema_version": plan.schema_version,
        "status": "validated",
        "benchmark_id": plan.benchmark_id,
        "config_path": _relative(plan, plan.config_path),
        "config_sha256": plan.config_sha256,
        "ft_root": _relative(plan, plan.ft_root),
        "ft_slug": plan.ft_slug,
        "scope_slug": plan.scope_slug,
        "source_files": [_relative(plan, path) for path in plan.source_files],
        "scope_inputs": [
            {
                "path": _relative(plan, item.path),
                "role": item.role,
                "manifest_binding": item.manifest_binding,
            }
            for item in plan.scope_inputs
        ],
        "observation_timer": _relative(plan, plan.timer),
        "recorder_entrypoint": _relative(plan, plan.recorder_entrypoint),
        "production_wrapper": _relative(plan, plan.production_wrapper),
        "production_wrapper_invocation": {
            "entrypoint": _relative(plan, plan.production_wrapper),
            "fixed_arguments": fixed_arguments,
            "required_dynamic_arguments": required_dynamic_arguments,
        },
        "measurement_mode": "observational",
        "request_started_epoch_ms": plan.request_started_epoch_ms,
        "codex_turn_id": plan.codex_turn_id,
        "request_start_source": plan.request_start_source,
        "initial_phase": "routing-preflight",
    }
    if execution is not None:
        payload["execution"] = execution
        payload["expected_sha256"] = {
            _relative(plan, path): digest for path, digest in plan.expected_sha256
        }
    return payload


def start_observation(
    plan: BootstrapPlan, *, python_executable: Path | str = sys.executable
) -> dict[str, Any]:
    # The checked-in pins are the last pre-recorder gate.  A schema-v2 run may
    # not start a timer from source/profile bytes that drifted after resolve.
    _verify_config_snapshot(plan)
    _verify_pinned_input_hashes(plan)
    command = [
        str(python_executable),
        str(plan.recorder_entrypoint),
        "start",
        "--output",
        str(plan.timer),
        "--ft-slug",
        plan.ft_slug,
        "--scope-slug",
        plan.scope_slug,
        "--profile",
        "current-full-process-observation",
        "--measurement-mode",
        "observational",
        "--request-started-epoch-ms",
        str(plan.request_started_epoch_ms),
        "--request-start-source",
        plan.request_start_source,
        "--request-start-precision-ms",
        "1",
        "--codex-turn-id",
        plan.codex_turn_id,
        "--end-anchor",
        (
            "pre-final-response"
            if plan.request_start_source == "codex-request-metadata"
            else "controller-job-complete"
        ),
        "--initial-phase",
        "routing-preflight",
    ]
    completed = subprocess.run(
        command,
        cwd=plan.repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise BootstrapError(f"workflow timer start failed: {detail}")
    try:
        timer_payload = json.loads(plan.timer.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"workflow timer was not created correctly: {exc}") from exc
    if (
        not isinstance(timer_payload, dict)
        or timer_payload.get("status") != "running"
        or timer_payload.get("ft_slug") != plan.ft_slug
        or timer_payload.get("scope_slug") != plan.scope_slug
        or timer_payload.get("measurement_coverage") != "request-received"
    ):
        raise BootstrapError("workflow timer does not match the validated bootstrap plan")

    source_profile_inventory: list[dict[str, Any]] = []
    if plan.context_template is not None:
        context_payload = _read_json_object(
            plan.context_template, label="bounded context template"
        )
        raw_spec = context_payload.get("source_row_extraction_spec")
        if not isinstance(raw_spec, str) or not raw_spec.strip():
            raise BootstrapError(
                "bounded context template source_row_extraction_spec is required"
            )
        extraction_spec = _resolve_under(
            plan.repo_root,
            Path(raw_spec),
            label="bounded context template source_row_extraction_spec",
        )
        bounded_evidence = _bounded_evidence_paths(
            context_payload, repo_root=plan.repo_root
        )
        for role, path in (
            ("bootstrap-config", plan.config_path),
            ("bounded-context-template", plan.context_template),
            ("source-row-extraction-spec", extraction_spec),
            *(
                (f"bounded-evidence-{name}", path)
                for name, path in bounded_evidence
            ),
        ):
            source_profile_inventory.append(
                {
                    "path": _relative(plan, path),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )

    receipt = {
        **plan_payload(plan),
        "status": "started",
        "timer_status": "running",
        "source_inventory": [
            {
                "path": _relative(plan, path),
                "role": PRIMARY_SOURCE_BINDINGS[path.suffix.lower()][0],
                "manifest_binding": PRIMARY_SOURCE_BINDINGS[path.suffix.lower()][1],
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in plan.source_files
        ],
        "scope_input_inventory": [
            {
                "path": _relative(plan, item.path),
                "role": item.role,
                "manifest_binding": item.manifest_binding,
                "bytes": item.path.stat().st_size,
                "sha256": _sha256(item.path),
            }
            for item in plan.scope_inputs
        ],
        "source_profile_inventory": source_profile_inventory,
        "execution_code_inventory": _execution_code_inventory(plan),
        "repository_state_at_start": _repository_state(plan),
        "next_action": {
            "phase": "routing-preflight",
            "rule": (
                "Use the recorded source_files, scope_inputs, production_wrapper "
                "and observation_timer; do not infer replacement paths."
            ),
        },
    }
    _write_json_atomic(plan.receipt, receipt)
    return receipt


def _preparation_payload(result: Any) -> dict[str, Any]:
    if hasattr(result, "to_dict") and callable(result.to_dict):
        payload = result.to_dict()
    elif isinstance(result, Mapping):
        payload = dict(result)
    else:
        raise BootstrapError("source preparer returned an unsupported result")
    if not isinstance(payload, dict):
        raise BootstrapError("source preparer result must serialize to an object")
    return payload


def _load_preparation_dependencies() -> tuple[
    Callable[..., Any],
    Callable[[Path, Mapping[str, Any]], Sequence[Mapping[str, Any]]],
    Callable[[Mapping[str, Any]], Mapping[str, Any]],
]:
    """Load default source-preparation dependencies after the timer starts.

    These imports are deliberately lazy.  A direct-file CLI execution must
    create its observation timer before an optional stage dependency can fail,
    so that the one-command boundary can record a terminal result instead of
    leaving an unmeasured early exit.
    """

    from test_case_agent.semantic_design_bridge import load_approved_clarifications
    from test_case_agent.source_preparation import prepare_bounded_scope_context
    from scripts.codex_exec_bounded_scope_analyzer import analyze_dependency_gaps

    return (
        prepare_bounded_scope_context,
        load_approved_clarifications,
        analyze_dependency_gaps,
    )


def _load_production_runner() -> Callable[[Sequence[str] | None], int]:
    """Load the canonical wrapper only after deterministic preflights pass."""

    from scripts.run_standard_production_iteration import main as production_main

    return production_main


def _execution_code_inventory(plan: BootstrapPlan) -> list[dict[str, Any]]:
    candidates = (
        plan.recorder_entrypoint,
        plan.production_wrapper,
        plan.repo_root / "scripts" / "run_standard_scope_bridge.py",
        plan.repo_root / "scripts" / "run_lean_production_iteration.py",
        plan.repo_root / "scripts" / "codex_exec_source_assertion_reviewer.py",
        plan.repo_root / "scripts" / "codex_exec_review_cycle_runner.py",
        plan.repo_root / "test_case_agent" / "lean_production.py",
        plan.repo_root / "test_case_agent" / "semantic_design_bridge.py",
    )
    unique: dict[Path, None] = {}
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            unique[resolved] = None
    return [
        {
            "path": _relative(plan, path),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in unique
    ]


def _repository_state(plan: BootstrapPlan) -> dict[str, Any]:
    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments),
            cwd=plan.repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    try:
        head = git("rev-parse", "HEAD")
        status = git("status", "--porcelain=v1", "--untracked-files=all")
    except Exception:  # noqa: BLE001 - provenance is explicitly best-effort.
        return {"status": "unavailable", "head": None, "dirty": None}
    if head.returncode != 0 or status.returncode != 0:
        return {"status": "unavailable", "head": None, "dirty": None}
    status_text = status.stdout.replace("\r\n", "\n")
    entries = [line for line in status_text.splitlines() if line]
    return {
        "status": "recorded",
        "head": head.stdout.strip(),
        "dirty": bool(entries),
        "status_entry_count": len(entries),
        "status_sha256": hashlib.sha256(status_text.encode("utf-8")).hexdigest(),
    }


def _production_arguments(plan: BootstrapPlan) -> list[str]:
    assert plan.prepared_context is not None
    assert plan.handoff_dir is not None
    assert plan.cycle_dir is not None
    assert plan.final_artifact is not None
    arguments = [
        "--repo-root",
        str(plan.repo_root),
        "--context",
        str(plan.prepared_context),
        "--runtime-dir",
        str(plan.runtime_dir),
        "--handoff-dir",
        str(plan.handoff_dir),
        "--cycle-dir",
        str(plan.cycle_dir),
        "--final-artifact",
        str(plan.final_artifact),
        "--timer",
        str(plan.timer),
        "--measurement-mode",
        "observational",
        "--semantic-sharding",
        plan.semantic_sharding_mode,
        "--semantic-shard-max-included-rows",
        str(plan.semantic_shard_max_included_rows),
        "--semantic-shard-max-source-rows",
        str(plan.semantic_shard_max_source_rows),
        "--semantic-shard-max-shards",
        str(plan.semantic_shard_max_shards),
        "--semantic-shard-max-weight",
        str(plan.semantic_shard_max_weight),
    ]
    for item in plan.scope_inputs:
        if item.role == "mockup":
            arguments.extend(("--image", str(item.path)))
    return arguments


def _pending_reconciliation(plan: BootstrapPlan) -> dict[str, Any]:
    if plan.request_start_source != "codex-request-metadata":
        return {
            "status": "not-applicable",
            "reason": (
                "This observation starts at the local controller job boundary, "
                "not at a Codex user request. A separate clean Codex turn is "
                "required for request-to-final reconciliation."
            ),
            "timer": _relative(plan, plan.timer),
            "required_action": "run a separate clean request-to-final observation",
            "codex_turn_id": None,
        }
    return {
        "status": "pending",
        "reason": (
            "Codex task_complete is emitted only after the final response; "
            "the timer currently proves the pre-final observed window."
        ),
        "timer": _relative(plan, plan.timer),
        "required_action": "workflow_wall_clock.py reconcile-codex-turn",
        "codex_turn_id": plan.codex_turn_id,
    }


def _count_test_cases(path: Path) -> int:
    return sum(
        line.startswith("## TC-")
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def _verify_receipt_input_hashes(
    plan: BootstrapPlan, receipt: Mapping[str, Any]
) -> None:
    _verify_config_snapshot(plan)
    expected_sources = [
        {
            "path": _relative(plan, path),
            "role": PRIMARY_SOURCE_BINDINGS[path.suffix.lower()][0],
            "manifest_binding": PRIMARY_SOURCE_BINDINGS[path.suffix.lower()][1],
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in plan.source_files
    ]
    expected_scope_inputs = [
        {
            "path": _relative(plan, item.path),
            "role": item.role,
            "manifest_binding": item.manifest_binding,
            "bytes": item.path.stat().st_size,
            "sha256": _sha256(item.path),
        }
        for item in plan.scope_inputs
    ]
    if receipt.get("source_inventory") != expected_sources:
        raise BootstrapError(
            "primary source bytes/SHA changed after the bootstrap receipt"
        )
    if receipt.get("scope_input_inventory") != expected_scope_inputs:
        raise BootstrapError(
            "scope input bytes/SHA changed after the bootstrap receipt"
        )
    if receipt.get("execution_code_inventory") != _execution_code_inventory(plan):
        raise BootstrapError(
            "execution code bytes/SHA changed after the bootstrap receipt"
        )
    if plan.context_template is not None:
        context = _read_json_object(
            plan.context_template, label="bounded context template"
        )
        raw_spec = context.get("source_row_extraction_spec")
        if not isinstance(raw_spec, str) or not raw_spec.strip():
            raise BootstrapError(
                "bounded context template source_row_extraction_spec is required"
            )
        extraction_spec = _resolve_under(
            plan.repo_root,
            Path(raw_spec),
            label="bounded context template source_row_extraction_spec",
        )
        bounded_evidence = _bounded_evidence_paths(
            context, repo_root=plan.repo_root
        )
        expected_profiles = [
            {
                "path": _relative(plan, path),
                "role": role,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for role, path in (
                ("bootstrap-config", plan.config_path),
                ("bounded-context-template", plan.context_template),
                ("source-row-extraction-spec", extraction_spec),
                *(
                    (f"bounded-evidence-{name}", path)
                    for name, path in bounded_evidence
                ),
            )
        ]
        if receipt.get("source_profile_inventory") != expected_profiles:
            raise BootstrapError(
                "source profile bytes/SHA changed after the bootstrap receipt"
            )


def execute_observation(
    plan: BootstrapPlan,
    *,
    observation_starter: Callable[[BootstrapPlan], Mapping[str, Any]] = start_observation,
    source_preparer: Callable[..., Any] | None = None,
    clarification_loader: Callable[[Path, Mapping[str, Any]], Sequence[Mapping[str, Any]]]
    | None = None,
    dependency_analyzer: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    | None = None,
    production_runner: Callable[[Sequence[str] | None], int] | None = None,
) -> dict[str, Any]:
    """Execute one configured observation without root-agent stage orchestration.

    All semantic/model gates remain owned by the canonical production wrapper.
    This outer route only validates the checked-in source profile, materializes
    its hash-bound context, performs the same deterministic preflights early,
    and invokes the wrapper exactly once.
    """

    _validate_fresh_execution_targets(plan)
    assert plan.context_template is not None
    assert plan.source_preparation_cache is not None
    assert plan.prepared_context is not None
    assert plan.source_row_baseline is not None
    assert plan.source_preparation_summary is not None
    assert plan.handoff_dir is not None
    assert plan.cycle_dir is not None
    assert plan.final_artifact is not None

    from test_case_agent.lean_production import (
        build_timing_report,
        finish_phase,
        finish_run,
        load_run,
        render_timing_markdown,
        start_phase,
        terminalize_run,
        transition_phase,
    )

    registered_inputs = tuple(plan.source_files) + tuple(
        item.path for item in plan.scope_inputs
    )
    registered_set = set(registered_inputs)
    preparation_inputs = (
        *(
            path
            for path, _digest in plan.expected_sha256
            if path not in registered_set
        ),
        *registered_inputs,
    )
    production_invocation_count = 0
    timing_json = plan.run_dir / "workflow-timing-report.json"
    timing_markdown = plan.run_dir / "workflow-timing-report.md"
    compact: dict[str, Any] = {
        "schema_version": 1,
        "benchmark_id": plan.benchmark_id,
        "status": "running",
        "return_code": None,
        "timer": _relative(plan, plan.timer),
        "prepared_context": _relative(plan, plan.prepared_context),
        "source_preparation": {"status": "not-run"},
        "preflight": {
            "status": "not-run",
            "approved_clarification_count": None,
            "blocking_gap_count": None,
        },
        "production": {
            "entrypoint": _relative(plan, plan.production_wrapper),
            "invocation_count": 0,
            "status": "not-run",
        },
        "final_artifact": _relative(plan, plan.final_artifact),
        "test_case_count": 0,
        "post_turn_reconciliation": _pending_reconciliation(plan),
        "timing_report": {
            "json": _relative(plan, timing_json),
            "markdown": _relative(plan, timing_markdown),
        },
        "reporting": {"status": "pending", "errors": []},
    }

    def record_reporting_error(*, operation: str, exc: Exception) -> None:
        compact["reporting"]["status"] = "failed"
        compact["reporting"]["errors"].append(
            {
                "operation": operation,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

    def write_compact() -> bool:
        compact["production"]["invocation_count"] = production_invocation_count
        if compact["reporting"]["status"] == "pending":
            compact["reporting"]["status"] = "completed"
        try:
            _write_json_atomic(plan.execution_summary, compact)
        except Exception as exc:  # noqa: BLE001 - reporting is best-effort.
            record_reporting_error(operation="write-execution-summary", exc=exc)
            return False
        return True

    def publish_timing_report() -> None:
        report = build_timing_report(load_run(plan.timer))
        _write_json_atomic(timing_json, report)
        _write_text_atomic(timing_markdown, render_timing_markdown(report))

    def terminalize(
        *, status: str, return_code: int, error_type: str, error: str
    ) -> dict[str, Any]:
        compact.update(
            {
                "status": status,
                "return_code": return_code,
                "error_type": error_type,
                "error": error,
            }
        )
        try:
            timer_payload = load_run(plan.timer)
            if timer_payload.get("status") == "running" and not any(
                item.get("status") == "running"
                for item in timer_payload.get("phases", [])
            ):
                start_phase(
                    plan.timer,
                    phase="final-reporting",
                    input_artifact_roots=(plan.execution_summary,),
                )
        except Exception as exc:  # noqa: BLE001 - still terminalize the timer.
            record_reporting_error(operation="start-final-reporting-phase", exc=exc)
        write_compact()
        try:
            terminalize_run(
                plan.timer,
                status=status,
                error_type=error_type,
                error=error,
                test_case_count=0,
                artifact_roots=(
                    plan.run_dir,
                    plan.handoff_dir,
                    plan.cycle_dir,
                    plan.final_artifact,
                ),
            )
            publish_timing_report()
        except Exception as timer_exc:  # noqa: BLE001 - preserve primary result.
            compact["timer_finalization_error"] = {
                "error_type": type(timer_exc).__name__,
                "error": str(timer_exc),
            }
            record_reporting_error(operation="terminalize-timer", exc=timer_exc)
            write_compact()
        return compact

    try:
        command_preparation_started = time.perf_counter_ns()
        receipt = dict(observation_starter(plan))
        _verify_receipt_input_hashes(plan, receipt)
        if (
            source_preparer is None
            or clarification_loader is None
            or dependency_analyzer is None
        ):
            (
                default_source_preparer,
                default_clarification_loader,
                default_dependency_analyzer,
            ) = _load_preparation_dependencies()
            if source_preparer is None:
                source_preparer = default_source_preparer
            if clarification_loader is None:
                clarification_loader = default_clarification_loader
            if dependency_analyzer is None:
                dependency_analyzer = default_dependency_analyzer
        routing_breakdown = [
            dict(item)
            for item in plan.routing_preflight_breakdown
            if item.get("component") != "other-orchestration"
        ]
        routing_breakdown.append(
            {
                "component": "command-preparation",
                "duration_ms": (
                    time.perf_counter_ns() - command_preparation_started
                )
                // 1_000_000,
                "status": "measured",
            }
        )
        routing_breakdown.append(
            next(
                dict(item)
                for item in plan.routing_preflight_breakdown
                if item.get("component") == "other-orchestration"
            )
        )
        transition_phase(
            plan.timer,
            phase="routing-preflight",
            status="completed",
            next_phase="source-selection",
            metrics={
                "route_id": "production.checked_in_observation",
                "config_schema_version": plan.schema_version,
                "manual_stage_orchestration": False,
                "routing_preflight_breakdown": routing_breakdown,
            },
            input_artifact_roots=(plan.config_path,),
            output_artifact_roots=(plan.receipt,),
            next_input_artifact_roots=registered_inputs,
        )
        transition_phase(
            plan.timer,
            phase="source-selection",
            status="completed",
            next_phase="source-preparation",
            metrics={
                "selection_mode": "checked-in-exact-registry",
                "source_count": len(plan.source_files),
                "scope_input_count": len(plan.scope_inputs),
            },
            input_artifact_roots=registered_inputs,
            output_artifact_roots=(plan.receipt,),
            next_input_artifact_roots=preparation_inputs,
        )
        preparation_result = source_preparer(
            repo_root=plan.repo_root,
            context_template=plan.context_template,
            cache_dir=plan.source_preparation_cache,
            output_context=plan.prepared_context,
            output_baseline=plan.source_row_baseline,
            allow_overwrite=False,
        )
        preparation_payload = _preparation_payload(preparation_result)
        prepared = _read_json_object(
            plan.prepared_context, label="prepared bounded context"
        )
        clarifications = tuple(clarification_loader(plan.repo_root, prepared))
        dependency = dict(dependency_analyzer(prepared))
        blocking_count = dependency.get("blocking_gap_count")
        if type(blocking_count) is not int or blocking_count < 0:
            raise BootstrapError(
                "dependency analyzer did not return a valid blocking_gap_count"
            )
        preparation_summary = {
            **preparation_payload,
            "approved_clarification_count": len(clarifications),
            "dependency_preflight": dependency,
        }
        _write_json_atomic(plan.source_preparation_summary, preparation_summary)
        compact["source_preparation"] = {
            key: preparation_payload.get(key)
            for key in (
                "status",
                "cache_key",
                "cache_hit",
                "input_file_count",
                "input_bytes",
                "candidate_count",
                "duration_ms",
            )
        }
        cache_hit = preparation_payload.get("cache_hit")
        compact["source_preparation"]["cache_classification"] = (
            "warm-cache"
            if cache_hit is True
            else "cold-cache"
            if cache_hit is False
            else "cache-status-unavailable"
        )
        compact["preflight"] = {
            "status": dependency.get("status"),
            "approved_clarification_count": len(clarifications),
            "blocking_gap_count": blocking_count,
        }
        finish_phase(
            plan.timer,
            phase="source-preparation",
            status="blocked" if blocking_count else "completed",
            metrics={
                "source_preparation": compact["source_preparation"],
                "preflight": compact["preflight"],
            },
            input_artifact_roots=preparation_inputs,
            output_artifact_roots=(
                plan.prepared_context,
                plan.source_row_baseline,
                plan.source_preparation_summary,
            ),
        )
        if blocking_count:
            return terminalize(
                status="blocked-input",
                return_code=3,
                error_type="DependencyPreflightBlocked",
                error=f"dependency preflight found {blocking_count} blocking gap(s)",
            )

        # Close the receipt-to-wrapper window as well as the earlier
        # receipt-to-preparation window.  Source preparation is allowed to
        # materialize outputs, but it must not change any registered input.
        _verify_receipt_input_hashes(plan, receipt)
        _validate_fresh_execution_targets(plan)
        arguments = _production_arguments(plan)
        if production_runner is None:
            production_runner = _load_production_runner()
        production_invocation_count = 1
        production_code = production_runner(arguments)
        if type(production_code) is not int:
            raise BootstrapError("production wrapper returned a non-integer code")
        production_summary_path = (
            plan.runtime_dir / "standard-production-iteration-summary.json"
        )
        production_summary = (
            _read_json_object(production_summary_path, label="production summary")
            if production_summary_path.is_file()
            else {}
        )
        compact["production"] = {
            "entrypoint": _relative(plan, plan.production_wrapper),
            "invocation_count": production_invocation_count,
            "status": production_summary.get(
                "status", "completed" if production_code == 0 else "terminal-failed"
            ),
            "return_code": production_code,
            "summary": (
                _relative(plan, production_summary_path)
                if production_summary_path.is_file()
                else None
            ),
        }
        if production_code != 0:
            terminal_status = (
                "blocked-input"
                if production_code == 3
                or production_summary.get("status") == "blocked-input"
                else "terminal-failed"
            )
            return terminalize(
                status=terminal_status,
                return_code=production_code,
                error_type="ProductionWrapperTerminalResult",
                error=f"production wrapper returned {production_code}",
            )
        if not plan.final_artifact.is_file():
            raise BootstrapError(
                "production wrapper returned success without the final test-case artifact"
            )

        test_case_count = _count_test_cases(plan.final_artifact)
        compact.update(
            {
                "status": "signed-off",
                "return_code": 0,
                "test_case_count": test_case_count,
            }
        )
        start_phase(
            plan.timer,
            phase="final-reporting",
            input_artifact_roots=(
                production_summary_path,
                plan.final_artifact,
            ),
        )
        summary_written = write_compact()
        finish_run(
            plan.timer,
            status="signed-off",
            test_case_count=test_case_count,
            artifact_roots=(
                plan.run_dir,
                plan.handoff_dir,
                plan.cycle_dir,
                plan.final_artifact,
            ),
            active_phase="final-reporting",
            phase_status="completed",
            phase_metrics={
                "execution_summary": _relative(plan, plan.execution_summary),
                "execution_summary_status": (
                    "written" if summary_written else "write-failed"
                ),
                "post_turn_reconciliation": "pending",
            },
            phase_input_artifact_roots=(
                production_summary_path,
                plan.final_artifact,
            ),
            phase_output_artifact_roots=(
                plan.execution_summary,
                plan.final_artifact,
            ),
        )
        publish_timing_report()
        if not summary_written:
            # The test-case release succeeded, but the observation report did
            # not.  Preserve signed-off workflow state and surface the
            # operational failure to the caller through a non-zero code.
            compact["return_code"] = 2
        return compact
    except Exception as exc:  # noqa: BLE001 - terminal one-command boundary.
        return terminalize(
            status="terminal-failed",
            return_code=2,
            error_type=type(exc).__name__,
            error=str(exc),
        )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Start one deterministic full-process observation from a checked-in "
            "FT benchmark profile."
        )
    )
    result.add_argument("--config", type=Path, required=True)
    result.add_argument("--request-started-epoch-ms", type=int, required=True)
    result.add_argument("--codex-turn-id", required=True)
    result.add_argument(
        "--request-start-source",
        choices=("codex-request-metadata", "controller-job-start"),
        default="codex-request-metadata",
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument(
        "--execute",
        action="store_true",
        help=(
            "For a schema-v2 profile, prepare the source-bound context and run "
            "the canonical full-production wrapper exactly once."
        ),
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        plan = resolve_plan(
            repo_root=args.repo_root,
            config_path=args.config,
            request_started_epoch_ms=args.request_started_epoch_ms,
            codex_turn_id=args.codex_turn_id,
            request_start_source=args.request_start_source,
        )
        if args.validate_only:
            payload = plan_payload(plan)
        elif args.execute:
            payload = execute_observation(plan)
        else:
            payload = start_observation(plan)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return int(payload.get("return_code", 0) or 0) if args.execute else 0
    except (BootstrapError, OSError, ValueError) as exc:
        print(
            json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
