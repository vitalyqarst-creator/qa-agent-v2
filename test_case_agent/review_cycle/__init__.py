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

__all__ = [
    "CONTRACT_VERSION",
    "ArtifactRef",
    "ContractValidationError",
    "ExpectedOutput",
    "FreshThreadSdkBackend",
    "StageInputManifest",
    "StageResult",
    "TransitionDecision",
    "BackendStageExecution",
    "StageArtifactStore",
    "StageAttemptPaths",
    "StageBackend",
    "StageRuntimeError",
    "artifact_ref",
    "ensure_new_session_id",
    "load_manifest",
    "load_result",
    "resolve_transition",
    "start_fresh_sdk_thread",
]
