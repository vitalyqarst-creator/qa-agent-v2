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

    def quality_finding_ids(self, path: Path, root: Path) -> set[str]:
        content = path.read_text(encoding="utf-8")
        blocks = self.validator.extract_test_case_blocks(content)
        findings, _ = self.validator.validate_test_case_quality_smells(
            content,
            path,
            root,
            blocks=blocks,
        )
        return {finding.id for finding in findings}

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

    def test_duplicate_constraint_positive_save_is_warned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Дубль расчетного счета сохраняется в карточке реквизита",
                    test_type="Positive",
                    test_data="- Расчетный счет уже существует у этого партнера.",
                    steps="1. Ввести расчетный счет, совпадающий с существующим.\n2. Нажать `Сохранить`.",
                    expected="Карточка реквизита сохранена и отображается после повторного открытия.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-duplicate-constraint-positive-oracle-smell", ids)

    def test_downstream_obligation_must_not_be_local_save_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Прошедшая дата начала действия отклоняется при сохранении",
                    test_type="Negative",
                    traceability="AS.40; SRC-003; FT 6",
                    test_data="- Дата начала действия = `01.01.2020`.",
                    steps="1. Указать дату начала действия `01.01.2020`.\n2. Нажать `Сохранить`.",
                    expected="Карточка не сохраняется, дата отклонена.",
                    requirement_quote="Правило применяется в будущем ФТ 6 на стадии выпуска.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-downstream-obligation-local-rejection-smell", ids)

    def test_requiredness_must_not_be_injected_into_positive_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Поле банка автозаполняется после выбора подсказки",
                    test_type="Positive",
                    test_data="- Значение из справочника.",
                    steps="1. Выбрать подсказку банка.\n2. Проверить required marker у поля.",
                    expected="Поле заполнено; отображается признак обязательности.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-requiredness-injected-into-positive-flow", ids)

    def test_optional_field_must_not_be_checked_as_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Необязательное поле `Город` можно оставить пустым",
                    test_type="Positive",
                    test_data="- Источник: `О = Нет` для поля `Город`.",
                    steps="1. Оставить поле `Город` пустым.\n2. Проверить обязательность поля.",
                    expected="Поле подсвечено как обязательное.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-optional-field-treated-as-required", ids)

    def test_field_input_after_save_is_warned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Карточка реквизита сохраняется с валидными данными",
                    test_type="Positive",
                    steps="1. Ввести значение в поле `БИК`.\n2. Нажать `Сохранить`.\n3. Завершить ввод в поле `Расчетный счет`.",
                    expected="Карточка сохранена.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-field-input-after-save-step", ids)

    def test_practical_source_token_must_be_covered_or_gapped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tc_path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            design_dir = root / "fts" / "Sample" / "work" / "test-design" / "scope"
            tc_path.parent.mkdir(parents=True)
            design_dir.mkdir(parents=True)
            tc_path.write_text(self.case(traceability="AS.39; SRC-001"), encoding="utf-8")
            (design_dir / "source-row-inventory.md").write_text(
                "| source_row_id | requirement_codes |\n| --- | --- |\n| SRC-001 | AS.39; AS.40 |\n",
                encoding="utf-8",
            )

            ids = self.quality_finding_ids(tc_path, root / "fts" / "Sample")

        self.assertIn("test-case-source-token-not-covered-or-gapped", ids)

    def test_practical_source_token_gap_counts_as_handled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tc_path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            design_dir = root / "fts" / "Sample" / "work" / "test-design" / "scope"
            tc_path.parent.mkdir(parents=True)
            design_dir.mkdir(parents=True)
            tc_path.write_text(self.case(traceability="AS.39; SRC-001"), encoding="utf-8")
            (design_dir / "source-row-inventory.md").write_text(
                "| source_row_id | requirement_codes |\n| --- | --- |\n| SRC-001 | AS.39; AS.40 |\n",
                encoding="utf-8",
            )
            (design_dir / "coverage-gaps.md").write_text(
                "- `AS.40`: `blocked-observability` for external payment stage.\n",
                encoding="utf-8",
            )

            ids = self.quality_finding_ids(tc_path, root / "fts" / "Sample")

        self.assertNotIn("test-case-source-token-not-covered-or-gapped", ids)

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
    def case(
        *,
        title: str = "Скрытый партнер не отображается для пользователя без прав",
        test_type: str = "Negative",
        traceability: str = "AS.1",
        test_data: str = "- Требуется скрытый партнер с известным уникальным признаком.",
        steps: str = "1. Попытаться найти скрытого партнера в реестре.\n2. Проверить доступность действий для этого партнера.",
        expected: str = "Партнер не отображается в реестре, поэтому действия для него недостижимы.",
        requirement_quote: str = "",
    ) -> str:
        quote_lines = []
        if requirement_quote:
            quote_lines = ["", f"**Источник / цитата требования:** {requirement_quote}"]
        return "\n".join(
            [
                "## TC-SAMPLE-001",
                f"**Название:** {title}",
                f"**Тип:** {test_type}",
                "**Приоритет:** High",
                "**Статус исполнения:** `needs-test-data`",
                "**package_id:** `WP-01`",
                f"**Трассировка:** `{traceability}`",
                "",
                f"**Цель:** Проверить поведение: {title}.",
                "",
                "**Предусловия:**",
                "1. Пользователь авторизован.",
                "2. Открыт проверяемый экран.",
                "",
                "**Тестовые данные:**",
                test_data,
                "",
                "**Шаги:**",
                steps,
                "",
                f"**Итоговый ожидаемый результат:** {expected}",
                "",
                "**Постусловия:**",
                "- Не требуются.",
                *quote_lines,
            ]
        )

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
