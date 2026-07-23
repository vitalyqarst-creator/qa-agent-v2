from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from .source_row_baseline import (
    SourceRowBaselineValidationError,
    resolve_xhtml_candidates_at_locators,
)


LEGACY_MANIFEST_VERSIONS = frozenset({1, 2, 3})
MIGRATABLE_MANIFEST_VERSIONS = frozenset({3})
MANIFEST_VERSION = 4
LEGACY_REVIEW_RECEIPT_VERSIONS = frozenset({1, 2, 3, 4, 5})
REVIEW_RECEIPT_VERSION = 6
COMPACT_REVIEWER_BASIS_CONTRACT = "bounded-source-first-assertions-v4"
SOURCE_ASSERTIONS_MARKER = "<!-- SOURCE-ASSERTIONS-V4 -->"
LEGACY_COMPACT_REVIEWER_BASIS_CONTRACTS = frozenset(
    {
        "bounded-source-first-assertions-v1",
        "bounded-source-first-assertions-v2",
        "bounded-source-first-assertions-v3",
    }
)
LEGACY_SOURCE_ASSERTIONS_MARKERS = frozenset(
    {
        "<!-- SOURCE-ASSERTIONS-V1 -->",
        "<!-- SOURCE-ASSERTIONS-V2 -->",
        "<!-- SOURCE-ASSERTIONS-V3 -->",
    }
)
SOURCE_ASSERTIONS_BASIS_HEADING = "## Bounded reviewer source basis"
SOURCE_ASSERTIONS_REVIEW_HEADING = "### Independent source review receipt"
POLARITIES = {"positive", "negative", "neutral"}
SEMANTIC_DISPOSITIONS = {"testable", "ambiguous", "not-applicable"}
EXECUTION_READINESS_VALUES = {"ready", "dependency-blocked", "not-applicable"}
RISKS = {"low", "medium", "high", "critical"}
EVIDENCE_SOURCE_ROLES = {
    "approved-clarification",
    "semantic-source-of-truth",
    "structural-visual-parity",
    "supporting-material",
}
SOURCE_REVIEW_VERDICTS = {"verified", "incorrect"}
SOURCE_REVIEW_DIMENSION_VERDICTS = {"verified", "incorrect"}
SOURCE_REVIEW_DIMENSIONS = (
    "source-binding",
    "canonical-statement",
    "requirement-codes",
    "polarity",
    "semantic-disposition",
    "risk",
    "condition",
    "action",
    "oracle",
    "gap-routing",
    "execution-readiness",
    "execution-dependencies",
    "clarification-provenance",
)
NO_REQUIRED_CHANGE = "none_required"
SCOPE_BOUNDARY_CONTEXT_CLASSES = {
    "document-global-constraints",
    "ancestor-and-section-preamble",
    "cross-referenced-constraints",
}
SOURCE_CONTEXT_CLASSES = {"scope-local", *SCOPE_BOUNDARY_CONTEXT_CLASSES}
SOURCE_ROW_SCOPE_DISPOSITIONS = {"yes", "unclear", "no"}
SUPPORTING_SOURCE_EVIDENCE_ROLES = {
    "applicability",
    "constraint",
    "cross-reference",
    "definition",
    "polarity",
    "property",
    "subject",
}
REQUIREMENT_CODE_PROVENANCE_ROLES = {"xhtml-row", "pdf-parity"}
CLAUSE_EVIDENCE_KINDS = {"condition", "action", "oracle"}
CLARIFICATION_CLAUSE_KINDS = {*CLAUSE_EVIDENCE_KINDS, "canonical"}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
ATOM_ID_RE = re.compile(r"ATOM-[A-Za-z0-9._-]+")
OBLIGATION_ID_RE = re.compile(r"OBL-[A-Za-z0-9._-]+")
GAP_ID_RE = re.compile(r"GAP-[A-Za-z0-9._-]+")
SOURCE_CANDIDATE_ID_RE = re.compile(r"SRC-CAND-[0-9a-f]{24}")
PDF_PAGE_LOCATOR_RE = re.compile(r"page:([1-9][0-9]*)")
COVERAGE_GAP_HEADING_RE = re.compile(
    r"(?m)^#{2,4}\s+(GAP-[A-Za-z0-9._-]+)(?:\s+[-—].*)?\s*$"
)
ASSERTION_ID_RE = re.compile(r"ASSERT-[A-Za-z0-9._-]+")
CLARIFICATION_ID_RE = re.compile(r"CLR-[A-Za-z0-9._-]+")
CLARIFICATION_AUTHORITIES = {"user", "analyst", "product-owner"}
CLARIFICATION_RESPONSE_STATUSES = {
    "answered",
    "superseded",
    "rejected",
    "unanswered",
}
CLARIFICATION_RESPONSE_TYPES = {
    "user-confirmed",
    "analyst-confirmed",
    "product-confirmed",
    "working-assumption",
    "rejected",
    "not-provided",
}
APPROVED_CLARIFICATION_RESPONSE_TYPES = {
    "user-confirmed",
    "analyst-confirmed",
    "product-confirmed",
}
CLARIFICATION_AUTHORITY_RESPONSE_TYPES = {
    "user": "user-confirmed",
    "analyst": "analyst-confirmed",
    "product-owner": "product-confirmed",
}
CLARIFICATION_BINDING_SCOPES = {"requirement-code", "source-context"}
CLARIFICATION_TABLE_COLUMNS = (
    "clarification_id",
    "gap_id",
    "scope_slug",
    "requirement_codes",
    "authority",
    "user_response",
    "response_status",
    "response_type",
    "updated_at",
)


_EMBEDDED_SOURCE_ASSERTIONS_RE = re.compile(
    rf"(?m)^{re.escape(SOURCE_ASSERTIONS_BASIS_HEADING)}[ \t]*\r?\n"
    rf"(?:[ \t]*\r?\n)*"
    rf"^{re.escape(SOURCE_ASSERTIONS_MARKER)}[ \t]*\r?\n"
    rf"^```json[ \t]*\r?\n"
    rf"(?P<basis>[^\r\n]+)\r?\n"
    rf"^```[ \t]*\r?\n"
    rf"(?:[ \t]*\r?\n)*"
    rf"^{re.escape(SOURCE_ASSERTIONS_REVIEW_HEADING)}[ \t]*\r?\n"
    rf"(?:[ \t]*\r?\n)*"
    rf"^```json[ \t]*\r?\n"
    rf"(?P<receipt>[^\r\n]+)\r?\n"
    rf"^```[ \t]*(?:\r?\n|$)"
)


class SourceAssertionContractError(ValueError):
    """A fail-closed source assertion contract violation."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise SourceAssertionContractError(code, message)


def _exact_fields(
    payload: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str] | None = None,
    label: str,
) -> None:
    if not isinstance(payload, Mapping):
        _fail("invalid-object", f"{label} must be a JSON object")
    optional = optional or set()
    actual = set(payload)
    missing = sorted(required - actual)
    unknown = sorted(actual - required - optional)
    if missing or unknown:
        _fail(
            "invalid-fields",
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}",
        )


def _nonempty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("invalid-text", f"{label} must be non-empty text")
    return value.strip()


def _optional_gap_id(value: Any, label: str) -> str | None:
    if value is None:
        return None
    text = _nonempty_text(value, label)
    if GAP_ID_RE.fullmatch(text) is None:
        _fail("invalid-gap-id", f"{label} must name one GAP-*")
    return text


def _text_list(value: Any, label: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list):
        _fail("invalid-list", f"{label} must be a JSON array")
    if not allow_empty and not value:
        _fail("empty-list", f"{label} must not be empty")
    result = tuple(_nonempty_text(item, f"{label}[]") for item in value)
    if len(result) != len(set(result)):
        _fail("duplicate-list-value", f"{label} must not contain duplicates")
    return result


def _relative_path(value: Any, label: str) -> str:
    text = _nonempty_text(value, label)
    if "\\" in text or text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        _fail("invalid-relative-path", f"{label} must be a repository-relative POSIX path")
    parsed = PurePosixPath(text)
    if parsed.as_posix() != text or any(part in {"", ".", ".."} for part in parsed.parts):
        _fail(
            "invalid-relative-path",
            f"{label} must be normalized and must not contain traversal",
        )
    return text


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _fail("invalid-sha256", f"{label} must be lowercase SHA-256")
    return value


@dataclass(frozen=True)
class _CoverageGapExecutionBinding:
    gap_id: str
    gap_type: str
    requirement_codes: tuple[str, ...]
    impact: str
    blocks_ready_for_review: str
    status: str
    resolution: str
    affected_assertion_ids: tuple[str, ...]
    affected_atom_ids: tuple[str, ...]
    assertion_ids: tuple[str, ...]
    atom_ids: tuple[str, ...]
    obligation_ids: tuple[str, ...]


def _coverage_gap_execution_bindings(
    path: Path,
) -> dict[str, _CoverageGapExecutionBinding]:
    """Parse only exact execution-dependency fields from the canonical gap artifact."""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _fail(
            "coverage-gaps-artifact-unreadable",
            f"cannot read coverage gaps artifact {path}: {exc}",
        )
    matches = tuple(COVERAGE_GAP_HEADING_RE.finditer(text))
    result: dict[str, _CoverageGapExecutionBinding] = {}
    for index, match in enumerate(matches):
        gap_id = match.group(1)
        if gap_id in result:
            _fail(
                "duplicate-coverage-gap",
                f"coverage gaps artifact contains duplicate {gap_id}",
            )
        block = text[
            match.end() : (
                matches[index + 1].start() if index + 1 < len(matches) else len(text)
            )
        ]
        fields: dict[str, str] = {}

        def register_field(raw_key: str, raw_value: str) -> None:
            key = raw_key.strip().casefold().replace(" ", "_")
            if key in fields:
                _fail(
                    "duplicate-coverage-gap-field",
                    f"coverage gap {gap_id} declares {key} more than once",
                )
            fields[key] = raw_value.strip()

        for raw_line in block.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("|"):
                cells = [item.strip() for item in stripped.strip("|").split("|")]
                if (
                    len(cells) == 2
                    and cells[0].strip("`").casefold() not in {"field", "---"}
                ):
                    register_field(cells[0].strip("`"), cells[1].strip("`"))
            bold = re.fullmatch(r"\*\*([^*]+):\*\*\s*`?([^`]+?)`?\s*", stripped)
            if bold:
                register_field(bold.group(1), bold.group(2))

        def ids(key: str, pattern: re.Pattern[str]) -> tuple[str, ...]:
            raw_value = fields.get(key, "")
            if not raw_value:
                return ()
            execution_field = key.startswith("execution_")
            parsed: list[str] = []
            for raw_item in raw_value.split(";"):
                item = raw_item.strip()
                if len(item) >= 2 and item.startswith("`") and item.endswith("`"):
                    item = item[1:-1].strip()
                if not item or pattern.fullmatch(item) is None:
                    _fail(
                        (
                            "malformed-coverage-gap-execution-id-set"
                            if execution_field
                            else "malformed-coverage-gap-affected-id-set"
                        ),
                        f"coverage gap {gap_id}.{key} must be a semicolon-separated "
                        "list containing only canonical IDs",
                    )
                if item in parsed:
                    _fail(
                        (
                            "duplicate-coverage-gap-execution-id"
                            if execution_field
                            else "duplicate-coverage-gap-affected-id"
                        ),
                        f"coverage gap {gap_id}.{key} contains duplicate {item}",
                    )
                parsed.append(item)
            return tuple(parsed)

        declared_gap_id = fields.get("gap_id", gap_id)
        if declared_gap_id != gap_id:
            _fail(
                "coverage-gap-id-mismatch",
                f"coverage gap heading {gap_id} declares gap_id={declared_gap_id}",
            )
        result[gap_id] = _CoverageGapExecutionBinding(
            gap_id=gap_id,
            gap_type=fields.get("gap_type", "").strip().casefold(),
            requirement_codes=tuple(
                dict.fromkeys(
                    re.findall(
                        r"\b(?:BSR|GSR|DIT)\s+[A-Za-z0-9._/-]+\b",
                        fields.get("requirement_codes", ""),
                        flags=re.IGNORECASE,
                    )
                )
            ),
            impact=fields.get("impact", "").strip().casefold().replace("_", "-"),
            blocks_ready_for_review=fields.get(
                "blocks_ready_for_review", ""
            ).strip().casefold().replace("_", "-"),
            status=fields.get("status", "").strip().casefold(),
            resolution=fields.get("resolution", "").strip(),
            affected_assertion_ids=ids("affected_assertion_id", ASSERTION_ID_RE),
            affected_atom_ids=ids("affected_atom_id", ATOM_ID_RE),
            assertion_ids=ids("execution_assertion_ids", ASSERTION_ID_RE),
            atom_ids=ids("execution_atom_ids", ATOM_ID_RE),
            obligation_ids=ids("execution_obligation_ids", OBLIGATION_ID_RE),
        )
    return result


def _review_explanation(value: Any, label: str) -> str:
    """Require a concrete explanation without relying on language heuristics."""

    text = normalize_exact_source_text(_nonempty_text(value, label))
    if len(text) < 12 or not any(character.isalnum() for character in text):
        _fail(
            "placeholder-review-explanation",
            f"{label} must contain a concrete explanation of at least 12 characters",
        )
    if re.fullmatch(r"(?:<[^<>]+>|\[[^\[\]]+\]|\{[^{}]+\})", text):
        _fail(
            "placeholder-review-explanation",
            f"{label} must not be an unfilled template token",
        )
    return text


def _resolve_registered_path(repo_root: Path, relative: str, label: str) -> Path:
    root = repo_root.resolve()
    candidate = (root / Path(*PurePosixPath(relative).parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        _fail("path-escapes-repository", f"{label} resolves outside the repository: {relative}")
    if not candidate.is_file():
        _fail("registered-file-missing", f"{label} is not a file: {relative}")
    return candidate


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_exact_source_text(value: str) -> str:
    """Normalize transport whitespace only; preserve spelling, case and punctuation."""

    normalized = value.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    return re.sub(r"[ \t\n\f\v]+", " ", normalized).strip()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clarification_date(value: Any, label: str) -> str:
    result = _nonempty_text(value, label)
    try:
        date.fromisoformat(result)
    except ValueError as exc:
        _fail("invalid-clarification-date", f"{label} must be YYYY-MM-DD")
        raise AssertionError("unreachable") from exc
    return result


def _markdown_cell(value: str) -> str:
    result = value.strip()
    if len(result) >= 2 and result.startswith("`") and result.endswith("`"):
        result = result[1:-1].strip()
    return result


_CLARIFICATION_CARD_HEADING_RE = re.compile(
    r"(?m)^###\s+(?P<clarification_id>CLR-[A-Za-z0-9_-]+)\b[^\r\n]*$"
)
_CLARIFICATION_METADATA_RE = re.compile(
    r"(?ms)^```ya?ml[ \t]*\r?\n(?P<body>.*?)^```[ \t]*(?:\r?\n|$)"
)
_CLARIFICATION_ANSWER_RE = re.compile(
    r"(?ms)^#{4}\s+[^\r\n]*(?:Ответ БА|user_response)[^\r\n]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    r"^```(?:text|md|markdown)?[ \t]*\r?\n(?P<body>.*?)^```"
)


def _strip_structured_value(value: str) -> str:
    result = value.strip()
    if (
        len(result) >= 2
        and result[0] == result[-1]
        and result[0] in {'"', "'"}
    ):
        result = result[1:-1].strip()
    return _markdown_cell(result)


def _parse_clarification_metadata(section: str) -> dict[str, str]:
    match = _CLARIFICATION_METADATA_RE.search(section)
    if match is None:
        return {}
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)", line)
        if key_match is None:
            continue
        fields[key_match.group(1)] = _strip_structured_value(key_match.group(2))
    return fields


def _clarification_card_rows(
    text: str,
    *,
    source_path: str,
    required: set[str],
) -> dict[str, Mapping[str, str]]:
    rows_by_id: dict[str, Mapping[str, str]] = {}
    matches = list(_CLARIFICATION_CARD_HEADING_RE.finditer(text))
    for index, match in enumerate(matches):
        section_start = match.start()
        section_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )
        section = text[section_start:section_end]
        row = _parse_clarification_metadata(section)
        clarification_id = row.get("clarification_id") or match.group(
            "clarification_id"
        )
        row["clarification_id"] = clarification_id
        answer_match = _CLARIFICATION_ANSWER_RE.search(section)
        if answer_match is not None:
            row["user_response"] = answer_match.group("body").strip()
        missing = sorted(required - set(row))
        if missing:
            _fail(
                "invalid-clarification-card",
                f"clarification card {clarification_id} in {source_path} "
                f"misses required fields: {', '.join(missing)}",
            )
        if clarification_id in rows_by_id:
            _fail(
                "duplicate-clarification-record",
                f"clarification artifact repeats {clarification_id}",
            )
        rows_by_id[clarification_id] = row
    return rows_by_id


def _clarification_table_rows(
    text: str,
    *,
    source_path: str,
) -> dict[str, Mapping[str, str]]:
    """Read canonical clarification records without accepting prose lookalikes."""

    required = set(CLARIFICATION_TABLE_COLUMNS)
    lines = text.splitlines()
    rows_by_id: dict[str, Mapping[str, str]] = {}
    found_table = False
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
        columns = tuple(
            _markdown_cell(item) for item in header.strip("|").split("|")
        )
        if not required.issubset(columns):
            index += 1
            continue
        if len(columns) != len(set(columns)):
            _fail(
                "duplicate-clarification-table-column",
                f"clarification table in {source_path} contains duplicate columns",
            )
        found_table = True
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = tuple(
                _markdown_cell(item)
                for item in lines[index].strip().strip("|").split("|")
            )
            if len(cells) != len(columns):
                _fail(
                    "invalid-clarification-table-row",
                    f"clarification row {source_path}:{index + 1} has "
                    f"{len(cells)} cells for {len(columns)} columns",
                )
            row = dict(zip(columns, cells))
            clarification_id = row["clarification_id"]
            if clarification_id in rows_by_id:
                _fail(
                    "duplicate-clarification-record",
                    f"clarification artifact repeats {clarification_id}",
                )
            rows_by_id[clarification_id] = row
            index += 1
    if not found_table:
        card_rows = _clarification_card_rows(
            text,
            source_path=source_path,
            required=required,
        )
        if card_rows:
            return card_rows
        _fail(
            "clarification-records-missing",
            f"{source_path} has no canonical clarification table/card with fields "
            + ", ".join(CLARIFICATION_TABLE_COLUMNS),
        )
    return rows_by_id


def _clarification_requirement_codes(
    value: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized_value = _markdown_cell(value).strip()
    if allow_empty and normalized_value in {"", "-", "–", "—"}:
        return ()
    parts_list: list[str] = []
    for item in re.split(r"\s*;\s*", value):
        if not item.strip():
            continue
        part = _markdown_cell(item)
        compact_range = re.fullmatch(
            r"(?P<prefix>[A-Z][A-Z0-9_-]*)\s+(?P<start>[1-9][0-9]*)"
            r"\s*[-–—]\s*(?:(?P<end_prefix>[A-Z][A-Z0-9_-]*)\s+)?"
            r"(?P<end>[1-9][0-9]*)",
            part,
        )
        if compact_range is None:
            parts_list.append(part)
            continue
        prefix = compact_range.group("prefix")
        end_prefix = compact_range.group("end_prefix")
        start = int(compact_range.group("start"))
        end = int(compact_range.group("end"))
        if end_prefix not in {None, prefix} or end < start or end - start > 100:
            _fail(
                "invalid-clarification-requirement-code-range",
                f"approved clarification requirement code range is invalid: {part}",
            )
        parts_list.extend(f"{prefix} {number}" for number in range(start, end + 1))
    parts = tuple(parts_list)
    if not parts and not allow_empty:
        _fail(
            "clarification-requirement-codes-missing",
            "approved clarification must bind at least one requirement code",
        )
    if len(parts) != len(set(parts)):
        _fail(
            "duplicate-clarification-requirement-code",
            "approved clarification requirement_codes contain duplicates",
        )
    return parts


def contains_token_bounded_source_fragment(source_text: str, fragment: str) -> bool:
    """Return true when a literal fragment does not cut a Unicode alnum token."""

    if not fragment:
        return False
    offset = 0
    while True:
        index = source_text.find(fragment, offset)
        if index < 0:
            return False
        end = index + len(fragment)
        cuts_left_token = (
            fragment[0].isalnum()
            and index > 0
            and source_text[index - 1].isalnum()
        )
        cuts_right_token = (
            fragment[-1].isalnum()
            and end < len(source_text)
            and source_text[end].isalnum()
        )
        if not cuts_left_token and not cuts_right_token:
            return True
        offset = index + 1


def scope_boundary_source_locator(source_path: str, exact_source_text: str) -> str:
    """Build the canonical content-bound locator used by boundary exclusions."""

    normalized_path = _relative_path(source_path, "scope boundary source path")
    normalized_text = normalize_exact_source_text(
        _nonempty_text(exact_source_text, "scope boundary exact source text")
    )
    fragment_digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return f"{normalized_path}#text-sha256={fragment_digest}"


def _pdf_page_number(value: str, label: str) -> int:
    match = PDF_PAGE_LOCATOR_RE.fullmatch(_nonempty_text(value, label))
    if match is None:
        _fail(
            "invalid-pdf-evidence-locator",
            f"{label} must use the exact 1-based form page:<positive-integer>",
        )
    return int(match.group(1))


def _extract_pdf_page_text(path: Path, page_number: int, label: str) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        if page_number > len(reader.pages):
            _fail(
                "pdf-evidence-page-out-of-range",
                f"{label} names page {page_number}, but the PDF has "
                f"{len(reader.pages)} pages",
            )
        extracted = reader.pages[page_number - 1].extract_text() or ""
    except SourceAssertionContractError:
        raise
    except Exception as exc:
        _fail(
            "pdf-evidence-unreadable",
            f"{label} cannot be extracted from the registered PDF: {exc}",
        )
    return normalize_exact_source_text(extracted)


@dataclass(frozen=True)
class RegisteredSource:
    path: str
    sha256: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RegisteredSource":
        _exact_fields(payload, required={"path", "sha256"}, label="source")
        return cls(
            path=_relative_path(payload["path"], "source.path"),
            sha256=_sha256(payload["sha256"], "source.sha256"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class SourceRow:
    source_row_id: str
    source_path: str
    source_locator: str
    bounded_source_text: str
    source_context_class: str
    candidate_id: str | None = None
    scope_disposition: str = "yes"
    requirement_codes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceRow":
        _exact_fields(
            payload,
            required={
                "source_row_id",
                "source_path",
                "source_locator",
                "bounded_source_text",
                "source_context_class",
                "candidate_id",
                "scope_disposition",
                "requirement_codes",
            },
            label="source row",
        )
        result = cls(
            source_row_id=_nonempty_text(
                payload["source_row_id"], "source row.source_row_id"
            ),
            source_path=_relative_path(
                payload["source_path"], "source row.source_path"
            ),
            source_locator=_nonempty_text(
                payload["source_locator"], "source row.source_locator"
            ),
            bounded_source_text=_nonempty_text(
                payload["bounded_source_text"], "source row.bounded_source_text"
            ),
            source_context_class=_nonempty_text(
                payload["source_context_class"],
                "source row.source_context_class",
            ),
            candidate_id=(
                _nonempty_text(payload["candidate_id"], "source row.candidate_id")
                if payload["candidate_id"] is not None
                else None
            ),
            scope_disposition=_nonempty_text(
                payload["scope_disposition"],
                "source row.scope_disposition",
            ),
            requirement_codes=_text_list(
                payload["requirement_codes"],
                "source row.requirement_codes",
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", self.source_row_id) is None:
            _fail(
                "invalid-source-row-id",
                "source row.source_row_id must name one SRC-* row",
            )
        _relative_path(self.source_path, "source row.source_path")
        _nonempty_text(self.source_locator, "source row.source_locator")
        _nonempty_text(self.bounded_source_text, "source row.bounded_source_text")
        if self.source_context_class not in SOURCE_CONTEXT_CLASSES:
            _fail(
                "invalid-source-context-class",
                "source row.source_context_class must be one of "
                f"{sorted(SOURCE_CONTEXT_CLASSES)}",
            )
        if (
            self.candidate_id is not None
            and SOURCE_CANDIDATE_ID_RE.fullmatch(self.candidate_id) is None
        ):
            _fail(
                "invalid-source-candidate-id",
                "source row.candidate_id must be null or one SRC-CAND-* identifier",
            )
        if self.scope_disposition not in SOURCE_ROW_SCOPE_DISPOSITIONS:
            _fail(
                "invalid-source-row-scope-disposition",
                "source row.scope_disposition must be one of "
                f"{sorted(SOURCE_ROW_SCOPE_DISPOSITIONS)}",
            )
        if len(self.requirement_codes) != len(set(self.requirement_codes)):
            _fail(
                "duplicate-source-row-requirement-code",
                "source row.requirement_codes must not contain duplicates",
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "source_row_id": self.source_row_id,
            "source_path": self.source_path,
            "source_locator": self.source_locator,
            "bounded_source_text": self.bounded_source_text,
            "source_context_class": self.source_context_class,
            "candidate_id": self.candidate_id,
            "scope_disposition": self.scope_disposition,
            "requirement_codes": list(self.requirement_codes),
        }


@dataclass(frozen=True)
class SupportingSourceBinding:
    source_row_id: str
    evidence_role: str
    exact_source_fragment: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SupportingSourceBinding":
        _exact_fields(
            payload,
            required={"source_row_id", "evidence_role", "exact_source_fragment"},
            label="supporting source binding",
        )
        result = cls(
            source_row_id=_nonempty_text(
                payload["source_row_id"],
                "supporting source binding.source_row_id",
            ),
            evidence_role=_nonempty_text(
                payload["evidence_role"],
                "supporting source binding.evidence_role",
            ),
            exact_source_fragment=_nonempty_text(
                payload["exact_source_fragment"],
                "supporting source binding.exact_source_fragment",
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", self.source_row_id) is None:
            _fail(
                "invalid-supporting-source-row-id",
                "supporting source binding.source_row_id must name one SRC-* row",
            )
        if self.evidence_role not in SUPPORTING_SOURCE_EVIDENCE_ROLES:
            _fail(
                "invalid-supporting-source-evidence-role",
                "supporting source binding.evidence_role must be one of "
                f"{sorted(SUPPORTING_SOURCE_EVIDENCE_ROLES)}",
            )
        _nonempty_text(
            self.exact_source_fragment,
            "supporting source binding.exact_source_fragment",
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "source_row_id": self.source_row_id,
            "evidence_role": self.evidence_role,
            "exact_source_fragment": self.exact_source_fragment,
        }


@dataclass(frozen=True)
class RequirementCodeBinding:
    requirement_code: str
    source_row_id: str
    provenance_role: str
    exact_source_fragment: str | None = None
    evidence_source_path: str | None = None
    evidence_locator: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RequirementCodeBinding":
        _exact_fields(
            payload,
            required={
                "requirement_code",
                "source_row_id",
                "provenance_role",
                "exact_source_fragment",
                "evidence_source_path",
                "evidence_locator",
            },
            label="requirement code binding",
        )
        result = cls(
            requirement_code=_nonempty_text(
                payload["requirement_code"],
                "requirement code binding.requirement_code",
            ),
            source_row_id=_nonempty_text(
                payload["source_row_id"],
                "requirement code binding.source_row_id",
            ),
            provenance_role=_nonempty_text(
                payload["provenance_role"],
                "requirement code binding.provenance_role",
            ),
            exact_source_fragment=(
                _nonempty_text(
                    payload["exact_source_fragment"],
                    "requirement code binding.exact_source_fragment",
                )
                if payload["exact_source_fragment"] is not None
                else None
            ),
            evidence_source_path=(
                _relative_path(
                    payload["evidence_source_path"],
                    "requirement code binding.evidence_source_path",
                )
                if payload["evidence_source_path"] is not None
                else None
            ),
            evidence_locator=(
                _nonempty_text(
                    payload["evidence_locator"],
                    "requirement code binding.evidence_locator",
                )
                if payload["evidence_locator"] is not None
                else None
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", self.source_row_id) is None:
            _fail(
                "invalid-requirement-code-source-row-id",
                "requirement code binding.source_row_id must name one SRC-* row",
            )
        if self.provenance_role not in REQUIREMENT_CODE_PROVENANCE_ROLES:
            _fail(
                "invalid-requirement-code-provenance-role",
                "requirement code binding.provenance_role must be one of "
                f"{sorted(REQUIREMENT_CODE_PROVENANCE_ROLES)}",
            )
        if self.provenance_role == "pdf-parity":
            if self.evidence_source_path is None or self.evidence_locator is None:
                _fail(
                    "pdf-requirement-code-evidence-binding-missing",
                    "PDF-only requirement code provenance requires exact "
                    "evidence_source_path and evidence_locator",
                )
            if self.exact_source_fragment is not None:
                _fail(
                    "pdf-requirement-code-xhtml-fragment-invalid",
                    "PDF-only requirement code provenance requires null "
                    "exact_source_fragment",
                )
            _relative_path(
                self.evidence_source_path,
                "requirement code binding.evidence_source_path",
            )
            if PurePosixPath(self.evidence_source_path).suffix.lower() != ".pdf":
                _fail(
                    "pdf-requirement-code-evidence-source-invalid",
                    "PDF-only requirement code provenance requires a .pdf evidence source",
                )
            _pdf_page_number(
                self.evidence_locator,
                "requirement code binding.evidence_locator",
            )
        else:
            if self.exact_source_fragment is None:
                _fail(
                    "xhtml-requirement-code-fragment-missing",
                    "XHTML-row requirement code provenance requires "
                    "exact_source_fragment",
                )
            _nonempty_text(
                self.exact_source_fragment,
                "requirement code binding.exact_source_fragment",
            )
            if self.evidence_source_path is not None or self.evidence_locator is not None:
                _fail(
                    "xhtml-requirement-code-pdf-evidence-invalid",
                    "XHTML-row requirement code provenance requires null PDF evidence fields",
                )
        _nonempty_text(
            self.requirement_code,
            "requirement code binding.requirement_code",
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "requirement_code": self.requirement_code,
            "source_row_id": self.source_row_id,
            "provenance_role": self.provenance_role,
            "exact_source_fragment": self.exact_source_fragment,
            "evidence_source_path": self.evidence_source_path,
            "evidence_locator": self.evidence_locator,
        }


@dataclass(frozen=True)
class ClauseEvidenceBinding:
    clause_kind: str
    clause_index: int
    source_row_id: str
    evidence_role: str
    exact_source_fragment: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ClauseEvidenceBinding":
        _exact_fields(
            payload,
            required={
                "clause_kind",
                "clause_index",
                "source_row_id",
                "evidence_role",
                "exact_source_fragment",
            },
            label="clause evidence binding",
        )
        if type(payload["clause_index"]) is not int:
            _fail(
                "invalid-clause-evidence-index",
                "clause evidence binding.clause_index must be an integer",
            )
        result = cls(
            clause_kind=_nonempty_text(
                payload["clause_kind"],
                "clause evidence binding.clause_kind",
            ),
            clause_index=payload["clause_index"],
            source_row_id=_nonempty_text(
                payload["source_row_id"],
                "clause evidence binding.source_row_id",
            ),
            evidence_role=_nonempty_text(
                payload["evidence_role"],
                "clause evidence binding.evidence_role",
            ),
            exact_source_fragment=_nonempty_text(
                payload["exact_source_fragment"],
                "clause evidence binding.exact_source_fragment",
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if self.clause_kind not in CLAUSE_EVIDENCE_KINDS:
            _fail(
                "invalid-clause-evidence-kind",
                "clause evidence binding.clause_kind must be one of "
                f"{sorted(CLAUSE_EVIDENCE_KINDS)}",
            )
        if type(self.clause_index) is not int or self.clause_index < 0:
            _fail(
                "invalid-clause-evidence-index",
                "clause evidence binding.clause_index must be a non-negative integer",
            )
        if re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", self.source_row_id) is None:
            _fail(
                "invalid-clause-evidence-source-row-id",
                "clause evidence binding.source_row_id must name one SRC-* row",
            )
        if self.evidence_role != self.clause_kind:
            _fail(
                "clause-evidence-role-kind-mismatch",
                "clause evidence binding.evidence_role must equal clause_kind",
            )
        _nonempty_text(
            self.exact_source_fragment,
            "clause evidence binding.exact_source_fragment",
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "clause_kind": self.clause_kind,
            "clause_index": self.clause_index,
            "source_row_id": self.source_row_id,
            "evidence_role": self.evidence_role,
            "exact_source_fragment": self.exact_source_fragment,
        }


@dataclass(frozen=True)
class RegisteredEvidenceSource:
    """Hash-bound binary or auxiliary evidence used to approve source semantics.

    Assertion text is still located in a UTF-8 ``RegisteredSource``.  This
    separate binding keeps the DOCX source of truth, PDF parity evidence and
    supporting material inside the reviewed manifest digest without trying to
    decode binary files as text or inventing assertion chains for them.
    """

    path: str
    sha256: str
    role: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RegisteredEvidenceSource":
        _exact_fields(
            payload,
            required={"path", "sha256", "role"},
            label="evidence source",
        )
        result = cls(
            path=_relative_path(payload["path"], "evidence_source.path"),
            sha256=_sha256(payload["sha256"], "evidence_source.sha256"),
            role=_nonempty_text(payload["role"], "evidence_source.role"),
        )
        if result.role not in EVIDENCE_SOURCE_ROLES:
            _fail(
                "invalid-evidence-source-role",
                "evidence_source.role must be one of "
                f"{sorted(EVIDENCE_SOURCE_ROLES)}",
            )
        return result

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256, "role": self.role}


@dataclass(frozen=True)
class ApprovedClarification:
    """One authoritative answer bound to one exact structured Markdown row."""

    clarification_id: str
    gap_id: str
    scope_slug: str
    requirement_codes: tuple[str, ...]
    authority: str
    response_status: str
    response_type: str
    answered_at: str
    exact_answer: str
    exact_answer_sha256: str
    evidence_source_path: str
    evidence_source_sha256: str
    binding_scope: str = "requirement-code"
    source_row_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ApprovedClarification":
        _exact_fields(
            payload,
            required={
                "clarification_id",
                "gap_id",
                "scope_slug",
                "requirement_codes",
                "authority",
                "response_status",
                "response_type",
                "answered_at",
                "exact_answer",
                "exact_answer_sha256",
                "evidence_source_path",
                "evidence_source_sha256",
            },
            optional={"binding_scope", "source_row_ids"},
            label="approved clarification",
        )
        has_binding_scope = "binding_scope" in payload
        has_source_row_ids = "source_row_ids" in payload
        if has_binding_scope != has_source_row_ids:
            _fail(
                "partial-clarification-binding-scope",
                "approved clarification must declare binding_scope and source_row_ids together",
            )
        result = cls(
            clarification_id=_nonempty_text(
                payload["clarification_id"],
                "approved clarification.clarification_id",
            ),
            gap_id=_nonempty_text(
                payload["gap_id"], "approved clarification.gap_id"
            ),
            scope_slug=_nonempty_text(
                payload["scope_slug"], "approved clarification.scope_slug"
            ),
            requirement_codes=_text_list(
                payload["requirement_codes"],
                "approved clarification.requirement_codes",
                allow_empty=True,
            ),
            authority=_nonempty_text(
                payload["authority"], "approved clarification.authority"
            ),
            response_status=_nonempty_text(
                payload["response_status"],
                "approved clarification.response_status",
            ),
            response_type=_nonempty_text(
                payload["response_type"], "approved clarification.response_type"
            ),
            answered_at=_clarification_date(
                payload["answered_at"], "approved clarification.answered_at"
            ),
            exact_answer=_nonempty_text(
                payload["exact_answer"], "approved clarification.exact_answer"
            ),
            exact_answer_sha256=_sha256(
                payload["exact_answer_sha256"],
                "approved clarification.exact_answer_sha256",
            ),
            evidence_source_path=_relative_path(
                payload["evidence_source_path"],
                "approved clarification.evidence_source_path",
            ),
            evidence_source_sha256=_sha256(
                payload["evidence_source_sha256"],
                "approved clarification.evidence_source_sha256",
            ),
            binding_scope=(
                _nonempty_text(
                    payload["binding_scope"],
                    "approved clarification.binding_scope",
                )
                if has_binding_scope
                else "requirement-code"
            ),
            source_row_ids=(
                _text_list(
                    payload["source_row_ids"],
                    "approved clarification.source_row_ids",
                    allow_empty=True,
                )
                if has_source_row_ids
                else ()
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if CLARIFICATION_ID_RE.fullmatch(self.clarification_id) is None:
            _fail(
                "invalid-clarification-id",
                "approved clarification.clarification_id must name one CLR-*",
            )
        if GAP_ID_RE.fullmatch(self.gap_id) is None:
            _fail(
                "invalid-clarification-gap-id",
                "approved clarification.gap_id must name one GAP-*",
            )
        _nonempty_text(self.scope_slug, "approved clarification.scope_slug")
        if self.binding_scope not in CLARIFICATION_BINDING_SCOPES:
            _fail(
                "invalid-clarification-binding-scope",
                f"{self.clarification_id}.binding_scope must be one of "
                f"{sorted(CLARIFICATION_BINDING_SCOPES)}",
            )
        if len(self.requirement_codes) != len(set(self.requirement_codes)):
            _fail(
                "duplicate-clarification-requirement-code",
                f"{self.clarification_id} requirement_codes contain duplicates",
            )
        if len(self.source_row_ids) != len(set(self.source_row_ids)):
            _fail(
                "duplicate-clarification-source-row-id",
                f"{self.clarification_id} source_row_ids contain duplicates",
            )
        if self.binding_scope == "requirement-code":
            if not self.requirement_codes:
                _fail(
                    "clarification-requirement-codes-missing",
                    f"{self.clarification_id} must bind at least one requirement code",
                )
            if self.source_row_ids:
                _fail(
                    "clarification-requirement-code-has-context-rows",
                    f"{self.clarification_id} requirement-code binding must not declare source_row_ids",
                )
        else:
            if self.requirement_codes:
                _fail(
                    "clarification-source-context-has-requirement-codes",
                    f"{self.clarification_id} source-context binding must not declare requirement_codes",
                )
            if not self.source_row_ids:
                _fail(
                    "clarification-source-context-rows-missing",
                    f"{self.clarification_id} source-context binding must declare source_row_ids",
                )
            for source_row_id in self.source_row_ids:
                if re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", source_row_id) is None:
                    _fail(
                        "invalid-clarification-source-row-id",
                        f"{self.clarification_id} source_row_ids must name SRC-* rows",
                    )
        if self.authority not in CLARIFICATION_AUTHORITIES:
            _fail(
                "invalid-clarification-authority",
                f"{self.clarification_id}.authority must be one of "
                f"{sorted(CLARIFICATION_AUTHORITIES)}",
            )
        if self.response_status not in CLARIFICATION_RESPONSE_STATUSES:
            _fail(
                "invalid-clarification-response-status",
                f"{self.clarification_id}.response_status must be one of "
                f"{sorted(CLARIFICATION_RESPONSE_STATUSES)}",
            )
        if self.response_status != "answered":
            _fail(
                "unapproved-clarification-response-status",
                f"{self.clarification_id} cannot be ready evidence with "
                f"response_status={self.response_status}",
            )
        if self.response_type not in CLARIFICATION_RESPONSE_TYPES:
            _fail(
                "invalid-clarification-response-type",
                f"{self.clarification_id}.response_type must be one of "
                f"{sorted(CLARIFICATION_RESPONSE_TYPES)}",
            )
        if self.response_type not in APPROVED_CLARIFICATION_RESPONSE_TYPES:
            _fail(
                "unapproved-clarification-response-type",
                f"{self.clarification_id} cannot be ready evidence with "
                f"response_type={self.response_type}",
            )
        expected_response_type = CLARIFICATION_AUTHORITY_RESPONSE_TYPES[self.authority]
        if self.response_type != expected_response_type:
            _fail(
                "clarification-authority-response-type-mismatch",
                f"{self.clarification_id} authority={self.authority} requires "
                f"response_type={expected_response_type}",
            )
        _clarification_date(
            self.answered_at, "approved clarification.answered_at"
        )
        if self.exact_answer_sha256 != _sha256_text(self.exact_answer):
            _fail(
                "clarification-answer-digest-mismatch",
                f"{self.clarification_id}.exact_answer_sha256 does not bind exact_answer",
            )
        _relative_path(
            self.evidence_source_path,
            "approved clarification.evidence_source_path",
        )
        _sha256(
            self.evidence_source_sha256,
            "approved clarification.evidence_source_sha256",
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "clarification_id": self.clarification_id,
            "gap_id": self.gap_id,
            "scope_slug": self.scope_slug,
            "requirement_codes": list(self.requirement_codes),
            "authority": self.authority,
            "response_status": self.response_status,
            "response_type": self.response_type,
            "answered_at": self.answered_at,
            "exact_answer": self.exact_answer,
            "exact_answer_sha256": self.exact_answer_sha256,
            "evidence_source_path": self.evidence_source_path,
            "evidence_source_sha256": self.evidence_source_sha256,
            "binding_scope": self.binding_scope,
            "source_row_ids": list(self.source_row_ids),
        }


@dataclass(frozen=True)
class ClarificationClauseBinding:
    clarification_id: str
    clause_kind: str
    clause_index: int
    requirement_codes: tuple[str, ...]
    exact_answer_sha256: str
    binding_scope: str = "requirement-code"
    source_row_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ClarificationClauseBinding":
        _exact_fields(
            payload,
            required={
                "clarification_id",
                "clause_kind",
                "clause_index",
                "requirement_codes",
                "exact_answer_sha256",
            },
            optional={"binding_scope", "source_row_ids"},
            label="clarification clause binding",
        )
        has_binding_scope = "binding_scope" in payload
        has_source_row_ids = "source_row_ids" in payload
        if has_binding_scope != has_source_row_ids:
            _fail(
                "partial-clarification-clause-binding-scope",
                "clarification clause binding must declare binding_scope and source_row_ids together",
            )
        result = cls(
            clarification_id=_nonempty_text(
                payload["clarification_id"],
                "clarification clause binding.clarification_id",
            ),
            clause_kind=_nonempty_text(
                payload["clause_kind"],
                "clarification clause binding.clause_kind",
            ),
            clause_index=payload["clause_index"],
            requirement_codes=_text_list(
                payload["requirement_codes"],
                "clarification clause binding.requirement_codes",
                allow_empty=True,
            ),
            exact_answer_sha256=_sha256(
                payload["exact_answer_sha256"],
                "clarification clause binding.exact_answer_sha256",
            ),
            binding_scope=(
                _nonempty_text(
                    payload["binding_scope"],
                    "clarification clause binding.binding_scope",
                )
                if has_binding_scope
                else "requirement-code"
            ),
            source_row_ids=(
                _text_list(
                    payload["source_row_ids"],
                    "clarification clause binding.source_row_ids",
                    allow_empty=True,
                )
                if has_source_row_ids
                else ()
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if CLARIFICATION_ID_RE.fullmatch(self.clarification_id) is None:
            _fail(
                "invalid-clarification-id",
                "clarification clause binding.clarification_id must name one CLR-*",
            )
        if self.clause_kind not in CLARIFICATION_CLAUSE_KINDS:
            _fail(
                "invalid-clarification-clause-kind",
                "clarification clause binding.clause_kind must be one of "
                f"{sorted(CLARIFICATION_CLAUSE_KINDS)}",
            )
        if type(self.clause_index) is not int or self.clause_index < 0:
            _fail(
                "invalid-clarification-clause-index",
                "clarification clause binding.clause_index must be a non-negative integer",
            )
        if self.clause_kind == "canonical" and self.clause_index != 0:
            _fail(
                "clarification-canonical-index-invalid",
                "canonical clarification binding must use clause_index=0",
            )
        if self.binding_scope not in CLARIFICATION_BINDING_SCOPES:
            _fail(
                "invalid-clarification-binding-scope",
                "clarification clause binding.binding_scope must be one of "
                f"{sorted(CLARIFICATION_BINDING_SCOPES)}",
            )
        if (
            self.clause_kind == "canonical"
            and self.binding_scope != "source-context"
        ):
            _fail(
                "clarification-canonical-binding-scope-invalid",
                "canonical clarification binding requires binding_scope=source-context",
            )
        if len(self.requirement_codes) != len(set(self.requirement_codes)):
            _fail(
                "duplicate-clarification-binding-requirement-code",
                "clarification clause binding requirement_codes contain duplicates",
            )
        if len(self.source_row_ids) != len(set(self.source_row_ids)):
            _fail(
                "duplicate-clarification-binding-source-row-id",
                "clarification clause binding source_row_ids contain duplicates",
            )
        if self.binding_scope == "requirement-code":
            if not self.requirement_codes:
                _fail(
                    "clarification-binding-requirement-codes-missing",
                    "clarification clause binding must name at least one local requirement code",
                )
            if self.source_row_ids:
                _fail(
                    "clarification-binding-requirement-code-has-context-rows",
                    "requirement-code clause binding must not declare source_row_ids",
                )
        else:
            if self.requirement_codes:
                _fail(
                    "clarification-binding-source-context-has-requirement-codes",
                    "source-context clause binding must not declare requirement_codes",
                )
            if not self.source_row_ids:
                _fail(
                    "clarification-binding-source-context-rows-missing",
                    "source-context clause binding must declare source_row_ids",
                )
            for source_row_id in self.source_row_ids:
                if re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", source_row_id) is None:
                    _fail(
                        "invalid-clarification-binding-source-row-id",
                        "source-context clause binding source_row_ids must name SRC-* rows",
                    )
        _sha256(
            self.exact_answer_sha256,
            "clarification clause binding.exact_answer_sha256",
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "clarification_id": self.clarification_id,
            "clause_kind": self.clause_kind,
            "clause_index": self.clause_index,
            "requirement_codes": list(self.requirement_codes),
            "exact_answer_sha256": self.exact_answer_sha256,
            "binding_scope": self.binding_scope,
            "source_row_ids": list(self.source_row_ids),
        }


@dataclass(frozen=True)
class RegisteredArtifact:
    """One repository artifact whose exact bytes are part of the manifest contract."""

    path: str
    sha256: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RegisteredArtifact":
        _exact_fields(
            payload,
            required={"path", "sha256"},
            label="registered artifact",
        )
        return cls(
            path=_relative_path(payload["path"], "registered_artifact.path"),
            sha256=_sha256(payload["sha256"], "registered_artifact.sha256"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class RegisteredMockup:
    path: str
    sha256: str
    screen_name: str
    locators: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RegisteredMockup":
        _exact_fields(
            payload,
            required={"path", "sha256", "screen_name", "locators"},
            label="mockup",
        )
        return cls(
            path=_relative_path(payload["path"], "mockup.path"),
            sha256=_sha256(payload["sha256"], "mockup.sha256"),
            screen_name=_nonempty_text(payload["screen_name"], "mockup.screen_name"),
            locators=_text_list(payload["locators"], "mockup.locators", allow_empty=False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "screen_name": self.screen_name,
            "locators": list(self.locators),
        }


@dataclass(frozen=True)
class SourceAssertion:
    assertion_id: str
    source_path: str
    source_context_class: str
    locator: str
    exact_source_text: str
    canonical_statement: str
    polarity: str
    semantic_disposition: str
    execution_readiness: str
    execution_readiness_rationale: str
    risk: str
    condition_clauses: tuple[str, ...]
    action_clauses: tuple[str, ...]
    oracle_clauses: tuple[str, ...]
    requirement_codes: tuple[str, ...]
    requirement_code_bindings: tuple[RequirementCodeBinding, ...]
    clause_evidence_bindings: tuple[ClauseEvidenceBinding, ...]
    source_row_id: str
    atom_id: str
    obligation_ids: tuple[str, ...]
    execution_dependency_gap_ids: tuple[str, ...]
    primary_gap_id: str | None
    disposition_rationale: str = ""
    exact_source_fragments: tuple[str, ...] = ()
    supporting_source_bindings: tuple[SupportingSourceBinding, ...] = ()
    clarification_clause_bindings: tuple[ClarificationClauseBinding, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceAssertion":
        _exact_fields(
            payload,
            required={
                "assertion_id",
                "source_path",
                "source_context_class",
                "locator",
                "exact_source_text",
                "canonical_statement",
                "polarity",
                "semantic_disposition",
                "execution_readiness",
                "execution_readiness_rationale",
                "risk",
                "condition_clauses",
                "action_clauses",
                "oracle_clauses",
                "requirement_codes",
                "requirement_code_bindings",
                "clause_evidence_bindings",
                "source_row_id",
                "atom_id",
                "obligation_ids",
                "execution_dependency_gap_ids",
                "primary_gap_id",
                "supporting_source_bindings",
                "clarification_clause_bindings",
            },
            optional={"disposition_rationale", "exact_source_fragments"},
            label="assertion",
        )
        assertion = cls(
            assertion_id=_nonempty_text(payload["assertion_id"], "assertion.assertion_id"),
            source_path=_relative_path(payload["source_path"], "assertion.source_path"),
            source_context_class=_nonempty_text(
                payload["source_context_class"],
                "assertion.source_context_class",
            ),
            locator=_nonempty_text(payload["locator"], "assertion.locator"),
            exact_source_text=_nonempty_text(
                payload["exact_source_text"], "assertion.exact_source_text"
            ),
            canonical_statement=_nonempty_text(
                payload["canonical_statement"], "assertion.canonical_statement"
            ),
            polarity=_nonempty_text(payload["polarity"], "assertion.polarity"),
            semantic_disposition=_nonempty_text(
                payload["semantic_disposition"], "assertion.semantic_disposition"
            ),
            execution_readiness=_nonempty_text(
                payload["execution_readiness"],
                "assertion.execution_readiness",
            ),
            execution_readiness_rationale=_nonempty_text(
                payload["execution_readiness_rationale"],
                "assertion.execution_readiness_rationale",
            ),
            risk=_nonempty_text(payload["risk"], "assertion.risk"),
            condition_clauses=_text_list(
                payload["condition_clauses"], "assertion.condition_clauses"
            ),
            action_clauses=_text_list(
                payload["action_clauses"], "assertion.action_clauses"
            ),
            oracle_clauses=_text_list(
                payload["oracle_clauses"], "assertion.oracle_clauses"
            ),
            requirement_codes=_text_list(
                payload["requirement_codes"], "assertion.requirement_codes"
            ),
            requirement_code_bindings=tuple(
                RequirementCodeBinding.from_dict(item)
                for item in payload["requirement_code_bindings"]
            )
            if isinstance(payload["requirement_code_bindings"], list)
            else _fail(
                "invalid-requirement-code-bindings",
                "assertion.requirement_code_bindings must be a JSON array",
            ),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding.from_dict(item)
                for item in payload["clause_evidence_bindings"]
            )
            if isinstance(payload["clause_evidence_bindings"], list)
            else _fail(
                "invalid-clause-evidence-bindings",
                "assertion.clause_evidence_bindings must be a JSON array",
            ),
            source_row_id=_nonempty_text(payload["source_row_id"], "assertion.source_row_id"),
            atom_id=_nonempty_text(payload["atom_id"], "assertion.atom_id"),
            obligation_ids=_text_list(
                payload["obligation_ids"], "assertion.obligation_ids"
            ),
            execution_dependency_gap_ids=_text_list(
                payload["execution_dependency_gap_ids"],
                "assertion.execution_dependency_gap_ids",
            ),
            primary_gap_id=_optional_gap_id(
                payload["primary_gap_id"], "assertion.primary_gap_id"
            ),
            disposition_rationale=(
                _nonempty_text(
                    payload["disposition_rationale"],
                    "assertion.disposition_rationale",
                )
                if "disposition_rationale" in payload
                else ""
            ),
            exact_source_fragments=(
                _text_list(
                    payload["exact_source_fragments"],
                    "assertion.exact_source_fragments",
                )
                if "exact_source_fragments" in payload
                else ()
            ),
            supporting_source_bindings=tuple(
                SupportingSourceBinding.from_dict(item)
                for item in payload["supporting_source_bindings"]
            )
            if isinstance(payload["supporting_source_bindings"], list)
            else _fail(
                "invalid-supporting-source-bindings",
                "assertion.supporting_source_bindings must be a JSON array",
            ),
            clarification_clause_bindings=tuple(
                ClarificationClauseBinding.from_dict(item)
                for item in payload["clarification_clause_bindings"]
            )
            if isinstance(payload["clarification_clause_bindings"], list)
            else _fail(
                "invalid-clarification-clause-bindings",
                "assertion.clarification_clause_bindings must be a JSON array",
            ),
        )
        assertion.validate_shape()
        return assertion

    def validate_shape(self) -> None:
        if self.source_context_class not in SOURCE_CONTEXT_CLASSES:
            _fail(
                "invalid-source-context-class",
                f"{self.assertion_id}.source_context_class must be one of "
                f"{sorted(SOURCE_CONTEXT_CLASSES)}",
            )
        if self.polarity not in POLARITIES:
            _fail(
                "invalid-polarity",
                f"{self.assertion_id}.polarity must be one of {sorted(POLARITIES)}",
            )
        if self.semantic_disposition not in SEMANTIC_DISPOSITIONS:
            _fail(
                "invalid-semantic-disposition",
                f"{self.assertion_id}.semantic_disposition must be one of "
                f"{sorted(SEMANTIC_DISPOSITIONS)}",
            )
        if self.execution_readiness not in EXECUTION_READINESS_VALUES:
            _fail(
                "invalid-execution-readiness",
                f"{self.assertion_id}.execution_readiness must be one of "
                f"{sorted(EXECUTION_READINESS_VALUES)}",
            )
        if self.semantic_disposition == "not-applicable":
            expected_readiness = {"not-applicable"}
        elif self.semantic_disposition == "ambiguous":
            expected_readiness = {"dependency-blocked"}
        else:
            expected_readiness = {"ready", "dependency-blocked"}
        if self.execution_readiness not in expected_readiness:
            _fail(
                "execution-readiness-disposition-mismatch",
                f"{self.assertion_id} semantic_disposition={self.semantic_disposition} "
                f"requires execution_readiness in {sorted(expected_readiness)}",
            )
        if self.execution_readiness == "dependency-blocked":
            if self.execution_readiness_rationale == NO_REQUIRED_CHANGE:
                _fail(
                    "dependency-blocked-rationale-missing",
                    f"{self.assertion_id} dependency-blocked execution requires a "
                    "substantive execution_readiness_rationale",
                )
            _review_explanation(
                self.execution_readiness_rationale,
                f"{self.assertion_id}.execution_readiness_rationale",
            )
        elif self.execution_readiness_rationale != NO_REQUIRED_CHANGE:
            _fail(
                "execution-readiness-rationale-invalid",
                f"{self.assertion_id} {self.execution_readiness} execution readiness "
                f"requires execution_readiness_rationale={NO_REQUIRED_CHANGE}",
            )
        if self.risk not in RISKS:
            _fail("invalid-risk", f"{self.assertion_id}.risk must be one of {sorted(RISKS)}")
        if self.primary_gap_id is not None and (
            not isinstance(self.primary_gap_id, str)
            or GAP_ID_RE.fullmatch(self.primary_gap_id) is None
        ):
            _fail(
                "invalid-gap-id",
                f"{self.assertion_id}.primary_gap_id must name one GAP-* or be null",
            )
        if ATOM_ID_RE.fullmatch(self.atom_id) is None:
            _fail("invalid-atom-id", f"{self.assertion_id}.atom_id must name one ATOM-*")
        for obligation_id in self.obligation_ids:
            if OBLIGATION_ID_RE.fullmatch(obligation_id) is None:
                _fail(
                    "invalid-obligation-id",
                    f"{self.assertion_id}.obligation_ids contains invalid id {obligation_id}",
                )
        for gap_id in self.execution_dependency_gap_ids:
            if GAP_ID_RE.fullmatch(gap_id) is None:
                _fail(
                    "invalid-execution-dependency-gap-id",
                    f"{self.assertion_id}.execution_dependency_gap_ids contains "
                    f"invalid id {gap_id}",
                )
        if len(self.execution_dependency_gap_ids) != len(
            set(self.execution_dependency_gap_ids)
        ):
            _fail(
                "duplicate-execution-dependency-gap-id",
                f"{self.assertion_id}.execution_dependency_gap_ids must not "
                "contain duplicates",
            )
        dependency_gap_ids_allowed = (
            self.semantic_disposition == "testable"
            and self.execution_readiness == "dependency-blocked"
        )
        if dependency_gap_ids_allowed and not self.execution_dependency_gap_ids:
            _fail(
                "execution-dependency-gap-missing",
                f"{self.assertion_id} dependency-blocked testable assertion requires "
                "execution_dependency_gap_ids",
            )
        if not dependency_gap_ids_allowed and self.execution_dependency_gap_ids:
            _fail(
                "execution-dependency-gap-forbidden",
                f"{self.assertion_id} may declare execution_dependency_gap_ids only "
                "when testable and dependency-blocked",
            )
        if self.semantic_disposition == "testable":
            if self.primary_gap_id is not None:
                _fail(
                    "testable-primary-gap-claim",
                    f"{self.assertion_id} testable assertion cannot claim a primary gap",
                )
            if not self.action_clauses:
                _fail(
                    "testable-action-missing",
                    f"{self.assertion_id} testable assertion requires action_clauses",
                )
            if not self.oracle_clauses:
                _fail(
                    "testable-oracle-missing",
                    f"{self.assertion_id} testable assertion requires oracle_clauses",
                )
            if not self.obligation_ids:
                _fail(
                    "testable-obligation-missing",
                    f"{self.assertion_id} testable assertion requires obligation_ids",
                )
        elif self.semantic_disposition == "ambiguous":
            if self.obligation_ids:
                _fail(
                    "ambiguous-obligation-claim",
                    f"{self.assertion_id} ambiguous assertion cannot claim obligations",
                )
            if self.primary_gap_id is None:
                _fail(
                    "ambiguous-primary-gap-missing",
                    f"{self.assertion_id} ambiguous assertion requires primary_gap_id",
                )
        else:
            if self.primary_gap_id is not None:
                _fail(
                    "not-applicable-primary-gap-claim",
                    f"{self.assertion_id} not-applicable assertion cannot claim a primary gap",
                )
            if self.obligation_ids:
                _fail(
                    "not-applicable-obligation-claim",
                    f"{self.assertion_id} not-applicable assertion cannot claim obligations",
                )
        if not isinstance(self.disposition_rationale, str):
            _fail(
                "invalid-text",
                f"{self.assertion_id}.disposition_rationale must be text",
            )
        if self.semantic_disposition == "ambiguous":
            if not self.disposition_rationale.strip():
                _fail(
                    "ambiguous-rationale-missing",
                    f"{self.assertion_id} ambiguous assertion requires a substantive "
                    "disposition_rationale",
                )
            _review_explanation(
                self.disposition_rationale,
                f"{self.assertion_id}.disposition_rationale",
            )
        if self.semantic_disposition == "not-applicable" and not self.disposition_rationale.strip():
            _fail(
                "not-applicable-rationale-missing",
                f"{self.assertion_id} not-applicable assertion requires a "
                "source-backed disposition_rationale",
            )
        if len(self.exact_source_fragments) != len(
            set(self.exact_source_fragments)
        ):
            _fail(
                "duplicate-exact-source-fragment",
                f"{self.assertion_id}.exact_source_fragments contains duplicates",
            )
        requirement_binding_codes: set[str] = set()
        requirement_binding_keys: set[tuple[str, str, str]] = set()
        for binding in self.requirement_code_bindings:
            if not isinstance(binding, RequirementCodeBinding):
                _fail(
                    "invalid-requirement-code-binding",
                    f"{self.assertion_id}.requirement_code_bindings contains an invalid item",
                )
            binding.validate_shape()
            key = (
                binding.requirement_code,
                binding.source_row_id,
                binding.provenance_role,
            )
            if key in requirement_binding_keys:
                _fail(
                    "duplicate-requirement-code-binding",
                    f"{self.assertion_id}.requirement_code_bindings contains duplicates",
                )
            if binding.requirement_code in requirement_binding_codes:
                _fail(
                    "duplicate-bound-requirement-code",
                    f"{self.assertion_id} must bind each requirement code exactly once",
                )
            requirement_binding_keys.add(key)
            requirement_binding_codes.add(binding.requirement_code)
        if set(self.requirement_codes) != requirement_binding_codes:
            _fail(
                "requirement-code-binding-set-mismatch",
                f"{self.assertion_id}.requirement_codes must exactly equal its typed "
                "requirement_code_bindings",
            )

        expected_clause_positions = {
            (clause_kind, index)
            for clause_kind, clauses in (
                ("condition", self.condition_clauses),
                ("action", self.action_clauses),
                ("oracle", self.oracle_clauses),
            )
            for index in range(len(clauses))
        }
        actual_clause_positions: set[tuple[str, int]] = set()
        clause_binding_keys: set[tuple[str, int, str, str, str]] = set()
        for binding in self.clause_evidence_bindings:
            if not isinstance(binding, ClauseEvidenceBinding):
                _fail(
                    "invalid-clause-evidence-binding",
                    f"{self.assertion_id}.clause_evidence_bindings contains an invalid item",
                )
            binding.validate_shape()
            position = (binding.clause_kind, binding.clause_index)
            actual_clause_positions.add(position)
            key = (
                binding.clause_kind,
                binding.clause_index,
                binding.source_row_id,
                binding.evidence_role,
                normalize_exact_source_text(binding.exact_source_fragment),
            )
            if key in clause_binding_keys:
                _fail(
                    "duplicate-clause-evidence-binding",
                    f"{self.assertion_id}.clause_evidence_bindings contains duplicates",
                )
            clause_binding_keys.add(key)
        if actual_clause_positions != expected_clause_positions:
            _fail(
                "clause-evidence-binding-set-mismatch",
                f"{self.assertion_id}.clause_evidence_bindings must cover every "
                "condition/action/oracle clause index and no others",
            )
        supporting_keys: set[tuple[str, str, str]] = set()
        for binding in self.supporting_source_bindings:
            if not isinstance(binding, SupportingSourceBinding):
                _fail(
                    "invalid-supporting-source-binding",
                    f"{self.assertion_id}.supporting_source_bindings contains an invalid item",
                )
            binding.validate_shape()
            key = (
                binding.source_row_id,
                binding.evidence_role,
                normalize_exact_source_text(binding.exact_source_fragment),
            )
            if key in supporting_keys:
                _fail(
                    "duplicate-supporting-source-binding",
                    f"{self.assertion_id}.supporting_source_bindings contains duplicates",
                )
            supporting_keys.add(key)
        clarification_keys: set[tuple[str, str, int]] = set()
        has_canonical_clarification_binding = False
        has_executable_clarification_binding = False
        for binding in self.clarification_clause_bindings:
            if not isinstance(binding, ClarificationClauseBinding):
                _fail(
                    "invalid-clarification-clause-binding",
                    f"{self.assertion_id}.clarification_clause_bindings contains "
                    "an invalid item",
                )
            binding.validate_shape()
            position = (binding.clause_kind, binding.clause_index)
            if binding.clause_kind == "canonical":
                has_canonical_clarification_binding = True
            elif position not in expected_clause_positions:
                _fail(
                    "clarification-clause-index-out-of-range",
                    f"{self.assertion_id} clarification binding references absent "
                    f"{binding.clause_kind}_clauses[{binding.clause_index}]",
                )
            else:
                has_executable_clarification_binding = True
            key = (
                binding.clarification_id,
                binding.clause_kind,
                binding.clause_index,
            )
            if key in clarification_keys:
                _fail(
                    "duplicate-clarification-clause-binding",
                    f"{self.assertion_id}.clarification_clause_bindings contains duplicates",
                )
            clarification_keys.add(key)
        if has_executable_clarification_binding and self.semantic_disposition != "testable":
            _fail(
                "clarification-binding-non-testable-assertion",
                f"{self.assertion_id} may use approved clarification evidence only "
                "for a testable assertion",
            )
        if has_canonical_clarification_binding:
            if self.semantic_disposition != "not-applicable":
                _fail(
                    "clarification-canonical-disposition-invalid",
                    f"{self.assertion_id} canonical clarification binding requires "
                    "semantic_disposition=not-applicable",
                )
            if self.execution_readiness != "not-applicable":
                _fail(
                    "clarification-canonical-readiness-invalid",
                    f"{self.assertion_id} canonical clarification binding requires "
                    "execution_readiness=not-applicable",
                )
            if (
                self.condition_clauses
                or self.action_clauses
                or self.oracle_clauses
                or self.obligation_ids
            ):
                _fail(
                    "clarification-canonical-executable-content-forbidden",
                    f"{self.assertion_id} canonical clarification binding requires "
                    "empty condition/action/oracle clauses and obligation_ids",
                )
            _review_explanation(
                self.disposition_rationale,
                f"{self.assertion_id}.disposition_rationale",
            )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "assertion_id": self.assertion_id,
            "source_path": self.source_path,
            "source_context_class": self.source_context_class,
            "locator": self.locator,
            "exact_source_text": self.exact_source_text,
            "canonical_statement": self.canonical_statement,
            "polarity": self.polarity,
            "semantic_disposition": self.semantic_disposition,
            "execution_readiness": self.execution_readiness,
            "execution_readiness_rationale": self.execution_readiness_rationale,
            "risk": self.risk,
            "condition_clauses": list(self.condition_clauses),
            "action_clauses": list(self.action_clauses),
            "oracle_clauses": list(self.oracle_clauses),
            "requirement_codes": list(self.requirement_codes),
            "requirement_code_bindings": [
                item.to_dict() for item in self.requirement_code_bindings
            ],
            "clause_evidence_bindings": [
                item.to_dict() for item in self.clause_evidence_bindings
            ],
            "source_row_id": self.source_row_id,
            "atom_id": self.atom_id,
            "obligation_ids": list(self.obligation_ids),
            "execution_dependency_gap_ids": list(
                self.execution_dependency_gap_ids
            ),
            "primary_gap_id": self.primary_gap_id,
            "supporting_source_bindings": [
                item.to_dict() for item in self.supporting_source_bindings
            ],
            "clarification_clause_bindings": [
                item.to_dict() for item in self.clarification_clause_bindings
            ],
        }
        if self.disposition_rationale:
            payload["disposition_rationale"] = self.disposition_rationale
        if self.exact_source_fragments:
            payload["exact_source_fragments"] = list(self.exact_source_fragments)
        return payload


@dataclass(frozen=True)
class SourceAssertionManifest:
    version: int
    scope_slug: str
    source_row_extraction_spec_digest: str
    source_row_baseline_digest: str
    source_row_candidate_count: int
    coverage_gaps_artifact: RegisteredArtifact
    sources: tuple[RegisteredSource, ...]
    assertions: tuple[SourceAssertion, ...]
    clarifications: tuple[ApprovedClarification, ...] = ()
    source_rows: tuple[SourceRow, ...] = ()
    evidence_sources: tuple[RegisteredEvidenceSource, ...] = ()
    mockups: tuple[RegisteredMockup, ...] = ()
    _validated_source_texts: Mapping[str, str] = field(
        default_factory=dict,
        repr=False,
        compare=False,
        hash=False,
    )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceAssertionManifest":
        if isinstance(payload, Mapping) and payload.get("version") in LEGACY_MANIFEST_VERSIONS:
            _fail(
                "legacy-manifest-requires-rematerialization",
                "legacy source assertion manifest cannot attest approved clarification "
                "provenance; rematerialize v4 and issue a fresh review receipt",
            )
        _exact_fields(
            payload,
            required={
                "version",
                "scope_slug",
                "source_row_extraction_spec_digest",
                "source_row_baseline_digest",
                "source_row_candidate_count",
                "coverage_gaps_artifact",
                "sources",
                "source_rows",
                "assertions",
                "clarifications",
            },
            optional={"evidence_sources", "mockups"},
            label="source assertion manifest",
        )
        if type(payload["version"]) is not int or payload["version"] != MANIFEST_VERSION:
            _fail(
                "unsupported-version",
                f"manifest.version must equal {MANIFEST_VERSION}",
            )
        if not isinstance(payload["sources"], list) or not payload["sources"]:
            _fail("invalid-sources", "manifest.sources must be a non-empty JSON array")
        if not isinstance(payload["assertions"], list) or not payload["assertions"]:
            _fail("invalid-assertions", "manifest.assertions must be a non-empty JSON array")
        if not isinstance(payload["source_rows"], list) or not payload["source_rows"]:
            _fail("invalid-source-rows", "manifest.source_rows must be a non-empty JSON array")
        if not isinstance(payload["clarifications"], list):
            _fail(
                "invalid-clarifications",
                "manifest.clarifications must be a JSON array",
            )
        if type(payload["source_row_candidate_count"]) is not int:
            _fail(
                "invalid-source-row-candidate-count",
                "manifest.source_row_candidate_count must be an integer",
            )
        mockups = payload.get("mockups", [])
        if not isinstance(mockups, list):
            _fail("invalid-mockups", "manifest.mockups must be a JSON array")
        evidence_sources = payload.get("evidence_sources", [])
        if not isinstance(evidence_sources, list):
            _fail(
                "invalid-evidence-sources",
                "manifest.evidence_sources must be a JSON array",
            )
        return cls(
            version=payload["version"],
            scope_slug=_nonempty_text(payload["scope_slug"], "manifest.scope_slug"),
            source_row_extraction_spec_digest=_sha256(
                payload["source_row_extraction_spec_digest"],
                "manifest.source_row_extraction_spec_digest",
            ),
            source_row_baseline_digest=_sha256(
                payload["source_row_baseline_digest"],
                "manifest.source_row_baseline_digest",
            ),
            source_row_candidate_count=payload["source_row_candidate_count"],
            coverage_gaps_artifact=RegisteredArtifact.from_dict(
                payload["coverage_gaps_artifact"]
            ),
            sources=tuple(RegisteredSource.from_dict(item) for item in payload["sources"]),
            assertions=tuple(SourceAssertion.from_dict(item) for item in payload["assertions"]),
            clarifications=tuple(
                ApprovedClarification.from_dict(item)
                for item in payload["clarifications"]
            ),
            source_rows=tuple(SourceRow.from_dict(item) for item in payload["source_rows"]),
            evidence_sources=tuple(
                RegisteredEvidenceSource.from_dict(item) for item in evidence_sources
            ),
            mockups=tuple(RegisteredMockup.from_dict(item) for item in mockups),
        )

    @classmethod
    def from_compact_reviewer_basis(
        cls, payload: Mapping[str, Any]
    ) -> "SourceAssertionManifest":
        if (
            isinstance(payload, Mapping)
            and payload.get("contract") in LEGACY_COMPACT_REVIEWER_BASIS_CONTRACTS
        ):
            _fail(
                "legacy-embedded-source-contract-requires-rematerialization",
                "legacy embedded source assertion contract cannot attest current "
                "clarification and review provenance",
            )
        _exact_fields(
            payload,
            required={
                "contract",
                "manifest_digest",
                "scope_slug",
                "source_row_extraction_spec_digest",
                "source_row_baseline_digest",
                "source_row_candidate_count",
                "coverage_gaps_artifact",
                "sources",
                "source_rows",
                "assertions",
                "clarifications",
                "mockups",
            },
            optional={"evidence_sources"},
            label="embedded source assertion basis",
        )
        if payload["contract"] != COMPACT_REVIEWER_BASIS_CONTRACT:
            _fail(
                "unsupported-embedded-contract",
                "embedded source assertion basis has an unsupported contract",
            )
        declared_digest = _sha256(
            payload["manifest_digest"], "embedded source assertion basis.manifest_digest"
        )
        manifest = cls.from_dict(
            {
                "version": MANIFEST_VERSION,
                "scope_slug": payload["scope_slug"],
                "source_row_extraction_spec_digest": payload[
                    "source_row_extraction_spec_digest"
                ],
                "source_row_baseline_digest": payload[
                    "source_row_baseline_digest"
                ],
                "source_row_candidate_count": payload[
                    "source_row_candidate_count"
                ],
                "coverage_gaps_artifact": payload["coverage_gaps_artifact"],
                "sources": payload["sources"],
                "source_rows": payload["source_rows"],
                "assertions": payload["assertions"],
                "clarifications": payload["clarifications"],
                "evidence_sources": payload.get("evidence_sources", []),
                "mockups": payload["mockups"],
            }
        )
        if declared_digest != manifest.digest:
            _fail(
                "embedded-manifest-digest-mismatch",
                "embedded source assertion basis digest does not match its manifest",
            )
        return manifest

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version": self.version,
            "scope_slug": self.scope_slug,
            "source_row_extraction_spec_digest": (
                self.source_row_extraction_spec_digest
            ),
            "source_row_baseline_digest": self.source_row_baseline_digest,
            "source_row_candidate_count": self.source_row_candidate_count,
            "coverage_gaps_artifact": self.coverage_gaps_artifact.to_dict(),
            "sources": [item.to_dict() for item in self.sources],
            "source_rows": [item.to_dict() for item in self.source_rows],
            "assertions": [item.to_dict() for item in self.assertions],
            "clarifications": [item.to_dict() for item in self.clarifications],
        }
        if self.evidence_sources:
            payload["evidence_sources"] = [
                item.to_dict() for item in self.evidence_sources
            ]
        if self.mockups:
            payload["mockups"] = [item.to_dict() for item in self.mockups]
        return payload

    @property
    def digest(self) -> str:
        return build_source_assertion_digest(self)

    def validate(
        self,
        repo_root: Path,
        *,
        expected_source_row_ids: Iterable[str] | None = None,
        expected_source_rows: Iterable[SourceRow] | None = None,
        approved_polarities: Mapping[str, str] | None = None,
    ) -> None:
        if self.version in LEGACY_MANIFEST_VERSIONS:
            _fail(
                "legacy-manifest-requires-rematerialization",
                "legacy source assertion manifest cannot attest approved clarification "
                "provenance; rematerialize v4 and issue a fresh review receipt",
            )
        if self.version != MANIFEST_VERSION:
            _fail("unsupported-version", f"manifest.version must equal {MANIFEST_VERSION}")
        _nonempty_text(self.scope_slug, "manifest.scope_slug")
        _sha256(
            self.source_row_extraction_spec_digest,
            "manifest.source_row_extraction_spec_digest",
        )
        _sha256(
            self.source_row_baseline_digest,
            "manifest.source_row_baseline_digest",
        )
        if (
            type(self.source_row_candidate_count) is not int
            or self.source_row_candidate_count <= 0
        ):
            _fail(
                "invalid-source-row-candidate-count",
                "manifest.source_row_candidate_count must be a positive integer",
            )
        if not self.sources:
            _fail("invalid-sources", "manifest.sources must not be empty")
        if not self.assertions:
            _fail("invalid-assertions", "manifest.assertions must not be empty")
        for assertion in self.assertions:
            assertion.validate_shape()
        if not self.source_rows:
            _fail("invalid-source-rows", "manifest.source_rows must not be empty")

        assertions_by_id: dict[str, SourceAssertion] = {}
        for assertion in self.assertions:
            if assertion.assertion_id in assertions_by_id:
                _fail(
                    "duplicate-assertion-id",
                    f"duplicate assertion_id {assertion.assertion_id}",
                )
            assertions_by_id[assertion.assertion_id] = assertion

        _relative_path(
            self.coverage_gaps_artifact.path,
            "manifest.coverage_gaps_artifact.path",
        )
        _sha256(
            self.coverage_gaps_artifact.sha256,
            "manifest.coverage_gaps_artifact.sha256",
        )
        coverage_gaps_path = _resolve_registered_path(
            repo_root,
            self.coverage_gaps_artifact.path,
            "manifest.coverage_gaps_artifact.path",
        )
        actual_coverage_gaps_sha256 = sha256_file(coverage_gaps_path)
        if actual_coverage_gaps_sha256 != self.coverage_gaps_artifact.sha256:
            _fail(
                "stale-coverage-gaps-artifact-sha256",
                "registered SHA-256 for coverage gaps is stale: "
                f"expected={self.coverage_gaps_artifact.sha256}, "
                f"actual={actual_coverage_gaps_sha256}",
            )
        coverage_gap_bindings = _coverage_gap_execution_bindings(
            coverage_gaps_path
        )
        primary_assertion_ids_by_gap: dict[str, set[str]] = {}
        for assertion in self.assertions:
            if assertion.primary_gap_id is None:
                continue
            primary_assertion_ids_by_gap.setdefault(
                assertion.primary_gap_id, set()
            ).add(assertion.assertion_id)
        for gap_id, assertion_ids in primary_assertion_ids_by_gap.items():
            gap = coverage_gap_bindings.get(gap_id)
            if gap is None:
                _fail(
                    "primary-gap-unknown",
                    f"primary gap {gap_id} for assertions {sorted(assertion_ids)} is "
                    "absent from the hash-bound coverage gaps artifact",
                )
            if gap.status != "open":
                _fail(
                    "primary-gap-not-open",
                    f"primary gap {gap_id} for assertions {sorted(assertion_ids)} "
                    "must declare status=open",
                )
            affected_assertion_ids = set(gap.affected_assertion_ids)
            missing_primary_assertions = sorted(
                assertion_ids - affected_assertion_ids
            )
            if missing_primary_assertions:
                _fail(
                    "primary-gap-affected-chain-mismatch",
                    f"primary gap {gap_id} must include every primary assertion in "
                    "affected_assertion_id: missing="
                    + ", ".join(missing_primary_assertions),
                )

        for gap_id, gap in coverage_gap_bindings.items():
            affected_assertion_ids = set(gap.affected_assertion_ids)
            unknown_affected_assertions = sorted(
                affected_assertion_ids - set(assertions_by_id)
            )
            if unknown_affected_assertions:
                _fail(
                    "coverage-gap-affected-assertion-unknown",
                    f"coverage gap {gap_id} names affected assertions absent from "
                    "the manifest: " + ", ".join(unknown_affected_assertions),
                )
            if affected_assertion_ids or gap.affected_atom_ids:
                expected_affected_atoms = {
                    assertions_by_id[assertion_id].atom_id
                    for assertion_id in affected_assertion_ids
                }
                actual_affected_atoms = set(gap.affected_atom_ids)
                if actual_affected_atoms != expected_affected_atoms:
                    _fail(
                        "coverage-gap-affected-chain-mismatch",
                        f"coverage gap {gap_id} affected_atom_id must exactly match "
                        "the atoms owned by affected_assertion_id: "
                        f"missing={sorted(expected_affected_atoms - actual_affected_atoms) or 'none'}, "
                        f"unexpected={sorted(actual_affected_atoms - expected_affected_atoms) or 'none'}",
                    )
        execution_chains_by_gap: dict[
            str, dict[str, set[str]]
        ] = {}
        for assertion in self.assertions:
            for gap_id in assertion.execution_dependency_gap_ids:
                chain = execution_chains_by_gap.setdefault(
                    gap_id,
                    {"assertions": set(), "atoms": set(), "obligations": set()},
                )
                chain["assertions"].add(assertion.assertion_id)
                chain["atoms"].add(assertion.atom_id)
                chain["obligations"].update(assertion.obligation_ids)
        for gap_id, expected_chain in execution_chains_by_gap.items():
            gap = coverage_gap_bindings.get(gap_id)
            if gap is None:
                _fail(
                    "execution-dependency-gap-unknown",
                    f"execution dependency {gap_id} is absent from the hash-bound "
                    "coverage gaps artifact",
                )
            if gap.status != "open":
                _fail(
                    "execution-dependency-gap-not-open",
                    f"execution dependency {gap_id} must declare status=open",
                )
            if gap.impact != "blocking":
                _fail(
                    "execution-dependency-gap-not-blocking",
                    f"execution dependency {gap_id} must declare Impact=blocking",
                )
            if gap.blocks_ready_for_review != "yes":
                _fail(
                    "execution-dependency-gap-does-not-block-review",
                    f"execution dependency {gap_id} must declare "
                    "blocks_ready_for_review=yes",
                )
            actual_chain = {
                "assertions": set(gap.assertion_ids),
                "atoms": set(gap.atom_ids),
                "obligations": set(gap.obligation_ids),
            }
            if actual_chain != expected_chain:
                _fail(
                    "execution-dependency-gap-chain-mismatch",
                    f"{gap_id} must name the exact ASSERT/ATOM/OBL chain: "
                    f"expected={{{', '.join(f'{key}={sorted(value)}' for key, value in expected_chain.items())}}}, "
                    f"actual={{{', '.join(f'{key}={sorted(value)}' for key, value in actual_chain.items())}}}",
                )

        source_paths = [item.path for item in self.sources]
        if len(source_paths) != len(set(source_paths)):
            _fail("duplicate-source", "manifest.sources contains duplicate paths")
        source_files: dict[str, Path] = {}
        source_texts: dict[str, str] = {}
        normalized_source_texts: dict[str, str] = {}
        for source in self.sources:
            _relative_path(source.path, "source.path")
            _sha256(source.sha256, "source.sha256")
            actual_path = _resolve_registered_path(repo_root, source.path, "source.path")
            actual_sha = sha256_file(actual_path)
            if actual_sha != source.sha256:
                _fail(
                    "stale-source-sha256",
                    f"registered SHA-256 for {source.path} is stale: "
                    f"expected={source.sha256}, actual={actual_sha}",
                )
            try:
                source_texts[source.path] = actual_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                _fail("source-not-utf8", f"registered source is not valid UTF-8: {source.path}: {exc}")
            normalized_source_texts[source.path] = normalize_exact_source_text(
                source_texts[source.path]
            )
            source_files[source.path] = actual_path
        object.__setattr__(
            self,
            "_validated_source_texts",
            dict(normalized_source_texts),
        )

        source_rows_by_id: dict[str, SourceRow] = {}
        source_row_locators: set[tuple[str, str]] = set()
        source_candidate_ids: set[str] = set()
        candidate_rows_by_path: dict[str, list[SourceRow]] = {}
        used_sources: set[str] = set()
        for source_row in self.source_rows:
            if not isinstance(source_row, SourceRow):
                _fail(
                    "invalid-source-row",
                    "manifest.source_rows contains an invalid item",
                )
            source_row.validate_shape()
            if source_row.candidate_id is not None:
                if source_row.candidate_id in source_candidate_ids:
                    _fail(
                        "duplicate-source-candidate-mapping",
                        "manifest.source_rows maps one source candidate more than once: "
                        f"{source_row.candidate_id}",
                    )
                source_candidate_ids.add(source_row.candidate_id)
            if source_row.source_row_id in source_rows_by_id:
                _fail(
                    "duplicate-source-row",
                    f"manifest.source_rows contains duplicate {source_row.source_row_id}",
                )
            locator_key = (source_row.source_path, source_row.source_locator)
            if locator_key in source_row_locators:
                _fail(
                    "duplicate-source-row-locator",
                    "manifest.source_rows contains duplicate source_path/source_locator: "
                    f"{source_row.source_path}#{source_row.source_locator}",
                )
            source_row_locators.add(locator_key)
            if source_row.source_path not in source_files:
                _fail(
                    "unregistered-source-row-source",
                    f"{source_row.source_row_id} references unregistered source "
                    f"{source_row.source_path}",
                )
            normalized_bounded_text = normalize_exact_source_text(
                source_row.bounded_source_text
            )
            if source_row.candidate_id is not None:
                candidate_rows_by_path.setdefault(source_row.source_path, []).append(
                    source_row
                )
            elif not contains_token_bounded_source_fragment(
                normalized_source_texts[source_row.source_path],
                normalized_bounded_text,
            ):
                _fail(
                    "source-row-bounded-text-mismatch",
                    f"{source_row.source_row_id}.bounded_source_text is absent from "
                    f"{source_row.source_path} after whitespace-only normalization",
                )
            source_rows_by_id[source_row.source_row_id] = source_row
            used_sources.add(source_row.source_path)

        for source_path, candidate_rows in candidate_rows_by_path.items():
            try:
                resolved_candidates = resolve_xhtml_candidates_at_locators(
                    xhtml_path=source_files[source_path],
                    canonical_xpaths=tuple(
                        item.source_locator for item in candidate_rows
                    ),
                )
            except SourceRowBaselineValidationError as exc:
                _fail(
                    "source-row-candidate-locator-invalid",
                    f"candidate-bound source rows for {source_path} do not resolve "
                    f"under baseline visible-text ownership semantics: {exc}",
                )
            for source_row in candidate_rows:
                resolved = resolved_candidates[source_row.source_locator]
                expected_text = normalize_exact_source_text(
                    source_row.bounded_source_text
                )
                if resolved.bounded_source_text != expected_text:
                    _fail(
                        "source-row-candidate-text-mismatch",
                        f"{source_row.source_row_id}.bounded_source_text must exactly "
                        f"equal visible text at {source_row.source_locator}: "
                        f"expected={resolved.bounded_source_text!r}, "
                        f"declared={expected_text!r}",
                    )

        if len(source_candidate_ids) != self.source_row_candidate_count:
            _fail(
                "source-row-candidate-count-mismatch",
                "manifest.source_row_candidate_count must equal the exact number of "
                "candidate-bound source rows",
            )

        assertion_ids: set[str] = set()
        atom_ids: set[str] = set()
        obligation_ids: set[str] = set()
        assertion_row_ids: set[str] = set()
        assertions_by_row: dict[str, list[SourceAssertion]] = {}
        bound_requirement_codes_by_row: dict[str, set[str]] = {}
        pdf_page_texts: dict[tuple[str, int], str] = {}
        for assertion in self.assertions:
            if assertion.assertion_id in assertion_ids:
                _fail("duplicate-assertion-id", f"duplicate assertion_id {assertion.assertion_id}")
            assertion_ids.add(assertion.assertion_id)
            if assertion.atom_id in atom_ids:
                _fail("duplicate-atom-mapping", f"atom {assertion.atom_id} maps from multiple assertions")
            atom_ids.add(assertion.atom_id)
            duplicates = sorted(set(assertion.obligation_ids) & obligation_ids)
            if duplicates:
                _fail(
                    "duplicate-obligation-mapping",
                    "obligations map from multiple assertions: " + ", ".join(duplicates),
                )
            obligation_ids.update(assertion.obligation_ids)
            if assertion.source_path not in source_files:
                _fail(
                    "unregistered-assertion-source",
                    f"{assertion.assertion_id} references unregistered source {assertion.source_path}",
                )
            source_row = source_rows_by_id.get(assertion.source_row_id)
            if source_row is None:
                _fail(
                    "assertion-source-row-missing",
                    f"{assertion.assertion_id} references absent source row "
                    f"{assertion.source_row_id}",
                )
            assertion_row_ids.add(assertion.source_row_id)
            assertions_by_row.setdefault(assertion.source_row_id, []).append(assertion)
            if assertion.source_path != source_row.source_path:
                _fail(
                    "assertion-source-path-mismatch",
                    f"{assertion.assertion_id}.source_path must equal its source row path",
                )
            if assertion.locator != source_row.source_locator:
                _fail(
                    "assertion-source-locator-mismatch",
                    f"{assertion.assertion_id}.locator must equal its source row locator",
                )
            if assertion.source_context_class != source_row.source_context_class:
                _fail(
                    "source-row-context-class-mismatch",
                    f"{assertion.assertion_id}.source_context_class must equal the "
                    f"source row class {source_row.source_context_class}",
                )
            bounded_row_text = normalize_exact_source_text(
                source_row.bounded_source_text
            )
            for field_name, source_fragment in (
                ("exact_source_text", assertion.exact_source_text),
                *(
                    (f"exact_source_fragments[{index}]", value)
                    for index, value in enumerate(
                        assertion.exact_source_fragments
                    )
                ),
            ):
                expected_text = normalize_exact_source_text(source_fragment)
                if not contains_token_bounded_source_fragment(
                    bounded_row_text,
                    expected_text,
                ):
                    _fail(
                        "assertion-source-fragment-outside-primary-row",
                        f"{assertion.assertion_id}.{field_name} is absent from bounded "
                        f"source row {assertion.source_row_id}",
                    )
            for binding in assertion.supporting_source_bindings:
                supporting_row = source_rows_by_id.get(binding.source_row_id)
                if supporting_row is None:
                    _fail(
                        "supporting-source-row-missing",
                        f"{assertion.assertion_id} supporting binding references absent "
                        f"source row {binding.source_row_id}",
                    )
                if binding.source_row_id == assertion.source_row_id:
                    _fail(
                        "supporting-source-binding-primary-row",
                        f"{assertion.assertion_id} must keep primary-row fragments in "
                        "exact_source_text/exact_source_fragments",
                    )
                if not contains_token_bounded_source_fragment(
                    normalize_exact_source_text(supporting_row.bounded_source_text),
                    normalize_exact_source_text(binding.exact_source_fragment),
                ):
                    _fail(
                        "supporting-source-fragment-outside-declared-row",
                        f"{assertion.assertion_id} supporting fragment is absent from "
                        f"declared source row {binding.source_row_id}",
                    )
            evidence_sources_by_path = {
                evidence_source.path: evidence_source
                for evidence_source in self.evidence_sources
            }
            for code_binding in assertion.requirement_code_bindings:
                code_row = source_rows_by_id.get(code_binding.source_row_id)
                if code_row is None:
                    _fail(
                        "requirement-code-source-row-missing",
                        f"{assertion.assertion_id} requirement code binding references "
                        f"absent source row {code_binding.source_row_id}",
                    )
                if code_binding.requirement_code not in code_row.requirement_codes:
                    _fail(
                        "requirement-code-absent-from-bound-row",
                        f"{assertion.assertion_id} binds {code_binding.requirement_code} "
                        f"to {code_binding.source_row_id}, whose registry does not contain it",
                    )
                bound_requirement_codes_by_row.setdefault(
                    code_binding.source_row_id, set()
                ).add(code_binding.requirement_code)
                if code_binding.provenance_role == "xhtml-row":
                    code_fragment = normalize_exact_source_text(
                        code_binding.exact_source_fragment or ""
                    )
                    if not contains_token_bounded_source_fragment(
                        normalize_exact_source_text(code_row.bounded_source_text),
                        code_fragment,
                    ):
                        _fail(
                            "xhtml-requirement-code-fragment-outside-row",
                            f"{assertion.assertion_id} declares XHTML provenance for "
                            f"{code_binding.requirement_code}, but its exact fragment is "
                            f"absent from {code_binding.source_row_id}",
                        )
                    if not contains_token_bounded_source_fragment(
                        code_fragment,
                        normalize_exact_source_text(code_binding.requirement_code),
                    ):
                        _fail(
                            "xhtml-requirement-code-not-literal-in-fragment",
                            f"{assertion.assertion_id} exact requirement-code fragment "
                            f"does not contain {code_binding.requirement_code}",
                        )
                else:
                    bound_pdf = evidence_sources_by_path.get(
                        code_binding.evidence_source_path or ""
                    )
                    if (
                        bound_pdf is None
                        or bound_pdf.role != "structural-visual-parity"
                    ):
                        _fail(
                            "pdf-requirement-code-evidence-source-mismatch",
                            f"{assertion.assertion_id} PDF-only provenance for "
                            f"{code_binding.requirement_code} must bind one exact "
                            "registered structural-visual-parity source",
                        )
                    assert code_binding.evidence_source_path is not None
                    assert code_binding.evidence_locator is not None
                    page_number = _pdf_page_number(
                        code_binding.evidence_locator,
                        "requirement code binding.evidence_locator",
                    )
                    page_key = (code_binding.evidence_source_path, page_number)
                    if page_key not in pdf_page_texts:
                        pdf_page_texts[page_key] = _extract_pdf_page_text(
                            _resolve_registered_path(
                                repo_root,
                                code_binding.evidence_source_path,
                                "requirement code binding.evidence_source_path",
                            ),
                            page_number,
                            "requirement code binding.evidence_locator",
                        )
                    if not contains_token_bounded_source_fragment(
                        pdf_page_texts[page_key],
                        normalize_exact_source_text(
                            code_binding.requirement_code
                        ),
                    ):
                        _fail(
                            "pdf-requirement-code-not-on-declared-page",
                            f"{assertion.assertion_id} binds "
                            f"{code_binding.requirement_code} to "
                            f"{code_binding.evidence_locator}, but the code is absent "
                            "from extracted text of that registered PDF page",
                        )
            clauses_by_kind = {
                "condition": assertion.condition_clauses,
                "action": assertion.action_clauses,
                "oracle": assertion.oracle_clauses,
            }
            for clause_binding in assertion.clause_evidence_bindings:
                clauses = clauses_by_kind[clause_binding.clause_kind]
                if clause_binding.clause_index >= len(clauses):
                    _fail(
                        "clause-evidence-index-out-of-range",
                        f"{assertion.assertion_id} clause evidence index is outside "
                        f"{clause_binding.clause_kind}_clauses",
                    )
                clause_row = source_rows_by_id.get(clause_binding.source_row_id)
                if clause_row is None:
                    _fail(
                        "clause-evidence-source-row-missing",
                        f"{assertion.assertion_id} clause evidence references absent "
                        f"source row {clause_binding.source_row_id}",
                    )
                normalized_clause_fragment = normalize_exact_source_text(
                    clause_binding.exact_source_fragment
                )
                if not contains_token_bounded_source_fragment(
                    normalize_exact_source_text(clause_row.bounded_source_text),
                    normalized_clause_fragment,
                ):
                    _fail(
                        "clause-evidence-fragment-outside-declared-row",
                        f"{assertion.assertion_id} {clause_binding.clause_kind} clause "
                        f"evidence is absent from {clause_binding.source_row_id}",
                    )

        for source_row_id, source_row in source_rows_by_id.items():
            row_assertions = assertions_by_row.get(source_row_id, ())
            declared_requirement_codes = set(source_row.requirement_codes)
            bound_requirement_codes = bound_requirement_codes_by_row.get(
                source_row_id, set()
            )
            if declared_requirement_codes != bound_requirement_codes:
                _fail(
                    "source-row-requirement-code-unbound",
                    f"source row {source_row_id}.requirement_codes must exactly equal "
                    "the union of typed requirement_code_bindings that reference the "
                    "row: "
                    f"unbound={sorted(declared_requirement_codes - bound_requirement_codes) or 'none'}, "
                    f"undeclared={sorted(bound_requirement_codes - declared_requirement_codes) or 'none'}",
                )
            if source_row.scope_disposition == "no" and any(
                assertion.semantic_disposition != "not-applicable"
                for assertion in row_assertions
            ):
                _fail(
                    "out-of-scope-row-executable-assertion",
                    f"source row {source_row_id} has scope_disposition=no but contains "
                    "an assertion that is not not-applicable",
                )
            if source_row.scope_disposition == "unclear" and any(
                assertion.execution_readiness == "ready"
                for assertion in row_assertions
            ):
                _fail(
                    "unclear-row-ready-assertion",
                    f"source row {source_row_id} has scope_disposition=unclear but "
                    "contains an execution_readiness=ready assertion",
                )

        missing_assertion_rows = sorted(set(source_rows_by_id) - assertion_row_ids)
        unexpected_assertion_rows = sorted(assertion_row_ids - set(source_rows_by_id))
        if missing_assertion_rows or unexpected_assertion_rows:
            _fail(
                "source-row-assertion-set-mismatch",
                "manifest source row/assertion row sets mismatch: "
                f"missing_assertions={missing_assertion_rows or 'none'}, "
                f"unexpected_assertions={unexpected_assertion_rows or 'none'}",
            )

        orphan_sources = sorted(set(source_paths) - used_sources)
        if orphan_sources:
            _fail(
                "orphan-registered-source",
                "registered sources have no assertion chain: " + ", ".join(orphan_sources),
            )

        evidence_paths: set[str] = set()
        evidence_sources_by_path: dict[str, RegisteredEvidenceSource] = {}
        evidence_files_by_path: dict[str, Path] = {}
        for evidence_source in self.evidence_sources:
            _relative_path(evidence_source.path, "evidence_source.path")
            _sha256(evidence_source.sha256, "evidence_source.sha256")
            if evidence_source.role not in EVIDENCE_SOURCE_ROLES:
                _fail(
                    "invalid-evidence-source-role",
                    "evidence_source.role must be one of "
                    f"{sorted(EVIDENCE_SOURCE_ROLES)}",
                )
            if evidence_source.path in evidence_paths:
                _fail(
                    "duplicate-evidence-source",
                    f"duplicate evidence source path {evidence_source.path}",
                )
            if evidence_source.path in source_files:
                _fail(
                    "evidence-source-overlaps-assertion-source",
                    f"evidence source also registered as assertion source: "
                    f"{evidence_source.path}",
                )
            evidence_paths.add(evidence_source.path)
            evidence_sources_by_path[evidence_source.path] = evidence_source
            actual_path = _resolve_registered_path(
                repo_root,
                evidence_source.path,
                "evidence_source.path",
            )
            actual_sha = sha256_file(actual_path)
            if actual_sha != evidence_source.sha256:
                _fail(
                    "stale-evidence-source-sha256",
                    f"registered SHA-256 for {evidence_source.path} is stale: "
                    f"expected={evidence_source.sha256}, actual={actual_sha}",
                )
            evidence_files_by_path[evidence_source.path] = actual_path

        clarification_by_id: dict[str, ApprovedClarification] = {}
        clarification_rows_by_path: dict[
            str, dict[str, Mapping[str, str]]
        ] = {}
        for clarification in self.clarifications:
            if not isinstance(clarification, ApprovedClarification):
                _fail(
                    "invalid-clarification-record",
                    "manifest.clarifications contains an invalid item",
                )
            clarification.validate_shape()
            if clarification.clarification_id in clarification_by_id:
                _fail(
                    "duplicate-clarification-record",
                    f"manifest.clarifications repeats {clarification.clarification_id}",
                )
            if clarification.scope_slug != self.scope_slug:
                _fail(
                    "clarification-scope-mismatch",
                    f"{clarification.clarification_id}.scope_slug must equal "
                    f"manifest.scope_slug={self.scope_slug}",
                )
            if clarification.binding_scope == "source-context":
                unknown_context_rows = sorted(
                    set(clarification.source_row_ids) - set(source_rows_by_id)
                )
                if unknown_context_rows:
                    _fail(
                        "clarification-source-context-row-missing",
                        f"{clarification.clarification_id} references absent source rows: "
                        + ", ".join(unknown_context_rows),
                    )
            gap_binding = coverage_gap_bindings.get(clarification.gap_id)
            if gap_binding is None:
                _fail(
                    "clarification-gap-unregistered",
                    f"{clarification.clarification_id} references {clarification.gap_id}, "
                    "which is absent from the hash-bound coverage gaps artifact",
                )
            if gap_binding.status != "resolved":
                _fail(
                    "clarification-gap-not-resolved",
                    f"{clarification.gap_id} must declare status=resolved before "
                    f"{clarification.clarification_id} can become ready evidence",
                )
            expected_resolution = (
                f"approved-clarification:{clarification.clarification_id}"
            )
            if gap_binding.resolution != expected_resolution:
                _fail(
                    "clarification-gap-resolution-mismatch",
                    f"{clarification.gap_id} must declare "
                    f"resolution={expected_resolution}",
                )
            if (
                gap_binding.assertion_ids
                or gap_binding.atom_ids
                or gap_binding.obligation_ids
            ):
                _fail(
                    "resolved-clarification-gap-has-execution-chain",
                    f"{clarification.gap_id} is resolved and must not remain in an "
                    "active execution-dependency chain",
                )
            evidence_source = evidence_sources_by_path.get(
                clarification.evidence_source_path
            )
            if evidence_source is None:
                _fail(
                    "clarification-evidence-unregistered",
                    f"{clarification.clarification_id} references unregistered evidence "
                    f"{clarification.evidence_source_path}",
                )
            if evidence_source.role != "approved-clarification":
                _fail(
                    "clarification-evidence-role-mismatch",
                    f"{clarification.clarification_id} evidence must use "
                    "role=approved-clarification",
                )
            if clarification.evidence_source_sha256 != evidence_source.sha256:
                _fail(
                    "clarification-evidence-digest-mismatch",
                    f"{clarification.clarification_id}.evidence_source_sha256 does not "
                    "match the registered evidence source",
                )
            if clarification.evidence_source_path not in clarification_rows_by_path:
                evidence_path = evidence_files_by_path[
                    clarification.evidence_source_path
                ]
                try:
                    evidence_text = evidence_path.read_text(encoding="utf-8")
                except UnicodeDecodeError as exc:
                    _fail(
                        "clarification-evidence-not-utf8",
                        "approved clarification evidence is not UTF-8: "
                        f"{clarification.evidence_source_path}: {exc}",
                    )
                clarification_rows_by_path[clarification.evidence_source_path] = (
                    _clarification_table_rows(
                        evidence_text,
                        source_path=clarification.evidence_source_path,
                    )
                )
            row = clarification_rows_by_path[
                clarification.evidence_source_path
            ].get(clarification.clarification_id)
            if row is None:
                _fail(
                    "clarification-structured-row-missing",
                    f"{clarification.clarification_id} is absent from its registered "
                    "clarification table",
                )
            row_codes = _clarification_requirement_codes(
                row["requirement_codes"],
                allow_empty=clarification.binding_scope == "source-context",
            )
            expected_row = {
                "clarification_id": clarification.clarification_id,
                "gap_id": clarification.gap_id,
                "scope_slug": clarification.scope_slug,
                "authority": clarification.authority,
                "user_response": clarification.exact_answer,
                "response_status": clarification.response_status,
                "response_type": clarification.response_type,
                "updated_at": clarification.answered_at,
            }
            mismatched_fields = sorted(
                field_name
                for field_name, expected_value in expected_row.items()
                if row[field_name] != expected_value
            )
            if row_codes != clarification.requirement_codes:
                mismatched_fields.append("requirement_codes")
            if mismatched_fields:
                _fail(
                    "clarification-structured-row-mismatch",
                    f"{clarification.clarification_id} manifest record differs from "
                    "the exact structured clarification row in fields: "
                    + ", ".join(sorted(mismatched_fields)),
                )
            clarification_by_id[clarification.clarification_id] = clarification

        used_clarification_ids: set[str] = set()
        bound_requirement_codes_by_clarification: dict[str, set[str]] = {}
        bound_source_row_ids_by_clarification: dict[str, set[str]] = {}
        source_context_binding_kinds: dict[tuple[str, str], set[str]] = {}
        for assertion in self.assertions:
            for binding in assertion.clarification_clause_bindings:
                clarification = clarification_by_id.get(binding.clarification_id)
                if clarification is None:
                    _fail(
                        "clarification-binding-unregistered",
                        f"{assertion.assertion_id} references absent clarification "
                        f"{binding.clarification_id}",
                    )
                if binding.exact_answer_sha256 != clarification.exact_answer_sha256:
                    _fail(
                        "clarification-binding-answer-digest-mismatch",
                        f"{assertion.assertion_id} does not bind the exact answer digest "
                        f"for {binding.clarification_id}",
                    )
                if binding.binding_scope != clarification.binding_scope:
                    _fail(
                        "clarification-binding-scope-mismatch",
                        f"{assertion.assertion_id} binding_scope does not match "
                        f"{binding.clarification_id}",
                    )
                if binding.binding_scope == "requirement-code":
                    local_codes = set(binding.requirement_codes)
                    unknown_clarification_codes = sorted(
                        local_codes - set(clarification.requirement_codes)
                    )
                    if unknown_clarification_codes:
                        _fail(
                            "clarification-requirement-code-mismatch",
                            f"{assertion.assertion_id} clarification binding names codes "
                            f"outside {binding.clarification_id}: "
                            + ", ".join(unknown_clarification_codes),
                        )
                    unknown_assertion_codes = sorted(
                        local_codes - set(assertion.requirement_codes)
                    )
                    if unknown_assertion_codes:
                        _fail(
                            "clarification-assertion-requirement-code-mismatch",
                            f"{assertion.assertion_id} clarification binding claims codes "
                            "not owned by that assertion: "
                            + ", ".join(unknown_assertion_codes),
                        )
                    bound_requirement_codes_by_clarification.setdefault(
                        binding.clarification_id, set()
                    ).update(local_codes)
                else:
                    local_rows = set(binding.source_row_ids)
                    unknown_clarification_rows = sorted(
                        local_rows - set(clarification.source_row_ids)
                    )
                    if unknown_clarification_rows:
                        _fail(
                            "clarification-source-context-row-mismatch",
                            f"{assertion.assertion_id} binding names rows outside "
                            f"{binding.clarification_id}: "
                            + ", ".join(unknown_clarification_rows),
                        )
                    if local_rows != {assertion.source_row_id}:
                        _fail(
                            "clarification-assertion-source-context-row-mismatch",
                            f"{assertion.assertion_id} source-context binding must name "
                            f"only its own row {assertion.source_row_id}",
                        )
                    bound_source_row_ids_by_clarification.setdefault(
                        binding.clarification_id, set()
                    ).update(local_rows)
                    for source_row_id in local_rows:
                        source_context_binding_kinds.setdefault(
                            (binding.clarification_id, source_row_id), set()
                        ).add(binding.clause_kind)
                used_clarification_ids.add(binding.clarification_id)
        orphan_clarifications = sorted(
            set(clarification_by_id) - used_clarification_ids
        )
        if orphan_clarifications:
            _fail(
                "orphan-approved-clarification",
                "approved clarifications have no clause-level assertion binding: "
                + ", ".join(orphan_clarifications),
            )
        for clarification_id, clarification in clarification_by_id.items():
            if clarification.binding_scope == "requirement-code":
                declared_codes = set(clarification.requirement_codes)
                definition_gapped_codes = {
                    code
                    for gap in coverage_gap_bindings.values()
                    if gap.status == "open"
                    and gap.gap_type == "missing-source-definition"
                    and gap.affected_assertion_ids
                    for code in gap.requirement_codes
                }
                bound_codes = bound_requirement_codes_by_clarification.get(
                    clarification_id, set()
                )
                # A definition gap permits a declared code to remain unbound only
                # when no executable assertion can own it.  Do not remove a code
                # that is already bound by a source-backed assertion: one row can
                # contain both a testable clause and a narrower definition gap.
                declared_codes -= definition_gapped_codes - bound_codes
                if bound_codes != declared_codes:
                    _fail(
                        "clarification-binding-requirement-code-set-mismatch",
                        f"{clarification_id} clause bindings must cover its exact "
                        "requirement-code set: "
                        f"missing={sorted(declared_codes - bound_codes) or 'none'}, "
                        f"unexpected={sorted(bound_codes - declared_codes) or 'none'}",
                    )
            else:
                declared_rows = set(clarification.source_row_ids)
                bound_rows = bound_source_row_ids_by_clarification.get(
                    clarification_id, set()
                )
                if bound_rows != declared_rows:
                    _fail(
                        "clarification-binding-source-context-row-set-mismatch",
                        f"{clarification_id} clause bindings must cover its exact "
                        "source-row set: "
                        f"missing={sorted(declared_rows - bound_rows) or 'none'}, "
                        f"unexpected={sorted(bound_rows - declared_rows) or 'none'}",
                    )
                noncanonical_excluded_rows = sorted(
                    source_row_id
                    for source_row_id in declared_rows
                    if source_rows_by_id[source_row_id].scope_disposition == "no"
                    and source_context_binding_kinds.get(
                        (clarification_id, source_row_id), set()
                    )
                    != {"canonical"}
                )
                if noncanonical_excluded_rows:
                    _fail(
                        "clarification-excluded-row-not-canonical",
                        f"{clarification_id} excluded source-context rows must bind "
                        "exactly one canonical not-applicable assertion: "
                        + ", ".join(noncanonical_excluded_rows),
                    )
        bound_clarification_paths = {
            item.evidence_source_path for item in self.clarifications
        }
        for evidence_path in sorted(bound_clarification_paths):
            canonical_rows = clarification_rows_by_path[evidence_path]
            canonical_approved_ids = {
                clarification_id
                for clarification_id, row in canonical_rows.items()
                if row["scope_slug"] == self.scope_slug
                and row["response_status"] == "answered"
                and row["response_type"]
                in APPROVED_CLARIFICATION_RESPONSE_TYPES
            }
            registered_ids = {
                item.clarification_id
                for item in self.clarifications
                if item.evidence_source_path == evidence_path
            }
            if canonical_approved_ids != registered_ids:
                _fail(
                    "clarification-record-set-mismatch",
                    "current-scope answered/approved clarification rows must equal "
                    "the typed manifest registry for "
                    f"{evidence_path}: missing="
                    f"{sorted(canonical_approved_ids - registered_ids) or 'none'}, "
                    f"unexpected={sorted(registered_ids - canonical_approved_ids) or 'none'}",
                )
        unbound_clarification_sources = sorted(
            path
            for path, evidence_source in evidence_sources_by_path.items()
            if evidence_source.role == "approved-clarification"
            and path not in bound_clarification_paths
        )
        if unbound_clarification_sources:
            _fail(
                "orphan-approved-clarification-source",
                "registered approved-clarification evidence has no typed record: "
                + ", ".join(unbound_clarification_sources),
            )

        expected_coverage_gap_ids = (
            set(primary_assertion_ids_by_gap)
            | set(execution_chains_by_gap)
            | {item.gap_id for item in self.clarifications}
            | {
                gap_id
                for gap_id, gap in coverage_gap_bindings.items()
                if gap.affected_assertion_ids
            }
        )
        orphan_coverage_gap_ids = sorted(
            set(coverage_gap_bindings) - expected_coverage_gap_ids
        )
        if orphan_coverage_gap_ids:
            _fail(
                "orphan-coverage-gap",
                "hash-bound coverage gap headings have no primary, execution-dependency, "
                "approved-clarification or exact affected ASSERT/ATOM binding: "
                + ", ".join(orphan_coverage_gap_ids),
            )

        if expected_source_row_ids is not None:
            expected_rows = tuple(
                _nonempty_text(item, "expected_source_row_ids[]")
                for item in expected_source_row_ids
            )
            if len(expected_rows) != len(set(expected_rows)):
                _fail("duplicate-expected-source-row", "expected_source_row_ids contains duplicates")
            actual_rows = set(source_rows_by_id)
            missing_rows = sorted(set(expected_rows) - actual_rows)
            unexpected_rows = sorted(actual_rows - set(expected_rows))
            if missing_rows or unexpected_rows:
                _fail(
                    "source-row-completeness-mismatch",
                    f"source rows mismatch: missing={missing_rows or 'none'}, "
                    f"unexpected={unexpected_rows or 'none'}",
                )
        if expected_source_rows is not None:
            expected_registry: dict[str, SourceRow] = {}
            for expected_row in expected_source_rows:
                if not isinstance(expected_row, SourceRow):
                    _fail(
                        "invalid-expected-source-row",
                        "expected_source_rows contains an invalid item",
                    )
                expected_row.validate_shape()
                if expected_row.source_row_id in expected_registry:
                    _fail(
                        "duplicate-expected-source-row",
                        "expected_source_rows contains duplicate source_row_id values",
                    )
                expected_registry[expected_row.source_row_id] = expected_row
            missing_rows = sorted(set(expected_registry) - set(source_rows_by_id))
            unexpected_rows = sorted(set(source_rows_by_id) - set(expected_registry))
            mismatched_rows = sorted(
                source_row_id
                for source_row_id in set(expected_registry) & set(source_rows_by_id)
                if source_rows_by_id[source_row_id] != expected_registry[source_row_id]
            )
            if missing_rows or unexpected_rows or mismatched_rows:
                _fail(
                    "source-row-registry-mismatch",
                    "manifest source_rows must exactly match source-row-inventory: "
                    f"missing={missing_rows or 'none'}, "
                    f"unexpected={unexpected_rows or 'none'}, "
                    f"mismatched={mismatched_rows or 'none'}",
                )

        if approved_polarities is not None:
            unknown_assertions = sorted(set(approved_polarities) - assertion_ids)
            if unknown_assertions:
                _fail(
                    "unknown-approved-polarity-assertion",
                    "approved polarity mapping names unknown assertions: "
                    + ", ".join(unknown_assertions),
                )
            by_id = {item.assertion_id: item for item in self.assertions}
            for assertion_id, expected_polarity in approved_polarities.items():
                if expected_polarity not in POLARITIES:
                    _fail(
                        "invalid-approved-polarity",
                        f"approved polarity for {assertion_id} must be one of "
                        f"{sorted(POLARITIES)}",
                    )
                actual_polarity = by_id[assertion_id].polarity
                if actual_polarity != expected_polarity:
                    _fail(
                        "approved-polarity-mismatch",
                        f"{assertion_id} declares {actual_polarity}, "
                        f"approved polarity is {expected_polarity}",
                    )

        mockup_paths: set[str] = set()
        screen_names: set[str] = set()
        for mockup in self.mockups:
            _relative_path(mockup.path, "mockup.path")
            _sha256(mockup.sha256, "mockup.sha256")
            _nonempty_text(mockup.screen_name, "mockup.screen_name")
            if not mockup.locators:
                _fail("mockup-locators-missing", f"{mockup.path} must declare locators")
            if len(mockup.locators) != len(set(mockup.locators)):
                _fail("duplicate-mockup-locator", f"{mockup.path} locators contain duplicates")
            if mockup.path in mockup_paths:
                _fail("duplicate-mockup", f"duplicate mockup path {mockup.path}")
            mockup_paths.add(mockup.path)
            if mockup.path in evidence_paths or mockup.path in source_files:
                _fail(
                    "registered-path-role-overlap",
                    f"registered path has multiple source roles: {mockup.path}",
                )
            if mockup.screen_name in screen_names:
                _fail("duplicate-screen-name", f"duplicate mockup screen_name {mockup.screen_name}")
            screen_names.add(mockup.screen_name)
            actual_path = _resolve_registered_path(repo_root, mockup.path, "mockup.path")
            actual_sha = sha256_file(actual_path)
            if actual_sha != mockup.sha256:
                _fail(
                    "stale-mockup-sha256",
                    f"registered SHA-256 for {mockup.path} is stale: "
                    f"expected={mockup.sha256}, actual={actual_sha}",
                )

    def to_compact_reviewer_basis(self) -> dict[str, Any]:
        return {
            "contract": COMPACT_REVIEWER_BASIS_CONTRACT,
            "manifest_digest": self.digest,
            "scope_slug": self.scope_slug,
            "source_row_extraction_spec_digest": (
                self.source_row_extraction_spec_digest
            ),
            "source_row_baseline_digest": self.source_row_baseline_digest,
            "source_row_candidate_count": self.source_row_candidate_count,
            "coverage_gaps_artifact": self.coverage_gaps_artifact.to_dict(),
            "sources": [item.to_dict() for item in self.sources],
            "source_rows": [item.to_dict() for item in self.source_rows],
            "assertions": [item.to_dict() for item in self.assertions],
            "clarifications": [item.to_dict() for item in self.clarifications],
            "evidence_sources": [item.to_dict() for item in self.evidence_sources],
            "mockups": [item.to_dict() for item in self.mockups],
        }

    def compact_reviewer_basis_json(self) -> str:
        return json.dumps(
            self.to_compact_reviewer_basis(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True)
class SourceAssertionReview:
    assertion_id: str
    approved_polarity: str
    approved_semantic_disposition: str
    approved_execution_readiness: str
    approved_risk: str
    dimension_verdicts: Mapping[str, str]
    verdict: str
    required_change: str
    note: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceAssertionReview":
        _exact_fields(
            payload,
            required={
                "assertion_id",
                "approved_polarity",
                "approved_semantic_disposition",
                "approved_execution_readiness",
                "approved_risk",
                "dimension_verdicts",
                "verdict",
                "required_change",
                "note",
            },
            label="source assertion review",
        )
        result = cls(
            assertion_id=_nonempty_text(
                payload["assertion_id"], "source assertion review.assertion_id"
            ),
            approved_polarity=_nonempty_text(
                payload["approved_polarity"],
                "source assertion review.approved_polarity",
            ),
            approved_semantic_disposition=_nonempty_text(
                payload["approved_semantic_disposition"],
                "source assertion review.approved_semantic_disposition",
            ),
            approved_execution_readiness=_nonempty_text(
                payload["approved_execution_readiness"],
                "source assertion review.approved_execution_readiness",
            ),
            approved_risk=_nonempty_text(
                payload["approved_risk"],
                "source assertion review.approved_risk",
            ),
            dimension_verdicts=payload["dimension_verdicts"],
            verdict=_nonempty_text(
                payload["verdict"], "source assertion review.verdict"
            ),
            required_change=_nonempty_text(
                payload["required_change"],
                "source assertion review.required_change",
            ),
            note=_review_explanation(
                payload["note"], "source assertion review.note"
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        _nonempty_text(self.assertion_id, "source assertion review.assertion_id")
        _review_explanation(self.note, f"{self.assertion_id}.note")
        if self.approved_polarity not in POLARITIES:
            _fail(
                "invalid-approved-polarity",
                f"{self.assertion_id}.approved_polarity must be one of "
                f"{sorted(POLARITIES)}",
            )
        if self.approved_semantic_disposition not in SEMANTIC_DISPOSITIONS:
            _fail(
                "invalid-approved-semantic-disposition",
                f"{self.assertion_id}.approved_semantic_disposition must be one of "
                f"{sorted(SEMANTIC_DISPOSITIONS)}",
            )
        if self.approved_execution_readiness not in EXECUTION_READINESS_VALUES:
            _fail(
                "invalid-approved-execution-readiness",
                f"{self.assertion_id}.approved_execution_readiness must be one of "
                f"{sorted(EXECUTION_READINESS_VALUES)}",
            )
        if self.approved_semantic_disposition == "not-applicable":
            approved_readiness_values = {"not-applicable"}
        elif self.approved_semantic_disposition == "ambiguous":
            approved_readiness_values = {"dependency-blocked"}
        else:
            approved_readiness_values = {"ready", "dependency-blocked"}
        if self.approved_execution_readiness not in approved_readiness_values:
            _fail(
                "approved-execution-readiness-disposition-mismatch",
                f"{self.assertion_id} approved semantic disposition requires "
                f"execution readiness in {sorted(approved_readiness_values)}",
            )
        if self.approved_risk not in RISKS:
            _fail(
                "invalid-approved-risk",
                f"{self.assertion_id}.approved_risk must be one of {sorted(RISKS)}",
            )
        if self.verdict not in SOURCE_REVIEW_VERDICTS:
            _fail(
                "invalid-source-review-verdict",
                f"{self.assertion_id}.verdict must be one of "
                f"{sorted(SOURCE_REVIEW_VERDICTS)}",
            )
        if not isinstance(self.dimension_verdicts, Mapping):
            _fail(
                "invalid-source-review-dimensions",
                f"{self.assertion_id}.dimension_verdicts must be a JSON object",
            )
        actual_dimensions = set(self.dimension_verdicts)
        expected_dimensions = set(SOURCE_REVIEW_DIMENSIONS)
        missing = sorted(expected_dimensions - actual_dimensions)
        unknown = sorted(actual_dimensions - expected_dimensions)
        if missing or unknown:
            _fail(
                "source-review-dimension-set-mismatch",
                f"{self.assertion_id}.dimension_verdicts mismatch: "
                f"missing={missing or 'none'}, unknown={unknown or 'none'}",
            )
        invalid_dimension_verdicts = {
            dimension: verdict
            for dimension, verdict in self.dimension_verdicts.items()
            if verdict not in SOURCE_REVIEW_DIMENSION_VERDICTS
        }
        if invalid_dimension_verdicts:
            _fail(
                "invalid-source-review-dimension-verdict",
                f"{self.assertion_id}.dimension_verdicts values must be one of "
                f"{sorted(SOURCE_REVIEW_DIMENSION_VERDICTS)}: "
                f"{invalid_dimension_verdicts}",
            )
        expected_verdict = (
            "incorrect"
            if any(
                self.dimension_verdicts[dimension] == "incorrect"
                for dimension in SOURCE_REVIEW_DIMENSIONS
            )
            else "verified"
        )
        if self.verdict != expected_verdict:
            _fail(
                "source-review-verdict-aggregate-mismatch",
                f"{self.assertion_id}.verdict must equal aggregate dimension verdict "
                f"{expected_verdict}",
            )
        if self.verdict == "verified":
            if self.required_change != NO_REQUIRED_CHANGE:
                _fail(
                    "verified-source-review-required-change-invalid",
                    f"{self.assertion_id} verified review requires "
                    f"required_change={NO_REQUIRED_CHANGE}",
                )
        else:
            if self.required_change == NO_REQUIRED_CHANGE:
                _fail(
                    "incorrect-source-review-required-change-missing",
                    f"{self.assertion_id} incorrect review requires a substantive "
                    "required_change",
                )
            _review_explanation(
                self.required_change,
                f"{self.assertion_id}.required_change",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assertion_id": self.assertion_id,
            "approved_polarity": self.approved_polarity,
            "approved_semantic_disposition": self.approved_semantic_disposition,
            "approved_execution_readiness": self.approved_execution_readiness,
            "approved_risk": self.approved_risk,
            "dimension_verdicts": {
                dimension: self.dimension_verdicts[dimension]
                for dimension in SOURCE_REVIEW_DIMENSIONS
            },
            "verdict": self.verdict,
            "required_change": self.required_change,
            "note": self.note,
        }


@dataclass(frozen=True)
class SourceInventoryReview:
    extraction_spec_digest: str
    baseline_digest: str
    candidate_count: int
    mapped_source_row_count: int
    verdict: str
    required_change: str
    note: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceInventoryReview":
        _exact_fields(
            payload,
            required={
                "extraction_spec_digest",
                "baseline_digest",
                "candidate_count",
                "mapped_source_row_count",
                "verdict",
                "required_change",
                "note",
            },
            label="source inventory review",
        )
        if type(payload["candidate_count"]) is not int:
            _fail(
                "invalid-source-inventory-count",
                "source inventory review.candidate_count must be an integer",
            )
        if type(payload["mapped_source_row_count"]) is not int:
            _fail(
                "invalid-source-inventory-count",
                "source inventory review.mapped_source_row_count must be an integer",
            )
        result = cls(
            extraction_spec_digest=_sha256(
                payload["extraction_spec_digest"],
                "source inventory review.extraction_spec_digest",
            ),
            baseline_digest=_sha256(
                payload["baseline_digest"],
                "source inventory review.baseline_digest",
            ),
            candidate_count=payload["candidate_count"],
            mapped_source_row_count=payload["mapped_source_row_count"],
            verdict=_nonempty_text(
                payload["verdict"], "source inventory review.verdict"
            ),
            required_change=_nonempty_text(
                payload["required_change"],
                "source inventory review.required_change",
            ),
            note=_review_explanation(
                payload["note"], "source inventory review.note"
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        _sha256(
            self.extraction_spec_digest,
            "source inventory review.extraction_spec_digest",
        )
        _sha256(self.baseline_digest, "source inventory review.baseline_digest")
        if type(self.candidate_count) is not int or self.candidate_count <= 0:
            _fail(
                "invalid-source-inventory-count",
                "source inventory review.candidate_count must be positive",
            )
        if (
            type(self.mapped_source_row_count) is not int
            or self.mapped_source_row_count != self.candidate_count
        ):
            _fail(
                "invalid-source-inventory-count",
                "source inventory review.mapped_source_row_count must equal "
                "candidate_count for the singular v1 candidate baseline",
            )
        if self.verdict not in SOURCE_REVIEW_VERDICTS:
            _fail(
                "invalid-source-inventory-verdict",
                "source inventory review.verdict must be verified or incorrect",
            )
        if self.verdict == "verified":
            if self.required_change != NO_REQUIRED_CHANGE:
                _fail(
                    "verified-source-inventory-required-change-invalid",
                    "verified source inventory review requires "
                    f"required_change={NO_REQUIRED_CHANGE}",
                )
        else:
            if self.required_change == NO_REQUIRED_CHANGE:
                _fail(
                    "incorrect-source-inventory-required-change-missing",
                    "incorrect source inventory review requires a substantive change",
                )
            _review_explanation(
                self.required_change,
                "source inventory review.required_change",
            )
        _review_explanation(self.note, "source inventory review.note")

    def validate(self, manifest: "SourceAssertionManifest") -> None:
        self.validate_shape()
        if (
            self.extraction_spec_digest
            != manifest.source_row_extraction_spec_digest
            or self.baseline_digest != manifest.source_row_baseline_digest
            or self.candidate_count != manifest.source_row_candidate_count
        ):
            _fail(
                "source-inventory-review-manifest-mismatch",
                "source inventory review must bind the exact extraction spec, baseline "
                "and candidate count carried by the manifest",
            )
        mapped_source_row_count = sum(
            1 for row in manifest.source_rows if row.candidate_id is not None
        )
        if self.mapped_source_row_count != mapped_source_row_count:
            _fail(
                "source-inventory-review-mapped-count-mismatch",
                "source inventory review.mapped_source_row_count must equal the exact "
                "number of candidate-bound manifest source rows",
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "extraction_spec_digest": self.extraction_spec_digest,
            "baseline_digest": self.baseline_digest,
            "candidate_count": self.candidate_count,
            "mapped_source_row_count": self.mapped_source_row_count,
            "verdict": self.verdict,
            "required_change": self.required_change,
            "note": self.note,
        }


@dataclass(frozen=True)
class ScopeBoundaryManifestContext:
    context_class: str
    source_row_id: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeBoundaryManifestContext":
        _exact_fields(
            payload,
            required={"context_class", "source_row_id"},
            label="scope boundary manifest context",
        )
        result = cls(
            context_class=_nonempty_text(
                payload["context_class"],
                "scope boundary manifest context.context_class",
            ),
            source_row_id=_nonempty_text(
                payload["source_row_id"],
                "scope boundary manifest context.source_row_id",
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if self.context_class not in SCOPE_BOUNDARY_CONTEXT_CLASSES:
            _fail(
                "invalid-scope-boundary-context-class",
                "scope boundary manifest context.context_class must be one of "
                f"{sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES)}",
            )
        if not re.fullmatch(r"SRC-[A-Za-z0-9_.-]+", self.source_row_id):
            _fail(
                "invalid-scope-boundary-source-row",
                "scope boundary manifest context.source_row_id must name one SRC-* row",
            )

    def validate(self, manifest: SourceAssertionManifest) -> None:
        self.validate_shape()
        source_row = next(
            (
                item
                for item in manifest.source_rows
                if item.source_row_id == self.source_row_id
            ),
            None,
        )
        if source_row is None:
            _fail(
                "scope-boundary-source-row-missing",
                "scope boundary manifest context names a row absent from the manifest: "
                + self.source_row_id,
            )
        assertions = tuple(
            item
            for item in manifest.assertions
            if item.source_row_id == self.source_row_id
        )
        if not assertions:
            _fail(
                "scope-boundary-source-row-missing",
                "scope boundary manifest context names a row absent from the manifest: "
                + self.source_row_id,
            )
        if source_row.source_context_class != self.context_class:
            _fail(
                "scope-boundary-context-class-mismatch",
                "scope boundary manifest context must equal the hash-bound manifest "
                f"classification for {self.source_row_id}: "
                f"declared={self.context_class}, "
                f"manifest={source_row.source_context_class}",
            )

    def to_dict(self) -> dict[str, str]:
        self.validate_shape()
        return {
            "context_class": self.context_class,
            "source_row_id": self.source_row_id,
        }


@dataclass(frozen=True)
class ScopeBoundaryExclusion:
    context_class: str
    source_path: str
    source_sha256: str
    source_locator: str
    exact_source_text: str
    reason: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeBoundaryExclusion":
        _exact_fields(
            payload,
            required={
                "context_class",
                "source_path",
                "source_sha256",
                "source_locator",
                "exact_source_text",
                "reason",
            },
            label="scope boundary exclusion",
        )
        result = cls(
            context_class=_nonempty_text(
                payload["context_class"],
                "scope boundary exclusion.context_class",
            ),
            source_path=_relative_path(
                payload["source_path"],
                "scope boundary exclusion.source_path",
            ),
            source_sha256=_sha256(
                payload["source_sha256"],
                "scope boundary exclusion.source_sha256",
            ),
            source_locator=_nonempty_text(
                payload["source_locator"],
                "scope boundary exclusion.source_locator",
            ),
            exact_source_text=_nonempty_text(
                payload["exact_source_text"],
                "scope boundary exclusion.exact_source_text",
            ),
            reason=_review_explanation(
                payload["reason"],
                "scope boundary exclusion.reason",
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if self.context_class not in SCOPE_BOUNDARY_CONTEXT_CLASSES:
            _fail(
                "invalid-scope-boundary-context-class",
                "scope boundary exclusion.context_class must be one of "
                f"{sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES)}",
            )
        _relative_path(
            self.source_path,
            "scope boundary exclusion.source_path",
        )
        _sha256(
            self.source_sha256,
            "scope boundary exclusion.source_sha256",
        )
        locator = _nonempty_text(
            self.source_locator,
            "scope boundary exclusion.source_locator",
        )
        exact_source_text = _nonempty_text(
            self.exact_source_text,
            "scope boundary exclusion.exact_source_text",
        )
        reason = _review_explanation(
            self.reason,
            "scope boundary exclusion.reason",
        )
        normalized_reason = normalize_exact_source_text(reason).casefold()
        if normalized_reason in {
            normalize_exact_source_text(locator).casefold(),
            normalize_exact_source_text(exact_source_text).casefold(),
        }:
            _fail(
                "placeholder-review-explanation",
                "scope boundary exclusion.reason must explain, not repeat, its source binding",
            )

    def validate(self, manifest: SourceAssertionManifest) -> None:
        self.validate_shape()
        source_by_path = {item.path: item for item in manifest.sources}
        registered_source = source_by_path.get(self.source_path)
        if registered_source is None:
            _fail(
                "scope-boundary-exclusion-source-unregistered",
                "scope boundary exclusion must bind a registered UTF-8 source: "
                + self.source_path,
            )
        if registered_source.sha256 != self.source_sha256:
            _fail(
                "scope-boundary-exclusion-source-digest-mismatch",
                "scope boundary exclusion source SHA-256 does not match the manifest: "
                + self.source_path,
            )
        source_text = manifest._validated_source_texts.get(self.source_path)
        if source_text is None:
            _fail(
                "scope-boundary-exclusion-source-unvalidated",
                "scope boundary exclusion requires a manifest validated against its "
                "registered source content: " + self.source_path,
            )
        expected_text = normalize_exact_source_text(self.exact_source_text)
        if not contains_token_bounded_source_fragment(source_text, expected_text):
            _fail(
                "scope-boundary-exclusion-text-mismatch",
                "scope boundary exclusion exact_source_text is absent from the "
                "registered source: " + self.source_path,
            )
        for source_row in manifest.source_rows:
            if source_row.source_path != self.source_path:
                continue
            row_text = normalize_exact_source_text(source_row.bounded_source_text)
            if contains_token_bounded_source_fragment(row_text, expected_text) or (
                contains_token_bounded_source_fragment(expected_text, row_text)
            ):
                _fail(
                    "scope-boundary-exclusion-overlaps-manifest-row",
                    "scope boundary exclusions may describe only source-bound context "
                    "outside manifest source_rows; reviewed manifest rows cannot be "
                    "reclassified as exclusions",
                )
        expected_locator = scope_boundary_source_locator(
            self.source_path,
            self.exact_source_text,
        )
        if self.source_locator != expected_locator:
            _fail(
                "scope-boundary-exclusion-locator-mismatch",
                "scope boundary exclusion source_locator must equal the canonical "
                "content-bound locator",
            )

    def to_dict(self) -> dict[str, str]:
        self.validate_shape()
        return {
            "context_class": self.context_class,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "source_locator": self.source_locator,
            "exact_source_text": self.exact_source_text,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ScopeBoundaryReview:
    verdict: str
    checked_context_classes: tuple[str, ...]
    reviewed_manifest_contexts: tuple[ScopeBoundaryManifestContext, ...]
    excluded_contexts: tuple[ScopeBoundaryExclusion, ...]
    required_change: str
    note: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeBoundaryReview":
        _exact_fields(
            payload,
            required={
                "verdict",
                "checked_context_classes",
                "reviewed_manifest_contexts",
                "excluded_contexts",
                "required_change",
                "note",
            },
            label="scope boundary review",
        )
        reviewed_manifest_contexts = payload["reviewed_manifest_contexts"]
        if not isinstance(reviewed_manifest_contexts, list):
            _fail(
                "invalid-scope-boundary-manifest-contexts",
                "scope boundary review.reviewed_manifest_contexts must be a JSON array",
            )
        excluded_contexts = payload["excluded_contexts"]
        if not isinstance(excluded_contexts, list):
            _fail(
                "invalid-scope-boundary-exclusions",
                "scope boundary review.excluded_contexts must be a JSON array",
            )
        result = cls(
            verdict=_nonempty_text(
                payload["verdict"],
                "scope boundary review.verdict",
            ),
            checked_context_classes=_text_list(
                payload["checked_context_classes"],
                "scope boundary review.checked_context_classes",
                allow_empty=False,
            ),
            reviewed_manifest_contexts=tuple(
                ScopeBoundaryManifestContext.from_dict(item)
                for item in reviewed_manifest_contexts
            ),
            excluded_contexts=tuple(
                ScopeBoundaryExclusion.from_dict(item)
                for item in excluded_contexts
            ),
            required_change=_nonempty_text(
                payload["required_change"],
                "scope boundary review.required_change",
            ),
            note=_review_explanation(
                payload["note"],
                "scope boundary review.note",
            ),
        )
        return result

    def validate(self, manifest: SourceAssertionManifest) -> None:
        if self.verdict not in SOURCE_REVIEW_VERDICTS:
            _fail(
                "invalid-scope-boundary-verdict",
                "scope boundary review.verdict must be one of "
                f"{sorted(SOURCE_REVIEW_VERDICTS)}",
            )
        checked = tuple(
            _nonempty_text(
                item,
                "scope boundary review.checked_context_classes[]",
            )
            for item in self.checked_context_classes
        )
        if len(checked) != len(set(checked)):
            _fail(
                "duplicate-scope-boundary-context-class",
                "scope boundary review.checked_context_classes must not contain duplicates",
            )
        missing_contexts = sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES - set(checked))
        unknown_contexts = sorted(set(checked) - SCOPE_BOUNDARY_CONTEXT_CLASSES)
        if missing_contexts or unknown_contexts:
            _fail(
                "scope-boundary-context-set-mismatch",
                "scope boundary review context classes mismatch: "
                f"missing={missing_contexts or 'none'}, "
                f"unknown={unknown_contexts or 'none'}",
            )

        reviewed_keys: set[tuple[str, str]] = set()
        reviewed_rows: set[str] = set()
        for reviewed_context in self.reviewed_manifest_contexts:
            if not isinstance(reviewed_context, ScopeBoundaryManifestContext):
                _fail(
                    "invalid-scope-boundary-manifest-context",
                    "scope boundary review.reviewed_manifest_contexts contains an "
                    "invalid item",
                )
            reviewed_context.validate(manifest)
            key = (reviewed_context.context_class, reviewed_context.source_row_id)
            if key in reviewed_keys or reviewed_context.source_row_id in reviewed_rows:
                _fail(
                    "duplicate-scope-boundary-source-row",
                    "one scope boundary source row may be accounted exactly once",
                )
            reviewed_keys.add(key)
            reviewed_rows.add(reviewed_context.source_row_id)

        expected_reviewed_keys = {
            (source_row.source_context_class, source_row.source_row_id)
            for source_row in manifest.source_rows
            if source_row.source_context_class in SCOPE_BOUNDARY_CONTEXT_CLASSES
        }
        if reviewed_keys != expected_reviewed_keys:
            missing = sorted(expected_reviewed_keys - reviewed_keys)
            unexpected = sorted(reviewed_keys - expected_reviewed_keys)
            _fail(
                "scope-boundary-manifest-context-set-mismatch",
                "scope boundary reviewed_manifest_contexts must cover every hash-bound "
                "manifest row in a boundary context class exactly, including "
                "scope_disposition=no and all-N/A rows: "
                f"missing={missing or 'none'}, unexpected={unexpected or 'none'}",
            )

        exclusion_keys: set[tuple[str, str, str]] = set()
        exclusion_bindings: dict[tuple[str, str], str] = {}
        for exclusion in self.excluded_contexts:
            if not isinstance(exclusion, ScopeBoundaryExclusion):
                _fail(
                    "invalid-scope-boundary-exclusion",
                    "scope boundary review.excluded_contexts contains an invalid item",
                )
            exclusion.validate(manifest)
            key = (
                exclusion.context_class,
                exclusion.source_path,
                normalize_exact_source_text(exclusion.source_locator).casefold(),
            )
            if key in exclusion_keys:
                _fail(
                    "duplicate-scope-boundary-exclusion",
                    "scope boundary review contains a duplicate exclusion locator",
                )
            binding = (
                exclusion.source_path,
                normalize_exact_source_text(exclusion.source_locator).casefold(),
            )
            prior_context_class = exclusion_bindings.get(binding)
            if (
                prior_context_class is not None
                and prior_context_class != exclusion.context_class
            ):
                _fail(
                    "scope-boundary-exclusion-reused-across-context-classes",
                    "one source-bound exclusion locator cannot account for multiple "
                    "scope boundary context classes",
                )
            exclusion_keys.add(key)
            exclusion_bindings[binding] = exclusion.context_class
        accounted_context_classes = {
            item.context_class for item in self.reviewed_manifest_contexts
        } | {item.context_class for item in self.excluded_contexts}
        missing_context_evidence = sorted(
            SCOPE_BOUNDARY_CONTEXT_CLASSES - accounted_context_classes
        )
        if missing_context_evidence and self.verdict == "verified":
            _fail(
                "scope-boundary-class-evidence-missing",
                "each checked boundary class requires either every manifest row in "
                "reviewed_manifest_contexts or one source-bound excluded context outside "
                "the manifest; missing=" + ", ".join(missing_context_evidence),
            )
        if self.verdict == "verified":
            if self.required_change != NO_REQUIRED_CHANGE:
                _fail(
                    "verified-scope-boundary-required-change-invalid",
                    "verified scope boundary review requires "
                    f"required_change={NO_REQUIRED_CHANGE}",
                )
        else:
            if self.required_change == NO_REQUIRED_CHANGE:
                _fail(
                    "incorrect-scope-boundary-required-change-missing",
                    "incorrect scope boundary review requires a substantive required_change",
                )
            _review_explanation(
                self.required_change,
                "scope boundary review.required_change",
            )
        _review_explanation(self.note, "scope boundary review.note")

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "checked_context_classes": list(self.checked_context_classes),
            "reviewed_manifest_contexts": [
                item.to_dict() for item in self.reviewed_manifest_contexts
            ],
            "excluded_contexts": [item.to_dict() for item in self.excluded_contexts],
            "required_change": self.required_change,
            "note": self.note,
        }


@dataclass(frozen=True)
class SourceAssertionReviewReceipt:
    version: int
    manifest_digest: str
    decision: str
    assertion_reviews: tuple[SourceAssertionReview, ...]
    source_inventory_review: SourceInventoryReview
    scope_boundary_review: ScopeBoundaryReview

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceAssertionReviewReceipt":
        if not isinstance(payload, Mapping):
            _fail(
                "invalid-object",
                "source assertion review receipt must be a JSON object",
            )
        if payload.get("version") in LEGACY_REVIEW_RECEIPT_VERSIONS:
            _fail(
                "legacy-review-receipt-requires-rereview",
                "legacy review receipts cannot attest the current typed, source-bound "
                "scope boundary contract; run a fresh independent source review and "
                f"issue receipt v{REVIEW_RECEIPT_VERSION}",
            )
        if (
            type(payload.get("version")) is not int
            or payload.get("version") != REVIEW_RECEIPT_VERSION
        ):
            _fail(
                "unsupported-review-receipt-version",
                f"review receipt.version must equal {REVIEW_RECEIPT_VERSION}",
            )
        _exact_fields(
            payload,
            required={
                "version",
                "manifest_digest",
                "decision",
                "assertion_reviews",
                "source_inventory_review",
                "scope_boundary_review",
            },
            label="source assertion review receipt",
        )
        reviews = payload["assertion_reviews"]
        if not isinstance(reviews, list) or not reviews:
            _fail(
                "invalid-source-reviews",
                "review receipt.assertion_reviews must be a non-empty JSON array",
            )
        return cls(
            version=payload["version"],
            manifest_digest=_sha256(
                payload["manifest_digest"], "review receipt.manifest_digest"
            ),
            decision=_nonempty_text(payload["decision"], "review receipt.decision"),
            assertion_reviews=tuple(
                SourceAssertionReview.from_dict(item) for item in reviews
            ),
            source_inventory_review=SourceInventoryReview.from_dict(
                payload["source_inventory_review"]
            ),
            scope_boundary_review=ScopeBoundaryReview.from_dict(
                payload["scope_boundary_review"]
            ),
        )

    def validate(self, manifest: SourceAssertionManifest) -> None:
        if self.version in LEGACY_REVIEW_RECEIPT_VERSIONS:
            _fail(
                "legacy-review-receipt-requires-rereview",
                "legacy review receipts cannot attest the current typed, source-bound "
                "scope boundary contract; run a fresh independent source review and "
                f"issue receipt v{REVIEW_RECEIPT_VERSION}",
            )
        if self.version != REVIEW_RECEIPT_VERSION:
            _fail(
                "unsupported-review-receipt-version",
                f"review receipt.version must equal {REVIEW_RECEIPT_VERSION}",
            )
        if self.manifest_digest != manifest.digest:
            _fail(
                "source-review-manifest-digest-mismatch",
                "source assertion review receipt does not bind the current manifest",
            )
        if self.decision not in {"accepted", "changes-required"}:
            _fail(
                "invalid-source-review-decision",
                "review receipt.decision must be accepted or changes-required",
            )
        if not isinstance(self.source_inventory_review, SourceInventoryReview):
            _fail(
                "source-inventory-review-missing",
                f"review receipt v{REVIEW_RECEIPT_VERSION} requires "
                "source_inventory_review",
            )
        self.source_inventory_review.validate(manifest)
        if (
            self.decision == "accepted"
            and self.source_inventory_review.verdict != "verified"
        ):
            _fail(
                "accepted-source-review-has-unverified-inventory",
                "accepted source review requires a verified source inventory review",
            )
        if not isinstance(self.scope_boundary_review, ScopeBoundaryReview):
            _fail(
                "scope-boundary-review-missing",
                f"review receipt v{REVIEW_RECEIPT_VERSION} requires scope_boundary_review",
            )
        self.scope_boundary_review.validate(manifest)
        if (
            self.decision == "accepted"
            and self.scope_boundary_review.verdict != "verified"
        ):
            _fail(
                "accepted-source-review-has-unverified-scope-boundary",
                "accepted source review requires a verified scope boundary review",
            )
        review_ids = [item.assertion_id for item in self.assertion_reviews]
        if len(review_ids) != len(set(review_ids)):
            _fail(
                "duplicate-source-review",
                "review receipt contains duplicate assertion reviews",
            )
        assertion_by_id = {item.assertion_id: item for item in manifest.assertions}
        missing = sorted(set(assertion_by_id) - set(review_ids))
        unknown = sorted(set(review_ids) - set(assertion_by_id))
        if missing or unknown:
            _fail(
                "source-review-set-mismatch",
                f"source assertion review set mismatch: missing={missing or 'none'}, "
                f"unknown={unknown or 'none'}",
            )
        incorrect: list[str] = []
        for review in self.assertion_reviews:
            review.validate_shape()
            assertion = assertion_by_id[review.assertion_id]
            for dimension, approved_value, declared_value, mismatch_code in (
                (
                    "polarity",
                    review.approved_polarity,
                    assertion.polarity,
                    "approved-polarity-mismatch",
                ),
                (
                    "semantic-disposition",
                    review.approved_semantic_disposition,
                    assertion.semantic_disposition,
                    "approved-semantic-disposition-mismatch",
                ),
                (
                    "execution-readiness",
                    review.approved_execution_readiness,
                    assertion.execution_readiness,
                    "approved-execution-readiness-mismatch",
                ),
                (
                    "risk",
                    review.approved_risk,
                    assertion.risk,
                    "approved-risk-mismatch",
                ),
            ):
                dimension_verdict = review.dimension_verdicts[dimension]
                if dimension_verdict == "verified" and approved_value != declared_value:
                    _fail(
                        mismatch_code,
                        f"{review.assertion_id} declares {declared_value}, "
                        f"independent review verified {approved_value}",
                    )
                if dimension_verdict == "incorrect" and approved_value == declared_value:
                    _fail(
                        f"incorrect-{dimension}-without-proposed-change",
                        f"{review.assertion_id} marks {dimension} incorrect but does not "
                        "propose a different valid value",
                    )
            if review.verdict == "incorrect":
                incorrect.append(review.assertion_id)
        if self.decision == "accepted" and incorrect:
            _fail(
                "accepted-source-review-has-errors",
                "accepted source assertion review contains incorrect verdicts: "
                + ", ".join(incorrect),
            )
        if (
            self.decision == "changes-required"
            and not incorrect
            and self.source_inventory_review.verdict != "incorrect"
            and self.scope_boundary_review.verdict != "incorrect"
        ):
            _fail(
                "changes-required-source-review-without-errors",
                "changes-required source assertion review requires an incorrect assertion "
                "verdict, an incorrect source inventory review or an incorrect scope "
                "boundary review",
            )

    @property
    def approved_polarities(self) -> dict[str, str]:
        return {
            item.assertion_id: item.approved_polarity
            for item in self.assertion_reviews
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "manifest_digest": self.manifest_digest,
            "decision": self.decision,
            "assertion_reviews": [item.to_dict() for item in self.assertion_reviews],
            "source_inventory_review": self.source_inventory_review.to_dict(),
            "scope_boundary_review": self.scope_boundary_review.to_dict(),
        }


@dataclass(frozen=True)
class EmbeddedSourceAssertionContract:
    manifest: SourceAssertionManifest
    review_receipt: SourceAssertionReviewReceipt


def render_embedded_source_assertion_contract(
    manifest: SourceAssertionManifest,
    review_receipt: SourceAssertionReviewReceipt,
) -> str:
    """Render the complete digest-bound source-first contract for prepared evidence."""

    review_receipt.validate(manifest)
    if review_receipt.decision != "accepted":
        _fail(
            "source-review-not-accepted",
            "source assertion review receipt must be accepted before embedding",
        )
    basis_json = json.dumps(
        manifest.to_compact_reviewer_basis(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    receipt_json = json.dumps(
        review_receipt.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "\n".join(
        (
            SOURCE_ASSERTIONS_BASIS_HEADING,
            "",
            SOURCE_ASSERTIONS_MARKER,
            "```json",
            basis_json,
            "```",
            "",
            SOURCE_ASSERTIONS_REVIEW_HEADING,
            "",
            "```json",
            receipt_json,
            "```",
            "",
        )
    )


def parse_embedded_source_assertion_contract(
    evidence_text: str,
    repo_root: Path,
    *,
    expected_scope_slug: str,
    expected_obligation_ids: Iterable[str],
) -> EmbeddedSourceAssertionContract | None:
    """Authenticate a source-first block, or return ``None`` for genuine legacy evidence.

    Any partial source-first hint is rejected.  This prevents a lone marker from
    enabling the stricter runner path without the complete, current basis and
    independent review receipt.
    """

    if not isinstance(evidence_text, str):
        _fail("invalid-embedded-evidence", "prepared source evidence must be text")
    structural_hints = (
        SOURCE_ASSERTIONS_BASIS_HEADING,
        SOURCE_ASSERTIONS_MARKER,
        SOURCE_ASSERTIONS_REVIEW_HEADING,
    )
    if any(
        marker in evidence_text for marker in LEGACY_SOURCE_ASSERTIONS_MARKERS
    ) or any(
        contract in evidence_text
        for contract in LEGACY_COMPACT_REVIEWER_BASIS_CONTRACTS
    ):
        _fail(
            "legacy-embedded-source-contract-requires-rematerialization",
            "legacy embedded source assertion evidence requires a fresh manifest and "
            "independent review",
        )
    if not any(item in evidence_text for item in structural_hints):
        if COMPACT_REVIEWER_BASIS_CONTRACT in evidence_text:
            _fail(
                "incomplete-embedded-source-contract",
                "embedded source assertion contract name appears without its bounded block",
            )
        return None
    if any(evidence_text.count(item) != 1 for item in structural_hints):
        _fail(
            "incomplete-embedded-source-contract",
            "prepared source evidence must contain exactly one complete source-first block",
        )
    matches = tuple(_EMBEDDED_SOURCE_ASSERTIONS_RE.finditer(evidence_text))
    if len(matches) != 1:
        _fail(
            "incomplete-embedded-source-contract",
            "prepared source evidence source-first block has an invalid bounded shape",
        )
    match = matches[0]
    try:
        basis_payload = json.loads(match.group("basis"))
    except json.JSONDecodeError as exc:
        _fail(
            "invalid-embedded-basis-json",
            f"embedded source assertion basis is not valid JSON: {exc}",
        )
    if not isinstance(basis_payload, Mapping):
        _fail(
            "invalid-object",
            "embedded source assertion basis root must be a JSON object",
        )
    manifest = SourceAssertionManifest.from_compact_reviewer_basis(basis_payload)
    manifest.validate(repo_root)
    expected_scope = _nonempty_text(expected_scope_slug, "expected_scope_slug")
    if manifest.scope_slug != expected_scope:
        _fail(
            "embedded-scope-mismatch",
            "embedded source assertion scope does not match the prepared package",
        )

    try:
        receipt_payload = json.loads(match.group("receipt"))
    except json.JSONDecodeError as exc:
        _fail(
            "invalid-embedded-review-json",
            f"embedded source assertion review receipt is not valid JSON: {exc}",
        )
    if not isinstance(receipt_payload, Mapping):
        _fail(
            "invalid-object",
            "embedded source assertion review receipt root must be a JSON object",
        )
    review_receipt = SourceAssertionReviewReceipt.from_dict(receipt_payload)
    review_receipt.validate(manifest)
    if review_receipt.decision != "accepted":
        _fail(
            "source-review-not-accepted",
            "embedded source assertion review receipt must be accepted",
        )

    expected_ids = tuple(
        _nonempty_text(item, "expected_obligation_ids[]")
        for item in expected_obligation_ids
    )
    if len(expected_ids) != len(set(expected_ids)):
        _fail(
            "duplicate-expected-obligation",
            "expected_obligation_ids must not contain duplicates",
        )
    invalid_expected = sorted(
        item for item in expected_ids if OBLIGATION_ID_RE.fullmatch(item) is None
    )
    if invalid_expected:
        _fail(
            "invalid-expected-obligation-id",
            "expected source-first obligations must use OBL-* ids: "
            + ", ".join(invalid_expected),
        )
    actual_ids = {
        obligation_id
        for assertion in manifest.assertions
        if assertion.semantic_disposition == "testable"
        and assertion.execution_readiness == "ready"
        for obligation_id in assertion.obligation_ids
    }
    missing = sorted(set(expected_ids) - actual_ids)
    unexpected = sorted(actual_ids - set(expected_ids))
    if missing or unexpected:
        _fail(
            "embedded-obligation-set-mismatch",
            f"embedded source assertion obligations mismatch: "
            f"missing={missing or 'none'}, unexpected={unexpected or 'none'}",
        )
    return EmbeddedSourceAssertionContract(manifest, review_receipt)


def build_source_assertion_digest(manifest: SourceAssertionManifest) -> str:
    canonical = json.dumps(
        manifest.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class LegacySourceAssertionManifestDiagnostic:
    source_path: Path
    original_version: int
    scope_slug: str
    production_eligible: bool
    migration_available: bool
    migrated_manifest_digest: str | None


def migrate_source_assertion_manifest_v3_payload(
    payload: Mapping[str, Any],
    *,
    confirm_no_approved_clarifications: bool,
) -> dict[str, Any]:
    """Deterministically add the v4 empty clarification contract to a true v3 basis.

    Migration is intentionally opt-in because v3 could not prove that an external
    prose clarification was not used.  The caller must independently confirm that
    the v3 semantics contain zero approved clarifications.
    """

    if payload.get("version") not in MIGRATABLE_MANIFEST_VERSIONS:
        _fail(
            "source-manifest-migration-version-mismatch",
            "deterministic migration accepts only manifest version 3",
        )
    if not confirm_no_approved_clarifications:
        _fail(
            "source-manifest-migration-confirmation-required",
            "v3 to v4 migration requires explicit confirmation that no approved "
            "clarification influenced the manifest",
        )
    if "clarifications" in payload:
        _fail(
            "source-manifest-migration-ambiguous-input",
            "v3 manifest unexpectedly declares clarifications",
        )
    evidence_sources = payload.get("evidence_sources", [])
    if not isinstance(evidence_sources, list):
        _fail(
            "invalid-evidence-sources",
            "legacy manifest.evidence_sources must be a JSON array",
        )
    if any(
        isinstance(item, Mapping)
        and item.get("role") == "approved-clarification"
        for item in evidence_sources
    ):
        _fail(
            "source-manifest-migration-approved-clarification-present",
            "v3 manifest already names approved clarification evidence and must be "
            "rematerialized semantically instead of zero-clarification migration",
        )
    assertions = payload.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        _fail(
            "invalid-assertions",
            "legacy manifest.assertions must be a non-empty JSON array",
        )
    migrated = json.loads(json.dumps(payload, ensure_ascii=False))
    migrated["version"] = MANIFEST_VERSION
    migrated["clarifications"] = []
    for index, assertion in enumerate(migrated["assertions"]):
        if not isinstance(assertion, dict):
            _fail(
                "invalid-assertion",
                f"legacy manifest.assertions[{index}] must be an object",
            )
        if "clarification_clause_bindings" in assertion:
            _fail(
                "source-manifest-migration-ambiguous-input",
                "v3 assertion unexpectedly declares clarification_clause_bindings",
            )
        assertion["clarification_clause_bindings"] = []
    # Full v4 shape validation prevents migration from laundering malformed v3.
    SourceAssertionManifest.from_dict(migrated)
    return migrated


def load_legacy_source_assertion_manifest_diagnostic(
    path: Path,
    *,
    confirm_no_approved_clarifications: bool = False,
) -> LegacySourceAssertionManifestDiagnostic:
    """Read legacy v3 identity without making it runnable or promotable."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("invalid-manifest-json", f"cannot load source assertion manifest {path}: {exc}")
    if not isinstance(raw, Mapping):
        _fail("invalid-object", "source assertion manifest root must be a JSON object")
    if raw.get("version") != 3:
        _fail(
            "legacy-diagnostic-version-mismatch",
            "legacy diagnostic loader accepts only source assertion manifest v3",
        )
    scope_slug = _nonempty_text(raw.get("scope_slug"), "manifest.scope_slug")
    migrated_digest: str | None = None
    migration_available = False
    if confirm_no_approved_clarifications:
        migrated = migrate_source_assertion_manifest_v3_payload(
            raw,
            confirm_no_approved_clarifications=True,
        )
        migrated_digest = SourceAssertionManifest.from_dict(migrated).digest
        migration_available = True
    return LegacySourceAssertionManifestDiagnostic(
        source_path=path,
        original_version=3,
        scope_slug=scope_slug,
        production_eligible=False,
        migration_available=migration_available,
        migrated_manifest_digest=migrated_digest,
    )


def _infer_source_rows(assertions: Sequence[SourceAssertion]) -> tuple[SourceRow, ...]:
    """Infer only the unambiguous one-row case; complex rows require an explicit registry."""

    grouped: dict[str, list[SourceAssertion]] = {}
    bound_requirement_codes_by_row: dict[str, dict[str, None]] = {}
    for assertion in assertions:
        grouped.setdefault(assertion.source_row_id, []).append(assertion)
        for binding in assertion.requirement_code_bindings:
            bound_requirement_codes_by_row.setdefault(
                binding.source_row_id, {}
            ).setdefault(binding.requirement_code, None)
    inferred: list[SourceRow] = []
    for source_row_id, row_assertions in grouped.items():
        first = row_assertions[0]
        for assertion in row_assertions:
            if assertion.source_path != first.source_path:
                _fail(
                    "source-row-source-mismatch",
                    f"source_row_id {source_row_id} maps to multiple source paths",
                )
            if assertion.locator != first.locator:
                _fail(
                    "source-row-locator-mismatch",
                    f"source_row_id {source_row_id} maps to multiple locators",
                )
            if assertion.source_context_class != first.source_context_class:
                _fail(
                    "source-row-context-class-mismatch",
                    f"source_row_id {source_row_id} maps to multiple context classes",
                )
        fragments = tuple(
            normalize_exact_source_text(fragment)
            for assertion in row_assertions
            for fragment in (
                assertion.exact_source_text,
                *assertion.exact_source_fragments,
            )
        )
        candidates = sorted(
            {
                assertion.exact_source_text
                for assertion in row_assertions
            },
            key=lambda value: len(normalize_exact_source_text(value)),
            reverse=True,
        )
        bounded_source_text = next(
            (
                candidate
                for candidate in candidates
                if all(
                    contains_token_bounded_source_fragment(
                        normalize_exact_source_text(candidate),
                        fragment,
                    )
                    for fragment in fragments
                )
            ),
            None,
        )
        if bounded_source_text is None:
            _fail(
                "source-row-bounded-text-required",
                f"source_row_id {source_row_id} cannot be inferred from assertion "
                "fragments; provide an explicit bounded source_rows registry",
            )
        inferred.append(
            SourceRow(
                source_row_id=source_row_id,
                source_path=first.source_path,
                source_locator=first.locator,
                bounded_source_text=bounded_source_text,
                source_context_class=first.source_context_class,
                scope_disposition=(
                    "no"
                    if all(
                        assertion.semantic_disposition == "not-applicable"
                        for assertion in row_assertions
                    )
                    else (
                        "unclear"
                        if all(
                            assertion.semantic_disposition == "ambiguous"
                            for assertion in row_assertions
                        )
                        else "yes"
                    )
                ),
                requirement_codes=tuple(
                    bound_requirement_codes_by_row.get(source_row_id, {})
                ),
            )
        )
    return tuple(inferred)


def build_source_assertion_manifest(
    repo_root: Path,
    *,
    scope_slug: str,
    coverage_gaps_path: str,
    source_paths: Sequence[str],
    assertions: Sequence[SourceAssertion],
    source_row_extraction_spec_digest: str,
    source_row_baseline_digest: str,
    source_row_candidate_count: int,
    source_rows: Sequence[SourceRow] | None = None,
    source_row_candidate_ids: Mapping[str, str | None] | None = None,
    evidence_sources: Sequence[tuple[str, str]] = (),
    clarifications: Sequence[ApprovedClarification] = (),
    mockups: Sequence[tuple[str, str, Sequence[str]]] = (),
    expected_source_row_ids: Iterable[str] | None = None,
    expected_source_rows: Iterable[SourceRow] | None = None,
    approved_polarities: Mapping[str, str] | None = None,
) -> SourceAssertionManifest:
    registered_sources = tuple(
        RegisteredSource(
            path=_relative_path(path, "source_paths[]"),
            sha256=sha256_file(
                _resolve_registered_path(
                    repo_root,
                    _relative_path(path, "source_paths[]"),
                    "source_paths[]",
                )
            ),
        )
        for path in source_paths
    )
    normalized_coverage_gaps_path = _relative_path(
        coverage_gaps_path,
        "coverage_gaps_path",
    )
    registered_coverage_gaps = RegisteredArtifact(
        path=normalized_coverage_gaps_path,
        sha256=sha256_file(
            _resolve_registered_path(
                repo_root,
                normalized_coverage_gaps_path,
                "coverage_gaps_path",
            )
        ),
    )
    registered_mockups = tuple(
        RegisteredMockup(
            path=_relative_path(path, "mockups[].path"),
            sha256=sha256_file(
                _resolve_registered_path(
                    repo_root,
                    _relative_path(path, "mockups[].path"),
                    "mockups[].path",
                )
            ),
            screen_name=_nonempty_text(screen_name, "mockups[].screen_name"),
            locators=tuple(_nonempty_text(item, "mockups[].locators[]") for item in locators),
        )
        for path, screen_name, locators in mockups
    )
    registered_evidence_sources = tuple(
        RegisteredEvidenceSource(
            path=_relative_path(path, "evidence_sources[].path"),
            sha256=sha256_file(
                _resolve_registered_path(
                    repo_root,
                    _relative_path(path, "evidence_sources[].path"),
                    "evidence_sources[].path",
                )
            ),
            role=_nonempty_text(role, "evidence_sources[].role"),
        )
        for path, role in evidence_sources
    )
    if source_rows is not None and source_row_candidate_ids is not None:
        _fail(
            "ambiguous-source-candidate-mapping",
            "declare candidate_id on explicit source_rows instead of also passing "
            "source_row_candidate_ids",
        )
    if source_rows is None:
        inferred_source_rows = _infer_source_rows(assertions)
        if source_row_candidate_ids is None:
            _fail(
                "source-candidate-mapping-required",
                "inferred source rows require an explicit source_row_candidate_ids "
                "mapping bound to the extraction baseline",
            )
        inferred_ids = {item.source_row_id for item in inferred_source_rows}
        mapping_ids = set(source_row_candidate_ids)
        if inferred_ids != mapping_ids:
            _fail(
                "source-candidate-mapping-set-mismatch",
                "source_row_candidate_ids must map the inferred source-row set exactly: "
                f"missing={sorted(inferred_ids - mapping_ids) or 'none'}, "
                f"unknown={sorted(mapping_ids - inferred_ids) or 'none'}",
            )
        resolved_source_rows = tuple(
            replace(item, candidate_id=source_row_candidate_ids[item.source_row_id])
            for item in inferred_source_rows
        )
    else:
        resolved_source_rows = tuple(source_rows)

    manifest = SourceAssertionManifest(
        version=MANIFEST_VERSION,
        scope_slug=_nonempty_text(scope_slug, "scope_slug"),
        source_row_extraction_spec_digest=_sha256(
            source_row_extraction_spec_digest,
            "source_row_extraction_spec_digest",
        ),
        source_row_baseline_digest=_sha256(
            source_row_baseline_digest,
            "source_row_baseline_digest",
        ),
        source_row_candidate_count=source_row_candidate_count,
        coverage_gaps_artifact=registered_coverage_gaps,
        sources=registered_sources,
        assertions=tuple(assertions),
        clarifications=tuple(clarifications),
        source_rows=resolved_source_rows,
        evidence_sources=registered_evidence_sources,
        mockups=registered_mockups,
    )
    manifest.validate(
        repo_root,
        expected_source_row_ids=expected_source_row_ids,
        expected_source_rows=expected_source_rows,
        approved_polarities=approved_polarities,
    )
    return manifest


def validate_source_assertion_manifest(
    manifest: SourceAssertionManifest,
    repo_root: Path,
    *,
    expected_source_row_ids: Iterable[str] | None = None,
    expected_source_rows: Iterable[SourceRow] | None = None,
    approved_polarities: Mapping[str, str] | None = None,
) -> SourceAssertionManifest:
    manifest.validate(
        repo_root,
        expected_source_row_ids=expected_source_row_ids,
        expected_source_rows=expected_source_rows,
        approved_polarities=approved_polarities,
    )
    return manifest


def load_source_assertion_manifest(
    path: Path,
    repo_root: Path,
    *,
    expected_source_row_ids: Iterable[str] | None = None,
    expected_source_rows: Iterable[SourceRow] | None = None,
    approved_polarities: Mapping[str, str] | None = None,
) -> SourceAssertionManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("invalid-manifest-json", f"cannot load source assertion manifest {path}: {exc}")
    if not isinstance(raw, Mapping):
        _fail("invalid-object", "source assertion manifest root must be a JSON object")
    manifest = SourceAssertionManifest.from_dict(raw)
    return validate_source_assertion_manifest(
        manifest,
        repo_root,
        expected_source_row_ids=expected_source_row_ids,
        expected_source_rows=expected_source_rows,
        approved_polarities=approved_polarities,
    )


def load_source_assertion_review_receipt(
    path: Path,
    manifest: SourceAssertionManifest,
    *,
    require_accepted: bool = True,
) -> SourceAssertionReviewReceipt:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(
            "invalid-source-review-json",
            f"cannot load source assertion review receipt {path}: {exc}",
        )
    if not isinstance(raw, Mapping):
        _fail(
            "invalid-object",
            "source assertion review receipt root must be a JSON object",
        )
    receipt = SourceAssertionReviewReceipt.from_dict(raw)
    receipt.validate(manifest)
    if require_accepted and receipt.decision != "accepted":
        _fail(
            "source-review-not-accepted",
            "source assertion review receipt must be accepted before compilation",
        )
    return receipt
