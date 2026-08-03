"""Compatibility imports for the legacy lean-v2 workflow.

New production code must import the neutral stage backend directly from
``test_case_agent.stage_backend``.
"""

from test_case_agent.stage_backend import (
    CodexExecStageBackend,
    StageBackendError,
    StageResult,
)

# Keep the established exception import working for legacy callers. This is an
# alias, not a subclass, so both names identify the same backend failure type.
LeanV2BackendError = StageBackendError

__all__ = [
    "CodexExecStageBackend",
    "LeanV2BackendError",
    "StageBackendError",
    "StageResult",
]
