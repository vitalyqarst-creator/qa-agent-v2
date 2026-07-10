"""Backend-independent contracts for staged writer/reviewer review cycles."""

from test_case_agent.review_cycle.contracts import (
    CONTRACT_VERSION,
    ArtifactRef,
    ContractValidationError,
    ExpectedOutput,
    StageInputManifest,
    StageResult,
    ensure_new_session_id,
)
from test_case_agent.review_cycle.transitions import TransitionDecision, resolve_transition
from test_case_agent.review_cycle.runtime import (
    BackendStageExecution,
    StageArtifactStore,
    StageAttemptPaths,
    StageBackend,
    StageRuntimeError,
    artifact_ref,
    load_manifest,
    load_result,
)
from test_case_agent.review_cycle.backends import FreshThreadSdkBackend, start_fresh_sdk_thread
from test_case_agent.review_cycle.attempts import (
    AttemptPlan,
    AttemptRecord,
    AttemptRecoveryError,
    StageAttemptLedger,
    format_attempt_id,
)
from test_case_agent.review_cycle.metrics import (
    StageMetrics,
    StageMetricsRecorder,
    build_stage_metrics,
    summarize_metrics,
)

__all__ = [
    "CONTRACT_VERSION",
    "ArtifactRef",
    "AttemptPlan",
    "AttemptRecord",
    "AttemptRecoveryError",
    "ContractValidationError",
    "ExpectedOutput",
    "FreshThreadSdkBackend",
    "StageInputManifest",
    "StageResult",
    "TransitionDecision",
    "BackendStageExecution",
    "StageArtifactStore",
    "StageAttemptLedger",
    "StageAttemptPaths",
    "StageBackend",
    "StageRuntimeError",
    "StageMetrics",
    "StageMetricsRecorder",
    "artifact_ref",
    "build_stage_metrics",
    "ensure_new_session_id",
    "format_attempt_id",
    "load_manifest",
    "load_result",
    "resolve_transition",
    "start_fresh_sdk_thread",
    "summarize_metrics",
]
