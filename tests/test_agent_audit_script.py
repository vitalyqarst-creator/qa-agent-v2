from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    ROOT_DIR
    / "skills"
    / "agent-architecture-auditor"
    / "scripts"
    / "audit_agent_architecture.py"
)
RUNTIME_SKILLS = (
    "ft-source-locator",
    "ft-scope-analyzer",
    "ft-test-case-writer",
    "ft-test-case-reviewer",
)


class AgentAuditScriptTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def create_runtime_fixture(self, root: Path) -> None:
        (root / "references" / "runtime").mkdir(parents=True)
        (root / "scripts").mkdir()
        (root / "tests").mkdir()
        (root / "AGENTS.md").write_text(
            "# Agent\n\nUse [shared rules](references/runtime/shared.md).\n",
            encoding="utf-8",
        )
        (root / "references" / "runtime" / "shared.md").write_text(
            "# Shared\n",
            encoding="utf-8",
        )
        for skill_name in RUNTIME_SKILLS:
            skill_dir = root / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                (
                    "---\n"
                    f"name: {skill_name}\n"
                    "description: Runtime fixture.\n"
                    "---\n\n"
                    "# Skill\n\n"
                    "Use [shared rules](../../references/runtime/shared.md).\n"
                ),
                encoding="utf-8",
            )
        (root / "scripts" / "validate_runtime_tree.py").write_text(
            "def validate(root):\n    return []\n",
            encoding="utf-8",
        )
        (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (root / "tests" / "test_runtime_contract.py").write_text(
            "import unittest\n\nclass ContractTest(unittest.TestCase):\n"
            "    def test_green(self):\n        self.assertTrue(True)\n",
            encoding="utf-8",
        )

    def test_script_exists(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists())

    def test_valid_runtime_profile_returns_factual_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.create_runtime_fixture(root)
            result = self.run_script(
                "--root", str(root), "--profile", "runtime-v1", "--json", "--fail-on", "error"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual("runtime-v1", payload["profile"]["resolved"])
            self.assertTrue(payload["summary"]["valid"])
            self.assertEqual(4, payload["summary"]["skills_count"])
            self.assertEqual([], payload["findings"])
            self.assertEqual(4, len(payload["instruction_contexts"]))
            self.assertEqual("runtime-contract-tests", payload["skipped_checks"][0]["id"])

    def test_unsupported_tree_fails_without_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.run_script(
                "--root", tmp_dir, "--json", "--fail-on", "error"
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertIsNone(payload["profile"]["resolved"])
            self.assertEqual(
                "unsupported-architecture-profile", payload["findings"][0]["id"]
            )

    def test_broken_reference_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.create_runtime_fixture(root)
            (root / "skills" / "ft-source-locator" / "SKILL.md").write_text(
                "---\nname: ft-source-locator\ndescription: Fixture.\n---\n\n"
                "[missing](../../references/runtime/missing.md)\n",
                encoding="utf-8",
            )
            result = self.run_script(
                "--root", str(root), "--json", "--fail-on", "error"
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertTrue(
                any(item["id"].startswith("broken-reference-") for item in payload["findings"])
            )

    def test_stale_marker_is_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.create_runtime_fixture(root)
            agents = root / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8") + "Use practical route v0.6.\n",
                encoding="utf-8",
            )
            result = self.run_script(
                "--root", str(root), "--json", "--fail-on", "warning"
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(1, payload["summary"]["warnings_count"])
            self.assertEqual("legacy-marker", payload["stale_items"][0]["type"])

    def test_optional_runtime_tests_are_executed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            self.create_runtime_fixture(root)
            result = self.run_script(
                "--root", str(root), "--json", "--with-tests", "--fail-on", "error"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            statuses = {item["id"]: item["status"] for item in payload["checks"]}
            self.assertEqual("pass", statuses["runtime-contract-tests"])
            self.assertEqual([], payload["skipped_checks"])

    def test_skill_describes_dev_only_runtime_profile(self) -> None:
        content = (
            ROOT_DIR / "skills" / "agent-architecture-auditor" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("script-first workflow", content)
        self.assertIn("--root <runtime-v1-root>", content)
        self.assertIn("Dev-only", content)
        self.assertIn("legacy/full", content)

    def test_architecture_suite_requires_explicit_runtime_root(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "run_tests.py"), "--suite", "architecture"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("requires --architecture-root", result.stderr)


if __name__ == "__main__":
    unittest.main()
