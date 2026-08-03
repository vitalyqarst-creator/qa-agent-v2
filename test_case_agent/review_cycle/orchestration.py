from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from test_case_agent.review_cycle.contracts import CONTRACT_VERSION, StageInputManifest, StageResult
from test_case_agent.review_cycle.metrics import StageMetrics, StageMetricsRecorder, build_stage_metrics
from test_case_agent.review_cycle.runtime import (
    BackendStageExecution,
    StageArtifactStore,
    StageAttemptPaths,
    StageRuntimeError,
)


RESULT_STATUS = {
    "draft-ready": "completed",
    "accepted": "completed",
    "changes-required": "changes-required",
    "blocked": "blocked",
}


@dataclass(frozen=True)
class CompletedStage:
    result: StageResult
    result_path: Path
    metrics: StageMetrics
    metrics_path: Path


class StageCompletionCoordinator:
    def __init__(self, repo_root: Path, cycle_root: Path):
        self.repo_root = repo_root.resolve()
        self.cycle_root = cycle_root.resolve()
        self.store = StageArtifactStore(self.repo_root)
        self.metrics = StageMetricsRecorder(self.cycle_root)

    def complete(
        self,
        manifest: StageInputManifest,
        execution: BackendStageExecution,
        *,
        outcome: str,
        blocking_reasons: Sequence[str] = (),
        prior_backend_session_ids: Sequence[str] = (),
    ) -> CompletedStage:
        manifest.validate()
        execution.validate()
        if outcome not in RESULT_STATUS:
            raise StageRuntimeError(f"unsupported stage outcome: {outcome}")
        try:
            self.store.verify_manifest_inputs(manifest)
        except StageRuntimeError:
            if outcome != "blocked":
                raise
            # Preserve immutable failure evidence when the blocker itself is an input mutation.
            # A blocked result cannot advance state or authorize promotion.
        backend_session_id = execution.backend_session_id
        if outcome == "blocked" and backend_session_id in prior_backend_session_ids:
            backend_session_id = ""
        outputs = self.store.collect_declared_outputs(
            manifest,
            require_all=outcome != "blocked",
        )
        result = StageResult(
            contract_version=CONTRACT_VERSION,
            cycle_id=manifest.cycle_id,
            stage_id=manifest.stage_id,
            attempt_id=manifest.attempt_id,
            session_id=manifest.session_id,
            backend_session_id=backend_session_id,
            role=manifest.role,
            scenario=manifest.scenario,
            input_digest=manifest.input_digest,
            status=RESULT_STATUS[outcome],
            outcome=outcome,
            output_artifacts=outputs,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            duration_ms=execution.duration_ms,
            exit_code=execution.exit_code,
            timed_out=execution.timed_out,
            blocking_reasons=tuple(blocking_reasons),
        )
        paths = StageAttemptPaths.from_manifest(self.repo_root, manifest)
        try:
            result_path = self.store.write_result(
                paths,
                manifest,
                result,
                prior_backend_session_ids=tuple(prior_backend_session_ids),
            )
            metrics = build_stage_metrics(
                manifest,
                result,
                execution,
                repo_root=self.repo_root,
            )
            metrics_path = self.metrics.record(paths.attempt_root, metrics)
        except (StageRuntimeError, ValueError) as exc:
            raise StageRuntimeError(f"stage completion evidence is invalid: {exc}") from exc
        return CompletedStage(
            result=result,
            result_path=result_path,
            metrics=metrics,
            metrics_path=metrics_path,
        )
