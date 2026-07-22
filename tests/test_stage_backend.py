from __future__ import annotations

import unittest

from test_case_agent.lean_v2.backend import (
    CodexExecStageBackend as LegacyCodexExecStageBackend,
)
from test_case_agent.lean_v2.backend import LeanV2BackendError
from test_case_agent.lean_v2.backend import StageResult as LegacyStageResult
from test_case_agent.stage_backend import (
    CodexExecStageBackend,
    StageBackendError,
    StageResult,
)


class StageBackendCompatibilityTests(unittest.TestCase):
    def test_legacy_backend_exports_are_identity_preserving_aliases(self) -> None:
        self.assertIs(CodexExecStageBackend, LegacyCodexExecStageBackend)
        self.assertIs(StageResult, LegacyStageResult)
        self.assertIs(StageBackendError, LeanV2BackendError)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
