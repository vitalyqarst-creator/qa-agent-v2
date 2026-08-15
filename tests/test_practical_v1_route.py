from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT_DIR / "references" / "agent" / "practical-test-case-route-v1.md"


class PracticalV1RouteTests(unittest.TestCase):
    def test_default_route_preserves_design_before_test_case_order(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("source scope → matrix → independent matrix review", content)
        self.assertIn("Только после `matrix-accepted` writer создаёт тест-кейсы", content)
        self.assertIn("Отдельная верхнеуровневая Codex-сессия", content)

    def test_default_route_has_bounded_reviews_without_controller_artifacts(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("один раз исправляет", content)
        self.assertIn("`review-failed`", content)
        self.assertIn("Не создавай `workflow-state`, immutable manifest, attestation", content)

    def test_default_route_keeps_nonblocking_execution_limits_visible(self) -> None:
        content = ROUTE_PATH.read_text(encoding="utf-8")
        self.assertIn("`scope-clarification-requests.md`", content)
        self.assertIn("`needs-test-data`", content)
        self.assertIn("`candidate-ui-calibration`", content)
        self.assertIn("`blocked-observability`", content)


if __name__ == "__main__":
    unittest.main()
