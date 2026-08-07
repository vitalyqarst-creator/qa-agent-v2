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

    def test_rejects_two_execution_statuses_in_one_test_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case().replace(
                    "**Статус исполнения:** `needs-test-data`",
                    "\n".join(
                        [
                            "**Статус исполнения:** `needs-test-data`",
                            "**Статус тест-кейса:** `candidate-ui-calibration`",
                        ]
                    ),
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-multiple-execution-statuses", ids)

    def test_rejects_duplicate_canonical_source_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case_with_steps("1. Попытаться найти скрытого партнера в реестре.")
                + "\n**Ссылка на ФТ:** `AS.1`; PDF стр. 3.\n",
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-duplicate-canonical-field", ids)

    def test_ignores_historical_snapshot_test_cases_for_current_quality_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = root / "fts" / "Sample" / "test-cases" / "scope.md"
            historical = (
                root
                / "fts"
                / "Sample"
                / "work"
                / "review-cycles"
                / "scope"
                / "versions"
                / "r1"
                / "files"
                / "test-cases"
                / "scope.md"
            )
            active.parent.mkdir(parents=True)
            historical.parent.mkdir(parents=True)
            active.write_text(self.case_with_steps("1. Попытаться найти скрытого партнера в реестре."), encoding="utf-8")
            historical.write_text(
                self.case_with_steps("1. Попытаться найти скрытого партнера в реестре.")
                + "\n**Ссылка на ФТ:** `AS.1`; PDF стр. 3.\n",
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("test-case-duplicate-canonical-field", ids)

    def test_form_isolation_requires_explicit_fields_and_immediate_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Новая форма не наследует значения первого объекта",
                    test_type="Positive",
                    test_data="- Первый объект: `Первое значение`.",
                    steps=(
                        "1. Открыть новую форму второго объекта.\n"
                        "2. Перевести фокус на поле `Наименование`.\n"
                        "3. Проверить значения новой формы."
                    ),
                    expected="Новая форма не содержит значения первого объекта.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-form-isolation-missing-checked-fields", ids)
        self.assertIn("test-case-form-isolation-delayed-observation", ids)

    def test_form_isolation_accepts_named_fields_checked_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            content = self.case(
                title="Новая форма не наследует значения первого объекта",
                test_type="Positive",
                test_data="- Первый объект: `Первое значение`; `40702810900000000001`.",
                steps=(
                    "1. Открыть новую форму второго объекта.\n"
                    "2. Проверить указанные поля новой формы."
                ),
                expected="Новая форма не содержит значений первого объекта в указанных полях.",
            ).replace(
                "**Шаги:**",
                "**Проверяемые поля:** `Наименование`; `Расчетный счет`.\n\n**Шаги:**",
            )
            path.write_text(content, encoding="utf-8")

            ids = self.finding_ids(root)

        self.assertNotIn("test-case-form-isolation-missing-checked-fields", ids)
        self.assertNotIn("test-case-form-isolation-delayed-observation", ids)

    def test_file_count_case_cannot_hide_an_unrelated_save_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Нельзя загрузить второй файл того же типа документа",
                    test_type="Negative",
                    test_data="- Первый файл: `a.pdf`.\n- Второй файл: `b.pdf`.",
                    steps="1. Добавить второй файл `b.pdf`.\n2. Нажать `Сохранить`.",
                    expected="Второй файл не добавлен; в поле остается только `a.pdf`.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-file-count-limit-save-crosscheck-smell", ids)

    def test_rejects_mixed_create_and_edit_entry_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Форма добавления или редактирования реквизита содержит обязательные поля",
                    test_type="Positive",
                    steps="1. Открыть форму добавления или редактирования реквизита.\n2. Проверить поля формы.",
                    expected="В форме отображаются обязательные поля.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-mixed-create-edit-path", ids)

    def test_rejects_manual_mutation_inferred_from_autofill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Поле партнера автозаполняется при создании реквизита",
                    test_type="Negative",
                    steps="1. Открыть добавление реквизита.\n2. Попытаться вручную очистить поле `Наименование партнера`.",
                    expected="Поле нельзя оставить пустым.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-autofill-manual-mutation-unsupported", ids)

    def test_rejects_document_type_as_file_cardinality_substitute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Нельзя загрузить второй файл того же типа документа",
                    test_type="Negative",
                    test_data="- Первый файл: `a.pdf`.\n- Второй файл: `b.pdf`.",
                    steps="1. Добавить второй файл того же типа документа.\n2. Проверить состав файлов.",
                    expected="В поле остается только первый файл.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-file-count-substituted-by-document-type", ids)

    def test_rejects_cancel_case_with_alternative_changed_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Отмена закрывает форму без сохранения изменений",
                    test_type="Positive",
                    test_data="- Изменение: расчетный счет `40702810900000000032` или город `Москва`.",
                    steps="1. Изменить данные.\n2. Нажать `Отменить`.",
                    expected="Изменения не сохранены.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-cancel-mutation-ambiguous", ids)

    def test_first_child_case_requires_an_empty_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Пользователь может добавить первый реквизит к партнеру",
                    test_type="Positive",
                    steps="1. Открыть добавление реквизита.\n2. Нажать `Сохранить`.",
                    expected="Реквизит сохранен.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-first-child-without-empty-parent-setup", ids)

    def test_second_child_case_requires_persistence_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Пользователь может добавить второй независимый реквизит к партнеру",
                    test_type="Positive",
                    steps="1. Открыть добавление реквизита.\n2. Нажать `Сохранить`.",
                    expected="Второй реквизит успешно привязан к партнеру.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-second-child-without-persistence-proof", ids)

    def test_declared_test_case_count_must_match_canonical_headings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "# Sample scope",
                        "",
                        "| Поле | Значение |",
                        "| --- | --- |",
                        "| Количество тест-кейсов | `2` |",
                        "",
                        self.case_with_steps("1. Попытаться найти скрытого партнера в реестре."),
                    ]
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("test-case-declared-count-mismatch", ids)

    def test_matching_declared_test_case_count_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "# Sample scope",
                        "",
                        "| Метрика | Значение |",
                        "| --- | --- |",
                        "| Тест-кейсов | `1` |",
                        "",
                        self.case_with_steps("1. Попытаться найти скрытого партнера в реестре."),
                    ]
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("test-case-declared-count-mismatch", ids)

    def test_persistence_case_requires_reopen_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Новая карточка сохраняется",
                    test_type="Positive",
                    test_data="- Уникальное значение: `Тест 001`.",
                    steps="1. Ввести `Тест 001`.\n2. Нажать `Сохранить`.",
                    expected="Карточка сохранена и форма закрыта.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("persistence-tc-without-reopen-verification", ids)

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

    def test_field_input_before_save_is_not_confused_by_save_noun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Реквизит сохраняется с валидными данными",
                    test_type="Positive",
                    steps=(
                        "1. Заполнить поля, необходимые для сохранения.\n"
                        "2. Ввести расчетный счет.\n"
                        "3. Нажать `Сохранить`."
                    ),
                    expected="Реквизит сохраняется.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("test-case-field-input-after-save-step", ids)

    def test_status_lifecycle_tc_cannot_merge_partner_and_requisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Сущность или реквизит в статусе `Подтвержден` доступна для использования",
                    test_type="Positive",
                    steps=(
                        "1. Найти подготовленную сущность или реквизит.\n"
                        "2. Проверить возможность использовать объект в обычном сценарии."
                    ),
                    expected="Сущность или реквизит в статусе `Подтвержден` доступна для использования.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertIn("status-lifecycle-execution-owner-missing", ids)

    def test_status_lifecycle_tc_for_one_card_does_not_trigger_mixed_owner_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="На карточке партнера отображается индикатор статуса `Подтвержден`",
                    test_type="Positive",
                    steps=(
                        "1. Открыть карточку подготовленного партнера.\n"
                        "2. Проверить зеленый индикатор статуса в карточке партнера."
                    ),
                    expected="В карточке партнера отображается зеленый индикатор статуса `Подтвержден`.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("status-lifecycle-execution-owner-missing", ids)

    def test_negative_no_save_tc_does_not_require_reopen_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "fts" / "Sample" / "test-cases" / "scope.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                self.case(
                    title="Пустое поле `ИНН` не позволяет сохранить карточку",
                    test_type="Negative",
                    steps="1. Оставить поле `ИНН` пустым.\n2. Нажать `Сохранить`.",
                    expected="Карточка не сохраняется; поле `ИНН` подсвечено красным.",
                ),
                encoding="utf-8",
            )

            ids = self.finding_ids(root)

        self.assertNotIn("persistence-tc-without-save-action", ids)
        self.assertNotIn("persistence-tc-without-reopen-verification", ids)

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
