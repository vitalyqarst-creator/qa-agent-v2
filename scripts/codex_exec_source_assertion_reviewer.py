from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.resolve_instruction_context import resolve_instruction_context
from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    probe_exec_capability,
    resolve_verified_exec_capability,
)
from test_case_agent.review_cycle.exec_events import TOOL_EVENT_ITEM_TYPES
from scripts.openai_strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from test_case_agent.review_cycle.source_assertions import (
    EXECUTION_READINESS_VALUES,
    POLARITIES,
    REVIEW_RECEIPT_VERSION,
    RISKS,
    SCOPE_BOUNDARY_CONTEXT_CLASSES,
    SEMANTIC_DISPOSITIONS,
    SOURCE_REVIEW_DIMENSIONS,
    SourceAssertionReviewReceipt,
    SourceAssertionManifest,
    SourceRow,
    contains_token_bounded_source_fragment,
    load_source_assertion_review_receipt,
    normalize_exact_source_text,
    scope_boundary_source_locator,
)
from test_case_agent.review_cycle.source_row_baseline import (
    load_extraction_spec,
    load_source_row_baseline,
)
from test_case_agent.review_cycle.source_gate import (
    validate_passed_source_gate_receipt,
)


SCENARIO_ID = "reviewer.session_prepared_source_assertion"
DEFAULT_MAX_PROMPT_BYTES = 320 * 1024
DEFAULT_MAX_REVIEW_SHARDS = 8
DEFAULT_SHARD_TARGET_PROMPT_BYTES = 160 * 1024
DEFAULT_MAX_ASSERTIONS_PER_SHARD = 64
# Backward-compatible alias for handoff-local imports.  The canonical list is
# owned by test_case_agent.review_cycle.exec_events.
FORBIDDEN_ITEM_TYPES = TOOL_EVENT_ITEM_TYPES
DIRECT_TEXT_SUFFIXES = frozenset(
    {".csv", ".htm", ".html", ".json", ".md", ".tsv", ".txt", ".xhtml", ".xml", ".yaml", ".yml"}
)


def _normalize_pdf_literal_text(value: str) -> str:
    """Normalize only layout whitespace introduced around PDF punctuation."""

    normalized = normalize_exact_source_text(value)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    normalized = re.sub(r"\s*-\s*", "-", normalized)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+([),.;:])", r"\1", normalized)
    return normalized
DIRECT_IMAGE_SUFFIXES = frozenset(
    {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
)
BOUNDED_EXTRACT_VERSION = 1
BOUNDED_EXTRACT_METHODS = frozenset(
    {
        "docx-xml-literal-fragments-v1",
        "pdf-page-literal-fragments-v1",
        "utf8-literal-fragments-v1",
    }
)
MANDATORY_SCOPE_ARTIFACT_ROLES = (
    "source-row-inventory",
    "source-row-extraction-spec",
    "source-row-baseline",
    "coverage-gaps",
)


class SourceReviewerRunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class BoundedEvidenceFragment:
    source_locator: str
    exact_source_text: str
    exact_source_text_sha256: str


@dataclass(frozen=True)
class BoundedEvidenceExtract:
    descriptor_path: Path
    source_path: str
    source_sha256: str
    extraction_method: str
    fragments: tuple[BoundedEvidenceFragment, ...]


@dataclass(frozen=True)
class PreparedEvidenceSet:
    inline_files: tuple[tuple[str, str], ...]
    image_paths: tuple[Path, ...]
    bindings: tuple[Mapping[str, Any], ...]
    snapshot_sha256: Mapping[str, str]
    digest: str


@dataclass(frozen=True)
class ReviewPromptShard:
    shard_id: str
    assertion_ids: tuple[str, ...]
    prompt: str
    prompt_bytes: int
    schema: Mapping[str, Any]


@dataclass
class OutputReservations:
    owner_token: str
    lock_handles: tuple[tuple[Path, int], ...]
    model_receipt_path: Path
    delete_locks_on_close: bool
    released: bool = False

    def cleanup_model_receipt(self) -> None:
        self.model_receipt_path.unlink(missing_ok=True)

    def release(self) -> None:
        if self.released:
            return
        self.released = True
        for lock_path, descriptor in reversed(self.lock_handles):
            if self.delete_locks_on_close:
                os.close(descriptor)
                continue
            try:
                owned_stat = os.fstat(descriptor)
                try:
                    path_stat = lock_path.stat(follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if os.path.samestat(owned_stat, path_stat):
                    lock_path.unlink(missing_ok=True)
            finally:
                os.close(descriptor)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish_file_no_clobber(source: Path, destination: Path, *, label: str) -> None:
    try:
        os.link(source, destination)
    except FileExistsError as exc:
        raise SourceReviewerRunnerError(
            f"{label} appeared concurrently; refusing to overwrite: {destination}"
        ) from exc


def unlink_if_owned_hardlink(path: Path, owner_reference: Path) -> bool:
    try:
        owner_stat = owner_reference.stat(follow_symlinks=False)
        path_stat = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return False
    if not os.path.samestat(owner_stat, path_stat):
        return False
    path.unlink()
    return True


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.source-review.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        publish_file_no_clobber(
            temporary_path,
            path,
            label="source reviewer JSON output",
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def write_text(path: Path, content: str) -> None:
    """Publish one UTF-8 text artifact without clobbering another owner."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.source-review.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content.rstrip() + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        publish_file_no_clobber(
            temporary_path,
            path,
            label="source reviewer text output",
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def resolve_under(root: Path, value: Path, *, label: str) -> Path:
    root = root.resolve()
    path = value if value.is_absolute() else root / value
    path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SourceReviewerRunnerError(f"{label} must stay under repo root: {path}") from exc
    return path


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceReviewerRunnerError(f"cannot load {label} {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceReviewerRunnerError(f"{label} must be a JSON object: {path}")
    return payload


def canonical_json_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _exact_keys(payload: Mapping[str, Any], expected: set[str], *, label: str) -> None:
    actual = set(payload)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise SourceReviewerRunnerError(
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}"
        )


def _nonempty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceReviewerRunnerError(f"{label} must be non-empty text")
    return value.strip()


def _lower_sha256(value: Any, *, label: str) -> str:
    text = _nonempty_string(value, label=label)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise SourceReviewerRunnerError(f"{label} must be lowercase SHA-256")
    return text


def exact_object(properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(properties),
        "additionalProperties": False,
    }


def _selected_assertion_ids(
    manifest: SourceAssertionManifest,
    assertion_ids: Sequence[str] | None,
) -> tuple[str, ...]:
    full_ids = tuple(item.assertion_id for item in manifest.assertions)
    if assertion_ids is None:
        return full_ids
    selected = tuple(assertion_ids)
    if not selected or len(selected) != len(set(selected)):
        raise SourceReviewerRunnerError(
            "source review assertion selection must be non-empty and unique"
        )
    unknown = sorted(set(selected) - set(full_ids))
    if unknown:
        raise SourceReviewerRunnerError(
            "source review assertion selection contains unknown ids: "
            + ", ".join(unknown)
        )
    return selected


def receipt_schema(
    manifest: SourceAssertionManifest,
    *,
    assertion_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    assertion_ids = list(_selected_assertion_ids(manifest, assertion_ids))
    boundary_rows = [
        item
        for item in manifest.source_rows
        if item.source_context_class in SCOPE_BOUNDARY_CONTEXT_CLASSES
    ]
    dimensions = exact_object(
        {
            dimension: {"type": "string", "enum": ["verified", "incorrect"]}
            for dimension in SOURCE_REVIEW_DIMENSIONS
        }
    )
    assertion_review = exact_object(
        {
            "assertion_id": {"type": "string", "enum": assertion_ids},
            "approved_polarity": {
                "type": "string",
                "enum": sorted(POLARITIES),
            },
            "approved_semantic_disposition": {
                "type": "string",
                "enum": sorted(SEMANTIC_DISPOSITIONS),
            },
            "approved_execution_readiness": {
                "type": "string",
                "enum": sorted(EXECUTION_READINESS_VALUES),
            },
            "approved_risk": {"type": "string", "enum": sorted(RISKS)},
            "dimension_verdicts": dimensions,
            "verdict": {"type": "string", "enum": ["verified", "incorrect"]},
            "required_change": {"type": "string"},
            "note": {"type": "string"},
        }
    )
    inventory_review = exact_object(
        {
            "extraction_spec_digest": {
                "type": "string",
                "enum": [manifest.source_row_extraction_spec_digest],
            },
            "baseline_digest": {
                "type": "string",
                "enum": [manifest.source_row_baseline_digest],
            },
            "candidate_count": {
                "type": "integer",
                "enum": [manifest.source_row_candidate_count],
            },
            "mapped_source_row_count": {
                "type": "integer",
                "enum": [manifest.source_row_candidate_count],
            },
            "verdict": {"type": "string", "enum": ["verified", "incorrect"]},
            "required_change": {"type": "string"},
            "note": {"type": "string"},
        }
    )
    reviewed_context = exact_object(
        {
            "context_class": {
                "type": "string",
                "enum": sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES),
            },
            "source_row_id": {
                "type": "string",
                "enum": [item.source_row_id for item in boundary_rows],
            },
        }
    )
    exclusion = exact_object(
        {
            "context_class": {
                "type": "string",
                "enum": sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES),
            },
            "source_path": {
                "type": "string",
                "enum": [item.path for item in manifest.sources],
            },
            "source_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "source_locator": {"type": "string"},
            "exact_source_text": {"type": "string"},
            "reason": {"type": "string"},
        }
    )
    boundary_review = exact_object(
        {
            "verdict": {"type": "string", "enum": ["verified", "incorrect"]},
            "checked_context_classes": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES),
                },
                "minItems": len(SCOPE_BOUNDARY_CONTEXT_CLASSES),
                "maxItems": len(SCOPE_BOUNDARY_CONTEXT_CLASSES),
            },
            "reviewed_manifest_contexts": {
                "type": "array",
                "items": reviewed_context,
                "minItems": len(boundary_rows),
                "maxItems": len(boundary_rows),
            },
            "excluded_contexts": {"type": "array", "items": exclusion},
            "required_change": {"type": "string"},
            "note": {"type": "string"},
        }
    )
    return exact_object(
        {
            "version": {"type": "integer", "enum": [REVIEW_RECEIPT_VERSION]},
            "manifest_digest": {"type": "string", "enum": [manifest.digest]},
            "decision": {
                "type": "string",
                "enum": ["accepted", "changes-required"],
            },
            "assertion_reviews": {
                "type": "array",
                "items": assertion_review,
                "minItems": len(assertion_ids),
                "maxItems": len(assertion_ids),
            },
            "source_inventory_review": inventory_review,
            "scope_boundary_review": boundary_review,
        }
    )


def verify_source_gate(
    gate_path: Path,
    *,
    manifest: SourceAssertionManifest,
) -> dict[str, Any]:
    gate = load_json_object(gate_path, label="source gate receipt")
    try:
        validate_passed_source_gate_receipt(gate, manifest=manifest)
    except ValueError as exc:
        raise SourceReviewerRunnerError(str(exc)) from exc
    return gate


def _clean_markdown_cell(value: str) -> str:
    result = value.strip()
    if len(result) >= 2 and result.startswith("`") and result.endswith("`"):
        result = result[1:-1].strip()
    return result


def _markdown_tables(path: Path) -> list[list[dict[str, str]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise SourceReviewerRunnerError(
            f"cannot read source-row inventory {path}: {exc}"
        ) from exc
    tables: list[list[dict[str, str]]] = []
    index = 0
    while index + 1 < len(lines):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (
            header.startswith("|")
            and separator.startswith("|")
            and "---" in separator
        ):
            index += 1
            continue
        columns = [
            _clean_markdown_cell(item) for item in header.strip("|").split("|")
        ]
        if len(columns) != len(set(columns)):
            raise SourceReviewerRunnerError(
                f"source-row inventory table has duplicate columns: {path}"
            )
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = [
                _clean_markdown_cell(item)
                for item in lines[index].strip().strip("|").split("|")
            ]
            if len(cells) != len(columns):
                raise SourceReviewerRunnerError(
                    f"source-row inventory row {index + 1} has {len(cells)} cells "
                    f"for {len(columns)} columns"
                )
            rows.append(dict(zip(columns, cells)))
            index += 1
        tables.append(rows)
    return tables


def load_source_row_inventory(path: Path) -> tuple[SourceRow, ...]:
    required = {
        "source_row_id",
        "in_scope",
        "source_path",
        "source_locator",
        "bounded_source_text",
        "source_context_class",
        "requirement_codes",
        "candidate_id",
    }
    table = next(
        (
            rows
            for rows in _markdown_tables(path)
            if rows and required <= set(rows[0])
        ),
        None,
    )
    if table is None:
        raise SourceReviewerRunnerError(
            "source-row inventory is missing the typed source-first registry table"
        )
    result: list[SourceRow] = []
    for raw in table:
        disposition = raw["in_scope"].strip().casefold()
        if disposition in {"yes", "true"}:
            scope_disposition = "yes"
        elif disposition in {"unclear", "ambiguous"}:
            scope_disposition = "unclear"
        elif disposition in {"no", "false", "out-of-scope", "not-applicable"}:
            scope_disposition = "no"
        else:
            raise SourceReviewerRunnerError(
                "source-row inventory in_scope must be yes, unclear or no: "
                + raw["source_row_id"]
            )
        raw_codes = raw["requirement_codes"].strip()
        requirement_codes = (
            []
            if raw_codes == "none_required"
            else [item.strip().strip("`") for item in raw_codes.split(";")]
        )
        if any(not item for item in requirement_codes):
            raise SourceReviewerRunnerError(
                "source-row inventory has an empty requirement code: "
                + raw["source_row_id"]
            )
        raw_candidate = raw["candidate_id"].strip().strip("`").strip()
        candidate_id = None if raw_candidate == "none_required" else raw_candidate
        result.append(
            SourceRow.from_dict(
                {
                    "source_row_id": raw["source_row_id"],
                    "source_path": raw["source_path"],
                    "source_locator": raw["source_locator"],
                    "bounded_source_text": raw["bounded_source_text"],
                    "source_context_class": raw["source_context_class"],
                    "scope_disposition": scope_disposition,
                    "requirement_codes": requirement_codes,
                    "candidate_id": candidate_id,
                }
            )
        )
    ids = [item.source_row_id for item in result]
    if not result or len(ids) != len(set(ids)):
        raise SourceReviewerRunnerError(
            "source-row inventory must contain a non-empty, duplicate-free row set"
        )
    return tuple(result)


def verify_scope_artifacts(
    *,
    manifest: SourceAssertionManifest,
    inventory_path: Path,
    extraction_spec_path: Path,
    baseline_path: Path,
) -> None:
    inventory_rows = load_source_row_inventory(inventory_path)
    actual_rows = {item.source_row_id: item.to_dict() for item in inventory_rows}
    expected_rows = {item.source_row_id: item.to_dict() for item in manifest.source_rows}
    if actual_rows != expected_rows:
        missing = sorted(set(expected_rows) - set(actual_rows))
        extra = sorted(set(actual_rows) - set(expected_rows))
        changed = sorted(
            row_id
            for row_id in set(actual_rows) & set(expected_rows)
            if actual_rows[row_id] != expected_rows[row_id]
        )
        raise SourceReviewerRunnerError(
            "source-row inventory does not exactly match manifest.source_rows: "
            f"missing={missing or 'none'}, extra={extra or 'none'}, "
            f"changed={changed or 'none'}"
        )
    try:
        extraction_spec = load_extraction_spec(extraction_spec_path)
        baseline = load_source_row_baseline(baseline_path)
    except Exception as exc:  # noqa: BLE001 - normalize the source-baseline contract.
        raise SourceReviewerRunnerError(
            f"cannot load mandatory source-row baseline artifacts: {exc}"
        ) from exc
    if extraction_spec.digest != manifest.source_row_extraction_spec_digest:
        raise SourceReviewerRunnerError(
            "source-row extraction spec digest does not match the manifest"
        )
    if baseline.digest != manifest.source_row_baseline_digest:
        raise SourceReviewerRunnerError(
            "source-row baseline digest does not match the manifest"
        )
    if baseline.extraction_spec_sha256 != extraction_spec.digest:
        raise SourceReviewerRunnerError(
            "source-row baseline does not bind the supplied extraction spec"
        )
    if len(baseline.candidates) != manifest.source_row_candidate_count:
        raise SourceReviewerRunnerError(
            "source-row baseline candidate count does not match the manifest"
        )
    baseline_candidates = {
        item.candidate_id: item.to_dict() for item in baseline.candidates
    }
    mapped_rows = {
        item.candidate_id: item
        for item in manifest.source_rows
        if item.candidate_id is not None
    }
    if set(baseline_candidates) != set(mapped_rows):
        missing = sorted(set(baseline_candidates) - set(mapped_rows))
        extra = sorted(set(mapped_rows) - set(baseline_candidates))
        raise SourceReviewerRunnerError(
            "source-row baseline candidate-id bijection mismatch: "
            f"unmapped_baseline={missing or 'none'}, unknown_manifest={extra or 'none'}"
        )
    changed: list[str] = []
    for candidate_id, row in mapped_rows.items():
        candidate = baseline_candidates[candidate_id]
        if (
            candidate["canonical_xpath"] != row.source_locator
            or candidate["bounded_source_text"] != row.bounded_source_text
            or candidate["source_context_class"] != row.source_context_class
            or baseline.selected_xhtml.relative_path != row.source_path
        ):
            changed.append(candidate_id)
    if changed:
        raise SourceReviewerRunnerError(
            "source-row baseline candidate mapping differs from manifest rows: "
            + ", ".join(sorted(changed))
        )


def _docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            document = archive.read("word/document.xml")
        root = ElementTree.fromstring(document)
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise SourceReviewerRunnerError(
            f"cannot deterministically extract DOCX text from {path}: {exc}"
        ) from exc
    paragraphs: list[str] = []
    for paragraph in root.iter():
        if paragraph.tag.rsplit("}", 1)[-1] != "p":
            continue
        text = "".join(
            node.text or ""
            for node in paragraph.iter()
            if node.tag.rsplit("}", 1)[-1] == "t"
        )
        if text.strip():
            paragraphs.append(text)
    return normalize_exact_source_text("\n".join(paragraphs))


def _pdf_page_text(path: Path, page_number: int) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        if page_number < 1 or page_number > len(reader.pages):
            raise SourceReviewerRunnerError(
                f"PDF bounded extract page is out of range: {path} page:{page_number}"
            )
        return normalize_exact_source_text(
            reader.pages[page_number - 1].extract_text() or ""
        )
    except SourceReviewerRunnerError:
        raise
    except Exception as exc:  # noqa: BLE001 - optional PDF backend normalized here.
        raise SourceReviewerRunnerError(
            f"cannot deterministically extract PDF text from {path}: {exc}"
        ) from exc


def load_bounded_evidence_extract(
    descriptor_path: Path,
    *,
    root: Path,
) -> BoundedEvidenceExtract:
    payload = load_json_object(descriptor_path, label="bounded evidence extract")
    _exact_keys(
        payload,
        {"version", "source_path", "source_sha256", "extraction_method", "fragments"},
        label="bounded evidence extract",
    )
    if type(payload["version"]) is not int or payload["version"] != BOUNDED_EXTRACT_VERSION:
        raise SourceReviewerRunnerError(
            f"bounded evidence extract.version must equal {BOUNDED_EXTRACT_VERSION}"
        )
    source_path = _nonempty_string(payload["source_path"], label="bounded extract source_path")
    if "\\" in source_path or source_path.startswith("/") or ".." in Path(source_path).parts:
        raise SourceReviewerRunnerError(
            "bounded extract source_path must be a normalized repository-relative POSIX path"
        )
    source_file = resolve_under(root, Path(source_path), label="bounded extract source_path")
    source_sha256 = _lower_sha256(
        payload["source_sha256"], label="bounded extract source_sha256"
    )
    if sha256_file(source_file) != source_sha256:
        raise SourceReviewerRunnerError(
            "bounded extract source_sha256 does not match current source bytes: "
            + source_path
        )
    extraction_method = _nonempty_string(
        payload["extraction_method"], label="bounded extract extraction_method"
    )
    if extraction_method not in BOUNDED_EXTRACT_METHODS:
        raise SourceReviewerRunnerError(
            "bounded extract extraction_method must be one of "
            + ", ".join(sorted(BOUNDED_EXTRACT_METHODS))
        )
    fragments_payload = payload["fragments"]
    if not isinstance(fragments_payload, list) or not fragments_payload:
        raise SourceReviewerRunnerError(
            "bounded evidence extract.fragments must be a non-empty array"
        )
    fragments: list[BoundedEvidenceFragment] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(fragments_payload):
        if not isinstance(item, Mapping):
            raise SourceReviewerRunnerError(
                f"bounded evidence extract.fragments[{index}] must be an object"
            )
        _exact_keys(
            item,
            {"source_locator", "exact_source_text", "exact_source_text_sha256"},
            label=f"bounded evidence extract.fragments[{index}]",
        )
        locator = _nonempty_string(
            item["source_locator"], label=f"bounded extract fragment {index} locator"
        )
        exact_text = _nonempty_string(
            item["exact_source_text"], label=f"bounded extract fragment {index} text"
        )
        exact_sha = _lower_sha256(
            item["exact_source_text_sha256"],
            label=f"bounded extract fragment {index} text SHA-256",
        )
        if hashlib.sha256(exact_text.encode("utf-8")).hexdigest() != exact_sha:
            raise SourceReviewerRunnerError(
                f"bounded extract fragment {index} text SHA-256 mismatch"
            )
        key = (locator, exact_sha)
        if key in seen:
            raise SourceReviewerRunnerError(
                "bounded evidence extract contains a duplicate locator/text binding"
            )
        seen.add(key)
        fragments.append(
            BoundedEvidenceFragment(
                source_locator=locator,
                exact_source_text=exact_text,
                exact_source_text_sha256=exact_sha,
            )
        )

    suffix = source_file.suffix.casefold()
    if extraction_method == "pdf-page-literal-fragments-v1":
        if suffix != ".pdf":
            raise SourceReviewerRunnerError(
                "pdf-page-literal-fragments-v1 requires a .pdf registered source"
            )
        page_cache: dict[int, str] = {}
        for fragment in fragments:
            if not fragment.source_locator.startswith("page:"):
                raise SourceReviewerRunnerError(
                    "PDF bounded extract locator must use page:<positive-integer>"
                )
            try:
                page_number = int(fragment.source_locator.removeprefix("page:"))
            except ValueError as exc:
                raise SourceReviewerRunnerError(
                    "PDF bounded extract locator must use page:<positive-integer>"
                ) from exc
            page_text = page_cache.setdefault(
                page_number, _pdf_page_text(source_file, page_number)
            )
            if _normalize_pdf_literal_text(
                fragment.exact_source_text
            ) not in _normalize_pdf_literal_text(page_text):
                raise SourceReviewerRunnerError(
                    "bounded PDF fragment is absent from its registered page: "
                    f"{source_path}#{fragment.source_locator}"
                )
    elif extraction_method == "docx-xml-literal-fragments-v1":
        if suffix != ".docx":
            raise SourceReviewerRunnerError(
                "docx-xml-literal-fragments-v1 requires a .docx registered source"
            )
        document_text = _docx_text(source_file)
        for fragment in fragments:
            if normalize_exact_source_text(fragment.exact_source_text) not in document_text:
                raise SourceReviewerRunnerError(
                    "bounded DOCX fragment is absent from registered document bytes: "
                    + source_path
                )
    else:
        if suffix not in DIRECT_TEXT_SUFFIXES:
            raise SourceReviewerRunnerError(
                "utf8-literal-fragments-v1 requires a supported UTF-8 text source"
            )
        try:
            source_text = normalize_exact_source_text(
                source_file.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError) as exc:
            raise SourceReviewerRunnerError(
                f"cannot read bounded UTF-8 source {source_path}: {exc}"
            ) from exc
        for fragment in fragments:
            if normalize_exact_source_text(fragment.exact_source_text) not in source_text:
                raise SourceReviewerRunnerError(
                    "bounded UTF-8 fragment is absent from registered source bytes: "
                    + source_path
                )
    return BoundedEvidenceExtract(
        descriptor_path=descriptor_path,
        source_path=source_path,
        source_sha256=source_sha256,
        extraction_method=extraction_method,
        fragments=tuple(fragments),
    )


def prepare_evidence_set(
    *,
    root: Path,
    manifest: SourceAssertionManifest,
    inventory_path: Path,
    extraction_spec_path: Path,
    baseline_path: Path,
    bounded_extract_paths: Sequence[Path],
    max_direct_file_bytes: int,
) -> PreparedEvidenceSet:
    root = root.resolve()
    inventory_path = resolve_under(
        root, inventory_path, label="source_row_inventory"
    )
    extraction_spec_path = resolve_under(
        root, extraction_spec_path, label="source_row_extraction_spec"
    )
    baseline_path = resolve_under(root, baseline_path, label="source_row_baseline")
    bounded_extract_paths = tuple(
        resolve_under(root, path, label="bounded_extract")
        for path in bounded_extract_paths
    )
    if max_direct_file_bytes <= 0:
        raise SourceReviewerRunnerError("max_direct_file_bytes must be positive")
    coverage_gaps_path = resolve_under(
        root,
        Path(manifest.coverage_gaps_artifact.path),
        label="coverage_gaps_artifact",
    )
    mandatory_paths = {
        "source-row-inventory": inventory_path,
        "source-row-extraction-spec": extraction_spec_path,
        "source-row-baseline": baseline_path,
        "coverage-gaps": coverage_gaps_path,
    }
    resolved_mandatory = [path.resolve() for path in mandatory_paths.values()]
    if len(resolved_mandatory) != len(set(resolved_mandatory)):
        raise SourceReviewerRunnerError(
            "mandatory source reviewer scope artifacts must be four distinct files"
        )
    verify_scope_artifacts(
        manifest=manifest,
        inventory_path=inventory_path,
        extraction_spec_path=extraction_spec_path,
        baseline_path=baseline_path,
    )
    if sha256_file(coverage_gaps_path) != manifest.coverage_gaps_artifact.sha256:
        raise SourceReviewerRunnerError(
            "coverage gaps artifact bytes do not match the manifest"
        )

    descriptor_paths = [path.resolve() for path in bounded_extract_paths]
    if len(descriptor_paths) != len(set(descriptor_paths)):
        raise SourceReviewerRunnerError(
            "bounded extract descriptor paths must not contain duplicates"
        )
    extracts: dict[str, BoundedEvidenceExtract] = {}
    for descriptor_path in descriptor_paths:
        extract = load_bounded_evidence_extract(descriptor_path, root=root)
        if extract.source_path in extracts:
            raise SourceReviewerRunnerError(
                "one registered evidence source may have exactly one bounded extract: "
                + extract.source_path
            )
        extracts[extract.source_path] = extract

    registered_sources = {item.path: item.sha256 for item in manifest.sources}
    registered_evidence = {
        item.path: (item.sha256, item.role) for item in manifest.evidence_sources
    }
    registered_mockups = {item.path: item.sha256 for item in manifest.mockups}
    registry_overlaps = sorted(
        (set(registered_sources) & set(registered_evidence))
        | (set(registered_sources) & set(registered_mockups))
        | (set(registered_evidence) & set(registered_mockups))
    )
    if registry_overlaps:
        raise SourceReviewerRunnerError(
            "one path cannot occupy multiple manifest evidence registries: "
            + ", ".join(registry_overlaps)
        )
    all_registered_paths = (
        set(registered_sources) | set(registered_evidence) | set(registered_mockups)
    )
    mandatory_relative_paths = {
        path.relative_to(root).as_posix() for path in mandatory_paths.values()
    }
    mandatory_registry_overlaps = sorted(
        mandatory_relative_paths & all_registered_paths
    )
    if mandatory_registry_overlaps:
        raise SourceReviewerRunnerError(
            "mandatory scope artifacts cannot also be registered source/evidence/mockup "
            "subjects: " + ", ".join(mandatory_registry_overlaps)
        )
    unknown_extracts = sorted(
        set(extracts) - set(registered_evidence) - set(registered_sources)
    )
    if unknown_extracts:
        raise SourceReviewerRunnerError(
            "bounded extracts may represent only manifest evidence/source subjects; "
            "unregistered/duplicate-mode subjects=" + ", ".join(unknown_extracts)
        )

    inline_files: list[tuple[str, str]] = []
    image_paths: list[Path] = []
    bindings: list[Mapping[str, Any]] = []
    snapshots: dict[str, str] = {}

    def snapshot(path: Path) -> tuple[str, str]:
        relative = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        snapshots[relative] = digest
        return relative, digest

    for role in MANDATORY_SCOPE_ARTIFACT_ROLES:
        path = mandatory_paths[role]
        relative, digest = snapshot(path)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise SourceReviewerRunnerError(
                f"mandatory scope artifact must be UTF-8 text: {relative}: {exc}"
            ) from exc
        inline_files.append((relative, content))
        bindings.append(
            {
                "subject_kind": "mandatory-scope-artifact",
                "subject_path": relative,
                "subject_sha256": digest,
                "role": role,
                "representation_mode": "direct-utf8",
                "representation_path": relative,
                "representation_sha256": digest,
            }
        )

    rows_by_source: dict[str, list[SourceRow]] = {}
    for row in manifest.source_rows:
        rows_by_source.setdefault(row.source_path, []).append(row)
    represented_boundary_classes = {
        row.source_context_class
        for row in manifest.source_rows
        if row.source_context_class in SCOPE_BOUNDARY_CONTEXT_CLASSES
    }
    missing_boundary_classes = sorted(
        SCOPE_BOUNDARY_CONTEXT_CLASSES - represented_boundary_classes
    )
    boundary_exclusion_candidate_count = 0
    boundary_exclusion_locators: set[str] = set()
    for source_path, expected_sha in registered_sources.items():
        path = resolve_under(root, Path(source_path), label="manifest source")
        relative, digest = snapshot(path)
        if digest != expected_sha:
            raise SourceReviewerRunnerError(
                "manifest source bytes changed before review: " + source_path
            )
        rows = rows_by_source.get(source_path, [])
        if not rows:
            raise SourceReviewerRunnerError(
                "manifest source has no runner-owned bounded source-row evidence: "
                + source_path
            )
        source_extract = extracts.get(source_path)
        boundary_candidates: list[dict[str, str]] = []
        descriptor_relative: str | None = None
        descriptor_digest: str | None = None
        bounded_extract_disposition = "not-provided"
        if source_extract is not None:
            descriptor_relative, descriptor_digest = snapshot(
                source_extract.descriptor_path
            )
            candidate_fragments: list[BoundedEvidenceFragment] = []
            covered_fragment_count = 0
            if not missing_boundary_classes:
                for fragment in source_extract.fragments:
                    normalized_fragment = normalize_exact_source_text(
                        fragment.exact_source_text
                    )
                    covered = any(
                        contains_token_bounded_source_fragment(
                            normalize_exact_source_text(row.bounded_source_text),
                            normalized_fragment,
                        )
                        or contains_token_bounded_source_fragment(
                            normalized_fragment,
                            normalize_exact_source_text(row.bounded_source_text),
                        )
                        for row in rows
                    )
                    if covered:
                        covered_fragment_count += 1
                    else:
                        candidate_fragments.append(fragment)
            else:
                candidate_fragments.extend(source_extract.fragments)
            for fragment in candidate_fragments:
                normalized_fragment = normalize_exact_source_text(
                    fragment.exact_source_text
                )
                if missing_boundary_classes and any(
                    contains_token_bounded_source_fragment(
                        normalize_exact_source_text(row.bounded_source_text),
                        normalized_fragment,
                    )
                    or contains_token_bounded_source_fragment(
                        normalized_fragment,
                        normalize_exact_source_text(row.bounded_source_text),
                    )
                    for row in manifest.source_rows
                    if row.source_path == source_path
                ):
                    raise SourceReviewerRunnerError(
                        "boundary exclusion extract candidate overlaps a manifest "
                        "source row: " + source_path
                    )
                canonical_locator = scope_boundary_source_locator(
                    source_path,
                    fragment.exact_source_text,
                )
                if canonical_locator in boundary_exclusion_locators:
                    raise SourceReviewerRunnerError(
                        "boundary exclusion extract candidates must have unique canonical "
                        "locators across all manifest sources"
                    )
                boundary_exclusion_locators.add(canonical_locator)
                boundary_candidates.append(
                    {
                        "source_path": source_path,
                        "source_sha256": digest,
                        "extract_locator": fragment.source_locator,
                        "canonical_exclusion_locator": canonical_locator,
                        "exact_source_text": fragment.exact_source_text,
                        "exact_source_text_sha256": (
                            fragment.exact_source_text_sha256
                        ),
                    }
                )
            boundary_exclusion_candidate_count += len(boundary_candidates)
            if boundary_candidates and covered_fragment_count:
                bounded_extract_disposition = (
                    "mixed-covered-and-boundary-exclusion-candidates"
                )
            elif boundary_candidates:
                bounded_extract_disposition = "boundary-exclusion-candidates"
            else:
                bounded_extract_disposition = "redundant-covered-by-manifest-rows"
        binding_payload = {
            "source_path": source_path,
            "source_sha256": digest,
            "source_rows": [item.to_dict() for item in rows],
            "missing_boundary_context_classes": missing_boundary_classes,
            "source_verified_boundary_exclusion_candidates": boundary_candidates,
        }
        virtual_path = f"runner://manifest-source-rows/{source_path}"
        inline_files.append(
            (
                virtual_path,
                json.dumps(binding_payload, ensure_ascii=False, indent=2) + "\n",
            )
        )
        bindings.append(
            {
                "subject_kind": "manifest-source",
                "subject_path": relative,
                "subject_sha256": digest,
                "role": "assertion-source",
                "representation_mode": (
                    "manifest-validated-source-rows+boundary-extract"
                    if boundary_candidates
                    else (
                        "manifest-validated-source-rows+covered-extract"
                        if bounded_extract_disposition
                        == "redundant-covered-by-manifest-rows"
                        else "manifest-validated-source-rows"
                    )
                ),
                "representation_path": virtual_path,
                "representation_sha256": canonical_json_sha256(binding_payload),
                "source_row_ids": [item.source_row_id for item in rows],
                "bounded_extract_descriptor_path": descriptor_relative,
                "bounded_extract_descriptor_sha256": descriptor_digest,
                "bounded_extract_disposition": bounded_extract_disposition,
                "boundary_exclusion_candidate_count": len(boundary_candidates),
            }
        )

    if missing_boundary_classes:
        if boundary_exclusion_candidate_count < len(missing_boundary_classes):
            raise SourceReviewerRunnerError(
                "each boundary class with zero manifest rows requires a distinct, "
                "source-verified exclusion candidate; missing_classes="
                + ", ".join(missing_boundary_classes)
            )

    for source_path, (expected_sha, evidence_role) in registered_evidence.items():
        path = resolve_under(root, Path(source_path), label="manifest evidence source")
        relative, digest = snapshot(path)
        if digest != expected_sha:
            raise SourceReviewerRunnerError(
                "manifest evidence source bytes changed before review: " + source_path
            )
        extract = extracts.get(source_path)
        suffix = path.suffix.casefold()
        if extract is not None:
            if extract.source_sha256 != digest:
                raise SourceReviewerRunnerError(
                    "bounded extract does not bind current manifest evidence bytes: "
                    + source_path
                )
            descriptor_relative, descriptor_digest = snapshot(extract.descriptor_path)
            rendered = {
                "source_path": source_path,
                "source_sha256": digest,
                "extraction_method": extract.extraction_method,
                "fragments": [
                    {
                        "source_locator": item.source_locator,
                        "exact_source_text": item.exact_source_text,
                        "exact_source_text_sha256": item.exact_source_text_sha256,
                    }
                    for item in extract.fragments
                ],
            }
            inline_files.append(
                (
                    descriptor_relative,
                    json.dumps(rendered, ensure_ascii=False, indent=2) + "\n",
                )
            )
            bindings.append(
                {
                    "subject_kind": "manifest-evidence-source",
                    "subject_path": relative,
                    "subject_sha256": digest,
                    "role": evidence_role,
                    "representation_mode": "source-verified-bounded-extract",
                    "representation_path": descriptor_relative,
                    "representation_sha256": descriptor_digest,
                    "fragment_count": len(extract.fragments),
                }
            )
        elif suffix in DIRECT_TEXT_SUFFIXES:
            if path.stat().st_size > max_direct_file_bytes:
                raise SourceReviewerRunnerError(
                    "registered UTF-8 evidence source exceeds direct-file cap and "
                    "requires one source-verified bounded extract: " + source_path
                )
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise SourceReviewerRunnerError(
                    f"cannot read registered UTF-8 evidence source {source_path}: {exc}"
                ) from exc
            inline_files.append((relative, content))
            bindings.append(
                {
                    "subject_kind": "manifest-evidence-source",
                    "subject_path": relative,
                    "subject_sha256": digest,
                    "role": evidence_role,
                    "representation_mode": "direct-utf8",
                    "representation_path": relative,
                    "representation_sha256": digest,
                }
            )
        elif suffix in DIRECT_IMAGE_SUFFIXES:
            image_paths.append(path)
            bindings.append(
                {
                    "subject_kind": "manifest-evidence-source",
                    "subject_path": relative,
                    "subject_sha256": digest,
                    "role": evidence_role,
                    "representation_mode": "direct-image-attachment",
                    "representation_path": relative,
                    "representation_sha256": digest,
                }
            )
        else:
            raise SourceReviewerRunnerError(
                "registered non-text evidence source requires one source-verified "
                "bounded extract: " + source_path
            )

    for mockup_path, expected_sha in registered_mockups.items():
        path = resolve_under(root, Path(mockup_path), label="manifest mockup")
        relative, digest = snapshot(path)
        if digest != expected_sha:
            raise SourceReviewerRunnerError(
                "manifest mockup bytes changed before review: " + mockup_path
            )
        if path.suffix.casefold() not in DIRECT_IMAGE_SUFFIXES:
            raise SourceReviewerRunnerError(
                "manifest mockups must be direct supported image attachments: "
                + mockup_path
            )
        image_paths.append(path)
        bindings.append(
            {
                "subject_kind": "manifest-mockup",
                "subject_path": relative,
                "subject_sha256": digest,
                "role": "mockup",
                "representation_mode": "direct-image-attachment",
                "representation_path": relative,
                "representation_sha256": digest,
            }
        )

    represented_registered_paths = {
        str(item["subject_path"])
        for item in bindings
        if item["subject_kind"]
        in {"manifest-source", "manifest-evidence-source", "manifest-mockup"}
    }
    if represented_registered_paths != all_registered_paths:
        missing = sorted(all_registered_paths - represented_registered_paths)
        extra = sorted(represented_registered_paths - all_registered_paths)
        raise SourceReviewerRunnerError(
            "runner evidence registry coverage mismatch: "
            f"missing={missing or 'none'}, extra={extra or 'none'}"
        )
    descriptor_subjects = set(extracts)
    bounded_binding_subjects = {
        str(item["subject_path"])
        for item in bindings
        if item["representation_mode"]
        in {
                "source-verified-bounded-extract",
                "manifest-validated-source-rows+boundary-extract",
                "manifest-validated-source-rows+covered-extract",
            }
    }
    if descriptor_subjects != bounded_binding_subjects:
        raise SourceReviewerRunnerError(
            "bounded extract descriptors must map one-to-one to bounded evidence bindings"
        )
    evidence_digest = canonical_json_sha256(bindings)
    return PreparedEvidenceSet(
        inline_files=tuple(inline_files),
        image_paths=tuple(image_paths),
        bindings=tuple(bindings),
        snapshot_sha256=snapshots,
        digest=evidence_digest,
    )


def assert_evidence_unchanged(root: Path, evidence: PreparedEvidenceSet) -> None:
    changed = []
    for relative, expected_sha in evidence.snapshot_sha256.items():
        path = resolve_under(root, Path(relative), label="snapshotted evidence")
        if sha256_file(path) != expected_sha:
            changed.append(relative)
    if changed:
        raise SourceReviewerRunnerError(
            "source reviewer evidence changed during the model call: "
            + ", ".join(sorted(changed))
        )


def assert_file_snapshot_unchanged(
    root: Path,
    snapshot_sha256: Mapping[str, str],
    *,
    label: str,
) -> None:
    changed = []
    for relative, expected_sha in snapshot_sha256.items():
        path = resolve_under(root, Path(relative), label=label)
        if sha256_file(path) != expected_sha:
            changed.append(relative)
    if changed:
        raise SourceReviewerRunnerError(
            f"{label} changed after its runner-owned snapshot: "
            + ", ".join(sorted(changed))
        )


def instruction_context(root: Path) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    resolved = resolve_instruction_context(root=root, scenario_id=SCENARIO_ID)
    if resolved["budget"]["status"] != "pass" or resolved["missing"]:
        raise SourceReviewerRunnerError(
            "prepared source reviewer instruction context failed its budget/missing-file gate"
        )
    files: list[tuple[str, str]] = []
    for item in resolved["files"]:
        rel = item["path"]
        raw = (root / rel).read_bytes()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceReviewerRunnerError(
                f"prepared source reviewer instruction must be UTF-8: {rel}: {exc}"
            ) from exc
        files.append((rel, content))
    return resolved, files


def reviewer_transport_basis_json(
    manifest: SourceAssertionManifest,
    *,
    assertion_ids: Sequence[str] | None = None,
) -> str:
    """Render a lossless-for-review projection without gate-verified duplication."""

    selected_ids = set(_selected_assertion_ids(manifest, assertion_ids))

    payload = {
        "contract": "source-assertion-reviewer-transport-v2",
        "manifest_digest": manifest.digest,
        "scope_slug": manifest.scope_slug,
        "source_row_extraction_spec_digest": (
            manifest.source_row_extraction_spec_digest
        ),
        "source_row_baseline_digest": manifest.source_row_baseline_digest,
        "source_row_candidate_count": manifest.source_row_candidate_count,
        "source_row_evidence_mode": "runner-inline-manifest-source-rows",
        "transport_legend": {
            "requirement_code_evidence": [
                "requirement_code",
                "source_row_id",
                "provenance_role",
                "exact_source_fragment",
                "evidence_source_path",
                "evidence_locator",
            ],
            "clause_evidence": [
                "clause_kind",
                "clause_index",
                "source_row_id",
                "exact_source_fragment",
            ],
            "supporting_evidence": [
                "source_row_id",
                "evidence_role",
                "exact_source_fragment",
            ],
            "clarification_evidence": [
                "clarification_id",
                "clause_kind",
                "clause_index",
                "requirement_codes",
                "exact_answer_sha256",
                "binding_scope",
                "source_row_ids",
            ],
        },
        "omitted_gate_verified_fields": [
            "source_path",
            "source_context_class",
            "locator",
            "exact_source_text",
            "execution_readiness_rationale",
            "atom_id",
            "obligation_ids",
        ],
        "assertions": [],
        "clarifications": [item.to_dict() for item in manifest.clarifications],
    }
    for item in manifest.assertions:
        if item.assertion_id not in selected_ids:
            continue
        assertion = {
            "assertion_id": item.assertion_id,
            "source_row_id": item.source_row_id,
            "canonical_statement": item.canonical_statement,
            "polarity": item.polarity,
            "semantic_disposition": item.semantic_disposition,
            "execution_readiness": item.execution_readiness,
            "risk": item.risk,
            "condition_clauses": list(item.condition_clauses),
            "action_clauses": list(item.action_clauses),
            "oracle_clauses": list(item.oracle_clauses),
            "requirement_codes": list(item.requirement_codes),
            "requirement_code_evidence": [
                [
                    binding.requirement_code,
                    binding.source_row_id,
                    binding.provenance_role,
                    binding.exact_source_fragment,
                    binding.evidence_source_path,
                    binding.evidence_locator,
                ]
                for binding in item.requirement_code_bindings
            ],
            "clause_evidence": [
                [
                    binding.clause_kind,
                    binding.clause_index,
                    binding.source_row_id,
                    binding.exact_source_fragment,
                ]
                for binding in item.clause_evidence_bindings
            ],
            "execution_dependency_gap_ids": list(
                item.execution_dependency_gap_ids
            ),
            "primary_gap_id": item.primary_gap_id,
            "supporting_evidence": [
                [
                    binding.source_row_id,
                    binding.evidence_role,
                    binding.exact_source_fragment,
                ]
                for binding in item.supporting_source_bindings
            ],
            "clarification_evidence": [
                [
                    binding.clarification_id,
                    binding.clause_kind,
                    binding.clause_index,
                    list(binding.requirement_codes),
                    binding.exact_answer_sha256,
                    binding.binding_scope,
                    list(binding.source_row_ids),
                ]
                for binding in item.clarification_clause_bindings
            ],
        }
        if item.semantic_disposition != "testable" and item.disposition_rationale:
            assertion["disposition_rationale"] = item.disposition_rationale
        payload["assertions"].append(assertion)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def render_prompt(
    *,
    manifest: SourceAssertionManifest,
    gate: Mapping[str, Any],
    instruction_files: Sequence[tuple[str, str]],
    review_prompt: str,
    evidence: PreparedEvidenceSet,
    assertion_ids: Sequence[str] | None = None,
    shard_id: str | None = None,
    shard_count: int | None = None,
) -> str:
    selected_ids = _selected_assertion_ids(manifest, assertion_ids)
    is_shard = len(selected_ids) != len(manifest.assertions)
    if is_shard and (not shard_id or type(shard_count) is not int or shard_count < 2):
        raise SourceReviewerRunnerError(
            "partial source review prompt requires a shard id and shard_count >= 2"
        )
    parts = [
        "# Runner-owned independent source assertion review\n\n"
        "Use only the inline instruction and evidence blocks below. Do not call tools, "
        "read files, run commands, browse, modify artifacts, or validate your own output. "
        "Review every assertion independently and return exactly one JSON receipt v6. "
        "If any dimension is incorrect, return changes-required; never repair the manifest. "
        "The scope-specific prompt is procedural context, not semantic evidence. Treat only "
        "the exact runner evidence registry, verified inline blocks and attached registered "
        "mockup images as evidence.\n\n"
        "Canonical calibration semantics: an assertion whose linked OBL is recorded in the "
        "negative or requiredness oracle inventory as decision=candidate_tc_required and "
        "gap_id=none_required is intentionally ready for downstream candidate-TC authorship, "
        "not calibrated UI execution. The unknown trigger or exact UI reaction is already "
        "preserved by its analyst question and candidate-ui-calibration marker; do not mark "
        "condition, action, oracle, gap-routing, execution-readiness or execution-dependencies "
        "incorrect solely for that known calibration need.\n\n"
        "Binary optionality semantics: a typed optionality cell for a source-typed "
        "two-state logical switch/checkbox with an explicit source-backed Да/Нет default "
        "does not imply a third empty state. Its dedicated candidate may instead preserve "
        "the default and prove that no separate activation/change is required while the "
        "exact confirmation UI response remains calibrated. Do not require an invented "
        "empty state or dependency-block that candidate solely because it uses the default.\n\n"
        "Mixed-observability semantics: one coded source statement may contain both an "
        "observable product effect and an internal-only effect for which the registered "
        "evidence set has no authorized observation interface. The requirement code may be "
        "owned by the executable observable sibling while a separate code-less not-applicable "
        "sibling preserves the exact internal fragment through a non-blocking "
        "missing-observation-interface gap. Do not require duplicate requirement-code ownership, "
        "remove that gap, or invent an API/model/database oracle solely because both siblings "
        "come from one coded source row. For a code-less not-applicable sibling, the canonical "
        "explicit routing is the hash-bound scope-coverage-gaps artifact row with matching "
        "affected_assertion_id and affected_atom_id. Its primary_gap_id and execution dependency "
        "gap fields intentionally remain empty under the manifest-v4 contract; do not demand "
        "those forbidden duplicate fields when the coverage artifact binding is present.\n\n"
        "Source priority: DOCX is the semantic source of truth and XHTML is its mandatory "
        "machine-readable projection. Registered support material may clarify but may not "
        "replace or extend a closed value list stated by the bounded main-FT row. Do not mark "
        "a main-FT dictionary assertion incorrect solely because support contains a different "
        "or broader list.\n\n"
        "Output consistency: when a classification dimension is incorrect, its corresponding "
        "approved_* value must propose a different valid value. If the approved value remains "
        "the manifest value, mark that classification dimension verified.\n",
        "## Bound manifest identity\n\n"
        + json.dumps(
            {
                "manifest_digest": manifest.digest,
                "scope_slug": manifest.scope_slug,
                "assertion_count": len(selected_ids),
                "full_assertion_count": len(manifest.assertions),
                "source_row_count": len(manifest.source_rows),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "## Exact runner evidence registry\n\n"
        + json.dumps(
            {
                "evidence_set_digest": evidence.digest,
                "binding_count": len(evidence.bindings),
                "bindings": list(evidence.bindings),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "## Passed deterministic source gate\n\n"
        + json.dumps(dict(gate), ensure_ascii=False, indent=2),
    ]
    if is_shard:
        parts.append(
            "## Runner-owned bounded review shard\n\n"
            + json.dumps(
                {
                    "shard_id": shard_id,
                    "shard_count": shard_count,
                    "assertion_ids": list(selected_ids),
                    "merge_policy": "complete-disjoint-runner-owned-v1",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n\nReview every listed assertion exactly once. Do not review or return "
            "assertions outside this list. The runner validates and merges all complete, "
            "disjoint shard receipts before publishing the full receipt."
        )
    for path, content in instruction_files:
        parts.append(f"## Instruction file: {path}\n\n{content}")
    parts.append(
        "## Scope-specific procedural review prompt (not evidence)\n\n" + review_prompt
    )
    parts.append(
        "## Compact typed source basis\n\n"
        "Repeated source-row identity and text are omitted from each assertion here; "
        "resolve every source_row_id against the runner-inline manifest-source-row "
        "evidence below. Binding arrays use the exact positional field order declared "
        "once in transport_legend; omitted_gate_verified_fields were already checked "
        "by the passed deterministic source gate and are not review evidence.\n\n```json\n"
        + reviewer_transport_basis_json(manifest, assertion_ids=selected_ids)
        + "\n```"
    )
    for path, content in evidence.inline_files:
        if Path(path).name in {
            "source-row-inventory.md",
            "source-row-extraction-spec.json",
            "source-row-baseline.json",
        }:
            parts.append(
                f"## Gate-verified evidence identity: {Path(path).name}\n\n"
                "This mandatory discovery artifact was exact-validated by the passed gate. "
                "Its hash-bound identity remains in the evidence registry; its semantic "
                "digest/count remain in the compact basis, and its candidate/source-row "
                "mapping is carried by the runner-inline manifest-source-row blocks below. "
                "The duplicate body is omitted from model transport."
            )
            continue
        rendered_content = content
        if content.lstrip().startswith(("{", "[")):
            try:
                rendered_content = json.dumps(
                    json.loads(content),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            except json.JSONDecodeError:
                pass
        parts.append(f"## Evidence file: {path}\n\n{rendered_content}")
    if evidence.image_paths:
        parts.append(
            "## Direct registered image attachments\n\n"
            + "\n".join(
                f"- {path.name} (use the attached image bytes; its repository binding is "
                "listed in the exact runner evidence registry)"
                for path in evidence.image_paths
            )
        )
    parts.append(
        "## Final response\n\nReturn only the JSON object matching the supplied output schema."
    )
    return "\n\n".join(parts).rstrip() + "\n"


def plan_review_prompt_shards(
    *,
    manifest: SourceAssertionManifest,
    gate: Mapping[str, Any],
    instruction_files: Sequence[tuple[str, str]],
    review_prompt: str,
    evidence: PreparedEvidenceSet,
    max_prompt_bytes: int = DEFAULT_MAX_PROMPT_BYTES,
    max_shards: int = DEFAULT_MAX_REVIEW_SHARDS,
    shard_target_prompt_bytes: int = DEFAULT_SHARD_TARGET_PROMPT_BYTES,
    max_assertions_per_shard: int = DEFAULT_MAX_ASSERTIONS_PER_SHARD,
) -> tuple[ReviewPromptShard, ...]:
    """Plan complete/disjoint review prompts without splitting source-row siblings."""

    if type(max_prompt_bytes) is not int or max_prompt_bytes <= 0:
        raise SourceReviewerRunnerError("source reviewer max_prompt_bytes must be positive")
    if (
        type(shard_target_prompt_bytes) is not int
        or shard_target_prompt_bytes <= 0
        or shard_target_prompt_bytes > max_prompt_bytes
    ):
        raise SourceReviewerRunnerError(
            "source reviewer shard_target_prompt_bytes must be positive and not "
            "exceed max_prompt_bytes"
        )
    if type(max_assertions_per_shard) is not int or max_assertions_per_shard <= 0:
        raise SourceReviewerRunnerError(
            "source reviewer max_assertions_per_shard must be positive"
        )
    if type(max_shards) is not int or not 2 <= max_shards <= 999:
        raise SourceReviewerRunnerError(
            "source reviewer max_shards must be between 2 and 999"
        )
    full_ids = tuple(item.assertion_id for item in manifest.assertions)
    full_prompt = render_prompt(
        manifest=manifest,
        gate=gate,
        instruction_files=instruction_files,
        review_prompt=review_prompt,
        evidence=evidence,
    )
    full_bytes = len(full_prompt.encode("utf-8"))
    if (
        full_bytes <= shard_target_prompt_bytes
        and len(full_ids) <= max_assertions_per_shard
    ):
        return (
            ReviewPromptShard(
                shard_id="source-review-shard-001",
                assertion_ids=full_ids,
                prompt=full_prompt,
                prompt_bytes=full_bytes,
                schema=receipt_schema(manifest),
            ),
        )

    assertions_by_row: dict[str, list[str]] = {}
    row_order: list[str] = []
    for assertion in manifest.assertions:
        if assertion.source_row_id not in assertions_by_row:
            assertions_by_row[assertion.source_row_id] = []
            row_order.append(assertion.source_row_id)
        assertions_by_row[assertion.source_row_id].append(assertion.assertion_id)

    groups = [tuple(assertions_by_row[row_id]) for row_id in row_order]
    partitions: list[tuple[str, ...]] = []
    current: tuple[str, ...] = ()

    def rendered_size(assertion_selection: tuple[str, ...]) -> int:
        candidate = render_prompt(
            manifest=manifest,
            gate=gate,
            instruction_files=instruction_files,
            review_prompt=review_prompt,
            evidence=evidence,
            assertion_ids=assertion_selection,
            shard_id="source-review-shard-999",
            shard_count=max_shards,
        )
        return len(candidate.encode("utf-8"))

    for group in groups:
        candidate = (*current, *group)
        candidate_bytes = rendered_size(candidate)
        if (
            candidate_bytes <= shard_target_prompt_bytes
            and len(candidate) <= max_assertions_per_shard
        ):
            current = candidate
            continue
        if current:
            partitions.append(current)
        if rendered_size(group) > max_prompt_bytes:
            raise SourceReviewerRunnerError(
                "one source-row assertion group exceeds the source reviewer prompt cap: "
                f"source_row_id={next(item.source_row_id for item in manifest.assertions if item.assertion_id == group[0])}, "
                f"max_prompt_bytes={max_prompt_bytes}"
            )
        current = group
    if current:
        partitions.append(current)
    if len(partitions) < 2:
        raise SourceReviewerRunnerError(
            "source reviewer prompt exceeds the one-shot cap but no safe shard split was produced"
        )
    if len(partitions) > max_shards:
        # The target is a soft latency preference.  A large shared evidence
        # prefix can make every row exceed that target on its own even though
        # several complete row groups still fit under the hard prompt cap.
        # Repack contiguously under the hard cap before declaring the scope
        # unshardable; source-row siblings and ordered ownership remain intact.
        hard_partitions: list[tuple[str, ...]] = []
        current = ()
        for group in groups:
            candidate = (*current, *group)
            if (
                rendered_size(candidate) <= max_prompt_bytes
                and len(candidate) <= max_assertions_per_shard
            ):
                current = candidate
                continue
            if current:
                hard_partitions.append(current)
            if (
                rendered_size(group) > max_prompt_bytes
                or len(group) > max_assertions_per_shard
            ):
                raise SourceReviewerRunnerError(
                    "one source-row assertion group exceeds the source reviewer "
                    "hard shard capacity"
                )
            current = group
        if current:
            hard_partitions.append(current)
        partitions = hard_partitions
        if len(partitions) > max_shards:
            raise SourceReviewerRunnerError(
                f"source reviewer requires {len(partitions)} hard-cap shards, "
                f"exceeding max_shards={max_shards}"
            )
        if len(partitions) == 1:
            return (
                ReviewPromptShard(
                    shard_id="source-review-shard-001",
                    assertion_ids=full_ids,
                    prompt=full_prompt,
                    prompt_bytes=full_bytes,
                    schema=receipt_schema(manifest),
                ),
            )

    result: list[ReviewPromptShard] = []
    for index, assertion_selection in enumerate(partitions, start=1):
        shard_id = f"source-review-shard-{index:03d}"
        prompt = render_prompt(
            manifest=manifest,
            gate=gate,
            instruction_files=instruction_files,
            review_prompt=review_prompt,
            evidence=evidence,
            assertion_ids=assertion_selection,
            shard_id=shard_id,
            shard_count=len(partitions),
        )
        prompt_bytes = len(prompt.encode("utf-8"))
        if prompt_bytes > max_prompt_bytes:
            raise SourceReviewerRunnerError(
                f"{shard_id} prompt exceeds cap after final plan rendering: "
                f"{prompt_bytes} > {max_prompt_bytes} bytes"
            )
        result.append(
            ReviewPromptShard(
                shard_id=shard_id,
                assertion_ids=assertion_selection,
                prompt=prompt,
                prompt_bytes=prompt_bytes,
                schema=receipt_schema(manifest, assertion_ids=assertion_selection),
            )
        )
    owned = tuple(assertion_id for shard in result for assertion_id in shard.assertion_ids)
    if owned != full_ids or len(owned) != len(set(owned)):
        raise SourceReviewerRunnerError(
            "source reviewer shard ownership must be complete, ordered and disjoint"
        )
    return tuple(result)


def _verified_assertion_review(assertion: Any) -> dict[str, Any]:
    return {
        "assertion_id": assertion.assertion_id,
        "approved_polarity": assertion.polarity,
        "approved_semantic_disposition": assertion.semantic_disposition,
        "approved_execution_readiness": assertion.execution_readiness,
        "approved_risk": assertion.risk,
        "dimension_verdicts": {
            dimension: "verified" for dimension in SOURCE_REVIEW_DIMENSIONS
        },
        "verdict": "verified",
        "required_change": "none_required",
        "note": "Deterministic validation filler for an unowned assertion.",
    }


def validate_review_shard_payload(
    payload: Mapping[str, Any],
    *,
    manifest: SourceAssertionManifest,
    shard: ReviewPromptShard,
) -> None:
    """Validate a partial model receipt against the full immutable manifest."""

    try:
        validate_openai_strict_output_instance(payload, shard.schema)
    except Exception as exc:
        raise SourceReviewerRunnerError(
            f"{shard.shard_id} output does not match its strict schema: {exc}"
        ) from exc
    reviews = payload.get("assertion_reviews")
    if not isinstance(reviews, list):
        raise SourceReviewerRunnerError(
            f"{shard.shard_id} assertion_reviews must be an array"
        )
    reviewed_ids = [
        item.get("assertion_id") if isinstance(item, Mapping) else None
        for item in reviews
    ]
    if (
        len(reviewed_ids) != len(set(reviewed_ids))
        or set(reviewed_ids) != set(shard.assertion_ids)
    ):
        raise SourceReviewerRunnerError(
            f"{shard.shard_id} assertion review set does not match shard ownership"
        )
    reviews_by_id = {
        str(item["assertion_id"]): dict(item)
        for item in reviews
        if isinstance(item, Mapping)
    }
    completed_reviews = [
        reviews_by_id.get(assertion.assertion_id, _verified_assertion_review(assertion))
        for assertion in manifest.assertions
    ]
    validation_payload = {
        **dict(payload),
        "assertion_reviews": completed_reviews,
    }
    try:
        receipt = SourceAssertionReviewReceipt.from_dict(validation_payload)
        receipt.validate(manifest)
    except Exception as exc:
        raise SourceReviewerRunnerError(
            f"{shard.shard_id} semantic receipt validation failed: {exc}"
        ) from exc


def merge_review_shard_payloads(
    payloads: Sequence[Mapping[str, Any]],
    *,
    manifest: SourceAssertionManifest,
    shards: Sequence[ReviewPromptShard],
) -> dict[str, Any]:
    if len(payloads) != len(shards) or not payloads:
        raise SourceReviewerRunnerError(
            "source reviewer merge requires one payload for every planned shard"
        )
    for payload, shard in zip(payloads, shards, strict=True):
        validate_review_shard_payload(payload, manifest=manifest, shard=shard)

    reviews_by_id = {
        str(review["assertion_id"]): dict(review)
        for payload in payloads
        for review in payload["assertion_reviews"]
    }
    assertion_reviews = [
        reviews_by_id[assertion.assertion_id] for assertion in manifest.assertions
    ]
    inventory_reviews = [dict(payload["source_inventory_review"]) for payload in payloads]
    boundary_reviews = [dict(payload["scope_boundary_review"]) for payload in payloads]

    def select_global_review(
        reviews: Sequence[dict[str, Any]],
        *,
        merge_excluded_contexts: bool = False,
    ) -> dict[str, Any]:
        incorrect = [review for review in reviews if review.get("verdict") == "incorrect"]
        if not incorrect:
            return reviews[0]
        selected = dict(incorrect[0])
        selected["required_change"] = " | ".join(
            dict.fromkeys(str(review["required_change"]) for review in incorrect)
        )
        selected["note"] = " | ".join(
            dict.fromkeys(str(review["note"]) for review in incorrect)
        )
        if merge_excluded_contexts:
            merged_exclusions: list[Mapping[str, Any]] = []
            seen_exclusions: set[str] = set()
            for review in incorrect:
                for exclusion in review.get("excluded_contexts", []):
                    identity = json.dumps(
                        exclusion,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    if identity not in seen_exclusions:
                        seen_exclusions.add(identity)
                        merged_exclusions.append(exclusion)
            selected["excluded_contexts"] = merged_exclusions
        return selected

    merged = {
        "version": REVIEW_RECEIPT_VERSION,
        "manifest_digest": manifest.digest,
        "decision": (
            "changes-required"
            if any(payload.get("decision") == "changes-required" for payload in payloads)
            else "accepted"
        ),
        "assertion_reviews": assertion_reviews,
        "source_inventory_review": select_global_review(inventory_reviews),
        "scope_boundary_review": select_global_review(
            boundary_reviews,
            merge_excluded_contexts=True,
        ),
    }
    try:
        receipt = SourceAssertionReviewReceipt.from_dict(merged)
        receipt.validate(manifest)
    except Exception as exc:
        raise SourceReviewerRunnerError(
            f"merged source reviewer receipt is invalid: {exc}"
        ) from exc
    return merged


def _aggregate_usage(payloads: Sequence[Mapping[str, int]]) -> dict[str, int]:
    keys = sorted({key for payload in payloads for key in payload})
    return {
        key: sum(
            value
            for payload in payloads
            for value in (payload.get(key),)
            if type(value) is int
        )
        for key in keys
    }


def event_item_type(line: str) -> str | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    item = payload.get("item")
    if not isinstance(item, dict):
        return None
    item_type = item.get("type")
    return item_type if isinstance(item_type, str) else None


def event_usage(line: str) -> dict[str, int] | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    usage = payload.get("usage") if payload.get("type") == "turn.completed" else None
    if not isinstance(usage, dict):
        return None
    return {
        key: value
        for key, value in usage.items()
        if isinstance(key, str) and type(value) is int
    }


def run_exec(
    command: Sequence[str],
    *,
    prompt: str,
    cwd: Path,
    events_path: Path,
    stderr_path: Path,
    timeout_seconds: int | None,
    runtime_metadata: MutableMapping[str, Any] | None = None,
) -> tuple[int, dict[str, int], str | None]:
    diagnostics: MutableMapping[str, Any]
    if runtime_metadata is None:
        diagnostics = {}
    else:
        runtime_metadata.clear()
        diagnostics = runtime_metadata
    diagnostics.update(
        {
            "timeout_seconds": timeout_seconds,
            "process_id": None,
            "timeout_triggered": False,
            "termination_required": False,
            "termination_method": "not-needed",
            "termination_return_code": None,
            "termination_error": None,
            "process_final_return_code": None,
        }
    )
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    line_queue: queue.Queue[str | None] = queue.Queue()
    usage: dict[str, int] = {}
    forbidden: str | None = None
    process: subprocess.Popen[str] | None = None
    reader: threading.Thread | None = None
    with (
        stderr_path.open("x", encoding="utf-8", newline="\n") as stderr_handle,
        events_path.open("x", encoding="utf-8", newline="\n") as events_handle,
    ):
        try:
            process = subprocess.Popen(
                list(command),
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=stderr_handle,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=environment,
            )
            diagnostics["process_id"] = process.pid
            assert process.stdin is not None
            assert process.stdout is not None
            process.stdin.write(prompt)
            process.stdin.close()

            def read_stdout() -> None:
                assert process is not None
                assert process.stdout is not None
                for raw_line in process.stdout:
                    line_queue.put(raw_line)
                line_queue.put(None)

            reader = threading.Thread(target=read_stdout, daemon=True)
            reader.start()
            deadline = (
                time.monotonic() + timeout_seconds
                if timeout_seconds is not None
                else None
            )
            finished_stream = False
            while not finished_stream:
                remaining = (
                    deadline - time.monotonic() if deadline is not None else None
                )
                if remaining is not None and remaining <= 0:
                    diagnostics["timeout_triggered"] = True
                    raise SourceReviewerRunnerError(
                        f"source reviewer timed out after {timeout_seconds}s"
                    )
                try:
                    line = line_queue.get(
                        timeout=(min(0.25, remaining) if remaining is not None else 0.25)
                    )
                except queue.Empty:
                    continue
                if line is None:
                    finished_stream = True
                    continue
                events_handle.write(line)
                events_handle.flush()
                item_type = event_item_type(line)
                if item_type in FORBIDDEN_ITEM_TYPES and forbidden is None:
                    forbidden = item_type
                    process.terminate()
                found_usage = event_usage(line)
                if found_usage is not None:
                    usage = found_usage
            try:
                return_code = process.wait(
                    timeout=(
                        max(1.0, deadline - time.monotonic())
                        if deadline is not None
                        else None
                    )
                )
            except subprocess.TimeoutExpired as exc:
                raise SourceReviewerRunnerError(
                    "source reviewer did not terminate"
                ) from exc
        finally:
            if process is not None:
                if process.poll() is None:
                    diagnostics["termination_required"] = True
                    try:
                        if os.name == "nt":
                            terminated = subprocess.run(
                                [
                                    "taskkill",
                                    "/PID",
                                    str(process.pid),
                                    "/T",
                                    "/F",
                                ],
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                                timeout=15,
                                check=False,
                            )
                            diagnostics["termination_method"] = "taskkill-tree"
                            diagnostics["termination_return_code"] = terminated.returncode
                            if terminated.returncode != 0:
                                diagnostics["termination_error"] = (
                                    terminated.stderr or terminated.stdout
                                ).strip()[-1000:]
                                process.kill()
                                diagnostics["termination_method"] = "taskkill-tree+process-kill"
                        else:
                            process.kill()
                            diagnostics["termination_method"] = "process-kill"
                    except (OSError, subprocess.SubprocessError) as termination_exc:
                        diagnostics["termination_error"] = str(termination_exc)
                        try:
                            process.kill()
                            diagnostics["termination_method"] = "process-kill-fallback"
                        except OSError as kill_exc:
                            diagnostics["termination_error"] = (
                                f"{diagnostics['termination_error']}; fallback={kill_exc}"
                            )
                try:
                    process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
                diagnostics["process_final_return_code"] = process.poll()
                if process.stdin is not None and not process.stdin.closed:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass
                if reader is not None:
                    reader.join(timeout=1)
                if process.stdout is not None:
                    process.stdout.close()
    return return_code, usage, forbidden


def output_paths(args: argparse.Namespace, root: Path) -> dict[str, Path]:
    paths = {
        name: resolve_under(root, getattr(args, name), label=name)
        for name in (
            "receipt_output",
            "events_output",
            "stderr_output",
            "summary_output",
            "schema_output",
            "context_output",
        )
    }
    optional_audit = (
        args.session_log_output,
        args.decision_log_output,
    )
    if any(optional_audit) and not all(optional_audit):
        raise SourceReviewerRunnerError(
            "source reviewer audit outputs must provide both session and decision logs"
        )
    if all(optional_audit):
        if not args.audit_ft_slug:
            raise SourceReviewerRunnerError(
                "--audit-ft-slug is required with source reviewer audit outputs"
            )
        paths["session_log_output"] = resolve_under(
            root, args.session_log_output, label="session_log_output"
        )
        paths["decision_log_output"] = resolve_under(
            root, args.decision_log_output, label="decision_log_output"
        )
    return paths


def _relative_label(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def render_source_review_audit_logs(
    *,
    root: Path,
    ft_slug: str,
    manifest: SourceAssertionManifest,
    receipt: SourceAssertionReviewReceipt,
    summary: Mapping[str, Any],
    manifest_path: Path,
    gate_path: Path,
    review_prompt_path: Path,
    context_path: Path,
    receipt_path: Path,
    summary_path: Path,
    session_log_path: Path,
    decision_log_path: Path,
) -> tuple[str, str]:
    """Render deterministic, evidence-bound audit logs for a completed review."""

    incorrect_ids = [
        item.assertion_id
        for item in receipt.assertion_reviews
        if item.verdict == "incorrect"
    ]
    status_after = (
        "ready-for-next-stage"
        if receipt.decision == "accepted"
        else "changes-required"
    )
    next_route = (
        "ft-test-case-iteration"
        if receipt.decision == "accepted"
        else "ft-scope-analyzer"
    )
    receipt_sha256 = sha256_file(receipt_path)
    usage = summary.get("usage") if isinstance(summary.get("usage"), Mapping) else {}

    def usage_value(name: str) -> str:
        value = usage.get(name)
        return str(value) if type(value) is int else "unavailable"

    incorrect_summary = (
        ", ".join(f"`{item}`" for item in incorrect_ids)
        if incorrect_ids
        else "none"
    )
    session = f"""# Source Assertion Reviewer Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-reviewer` |
| mode | `source_assertion_review` |
| ft_slug | `{ft_slug}` |
| scope_slug | `{manifest.scope_slug}` |
| started_from | `{_relative_label(root, manifest_path)}` |
| status_after | `{status_after}` |

## Inputs Read

- `{_relative_label(root, manifest_path)}` — source-first manifest с digest `{manifest.digest}`.
- `{_relative_label(root, gate_path)}` — успешный deterministic pre-review gate.
- `{_relative_label(root, review_prompt_path)}` — tool-free reviewer contract.
- `{_relative_label(root, context_path)}` — hash-bound bounded context, созданный runner-ом.

## Inputs Not Used

- `test-cases/**` и старые review-cycle outputs — не входили в reviewer context.

## Key Decisions

- Independent receipt decision: `{receipt.decision}`; receipt SHA-256: `{receipt_sha256}`.
- Проверены `{len(receipt.assertion_reviews)}` assertions; incorrect: `{len(incorrect_ids)}` ({incorrect_summary}).
- Следующий маршрут: `{next_route}`.

## Risks And Fallbacks

- Assertions, требующие исправления: {incorrect_summary}.
- Runner retry count: `{summary.get('retry_count', 0)}`; скрытое продолжение испорченного review не выполнялось.

## Validation

- Runner postvalidation: `{summary.get('status', 'unknown')}`; receipt `{receipt.decision}`.
- Duration: `{summary.get('duration_ms', 'unavailable')} ms`; model sessions: `{summary.get('model_session_count', 'unavailable')}`; tool events: `{summary.get('tool_event_count', 'unavailable')}`.
- Usage: input `{usage_value('input_tokens')}`, output `{usage_value('output_tokens')}`, reasoning `{usage_value('reasoning_output_tokens')}` tokens.

## Contamination Check

- Tool-free bounded context и immutable input snapshot: pass; `test-cases/**` не читались reviewer-ом.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Deterministic source gate | pass | `{_relative_label(root, gate_path)}` |
| 2 | Independent bounded reviewer session | `{receipt.decision}`; `{summary.get('model_session_count', 'unavailable')}` model sessions; zero tool events | `{_relative_label(root, summary_path)}` |
| 3 | Canonical receipt postvalidation | pass; exact manifest digest | `{_relative_label(root, receipt_path)}` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Exact source assertion receipt | {'pass' if receipt.decision == 'accepted' else 'fail'} | receipt v{receipt.version}; `{len(receipt.assertion_reviews)}` reviews | `{next_route}` |
| Source inventory | `{receipt.source_inventory_review.verdict}` | `{receipt.source_inventory_review.mapped_source_row_count}`/`{receipt.source_inventory_review.candidate_count}` candidates | preserve exact baseline binding |
| Scope boundary | `{receipt.scope_boundary_review.verdict}` | typed boundary receipt | preserve reviewed boundary classes |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `{_relative_label(root, session_log_path)}` | `small deterministic audit artifact` | `atomic UTF-8 runner output` | `yes` | `codex_exec_source_assertion_reviewer.py` | `yes` |
| `{_relative_label(root, decision_log_path)}` | `small deterministic audit artifact` | `atomic UTF-8 runner output` | `yes` | `codex_exec_source_assertion_reviewer.py` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `none` | `none` | `none` | `none` | `n/a` | `n/a` | `none` | `none` |

## Handoff Notes For Next Session

- Route to `{next_route}`; incorrect assertions: {incorrect_summary}.
"""
    decision_status = "applied" if receipt.decision == "accepted" else "blocked"
    decision = f"""# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `{ft_slug}` |
| scope_slug | `{manifest.scope_slug}` |
| stage | `ft-test-case-reviewer` |
| started_from | `{_relative_label(root, manifest_path)}` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `validation` | receipt v{receipt.version} | Зафиксировать decision `{receipt.decision}` | Независимый reviewer проверил `{len(receipt.assertion_reviews)}` assertions; incorrect: `{len(incorrect_ids)}` | `{_relative_label(root, receipt_path)}` | `high` | `{decision_status}` |
| `DEC-002` | 2 | `routing` | exact-digest source review | Передать workflow в `{next_route}` | Маршрут определяется только валидированным receipt decision | `workflow-state.yaml` | `high` | `applied` |
"""
    return session, decision


def _shard_output_path(path: Path, shard_id: str) -> Path:
    return path.with_name(f"{path.stem}.{shard_id}{path.suffix}")


def reserve_fresh_outputs(
    paths: Iterable[Path],
    *,
    receipt_output: Path,
) -> OutputReservations:
    resolved = [path.resolve() for path in paths]
    if len(resolved) != len(set(resolved)):
        raise SourceReviewerRunnerError(
            "source reviewer output paths must be distinct files"
        )
    receipt_output = receipt_output.resolve()
    if receipt_output not in resolved:
        raise SourceReviewerRunnerError(
            "source reviewer receipt output must be part of the reserved output set"
        )
    lock_paths = {
        path: path.with_name(f".{path.name}.source-review.lock")
        for path in resolved
    }
    if len(set(lock_paths.values())) != len(lock_paths) or set(resolved) & set(
        lock_paths.values()
    ):
        raise SourceReviewerRunnerError(
            "source reviewer output paths collide with reservation sidecars"
        )
    owner_token = uuid.uuid4().hex
    model_receipt_path = receipt_output.with_name(
        f".{receipt_output.name}.source-review.{owner_token}.model-output.tmp"
    )
    if model_receipt_path in resolved or model_receipt_path.exists():
        raise SourceReviewerRunnerError(
            "source reviewer private model receipt path is not fresh"
        )
    delete_on_close_flag = getattr(os, "O_TEMPORARY", 0)
    lock_handles: list[tuple[Path, int]] = []
    for path in resolved:
        path.parent.mkdir(parents=True, exist_ok=True)
    try:
        for path in sorted(resolved, key=lambda item: os.path.normcase(str(item))):
            if path.exists():
                raise SourceReviewerRunnerError(
                    "source reviewer output already exists; hidden overwrite/retry is "
                    f"forbidden: {path}"
                )
            lock_path = lock_paths[path]
            try:
                descriptor = os.open(
                    lock_path,
                    os.O_CREAT
                    | os.O_EXCL
                    | os.O_WRONLY
                    | delete_on_close_flag,
                    0o600,
                )
            except FileExistsError as exc:
                raise SourceReviewerRunnerError(
                    f"source reviewer output is already reserved: {path}"
                ) from exc
            lock_handles.append((lock_path, descriptor))
            metadata = json.dumps(
                {
                    "owner_token": owner_token,
                    "output_path": str(path),
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            os.write(descriptor, metadata + b"\n")
            os.fsync(descriptor)
            if path.exists():
                raise SourceReviewerRunnerError(
                    f"source reviewer output appeared during reservation: {path}"
                )
    except Exception:
        partial = OutputReservations(
            owner_token=owner_token,
            lock_handles=tuple(lock_handles),
            model_receipt_path=model_receipt_path,
            delete_locks_on_close=bool(delete_on_close_flag),
        )
        partial.release()
        raise
    return OutputReservations(
        owner_token=owner_token,
        lock_handles=tuple(lock_handles),
        model_receipt_path=model_receipt_path,
        delete_locks_on_close=bool(delete_on_close_flag),
    )


def assert_output_isolation(
    outputs: Iterable[Path],
    *,
    inputs: Iterable[Path],
) -> None:
    output_paths = [path.resolve() for path in outputs]
    if len(output_paths) != len(set(output_paths)):
        raise SourceReviewerRunnerError(
            "source reviewer output paths must be distinct files"
        )
    input_paths = {path.resolve() for path in inputs}
    aliases = sorted(str(path) for path in set(output_paths) & input_paths)
    if aliases:
        raise SourceReviewerRunnerError(
            "source reviewer outputs must not alias any input/evidence path: "
            + ", ".join(aliases)
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one bounded, tool-free codex exec source assertion review."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-gate-receipt", type=Path, required=True)
    parser.add_argument("--review-prompt", type=Path, required=True)
    parser.add_argument("--source-row-inventory", type=Path, required=True)
    parser.add_argument("--source-row-extraction-spec", type=Path, required=True)
    parser.add_argument("--source-row-baseline", type=Path, required=True)
    parser.add_argument("--bounded-extract", action="append", type=Path, default=[])
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--events-output", type=Path, required=True)
    parser.add_argument("--stderr-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--schema-output", type=Path, required=True)
    parser.add_argument("--context-output", type=Path, required=True)
    parser.add_argument("--session-log-output", type=Path)
    parser.add_argument("--decision-log-output", type=Path)
    parser.add_argument("--audit-ft-slug")
    parser.add_argument("--codex-command")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument(
        "--max-prompt-bytes",
        type=int,
        default=DEFAULT_MAX_PROMPT_BYTES,
        help="Per-session source-review prompt cap; oversized reviews are safely sharded.",
    )
    parser.add_argument(
        "--max-review-shards",
        type=int,
        default=DEFAULT_MAX_REVIEW_SHARDS,
    )
    parser.add_argument(
        "--shard-target-prompt-bytes",
        type=int,
        default=DEFAULT_SHARD_TARGET_PROMPT_BYTES,
        help="Soft per-shard target; the hard transport cap remains max-prompt-bytes.",
    )
    parser.add_argument(
        "--max-assertions-per-shard",
        type=int,
        default=DEFAULT_MAX_ASSERTIONS_PER_SHARD,
    )
    parser.add_argument("--max-direct-file-bytes", type=int, default=65_536)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    started_at = utc_now()
    started = time.monotonic()
    paths = output_paths(args, root)
    outputs_safe_for_failure = False
    model_attempt_count = 0
    execution_route = "not-planned"
    planned_shard_count = 0
    receipt_published = False
    completed_summary_published = False
    reservations: OutputReservations | None = None
    private_shard_receipts: list[Path] = []
    audit_outputs_published: list[Path] = []
    try:
        manifest_path = resolve_under(root, args.manifest, label="manifest")
        gate_path = resolve_under(
            root, args.source_gate_receipt, label="source_gate_receipt"
        )
        review_prompt_path = resolve_under(root, args.review_prompt, label="review_prompt")
        inventory_path = resolve_under(
            root, args.source_row_inventory, label="source_row_inventory"
        )
        extraction_spec_path = resolve_under(
            root,
            args.source_row_extraction_spec,
            label="source_row_extraction_spec",
        )
        baseline_path = resolve_under(
            root, args.source_row_baseline, label="source_row_baseline"
        )
        bounded_extract_paths = [
            resolve_under(root, item, label="bounded_extract")
            for item in args.bounded_extract
        ]
        manifest_bytes = manifest_path.read_bytes()
        manifest_input_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        try:
            raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceReviewerRunnerError(
                f"cannot parse captured source assertion manifest bytes: {exc}"
            ) from exc
        if not isinstance(raw_manifest, Mapping):
            raise SourceReviewerRunnerError(
                "captured source assertion manifest must be a JSON object"
            )
        manifest = SourceAssertionManifest.from_dict(raw_manifest)
        manifest.validate(root)
        gate_bytes = gate_path.read_bytes()
        gate_input_sha256 = hashlib.sha256(gate_bytes).hexdigest()
        try:
            gate = json.loads(gate_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceReviewerRunnerError(
                f"cannot parse captured source gate receipt bytes: {exc}"
            ) from exc
        if not isinstance(gate, Mapping):
            raise SourceReviewerRunnerError(
                "captured source gate receipt must be a JSON object"
            )
        try:
            validate_passed_source_gate_receipt(gate, manifest=manifest)
        except ValueError as exc:
            raise SourceReviewerRunnerError(str(exc)) from exc
        resolved_context, instruction_files = instruction_context(root)
        bounded_descriptor_input_sha256 = {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in bounded_extract_paths
        }
        evidence = prepare_evidence_set(
            root=root,
            manifest=manifest,
            inventory_path=inventory_path,
            extraction_spec_path=extraction_spec_path,
            baseline_path=baseline_path,
            bounded_extract_paths=bounded_extract_paths,
            max_direct_file_bytes=args.max_direct_file_bytes,
        )
        review_prompt_bytes = review_prompt_path.read_bytes()
        try:
            review_prompt_content = review_prompt_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceReviewerRunnerError(
                f"review prompt must be UTF-8: {review_prompt_path}: {exc}"
            ) from exc
        review_prompt_input_sha256 = hashlib.sha256(review_prompt_bytes).hexdigest()
        prompt_shards = plan_review_prompt_shards(
            manifest=manifest,
            gate=gate,
            instruction_files=instruction_files,
            review_prompt=review_prompt_content,
            evidence=evidence,
            max_prompt_bytes=args.max_prompt_bytes,
            max_shards=args.max_review_shards,
            shard_target_prompt_bytes=args.shard_target_prompt_bytes,
            max_assertions_per_shard=args.max_assertions_per_shard,
        )
        planned_shard_count = len(prompt_shards)
        execution_route = (
            "one-shot" if planned_shard_count == 1 else "bounded-sharded"
        )
        one_shot_prompt = render_prompt(
            manifest=manifest,
            gate=gate,
            instruction_files=instruction_files,
            review_prompt=review_prompt_content,
            evidence=evidence,
        )
        one_shot_prompt_bytes = len(one_shot_prompt.encode("utf-8"))
        schema = receipt_schema(manifest)
        try:
            validate_openai_strict_output_schema(schema)
            for shard in prompt_shards:
                validate_openai_strict_output_schema(shard.schema)
        except ValueError as exc:
            raise SourceReviewerRunnerError(
                f"source reviewer output schema is transport-incompatible: {exc}"
            ) from exc
        input_paths = {
            manifest_path,
            gate_path,
            review_prompt_path,
            inventory_path,
            extraction_spec_path,
            baseline_path,
            *bounded_extract_paths,
            *(root / path for path, _content in instruction_files),
            *(root / path for path in evidence.snapshot_sha256),
        }
        input_snapshot_sha256 = {
            **dict(evidence.snapshot_sha256),
            **bounded_descriptor_input_sha256,
            **{
                path: hashlib.sha256(content.encode("utf-8")).hexdigest()
                for path, content in instruction_files
            },
            manifest_path.relative_to(root).as_posix(): manifest_input_sha256,
            gate_path.relative_to(root).as_posix(): gate_input_sha256,
            review_prompt_path.relative_to(root).as_posix(): (
                review_prompt_input_sha256
            ),
        }
        shard_runtime_paths: list[dict[str, Path]] = []
        for index, shard in enumerate(prompt_shards):
            if planned_shard_count == 1:
                schema_path = paths["schema_output"]
            else:
                schema_path = _shard_output_path(paths["schema_output"], shard.shard_id)
            shard_runtime_paths.append(
                {
                    "schema": schema_path,
                    "events": (
                        paths["events_output"]
                        if index == 0
                        else _shard_output_path(paths["events_output"], shard.shard_id)
                    ),
                    "stderr": (
                        paths["stderr_output"]
                        if index == 0
                        else _shard_output_path(paths["stderr_output"], shard.shard_id)
                    ),
                }
            )
        all_output_paths = list(paths.values())
        for runtime_paths in shard_runtime_paths:
            for path in runtime_paths.values():
                if path not in all_output_paths:
                    all_output_paths.append(path)
        assert_output_isolation(all_output_paths, inputs=input_paths)
        required_flags = ["--ephemeral", "--ignore-user-config", "--color"]
        if evidence.image_paths:
            required_flags.append("--image")
        resolution = resolve_verified_exec_capability(
            args.codex_command,
            additional_required_flags=tuple(required_flags),
            required_disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
            probe=probe_exec_capability,
        )
        capability = resolution.selection_capability()
        if not resolution.verified:
            raise SourceReviewerRunnerError(
                "codex exec capability is unavailable or unverified: "
                + (capability.error or ", ".join(capability.missing_flags))
            )
        codex = resolution.selected_executable or capability.resolved_command or capability.command
        assert_file_snapshot_unchanged(
            root,
            input_snapshot_sha256,
            label="source reviewer preflight input",
        )
        reservations = reserve_fresh_outputs(
            all_output_paths,
            receipt_output=paths["receipt_output"],
        )
        outputs_safe_for_failure = True
        write_json(paths["schema_output"], schema)
        schema_sha256 = sha256_file(paths["schema_output"])
        shard_schema_sha256: dict[str, str] = {}
        if planned_shard_count == 1:
            shard_schema_sha256[prompt_shards[0].shard_id] = schema_sha256
        else:
            for shard, runtime_paths in zip(
                prompt_shards, shard_runtime_paths, strict=True
            ):
                write_json(runtime_paths["schema"], shard.schema)
                shard_schema_sha256[shard.shard_id] = sha256_file(
                    runtime_paths["schema"]
                )
        prompt_bytes_total = sum(shard.prompt_bytes for shard in prompt_shards)
        max_shard_prompt_bytes = max(shard.prompt_bytes for shard in prompt_shards)
        context_report = {
            "version": 1,
            "scenario": SCENARIO_ID,
            "manifest_digest": manifest.digest,
            "execution_route": execution_route,
            "prompt_bytes": prompt_bytes_total,
            "one_shot_prompt_bytes": one_shot_prompt_bytes,
            "max_shard_prompt_bytes": max_shard_prompt_bytes,
            "max_prompt_bytes": args.max_prompt_bytes,
            "shard_target_prompt_bytes": args.shard_target_prompt_bytes,
            "max_assertions_per_shard": args.max_assertions_per_shard,
            "max_review_shards": args.max_review_shards,
            "rendered_prompt_sha256": (
                hashlib.sha256(prompt_shards[0].prompt.encode("utf-8")).hexdigest()
                if planned_shard_count == 1
                else canonical_json_sha256(
                    [
                        {
                            "shard_id": shard.shard_id,
                            "prompt_sha256": hashlib.sha256(
                                shard.prompt.encode("utf-8")
                            ).hexdigest(),
                        }
                        for shard in prompt_shards
                    ]
                )
            ),
            "review_shards": [
                {
                    "shard_id": shard.shard_id,
                    "assertion_ids": list(shard.assertion_ids),
                    "assertion_count": len(shard.assertion_ids),
                    "prompt_bytes": shard.prompt_bytes,
                    "rendered_prompt_sha256": hashlib.sha256(
                        shard.prompt.encode("utf-8")
                    ).hexdigest(),
                    "schema_path": shard_runtime_paths[index]["schema"]
                    .relative_to(root)
                    .as_posix(),
                    "schema_sha256": shard_schema_sha256[shard.shard_id],
                }
                for index, shard in enumerate(prompt_shards)
            ],
            "review_prompt": {
                "path": review_prompt_path.relative_to(root).as_posix(),
                "sha256": review_prompt_input_sha256,
                "size_bytes": len(review_prompt_bytes),
                "evidence_status": "procedural-not-semantic-evidence",
            },
            "output_schema": {
                "path": paths["schema_output"].relative_to(root).as_posix(),
                "sha256": schema_sha256,
            },
            "instruction_budget": resolved_context["budget"],
            "instruction_files": [
                {
                    "path": path,
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "size_bytes": len(content.encode("utf-8")),
                }
                for path, content in instruction_files
            ],
            "evidence_contract_version": 1,
            "evidence_set_digest": evidence.digest,
            "evidence_bindings": list(evidence.bindings),
            "evidence_snapshot_sha256": dict(evidence.snapshot_sha256),
            "direct_image_attachments": [
                path.relative_to(root).as_posix() for path in evidence.image_paths
            ],
            "source_gate_receipt": {
                "path": gate_path.relative_to(root).as_posix(),
                "sha256": gate_input_sha256,
            },
            "runner_input_snapshot_sha256": input_snapshot_sha256,
            "exec_backend": {
                "selected_executable": codex,
                "selected_version": capability.version,
                "capability_probe_total_ms": resolution.total_duration_ms,
                "disable_features": list(resolution.disable_features),
            },
        }
        write_json(paths["context_output"], context_report)
        assert_file_snapshot_unchanged(
            root,
            input_snapshot_sha256,
            label="source reviewer input before model call",
        )
        shard_payloads: list[Mapping[str, Any]] = []
        usage_payloads: list[Mapping[str, int]] = []
        for shard, runtime_paths in zip(
            prompt_shards, shard_runtime_paths, strict=True
        ):
            if planned_shard_count == 1:
                model_receipt_path = reservations.model_receipt_path
            else:
                model_receipt_path = reservations.model_receipt_path.with_name(
                    f"{reservations.model_receipt_path.name}.{shard.shard_id}.tmp"
                )
                if model_receipt_path.exists():
                    raise SourceReviewerRunnerError(
                        f"private shard receipt path is not fresh: {model_receipt_path}"
                    )
                private_shard_receipts.append(model_receipt_path)
            command = [
                codex,
                "exec",
                *resolution.disable_args,
                "--ephemeral",
                "--ignore-user-config",
                "--sandbox",
                "read-only",
                "--cd",
                str(root),
                "--json",
                "--output-last-message",
                str(model_receipt_path),
                "--output-schema",
                str(runtime_paths["schema"]),
                "--color",
                "never",
            ]
            for image_path in evidence.image_paths:
                command.extend(["--image", str(image_path)])
            command.append("-")
            model_attempt_count += 1
            return_code, usage, forbidden = run_exec(
                command,
                prompt=shard.prompt,
                cwd=root,
                events_path=runtime_paths["events"],
                stderr_path=runtime_paths["stderr"],
                timeout_seconds=(args.timeout_seconds if args.timeout_seconds > 0 else None),
            )
            if forbidden is not None:
                raise SourceReviewerRunnerError(
                    f"{shard.shard_id} attempted forbidden tool event: {forbidden}"
                )
            if return_code != 0:
                raise SourceReviewerRunnerError(
                    f"codex exec {shard.shard_id} exited with code {return_code}"
                )
            assert_file_snapshot_unchanged(
                root,
                input_snapshot_sha256,
                label=f"source reviewer input after {shard.shard_id}",
            )
            expected_schema_sha256 = shard_schema_sha256[shard.shard_id]
            if sha256_file(runtime_paths["schema"]) != expected_schema_sha256:
                raise SourceReviewerRunnerError(
                    f"{shard.shard_id} output schema changed during the model call"
                )
            if planned_shard_count > 1:
                payload = load_json_object(
                    model_receipt_path,
                    label=f"{shard.shard_id} model receipt",
                )
                validate_review_shard_payload(
                    payload,
                    manifest=manifest,
                    shard=shard,
                )
                shard_payloads.append(payload)
            usage_payloads.append(usage)

        if planned_shard_count == 1:
            receipt = load_source_assertion_review_receipt(
                reservations.model_receipt_path,
                manifest,
                require_accepted=False,
            )
        else:
            merged_payload = merge_review_shard_payloads(
                shard_payloads,
                manifest=manifest,
                shards=prompt_shards,
            )
            write_json(reservations.model_receipt_path, merged_payload)
            receipt = load_source_assertion_review_receipt(
                reservations.model_receipt_path,
                manifest,
                require_accepted=False,
            )
        publish_file_no_clobber(
            reservations.model_receipt_path,
            paths["receipt_output"],
            label="validated source reviewer receipt",
        )
        receipt_published = True
        summary = {
            "version": 1,
            "status": "completed",
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "execution_route": execution_route,
            "attempt_count": model_attempt_count,
            "retry_count": 0,
            "model_session_count": model_attempt_count,
            "review_shard_count": planned_shard_count,
            "tool_event_count": 0,
            "receipt_validation_count": 1,
            "shard_receipt_validation_count": planned_shard_count,
            "manifest_digest": manifest.digest,
            "evidence_set_digest": evidence.digest,
            "decision": receipt.decision,
            "assertion_review_count": len(receipt.assertion_reviews),
            "prompt_bytes": prompt_bytes_total,
            "one_shot_prompt_bytes": one_shot_prompt_bytes,
            "max_shard_prompt_bytes": max_shard_prompt_bytes,
            "usage": _aggregate_usage(usage_payloads),
            "codex_capability": {
                "verified": capability.verified,
                "duration_ms": capability.duration_ms,
                "missing_flags": list(capability.missing_flags),
            },
        }
        if "session_log_output" in paths:
            session_log, decision_log = render_source_review_audit_logs(
                root=root,
                ft_slug=args.audit_ft_slug,
                manifest=manifest,
                receipt=receipt,
                summary=summary,
                manifest_path=manifest_path,
                gate_path=gate_path,
                review_prompt_path=review_prompt_path,
                context_path=paths["context_output"],
                receipt_path=paths["receipt_output"],
                summary_path=paths["summary_output"],
                session_log_path=paths["session_log_output"],
                decision_log_path=paths["decision_log_output"],
            )
            write_text(paths["session_log_output"], session_log)
            audit_outputs_published.append(paths["session_log_output"])
            write_text(paths["decision_log_output"], decision_log)
            audit_outputs_published.append(paths["decision_log_output"])
        write_json(paths["summary_output"], summary)
        completed_summary_published = True
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - preserve one terminal runner receipt.
        for audit_output in audit_outputs_published:
            audit_output.unlink(missing_ok=True)
        if (
            receipt_published
            and not completed_summary_published
            and reservations is not None
        ):
            try:
                unlink_if_owned_hardlink(
                    paths["receipt_output"],
                    reservations.model_receipt_path,
                )
            except OSError:
                pass
        summary = {
            "version": 1,
            "status": "failed",
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "duration_ms": int((time.monotonic() - started) * 1000),
            # A reserved output set or completed deterministic preflight is not a
            # model attempt.  Keep failure metrics honest for the end-to-end
            # timing report and count only an actually started exec call.
            "execution_route": execution_route,
            "attempt_count": model_attempt_count,
            "retry_count": 0,
            "model_session_count": model_attempt_count,
            "review_shard_count": planned_shard_count,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        try:
            if outputs_safe_for_failure:
                write_json(paths["summary_output"], summary)
        except (OSError, SourceReviewerRunnerError):
            pass
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    finally:
        if reservations is not None:
            try:
                reservations.cleanup_model_receipt()
                for path in private_shard_receipts:
                    path.unlink(missing_ok=True)
            finally:
                reservations.release()


if __name__ == "__main__":
    raise SystemExit(main())
