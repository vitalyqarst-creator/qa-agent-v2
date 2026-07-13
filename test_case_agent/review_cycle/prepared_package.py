from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from test_case_agent.review_cycle.runtime import (
    StageRuntimeError,
    repository_relative,
    resolve_repository_path,
    sha256_path,
    utc_timestamp,
    write_json_atomic,
)


PACKAGE_VERSION = 5
SUPPORTED_PACKAGE_VERSIONS = {1, 2, 3, 4, PACKAGE_VERSION}
FAST_EXECUTION_PROFILE = "simple-field-property"
STANDARD_EXECUTION_PROFILE = "standard-required"
FAST_EVIDENCE_MAX_BYTES = 32768
STANDARD_ROUTING_EVIDENCE_MAX_BYTES = 49152
PACKAGE_KINDS = {"source-evidence", "atomic-obligations", "stage-instructions"}
COVERAGE_STATUSES = {"testable", "gap", "unclear", "not-applicable"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
SHA256 = re.compile(r"[0-9a-f]{64}")
OBLIGATION_ID = re.compile(r"(?:ATOM|OBL)-[A-Za-z0-9._-]+")
ATOM_ID = re.compile(r"ATOM-[A-Za-z0-9._-]+")
GAP_ID = re.compile(r"GAP-[A-Za-z0-9._-]+")
DICT_ID = re.compile(r"DICT-[A-Za-z0-9._-]+")
REFERENCE_SELECTOR = re.compile(
    r"(?i)(?:(?:SRC|GAP|RISK|DICT|ATOM)-[A-Za-z0-9._-]+|(?:GSR|BSR|DIT)\s+\d+(?:\.\d+)*)"
)
DICTIONARY_CLAIM = re.compile(
    r"(?i)\b(?:справочник\w*|dictionary|reference\s+list|fixed\s+list|closed\s+list)\b"
)
REFERENCE_BOUNDARY_CHARS = "A-Za-z0-9._-"


def _exact_fields(payload: Mapping[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, Mapping):
        raise StageRuntimeError(f"{label} must be a JSON object")
    missing = sorted(expected - set(payload))
    unknown = sorted(set(payload) - expected)
    if missing or unknown:
        raise StageRuntimeError(
            f"invalid {label} fields: missing={missing or 'none'}, unknown={unknown or 'none'}"
        )


def _identifier(value: Any, field_name: str, pattern: re.Pattern[str] = IDENTIFIER) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise StageRuntimeError(f"{field_name} must be a stable identifier")
    return value


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageRuntimeError(f"{field_name} must be non-empty text")
    return value.strip()


def _path(value: Any, field_name: str) -> str:
    value = _text(value, field_name)
    if "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise StageRuntimeError(f"{field_name} must be repository-relative POSIX path")
    parsed = PurePosixPath(value)
    if parsed.as_posix() != value or any(part in {"", ".", ".."} for part in parsed.parts):
        raise StageRuntimeError(f"{field_name} must be normalized without traversal")
    return value


def _sha(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise StageRuntimeError(f"{field_name} must be lowercase SHA-256")
    return value


def _string_list(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise StageRuntimeError(f"{field_name} must be a JSON array")
    result = tuple(_text(item, f"{field_name}[]") for item in value)
    if not allow_empty and not result:
        raise StageRuntimeError(f"{field_name} must not be empty")
    if len(set(result)) != len(result):
        raise StageRuntimeError(f"{field_name} must not contain duplicates")
    return result


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _names_reference(text: str, reference: str) -> bool:
    return bool(
        re.search(
            rf"(?<![{REFERENCE_BOUNDARY_CHARS}]){re.escape(reference)}"
            rf"(?![{REFERENCE_BOUNDARY_CHARS}])",
            text,
        )
    )


def _selector_matches(line: str, selector: str) -> bool:
    if REFERENCE_SELECTOR.fullmatch(selector):
        return _names_reference(line, selector)
    return selector in line


@dataclass(frozen=True)
class SourceRegistryEntry:
    path: str
    sha256: str
    role: str
    locator: str

    def validate(self) -> None:
        _path(self.path, "source.path")
        _sha(self.sha256, "source.sha256")
        _identifier(self.role, "source.role")
        _text(self.locator, "source.locator")

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "role": self.role, "locator": self.locator}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SourceRegistryEntry:
        _exact_fields(payload, {"path", "sha256", "role", "locator"}, "source registry entry")
        item = cls(**payload)
        item.validate()
        return item


@dataclass(frozen=True)
class PackageArtifact:
    path: str
    sha256: str
    kind: str
    bytes: int

    def validate(self) -> None:
        _path(self.path, "package_artifact.path")
        _sha(self.sha256, "package_artifact.sha256")
        if self.kind not in PACKAGE_KINDS:
            raise StageRuntimeError(f"unsupported package artifact kind: {self.kind}")
        if not isinstance(self.bytes, int) or isinstance(self.bytes, bool) or self.bytes < 0:
            raise StageRuntimeError("package_artifact.bytes must be a non-negative integer")

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "kind": self.kind, "bytes": self.bytes}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PackageArtifact:
        _exact_fields(payload, {"path", "sha256", "kind", "bytes"}, "package artifact")
        item = cls(**payload)
        item.validate()
        return item


@dataclass(frozen=True)
class PreparedGap:
    gap_id: str
    source_refs: tuple[str, ...]
    problem: str
    handling: str
    blocking: bool

    def validate(self) -> None:
        _identifier(self.gap_id, "gap_id", GAP_ID)
        if not self.source_refs:
            raise StageRuntimeError(f"{self.gap_id}.source_refs must not be empty")
        for value in self.source_refs:
            _text(value, f"{self.gap_id}.source_refs[]")
        _text(self.problem, f"{self.gap_id}.problem")
        _text(self.handling, f"{self.gap_id}.handling")
        if not isinstance(self.blocking, bool):
            raise StageRuntimeError(f"{self.gap_id}.blocking must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "source_refs": list(self.source_refs),
            "problem": self.problem,
            "handling": self.handling,
            "blocking": self.blocking,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PreparedGap:
        _exact_fields(payload, {"gap_id", "source_refs", "problem", "handling", "blocking"}, "gap")
        item = cls(
            gap_id=payload["gap_id"],
            source_refs=_string_list(payload["source_refs"], "gap.source_refs"),
            problem=payload["problem"],
            handling=payload["handling"],
            blocking=payload["blocking"],
        )
        item.validate()
        return item


@dataclass(frozen=True)
class PreparedObligation:
    obligation_id: str
    source_refs: tuple[str, ...]
    atomic_statement: str
    observable_oracle: str
    test_intent: str
    coverage_status: str
    gap_id: str
    dictionary_refs: tuple[str, ...]
    notes: str
    constraint_gap_ids: tuple[str, ...] = ()
    atom_id: str = ""
    planned_test_case_id: str = ""

    @property
    def traceability_atom_id(self) -> str:
        if self.atom_id:
            return self.atom_id
        if self.obligation_id.startswith("ATOM-"):
            return self.obligation_id
        return ""

    def validate(self, *, package_version: int = PACKAGE_VERSION) -> None:
        _identifier(self.obligation_id, "obligation_id", OBLIGATION_ID)
        if package_version >= 5:
            _identifier(
                self.traceability_atom_id,
                f"{self.obligation_id}.atom_id",
                ATOM_ID,
            )
        if not self.source_refs:
            raise StageRuntimeError(f"{self.obligation_id}.source_refs must not be empty")
        for value in self.source_refs:
            _text(value, f"{self.obligation_id}.source_refs[]")
        _text(self.atomic_statement, f"{self.obligation_id}.atomic_statement")
        _text(self.test_intent, f"{self.obligation_id}.test_intent")
        if self.coverage_status not in COVERAGE_STATUSES:
            raise StageRuntimeError(
                f"{self.obligation_id}.coverage_status must be one of {sorted(COVERAGE_STATUSES)}"
            )
        if self.coverage_status == "testable":
            _text(self.observable_oracle, f"{self.obligation_id}.observable_oracle")
            if self.gap_id:
                raise StageRuntimeError(f"{self.obligation_id} testable obligation cannot link a gap")
        elif self.coverage_status in {"gap", "unclear"}:
            _identifier(self.gap_id, f"{self.obligation_id}.gap_id", GAP_ID)
        elif self.gap_id:
            raise StageRuntimeError(f"{self.obligation_id} not-applicable obligation cannot link a gap")
        for value in self.dictionary_refs:
            _identifier(value, f"{self.obligation_id}.dictionary_refs[]")
        for value in self.constraint_gap_ids:
            _identifier(value, f"{self.obligation_id}.constraint_gap_ids[]", GAP_ID)
        if len(self.constraint_gap_ids) != len(set(self.constraint_gap_ids)):
            raise StageRuntimeError(
                f"{self.obligation_id}.constraint_gap_ids must not contain duplicates"
            )
        if not isinstance(self.notes, str):
            raise StageRuntimeError(f"{self.obligation_id}.notes must be text")
        if self.planned_test_case_id:
            _identifier(
                self.planned_test_case_id,
                f"{self.obligation_id}.planned_test_case_id",
                re.compile(r"^TC-[A-Za-z0-9_.-]+$"),
            )

    def to_dict(
        self,
        *,
        include_constraints: bool = False,
        include_atom_id: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "obligation_id": self.obligation_id,
            "source_refs": list(self.source_refs),
            "atomic_statement": self.atomic_statement,
            "observable_oracle": self.observable_oracle,
            "test_intent": self.test_intent,
            "coverage_status": self.coverage_status,
            "gap_id": self.gap_id,
            "dictionary_refs": list(self.dictionary_refs),
            "notes": self.notes,
        }
        if include_constraints:
            payload["constraint_gap_ids"] = list(self.constraint_gap_ids)
        if include_atom_id:
            payload["atom_id"] = self.traceability_atom_id
        if self.planned_test_case_id:
            payload["planned_test_case_id"] = self.planned_test_case_id
        return payload

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any], *, package_version: int = PACKAGE_VERSION
    ) -> PreparedObligation:
        expected = {
            "obligation_id",
            "source_refs",
            "atomic_statement",
            "observable_oracle",
            "test_intent",
            "coverage_status",
            "gap_id",
            "dictionary_refs",
            "notes",
        }
        if package_version >= 4:
            expected.add("constraint_gap_ids")
        if package_version >= 5:
            expected.add("atom_id")
        if "planned_test_case_id" in payload:
            expected.add("planned_test_case_id")
        _exact_fields(payload, expected, "obligation")
        item = cls(
            obligation_id=payload["obligation_id"],
            source_refs=_string_list(payload["source_refs"], "obligation.source_refs"),
            atomic_statement=payload["atomic_statement"],
            observable_oracle=payload["observable_oracle"],
            test_intent=payload["test_intent"],
            coverage_status=payload["coverage_status"],
            gap_id=payload["gap_id"],
            dictionary_refs=_string_list(
                payload["dictionary_refs"], "obligation.dictionary_refs", allow_empty=True
            ),
            notes=payload["notes"],
            constraint_gap_ids=(
                _string_list(
                    payload["constraint_gap_ids"],
                    "obligation.constraint_gap_ids",
                    allow_empty=True,
                )
                if package_version >= 4
                else ()
            ),
            atom_id=(payload["atom_id"] if package_version >= 5 else ""),
            planned_test_case_id=payload.get("planned_test_case_id", ""),
        )
        item.validate(package_version=package_version)
        return item


@dataclass(frozen=True)
class PreparedObligationSet:
    package_version: int
    package_id: str
    obligations: tuple[PreparedObligation, ...]
    coverage_gaps: tuple[PreparedGap, ...]
    digest: str

    def _without_digest(self) -> dict[str, Any]:
        return {
            "package_version": self.package_version,
            "package_id": self.package_id,
            "obligations": [
                item.to_dict(
                    include_constraints=self.package_version >= 4,
                    include_atom_id=self.package_version >= 5,
                )
                for item in self.obligations
            ],
            "coverage_gaps": [item.to_dict() for item in self.coverage_gaps],
        }

    def validate(self, *, evidence_text: str | None = None) -> None:
        if self.package_version not in SUPPORTED_PACKAGE_VERSIONS:
            raise StageRuntimeError(
                f"package_version must be one of {sorted(SUPPORTED_PACKAGE_VERSIONS)}"
            )
        _identifier(self.package_id, "package_id")
        if not self.obligations:
            raise StageRuntimeError("obligations must not be empty")
        ids = [item.obligation_id for item in self.obligations]
        if len(ids) != len(set(ids)):
            raise StageRuntimeError("obligation ids must be unique")
        gap_ids = [item.gap_id for item in self.coverage_gaps]
        if len(gap_ids) != len(set(gap_ids)):
            raise StageRuntimeError("gap ids must be unique")
        for item in self.coverage_gaps:
            item.validate()
        known_gaps = set(gap_ids)
        linked_gaps: set[str] = set()
        all_refs: set[str] = set()
        for item in self.obligations:
            item.validate(package_version=self.package_version)
            all_refs.update(item.source_refs)
            if item.gap_id and item.gap_id not in known_gaps:
                raise StageRuntimeError(f"{item.obligation_id} references unknown gap {item.gap_id}")
            if item.gap_id:
                linked_gaps.add(item.gap_id)
            if self.package_version >= 4:
                for constraint_gap_id in item.constraint_gap_ids:
                    if constraint_gap_id not in known_gaps:
                        raise StageRuntimeError(
                            f"{item.obligation_id} references unknown constraint gap "
                            f"{constraint_gap_id}"
                        )
                    linked_gaps.add(constraint_gap_id)
            elif item.constraint_gap_ids:
                raise StageRuntimeError(
                    f"{item.obligation_id} constraint gaps require package_version 4"
                )
            if self.package_version >= 3:
                for value in item.dictionary_refs:
                    _identifier(value, f"{item.obligation_id}.dictionary_refs[]", DICT_ID)
                claim_text = " ".join((item.atomic_statement, item.observable_oracle))
                if (
                    item.coverage_status == "testable"
                    and DICTIONARY_CLAIM.search(claim_text)
                    and not item.dictionary_refs
                ):
                    raise StageRuntimeError(
                        f"{item.obligation_id} dictionary-backed testable obligation must link "
                        "dictionary_refs or be preserved as a gap"
                    )
                all_refs.update(item.dictionary_refs)
        for item in self.coverage_gaps:
            all_refs.update(item.source_refs)
        if self.package_version >= 3:
            orphan_gaps = sorted(known_gaps - linked_gaps)
            if orphan_gaps:
                raise StageRuntimeError(
                    "coverage gaps must be linked from obligations: " + ", ".join(orphan_gaps)
                )
        if evidence_text is not None:
            missing_refs = sorted(
                ref for ref in all_refs if not _names_reference(evidence_text, ref)
            )
            if missing_refs:
                raise StageRuntimeError(
                    "source evidence does not name obligation/gap refs: " + ", ".join(missing_refs)
                )
        _sha(self.digest, "obligation digest")
        if self.digest != _canonical_digest(self._without_digest()):
            raise StageRuntimeError("atomic obligations digest mismatch")

    def to_dict(self) -> dict[str, Any]:
        return {**self._without_digest(), "digest": self.digest}

    @classmethod
    def create(
        cls,
        *,
        package_id: str,
        obligations: Sequence[PreparedObligation],
        coverage_gaps: Sequence[PreparedGap],
        evidence_text: str | None = None,
    ) -> PreparedObligationSet:
        value = cls(PACKAGE_VERSION, package_id, tuple(obligations), tuple(coverage_gaps), "")
        completed = replace(value, digest=_canonical_digest(value._without_digest()))
        completed.validate(evidence_text=evidence_text)
        return completed

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        evidence_text: str | None = None,
    ) -> PreparedObligationSet:
        _exact_fields(
            payload,
            {"package_version", "package_id", "obligations", "coverage_gaps", "digest"},
            "atomic obligations",
        )
        if not isinstance(payload["obligations"], list) or not isinstance(payload["coverage_gaps"], list):
            raise StageRuntimeError("obligations and coverage_gaps must be JSON arrays")
        value = cls(
            package_version=payload["package_version"],
            package_id=payload["package_id"],
            obligations=tuple(
                PreparedObligation.from_dict(item, package_version=payload["package_version"])
                for item in payload["obligations"]
            ),
            coverage_gaps=tuple(PreparedGap.from_dict(item) for item in payload["coverage_gaps"]),
            digest=payload["digest"],
        )
        value.validate(evidence_text=evidence_text)
        return value


@dataclass(frozen=True)
class PreparedStagePackage:
    package_version: int
    package_id: str
    ft_slug: str
    scope_slug: str
    section_id: str
    created_at: str
    source_registry: tuple[SourceRegistryEntry, ...]
    package_artifacts: tuple[PackageArtifact, ...]
    execution_profile: str
    unsupported_dimensions: tuple[str, ...]
    forbidden_evidence_roots: tuple[str, ...]
    fallback_policy: str
    package_digest: str

    def _without_digest(self) -> dict[str, Any]:
        payload = {
            "package_version": self.package_version,
            "package_id": self.package_id,
            "ft_slug": self.ft_slug,
            "scope_slug": self.scope_slug,
            "section_id": self.section_id,
            "created_at": self.created_at,
            "source_registry": [item.to_dict() for item in self.source_registry],
            "package_artifacts": [item.to_dict() for item in self.package_artifacts],
        }
        if self.package_version >= 2:
            payload["execution_profile"] = self.execution_profile
            payload["unsupported_dimensions"] = list(self.unsupported_dimensions)
        payload["forbidden_evidence_roots"] = list(self.forbidden_evidence_roots)
        payload["fallback_policy"] = self.fallback_policy
        return payload

    def validate(self) -> None:
        if self.package_version not in SUPPORTED_PACKAGE_VERSIONS:
            raise StageRuntimeError(
                f"package_version must be one of {sorted(SUPPORTED_PACKAGE_VERSIONS)}"
            )
        for name in ("package_id", "ft_slug", "scope_slug"):
            _identifier(getattr(self, name), name)
        _text(self.section_id, "section_id")
        try:
            timestamp = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc:
            raise StageRuntimeError("created_at must be ISO-8601 timestamp") from exc
        if timestamp.tzinfo is None:
            raise StageRuntimeError("created_at must include timezone")
        if not self.source_registry:
            raise StageRuntimeError("source_registry must not be empty")
        source_paths = [item.path for item in self.source_registry]
        if len(source_paths) != len(set(source_paths)):
            raise StageRuntimeError("source_registry paths must be unique")
        for item in self.source_registry:
            item.validate()
        kinds = [item.kind for item in self.package_artifacts]
        if set(kinds) != PACKAGE_KINDS or len(kinds) != len(PACKAGE_KINDS):
            raise StageRuntimeError("package_artifacts must contain exactly the three package kinds")
        artifact_paths = [item.path for item in self.package_artifacts]
        if len(artifact_paths) != len(set(artifact_paths)):
            raise StageRuntimeError("package artifact paths must be unique")
        for item in self.package_artifacts:
            item.validate()
        if self.package_version >= 2:
            _identifier(self.execution_profile, "execution_profile")
            for dimension in self.unsupported_dimensions:
                _identifier(dimension, "unsupported_dimensions[]")
            if len(set(self.unsupported_dimensions)) != len(self.unsupported_dimensions):
                raise StageRuntimeError("unsupported_dimensions must not contain duplicates")
            if self.execution_profile == FAST_EXECUTION_PROFILE and self.unsupported_dimensions:
                raise StageRuntimeError(
                    "simple-field-property package cannot declare unsupported dimensions"
                )
            if self.package_version >= 3 and self.execution_profile == FAST_EXECUTION_PROFILE:
                has_docx_truth = any(
                    item.role == "source-of-truth"
                    and PurePosixPath(item.path).suffix.lower() == ".docx"
                    for item in self.source_registry
                )
                has_xhtml_machine_source = any(
                    item.role == "machine-readable"
                    and PurePosixPath(item.path).suffix.lower() in {".xhtml", ".html"}
                    for item in self.source_registry
                )
                if not has_docx_truth or not has_xhtml_machine_source:
                    raise StageRuntimeError(
                        f"package version {PACKAGE_VERSION} fast path requires DOCX source-of-truth and "
                        "XHTML machine-readable source registry entries"
                    )
        if not self.forbidden_evidence_roots:
            raise StageRuntimeError("forbidden_evidence_roots must not be empty")
        for root in self.forbidden_evidence_roots:
            _path(root, "forbidden_evidence_roots[]")
        if self.fallback_policy != "targeted-only":
            raise StageRuntimeError("fallback_policy must be targeted-only")
        _sha(self.package_digest, "package_digest")
        if self.package_digest != _canonical_digest(self._without_digest()):
            raise StageRuntimeError("stage package digest mismatch")

    def to_dict(self) -> dict[str, Any]:
        return {**self._without_digest(), "package_digest": self.package_digest}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PreparedStagePackage:
        expected = {
            "package_version",
            "package_id",
            "ft_slug",
            "scope_slug",
            "section_id",
            "created_at",
            "source_registry",
            "package_artifacts",
            "forbidden_evidence_roots",
            "fallback_policy",
            "package_digest",
        }
        package_version = payload.get("package_version")
        if isinstance(package_version, int) and package_version >= 2:
            expected.update({"execution_profile", "unsupported_dimensions"})
        _exact_fields(payload, expected, "prepared stage package")
        if not isinstance(payload["source_registry"], list) or not isinstance(payload["package_artifacts"], list):
            raise StageRuntimeError("source_registry and package_artifacts must be JSON arrays")
        value = cls(
            package_version=payload["package_version"],
            package_id=payload["package_id"],
            ft_slug=payload["ft_slug"],
            scope_slug=payload["scope_slug"],
            section_id=payload["section_id"],
            created_at=payload["created_at"],
            source_registry=tuple(SourceRegistryEntry.from_dict(item) for item in payload["source_registry"]),
            package_artifacts=tuple(PackageArtifact.from_dict(item) for item in payload["package_artifacts"]),
            execution_profile=(
                payload["execution_profile"] if isinstance(package_version, int) and package_version >= 2 else "legacy-unclassified"
            ),
            unsupported_dimensions=(
                _string_list(
                    payload["unsupported_dimensions"],
                    "unsupported_dimensions",
                    allow_empty=True,
                )
                if isinstance(package_version, int) and package_version >= 2
                else ("legacy-unclassified",)
            ),
            forbidden_evidence_roots=_string_list(
                payload["forbidden_evidence_roots"], "forbidden_evidence_roots"
            ),
            fallback_policy=payload["fallback_policy"],
            package_digest=payload["package_digest"],
        )
        value.validate()
        return value


@dataclass(frozen=True)
class EvidenceInput:
    path: Path
    title: str
    selectors: tuple[str, ...] = ()
    include_full: bool = False
    max_bytes: int = 8192


@dataclass(frozen=True)
class StageInstructionConfig:
    role: str
    scenario: str
    output_path: str
    attempt_root: str
    sandbox_policy: str
    timeout_seconds: int
    idle_timeout_seconds: int
    command_budget: int

    def validate(self) -> None:
        if self.role not in {"writer", "reviewer"}:
            raise StageRuntimeError("instruction role must be writer or reviewer")
        _identifier(self.scenario, "instruction scenario")
        _path(self.output_path, "instruction output_path")
        _path(self.attempt_root, "instruction attempt_root")
        allowed_sandboxes = (
            {"workspace_write", "read_only"} if self.role == "writer" else {"read_only"}
        )
        if self.sandbox_policy not in allowed_sandboxes:
            raise StageRuntimeError(
                f"{self.role} prepared stage requires sandbox_policy in "
                f"{sorted(allowed_sandboxes)}"
            )
        for name in ("timeout_seconds", "idle_timeout_seconds"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise StageRuntimeError(f"{name} must be a positive integer")
        if (
            not isinstance(self.command_budget, int)
            or isinstance(self.command_budget, bool)
            or self.command_budget < 0
        ):
            raise StageRuntimeError("command_budget must be a non-negative integer")
        if self.sandbox_policy == "workspace_write" and self.command_budget < 1:
            raise StageRuntimeError(
                "workspace_write prepared stage requires a positive command_budget"
            )
        if self.idle_timeout_seconds >= self.timeout_seconds:
            raise StageRuntimeError("idle_timeout_seconds must be lower than timeout_seconds")


class PreparedPackageBuilder:
    def __init__(self, repo_root: Path, *, max_package_bytes: int = 512000):
        self.repo_root = repo_root.resolve()
        if not isinstance(max_package_bytes, int) or isinstance(max_package_bytes, bool) or max_package_bytes < 1:
            raise StageRuntimeError("max_package_bytes must be a positive integer")
        self.max_package_bytes = max_package_bytes

    def build(
        self,
        *,
        output_root: Path,
        package_id: str,
        ft_slug: str,
        scope_slug: str,
        section_id: str,
        source_registry: Sequence[tuple[Path, str, str]],
        evidence_inputs: Sequence[EvidenceInput],
        obligations: PreparedObligationSet,
        instructions: StageInstructionConfig,
        execution_profile: str,
        unsupported_dimensions: Sequence[str],
        forbidden_evidence_roots: Sequence[str],
    ) -> PreparedStagePackage:
        _identifier(package_id, "package_id")
        _identifier(ft_slug, "ft_slug")
        _identifier(scope_slug, "scope_slug")
        _text(section_id, "section_id")
        instructions.validate()
        _identifier(execution_profile, "execution_profile")
        normalized_unsupported = tuple(unsupported_dimensions)
        for dimension in normalized_unsupported:
            _identifier(dimension, "unsupported_dimensions[]")
        if execution_profile == FAST_EXECUTION_PROFILE and normalized_unsupported:
            raise StageRuntimeError(
                "simple-field-property package cannot declare unsupported dimensions"
            )
        if execution_profile == FAST_EXECUTION_PROFILE:
            if obligations.package_version != PACKAGE_VERSION:
                raise StageRuntimeError(
                    f"simple-field-property fast path requires package version {PACKAGE_VERSION}"
                )
            blocking_gaps = sorted(
                item.gap_id for item in obligations.coverage_gaps if item.blocking
            )
            if blocking_gaps:
                raise StageRuntimeError(
                    "simple-field-property fast path cannot contain blocking coverage gaps: "
                    + ", ".join(blocking_gaps)
                )
        if obligations.package_id != package_id:
            raise StageRuntimeError("obligations package_id does not match package_id")
        resolved_output = output_root.resolve()
        try:
            resolved_output.relative_to(self.repo_root)
        except ValueError as exc:
            raise StageRuntimeError("prepared package output must be inside repository") from exc
        if resolved_output.exists():
            raise StageRuntimeError("prepared package output already exists and is immutable")
        if not evidence_inputs:
            raise StageRuntimeError("at least one evidence input is required")
        registry = tuple(
            SourceRegistryEntry(
                path=repository_relative(path, self.repo_root),
                sha256=sha256_path(path),
                role=role,
                locator=locator,
            )
            for path, role, locator in source_registry
        )
        if not registry:
            raise StageRuntimeError("at least one full source registry entry is required")
        for item in registry:
            item.validate()
        temporary = resolved_output.with_name(f".{resolved_output.name}.building-{os.getpid()}")
        if temporary.exists():
            raise StageRuntimeError(f"prepared package temporary path already exists: {temporary}")
        try:
            temporary.mkdir(parents=True)
            evidence_text = self._render_evidence(package_id, evidence_inputs)
            evidence_max_bytes = (
                FAST_EVIDENCE_MAX_BYTES
                if execution_profile == FAST_EXECUTION_PROFILE
                else STANDARD_ROUTING_EVIDENCE_MAX_BYTES
            )
            evidence_bytes = len(evidence_text.encode("utf-8"))
            if evidence_bytes > evidence_max_bytes:
                raise StageRuntimeError(
                    "blocked-package-budget: source evidence exceeds "
                    f"{evidence_max_bytes} bytes for {execution_profile}: "
                    f"actual={evidence_bytes}"
                )
            obligations.validate(evidence_text=evidence_text)
            evidence_path = temporary / "source-evidence.md"
            obligations_path = temporary / "atomic-obligations.json"
            instructions_path = temporary / "stage-instructions.md"
            evidence_path.write_text(evidence_text, encoding="utf-8")
            write_json_atomic(obligations_path, obligations.to_dict())
            instructions_path.write_text(
                self._render_instructions(package_id, instructions), encoding="utf-8"
            )
            artifacts = tuple(
                PackageArtifact(
                    path=repository_relative(resolved_output / path.name, self.repo_root),
                    sha256=sha256_path(path),
                    kind=kind,
                    bytes=path.stat().st_size,
                )
                for path, kind in (
                    (evidence_path, "source-evidence"),
                    (obligations_path, "atomic-obligations"),
                    (instructions_path, "stage-instructions"),
                )
            )
            package = PreparedStagePackage(
                package_version=PACKAGE_VERSION,
                package_id=package_id,
                ft_slug=ft_slug,
                scope_slug=scope_slug,
                section_id=section_id,
                created_at=utc_timestamp(),
                source_registry=registry,
                package_artifacts=artifacts,
                execution_profile=execution_profile,
                unsupported_dimensions=normalized_unsupported,
                forbidden_evidence_roots=tuple(forbidden_evidence_roots),
                fallback_policy="targeted-only",
                package_digest="",
            )
            package = replace(package, package_digest=_canonical_digest(package._without_digest()))
            package.validate()
            write_json_atomic(temporary / "stage-package.json", package.to_dict())
            total_bytes = sum(path.stat().st_size for path in temporary.iterdir() if path.is_file())
            if total_bytes > self.max_package_bytes:
                raise StageRuntimeError(
                    f"blocked-package-budget: package bytes {total_bytes} exceed {self.max_package_bytes}"
                )
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(resolved_output)
            return load_prepared_package(resolved_output / "stage-package.json", self.repo_root)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

    def _render_evidence(
        self,
        package_id: str,
        evidence_inputs: Sequence[EvidenceInput],
    ) -> str:
        lines = ["# Prepared Source Evidence", "", f"- package_id: `{package_id}`", ""]
        seen: set[Path] = set()
        for item in evidence_inputs:
            path = item.path.resolve()
            if path in seen:
                raise StageRuntimeError(f"duplicate evidence input: {path}")
            seen.add(path)
            if not path.is_file():
                raise StageRuntimeError(f"evidence input is missing: {path}")
            relative = repository_relative(path, self.repo_root)
            content = path.read_text(encoding="utf-8")
            selected = self._select_evidence(item, content, relative)
            lines.extend(
                [
                    f"## {item.title}",
                    "",
                    f"- source_path: `{relative}`",
                    f"- source_sha256: `{sha256_path(path)}`",
                    f"- selectors: `{', '.join(item.selectors) if item.selectors else 'full-explicit'}`",
                    "",
                    selected.rstrip(),
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _select_evidence(item: EvidenceInput, content: str, relative: str) -> str:
        if not isinstance(item.max_bytes, int) or isinstance(item.max_bytes, bool) or item.max_bytes < 1:
            raise StageRuntimeError(f"evidence max_bytes must be positive: {relative}")
        if item.include_full:
            selected = content
        else:
            if not item.selectors:
                raise StageRuntimeError(
                    f"scope-local evidence requires selectors or include_full=true: {relative}"
                )
            lines = content.splitlines()
            ranges: list[tuple[int, int]] = []
            for selector in item.selectors:
                _text(selector, "evidence selector")
                matches = [
                    index
                    for index, line in enumerate(lines)
                    if _selector_matches(line, selector)
                ]
                if not matches:
                    raise StageRuntimeError(
                        f"evidence selector not found in {relative}: {selector}"
                    )
                for match in matches:
                    start = match
                    heading_level: int | None = None
                    for index in range(match, -1, -1):
                        heading = re.match(r"^(#{1,6})\s+", lines[index])
                        if heading:
                            start = index
                            heading_level = len(heading.group(1))
                            break
                    if heading_level is None:
                        ranges.append((max(0, match - 2), min(len(lines), match + 3)))
                        continue
                    end = len(lines)
                    for index in range(start + 1, len(lines)):
                        heading = re.match(r"^(#{1,6})\s+", lines[index])
                        if heading and len(heading.group(1)) <= heading_level:
                            end = index
                            break
                    ranges.append((start, end))
            merged: list[tuple[int, int]] = []
            for start, end in sorted(ranges):
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            selected = "\n\n".join("\n".join(lines[start:end]).strip() for start, end in merged)
        if len(selected.encode("utf-8")) > item.max_bytes:
            raise StageRuntimeError(
                f"evidence slice exceeds max_bytes for {relative}: {len(selected.encode('utf-8'))}"
            )
        return selected

    @staticmethod
    def _render_instructions(package_id: str, config: StageInstructionConfig) -> str:
        fast_path = config.scenario == "writer.session_prepared_initial_draft"
        structured_fast = fast_path and config.sandbox_policy == "read_only"
        structured_standard = not fast_path and config.sandbox_policy == "read_only"
        section_title = (
            "Structured Fast Path"
            if structured_fast
            else "Structured Standard Path"
            if structured_standard
            else "Fast Path"
            if fast_path
            else "Prepared Standard Context"
        )
        if structured_fast or structured_standard:
            execution_rules = [
                "1. Use only the runner-embedded verified projection; do not reread workspace files.",
                "2. Do not call shell or file tools; the command budget is zero.",
                "3. Return the complete unsigned draft in the schema-constrained final contract.",
                "4. The runner alone materializes output_path and applies deterministic gates.",
                "5. Return blocked-input only when inline evidence cannot define test intent or an observable oracle without invention; missing stand IDs, locators, tokens or prerecorded provider responses are UI-prep bindings, not FT-first blockers.",
            ]
        elif fast_path:
            execution_rules = [
                "1. Use the runner-embedded verified projection; do not reread package files in the stage.",
                "2. Do not rerun source locator, scope analyzer, source parity, DOCX extraction or PDF rendering.",
                "3. Write a structurally complete minimum output before optional refinement.",
                "4. Keep output and scratch inside attempt_root.",
                "5. Do not read generated test cases, earlier cycles or canary artifacts as evidence.",
            ]
        else:
            execution_rules = [
                "1. Load the full standard writer instruction scenario selected by the runner.",
                "2. Use the runner-embedded verified projection as the primary scope evidence.",
                "3. Do not rerun source locator, scope analyzer or broad full-document discovery.",
                "4. Keep output and scratch inside attempt_root.",
                "5. Do not read generated test cases, earlier cycles or canary artifacts as evidence.",
            ]
        fallback_rules = (
            [
                "Structured mode has no source fallback. Portable synthetic values, relative dates and runtime-selected integration responses with source-defined observable properties are reproducible FT-first fixtures; block only when test intent or oracle still requires invention."
            ]
            if structured_fast or structured_standard
            else [
                "Use a registered full source only when one named ATOM/source locator is unresolved by the package.",
                "Record targeted_source_fallback with the reason, source path and exact locator.",
                "Do not scan a complete document or use external scratch paths. Return blocked if evidence stays insufficient.",
            ]
        )
        return "\n".join(
            [
                "# Prepared Stage Instructions",
                "",
                f"- package_id: `{package_id}`",
                f"- role: `{config.role}`",
                f"- scenario: `{config.scenario}`",
                f"- output_path: `{config.output_path}`",
                f"- attempt_root: `{config.attempt_root}`",
                f"- sandbox_policy: `{config.sandbox_policy}`",
                f"- hard_timeout_seconds: `{config.timeout_seconds}`",
                f"- idle_timeout_seconds: `{config.idle_timeout_seconds}`",
                f"- command_budget: `{config.command_budget}`",
                "",
                f"## {section_title}",
                "",
                *execution_rules,
                "",
                "## Targeted Fallback",
                "",
                *fallback_rules,
                "",
            ]
        )


def load_obligations(path: Path, *, evidence_text: str | None = None) -> PreparedObligationSet:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(f"cannot load prepared obligations: {path}") from exc
    return PreparedObligationSet.from_dict(payload, evidence_text=evidence_text)


def load_prepared_package(path: Path, repo_root: Path) -> PreparedStagePackage:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(f"cannot load prepared stage package: {path}") from exc
    package = PreparedStagePackage.from_dict(payload)
    verify_prepared_package(package, repo_root, manifest_path=path)
    return package


def verify_prepared_package(
    package: PreparedStagePackage,
    repo_root: Path,
    *,
    manifest_path: Path | None = None,
) -> None:
    package.validate()
    for source in package.source_registry:
        path = resolve_repository_path(source.path, repo_root)
        actual = sha256_path(path)
        if actual != source.sha256:
            raise StageRuntimeError(f"registered full source hash mismatch: {source.path}")
    package_root = manifest_path.resolve().parent if manifest_path is not None else None
    for artifact in package.package_artifacts:
        path = resolve_repository_path(artifact.path, repo_root)
        if package_root is not None and path.parent != package_root:
            raise StageRuntimeError("package artifacts must be siblings of stage-package.json")
        actual = sha256_path(path)
        if actual != artifact.sha256:
            raise StageRuntimeError(f"prepared package artifact hash mismatch: {artifact.path}")
        if path.stat().st_size != artifact.bytes:
            raise StageRuntimeError(f"prepared package artifact byte size mismatch: {artifact.path}")
    obligations_artifact = next(
        item for item in package.package_artifacts if item.kind == "atomic-obligations"
    )
    evidence_artifact = next(item for item in package.package_artifacts if item.kind == "source-evidence")
    evidence_text = resolve_repository_path(evidence_artifact.path, repo_root).read_text(encoding="utf-8")
    obligations = load_obligations(
        resolve_repository_path(obligations_artifact.path, repo_root),
        evidence_text=evidence_text,
    )
    if obligations.package_id != package.package_id:
        raise StageRuntimeError("prepared obligations package_id does not match stage package")
