from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


EXTRACTION_SPEC_VERSION = 1
SOURCE_ROW_BASELINE_VERSION = 1
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
SOURCE_CONTEXT_CLASSES = {
    "scope-local",
    "document-global-constraints",
    "ancestor-and-section-preamble",
    "cross-referenced-constraints",
}
CANDIDATE_ELEMENT_KINDS = {"tr", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6"}

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_SCOPE_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
_REGION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_SOURCE_ROW_ID_RE = re.compile(r"SRC-[A-Za-z0-9_.-]+")
_CANDIDATE_ID_RE = re.compile(r"SRC-CAND-[0-9a-f]{24}")
_NAMESPACE_PREFIX_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*")
_XPATH_STEP_RE = re.compile(
    r"(?P<node>\*|(?:[A-Za-z_][A-Za-z0-9_.-]*:)?[A-Za-z_][A-Za-z0-9_.-]*)"
    r"(?:\[(?P<position>[1-9][0-9]*)\])?"
)
_ASCII_CLASS_WHITESPACE_RE = re.compile(r"[ \t\r\n\f]+")
_DOCTYPE_RE = re.compile(
    rb"<!DOCTYPE(?:[^>\"']|\"[^\"]*\"|'[^']*')*>",
    re.IGNORECASE,
)


class SourceRowBaselineValidationError(ValueError):
    """A fail-closed deterministic source-row baseline violation."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise SourceRowBaselineValidationError(code, message)


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


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        _fail("invalid-boolean", f"{label} must be a JSON boolean")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("invalid-sha256", f"{label} must be lowercase SHA-256")
    return value


def _relative_path(value: Any, label: str) -> str:
    text = _nonempty_text(value, label)
    if "\\" in text or text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        _fail("invalid-relative-path", f"{label} must be repository-relative POSIX path")
    parsed = PurePosixPath(text)
    if parsed.as_posix() != text or any(part in {"", ".", ".."} for part in parsed.parts):
        _fail(
            "invalid-relative-path",
            f"{label} must be normalized and must not contain traversal",
        )
    return text


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    """Return a stable SHA-256 for a JSON-compatible value."""

    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def normalize_bounded_source_text(value: str) -> str:
    """Normalize transport whitespace while preserving source spelling and punctuation."""

    normalized = value.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    return re.sub(r"[ \t\n\f\v]+", " ", normalized).strip()


@dataclass(frozen=True)
class ResolvedXhtmlCandidate:
    """One baseline-visible candidate resolved at its canonical XHTML locator."""

    canonical_xpath: str
    element_kind: str
    bounded_source_text: str


@dataclass(frozen=True)
class ResolvedXhtmlTableCell:
    """One physical ``th``/``td`` child of a canonical XHTML table row."""

    physical_column_index: int
    canonical_xpath: str
    element_kind: str
    bounded_source_text: str


@dataclass(frozen=True)
class ResolvedXhtmlSectionHeading:
    """One visible standalone heading contributing to a candidate section path."""

    level: int
    canonical_xpath: str
    bounded_source_text: str


@dataclass(frozen=True)
class ResolvedXhtmlStructuralAncestor:
    """One exact list or table ancestor of a canonical XHTML candidate."""

    canonical_xpath: str
    element_kind: str


@dataclass(frozen=True)
class ResolvedXhtmlStructuralContext:
    """Deterministic document structure surrounding one canonical candidate."""

    canonical_xpath: str
    section_path: tuple[str, ...]
    section_headings: tuple[ResolvedXhtmlSectionHeading, ...]
    table_identity: str | None
    table_ancestry: tuple[ResolvedXhtmlStructuralAncestor, ...]
    list_ancestry: tuple[ResolvedXhtmlStructuralAncestor, ...]


@dataclass(frozen=True)
class SelectedXhtml:
    relative_path: str
    sha256: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SelectedXhtml":
        _exact_fields(
            payload,
            required={"relative_path", "sha256"},
            label="selected_xhtml",
        )
        result = cls(
            relative_path=_relative_path(
                payload["relative_path"], "selected_xhtml.relative_path"
            ),
            sha256=_sha256(payload["sha256"], "selected_xhtml.sha256"),
        )
        if not result.relative_path.lower().endswith(".xhtml"):
            _fail(
                "selected-source-is-not-xhtml",
                "selected_xhtml.relative_path must identify an .xhtml file",
            )
        return result

    def to_dict(self) -> dict[str, str]:
        return {"relative_path": self.relative_path, "sha256": self.sha256}


@dataclass(frozen=True)
class ContainerSelector:
    container_xpath: str
    kind: str = "container"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContainerSelector":
        _exact_fields(
            payload,
            required={"kind", "container_xpath"},
            label="container selector",
        )
        if payload["kind"] != "container":
            _fail("invalid-region-kind", "container selector.kind must be 'container'")
        xpath = _absolute_xpath(payload["container_xpath"], "selector.container_xpath")
        return cls(container_xpath=xpath)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "container_xpath": self.container_xpath}


@dataclass(frozen=True)
class ContiguousSiblingRangeSelector:
    start_xpath: str
    end_xpath: str
    include_start: bool
    include_end: bool
    kind: str = "contiguous-sibling-range"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ContiguousSiblingRangeSelector":
        _exact_fields(
            payload,
            required={
                "kind",
                "start_xpath",
                "end_xpath",
                "include_start",
                "include_end",
            },
            label="contiguous sibling range selector",
        )
        if payload["kind"] != "contiguous-sibling-range":
            _fail(
                "invalid-region-kind",
                "contiguous sibling range selector.kind must be "
                "'contiguous-sibling-range'",
            )
        return cls(
            start_xpath=_absolute_xpath(
                payload["start_xpath"], "selector.start_xpath"
            ),
            end_xpath=_absolute_xpath(payload["end_xpath"], "selector.end_xpath"),
            include_start=_bool(payload["include_start"], "selector.include_start"),
            include_end=_bool(payload["include_end"], "selector.include_end"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "start_xpath": self.start_xpath,
            "end_xpath": self.end_xpath,
            "include_start": self.include_start,
            "include_end": self.include_end,
        }


RegionSelector = ContainerSelector | ContiguousSiblingRangeSelector


def _selector_from_dict(payload: Mapping[str, Any]) -> RegionSelector:
    if not isinstance(payload, Mapping):
        _fail("invalid-object", "region.selector must be a JSON object")
    kind = payload.get("kind")
    if kind == "container":
        return ContainerSelector.from_dict(payload)
    if kind == "contiguous-sibling-range":
        return ContiguousSiblingRangeSelector.from_dict(payload)
    _fail(
        "invalid-region-kind",
        "region.selector.kind must be 'container' or 'contiguous-sibling-range'",
    )


@dataclass(frozen=True)
class ExtractionRegion:
    region_id: str
    source_context_class: str
    selector: RegionSelector

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExtractionRegion":
        _exact_fields(
            payload,
            required={"region_id", "source_context_class", "selector"},
            label="extraction region",
        )
        region_id = _nonempty_text(payload["region_id"], "region.region_id")
        if _REGION_ID_RE.fullmatch(region_id) is None:
            _fail("invalid-region-id", "region.region_id has invalid syntax")
        context = _nonempty_text(
            payload["source_context_class"], "region.source_context_class"
        )
        if context not in SOURCE_CONTEXT_CLASSES:
            _fail(
                "invalid-source-context-class",
                "region.source_context_class must be one of "
                f"{sorted(SOURCE_CONTEXT_CLASSES)}",
            )
        return cls(
            region_id=region_id,
            source_context_class=context,
            selector=_selector_from_dict(payload["selector"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "source_context_class": self.source_context_class,
            "selector": self.selector.to_dict(),
        }


@dataclass(frozen=True)
class SourceRowExtractionSpec:
    version: int
    scope_slug: str
    selected_xhtml: SelectedXhtml
    namespaces: tuple[tuple[str, str], ...]
    regions: tuple[ExtractionRegion, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceRowExtractionSpec":
        _exact_fields(
            payload,
            required={"version", "scope_slug", "selected_xhtml", "regions"},
            optional={"namespaces"},
            label="source-row extraction spec",
        )
        version = payload["version"]
        if type(version) is not int or version != EXTRACTION_SPEC_VERSION:
            _fail(
                "unsupported-extraction-spec-version",
                f"source-row extraction spec.version must be {EXTRACTION_SPEC_VERSION}",
            )
        scope_slug = _nonempty_text(payload["scope_slug"], "spec.scope_slug")
        if _SCOPE_SLUG_RE.fullmatch(scope_slug) is None:
            _fail("invalid-scope-slug", "spec.scope_slug has invalid syntax")

        raw_namespaces = payload.get("namespaces", {})
        if not isinstance(raw_namespaces, Mapping):
            _fail("invalid-object", "spec.namespaces must be a JSON object")
        namespaces: list[tuple[str, str]] = []
        for raw_prefix, raw_uri in raw_namespaces.items():
            prefix = _nonempty_text(raw_prefix, "spec.namespaces prefix")
            uri = _nonempty_text(raw_uri, f"spec.namespaces.{prefix}")
            if _NAMESPACE_PREFIX_RE.fullmatch(prefix) is None or prefix in {"xml", "xmlns"}:
                _fail("invalid-namespace-prefix", f"invalid namespace prefix: {prefix}")
            if prefix == "xhtml" and uri != XHTML_NAMESPACE:
                _fail(
                    "invalid-xhtml-namespace",
                    f"xhtml prefix must resolve to {XHTML_NAMESPACE}",
                )
            namespaces.append((prefix, uri))
        namespaces.sort()

        raw_regions = payload["regions"]
        if not isinstance(raw_regions, list) or not raw_regions:
            _fail("invalid-regions", "spec.regions must be a non-empty JSON array")
        regions = tuple(ExtractionRegion.from_dict(item) for item in raw_regions)
        region_ids = [item.region_id for item in regions]
        if len(region_ids) != len(set(region_ids)):
            _fail("duplicate-region-id", "spec.regions contains duplicate region_id")
        return cls(
            version=version,
            scope_slug=scope_slug,
            selected_xhtml=SelectedXhtml.from_dict(payload["selected_xhtml"]),
            namespaces=tuple(namespaces),
            regions=regions,
        )

    @property
    def digest(self) -> str:
        return canonical_json_sha256(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scope_slug": self.scope_slug,
            "selected_xhtml": self.selected_xhtml.to_dict(),
            "namespaces": dict(self.namespaces),
            "regions": [item.to_dict() for item in self.regions],
        }


@dataclass(frozen=True)
class SourceCandidate:
    candidate_id: str
    candidate_hash: str
    region_id: str
    element_kind: str
    canonical_xpath: str
    bounded_source_text: str
    source_context_class: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceCandidate":
        _exact_fields(
            payload,
            required={
                "candidate_id",
                "candidate_hash",
                "region_id",
                "element_kind",
                "canonical_xpath",
                "bounded_source_text",
                "source_context_class",
            },
            label="source candidate",
        )
        result = cls(
            candidate_id=_nonempty_text(payload["candidate_id"], "candidate.candidate_id"),
            candidate_hash=_sha256(payload["candidate_hash"], "candidate.candidate_hash"),
            region_id=_nonempty_text(payload["region_id"], "candidate.region_id"),
            element_kind=_nonempty_text(payload["element_kind"], "candidate.element_kind"),
            canonical_xpath=_absolute_xpath(
                payload["canonical_xpath"], "candidate.canonical_xpath"
            ),
            bounded_source_text=_nonempty_text(
                payload["bounded_source_text"], "candidate.bounded_source_text"
            ),
            source_context_class=_nonempty_text(
                payload["source_context_class"], "candidate.source_context_class"
            ),
        )
        result.validate_shape()
        return result

    def validate_shape(self) -> None:
        if _CANDIDATE_ID_RE.fullmatch(self.candidate_id) is None:
            _fail("invalid-candidate-id", "candidate.candidate_id has invalid syntax")
        if _REGION_ID_RE.fullmatch(self.region_id) is None:
            _fail("invalid-region-id", "candidate.region_id has invalid syntax")
        if self.element_kind not in CANDIDATE_ELEMENT_KINDS:
            _fail(
                "invalid-candidate-element-kind",
                f"candidate.element_kind must be one of {sorted(CANDIDATE_ELEMENT_KINDS)}",
            )
        if self.source_context_class not in SOURCE_CONTEXT_CLASSES:
            _fail(
                "invalid-source-context-class",
                "candidate.source_context_class must be one of "
                f"{sorted(SOURCE_CONTEXT_CLASSES)}",
            )
        if normalize_bounded_source_text(self.bounded_source_text) != self.bounded_source_text:
            _fail(
                "non-normalized-candidate-text",
                "candidate.bounded_source_text must already be normalized",
            )

    def to_dict(self) -> dict[str, str]:
        self.validate_shape()
        return {
            "candidate_id": self.candidate_id,
            "candidate_hash": self.candidate_hash,
            "region_id": self.region_id,
            "element_kind": self.element_kind,
            "canonical_xpath": self.canonical_xpath,
            "bounded_source_text": self.bounded_source_text,
            "source_context_class": self.source_context_class,
        }


@dataclass(frozen=True)
class SourceRowBaseline:
    version: int
    scope_slug: str
    selected_xhtml: SelectedXhtml
    extraction_spec_sha256: str
    candidate_set_sha256: str
    candidates: tuple[SourceCandidate, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceRowBaseline":
        _exact_fields(
            payload,
            required={
                "version",
                "scope_slug",
                "selected_xhtml",
                "extraction_spec_sha256",
                "candidate_set_sha256",
                "candidates",
            },
            label="source-row baseline",
        )
        version = payload["version"]
        if type(version) is not int or version != SOURCE_ROW_BASELINE_VERSION:
            _fail(
                "unsupported-source-row-baseline-version",
                f"source-row baseline.version must be {SOURCE_ROW_BASELINE_VERSION}",
            )
        raw_candidates = payload["candidates"]
        if not isinstance(raw_candidates, list) or not raw_candidates:
            _fail("invalid-candidates", "baseline.candidates must be a non-empty array")
        result = cls(
            version=version,
            scope_slug=_nonempty_text(payload["scope_slug"], "baseline.scope_slug"),
            selected_xhtml=SelectedXhtml.from_dict(payload["selected_xhtml"]),
            extraction_spec_sha256=_sha256(
                payload["extraction_spec_sha256"], "baseline.extraction_spec_sha256"
            ),
            candidate_set_sha256=_sha256(
                payload["candidate_set_sha256"], "baseline.candidate_set_sha256"
            ),
            candidates=tuple(SourceCandidate.from_dict(item) for item in raw_candidates),
        )
        result.validate_shape()
        return result

    @property
    def digest(self) -> str:
        return canonical_json_sha256(self.to_dict())

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def validate_shape(self) -> None:
        if _SCOPE_SLUG_RE.fullmatch(self.scope_slug) is None:
            _fail("invalid-scope-slug", "baseline.scope_slug has invalid syntax")
        candidate_ids = [item.candidate_id for item in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            _fail("duplicate-candidate-id", "baseline contains duplicate candidate_id")
        locators = [item.canonical_xpath for item in self.candidates]
        if len(locators) != len(set(locators)):
            _fail(
                "duplicate-candidate-locator",
                "baseline contains duplicate candidate canonical_xpath",
            )
        for candidate in self.candidates:
            expected_hash = _source_candidate_hash(
                scope_slug=self.scope_slug,
                selected_xhtml=self.selected_xhtml,
                region_id=candidate.region_id,
                element_kind=candidate.element_kind,
                canonical_xpath=candidate.canonical_xpath,
                bounded_source_text=candidate.bounded_source_text,
                source_context_class=candidate.source_context_class,
            )
            if candidate.candidate_hash != expected_hash:
                _fail(
                    "candidate-hash-mismatch",
                    f"candidate hash does not match content: {candidate.candidate_id}",
                )
            expected_id = _candidate_id(expected_hash)
            if candidate.candidate_id != expected_id:
                _fail(
                    "candidate-id-mismatch",
                    f"candidate id does not match content hash: {candidate.candidate_id}",
                )
        expected_set_digest = canonical_json_sha256(
            [item.to_dict() for item in self.candidates]
        )
        if self.candidate_set_sha256 != expected_set_digest:
            _fail(
                "candidate-set-digest-mismatch",
                "baseline.candidate_set_sha256 does not match candidates",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scope_slug": self.scope_slug,
            "selected_xhtml": self.selected_xhtml.to_dict(),
            "extraction_spec_sha256": self.extraction_spec_sha256,
            "candidate_set_sha256": self.candidate_set_sha256,
            "candidates": [item.to_dict() for item in self.candidates],
        }


@dataclass(frozen=True)
class SourceRowCandidateMapping:
    source_row_id: str
    source_path: str
    source_locator: str
    bounded_source_text: str
    source_context_class: str
    candidate_id: str | None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceRowCandidateMapping":
        _exact_fields(
            payload,
            required={
                "source_row_id",
                "source_path",
                "source_locator",
                "bounded_source_text",
                "source_context_class",
                "candidate_id",
            },
            label="source-row candidate mapping",
        )
        candidate_id = payload["candidate_id"]
        if candidate_id is not None:
            candidate_id = _nonempty_text(candidate_id, "mapping.candidate_id")
            if _CANDIDATE_ID_RE.fullmatch(candidate_id) is None:
                _fail("invalid-candidate-id", "mapping.candidate_id has invalid syntax")
        result = cls(
            source_row_id=_nonempty_text(payload["source_row_id"], "mapping.source_row_id"),
            source_path=_relative_path(payload["source_path"], "mapping.source_path"),
            source_locator=_nonempty_text(payload["source_locator"], "mapping.source_locator"),
            bounded_source_text=_nonempty_text(
                payload["bounded_source_text"], "mapping.bounded_source_text"
            ),
            source_context_class=_nonempty_text(
                payload["source_context_class"], "mapping.source_context_class"
            ),
            candidate_id=candidate_id,
        )
        if _SOURCE_ROW_ID_RE.fullmatch(result.source_row_id) is None:
            _fail("invalid-source-row-id", "mapping.source_row_id must name one SRC-* row")
        if result.source_context_class not in SOURCE_CONTEXT_CLASSES:
            _fail(
                "invalid-source-context-class",
                "mapping.source_context_class must be one of "
                f"{sorted(SOURCE_CONTEXT_CLASSES)}",
            )
        return result

    def validate_shape(self) -> None:
        if _SOURCE_ROW_ID_RE.fullmatch(self.source_row_id) is None:
            _fail("invalid-source-row-id", "mapping.source_row_id must name one SRC-* row")
        _relative_path(self.source_path, "mapping.source_path")
        _nonempty_text(self.source_locator, "mapping.source_locator")
        _nonempty_text(self.bounded_source_text, "mapping.bounded_source_text")
        if self.source_context_class not in SOURCE_CONTEXT_CLASSES:
            _fail(
                "invalid-source-context-class",
                "mapping.source_context_class must be one of "
                f"{sorted(SOURCE_CONTEXT_CLASSES)}",
            )
        if self.candidate_id is not None and _CANDIDATE_ID_RE.fullmatch(self.candidate_id) is None:
            _fail("invalid-candidate-id", "mapping.candidate_id has invalid syntax")

    def to_dict(self) -> dict[str, Any]:
        self.validate_shape()
        return {
            "source_row_id": self.source_row_id,
            "source_path": self.source_path,
            "source_locator": self.source_locator,
            "bounded_source_text": self.bounded_source_text,
            "source_context_class": self.source_context_class,
            "candidate_id": self.candidate_id,
        }


@dataclass(frozen=True)
class CandidateCoverageResult:
    candidate_count: int
    mapped_xhtml_source_row_count: int
    non_xhtml_source_row_count: int


@dataclass(frozen=True)
class SourceRowCompletenessResult:
    source_row_extraction_spec_digest: str
    source_row_baseline_digest: str
    candidate_set_digest: str
    candidate_count: int
    mapped_xhtml_source_row_count: int
    non_xhtml_source_row_count: int


def _absolute_xpath(value: Any, label: str) -> str:
    xpath = _nonempty_text(value, label)
    if not xpath.startswith("/") or xpath.startswith("//") or xpath.endswith("/"):
        _fail(
            "invalid-xpath",
            f"{label} must be an absolute child-axis XPath",
        )
    parts = xpath[1:].split("/")
    if not parts or any(_XPATH_STEP_RE.fullmatch(part) is None for part in parts):
        _fail(
            "unsupported-xpath",
            f"{label} supports only QName or wildcard child steps with numeric positions",
        )
    return xpath


def _load_json_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        _fail("artifact-read-failed", f"cannot read {label} {path}: {exc}")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        _fail("invalid-json", f"cannot parse {label} {path}: {exc}")
    if not isinstance(payload, Mapping):
        _fail("invalid-object", f"{label} must contain a JSON object")
    return payload


def load_extraction_spec(path: Path) -> SourceRowExtractionSpec:
    return SourceRowExtractionSpec.from_dict(
        _load_json_object(path, "source-row extraction spec")
    )


def load_source_row_baseline(path: Path) -> SourceRowBaseline:
    return SourceRowBaseline.from_dict(_load_json_object(path, "source-row baseline"))


def write_source_row_baseline(path: Path, baseline: SourceRowBaseline) -> None:
    baseline.validate_shape()
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(baseline.to_dict(), ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _resolve_selected_xhtml(repo_root: Path, selected: SelectedXhtml) -> Path:
    root = repo_root.resolve()
    candidate = (root / Path(*PurePosixPath(selected.relative_path).parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        _fail(
            "selected-xhtml-escapes-repository",
            f"selected XHTML resolves outside repository: {selected.relative_path}",
        )
    if not candidate.is_file():
        _fail("selected-xhtml-missing", f"selected XHTML is missing: {selected.relative_path}")
    try:
        content = candidate.read_bytes()
    except OSError as exc:
        _fail("selected-xhtml-read-failed", f"cannot read selected XHTML: {exc}")
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != selected.sha256:
        _fail(
            "stale-selected-xhtml",
            f"selected XHTML SHA-256 changed: expected={selected.sha256}, actual={actual_sha256}",
        )
    return candidate


def _parse_xhtml(path: Path) -> ET.Element:
    try:
        content = path.read_bytes()
    except OSError as exc:
        _fail("selected-xhtml-read-failed", f"cannot read selected XHTML: {exc}")
    upper = content.upper()
    if b"<!ENTITY" in upper:
        _fail(
            "unsafe-xhtml-declaration",
            "selected XHTML must not contain ENTITY declarations",
        )
    if b"<!DOCTYPE" in upper:
        declarations = list(_DOCTYPE_RE.finditer(content))
        if len(declarations) != 1 or upper.count(b"<!DOCTYPE") != 1:
            _fail(
                "unsafe-xhtml-declaration",
                "selected XHTML contains an unsupported DOCTYPE declaration",
            )
        declaration = declarations[0].group(0)
        if b"[" in declaration:
            _fail(
                "unsafe-xhtml-declaration",
                "selected XHTML must not contain an internal DTD subset",
            )
        content = content[: declarations[0].start()] + content[declarations[0].end() :]
    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        _fail("invalid-xhtml", f"selected XHTML is not well-formed XML: {exc}")


def _element_children(element: ET.Element) -> list[ET.Element]:
    return [child for child in list(element) if isinstance(child.tag, str)]


def _expanded_name(node_test: str, namespaces: Mapping[str, str]) -> str | None:
    if node_test == "*":
        return None
    if ":" not in node_test:
        return node_test
    prefix, local_name = node_test.split(":", 1)
    if prefix not in namespaces:
        _fail("unknown-xpath-namespace", f"XPath uses undeclared namespace prefix: {prefix}")
    return f"{{{namespaces[prefix]}}}{local_name}"


def _step_matches(element: ET.Element, node_test: str, namespaces: Mapping[str, str]) -> bool:
    expanded = _expanded_name(node_test, namespaces)
    return expanded is None or element.tag == expanded


def _select_xpath(
    root: ET.Element,
    xpath: str,
    namespaces: Mapping[str, str],
) -> list[ET.Element]:
    steps = xpath[1:].split("/")
    first = _XPATH_STEP_RE.fullmatch(steps[0])
    assert first is not None
    first_position = int(first.group("position")) if first.group("position") else None
    if not _step_matches(root, first.group("node"), namespaces) or first_position not in {None, 1}:
        return []
    selected = [root]
    for raw_step in steps[1:]:
        match = _XPATH_STEP_RE.fullmatch(raw_step)
        assert match is not None
        node_test = match.group("node")
        position = int(match.group("position")) if match.group("position") else None
        next_selected: list[ET.Element] = []
        for parent in selected:
            matching = [
                child
                for child in _element_children(parent)
                if _step_matches(child, node_test, namespaces)
            ]
            if position is None:
                next_selected.extend(matching)
            elif position <= len(matching):
                next_selected.append(matching[position - 1])
        selected = next_selected
    return selected


def _select_one(
    root: ET.Element,
    xpath: str,
    namespaces: Mapping[str, str],
    label: str,
) -> ET.Element:
    selected = _select_xpath(root, xpath, namespaces)
    if len(selected) != 1:
        _fail(
            "xpath-cardinality-mismatch",
            f"{label} must select exactly one element, selected={len(selected)}: {xpath}",
        )
    return selected[0]


def _region_roots(
    root: ET.Element,
    region: ExtractionRegion,
    namespaces: Mapping[str, str],
    parent_map: Mapping[ET.Element, ET.Element],
) -> tuple[ET.Element, ...]:
    selector = region.selector
    if isinstance(selector, ContainerSelector):
        return (
            _select_one(
                root,
                selector.container_xpath,
                namespaces,
                f"region {region.region_id} container",
            ),
        )

    start = _select_one(
        root,
        selector.start_xpath,
        namespaces,
        f"region {region.region_id} start",
    )
    end = _select_one(
        root,
        selector.end_xpath,
        namespaces,
        f"region {region.region_id} end",
    )
    start_parent = parent_map.get(start)
    end_parent = parent_map.get(end)
    if start_parent is None or start_parent is not end_parent:
        _fail(
            "non-sibling-region-boundary",
            f"region {region.region_id} boundaries must be children of the same parent",
        )
    siblings = _element_children(start_parent)
    start_index = siblings.index(start)
    end_index = siblings.index(end)
    if start_index > end_index:
        _fail(
            "reversed-region-boundary",
            f"region {region.region_id} start occurs after end",
        )
    lower = start_index if selector.include_start else start_index + 1
    upper = end_index + 1 if selector.include_end else end_index
    selected = tuple(siblings[lower:upper])
    if not selected:
        _fail("empty-region", f"region {region.region_id} selects no elements")
    return selected


def _local_name(element: ET.Element) -> str:
    tag = element.tag
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _is_annotation_metadata_subtree(element: ET.Element) -> bool:
    """Return true only for the two exact LibreOffice annotation markers."""

    if element.attrib.get("title") == "annotation":
        return True
    class_value = element.attrib.get("class", "")
    class_tokens = {
        token
        for token in _ASCII_CLASS_WHITESPACE_RE.split(class_value)
        if token
    }
    return "annotation_style_by_filter" in class_tokens


def _collect_visible_text(
    element: ET.Element,
    *,
    exclude_nested_candidates: bool,
) -> list[str]:
    if _is_annotation_metadata_subtree(element):
        return []
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in _element_children(element):
        child_is_nested_candidate = (
            exclude_nested_candidates and _local_name(child).lower() in {"li", "tr"}
        )
        if not child_is_nested_candidate and not _is_annotation_metadata_subtree(child):
            parts.extend(
                _collect_visible_text(
                    child,
                    exclude_nested_candidates=exclude_nested_candidates,
                )
            )
        if child.tail:
            parts.append(child.tail)
    return parts


def _full_element_text(element: ET.Element) -> str:
    return normalize_bounded_source_text(
        " ".join(
            _collect_visible_text(
                element,
                exclude_nested_candidates=False,
            )
        )
    )


def _li_owned_text(element: ET.Element) -> str:
    return normalize_bounded_source_text(
        " ".join(
            _collect_visible_text(
                element,
                exclude_nested_candidates=True,
            )
        )
    )


def _candidate_nodes(region_root: ET.Element) -> list[tuple[ET.Element, str, str]]:
    result: list[tuple[ET.Element, str, str]] = []

    def visit(element: ET.Element, *, inside_li: bool = False) -> None:
        if _is_annotation_metadata_subtree(element):
            return
        kind = _local_name(element).lower()
        if kind == "tr":
            text = _full_element_text(element)
            if text:
                result.append((element, kind, text))
            return
        if kind == "li":
            text = _li_owned_text(element)
            if text:
                result.append((element, kind, text))
            for child in _element_children(element):
                visit(child, inside_li=True)
            return
        if kind in {"p", "h1", "h2", "h3", "h4", "h5", "h6"}:
            if not inside_li:
                text = _full_element_text(element)
                if text:
                    result.append((element, kind, text))
            return
        for child in _element_children(element):
            visit(child, inside_li=inside_li)

    visit(region_root)
    return result


def _canonical_xpath(
    element: ET.Element,
    root: ET.Element,
    parent_map: Mapping[ET.Element, ET.Element],
) -> str:
    positions: list[int] = []
    current = element
    while current is not root:
        parent = parent_map.get(current)
        if parent is None:
            _fail("detached-candidate", "candidate is not attached to selected XHTML root")
        positions.append(_element_children(parent).index(current) + 1)
        current = parent
    return "/*" + "".join(f"/*[{position}]" for position in reversed(positions))


def _resolve_candidate_element(
    *,
    root: ET.Element,
    parent_map: Mapping[ET.Element, ET.Element],
    locator: str,
) -> ResolvedXhtmlCandidate:
    element = _select_one(
        root,
        locator,
        {"xhtml": XHTML_NAMESPACE},
        "candidate canonical_xpath",
    )
    resolved_locator = _canonical_xpath(element, root, parent_map)
    if locator != resolved_locator:
        _fail(
            "non-canonical-candidate-locator",
            "candidate locator must use the canonical wildcard/element-sibling form: "
            + resolved_locator,
        )

    ancestors: list[str] = []
    inside_annotation_metadata = _is_annotation_metadata_subtree(element)
    current = parent_map.get(element)
    while current is not None:
        ancestors.append(_local_name(current).lower())
        inside_annotation_metadata = (
            inside_annotation_metadata or _is_annotation_metadata_subtree(current)
        )
        current = parent_map.get(current)

    element_kind = _local_name(element).lower()
    if inside_annotation_metadata:
        _fail(
            "candidate-is-annotation-metadata",
            "annotation metadata subtrees do not contain source candidates",
        )
    if "tr" in ancestors:
        _fail(
            "candidate-owned-by-table-row",
            "a containing tr owns all visible descendant text; bind the tr candidate",
        )
    if element_kind == "tr":
        bounded_text = _full_element_text(element)
    elif element_kind == "li":
        bounded_text = _li_owned_text(element)
    elif element_kind in {"p", "h1", "h2", "h3", "h4", "h5", "h6"}:
        if "li" in ancestors:
            _fail(
                "candidate-owned-by-list-item",
                "a containing li owns standalone descendant text; bind the li candidate",
            )
        bounded_text = _full_element_text(element)
    else:
        _fail(
            "locator-is-not-candidate-element",
            "candidate locator must select tr, li, standalone p or h1-h6",
        )
    if not bounded_text:
        _fail(
            "empty-candidate-text",
            "candidate locator selects an element without visible candidate text",
        )
    return ResolvedXhtmlCandidate(
        canonical_xpath=resolved_locator,
        element_kind=element_kind,
        bounded_source_text=bounded_text,
    )


def resolve_xhtml_candidates_at_locators(
    *,
    xhtml_path: Path,
    canonical_xpaths: Sequence[str],
) -> dict[str, ResolvedXhtmlCandidate]:
    """Resolve many baseline-visible candidates while parsing the XHTML only once."""

    if xhtml_path.suffix.lower() != ".xhtml":
        _fail(
            "candidate-source-is-not-xhtml",
            "candidate-bound source rows require an .xhtml source",
        )
    locators = tuple(
        _absolute_xpath(value, "candidate canonical_xpath")
        for value in canonical_xpaths
    )
    if len(locators) != len(set(locators)):
        _fail(
            "duplicate-candidate-locator",
            "candidate locator batch must not contain duplicates",
        )
    root = _parse_xhtml(xhtml_path)
    parent_map = {
        child: parent
        for parent in root.iter()
        if isinstance(parent.tag, str)
        for child in _element_children(parent)
    }
    return {
        locator: _resolve_candidate_element(
            root=root,
            parent_map=parent_map,
            locator=locator,
        )
        for locator in locators
    }


def resolve_xhtml_candidate_at_locator(
    *,
    xhtml_path: Path,
    canonical_xpath: str,
) -> ResolvedXhtmlCandidate:
    """Resolve one candidate with the exact text-ownership rules used by baseline v1."""

    resolved = resolve_xhtml_candidates_at_locators(
        xhtml_path=xhtml_path,
        canonical_xpaths=(canonical_xpath,),
    )
    return next(iter(resolved.values()))


def resolve_xhtml_table_cells_at_locators(
    *,
    xhtml_path: Path,
    canonical_xpaths: Sequence[str],
) -> dict[str, tuple[ResolvedXhtmlTableCell, ...]]:
    """Resolve physical table cells for canonical ``tr`` candidates.

    Column indices deliberately follow direct XML child order.  ``rowspan`` and
    ``colspan`` are presentation metadata and must not silently shift the source
    column semantics declared by a package-specific extraction contract.
    """

    if xhtml_path.suffix.lower() != ".xhtml":
        _fail(
            "table-cell-source-is-not-xhtml",
            "table-cell evidence requires an .xhtml source",
        )
    locators = tuple(
        _absolute_xpath(value, "table row canonical_xpath")
        for value in canonical_xpaths
    )
    if len(locators) != len(set(locators)):
        _fail(
            "duplicate-table-row-locator",
            "table row locator batch must not contain duplicates",
        )
    root = _parse_xhtml(xhtml_path)
    parent_map = {
        child: parent
        for parent in root.iter()
        if isinstance(parent.tag, str)
        for child in _element_children(parent)
    }
    result: dict[str, tuple[ResolvedXhtmlTableCell, ...]] = {}
    for locator in locators:
        candidate = _resolve_candidate_element(
            root=root,
            parent_map=parent_map,
            locator=locator,
        )
        if candidate.element_kind != "tr":
            _fail(
                "table-cell-locator-is-not-row",
                f"table-cell locator must select a tr candidate: {locator}",
            )
        row = _select_one(
            root,
            locator,
            {"xhtml": XHTML_NAMESPACE},
            "table row canonical_xpath",
        )
        cells: list[ResolvedXhtmlTableCell] = []
        for index, cell in enumerate(_element_children(row), start=1):
            kind = _local_name(cell).lower()
            if kind not in {"th", "td"}:
                _fail(
                    "table-row-has-non-cell-child",
                    f"table row has direct non-cell child {kind}: {locator}",
                )
            cells.append(
                ResolvedXhtmlTableCell(
                    physical_column_index=index,
                    canonical_xpath=_canonical_xpath(cell, root, parent_map),
                    element_kind=kind,
                    bounded_source_text=_full_element_text(cell),
                )
            )
        if not cells:
            _fail(
                "table-row-has-no-cells",
                f"table row has no direct th/td cells: {locator}",
            )
        result[locator] = tuple(cells)
    return result


def resolve_xhtml_structural_contexts_at_locators(
    *,
    xhtml_path: Path,
    canonical_xpaths: Sequence[str],
) -> dict[str, ResolvedXhtmlStructuralContext]:
    """Resolve heading, table and list context for canonical source candidates.

    The section path follows visible standalone ``h1``-``h6`` elements that
    precede the candidate in XHTML document order.  Heading levels replace the
    active heading at the same or a deeper level.  Headings owned by a table
    row or list item are deliberately excluded, matching baseline candidate
    ownership instead of treating cell/list formatting as document sections.
    """

    if xhtml_path.suffix.lower() != ".xhtml":
        _fail(
            "structural-context-source-is-not-xhtml",
            "structural context requires an .xhtml source",
        )
    locators = tuple(
        _absolute_xpath(value, "structural context canonical_xpath")
        for value in canonical_xpaths
    )
    if len(locators) != len(set(locators)):
        _fail(
            "duplicate-structural-context-locator",
            "structural context locator batch must not contain duplicates",
        )
    root = _parse_xhtml(xhtml_path)
    parent_map = {
        child: parent
        for parent in root.iter()
        if isinstance(parent.tag, str)
        for child in _element_children(parent)
    }
    target_by_element: dict[ET.Element, str] = {}
    for locator in locators:
        _resolve_candidate_element(
            root=root,
            parent_map=parent_map,
            locator=locator,
        )
        element = _select_one(
            root,
            locator,
            {"xhtml": XHTML_NAMESPACE},
            "structural context canonical_xpath",
        )
        target_by_element[element] = locator

    if not target_by_element:
        return {}

    ordered_elements = [
        element for element in root.iter() if isinstance(element.tag, str)
    ]
    positions = {element: index for index, element in enumerate(ordered_elements)}
    last_target_position = max(positions[element] for element in target_by_element)
    active_headings: dict[int, ResolvedXhtmlSectionHeading] = {}
    result: dict[str, ResolvedXhtmlStructuralContext] = {}

    for element in ordered_elements[: last_target_position + 1]:
        locator = target_by_element.get(element)
        if locator is not None:
            ancestors: list[ResolvedXhtmlStructuralAncestor] = []
            current = parent_map.get(element)
            while current is not None:
                kind = _local_name(current).lower()
                if kind in {"table", "ol", "ul", "li"}:
                    ancestors.append(
                        ResolvedXhtmlStructuralAncestor(
                            canonical_xpath=_canonical_xpath(
                                current,
                                root,
                                parent_map,
                            ),
                            element_kind=kind,
                        )
                    )
                current = parent_map.get(current)
            ancestors.reverse()
            table_ancestry = tuple(
                item for item in ancestors if item.element_kind == "table"
            )
            list_ancestry = tuple(
                item for item in ancestors if item.element_kind in {"ol", "ul", "li"}
            )
            headings = tuple(
                active_headings[level] for level in sorted(active_headings)
            )
            result[locator] = ResolvedXhtmlStructuralContext(
                canonical_xpath=locator,
                section_path=tuple(item.bounded_source_text for item in headings),
                section_headings=headings,
                table_identity=(
                    table_ancestry[-1].canonical_xpath if table_ancestry else None
                ),
                table_ancestry=table_ancestry,
                list_ancestry=list_ancestry,
            )

        kind = _local_name(element).lower()
        if kind not in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            continue
        current = element
        owned_or_hidden = False
        while current is not None:
            current_kind = _local_name(current).lower()
            if _is_annotation_metadata_subtree(current) or (
                current is not element and current_kind in {"tr", "li"}
            ):
                owned_or_hidden = True
                break
            current = parent_map.get(current)
        if owned_or_hidden:
            continue
        heading_text = _full_element_text(element)
        if not heading_text:
            _fail(
                "empty-structural-heading",
                "a visible standalone heading preceding a candidate has no text: "
                + _canonical_xpath(element, root, parent_map),
            )
        level = int(kind[1])
        for stale_level in tuple(
            value for value in active_headings if value >= level
        ):
            del active_headings[stale_level]
        active_headings[level] = ResolvedXhtmlSectionHeading(
            level=level,
            canonical_xpath=_canonical_xpath(element, root, parent_map),
            bounded_source_text=heading_text,
        )

    if set(result) != set(locators):
        _fail(
            "structural-context-resolution-incomplete",
            "not every canonical candidate received structural context",
        )
    return {locator: result[locator] for locator in locators}


def resolve_xhtml_structural_context_at_locator(
    *,
    xhtml_path: Path,
    canonical_xpath: str,
) -> ResolvedXhtmlStructuralContext:
    """Resolve document structure for one canonical XHTML candidate."""

    resolved = resolve_xhtml_structural_contexts_at_locators(
        xhtml_path=xhtml_path,
        canonical_xpaths=(canonical_xpath,),
    )
    return next(iter(resolved.values()))


def _source_candidate_hash(
    *,
    scope_slug: str,
    selected_xhtml: SelectedXhtml,
    region_id: str,
    element_kind: str,
    canonical_xpath: str,
    bounded_source_text: str,
    source_context_class: str,
) -> str:
    return canonical_json_sha256(
        {
            "scope_slug": scope_slug,
            "source_relative_path": selected_xhtml.relative_path,
            "region_id": region_id,
            "element_kind": element_kind,
            "canonical_xpath": canonical_xpath,
            "bounded_source_text": bounded_source_text,
            "source_context_class": source_context_class,
        }
    )


def _candidate_id(candidate_hash: str) -> str:
    return f"SRC-CAND-{candidate_hash[:24]}"


def build_source_row_baseline(
    *,
    repo_root: Path,
    spec: SourceRowExtractionSpec,
) -> SourceRowBaseline:
    """Re-extract every deterministic requirement candidate from the selected XHTML."""

    spec = SourceRowExtractionSpec.from_dict(spec.to_dict())
    selected_path = _resolve_selected_xhtml(repo_root, spec.selected_xhtml)
    root = _parse_xhtml(selected_path)
    parent_map = {
        child: parent
        for parent in root.iter()
        if isinstance(parent.tag, str)
        for child in _element_children(parent)
    }
    document_order = {
        element: index
        for index, element in enumerate(root.iter())
        if isinstance(element.tag, str)
    }
    namespaces = dict(spec.namespaces)
    namespaces.setdefault("xhtml", XHTML_NAMESPACE)

    extracted: list[tuple[int, ExtractionRegion, ET.Element, str, str]] = []
    seen_elements: dict[ET.Element, str] = {}
    for region in spec.regions:
        region_candidate_count = 0
        for region_root in _region_roots(root, region, namespaces, parent_map):
            for element, element_kind, bounded_text in _candidate_nodes(region_root):
                previous_region = seen_elements.get(element)
                if previous_region is not None:
                    _fail(
                        "overlapping-extraction-regions",
                        f"candidate belongs to both {previous_region} and {region.region_id}",
                    )
                seen_elements[element] = region.region_id
                extracted.append(
                    (
                        document_order[element],
                        region,
                        element,
                        element_kind,
                        bounded_text,
                    )
                )
                region_candidate_count += 1
        if region_candidate_count == 0:
            _fail(
                "empty-region-candidates",
                f"region {region.region_id} contains no requirement candidates",
            )

    extracted.sort(key=lambda item: item[0])
    candidates: list[SourceCandidate] = []
    for _, region, element, element_kind, bounded_text in extracted:
        locator = _canonical_xpath(element, root, parent_map)
        candidate_hash = _source_candidate_hash(
            scope_slug=spec.scope_slug,
            selected_xhtml=spec.selected_xhtml,
            region_id=region.region_id,
            element_kind=element_kind,
            canonical_xpath=locator,
            bounded_source_text=bounded_text,
            source_context_class=region.source_context_class,
        )
        candidates.append(
            SourceCandidate(
                candidate_id=_candidate_id(candidate_hash),
                candidate_hash=candidate_hash,
                region_id=region.region_id,
                element_kind=element_kind,
                canonical_xpath=locator,
                bounded_source_text=bounded_text,
                source_context_class=region.source_context_class,
            )
        )
    if not candidates:
        _fail("empty-candidate-set", "extraction spec produced no source candidates")

    baseline = SourceRowBaseline(
        version=SOURCE_ROW_BASELINE_VERSION,
        scope_slug=spec.scope_slug,
        selected_xhtml=spec.selected_xhtml,
        extraction_spec_sha256=spec.digest,
        candidate_set_sha256=canonical_json_sha256(
            [item.to_dict() for item in candidates]
        ),
        candidates=tuple(candidates),
    )
    baseline.validate_shape()
    return baseline


def validate_source_row_baseline(
    *,
    repo_root: Path,
    spec: SourceRowExtractionSpec,
    baseline: SourceRowBaseline,
) -> SourceRowBaseline:
    """Re-extract current XHTML and require byte-semantic equality with the stored baseline."""

    if baseline.scope_slug != spec.scope_slug:
        _fail("baseline-scope-mismatch", "baseline.scope_slug does not match spec.scope_slug")
    if baseline.selected_xhtml != spec.selected_xhtml:
        _fail(
            "baseline-source-binding-mismatch",
            "baseline.selected_xhtml does not match spec.selected_xhtml",
        )
    if baseline.extraction_spec_sha256 != spec.digest:
        _fail(
            "stale-extraction-spec",
            "baseline.extraction_spec_sha256 does not match current extraction spec",
        )
    current = build_source_row_baseline(repo_root=repo_root, spec=spec)
    if baseline.to_dict() != current.to_dict():
        _fail(
            "stale-source-row-baseline",
            "stored baseline does not match deterministic extraction from current XHTML",
        )
    return current


def _coerce_mapping(
    value: SourceRowCandidateMapping | Mapping[str, Any],
) -> SourceRowCandidateMapping:
    if isinstance(value, SourceRowCandidateMapping):
        value.validate_shape()
        return value
    return SourceRowCandidateMapping.from_dict(value)


def validate_candidate_coverage(
    *,
    baseline: SourceRowBaseline,
    source_row_mappings: Sequence[SourceRowCandidateMapping | Mapping[str, Any]],
) -> CandidateCoverageResult:
    """Require a one-to-one mapping from selected-XHTML SourceRows to candidates."""

    baseline.validate_shape()
    mappings = tuple(_coerce_mapping(item) for item in source_row_mappings)
    source_row_ids = [item.source_row_id for item in mappings]
    if len(source_row_ids) != len(set(source_row_ids)):
        _fail("duplicate-source-row-mapping", "source_row_mappings repeats source_row_id")

    candidates = {item.candidate_id: item for item in baseline.candidates}
    mapped_candidate_ids: set[str] = set()
    mapped_xhtml_count = 0
    non_xhtml_count = 0
    for mapping in mappings:
        is_selected_xhtml = mapping.source_path == baseline.selected_xhtml.relative_path
        if not is_selected_xhtml:
            non_xhtml_count += 1
            if mapping.candidate_id is not None:
                _fail(
                    "non-xhtml-candidate-mapping",
                    f"non-XHTML source row must have candidate_id=null: {mapping.source_row_id}",
                )
            continue

        mapped_xhtml_count += 1
        if mapping.candidate_id is None:
            _fail(
                "xhtml-source-row-candidate-missing",
                f"selected-XHTML source row has no candidate_id: {mapping.source_row_id}",
            )
        candidate = candidates.get(mapping.candidate_id)
        if candidate is None:
            _fail(
                "unknown-candidate-mapping",
                f"source row maps unknown candidate_id: {mapping.candidate_id}",
            )
        if mapping.candidate_id in mapped_candidate_ids:
            _fail(
                "duplicate-candidate-mapping",
                f"candidate is mapped by more than one source row: {mapping.candidate_id}",
            )
        if mapping.source_locator != candidate.canonical_xpath:
            _fail(
                "source-row-candidate-locator-mismatch",
                f"source row locator differs from candidate: {mapping.source_row_id}",
            )
        if mapping.bounded_source_text != candidate.bounded_source_text:
            _fail(
                "source-row-candidate-text-mismatch",
                f"source row bounded text differs from candidate: {mapping.source_row_id}",
            )
        if mapping.source_context_class != candidate.source_context_class:
            _fail(
                "source-row-candidate-context-mismatch",
                f"source row context differs from candidate: {mapping.source_row_id}",
            )
        mapped_candidate_ids.add(mapping.candidate_id)

    missing = sorted(set(candidates) - mapped_candidate_ids)
    if missing:
        _fail(
            "unmapped-source-candidates",
            f"baseline candidates are not mapped by SourceRows: {missing}",
        )
    return CandidateCoverageResult(
        candidate_count=baseline.candidate_count,
        mapped_xhtml_source_row_count=mapped_xhtml_count,
        non_xhtml_source_row_count=non_xhtml_count,
    )


def validate_source_row_completeness(
    *,
    repo_root: Path,
    extraction_spec_path: Path,
    baseline_path: Path,
    source_row_mappings: Sequence[SourceRowCandidateMapping | Mapping[str, Any]],
) -> SourceRowCompletenessResult:
    """Validate spec, current XHTML, stored baseline and exact SourceRow coverage."""

    spec = load_extraction_spec(extraction_spec_path)
    baseline = load_source_row_baseline(baseline_path)
    current = validate_source_row_baseline(
        repo_root=repo_root,
        spec=spec,
        baseline=baseline,
    )
    coverage = validate_candidate_coverage(
        baseline=current,
        source_row_mappings=source_row_mappings,
    )
    return SourceRowCompletenessResult(
        source_row_extraction_spec_digest=spec.digest,
        source_row_baseline_digest=current.digest,
        candidate_set_digest=current.candidate_set_sha256,
        candidate_count=coverage.candidate_count,
        mapped_xhtml_source_row_count=coverage.mapped_xhtml_source_row_count,
        non_xhtml_source_row_count=coverage.non_xhtml_source_row_count,
    )
