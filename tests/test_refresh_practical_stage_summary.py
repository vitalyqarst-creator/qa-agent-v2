from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class RefreshPracticalStageSummaryTests(unittest.TestCase):
    def load_helper(self):
        module_path = ROOT_DIR / "scripts" / "refresh_practical_stage_summary.py"
        spec = importlib.util.spec_from_file_location(
            "refresh_practical_stage_summary_for_tests", module_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_summarize_validator_findings_ignores_summary_self_checks(self) -> None:
        helper = self.load_helper()

        result = helper.summarize_validator_findings(
            [
                {
                    "severity": "error",
                    "category": "practical-stage-summary",
                    "id": "practical-stage-summary-validator-warning-count-stale",
                },
                {
                    "severity": "warning",
                    "category": "coverage",
                    "id": "oracle-candidate-obligation-without-test-case",
                },
                {
                    "severity": "info",
                    "category": "source-quality",
                    "id": "source-quality-many-untitled-sections",
                },
            ]
        )

        self.assertEqual(result["validator_errors_count"], 0)
        self.assertEqual(result["validator_errors_evidence"], "not-applicable")
        self.assertEqual(result["validator_warnings_count"], 1)
        self.assertEqual(
            result["validator_warnings_evidence"],
            "oracle-candidate-obligation-without-test-case",
        )
        self.assertEqual(result["validator_info_count"], 1)
        self.assertEqual(result["validator_info_evidence"], "source-quality-many-untitled-sections")

    def test_validator_findings_breakdown_classifies_actionable_groups(self) -> None:
        helper = self.load_helper()

        result = helper.format_validator_findings_breakdown(
            [
                {
                    "severity": "warning",
                    "category": "test-cases",
                    "id": "test-case-non-atomic",
                },
                {
                    "severity": "error",
                    "category": "workflow",
                    "id": "workflow-state-stale",
                },
                {
                    "severity": "warning",
                    "category": "references",
                    "id": "writer-quality-gate-scoped-validator-profile-invalid",
                    "details": "profile path not found",
                },
                {
                    "severity": "warning",
                    "category": "source-quality",
                    "id": "old-source-quality-note",
                },
                {
                    "severity": "info",
                    "category": "test-cases",
                    "id": "ignored-info",
                },
            ]
        )

        self.assertEqual(
            result,
            "tc_quality=1; process_artifact=1; validator_path_resolution=1; unrelated_repo=1",
        )

    def test_detect_git_persistence_reports_gitignored_summary(self) -> None:
        helper = self.load_helper()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            (root / ".gitignore").write_text("fts/*\n", encoding="utf-8")
            summary = (
                root
                / "fts"
                / "Partners"
                / "Partners-v1"
                / "work"
                / "practical-stage-summary.md"
            )
            summary.parent.mkdir(parents=True)
            summary.write_text("# Practical Stage Summary\n", encoding="utf-8")

            result = helper.detect_git_persistence(root, summary)

        self.assertEqual(result.value, "ignored-by-git")
        self.assertIn(".gitignore", result.evidence)
        self.assertIn("fts/*", result.evidence)

    def test_build_refresh_uses_nearest_ft_package_root_as_primary_validator_root(self) -> None:
        helper = self.load_helper()

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            ft_root = repo_root / "fts" / "Partners" / "Partners-v1"
            summary = ft_root / "work" / "practical-stage-summary.md"
            (ft_root / "test-cases").mkdir(parents=True)
            summary.parent.mkdir(parents=True)
            summary.write_text("# Practical Stage Summary\n", encoding="utf-8")
            validate_roots: list[Path] = []
            original_validate = helper.artifact_validator.validate
            original_detect_git_persistence = helper.detect_git_persistence

            def fake_validate(root: Path):
                validate_roots.append(root.resolve())
                return {"findings": []}

            helper.artifact_validator.validate = fake_validate
            helper.detect_git_persistence = lambda root, summary_path: helper.GitPersistence(
                "not-applicable",
                "stubbed",
            )
            try:
                refresh = helper.build_refresh(
                    repo_root,
                    Path("fts") / "Partners" / "Partners-v1" / "work" / "practical-stage-summary.md",
                )
            finally:
                helper.artifact_validator.validate = original_validate
                helper.detect_git_persistence = original_detect_git_persistence

        self.assertEqual([ft_root.resolve()], validate_roots)
        self.assertIn("--root fts/Partners/Partners-v1 --json", refresh.validator_primary_command)
        self.assertEqual("python scripts/validate_agent_artifacts.py --root . --json", refresh.validator_supplementary_command)

    def test_format_field_rows_outputs_copyable_summary_rows(self) -> None:
        helper = self.load_helper()
        refresh = helper.SummaryRefresh(
            validator_primary_command="python scripts/validate_agent_artifacts.py --root fts/Partners/Partners-v1 --json",
            validator_primary_root="C:/repo/fts/Partners/Partners-v1",
            validator_supplementary_command="python scripts/validate_agent_artifacts.py --root . --json",
            validator_findings_breakdown="tc_quality=0; process_artifact=3; validator_path_resolution=0; unrelated_repo=0",
            validator_errors_count=0,
            validator_errors_evidence="not-applicable",
            validator_warnings_count=3,
            validator_warnings_evidence="warning-a; warning-b",
            validator_info_count=4,
            validator_info_evidence="info-a; info-b",
            git_persistence="ignored-by-git",
            git_persistence_evidence=".gitignore:1:fts/* fts/Partners/Partners-v1",
        )

        output = helper.format_field_rows(refresh)

        self.assertIn("| validator_primary_command | `python scripts/validate_agent_artifacts.py --root fts/Partners/Partners-v1 --json` |", output)
        self.assertIn("| validator_supplementary_command | `python scripts/validate_agent_artifacts.py --root . --json` |", output)
        self.assertIn("| validator_findings_breakdown | `tc_quality=0; process_artifact=3; validator_path_resolution=0; unrelated_repo=0` |", output)
        self.assertIn("| validator_errors_count | `0` |", output)
        self.assertIn("| validator_warnings_count | `3` |", output)
        self.assertIn("| validator_info_count | `4` |", output)
        self.assertIn("| git_persistence | `ignored-by-git` |", output)
        self.assertIn("| source_row_counts | `not-applicable` |", output)
        self.assertIn("warning-a; warning-b", output)
        self.assertIn("info-a; info-b", output)

    def test_scope_fields_are_printed_only_when_scope_ids_are_supplied(self) -> None:
        helper = self.load_helper()
        refresh = helper.SummaryRefresh(
            validator_primary_command="command",
            validator_primary_root="C:/repo/fts/Sample",
            validator_supplementary_command="not-run",
            validator_findings_breakdown="tc_quality=0; process_artifact=0; validator_path_resolution=0; unrelated_repo=0",
            validator_errors_count=3,
            validator_errors_evidence="scope-a; other-b",
            validator_warnings_count=0,
            validator_warnings_evidence="not-applicable",
            validator_info_count=0,
            validator_info_evidence="not-applicable",
            git_persistence="tracked",
            git_persistence_evidence="git ls-files",
            validator_scope_errors_count=1,
            validator_scope_errors_evidence="scope-a",
            validator_external_errors_count=2,
            validator_external_errors_evidence="other-b; other-c",
        )

        output = helper.format_field_rows(refresh)

        self.assertIn("| validator_scope_errors_count | `1` |", output)
        self.assertIn("| validator_external_errors_count | `2` |", output)


if __name__ == "__main__":
    unittest.main()
