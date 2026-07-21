from __future__ import annotations

import subprocess
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from test_case_agent.review_cycle import exec_backend
from test_case_agent.review_cycle.exec_backend import (
    ExecCapability,
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    PLUGIN_ISOLATION_DISABLE_FEATURES,
    plugin_isolation_exec_args,
    probe_exec_capability,
    resolve_verified_exec_capability,
    tool_free_exec_args,
)


class ExecBackendTests(unittest.TestCase):
    @staticmethod
    def _capability(
        command: str,
        *,
        verified: bool,
        error: str = "",
    ) -> ExecCapability:
        return ExecCapability(
            command=command,
            available=verified,
            verified=verified,
            returncode=0 if verified else None,
            duration_ms=3,
            missing_flags=() if verified else ("--json",),
            error=error,
            version="codex-cli test" if verified else "",
            resolved_command=str(Path(command).resolve()),
        )

    def test_resolver_probes_until_first_verified_and_pins_executable(self) -> None:
        calls: list[tuple[str, tuple[str, ...]]] = []

        def probe(command: str, **kwargs: object) -> ExecCapability:
            calls.append((command, tuple(kwargs["additional_required_flags"])))
            return self._capability(
                command,
                verified=command == "second.exe",
                error="access denied" if command == "first.exe" else "",
            )

        resolution = resolve_verified_exec_capability(
            candidates=("first.exe", "second.exe", "third.exe"),
            additional_required_flags=("--image",),
            required_disable_features=PLUGIN_ISOLATION_DISABLE_FEATURES,
            probe=probe,
        )

        self.assertTrue(resolution.verified)
        self.assertEqual(str(Path("second.exe").resolve()), resolution.selected_executable)
        self.assertEqual(["first.exe", "second.exe"], [item[0] for item in calls])
        self.assertIn("--image", calls[0][1])
        self.assertIn("--disable", calls[0][1])
        self.assertGreaterEqual(resolution.total_duration_ms, 0)
        self.assertEqual(6, sum(item.duration_ms for item in resolution.probes))

    def test_explicit_command_is_strict_and_has_no_fallback(self) -> None:
        calls: list[str] = []

        def probe(command: str, **_kwargs: object) -> ExecCapability:
            calls.append(command)
            return self._capability(command, verified=False, error="denied")

        resolution = resolve_verified_exec_capability(
            "explicit.exe",
            candidates=("working.exe",),
            probe=probe,
        )

        self.assertFalse(resolution.verified)
        self.assertEqual(["explicit.exe"], calls)

    def test_disable_features_own_both_probe_requirement_and_command_args(self) -> None:
        observed_flags: tuple[str, ...] = ()

        def probe(command: str, **kwargs: object) -> ExecCapability:
            nonlocal observed_flags
            observed_flags = tuple(kwargs["additional_required_flags"])
            return self._capability(command, verified=True)

        resolution = resolve_verified_exec_capability(
            candidates=("codex.exe",),
            required_disable_features=("remote_plugin", "plugins", "apps", "apps"),
            probe=probe,
        )

        self.assertIn("--disable", observed_flags)
        self.assertEqual(
            (
                "--disable", "remote_plugin",
                "--disable", "plugins",
                "--disable", "apps",
            ),
            resolution.disable_args,
        )

    def test_shared_probe_budget_stops_before_next_real_probe(self) -> None:
        calls: list[str] = []

        def slow_probe(command: str, **_kwargs: object) -> ExecCapability:
            calls.append(command)
            time.sleep(0.02)
            return self._capability(command, verified=False, error="failed")

        resolution = resolve_verified_exec_capability(
            candidates=("first.exe", "second.exe"),
            total_timeout_seconds=0.005,
            probe=slow_probe,
        )

        self.assertFalse(resolution.verified)
        self.assertEqual(["first.exe"], calls)
        self.assertIn("budget exhausted", resolution.probes[-1].error)

    def test_unbounded_probe_mode_probes_all_candidates_without_deadline(self) -> None:
        calls: list[tuple[str, object]] = []

        def probe(command: str, **kwargs: object) -> ExecCapability:
            calls.append((command, kwargs["timeout_seconds"]))
            return self._capability(
                command,
                verified=command == "second.exe",
                error="failed" if command == "first.exe" else "",
            )

        resolution = resolve_verified_exec_capability(
            candidates=("first.exe", "second.exe"),
            total_timeout_seconds=None,
            probe=probe,
        )

        self.assertTrue(resolution.verified)
        self.assertEqual(
            [("first.exe", None), ("second.exe", None)],
            calls,
        )

    def test_candidate_aliases_are_deduplicated_by_resolved_path(self) -> None:
        with patch.object(
            exec_backend,
            "_resolved_command",
            return_value=str(Path("same-codex.exe").resolve()),
        ):
            candidates = exec_backend._deduplicate_candidates(
                ("codex", str(Path("same-codex.exe").resolve()))
            )

        self.assertEqual(("codex",), candidates)

    def test_capability_probe_pins_nonempty_version(self) -> None:
        help_text = " ".join(exec_backend.REQUIRED_EXEC_HELP_FLAGS)
        results = [
            subprocess.CompletedProcess([], 0, help_text, ""),
            subprocess.CompletedProcess([], 0, "codex-cli 1.2.3\n", ""),
        ]
        with (
            patch.object(exec_backend, "_resolved_command", return_value="C:/codex.exe"),
            patch.object(exec_backend.subprocess, "run", side_effect=results),
        ):
            capability = probe_exec_capability("codex")

        self.assertTrue(capability.verified)
        self.assertEqual("codex-cli 1.2.3", capability.version)
        self.assertEqual("C:/codex.exe", capability.resolved_command)

    def test_capability_probe_parses_each_disable_feature_directly(self) -> None:
        help_text = " ".join((*exec_backend.REQUIRED_EXEC_HELP_FLAGS, "--disable"))
        results = [
            subprocess.CompletedProcess(
                [],
                0,
                "remote_plugin stable true\nplugins stable true\napps stable true\n",
                "",
            ),
            subprocess.CompletedProcess([], 0, help_text, ""),
            subprocess.CompletedProcess([], 0, "codex-cli 1.2.3\n", ""),
        ]
        with (
            patch.object(exec_backend, "_resolved_command", return_value="C:/codex.exe"),
            patch.object(exec_backend.subprocess, "run", side_effect=results) as runner,
        ):
            capability = probe_exec_capability(
                "codex",
                required_disable_features=("remote_plugin", "plugins", "apps"),
            )

        self.assertTrue(capability.verified)
        self.assertEqual(["C:/codex.exe", "features", "list"], runner.call_args_list[0].args[0])
        command = runner.call_args_list[1].args[0]
        self.assertEqual(3, command.count("--disable"))
        self.assertIn("remote_plugin", command)
        self.assertIn("plugins", command)
        self.assertIn("apps", command)

    def test_capability_probe_rejects_unknown_disable_feature(self) -> None:
        feature_result = subprocess.CompletedProcess(
            [],
            0,
            "remote_plugin stable true\nplugins stable true\n",
            "",
        )
        with (
            patch.object(exec_backend, "_resolved_command", return_value="C:/codex.exe"),
            patch.object(exec_backend.subprocess, "run", return_value=feature_result) as runner,
        ):
            capability = probe_exec_capability(
                "codex",
                required_disable_features=("remote_plugin", "apps"),
            )

        self.assertFalse(capability.verified)
        self.assertIn("unsupported disable features: apps", capability.error)
        runner.assert_called_once()

    def test_verified_resolution_requires_absolute_pin_and_version(self) -> None:
        def incomplete_probe(command: str, **_kwargs: object) -> ExecCapability:
            return ExecCapability(
                command=command,
                available=True,
                verified=True,
                returncode=0,
                duration_ms=1,
                missing_flags=(),
                resolved_command="relative-codex.exe",
                version="",
            )

        resolution = resolve_verified_exec_capability(
            candidates=("codex",),
            probe=incomplete_probe,
        )

        self.assertFalse(resolution.verified)
        self.assertIn("non-empty version", resolution.probes[0].error)

    def test_plugin_isolation_args_are_ordered_and_direct(self) -> None:
        self.assertEqual(
            (
                "--disable", "remote_plugin",
                "--disable", "plugins",
                "--disable", "apps",
            ),
            plugin_isolation_exec_args(),
        )

    def test_tool_free_args_disable_local_and_external_model_tools(self) -> None:
        args = tool_free_exec_args()

        self.assertEqual(
            len(MODEL_TOOL_ISOLATION_DISABLE_FEATURES),
            args.count("--disable"),
        )
        for feature in (
            "remote_plugin",
            "shell_tool",
            "browser_use",
            "computer_use",
            "multi_agent",
        ):
            self.assertIn(feature, args)


if __name__ == "__main__":
    unittest.main()
