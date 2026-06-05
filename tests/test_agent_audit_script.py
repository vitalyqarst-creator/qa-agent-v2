from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "skills" / "agent-architecture-auditor" / "scripts" / "audit_agent_architecture.py"


class AgentAuditScriptTests(unittest.TestCase):
    def run_script(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=str(cwd or ROOT_DIR),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_script_exists(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists())

    def test_script_runs_from_repo_root_without_arguments(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"summary"', result.stdout)
        self.assertIn("Agent architecture audit summary", result.stdout)

    def test_script_supports_json_output(self) -> None:
        result = self.run_script("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            {"summary", "findings", "duplication_map", "stale_items", "instruction_budgets", "task_start_routing", "checks"},
            set(payload),
        )
        severities = {item["severity"] for item in payload["findings"]}
        self.assertTrue(severities.issubset({"error", "warning", "info"}))
        self.assertIn("skills_count", payload["summary"])

    def test_script_supports_text_output(self) -> None:
        result = self.run_script("--text")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Agent architecture audit summary", result.stdout)
        self.assertIn("instruction budgets", result.stdout)
        self.assertIn("writer.initial_draft.simple", result.stdout)
        self.assertIn("task start routing", result.stdout)
        self.assertNotEqual("", result.stdout.strip())

    def test_script_can_write_json_report_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "audit.json"
            result = self.run_script("--json", "--output", str(output_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("summary", payload)

    def test_skill_and_reference_describe_script_contract(self) -> None:
        skill_content = (ROOT_DIR / "skills" / "agent-architecture-auditor" / "SKILL.md").read_text(encoding="utf-8")
        ref_content = (ROOT_DIR / "references" / "agent" / "audit-output-format.md").read_text(encoding="utf-8")
        self.assertIn("audit_agent_architecture.py", skill_content)
        self.assertIn("script-first", skill_content)
        self.assertIn("severity", ref_content.lower())
        self.assertIn("summary", ref_content)

    def test_synthetic_fixture_reports_known_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            (fixture_root / "skills" / "sample-skill" / "agents").mkdir(parents=True)
            (fixture_root / "references" / "agent").mkdir(parents=True)
            (fixture_root / "references" / "qa").mkdir(parents=True)

            (fixture_root / "AGENTS.md").write_text(
                dedent(
                    """
                    # Agent

                    ## Рабочий процесс

                    1. Найди документ.
                    2. Напиши кейсы.
                    3. Проверь их.
                    """
                ).strip() + "\n",
                encoding="utf-8",
            )
            (fixture_root / "skills" / "README.md").write_text("# Skills\n", encoding="utf-8")
            (fixture_root / "skills" / "sample-skill" / "SKILL.md").write_text(
                dedent(
                    """
                    ---
                    name: sample-skill
                    description: Test fixture.
                    ---

                    # Sample

                    ## Входы

                    - input

                    ## Выходы

                    - output

                    ## Ограничения

                    - none
                    """
                ).strip() + "\n",
                encoding="utf-8",
            )
            (fixture_root / "skills" / "sample-skill" / "agents" / "openai.yaml").write_text(
                "display_name: Sample\nshort_description: Sample\ndefault_prompt: Sample\n",
                encoding="utf-8",
            )

            result = self.run_script("--root", str(fixture_root), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            finding_ids = {item["id"] for item in payload["findings"]}
            self.assertIn("agents-procedural-workflow", finding_ids)


if __name__ == "__main__":
    unittest.main()
