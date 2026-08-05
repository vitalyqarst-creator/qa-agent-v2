from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_practical_quality_gates",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalArtifactQualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def finding_ids(self, root: Path) -> set[str]:
        report = self.validator.validate(root)
        return {finding["id"] for finding in report["findings"]}

    def test_practical_review_artifacts_must_not_keep_controller_thread_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "work" / "practical" / "scope-01" / "review-findings.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "# Review Findings",
                        "",
                        "| field | value |",
                        "| --- | --- |",
                        "| reviewer_task_or_session | `CONTROLLER_THREAD_ID_REQUIRED` |",
                    ]
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("practical-controller-thread-id-placeholder", ids)

    def test_absence_oracle_cannot_use_find_step_for_hidden_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(self.case_with_steps("1. Найти скрытого партнера в реестре."), encoding="utf-8")

            ids = self.finding_ids(root)

        self.assertIn("test-case-absence-oracle-find-step-mismatch", ids)

    def test_absence_oracle_accepts_attempt_to_find_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case_with_steps("1. Попытаться найти скрытого партнера в реестре."),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("test-case-absence-oracle-find-step-mismatch", ids)

    def test_production_tc_runtime_fields_reject_agent_process_english(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case_with_steps("1. Попытаться найти скрытого партнера в реестре.").replace(
                    "**Цель:** Проверить, что скрытый партнер отсутствует в реестре.",
                    "**Цель:** Проверить source-backed ограничение видимости скрытого партнера.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("production-runtime-agent-process-language-leak", ids)

    def test_production_tc_runtime_fields_allow_metadata_enums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case_with_steps("1. Попытаться найти скрытого партнера в реестре."),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("production-runtime-agent-process-language-leak", ids)

    def test_ui_evidence_index_warns_on_output_playwright_paths_even_when_declared_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "work" / "ui-automation-prep" / "scope-01" / "ui-evidence-index.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "# UI Evidence Index",
                        "",
                        "- `evidence_export_policy`: `local-output-index-only`",
                        "",
                        "| test_case_id | artifact_type | path | note |",
                        "| --- | --- | --- | --- |",
                        "| TC-001 | screenshot | output/playwright/scope-01/TC-001.png | local only |",
                    ]
                ),
                encoding="utf-8",
            )

            report = self.validator.validate(root)
            findings = {finding["id"]: finding for finding in report["findings"]}

        self.assertIn("ui-evidence-output-paths-declared-local", findings)
        self.assertEqual("warning", findings["ui-evidence-output-paths-declared-local"]["severity"])

    @staticmethod
    def case_with_steps(first_step: str) -> str:
        return "\n".join(
            [
                "## TC-SAMPLE-001",
                "**Название:** Скрытый партнер не отображается для пользователя без прав",
                "**Тип:** Negative",
                "**Приоритет:** High",
                "**Статус исполнения:** `needs-test-data`",
                "**package_id:** `WP-01`",
                "**Трассировка:** `AS.1`",
                "",
                "**Цель:** Проверить, что скрытый партнер отсутствует в реестре.",
                "",
                "**Предусловия:**",
                "1. Пользователь авторизован без административных прав.",
                "2. Открыт экран `Партнеры`.",
                "",
                "**Тестовые данные:**",
                "- Требуется скрытый партнер с известным уникальным признаком.",
                "",
                "**Шаги:**",
                first_step,
                "2. Проверить доступность действий для этого партнера.",
                "",
                "**Итоговый ожидаемый результат:** Партнер не отображается в реестре, поэтому действия для него недостижимы.",
                "",
                "**Постусловия:**",
                "- Не требуются.",
                "",
                "**Ссылка на ФТ:** `AS.1`.",
            ]
        )


if __name__ == "__main__":
    unittest.main()
