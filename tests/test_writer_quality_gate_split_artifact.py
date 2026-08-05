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
            evidence = "`validator.json`" if item == "scoped-validator-findings" else "checked"
            rows.append(f"| `{item}` | `pass` | {evidence} | `WP-01` | `none_required:pass` | `no` |")
        (design_dir / "writer-quality-gate.md").write_text(
            "# Writer Quality Gate\n\n" + "\n".join(rows) + "\n",
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


if __name__ == "__main__":
    unittest.main()
