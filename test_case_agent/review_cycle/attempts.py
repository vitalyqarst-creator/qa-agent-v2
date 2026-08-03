from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from test_case_agent.review_cycle.runtime import (
    StageArtifactStore,
    StageRuntimeError,
    load_manifest,
    load_result,
    repository_relative,
)


ATTEMPT_PATTERN = re.compile(r"attempt-(\d{3})")
STAGE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class AttemptRecoveryError(StageRuntimeError):
    """Raised when an attempt cannot be safely retried or recovered."""


def format_attempt_id(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 999:
        raise AttemptRecoveryError("attempt number must be an integer from 1 to 999")
    return f"attempt-{number:03d}"


@dataclass(frozen=True)
class AttemptRecord:
    stage_id: str
    attempt_id: str
    root: Path
    state: str
    backend_session_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class AttemptPlan:
    stage_id: str
    attempt_id: str
    root: Path
    prior_backend_session_ids: tuple[str, ...]
    recovery_from: str = ""


class StageAttemptLedger:
    def __init__(self, repo_root: Path, cycle_root: Path):
        self.repo_root = repo_root.resolve()
        self.cycle_root = cycle_root.resolve()
        try:
            self.cycle_root.relative_to(self.repo_root)
        except ValueError as exc:
            raise AttemptRecoveryError("cycle root must be inside repository root") from exc
        self.store = StageArtifactStore(self.repo_root)

    def stage_root(self, stage_id: str) -> Path:
        if not isinstance(stage_id, str) or not STAGE_PATTERN.fullmatch(stage_id):
            raise AttemptRecoveryError("stage_id must be a stable identifier")
        return self.cycle_root / "attempts" / stage_id

    def inspect(self, stage_id: str) -> tuple[AttemptRecord, ...]:
        stage_root = self.stage_root(stage_id)
        if not stage_root.exists():
            return ()
        records: list[AttemptRecord] = []
        seen_sessions: list[str] = []
        for root in sorted(path for path in stage_root.iterdir() if path.is_dir()):
            match = ATTEMPT_PATTERN.fullmatch(root.name)
            if match is None:
                records.append(
                    AttemptRecord(
                        stage_id=stage_id,
                        attempt_id=root.name,
                        root=root,
                        state="corrupt",
                        reason="attempt directory name does not match attempt-NNN",
                    )
                )
                continue
            record = self._inspect_one(stage_id, root, tuple(seen_sessions))
            records.append(record)
            if record.backend_session_id:
                seen_sessions.append(record.backend_session_id)
        return tuple(records)

    def _inspect_one(
        self,
        stage_id: str,
        root: Path,
        prior_backend_session_ids: tuple[str, ...],
    ) -> AttemptRecord:
        manifest_path = root / "stage-input.json"
        result_path = root / "stage-result.json"
        if not manifest_path.is_file():
            return AttemptRecord(stage_id, root.name, root, "incomplete", reason="stage-input.json missing")
        try:
            manifest = load_manifest(manifest_path)
            expected_root = repository_relative(root, self.repo_root)
            if manifest.stage_id != stage_id or manifest.attempt_id != root.name:
                raise AttemptRecoveryError("manifest identity does not match attempt directory")
            if manifest.attempt_root != expected_root:
                raise AttemptRecoveryError("manifest attempt_root does not match attempt directory")
            self.store.verify_manifest_inputs(manifest)
        except StageRuntimeError as exc:
            return AttemptRecord(stage_id, root.name, root, "corrupt", reason=str(exc))
        if not result_path.is_file():
            return AttemptRecord(stage_id, root.name, root, "incomplete", reason="stage-result.json missing")
        try:
            result = load_result(result_path)
            result.validate_against(
                manifest,
                prior_backend_session_ids=prior_backend_session_ids,
            )
            for reference in result.output_artifacts:
                self.store.verify_artifact(reference)
        except (StageRuntimeError, ValueError) as exc:
            return AttemptRecord(stage_id, root.name, root, "corrupt", reason=str(exc))
        state = {
            "blocked": "blocked",
            "changes-required": "changes-required",
            "completed": "succeeded",
        }[result.status]
        return AttemptRecord(
            stage_id=stage_id,
            attempt_id=root.name,
            root=root,
            state=state,
            backend_session_id=result.backend_session_id,
        )

    def plan_next(self, stage_id: str, *, retry_blocked: bool = False) -> AttemptPlan:
        records = self.inspect(stage_id)
        prior_sessions = tuple(
            record.backend_session_id for record in records if record.backend_session_id
        )
        if not records:
            attempt_id = format_attempt_id(1)
            return AttemptPlan(
                stage_id=stage_id,
                attempt_id=attempt_id,
                root=self.stage_root(stage_id) / attempt_id,
                prior_backend_session_ids=prior_sessions,
            )
        unsafe = [record for record in records if record.state in {"incomplete", "corrupt"}]
        if unsafe:
            latest = unsafe[-1]
            raise AttemptRecoveryError(
                f"{latest.attempt_id} is {latest.state}; manual reconciliation is required: {latest.reason}"
            )
        latest = records[-1]
        if latest.state != "blocked":
            raise AttemptRecoveryError(
                f"{latest.attempt_id} is already {latest.state}; the stage must not be repeated"
            )
        if not retry_blocked:
            raise AttemptRecoveryError(
                f"{latest.attempt_id} is blocked; an explicit retry_blocked decision is required"
            )
        match = ATTEMPT_PATTERN.fullmatch(latest.attempt_id)
        if match is None:
            raise AttemptRecoveryError("latest attempt id is invalid")
        attempt_id = format_attempt_id(int(match.group(1)) + 1)
        return AttemptPlan(
            stage_id=stage_id,
            attempt_id=attempt_id,
            root=self.stage_root(stage_id) / attempt_id,
            prior_backend_session_ids=prior_sessions,
            recovery_from=latest.attempt_id,
        )
