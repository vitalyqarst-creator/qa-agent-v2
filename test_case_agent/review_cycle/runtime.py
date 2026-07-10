from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from test_case_agent.review_cycle.contracts import (
    ArtifactRef,
    ContractValidationError,
    StageInputManifest,
    StageResult,
)


class StageRuntimeError(RuntimeError):
    """Raised when filesystem evidence does not satisfy a stage contract."""


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def repository_relative(path: Path, repo_root: Path) -> str:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise StageRuntimeError(f"path is outside repository root: {resolved_path}") from exc
    value = relative.as_posix()
    if not value or value == ".":
        raise StageRuntimeError("artifact path must not resolve to the repository root")
    return value


def resolve_repository_path(path_value: str, repo_root: Path) -> Path:
    candidate = (repo_root.resolve() / Path(path_value)).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise StageRuntimeError(f"repository-relative path escapes repository root: {path_value}") from exc
    return candidate


def sha256_path(path: Path) -> str:
    import hashlib

    if not path.is_file():
        raise StageRuntimeError(f"artifact is missing or is not a file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_ref(path: Path, repo_root: Path, *, kind: str) -> ArtifactRef:
    reference = ArtifactRef(
        path=repository_relative(path, repo_root),
        sha256=sha256_path(path),
        kind=kind,
    )
    reference.validate()
    return reference


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def append_ndjson(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


@dataclass(frozen=True)
class BackendStageExecution:
    backend: str
    backend_session_id: str
    started_at: str
    finished_at: str
    duration_ms: int
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    events: str = ""
    timed_out: bool = False
    launch_error: bool = False
    usage: Mapping[str, int] | None = None

    def validate(self) -> None:
        if not self.backend.strip():
            raise StageRuntimeError("backend must be non-empty")
        if not isinstance(self.duration_ms, int) or isinstance(self.duration_ms, bool) or self.duration_ms < 0:
            raise StageRuntimeError("duration_ms must be a non-negative integer")
        if self.exit_code is not None and (
            not isinstance(self.exit_code, int) or isinstance(self.exit_code, bool)
        ):
            raise StageRuntimeError("exit_code must be an integer or null")
        if not isinstance(self.timed_out, bool) or not isinstance(self.launch_error, bool):
            raise StageRuntimeError("timed_out and launch_error must be boolean")
        for field_name, value in (("started_at", self.started_at), ("finished_at", self.finished_at)):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (AttributeError, ValueError) as exc:
                raise StageRuntimeError(f"{field_name} must be an ISO-8601 timestamp") from exc
            if parsed.tzinfo is None:
                raise StageRuntimeError(f"{field_name} must include a timezone")
        if self.usage is not None:
            for key, value in self.usage.items():
                if not isinstance(key, str) or not key:
                    raise StageRuntimeError("usage keys must be non-empty text")
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise StageRuntimeError(f"usage[{key!r}] must be a non-negative integer")


class StageBackend(Protocol):
    name: str

    def execute(
        self,
        manifest: StageInputManifest,
        *,
        prompt: str,
        cwd: Path,
    ) -> BackendStageExecution:
        ...


@dataclass(frozen=True)
class StageAttemptPaths:
    repo_root: Path
    attempt_root: Path

    @classmethod
    def from_manifest(cls, repo_root: Path, manifest: StageInputManifest) -> StageAttemptPaths:
        manifest.validate()
        return cls(
            repo_root=repo_root.resolve(),
            attempt_root=resolve_repository_path(manifest.attempt_root, repo_root),
        )

    @property
    def manifest(self) -> Path:
        return self.attempt_root / "stage-input.json"

    @property
    def result(self) -> Path:
        return self.attempt_root / "stage-result.json"

    @property
    def stdout(self) -> Path:
        return self.attempt_root / "stdout.txt"

    @property
    def stderr(self) -> Path:
        return self.attempt_root / "stderr.txt"

    @property
    def events(self) -> Path:
        return self.attempt_root / "events.ndjson"


class StageArtifactStore:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()

    def prepare_new_attempt(self, manifest: StageInputManifest) -> StageAttemptPaths:
        paths = StageAttemptPaths.from_manifest(self.repo_root, manifest)
        if paths.attempt_root.exists():
            raise StageRuntimeError(
                f"attempt root already exists; recovery must be explicit: {manifest.attempt_root}"
            )
        paths.attempt_root.mkdir(parents=True)
        return paths

    def verify_artifact(self, reference: ArtifactRef) -> Path:
        reference.validate()
        path = resolve_repository_path(reference.path, self.repo_root)
        actual = sha256_path(path)
        if actual != reference.sha256:
            raise StageRuntimeError(
                f"artifact hash mismatch for {reference.path}: expected {reference.sha256}, got {actual}"
            )
        return path

    def verify_manifest_inputs(self, manifest: StageInputManifest) -> None:
        manifest.validate()
        references = (
            manifest.prompt_artifact,
            *manifest.instruction_artifacts,
            *manifest.source_artifacts,
            *manifest.handoff_artifacts,
        )
        for reference in references:
            self.verify_artifact(reference)

    def write_manifest(self, paths: StageAttemptPaths, manifest: StageInputManifest) -> Path:
        expected = StageAttemptPaths.from_manifest(self.repo_root, manifest)
        if expected.attempt_root != paths.attempt_root:
            raise StageRuntimeError("attempt paths do not match manifest.attempt_root")
        self.verify_manifest_inputs(manifest)
        if paths.manifest.exists():
            raise StageRuntimeError("stage-input.json already exists and is immutable")
        write_json_atomic(paths.manifest, manifest.to_dict())
        return paths.manifest

    def collect_declared_outputs(self, manifest: StageInputManifest) -> tuple[ArtifactRef, ...]:
        references: list[ArtifactRef] = []
        for output in manifest.expected_outputs:
            path = resolve_repository_path(output.path, self.repo_root)
            if not path.is_file():
                if output.required:
                    raise StageRuntimeError(f"required stage output is missing: {output.path}")
                continue
            references.append(artifact_ref(path, self.repo_root, kind=output.kind))
        return tuple(references)

    def write_result(
        self,
        paths: StageAttemptPaths,
        manifest: StageInputManifest,
        result: StageResult,
        *,
        prior_backend_session_ids: tuple[str, ...] = (),
    ) -> Path:
        result.validate_against(
            manifest,
            prior_backend_session_ids=prior_backend_session_ids,
        )
        expected = StageAttemptPaths.from_manifest(self.repo_root, manifest)
        if expected.attempt_root != paths.attempt_root:
            raise StageRuntimeError("attempt paths do not match result manifest")
        for reference in result.output_artifacts:
            self.verify_artifact(reference)
        if paths.result.exists():
            raise StageRuntimeError("stage-result.json already exists and is immutable")
        write_json_atomic(paths.result, result.to_dict())
        return paths.result


def load_manifest(path: Path) -> StageInputManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(f"cannot load stage manifest: {path}") from exc
    try:
        return StageInputManifest.from_dict(payload)
    except ContractValidationError as exc:
        raise StageRuntimeError(f"invalid stage manifest {path}: {exc}") from exc


def load_result(path: Path) -> StageResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StageRuntimeError(f"cannot load stage result: {path}") from exc
    try:
        return StageResult.from_dict(payload)
    except ContractValidationError as exc:
        raise StageRuntimeError(f"invalid stage result {path}: {exc}") from exc
