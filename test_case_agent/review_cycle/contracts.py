from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


CONTRACT_VERSION = 2
ROLES = {"writer", "reviewer"}
SANDBOX_BY_ROLE = {"writer": "workspace_write", "reviewer": "read_only"}
RESULT_STATUS_BY_OUTCOME = {
    "draft-ready": "completed",
    "accepted": "completed",
    "changes-required": "changes-required",
    "blocked": "blocked",
}
OUTCOMES_BY_ROLE = {
    "writer": {"draft-ready", "blocked"},
    "reviewer": {"accepted", "changes-required", "blocked"},
}
OUTPUT_PRODUCERS = {"stage", "runner"}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class ContractValidationError(ValueError):
    """Raised when a stage manifest or result violates the v2 contract."""


def _require_exact_keys(payload: Mapping[str, Any], expected: set[str], label: str) -> None:
    if not isinstance(payload, Mapping):
        raise ContractValidationError(f"{label} must be a JSON object")
    actual = set(payload)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unknown:
            details.append("unknown=" + ",".join(unknown))
        raise ContractValidationError(f"Invalid {label} fields: {'; '.join(details)}")


def _require_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not IDENTIFIER_PATTERN.fullmatch(value):
        raise ContractValidationError(f"{field_name} must be a non-empty stable identifier")


def _require_json_array(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractValidationError(f"{field_name} must be a JSON array")
    return value


def _require_sha256(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
        raise ContractValidationError(f"{field_name} must be a lowercase SHA-256 hex digest")


def _require_relative_path(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ContractValidationError(f"{field_name} must be a non-empty repository-relative path")
    if "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ContractValidationError(f"{field_name} must use canonical repository-relative POSIX syntax")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts) or path.as_posix() != value:
        raise ContractValidationError(f"{field_name} must be normalized and cannot traverse directories")


def _path_is_under(path_value: str, root_value: str) -> bool:
    try:
        PurePosixPath(path_value).relative_to(PurePosixPath(root_value))
    except ValueError:
        return False
    return True


def _require_timestamp(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ContractValidationError(f"{field_name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractValidationError(f"{field_name} must include a timezone")
    return parsed


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    sha256: str
    kind: str

    def validate(self, field_name: str = "artifact") -> None:
        _require_relative_path(self.path, f"{field_name}.path")
        _require_sha256(self.sha256, f"{field_name}.sha256")
        _require_identifier(self.kind, f"{field_name}.kind")

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "kind": self.kind}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], field_name: str = "artifact") -> ArtifactRef:
        _require_exact_keys(payload, {"path", "sha256", "kind"}, field_name)
        artifact = cls(
            path=payload["path"],
            sha256=payload["sha256"],
            kind=payload["kind"],
        )
        artifact.validate(field_name)
        return artifact


@dataclass(frozen=True)
class ExpectedOutput:
    path: str
    kind: str
    producer: str
    required: bool = True

    def validate(self, field_name: str = "expected_output") -> None:
        _require_relative_path(self.path, f"{field_name}.path")
        _require_identifier(self.kind, f"{field_name}.kind")
        if not isinstance(self.producer, str) or self.producer not in OUTPUT_PRODUCERS:
            raise ContractValidationError(
                f"{field_name}.producer must be one of {sorted(OUTPUT_PRODUCERS)}"
            )
        if not isinstance(self.required, bool):
            raise ContractValidationError(f"{field_name}.required must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "producer": self.producer,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], field_name: str = "expected_output") -> ExpectedOutput:
        _require_exact_keys(payload, {"path", "kind", "producer", "required"}, field_name)
        output = cls(
            path=payload["path"],
            kind=payload["kind"],
            producer=payload["producer"],
            required=payload["required"],
        )
        output.validate(field_name)
        return output


@dataclass(frozen=True)
class StageInputManifest:
    contract_version: int
    cycle_id: str
    stage_id: str
    attempt_id: str
    session_id: str
    role: str
    scenario: str
    semantic_round: int
    sandbox_policy: str
    timeout_seconds: int
    attempt_root: str
    canonical_test_cases: str
    prompt_artifact: ArtifactRef
    instruction_artifacts: tuple[ArtifactRef, ...]
    source_artifacts: tuple[ArtifactRef, ...]
    handoff_artifacts: tuple[ArtifactRef, ...]
    expected_outputs: tuple[ExpectedOutput, ...]
    allowed_write_roots: tuple[str, ...]
    forbidden_write_roots: tuple[str, ...]
    input_digest: str

    @classmethod
    def create(
        cls,
        *,
        cycle_id: str,
        stage_id: str,
        attempt_id: str,
        session_id: str,
        role: str,
        scenario: str,
        semantic_round: int,
        sandbox_policy: str,
        timeout_seconds: int,
        attempt_root: str,
        canonical_test_cases: str,
        prompt_artifact: ArtifactRef,
        instruction_artifacts: Sequence[ArtifactRef],
        source_artifacts: Sequence[ArtifactRef],
        handoff_artifacts: Sequence[ArtifactRef],
        expected_outputs: Sequence[ExpectedOutput],
        allowed_write_roots: Sequence[str],
        forbidden_write_roots: Sequence[str],
    ) -> StageInputManifest:
        manifest = cls(
            contract_version=CONTRACT_VERSION,
            cycle_id=cycle_id,
            stage_id=stage_id,
            attempt_id=attempt_id,
            session_id=session_id,
            role=role,
            scenario=scenario,
            semantic_round=semantic_round,
            sandbox_policy=sandbox_policy,
            timeout_seconds=timeout_seconds,
            attempt_root=attempt_root,
            canonical_test_cases=canonical_test_cases,
            prompt_artifact=prompt_artifact,
            instruction_artifacts=tuple(instruction_artifacts),
            source_artifacts=tuple(source_artifacts),
            handoff_artifacts=tuple(handoff_artifacts),
            expected_outputs=tuple(expected_outputs),
            allowed_write_roots=tuple(allowed_write_roots),
            forbidden_write_roots=tuple(forbidden_write_roots),
            input_digest="",
        )
        manifest._validate_structure(check_digest=False)
        completed = replace(manifest, input_digest=manifest.compute_digest())
        completed.validate()
        return completed

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "cycle_id": self.cycle_id,
            "stage_id": self.stage_id,
            "attempt_id": self.attempt_id,
            "session_id": self.session_id,
            "role": self.role,
            "scenario": self.scenario,
            "semantic_round": self.semantic_round,
            "sandbox_policy": self.sandbox_policy,
            "timeout_seconds": self.timeout_seconds,
            "attempt_root": self.attempt_root,
            "canonical_test_cases": self.canonical_test_cases,
            "prompt_artifact": self.prompt_artifact.to_dict(),
            "instruction_artifacts": [artifact.to_dict() for artifact in self.instruction_artifacts],
            "source_artifacts": [artifact.to_dict() for artifact in self.source_artifacts],
            "handoff_artifacts": [artifact.to_dict() for artifact in self.handoff_artifacts],
            "expected_outputs": [output.to_dict() for output in self.expected_outputs],
            "allowed_write_roots": list(self.allowed_write_roots),
            "forbidden_write_roots": list(self.forbidden_write_roots),
        }

    def compute_digest(self) -> str:
        canonical = json.dumps(
            self._payload_without_digest(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload_without_digest(), "input_digest": self.input_digest}

    def validate(self) -> None:
        self._validate_structure(check_digest=True)

    def _validate_structure(self, *, check_digest: bool) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise ContractValidationError(
                f"contract_version must be {CONTRACT_VERSION}, got {self.contract_version}"
            )
        for field_name, value in (
            ("cycle_id", self.cycle_id),
            ("stage_id", self.stage_id),
            ("attempt_id", self.attempt_id),
            ("session_id", self.session_id),
            ("scenario", self.scenario),
        ):
            _require_identifier(value, field_name)
        if not isinstance(self.role, str) or self.role not in ROLES:
            raise ContractValidationError(f"role must be one of {sorted(ROLES)}")
        if not isinstance(self.sandbox_policy, str) or self.sandbox_policy != SANDBOX_BY_ROLE[self.role]:
            raise ContractValidationError(
                f"{self.role} stages require sandbox_policy={SANDBOX_BY_ROLE[self.role]}"
            )
        if (
            isinstance(self.semantic_round, bool)
            or not isinstance(self.semantic_round, int)
            or not 0 <= self.semantic_round <= 2
        ):
            raise ContractValidationError("semantic_round must be an integer from 0 to 2")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, int)
            or self.timeout_seconds < 1
        ):
            raise ContractValidationError("timeout_seconds must be a positive integer")
        _require_relative_path(self.attempt_root, "attempt_root")
        _require_relative_path(self.canonical_test_cases, "canonical_test_cases")
        self.prompt_artifact.validate("prompt_artifact")
        if not _path_is_under(self.prompt_artifact.path, self.attempt_root):
            raise ContractValidationError("prompt_artifact must be under attempt_root")

        groups = (
            ("instruction_artifacts", self.instruction_artifacts),
            ("source_artifacts", self.source_artifacts),
            ("handoff_artifacts", self.handoff_artifacts),
        )
        all_input_paths = [self.prompt_artifact.path]
        for group_name, group in groups:
            if not group:
                raise ContractValidationError(f"{group_name} must contain at least one artifact")
            for index, artifact in enumerate(group):
                artifact.validate(f"{group_name}[{index}]")
                all_input_paths.append(artifact.path)
        if len(all_input_paths) != len(set(all_input_paths)):
            raise ContractValidationError("input artifact paths must be unique")

        if not self.expected_outputs:
            raise ContractValidationError("expected_outputs must contain at least one artifact contract")
        output_paths: list[str] = []
        for index, output in enumerate(self.expected_outputs):
            output.validate(f"expected_outputs[{index}]")
            if not _path_is_under(output.path, self.attempt_root):
                raise ContractValidationError(
                    f"expected output must be under attempt_root: {output.path}"
                )
            output_paths.append(output.path)
        if len(output_paths) != len(set(output_paths)):
            raise ContractValidationError("expected output paths must be unique")
        if set(output_paths) & set(all_input_paths):
            raise ContractValidationError("input and output artifact paths must not overlap")

        for field_name, roots in (
            ("allowed_write_roots", self.allowed_write_roots),
            ("forbidden_write_roots", self.forbidden_write_roots),
        ):
            for index, root in enumerate(roots):
                _require_relative_path(root, f"{field_name}[{index}]")
            if len(roots) != len(set(roots)):
                raise ContractValidationError(f"{field_name} must not contain duplicates")
        if not self.forbidden_write_roots:
            raise ContractValidationError("forbidden_write_roots must protect the production artifact tree")
        if any(_path_is_under(self.attempt_root, root) for root in self.forbidden_write_roots):
            raise ContractValidationError("attempt_root must not be under a forbidden write root")
        if not any(
            _path_is_under(self.canonical_test_cases, root) for root in self.forbidden_write_roots
        ):
            raise ContractValidationError("canonical_test_cases must be under a forbidden write root")
        for allowed in self.allowed_write_roots:
            if not _path_is_under(allowed, self.attempt_root):
                raise ContractValidationError("allowed write roots must be under attempt_root")
            for forbidden in self.forbidden_write_roots:
                if _path_is_under(allowed, forbidden) or _path_is_under(forbidden, allowed):
                    raise ContractValidationError("allowed and forbidden write roots must not overlap")

        stage_outputs = [output for output in self.expected_outputs if output.producer == "stage"]
        if self.role == "reviewer":
            if self.allowed_write_roots:
                raise ContractValidationError("reviewer stages must not declare allowed write roots")
            if stage_outputs:
                raise ContractValidationError("reviewer outputs must be persisted by the runner")
        else:
            if not self.allowed_write_roots:
                raise ContractValidationError("writer stages must declare an allowed work output root")
            for output in stage_outputs:
                if not any(_path_is_under(output.path, root) for root in self.allowed_write_roots):
                    raise ContractValidationError(
                        f"stage-produced output is outside allowed write roots: {output.path}"
                    )
        for output in self.expected_outputs:
            if any(_path_is_under(output.path, root) for root in self.forbidden_write_roots):
                raise ContractValidationError(
                    f"expected output is inside a forbidden write root: {output.path}"
                )

        if check_digest:
            _require_sha256(self.input_digest, "input_digest")
            if self.compute_digest() != self.input_digest:
                raise ContractValidationError("input_digest does not match the manifest payload")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StageInputManifest:
        expected_keys = {
            "contract_version",
            "cycle_id",
            "stage_id",
            "attempt_id",
            "session_id",
            "role",
            "scenario",
            "semantic_round",
            "sandbox_policy",
            "timeout_seconds",
            "attempt_root",
            "canonical_test_cases",
            "prompt_artifact",
            "instruction_artifacts",
            "source_artifacts",
            "handoff_artifacts",
            "expected_outputs",
            "allowed_write_roots",
            "forbidden_write_roots",
            "input_digest",
        }
        _require_exact_keys(payload, expected_keys, "stage input manifest")
        instruction_artifacts = _require_json_array(
            payload["instruction_artifacts"], "instruction_artifacts"
        )
        source_artifacts = _require_json_array(payload["source_artifacts"], "source_artifacts")
        handoff_artifacts = _require_json_array(payload["handoff_artifacts"], "handoff_artifacts")
        expected_outputs = _require_json_array(payload["expected_outputs"], "expected_outputs")
        allowed_write_roots = _require_json_array(
            payload["allowed_write_roots"], "allowed_write_roots"
        )
        forbidden_write_roots = _require_json_array(
            payload["forbidden_write_roots"], "forbidden_write_roots"
        )
        manifest = cls(
            contract_version=payload["contract_version"],
            cycle_id=payload["cycle_id"],
            stage_id=payload["stage_id"],
            attempt_id=payload["attempt_id"],
            session_id=payload["session_id"],
            role=payload["role"],
            scenario=payload["scenario"],
            semantic_round=payload["semantic_round"],
            sandbox_policy=payload["sandbox_policy"],
            timeout_seconds=payload["timeout_seconds"],
            attempt_root=payload["attempt_root"],
            canonical_test_cases=payload["canonical_test_cases"],
            prompt_artifact=ArtifactRef.from_dict(payload["prompt_artifact"], "prompt_artifact"),
            instruction_artifacts=tuple(
                ArtifactRef.from_dict(item, f"instruction_artifacts[{index}]")
                for index, item in enumerate(instruction_artifacts)
            ),
            source_artifacts=tuple(
                ArtifactRef.from_dict(item, f"source_artifacts[{index}]")
                for index, item in enumerate(source_artifacts)
            ),
            handoff_artifacts=tuple(
                ArtifactRef.from_dict(item, f"handoff_artifacts[{index}]")
                for index, item in enumerate(handoff_artifacts)
            ),
            expected_outputs=tuple(
                ExpectedOutput.from_dict(item, f"expected_outputs[{index}]")
                for index, item in enumerate(expected_outputs)
            ),
            allowed_write_roots=tuple(allowed_write_roots),
            forbidden_write_roots=tuple(forbidden_write_roots),
            input_digest=payload["input_digest"],
        )
        manifest.validate()
        return manifest


@dataclass(frozen=True)
class StageResult:
    contract_version: int
    cycle_id: str
    stage_id: str
    attempt_id: str
    session_id: str
    backend_session_id: str
    role: str
    scenario: str
    input_digest: str
    status: str
    outcome: str
    output_artifacts: tuple[ArtifactRef, ...]
    started_at: str
    finished_at: str
    duration_ms: int
    exit_code: int | None
    timed_out: bool
    blocking_reasons: tuple[str, ...]

    def validate(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise ContractValidationError(
                f"contract_version must be {CONTRACT_VERSION}, got {self.contract_version}"
            )
        for field_name, value in (
            ("cycle_id", self.cycle_id),
            ("stage_id", self.stage_id),
            ("attempt_id", self.attempt_id),
            ("session_id", self.session_id),
            ("scenario", self.scenario),
        ):
            _require_identifier(value, field_name)
        if not isinstance(self.role, str) or self.role not in ROLES:
            raise ContractValidationError(f"role must be one of {sorted(ROLES)}")
        if not isinstance(self.outcome, str) or self.outcome not in OUTCOMES_BY_ROLE[self.role]:
            raise ContractValidationError(
                f"outcome={self.outcome!r} is not allowed for role={self.role!r}"
            )
        expected_status = RESULT_STATUS_BY_OUTCOME[self.outcome]
        if not isinstance(self.status, str) or self.status != expected_status:
            raise ContractValidationError(
                f"status={self.status!r} does not match outcome={self.outcome!r}"
            )
        _require_sha256(self.input_digest, "input_digest")
        if self.status == "blocked":
            if not self.blocking_reasons:
                raise ContractValidationError("blocked results must include blocking_reasons")
        elif self.blocking_reasons:
            raise ContractValidationError("non-blocked results must not include blocking_reasons")
        if not isinstance(self.backend_session_id, str):
            raise ContractValidationError("backend_session_id must be text")
        if self.status != "blocked":
            _require_identifier(self.backend_session_id, "backend_session_id")
        elif self.backend_session_id:
            _require_identifier(self.backend_session_id, "backend_session_id")
        if not isinstance(self.timed_out, bool):
            raise ContractValidationError("timed_out must be boolean")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, int)
            or self.duration_ms < 0
        ):
            raise ContractValidationError("duration_ms must be a non-negative integer")
        if self.exit_code is not None and (
            isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)
        ):
            raise ContractValidationError("exit_code must be an integer or null")
        started = _require_timestamp(self.started_at, "started_at")
        finished = _require_timestamp(self.finished_at, "finished_at")
        if finished < started:
            raise ContractValidationError("finished_at must not be earlier than started_at")
        paths: list[str] = []
        for index, artifact in enumerate(self.output_artifacts):
            artifact.validate(f"output_artifacts[{index}]")
            paths.append(artifact.path)
        if len(paths) != len(set(paths)):
            raise ContractValidationError("output artifact paths must be unique")
        for index, reason in enumerate(self.blocking_reasons):
            if not isinstance(reason, str) or not reason.strip():
                raise ContractValidationError(f"blocking_reasons[{index}] must be non-empty text")

    def validate_against(
        self,
        manifest: StageInputManifest,
        *,
        prior_backend_session_ids: Iterable[str] = (),
    ) -> None:
        self.validate()
        manifest.validate()
        identity_fields = (
            "contract_version",
            "cycle_id",
            "stage_id",
            "attempt_id",
            "session_id",
            "role",
            "scenario",
            "input_digest",
        )
        mismatched = [
            field_name
            for field_name in identity_fields
            if getattr(self, field_name) != getattr(manifest, field_name)
        ]
        if mismatched:
            raise ContractValidationError(
                "stage result does not match its input manifest: " + ", ".join(mismatched)
            )
        if self.backend_session_id:
            ensure_new_session_id(self.backend_session_id, prior_backend_session_ids)
        declared = {output.path: output for output in manifest.expected_outputs}
        actual = {artifact.path: artifact for artifact in self.output_artifacts}
        undeclared = sorted(set(actual) - set(declared))
        missing = sorted(
            path for path, output in declared.items() if output.required and path not in actual
        )
        if undeclared:
            raise ContractValidationError(
                "stage result contains undeclared output artifacts: " + ", ".join(undeclared)
            )
        if self.status != "blocked" and missing:
            raise ContractValidationError(
                "stage result is missing required output artifacts: " + ", ".join(missing)
            )
        for artifact in self.output_artifacts:
            if declared[artifact.path].kind != artifact.kind:
                raise ContractValidationError(
                    f"output artifact kind mismatch for {artifact.path}: "
                    f"expected {declared[artifact.path].kind}, got {artifact.kind}"
                )
            if any(
                _path_is_under(artifact.path, root) for root in manifest.forbidden_write_roots
            ):
                raise ContractValidationError(
                    f"stage result references an output under a forbidden write root: {artifact.path}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "cycle_id": self.cycle_id,
            "stage_id": self.stage_id,
            "attempt_id": self.attempt_id,
            "session_id": self.session_id,
            "backend_session_id": self.backend_session_id,
            "role": self.role,
            "scenario": self.scenario,
            "input_digest": self.input_digest,
            "status": self.status,
            "outcome": self.outcome,
            "output_artifacts": [artifact.to_dict() for artifact in self.output_artifacts],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "blocking_reasons": list(self.blocking_reasons),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StageResult:
        expected_keys = {
            "contract_version",
            "cycle_id",
            "stage_id",
            "attempt_id",
            "session_id",
            "backend_session_id",
            "role",
            "scenario",
            "input_digest",
            "status",
            "outcome",
            "output_artifacts",
            "started_at",
            "finished_at",
            "duration_ms",
            "exit_code",
            "timed_out",
            "blocking_reasons",
        }
        _require_exact_keys(payload, expected_keys, "stage result")
        output_artifacts = _require_json_array(payload["output_artifacts"], "output_artifacts")
        blocking_reasons = _require_json_array(payload["blocking_reasons"], "blocking_reasons")
        result = cls(
            contract_version=payload["contract_version"],
            cycle_id=payload["cycle_id"],
            stage_id=payload["stage_id"],
            attempt_id=payload["attempt_id"],
            session_id=payload["session_id"],
            backend_session_id=payload["backend_session_id"],
            role=payload["role"],
            scenario=payload["scenario"],
            input_digest=payload["input_digest"],
            status=payload["status"],
            outcome=payload["outcome"],
            output_artifacts=tuple(
                ArtifactRef.from_dict(item, f"output_artifacts[{index}]")
                for index, item in enumerate(output_artifacts)
            ),
            started_at=payload["started_at"],
            finished_at=payload["finished_at"],
            duration_ms=payload["duration_ms"],
            exit_code=payload["exit_code"],
            timed_out=payload["timed_out"],
            blocking_reasons=tuple(blocking_reasons),
        )
        result.validate()
        return result


def ensure_new_session_id(session_id: str, prior_session_ids: Iterable[str]) -> None:
    _require_identifier(session_id, "backend_session_id")
    prior = {str(item) for item in prior_session_ids}
    if session_id in prior:
        raise ContractValidationError(
            f"backend_session_id must identify a fresh stage session: {session_id}"
        )
