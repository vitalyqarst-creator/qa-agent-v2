from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_writer_quality_gate_split",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WriterQualityGateSplitArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def make_package(self) -> tuple[Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "fts" / "Sample"
        tc_dir = root / "test-cases"
        tc_dir.mkdir(parents=True)
        tc_path = tc_dir / "9.1-sample.md"
        tc_path.write_text(
            "\n".join(
                [
                    "# 9.1 Sample",
                    "",
                    "## TC-SAMPLE-001",
                    "**Название:** Проверка отображения пункта меню",
                    "**Тип:** Positive",
                    "**Приоритет:** High",
                    "**package_id:** `WP-01`",
                    "**Трассировка:** `SRC-001`; `ATOM-001`",
                    "**Статус исполнения:** `ready`",
                    "",
                    "**Цель:** Проверить отображение пункта меню.",
                    "",
                    "**Предусловия:**",
                    "1. Войти в систему.",
                    "",
                    "**Тестовые данные:** Не требуются.",
                    "",
                    "**Шаги:**",
                    "1. Открыть меню.",
                    "2. Проверить наличие пункта.",
                    "",
                    "**Итоговый ожидаемый результат:** Пункт меню отображается.",
                    "",
                    "**Постусловия:** Не требуются.",
                    "",
                    "**Ссылка на ФТ:** `9.1`; `SRC-001`.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        design_dir = root / "work" / "test-design" / "9.1-sample"
        design_dir.mkdir(parents=True)
        return root, tc_path, design_dir

    def write_valid_gate(self, design_dir: Path) -> None:
        (design_dir / "validator.json").write_text(
            json.dumps(
                {
                    "passed": True,
                    "validator": "validate_agent_artifacts.py",
                    "findings": [],
                }
            ),
            encoding="utf-8",
        )
        rows = [
            "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for item in sorted(self.validator.WRITER_QUALITY_GATE_REQUIRED_ITEMS):
            evidence = {
                "scoped-validator-findings": "`validator.json`",
                "source-obligation-completeness": "`source-row-inventory.md` и `test-design-matrix.md` сопоставлены.",
                "expected-result-singularity": "`test-cases/9.1-sample.md`: `TC-SAMPLE-001`.",
                "creation-form-isolation-coverage": "`test-design-matrix.md`: `TC-SAMPLE-001`; создание независимого объекта не применимо: `not_applicable:SRC-001`.",
            }.get(item, "checked")
            rows.append(f"| `{item}` | `pass` | {evidence} | `WP-01` | `none_required:pass` | `no` |")
        (design_dir / "writer-quality-gate.md").write_text(
            "# Writer Quality Gate\n\n"
            f"**Версия контракта:** `{self.validator.WRITER_QUALITY_GATE_CONTRACT_VERSION}`\n\n"
            + "\n".join(rows)
            + "\n",
            encoding="utf-8",
        )

    def finding_ids_for_test_case(self, root: Path, tc_path: Path) -> set[str]:
        findings, _ = self.validator.validate_test_case_file(tc_path, root)
        return {finding.id for finding in findings}

    def test_split_writer_quality_gate_satisfies_test_case_validator(self) -> None:
        root, tc_path, design_dir = self.make_package()
        (design_dir / "package-test-design-plan.md").write_text(
            "# Package Test Design Plan\n\n| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| `D-001` | `WP-01` | `menu` | `SRC-001` | `ATOM-001` | `check menu` | `positive` | `source` | `n/a` | `menu visible` | `FT` | `TC-SAMPLE-001` | `covered` |\n",
            encoding="utf-8",
        )
        self.write_valid_gate(design_dir)

        ids = self.finding_ids_for_test_case(root, tc_path)

        self.assertNotIn("writer-quality-gate-missing", ids)
        self.assertNotIn("internal-diagnostic-section-in-production-testcases", ids)

    def test_creation_form_isolation_row_is_required(self) -> None:
        root, _, design_dir = self.make_package()
        self.write_valid_gate(design_dir)
        gate_path = design_dir / "writer-quality-gate.md"
        gate_path.write_text(
            "\n".join(
                line
                for line in gate_path.read_text(encoding="utf-8").splitlines()
                if "creation-form-isolation-coverage" not in line
            )
            + "\n",
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_writer_quality_gate(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            root,
        )

        self.assertIn(
            "writer-quality-gate-missing-required-items",
            {finding.id for finding in findings},
        )

    def test_current_gate_contract_and_semantic_evidence_are_required(self) -> None:
        root, _, design_dir = self.make_package()
        self.write_valid_gate(design_dir)
        gate_path = design_dir / "writer-quality-gate.md"
        invalid_content = gate_path.read_text(encoding="utf-8").replace(
            f"**Версия контракта:** `{self.validator.WRITER_QUALITY_GATE_CONTRACT_VERSION}`\n\n",
            "",
        ).replace(
            "`test-design-matrix.md`: `TC-SAMPLE-001`; создание независимого объекта не применимо: `not_applicable:SRC-001`.",
            "checked",
        )
        gate_path.write_text(invalid_content, encoding="utf-8")

        findings, _ = self.validator.validate_writer_quality_gate(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            root,
        )

        ids = {finding.id for finding in findings}
        self.assertIn("writer-quality-gate-contract-version-missing", ids)
        self.assertIn("writer-quality-gate-semantic-evidence-insufficient", ids)

    def test_stale_gate_contract_requires_real_revalidation(self) -> None:
        root, _, design_dir = self.make_package()
        self.write_valid_gate(design_dir)
        gate_path = design_dir / "writer-quality-gate.md"
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace(
                self.validator.WRITER_QUALITY_GATE_CONTRACT_VERSION,
                "writer-quality-gate-v1",
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_writer_quality_gate(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            root,
        )

        self.assertIn(
            "writer-quality-gate-contract-version-stale",
            {finding.id for finding in findings},
        )

    def test_recheck_history_cannot_repeat_a_gate_item(self) -> None:
        root, _, design_dir = self.make_package()
        self.write_valid_gate(design_dir)
        gate_path = design_dir / "writer-quality-gate.md"
        with gate_path.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n## Повторная проверка\n\n"
                "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                "| `expected-result-singularity` | `pass` | `test-cases/9.1-sample.md`: `TC-SAMPLE-001`. | `WP-01` | `none_required:pass` | `no` |\n"
            )

        findings, _ = self.validator.validate_writer_quality_gate(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            root,
        )

        self.assertIn(
            "writer-quality-gate-duplicate-item-rows",
            {finding.id for finding in findings},
        )

    def test_package_relative_scoped_profile_resolves_from_package_and_repo_root(self) -> None:
        root, _, design_dir = self.make_package()
        repo_root = root.parents[1]
        profile_path = (
            root
            / "work"
            / "stage-handoffs"
            / "01-sample"
            / "outputs"
            / "scoped-validator-profile.writer-r1.json"
        )
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(
            json.dumps(
                {
                    "command": "python scripts/validate_agent_artifacts.py --root fts/Sample --json",
                    "generated_by": "codex_review_cycle_runner",
                    "scope_slug": "9.1-sample",
                    "canonical_test_cases": "test-cases/9.1-sample.md",
                    "test_design_dir": "work/test-design/9.1-sample",
                    "current_scope_findings": [],
                    "unresolved_warning_error_count": 0,
                }
            ),
            encoding="utf-8",
        )
        package_relative_profile = "work/stage-handoffs/01-sample/outputs/scoped-validator-profile.writer-r1.json"
        gate_path = design_dir / "writer-quality-gate.md"
        gate_path.write_text(
            "\n".join(
                [
                    "# Writer Quality Gate",
                    "",
                    "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |",
                    "| --- | --- | --- | --- | --- | --- |",
                    f"| `scoped-validator-findings` | `pass` | `{package_relative_profile}` | `WP-01` | `none_required:pass` | `no` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        package_root_issues, _ = self.validator.validate_writer_quality_gate_scoped_validator_profile(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            root,
        )
        repo_root_issues, _ = self.validator.validate_writer_quality_gate_scoped_validator_profile(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            repo_root,
        )

        self.assertEqual([], package_root_issues)
        self.assertEqual([], repo_root_issues)

    def test_embedded_writer_quality_gate_does_not_satisfy_production_validator(self) -> None:
        root, tc_path, _ = self.make_package()
        embedded_gate = (
            "\n## Package Test Design Plan\n\n"
            "| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| `D-001` | `WP-01` | `menu` | `SRC-001` | `ATOM-001` | `check menu` | `positive` | `source` | `n/a` | `menu visible` | `FT` | `TC-SAMPLE-001` | `covered` |\n"
            "\n## Writer Quality Gate\n\n"
            "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| `package-ready` | `pass` | checked | `WP-01` | `none_required:pass` | `no` |\n"
        )
        tc_path.write_text(tc_path.read_text(encoding="utf-8") + embedded_gate, encoding="utf-8")

        ids = self.finding_ids_for_test_case(root, tc_path)

        self.assertIn("writer-quality-gate-missing", ids)
        self.assertIn("internal-diagnostic-section-in-production-testcases", ids)

    def test_embedded_split_design_sections_dirty_production_test_cases(self) -> None:
        root, tc_path, design_dir = self.make_package()
        (design_dir / "coverage-gaps.md").write_text(
            "# Coverage Gaps\n\n"
            "| gap_id | source_ref | status | handling |\n"
            "| --- | --- | --- | --- |\n"
            "| `GAP-001` | `SRC-001` | `closed` | `not_applicable:covered` |\n",
            encoding="utf-8",
        )
        tc_path.write_text(
            tc_path.read_text(encoding="utf-8")
            + "\n## Coverage Gaps\n\n"
            + "| gap_id | source_ref | status | handling |\n"
            + "| --- | --- | --- | --- |\n"
            + "| `GAP-001` | `SRC-001` | `closed` | `not_applicable:covered` |\n"
            + "\n## Writer Self-Check\n\n"
            + "- checked\n",
            encoding="utf-8",
        )

        ids = self.finding_ids_for_test_case(root, tc_path)

        self.assertIn("internal-diagnostic-section-in-production-testcases", ids)
        self.assertIn("test-case-split-artifact-duplicated-sections", ids)

    def test_rejects_pass_row_substituted_by_reviewer_finding(self) -> None:
        root, _, design_dir = self.make_package()
        gate_path = design_dir / "writer-quality-gate.md"
        gate_path.write_text(
            "\n".join(
                [
                    "# Writer Quality Gate",
                    "",
                    "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| `step-executability` | `pass` | Дефект отмечен ревьюером. | `WP-01` | `none_required:tracked_in_tc_review_findings` | `no` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        findings, _ = self.validator.validate_writer_quality_gate(
            gate_path.read_text(encoding="utf-8"),
            gate_path,
            root,
        )

        self.assertIn(
            "writer-quality-gate-pass-uses-postreview-substitution",
            {finding.id for finding in findings},
        )


if __name__ == "__main__":
    unittest.main()
