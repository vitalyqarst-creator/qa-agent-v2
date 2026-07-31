from __future__ import annotations

import os
import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest.mock import patch

from scripts.dev_route_guard import (
    DEV_ROUTE_ENV,
    DevRouteDisabledError,
    require_dev_routes_enabled,
)
from scripts import (
    run_semantic_design_qualification,
    run_standard_production_iteration,
    run_standard_scope_bridge,
    start_full_process_observation,
)


class ProductionRouteGuardTests(unittest.TestCase):
    def test_dev_routes_are_disabled_without_explicit_opt_in(self) -> None:
        with patch.dict(os.environ, {DEV_ROUTE_ENV: ""}, clear=False):
            with self.assertRaises(DevRouteDisabledError):
                require_dev_routes_enabled("semantic bridge")

    def test_dev_routes_can_be_enabled_only_by_explicit_env(self) -> None:
        with patch.dict(os.environ, {DEV_ROUTE_ENV: "1"}, clear=False):
            require_dev_routes_enabled("semantic bridge")

    def test_development_entrypoints_fail_before_argparse(self) -> None:
        entrypoints = (
            start_full_process_observation.main,
            run_standard_scope_bridge.main,
            run_standard_production_iteration.main,
            run_semantic_design_qualification.main,
        )
        with patch.dict(os.environ, {DEV_ROUTE_ENV: ""}, clear=False):
            for entrypoint in entrypoints:
                stderr = StringIO()
                with redirect_stderr(stderr):
                    self.assertEqual(2, entrypoint([]), entrypoint)
                self.assertIn("disabled in the production agent profile", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
