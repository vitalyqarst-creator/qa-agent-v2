"""Strict, non-semantic registry for bounded FT scopes.

The registry only points at package-local evidence and records structural scope
boundaries.  It deliberately has no field capable of carrying requirement text,
atomic statements, obligations, test steps, or expected results; those remain the
responsibility of the source-assertion and prepared-package contracts.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from test_case_agent.review_cycle.source_row_baseline import (
    ContainerSelector,
    ContiguousSiblingRangeSelector,
    SourceRowBaselineValidationError,
)


REGISTRY_VERSION = 1
EXECUTION_PROFILES = frozenset({"lean-production", "standard-production"})
ROW_ROLES = frozenset({"context", "testable"})

_SCOPE_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
_TC_PREFIX_RE = re.compile(r"[A-Z0-9][A-Z0-9-]{1,30}")
_REFERENCE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REQUIREMENT_PREFIX_RE = re.compile(r"[A-Z][A-Z0-9_-]*")
_REQUIREMENT_CODE_RE = re.compile(
    r"(?P<prefix>[A-Z][A-Z0-9_-]*) (?P<number>[1-9][0-9]*)"
)


class ScopeRegistryError(ValueError):
    """A fail-closed registry validation or resolution error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise ScopeRegistryError(code, message)


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
    if value != value.strip():
        _fail("non-canonical-text", f"{label} must not have surrounding whitespace")
    return value


def _positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value < 1:
        _fail("invalid-positive-integer", f"{label} must be a positive integer")
    return value


def _relative_package_path(value: Any, label: str) -> str:
    text = _nonempty_text(value, label)
    if "\\" in text or text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        _fail(
            "invalid-package-path",
            f"{label} must be a package-relative POSIX path",
        )
    parsed = PurePosixPath(text)
    if parsed.as_posix() != text or any(
        part in {"", ".", ".."} for part in parsed.parts
    ):
        _fail(
            "invalid-package-path",
            f"{label} must be normalized and must not contain traversal",
        )
    return text


def _identifier(value: Any, label: str) -> str:
    text = _nonempty_text(value, label)
    if _REFERENCE_ID_RE.fullmatch(text) is None:
        _fail("invalid-identifier", f"{label} is not a portable identifier")
    return text


def _unique_sorted_texts(
    value: Any,
    label: str,
    *,
    validator: Any,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        _fail("invalid-array", f"{label} must be a JSON array")
    items = tuple(validator(item, f"{label}[{index}]") for index, item in enumerate(value))
    folded = [item.casefold() for item in items]
    if len(folded) != len(set(folded)):
        _fail("duplicate-value", f"{label} contains duplicate values")
    return tuple(sorted(items, key=lambda item: (item.casefold(), item)))


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class ScopeSourceSet:
    docx: str
    xhtml: str
    pdf: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeSourceSet":
        _exact_fields(
            payload,
            required={"docx", "xhtml"},
            optional={"pdf"},
            label="source_set",
        )
        docx = _relative_package_path(payload["docx"], "source_set.docx")
        xhtml = _relative_package_path(payload["xhtml"], "source_set.xhtml")
        pdf = (
            _relative_package_path(payload["pdf"], "source_set.pdf")
            if "pdf" in payload
            else None
        )
        _require_suffix(docx, ".docx", "source_set.docx")
        _require_suffix(xhtml, ".xhtml", "source_set.xhtml")
        if pdf is not None:
            _require_suffix(pdf, ".pdf", "source_set.pdf")
        return cls(docx=docx, xhtml=xhtml, pdf=pdf)

    def to_dict(self) -> dict[str, str]:
        result = {"docx": self.docx, "xhtml": self.xhtml}
        if self.pdf is not None:
            result["pdf"] = self.pdf
        return result


@dataclass(frozen=True)
class ScopeRowRange:
    role: str
    start: int
    end: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, label: str) -> "ScopeRowRange":
        _exact_fields(
            payload,
            required={"role", "start", "end"},
            label=label,
        )
        role = _nonempty_text(payload["role"], f"{label}.role")
        if role not in ROW_ROLES:
            _fail(
                "invalid-row-role",
                f"{label}.role must be one of {sorted(ROW_ROLES)}",
            )
        start = _positive_int(payload["start"], f"{label}.start")
        end = _positive_int(payload["end"], f"{label}.end")
        if start > end:
            _fail("invalid-row-range", f"{label}.start must not exceed end")
        return cls(role=role, start=start, end=end)

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "start": self.start, "end": self.end}


@dataclass(frozen=True)
class ScopeCrossReference:
    reference_id: str
    xpath: str

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        label: str,
    ) -> "ScopeCrossReference":
        _exact_fields(
            payload,
            required={"reference_id", "xpath"},
            label=label,
        )
        reference_id = _identifier(payload["reference_id"], f"{label}.reference_id")
        try:
            xpath = ContiguousSiblingRangeSelector.from_dict(
                {
                    "kind": "contiguous-sibling-range",
                    "start_xpath": payload["xpath"],
                    "end_xpath": payload["xpath"],
                    "include_start": True,
                    "include_end": True,
                }
            ).start_xpath
        except SourceRowBaselineValidationError as error:
            _fail("invalid-cross-reference-xpath", str(error))
        return cls(reference_id=reference_id, xpath=xpath)

    def to_dict(self) -> dict[str, str]:
        return {"reference_id": self.reference_id, "xpath": self.xpath}


@dataclass(frozen=True)
class ScopeBoundary:
    container_xpath: str
    row_ranges: tuple[ScopeRowRange, ...]
    cross_references: tuple[ScopeCrossReference, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeBoundary":
        _exact_fields(
            payload,
            required={"container_xpath", "row_ranges"},
            optional={"cross_references"},
            label="boundary",
        )
        try:
            xpath = ContainerSelector.from_dict(
                {"kind": "container", "container_xpath": payload["container_xpath"]}
            ).container_xpath
        except SourceRowBaselineValidationError as error:
            _fail("invalid-container-xpath", str(error))
        raw_ranges = payload["row_ranges"]
        if not isinstance(raw_ranges, list) or not raw_ranges:
            _fail("invalid-array", "boundary.row_ranges must be a non-empty array")
        ranges = tuple(
            sorted(
                (
                    ScopeRowRange.from_dict(item, label=f"boundary.row_ranges[{index}]")
                    for index, item in enumerate(raw_ranges)
                ),
                key=lambda item: (item.start, item.end, item.role),
            )
        )
        if not any(item.role == "testable" for item in ranges):
            _fail(
                "missing-testable-range",
                "boundary.row_ranges must contain at least one testable range",
            )
        _reject_overlapping_row_ranges(ranges)
        raw_cross_references = payload.get("cross_references", [])
        if not isinstance(raw_cross_references, list):
            _fail("invalid-array", "boundary.cross_references must be a JSON array")
        cross_references = tuple(
            sorted(
                (
                    ScopeCrossReference.from_dict(
                        item,
                        label=f"boundary.cross_references[{index}]",
                    )
                    for index, item in enumerate(raw_cross_references)
                ),
                key=lambda item: item.reference_id,
            )
        )
        reference_ids = [item.reference_id.casefold() for item in cross_references]
        reference_xpaths = [item.xpath for item in cross_references]
        if len(reference_ids) != len(set(reference_ids)):
            _fail(
                "duplicate-cross-reference-id",
                "boundary.cross_references repeats reference_id",
            )
        if len(reference_xpaths) != len(set(reference_xpaths)):
            _fail(
                "duplicate-cross-reference-xpath",
                "boundary.cross_references repeats xpath",
            )
        return cls(
            container_xpath=xpath,
            row_ranges=ranges,
            cross_references=cross_references,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "container_xpath": self.container_xpath,
            "row_ranges": [item.to_dict() for item in self.row_ranges],
            "cross_references": [item.to_dict() for item in self.cross_references],
        }


@dataclass(frozen=True)
class RequirementRange:
    prefix: str
    start: int
    end: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, label: str) -> "RequirementRange":
        _exact_fields(
            payload,
            required={"prefix", "start", "end"},
            label=label,
        )
        prefix = _nonempty_text(payload["prefix"], f"{label}.prefix")
        if _REQUIREMENT_PREFIX_RE.fullmatch(prefix) is None:
            _fail(
                "invalid-requirement-prefix",
                f"{label}.prefix must be an uppercase portable code prefix",
            )
        start = _positive_int(payload["start"], f"{label}.start")
        end = _positive_int(payload["end"], f"{label}.end")
        if start > end:
            _fail("invalid-requirement-range", f"{label}.start must not exceed end")
        return cls(prefix=prefix, start=start, end=end)

    def contains(self, prefix: str, number: int) -> bool:
        return self.prefix == prefix and self.start <= number <= self.end

    def to_dict(self) -> dict[str, Any]:
        return {"prefix": self.prefix, "start": self.start, "end": self.end}


@dataclass(frozen=True)
class RequirementGuard:
    allowed_ranges: tuple[RequirementRange, ...]
    excluded_codes: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RequirementGuard":
        _exact_fields(
            payload,
            required={"allowed_ranges", "excluded_codes"},
            label="requirement_guard",
        )
        raw_ranges = payload["allowed_ranges"]
        if not isinstance(raw_ranges, list) or not raw_ranges:
            _fail(
                "invalid-array",
                "requirement_guard.allowed_ranges must be a non-empty array",
            )
        ranges = tuple(
            sorted(
                (
                    RequirementRange.from_dict(
                        item,
                        label=f"requirement_guard.allowed_ranges[{index}]",
                    )
                    for index, item in enumerate(raw_ranges)
                ),
                key=lambda item: (item.prefix, item.start, item.end),
            )
        )
        _reject_overlapping_requirement_ranges(ranges)
        excluded = _unique_sorted_texts(
            payload["excluded_codes"],
            "requirement_guard.excluded_codes",
            validator=_requirement_code,
        )
        for code in excluded:
            match = _REQUIREMENT_CODE_RE.fullmatch(code)
            assert match is not None
            prefix = match.group("prefix")
            number = int(match.group("number"))
            if not any(item.contains(prefix, number) for item in ranges):
                _fail(
                    "excluded-code-outside-guard",
                    f"excluded requirement code {code!r} is outside allowed_ranges",
                )
        return cls(allowed_ranges=ranges, excluded_codes=excluded)

    def allows(self, code: str) -> bool:
        match = _REQUIREMENT_CODE_RE.fullmatch(code)
        if match is None or code in self.excluded_codes:
            return False
        prefix = match.group("prefix")
        number = int(match.group("number"))
        return any(item.contains(prefix, number) for item in self.allowed_ranges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_ranges": [item.to_dict() for item in self.allowed_ranges],
            "excluded_codes": list(self.excluded_codes),
        }


@dataclass(frozen=True)
class ScopeDefinition:
    scope_id: str
    tc_prefix: str
    source_set: ScopeSourceSet
    boundary: ScopeBoundary
    requirement_guard: RequirementGuard
    reference_paths: tuple[str, ...]
    fixture_ids: tuple[str, ...]
    gap_ids: tuple[str, ...]
    execution_profile: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeDefinition":
        if isinstance(payload, Mapping) and "tc_prefix" not in payload:
            _fail(
                "missing-tc-prefix",
                "scope.tc_prefix is required; migrate the registry by assigning "
                "one stable uppercase prefix to this scope",
            )
        _exact_fields(
            payload,
            required={
                "scope_id",
                "tc_prefix",
                "source_set",
                "boundary",
                "requirement_guard",
                "reference_paths",
                "fixture_ids",
                "gap_ids",
                "execution_profile",
            },
            label="scope",
        )
        scope_id = _nonempty_text(payload["scope_id"], "scope.scope_id")
        if _SCOPE_ID_RE.fullmatch(scope_id) is None:
            _fail("invalid-scope-id", "scope.scope_id must be a lowercase slug")
        tc_prefix = _nonempty_text(payload["tc_prefix"], "scope.tc_prefix")
        if _TC_PREFIX_RE.fullmatch(tc_prefix) is None or tc_prefix.startswith("TC-"):
            _fail(
                "invalid-tc-prefix",
                "scope.tc_prefix must match [A-Z0-9][A-Z0-9-]{1,30} and must "
                "omit the TC- namespace added by the ID generator",
            )
        reference_paths = _unique_sorted_texts(
            payload["reference_paths"],
            "scope.reference_paths",
            validator=_relative_package_path,
        )
        fixture_ids = _unique_sorted_texts(
            payload["fixture_ids"],
            "scope.fixture_ids",
            validator=_identifier,
        )
        gap_ids = _unique_sorted_texts(
            payload["gap_ids"],
            "scope.gap_ids",
            validator=_identifier,
        )
        if set(fixture_ids).intersection(gap_ids):
            _fail(
                "identifier-namespace-collision",
                "scope.fixture_ids and scope.gap_ids must not share identifiers",
            )
        execution_profile = _nonempty_text(
            payload["execution_profile"], "scope.execution_profile"
        )
        if execution_profile not in EXECUTION_PROFILES:
            _fail(
                "invalid-execution-profile",
                f"scope.execution_profile must be one of {sorted(EXECUTION_PROFILES)}",
            )
        return cls(
            scope_id=scope_id,
            tc_prefix=tc_prefix,
            source_set=ScopeSourceSet.from_dict(payload["source_set"]),
            boundary=ScopeBoundary.from_dict(payload["boundary"]),
            requirement_guard=RequirementGuard.from_dict(payload["requirement_guard"]),
            reference_paths=reference_paths,
            fixture_ids=fixture_ids,
            gap_ids=gap_ids,
            execution_profile=execution_profile,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "tc_prefix": self.tc_prefix,
            "source_set": self.source_set.to_dict(),
            "boundary": self.boundary.to_dict(),
            "requirement_guard": self.requirement_guard.to_dict(),
            "reference_paths": list(self.reference_paths),
            "fixture_ids": list(self.fixture_ids),
            "gap_ids": list(self.gap_ids),
            "execution_profile": self.execution_profile,
        }


@dataclass(frozen=True)
class ScopeRegistry:
    version: int
    scopes: tuple[ScopeDefinition, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeRegistry":
        _exact_fields(payload, required={"version", "scopes"}, label="registry")
        if type(payload["version"]) is not int or payload["version"] != REGISTRY_VERSION:
            _fail(
                "unsupported-registry-version",
                f"registry.version must equal {REGISTRY_VERSION}",
            )
        raw_scopes = payload["scopes"]
        if not isinstance(raw_scopes, list) or not raw_scopes:
            _fail("invalid-array", "registry.scopes must be a non-empty array")
        scopes = tuple(
            sorted(
                (ScopeDefinition.from_dict(item) for item in raw_scopes),
                key=lambda item: item.scope_id,
            )
        )
        scope_ids = [item.scope_id for item in scopes]
        if len(scope_ids) != len(set(scope_ids)):
            _fail("duplicate-scope-id", "registry.scopes contains duplicate scope_id")
        return cls(version=REGISTRY_VERSION, scopes=scopes)

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical_json_bytes(self.to_dict())).hexdigest()

    def get(self, scope_id: str) -> ScopeDefinition:
        for scope in self.scopes:
            if scope.scope_id == scope_id:
                return scope
        raise KeyError(scope_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scopes": [scope.to_dict() for scope in self.scopes],
        }


@dataclass(frozen=True)
class ResolvedSourceSet:
    docx: Path
    xhtml: Path
    pdf: Path | None


@dataclass(frozen=True)
class ResolvedScope:
    definition: ScopeDefinition
    source_set: ResolvedSourceSet
    reference_paths: tuple[Path, ...]


@dataclass(frozen=True)
class ResolvedScopeRegistry:
    registry: ScopeRegistry
    package_root: Path
    scopes: tuple[ResolvedScope, ...]

    @property
    def digest(self) -> str:
        return self.registry.digest

    def get(self, scope_id: str) -> ResolvedScope:
        for scope in self.scopes:
            if scope.definition.scope_id == scope_id:
                return scope
        raise KeyError(scope_id)


def load_scope_registry(path: str | Path) -> ScopeRegistry:
    """Load a strict UTF-8 JSON registry, rejecting duplicate object keys."""

    registry_path = Path(path)
    try:
        raw = registry_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        _fail("registry-read-failed", f"cannot read {registry_path}: {error}")
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_json_object)
    except ScopeRegistryError:
        raise
    except json.JSONDecodeError as error:
        _fail("invalid-json", f"cannot parse {registry_path}: {error}")
    if not isinstance(payload, Mapping):
        _fail("invalid-object", "registry root must be a JSON object")
    return ScopeRegistry.from_dict(payload)


def resolve_scope_registry(
    registry: ScopeRegistry | Mapping[str, Any],
    ft_package_root: str | Path,
    *,
    scope_id: str | None = None,
) -> ResolvedScopeRegistry:
    """Resolve selected paths and prove they remain inside the FT package.

    The complete registry is always parsed with its closed schema before any path
    resolution.  When ``scope_id`` is supplied, only that scope's files are
    resolved, so an unrelated scope's missing local input cannot block the
    requested compilation.
    """

    parsed = registry if isinstance(registry, ScopeRegistry) else ScopeRegistry.from_dict(registry)
    root = Path(ft_package_root)
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        _fail("invalid-package-root", f"cannot resolve FT package root {root}: {error}")
    if not resolved_root.is_dir():
        _fail("invalid-package-root", f"FT package root is not a directory: {root}")

    if scope_id is None:
        scopes_to_resolve = parsed.scopes
    else:
        try:
            scopes_to_resolve = (parsed.get(scope_id),)
        except KeyError:
            _fail("unknown-scope-id", f"registry has no scope_id {scope_id!r}")

    resolved_scopes: list[ResolvedScope] = []
    for scope in scopes_to_resolve:
        sources = scope.source_set
        docx = _resolve_package_file(resolved_root, sources.docx, "source_set.docx")
        xhtml = _resolve_package_file(resolved_root, sources.xhtml, "source_set.xhtml")
        pdf = (
            _resolve_package_file(resolved_root, sources.pdf, "source_set.pdf")
            if sources.pdf is not None
            else None
        )
        references = tuple(
            _resolve_package_file(
                resolved_root,
                relative_path,
                f"scope[{scope.scope_id}].reference_paths",
            )
            for relative_path in scope.reference_paths
        )
        resolved_scopes.append(
            ResolvedScope(
                definition=scope,
                source_set=ResolvedSourceSet(docx=docx, xhtml=xhtml, pdf=pdf),
                reference_paths=references,
            )
        )
    return ResolvedScopeRegistry(
        registry=parsed,
        package_root=resolved_root,
        scopes=tuple(resolved_scopes),
    )


def load_and_resolve_scope_registry(
    registry_path: str | Path,
    ft_package_root: str | Path,
    *,
    scope_id: str | None = None,
) -> ResolvedScopeRegistry:
    return resolve_scope_registry(
        load_scope_registry(registry_path),
        ft_package_root,
        scope_id=scope_id,
    )


def _require_suffix(value: str, suffix: str, label: str) -> None:
    if not value.casefold().endswith(suffix):
        _fail("invalid-source-extension", f"{label} must end with {suffix}")


def _requirement_code(value: Any, label: str) -> str:
    text = _nonempty_text(value, label)
    if _REQUIREMENT_CODE_RE.fullmatch(text) is None:
        _fail(
            "invalid-requirement-code",
            f"{label} must have the form PREFIX positive-integer",
        )
    return text


def _reject_overlapping_row_ranges(ranges: Sequence[ScopeRowRange]) -> None:
    for previous, current in zip(ranges, ranges[1:]):
        if current.start <= previous.end:
            _fail(
                "overlapping-row-ranges",
                "boundary.row_ranges must be unique and non-overlapping: "
                f"{previous.to_dict()} conflicts with {current.to_dict()}",
            )


def _reject_overlapping_requirement_ranges(
    ranges: Sequence[RequirementRange],
) -> None:
    previous_by_prefix: dict[str, RequirementRange] = {}
    for current in ranges:
        previous = previous_by_prefix.get(current.prefix)
        if previous is not None and current.start <= previous.end:
            _fail(
                "overlapping-requirement-ranges",
                "requirement_guard.allowed_ranges must be unique and non-overlapping: "
                f"{previous.to_dict()} conflicts with {current.to_dict()}",
            )
        previous_by_prefix[current.prefix] = current


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate-json-key", f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _resolve_package_file(root: Path, relative_path: str, label: str) -> Path:
    parts = PurePosixPath(relative_path).parts
    candidate = root.joinpath(*parts).resolve(strict=False)
    if not candidate.is_relative_to(root):
        _fail(
            "package-path-escape",
            f"{label} resolves outside FT package: {relative_path}",
        )
    if not candidate.exists():
        _fail("missing-package-file", f"{label} does not exist: {relative_path}")
    if not candidate.is_file():
        _fail("package-path-not-file", f"{label} is not a file: {relative_path}")
    return candidate


__all__ = [
    "EXECUTION_PROFILES",
    "REGISTRY_VERSION",
    "ROW_ROLES",
    "RequirementGuard",
    "RequirementRange",
    "ResolvedScope",
    "ResolvedScopeRegistry",
    "ResolvedSourceSet",
    "ScopeBoundary",
    "ScopeCrossReference",
    "ScopeDefinition",
    "ScopeRegistry",
    "ScopeRegistryError",
    "ScopeRowRange",
    "ScopeSourceSet",
    "load_and_resolve_scope_registry",
    "load_scope_registry",
    "resolve_scope_registry",
]
