from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_practical_writer_revision_contract",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalWriterRevisionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def make_test_case(self, root: Path, *, status: str, confirmation: str) -> Path:
        tc_dir = root / "test-cases"
        tc_dir.mkdir(parents=True)
        tc_path = tc_dir / "9.1-sample.md"
        tc_path.write_text(
            "\n".join(
                [
                    "# 9.1 Sample",
                    "",
                    "## TC-SAMPLE-001",
                    "**Название:** Проверка подсказки организации",
                    "**Тип:** Positive",
                    "**Приоритет:** High",
                    "**package_id:** `WP-01`",
                    "**Трассировка:** `SRC-001`",
                    f"**Статус исполнения:** `{status}`",
                    "",
                    "**Цель:** Проверить получение подсказки организации.",
                    "",
                    "**Предусловия:**",
                    "1. Открыть карточку партнера.",
                    "",
                    "**Тестовые данные:**",
                    "- Запрос: `7707083893`.",
                    "",
                    "**Шаги:**",
                    "1. Ввести запрос в поле поиска.",
                    "2. Проверить список подсказок.",
                    "",
                    "**Итоговый ожидаемый результат:** В списке отображается организация с ИНН `7707083893`.",
                    "",
                    "**Постусловия:** Не требуются.",
                    "",
                    f"**Требуется подтверждение:** {confirmation}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return tc_path

    def test_ready_case_with_pending_confirmation_blocks_review_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fts" / "Sample"
            tc_path = self.make_test_case(
                root,
                status="ready",
                confirmation="Нужна проверенная фикстура поиска по наименованию.",
            )

            findings, _ = self.validator.validate_test_case_file(tc_path, root)
            finding_ids = {finding.id for finding in findings}
            blocking = self.validator.ready_for_review_blocking_test_case_findings(tc_path, root)

            self.assertIn("test-case-ready-status-with-unresolved-execution-input", finding_ids)
            self.assertIn(
                "test-case-ready-status-with-unresolved-execution-input",
                {finding.id for finding in blocking},
            )

    def test_ready_case_allows_nonpending_confirmation_evidence_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fts" / "Sample"
            tc_path = self.make_test_case(
                root,
                status="ready",
                confirmation="Не требуется; используется заранее проверенная фикстура поиска по ИНН.",
            )

            findings, _ = self.validator.validate_test_case_file(tc_path, root)

            self.assertNotIn(
                "test-case-ready-status-with-unresolved-execution-input",
                {finding.id for finding in findings},
            )

    def test_revision_status_assertion_must_match_canonical_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fts" / "Sample"
            tc_path = self.make_test_case(
                root,
                status="needs-test-data",
                confirmation="Нужна проверенная фикстура поиска по наименованию.",
            )
            summary_path = root / "work" / "practical" / "9.1-sample" / "tc-revision-summary.md"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                "\n".join(
                    [
                        "# TC Revision Summary: sample",
                        "",
                        "**revision_type:** bounded_tc_revision_after_independent_review",
                        "",
                        "## Status Assertions",
                        "",
                        "| tc_id | status_after_revision |",
                        "| --- | --- |",
                        "| `TC-SAMPLE-001` | `ready` |",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            statuses = self.validator.build_test_case_execution_status_index([tc_path])
            findings, _ = self.validator.validate_tc_revision_summary_status_assertions(
                summary_path,
                root,
                statuses,
            )

            self.assertIn(
                "writer-revision-summary-status-assertion-mismatch",
                {finding.id for finding in findings},
            )

    def test_bounded_revision_requires_nonempty_status_assertions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fts" / "Sample"
            self.make_test_case(root, status="ready", confirmation="Не требуется.")
            summary_path = root / "work" / "practical" / "9.1-sample" / "tc-revision-summary.md"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                "\n".join(
                    [
                        "# TC Revision Summary: sample",
                        "",
                        "**revision_type:** bounded_tc_revision_after_independent_review",
                        "",
                        "## Status Assertions",
                        "",
                        "| tc_id | status_after_revision |",
                        "| --- | --- |",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_tc_revision_summary_status_assertions(
                summary_path,
                root,
                {},
            )

            self.assertIn(
                "writer-revision-summary-status-assertions-empty-table",
                {finding.id for finding in findings},
            )

    def test_revision_status_assertion_accepts_matching_canonical_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fts" / "Sample"
            tc_path = self.make_test_case(
                root,
                status="needs-test-data",
                confirmation="Нужна проверенная фикстура поиска по наименованию.",
            )
            summary_path = root / "work" / "practical" / "9.1-sample" / "tc-revision-summary.md"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                "\n".join(
                    [
                        "# TC Revision Summary: sample",
                        "",
                        "**revision_type:** bounded_tc_revision_after_independent_review",
                        "",
                        "## Status Assertions",
                        "",
                        "| tc_id | status_after_revision |",
                        "| --- | --- |",
                        "| `TC-SAMPLE-001` | `needs-test-data` |",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            statuses = self.validator.build_test_case_execution_status_index([tc_path])
            findings, _ = self.validator.validate_tc_revision_summary_status_assertions(
                summary_path,
                root,
                statuses,
            )

            self.assertNotIn(
                "writer-revision-summary-status-assertion-mismatch",
                {finding.id for finding in findings},
            )


if __name__ == "__main__":
    unittest.main()
