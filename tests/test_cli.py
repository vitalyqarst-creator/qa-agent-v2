from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from test_case_agent.cli import build_parser, main
from test_case_agent.source_qualified_run import SourceQualifiedRunError


class CliTests(unittest.TestCase):
    def test_public_parser_exposes_only_run(self) -> None:
        parser = build_parser()
        help_text = parser.format_help()

        self.assertIn("{run}", help_text)
        for forbidden in (
            "scope-compile",
            "graph-build",
            "context-build",
            "iterate",
            "quality-proof",
        ):
            self.assertNotIn(forbidden, help_text)
            with self.subTest(command=forbidden), redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "2"):
                    parser.parse_args([forbidden])

    def test_run_parser_has_only_public_inputs(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "--repo-root",
                "repo",
                "run",
                "--config",
                "run-config.json",
                "--output-dir",
                "attempt-001",
            ]
        )

        self.assertEqual("run", args.command)
        self.assertEqual(Path("repo"), args.repo_root)
        self.assertEqual(Path("run-config.json"), args.config)
        self.assertEqual(Path("attempt-001"), args.output_dir)
        self.assertEqual(
            {"command", "config", "handler", "output_dir", "repo_root"},
            set(vars(args)),
        )

        with redirect_stderr(io.StringIO()), self.assertRaisesRegex(SystemExit, "2"):
            parser.parse_args(
                [
                    "run",
                    "--config",
                    "run-config.json",
                    "--output-dir",
                    "attempt-001",
                    "--reviewer-response",
                    "offline.json",
                ]
            )

    def test_main_returns_public_run_exit_code(self) -> None:
        with patch("test_case_agent.cli._run", return_value=1):
            self.assertEqual(
                1,
                main(
                    [
                        "run",
                        "--config",
                        "config.json",
                        "--output-dir",
                        "run-001",
                    ]
                ),
            )

    def test_main_separates_contract_infrastructure_and_internal_errors(self) -> None:
        scenarios = (
            (
                SourceQualifiedRunError("safe-contract", "safe contract detail"),
                2,
                "contract-error",
            ),
            (OSError("disk unavailable"), 3, "infrastructure-error"),
            (RuntimeError("SECRET-INTERNAL-DETAIL"), 70, "internal-error"),
        )

        for error, expected_code, marker in scenarios:
            with self.subTest(error=type(error).__name__), patch(
                "test_case_agent.cli._run",
                side_effect=error,
            ), redirect_stderr(io.StringIO()) as stderr:
                exit_code = main(
                    [
                        "run",
                        "--config",
                        "config.json",
                        "--output-dir",
                        "run-001",
                    ]
                )

                self.assertEqual(expected_code, exit_code)
                self.assertIn(marker, stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())
                if isinstance(error, RuntimeError):
                    self.assertIn("RuntimeError", stderr.getvalue())
                    self.assertNotIn("SECRET-INTERNAL-DETAIL", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
