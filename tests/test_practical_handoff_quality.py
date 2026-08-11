from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_practical_handoff_quality",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalHandoffQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    @staticmethod
    def source_selection_content(*, include_provenance: bool) -> str:
        provenance = (
            "- Ветка кода: `codex/test`\n"
            "- Коммит кода: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`\n"
            if include_provenance
            else ""
        )
        return (
            "# Выбор источников\n\n"
            "## Контекст\n\n"
            "- Выбранный FT slug: `Partners-v1`\n"
            "- Статус выбора: `selected`\n"
            f"{provenance}"
            "## Основные документы ФТ\n\n"
            "| Путь | Роль |\n| --- | --- |\n| `source/main.docx` | `main-ft-docx` |\n\n"
            "## Машиночитаемый источник XHTML\n\n"
            "- XHTML доступен: `yes`\n\n"
            "## PDF для структурной и визуальной сверки\n\n- PDF доступен: `yes`\n\n"
            "## Вспомогательные файлы и макеты\n\n- Нет.\n\n"
            "## Качество источников\n\n- Читаемость: подтверждена.\n\n"
            "## Неоднозначности и журнал решений\n\n- Нет.\n\n"
            "## Передача следующему этапу\n\n- Следующий навык: `ft-scope-analyzer`\n"
        )

    def test_selected_source_handoff_requires_code_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_selection = root / "source-selection.md"
            source_selection.write_text(
                self.source_selection_content(include_provenance=False), encoding="utf-8"
            )
            workflow = root / "workflow-state.yaml"
            state = {"stage_status": "ready-for-next-stage", "next_skill": "ft-scope-analyzer"}

            missing_findings, _ = self.validator.validate_source_selection_artifact(
                source_selection, root, state, workflow
            )
            source_selection.write_text(
                self.source_selection_content(include_provenance=True), encoding="utf-8"
            )
            accepted_findings, _ = self.validator.validate_source_selection_artifact(
                source_selection, root, state, workflow
            )

        self.assertIn(
            "source-selection-missing-code-provenance",
            {finding.id for finding in missing_findings},
        )
        self.assertNotIn(
            "source-selection-missing-code-provenance",
            {finding.id for finding in accepted_findings},
        )

    def test_source_selection_rejects_dangling_handoff_artifact_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_selection = root / "source-selection.md"
            source_selection.write_text(
                self.source_selection_content(include_provenance=True).replace(
                    "- Следующий навык: `ft-scope-analyzer`\n",
                    "- Следующий навык: `ft-scope-analyzer`\n"
                    "- latest_artifacts: `source-locator-session-log.md`\n",
                ),
                encoding="utf-8",
            )
            workflow = root / "workflow-state.yaml"
            state = {"stage_status": "ready-for-next-stage", "next_skill": "ft-scope-analyzer"}

            missing_findings, _ = self.validator.validate_source_selection_artifact(
                source_selection, root, state, workflow
            )
            (root / "source-locator-session-log.md").write_text("# Receipt\n", encoding="utf-8")
            accepted_findings, _ = self.validator.validate_source_selection_artifact(
                source_selection, root, state, workflow
            )

        self.assertIn(
            "source-selection-handoff-dangling-artifact-link",
            {finding.id for finding in missing_findings},
        )
        self.assertNotIn(
            "source-selection-handoff-dangling-artifact-link",
            {finding.id for finding in accepted_findings},
        )

    def test_practical_source_selection_requires_russian_visible_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_selection = root / "source-selection.md"
            source_selection.write_text(
                self.source_selection_content(include_provenance=True).replace(
                    "# Выбор источников",
                    "# Source Selection",
                ),
                encoding="utf-8",
            )
            workflow = root / "workflow-state.yaml"
            state = {
                "route_profile": "practical_v0_8",
                "stage_status": "ready-for-next-stage",
                "next_skill": "ft-scope-analyzer",
            }

            findings, _ = self.validator.validate_source_selection_artifact(
                source_selection, root, state, workflow
            )

        self.assertIn(
            "source-selection-non-russian-visible-text",
            {finding.id for finding in findings},
        )

    def test_scope_options_rejects_unallocated_source_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            options = root / "scope-options.md"
            options.write_text(
                "# Варианты области\n\n"
                "## Candidate Scope\n\n"
                "### SCOPE-OPTION-001\n\n"
                "**Scope Slug:** `sample`\n\n"
                "## Распределение требований ФТ\n\n"
                "| Якорь ФТ | Назначение | Обоснование |\n"
                "| --- | --- | --- |\n"
                "| `AS.1` | `sample` | Проверяется в области. |\n",
                encoding="utf-8",
            )

            missing_findings, _ = self.validator.validate_scope_options_source_allocation(
                options,
                root,
                {"AS.1", "AS.2"},
            )
            options.write_text(
                options.read_text(encoding="utf-8")
                + "| `AS.2` | `sample` | Проверяется в области. |\n",
                encoding="utf-8",
            )
            accepted_findings, _ = self.validator.validate_scope_options_source_allocation(
                options,
                root,
                {"AS.1", "AS.2"},
            )

        self.assertIn(
            "scope-options-source-allocation-incomplete",
            {finding.id for finding in missing_findings},
        )
        self.assertEqual([], accepted_findings)

    def test_scope_options_rejects_cross_scope_rule_without_affected_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            options = root / "scope-options.md"
            options.write_text(
                "\n".join(
                    [
                        "# Варианты области",
                        "",
                        "## Candidate Scope",
                        "",
                        "### SCOPE-OPTION-001",
                        "**Scope Slug:** `partner-card`",
                        "",
                        "### SCOPE-OPTION-002",
                        "**Scope Slug:** `requisites-card`",
                        "",
                        "## Распределение требований ФТ",
                        "",
                        "| Якорь ФТ | Владелец | Затрагиваемые области | Обоснование |",
                        "| --- | --- | --- | --- |",
                        "| `AS.1` | `partner-card` | — | `cross-scope`: общее правило. |",
                    ]
                ),
                encoding="utf-8",
            )

            missing_findings, _ = self.validator.validate_scope_options_source_allocation(
                options, root, {"AS.1"}
            )
            options.write_text(
                options.read_text(encoding="utf-8").replace(
                    "| `AS.1` | `partner-card` | — |",
                    "| `AS.1` | `partner-card` | `partner-card`; `requisites-card` |",
                ),
                encoding="utf-8",
            )
            accepted_findings, _ = self.validator.validate_scope_options_source_allocation(
                options, root, {"AS.1"}
            )

        self.assertIn(
            "scope-options-cross-scope-targets-missing",
            {finding.id for finding in missing_findings},
        )
        self.assertNotIn(
            "scope-options-cross-scope-targets-missing",
            {finding.id for finding in accepted_findings},
        )

    def test_source_locator_session_log_requires_provenance_and_validator_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "source-locator-session-log.md"
            base = (
                "# Source Locator Session Log\n\n"
                "## Session Metadata\n\n"
                "| field | value |\n| --- | --- |\n"
                "| skill | `ft-source-locator` |\n"
                "| ft_slug | `Partners-v1` |\n\n"
                "## Inputs Read\n\n- `source/main.docx`\n\n"
                "## Inputs Not Used\n\n- `fts/Partners/old` — not used.\n\n"
                "## Key Decisions\n\n- Selected package.\n\n"
                "## Risks And Fallbacks\n\n- none\n\n"
                "## Validation\n\n{validation}\n\n"
                "## Contamination Check\n\n- Neighbor baseline excluded and not used.\n"
            )
            log.write_text(base.format(validation="- source readability passed."), encoding="utf-8")
            missing_findings, _ = self.validator.validate_session_log(
                log, root, session_log_policy="strict"
            )
            log.write_text(
                base.replace(
                    "| ft_slug | `Partners-v1` |\n",
                    "| ft_slug | `Partners-v1` |\n"
                    "| code_branch | `codex/test` |\n"
                    "| code_commit | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` |\n",
                ).format(
                    validation=(
                        "- `python scripts/validate_agent_artifacts.py --root fts/Partners/Partners-v1` — "
                        "errors: 0; warnings: 0; info: 0; downstream_allowed: yes."
                    )
                ),
                encoding="utf-8",
            )
            accepted_findings, _ = self.validator.validate_session_log(
                log, root, session_log_policy="strict"
            )

        missing_ids = {finding.id for finding in missing_findings}
        accepted_ids = {finding.id for finding in accepted_findings}
        self.assertIn("session-log-source-locator-code-provenance-missing", missing_ids)
        self.assertIn("session-log-source-locator-final-validator-missing", missing_ids)
        self.assertNotIn("session-log-source-locator-code-provenance-missing", accepted_ids)
        self.assertNotIn("session-log-source-locator-final-validator-missing", accepted_ids)

    def write_scope_brief(
        self,
        path: Path,
        *,
        dependency_status: str = "needs-test-data",
        include_ready_dependency: bool = False,
    ) -> None:
        dependency_rows = [
            "| Ключ подготовки | Подготовка | Затронутые проверки | Статус исполнения |",
            "| --- | --- | --- | --- |",
            f"| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-002` | `{dependency_status}` |",
        ]
        if include_ready_dependency:
            dependency_rows.append(
                "| `SETUP-OBJECT-001` | Подготовить объект. | `ATOM-001` | `needs-test-data` |"
            )
        path.write_text(
            "\n".join(
                [
                    "# Краткое описание области",
                    "",
                    "## Планируемые проверки",
                    "",
                    "| Идентификатор | Проверяемое утверждение | Основной ожидаемый результат | Статус исполнения |",
                    "| --- | --- | --- | --- |",
                    "| `ATOM-001` | Действие выполняется для подготовленного объекта. | Действие выполнено. | `ready` |",
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | Действие доступно. | `needs-test-data` |",
                    "",
                    "## Предпосылки исполнения",
                    "",
                    "| Затронутые проверки | Исполнитель | Объект и исходное состояние | Ключ подготовки | Подтверждение подготовки | Статус исполнения |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "",
                    "## Зависимости от тестовых данных",
                    "",
                    *dependency_rows,
                ]
            ),
            encoding="utf-8",
        )

    def test_scope_brief_rejects_dependency_rows_that_leave_affected_check_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief, include_ready_dependency=True)

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-data-dependency-status-mismatch", finding_ids)

    def test_scope_brief_accepts_structured_preparation_and_setup_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)

            findings, checks = self.validator.validate_practical_scope_brief(brief, root)

        self.assertEqual([], findings)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_scope_brief_requires_one_uncertainty_type_for_each_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\n## Открытые вопросы\n\n- `GAP-001`: Не определено продуктовое правило.\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-uncertainty-classification-missing", finding_ids)

    def test_scope_brief_accepts_complete_uncertainty_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\n## Открытые вопросы\n\n- `GAP-001`: Не определено продуктовое правило.\n"
                + "\n## Неопределённости и классификация\n\n"
                + "| Идентификатор | Тип неопределённости | Дальнейшее действие |\n"
                + "| --- | --- | --- |\n"
                + "| `GAP-001` | `ba-business-ambiguity` | Задать вопрос БА. |\n",
                encoding="utf-8",
            )

            findings, checks = self.validator.validate_practical_scope_brief(brief, root)

        self.assertEqual([], findings)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_scope_brief_rejects_candidate_ui_status_that_hides_missing_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                .replace("| `ATOM-002` | Действие доступно пользователю с заданными правами. | Действие доступно. | `needs-test-data` |", "| `ATOM-002` | Действие доступно пользователю с заданными правами. | Действие доступно. | `candidate-ui-calibration` |")
                .replace("| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |", "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `candidate-ui-calibration` |"),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_abstract_source_setup_hidden_by_ui_calibration_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                .replace(
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | Действие доступно. | `needs-test-data` |",
                    "| `ATOM-002` | Открытие подготовленного объекта требует уточнения UI. | Действие доступно. | `candidate-ui-calibration` |",
                )
                .replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Шаги подготовки: Таблица 3; данные: объект = существующий. | `candidate-ui-calibration` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)
        evidence = "\n".join(
            item
            for finding in findings
            if finding.id == "practical-scope-brief-execution-prerequisites-incomplete"
            for item in finding.evidence
        )
        self.assertIn("missing-setup-hidden-by-status=ATOM-002", evidence)

    def test_scope_brief_rejects_role_inventory_for_administrator_only_atom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                .replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | Администратор. | Подготовленный объект. | `SETUP-ACCESS-001`; `SETUP-ROLE-INVENTORY` | Отсутствует: учетная запись администратора и полный перечень ролей. | `needs-test-data` |",
                )
                .replace(
                    "| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-002` | `needs-test-data` |",
                    "| `SETUP-ACCESS-001`; `SETUP-ROLE-INVENTORY` | Подготовить учетную запись администратора и полный перечень ролей. | `ATOM-002` | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-overbroad-role-inventory-setup", finding_ids)

    def test_mockup_inventory_accepts_russian_visible_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = root / "mockup-visual-inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "# Визуальный инвентарь макета",
                        "",
                        "## Метаданные",
                        "",
                        "| Поле | Значение | Доказательство |",
                        "| --- | --- | --- |",
                        "| Путь к макету | `mockups/sample.png` | SHA-256 `abc` |",
                        "| Открыт | `yes` | просмотр изображения |",
                        "| Способ просмотра | `visual-inspection` | вручную |",
                        "| Экран | `Партнеры` | подпись макета |",
                        "",
                        "## Состав макета",
                        "",
                        "| Тип элемента | Подпись на макете | Каноническое имя ФТ | Видимое состояние | Примечание |",
                        "| --- | --- | --- | --- | --- |",
                        "| `visible_blocks` | `Партнеры` | `Партнеры` | `visible` | заголовок |",
                        "| `visible_fields` | `Название` | `Название` | `visible` | поле |",
                        "| `visible_actions` | `Добавить` | `Добавить` | `visible` | кнопка |",
                        "",
                        "## Подсказки по взаимодействию",
                        "",
                        "| Элемент | Способ действия | Источник | Используется в шагах | Ограничение |",
                        "| --- | --- | --- | --- | --- |",
                        "| `Добавить` | нажать кнопку | макет | `yes` | не является бизнес-правилом |",
                        "",
                        "## Элементы только макета",
                        "",
                        "| Элемент | Наблюдение на макете | Ссылка на ФТ | Обработка |",
                        "| --- | --- | --- | --- |",
                        "| `-` | нет | `-` | `ignore-out-of-scope` |",
                        "",
                        "## Конфликты с ФТ",
                        "",
                        "| Элемент | Утверждение ФТ | Наблюдение на макете | Решение |",
                        "| --- | --- | --- | --- |",
                        "| `-` | нет | нет | `FT wins` |",
                        "",
                        "## Решение об использовании",
                        "",
                        "| Поле | Значение | Доказательство |",
                        "| --- | --- | --- |",
                        "| Используется в шагах | `yes` | шаги проверки |",
                        "| Не используется как источник требований | `yes` | ФТ определяет поведение |",
                    ]
                ),
                encoding="utf-8",
            )

            findings, checks = self.validator.validate_mockup_visual_inventory(inventory, root)

        self.assertEqual([], findings)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_scope_brief_rejects_renamed_gap_in_linked_parity_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            (root / "source-parity-check.md").write_text(
                "# Сверка источников\n\n- `GAP-OTHER-001`: Расхождение источников.\n",
                encoding="utf-8",
            )
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\n## Источники\n\n- `source-parity-check.md`\n"
                + "\n## Открытые вопросы\n\n- `GAP-001`: Не определено продуктовое правило.\n"
                + "\n## Неопределённости и классификация\n\n"
                + "| Идентификатор | Тип неопределённости | Дальнейшее действие |\n"
                + "| --- | --- | --- |\n"
                + "| `GAP-001` | `ba-business-ambiguity` | Задать вопрос БА. |\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-linked-gap-id-mismatch", finding_ids)

    def test_practical_clarification_rejects_ui_detail_and_external_boundary_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clarification = root / "scope-clarification-requests.md"
            clarification.write_text(
                "\n".join(
                    [
                        "## Clarification Requests",
                        "",
                        "```yaml",
                        "clarification_id: CLR-001",
                        "gap_id: GAP-001",
                        "request_kind: ba-business-ambiguity",
                        "question: Какой экран или видимый признак подтверждает успешный переход?",
                        "```",
                        "",
                        "```yaml",
                        "clarification_id: CLR-002",
                        "gap_id: GAP-002",
                        "request_kind: ba-business-ambiguity",
                        "question: Какие роли будут описаны в ФТ 11?",
                        "```",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_clarification_requests(
                clarification,
                root,
                {"GAP-001", "GAP-002"},
            )

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-clarification-request-classification-invalid", finding_ids)

    def test_scope_brief_does_not_require_fixture_data_for_a_simple_screen_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                    "| `ATOM-001` | Пользователь с доступом. | Экран с доступной кнопкой добавления. | `SETUP-OBJECT-001` | Шаги подготовки: открыть экран по AS.10; данные: путь к экрану. | `ready` |",
                ),
                encoding="utf-8",
            )

            findings, checks = self.validator.validate_practical_scope_brief(brief, root)

        self.assertEqual([], findings)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_scope_brief_requires_prerequisites_for_every_planned_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |\n",
                    "",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_requires_actor_and_initial_state_for_missing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | Не требуется. | Не требуется. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_ready_existing_state_without_reproducible_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`.",
                    "Подготовленный объект уже существует.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_generic_actor_for_ready_access_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                    "| `ATOM-001` | Тестировщик | Объект доступен только администратору. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_requires_fixture_for_ready_role_and_status_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                    "| `ATOM-001` | Администратор | Объект в статусе «Подтвержден». | `SETUP-ADMIN-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_free_text_as_ready_preparation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`.",
                    "Исходные данные: создать или выбрать объект.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_ready_preparation_without_concrete_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`.",
                    "Шаги подготовки: создать объект по AS.10; данные: наименование объекта.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def write_multi_action_brief(self, root: Path, *, mapped_atoms: str) -> Path:
        inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
        inventory.parent.mkdir(parents=True)
        inventory.write_text(
            "\n".join(
                [
                    "## Реестр строк источника",
                    "",
                    "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                    f"| `SRC-001` | `PKG-01` | Архивирование партнера | Таблица действий | `AS.12; AS.13` | `yes` | {mapped_atoms} |",
                ]
            ),
            encoding="utf-8",
        )
        brief = root / "scope-brief.md"
        brief.write_text(
            "\n".join(
                [
                    "# Краткое описание области",
                    "",
                    "## Источники",
                    "",
                    "- `work/stage-handoffs/scope/source-row-inventory.md`",
                    "",
                    "## Планируемые проверки",
                    "",
                    "| Идентификатор | Проверяемое утверждение | Основной ожидаемый результат | Статус исполнения |",
                    "| --- | --- | --- | --- |",
                    "| `ATOM-001` | Архивирование доступно. | Карточка архивирована. | `needs-test-data` |",
                    "| `ATOM-002` | Архивирование разрешено администратору. | Действие доступно. | `needs-test-data` |",
                    "",
                    "## Предпосылки исполнения",
                    "",
                    "| Затронутые проверки | Исполнитель | Объект и исходное состояние | Ключ подготовки | Подтверждение подготовки | Статус исполнения |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| `ATOM-001` | Администратор | Партнер в статусе «Подтвержден». | `SETUP-PARTNER-STATE` | Отсутствует: партнер в статусе «Подтвержден». | `needs-test-data` |",
                    "| `ATOM-002` | Администратор | Партнер в статусе «Подтвержден». | `SETUP-ROLE-ACCOUNT` | Отсутствует: учетная запись администратора. | `needs-test-data` |",
                    "",
                    "## Зависимости от тестовых данных",
                    "",
                    "| Ключ подготовки | Подготовка | Затронутые проверки | Статус исполнения |",
                    "| --- | --- | --- | --- |",
                    "| `SETUP-PARTNER-STATE` | Подготовить партнера в заданном статусе. | `ATOM-001` | `needs-test-data` |",
                    "| `SETUP-ROLE-ACCOUNT` | Подготовить учетную запись администратора. | `ATOM-002` | `needs-test-data` |",
                ]
            ),
            encoding="utf-8",
        )
        return brief

    def test_scope_brief_requires_each_action_code_to_map_to_atom_or_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`")

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-source-row-atom-coverage-incomplete", finding_ids)

    def test_scope_brief_requires_reciprocal_source_row_atom_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
            inventory.parent.mkdir(parents=True)
            inventory.write_text(
                "\n".join(
                    [
                        "## Реестр строк источника",
                        "",
                        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                        "| --- | --- | --- | --- | --- | --- | --- |",
                        "| `SRC-001` | `PKG-01` | Первое действие. | Таблица 1 | `AS.10` | `yes` | `ATOM-001` |",
                        "| `SRC-002` | `PKG-01` | Второе действие. | Таблица 1 | `AS.11` | `yes` | `ATOM-002` |",
                    ]
                ),
                encoding="utf-8",
            )
            brief = root / "scope-brief.md"
            brief.write_text(
                "\n".join(
                    [
                        "# Краткое описание области",
                        "",
                        "## Источники",
                        "",
                        "- `work/stage-handoffs/scope/source-row-inventory.md`",
                        "",
                        "## Планируемые проверки",
                        "",
                        "| Идентификатор | Источник | Проверяемое утверждение | Основной ожидаемый результат | Статус исполнения |",
                        "| --- | --- | --- | --- | --- |",
                        "| `ATOM-001` | `AS.10`; `SRC-002` | Первое действие. | Первое действие выполнено. | `needs-test-data` |",
                        "| `ATOM-002` | `AS.11`; `SRC-001` | Второе действие. | Второе действие выполнено. | `needs-test-data` |",
                        "",
                        "## Предпосылки исполнения",
                        "",
                        "| Затронутые проверки | Исполнитель | Объект и исходное состояние | Ключ подготовки | Подтверждение подготовки | Статус исполнения |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-001` | Отсутствует: подготовленный объект. | `needs-test-data` |",
                        "| `ATOM-002` | Пользователь с доступом. | Подготовленный объект. | `SETUP-002` | Отсутствует: подготовленный объект. | `needs-test-data` |",
                        "",
                        "## Зависимости от тестовых данных",
                        "",
                        "| Ключ подготовки | Подготовка | Затронутые проверки | Статус исполнения |",
                        "| --- | --- | --- | --- |",
                        "| `SETUP-001` | Подготовить первый объект. | `ATOM-001` | `needs-test-data` |",
                        "| `SETUP-002` | Подготовить второй объект. | `ATOM-002` | `needs-test-data` |",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-source-row-atom-bindings-inconsistent", finding_ids)

    def write_universal_role_brief(self, root: Path, *, quantified: bool) -> Path:
        inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
        inventory.parent.mkdir(parents=True)
        inventory.write_text(
            "\n".join(
                [
                    "## Реестр строк источника",
                    "",
                    "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                    "| `SRC-001` | `PKG-01` | Скрытый партнер скрыт для всех, кроме администратора. | Таблица статусов | `AS.11` | `yes` | `ATOM-001` |",
                ]
            ),
            encoding="utf-8",
        )
        assertion = (
            "Скрытый партнер не отображается для каждой настроенной роли, кроме администратора."
            if quantified
            else "Скрытый партнер не отображается для пользователя без роли администратора."
        )
        actor = (
            "Пользователь с каждой настроенной ролью, кроме администратора"
            if quantified
            else "Пользователь без роли администратора"
        )
        dependency = (
            "Полный перечень настроенных ролей, кроме администратора, и учетные записи для каждой роли."
            if quantified
            else "Учетная запись пользователя без роли администратора."
        )
        proof = (
            "\n## Обоснование параметризации ATOM\n\n"
            "| Атом | Стартовый экран | UI-уровень | Навигация | Действие | Триггер | Ожидаемый результат |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| `ATOM-001` | Список партнеров | Карточка партнера | Открыть список | Найти партнера | Вход каждой ролью | Скрытый партнер не отображается. |\n"
            if quantified
            else ""
        )
        brief = root / "scope-brief.md"
        brief.write_text(
            "\n".join(
                [
                    "# Краткое описание области",
                    "",
                    "## Источники",
                    "",
                    "- `work/stage-handoffs/scope/source-row-inventory.md`",
                    "",
                    "## Планируемые проверки",
                    "",
                    "| Идентификатор | Источник | Проверяемое утверждение | Основной ожидаемый результат | Статус исполнения |",
                    "| --- | --- | --- | --- | --- |",
                    f"| `ATOM-001` | `AS.11`; `SRC-001` | {assertion} | Скрытый партнер не отображается. | `needs-test-data` |",
                    "",
                    "## Предпосылки исполнения",
                    "",
                    "| Затронутые проверки | Исполнитель | Объект и исходное состояние | Ключ подготовки | Подтверждение подготовки | Статус исполнения |",
                    "| --- | --- | --- | --- | --- | --- |",
                    f"| `ATOM-001` | {actor} | Скрытый партнер. | `SETUP-ROLES-001` | Отсутствует: {dependency} | `needs-test-data` |",
                    "",
                    "## Зависимости от тестовых данных",
                    "",
                    "| Ключ подготовки | Подготовка | Затронутые проверки | Статус исполнения |",
                    "| --- | --- | --- | --- |",
                    f"| `SETUP-ROLES-001` | {dependency} | `ATOM-001` | `needs-test-data` |",
                    proof,
                ]
            ),
            encoding="utf-8",
        )
        return brief

    def test_scope_brief_rejects_single_user_for_universal_role_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_universal_role_brief(root, quantified=False)

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-universal-role-coverage-incomplete", finding_ids)

    def test_scope_brief_accepts_quantified_role_coverage_with_full_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_universal_role_brief(root, quantified=True)

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("practical-scope-brief-universal-role-coverage-incomplete", finding_ids)

    def test_scope_brief_rejects_phased_multi_actor_row_even_with_parameterization_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_universal_role_brief(root, quantified=True)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с каждой настроенной ролью, кроме администратора |",
                    "| `ATOM-001` | Администратор, затем пользователь с каждой настроенной ролью, кроме администратора |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        evidence = "\n".join(
            item
            for finding in findings
            if finding.id == "practical-scope-brief-execution-prerequisites-incomplete"
            for item in finding.evidence
        )
        self.assertIn("phased-multiple-actors=ATOM-001", evidence)

    def test_scope_brief_rejects_unresolved_source_inventory_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "`work/stage-handoffs/scope/source-row-inventory.md`",
                    "`source-row-inventory.md`",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-source-row-inventory-link-unresolved", finding_ids)

    def test_scope_brief_rejects_aggregated_oracle_obligations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | Действие доступно. | `needs-test-data` |",
                    "| `ATOM-002` | `SO-NEG-001`; `SO-NEG-002` требуют разной проверки. | Действие доступно. | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-aggregated-oracle-obligations", finding_ids)

    def test_scope_brief_rejects_multiple_actors_without_parameterization_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | Пользователь с ролью «Администратор» и пользователь без роли администратора. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствуют: учетные записи для обеих ролей. | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_allows_multiple_actors_only_with_complete_parameterization_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | Пользователь с ролью «Администратор» и пользователь без роли администратора. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствуют: учетные записи для обеих ролей. | `needs-test-data` |",
                ) + "\n## Обоснование параметризации ATOM\n\n"
                + "| Атом | Стартовый экран | UI-уровень | Навигация | Действие | Триггер | Ожидаемый результат |\n"
                + "| --- | --- | --- | --- | --- | --- | --- |\n"
                + "| `ATOM-002` | Экран A | Уровень A | Путь A | Действие A | Триггер A | Действие доступно. |\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_missing_main_expected_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | Действие доступно. | `needs-test-data` |",
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. |  | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-planned-expected-result-missing", finding_ids)

    def test_scope_brief_rejects_negative_obligation_for_multiple_atoms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\n\n## Кандидаты отрицательных проверок\n\n"
                + "| Идентификатор | Связанный ATOM |\n"
                + "| --- | --- |\n"
                + "| `SO-NEG-001` | `ATOM-001`; `ATOM-002` |\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-negative-obligation-aggregated-fields", finding_ids)

    def test_scope_brief_requires_atom_link_for_negative_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\n\n## Кандидаты отрицательных проверок\n\n"
                + "| Идентификатор | Вход |\n"
                + "| --- | --- |\n"
                + "| `SO-NEG-001` | Невалидное значение |\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-negative-obligation-atom-link-missing", finding_ids)

    def test_fidelity_binding_must_match_inventory_atom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "06-scope"
            handoff.mkdir(parents=True)
            inventory = handoff / "source-row-inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "## Реестр строк источника",
                        "",
                        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                        "| --- | --- | --- | --- | --- | --- | --- |",
                        "| `SRC-001` | `PKG-01` | Зеленый индикатор | Таблица 9 | `AS.44` | yes | `ATOM-002`; `FID-001` |",
                    ]
                ),
                encoding="utf-8",
            )
            fidelity = handoff / "source-to-package-fidelity.json"
            fidelity.write_text(
                '{"version":1,"bindings":[{"binding_id":"FID-001","atom_id":"ATOM-001"}]}',
                encoding="utf-8",
            )
            state = {
                "route_profile": "practical_v0_8",
                "latest_artifacts": {"source_to_package_fidelity": str(fidelity)},
            }

            findings, _ = self.validator.validate_practical_fidelity_inventory_bindings(
                state,
                handoff / "workflow-state.yaml",
                root,
                root,
                [inventory],
            )

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-fidelity-inventory-binding-mismatch", finding_ids)

    def test_fidelity_binding_accepts_exactly_one_matching_inventory_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "06-scope"
            handoff.mkdir(parents=True)
            inventory = handoff / "source-row-inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "## Реестр строк источника",
                        "",
                        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                        "| --- | --- | --- | --- | --- | --- | --- |",
                        "| `SRC-001` | `PKG-01` | Зеленый индикатор | Таблица 9 | `AS.44` | yes | `ATOM-002`; `FID-001` |",
                    ]
                ),
                encoding="utf-8",
            )
            fidelity = handoff / "source-to-package-fidelity.json"
            fidelity.write_text(
                '{"version":1,"bindings":[{"binding_id":"FID-001","atom_id":"ATOM-002"}]}',
                encoding="utf-8",
            )
            state = {
                "route_profile": "practical_v0_8",
                "latest_artifacts": {"source_to_package_fidelity": str(fidelity)},
            }

            findings, checks = self.validator.validate_practical_fidelity_inventory_bindings(
                state,
                handoff / "workflow-state.yaml",
                root,
                root,
                [inventory],
            )

        self.assertEqual([], findings)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_scope_gap_language_rejects_english_explanatory_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gaps = root / "scope-coverage-gaps.md"
            gaps.write_text(
                "\n".join(
                    [
                        "# Scope Coverage Gaps",
                        "",
                        "### GAP-001",
                        "**Description:** Неизвестное правило.",
                        "**Missing Behavior:** Exact UI response is not specified.",
                        "**Source Statement:** `Исходная цитата ФТ`",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_gap_language(gaps, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-gaps-non-russian-agent-prose", finding_ids)

    def test_scope_brief_requires_shared_setup_for_atomic_checks_of_one_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-operation-setup-inheritance-incomplete", finding_ids)

    def test_scope_brief_requires_specific_actor_for_atomic_checks_of_one_restricted_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Администратор | Партнер в статусе «Подтвержден». |",
                    "| `ATOM-001` | Тестировщик | Партнер в статусе «Подтвержден». |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-operation-actor-inheritance-incomplete", finding_ids)

    def test_scope_brief_rejects_english_visible_source_inventory_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")
            inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
            inventory.write_text(
                inventory.read_text(encoding="utf-8").replace(
                    "Архивирование партнера",
                    "Partner widget",
                ) + "\n\n- This compact registry source is ready.\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-source-row-inventory-non-russian-visible-text", finding_ids)

    def test_scope_brief_rejects_english_source_inventory_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")
            inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
            inventory.write_text(
                inventory.read_text(encoding="utf-8").replace(
                    "## Реестр строк источника",
                    "## Source Row Inventory",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-source-row-inventory-non-russian-visible-text", finding_ids)

    def test_scope_brief_accepts_russian_source_inventory_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")
            inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
            rows = self.validator.parsed_source_row_inventory_rows(
                inventory.read_text(encoding="utf-8")
            )

        self.assertEqual("SRC-001", rows[0]["source_row_id"])
        self.assertIn("ATOM-001", rows[0]["mapped_atom_or_gap"])

    def test_scope_brief_rejects_hidden_source_inventory_markup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = self.write_multi_action_brief(root, mapped_atoms="`ATOM-001`; `ATOM-002`")
            inventory = root / "work" / "stage-handoffs" / "scope" / "source-row-inventory.md"
            inventory.write_text(
                inventory.read_text(encoding="utf-8").replace(
                    "## Реестр строк источника",
                    "## Реестр строк источника\n\n<!-- compatibility marker -->\n```\n## Source Row Inventory\n```",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-source-row-inventory-hidden-markup", finding_ids)
        binding_findings = [
            finding
            for finding in findings
            if finding.id == "practical-scope-brief-source-row-atom-bindings-inconsistent"
        ]
        self.assertFalse(
            any(
                "unknown-source-row" in item
                for finding in binding_findings
                for item in finding.evidence
            )
        )

    def test_source_inventory_parser_accepts_russian_heading(self) -> None:
        content = "\n".join(
            [
                "## Реестр строк источника",
                "",
                "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                "| `SRC-001` | `PKG-01` | Поле | Таблица 1 | `AS.1` | `yes` | `ATOM-001` |",
                "",
                "## Source Table Normalization",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            findings, _ = self.validator.validate_source_row_inventory(
                content, root / "source-row-inventory.md", root
            )

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("source-row-inventory-missing", finding_ids)
        self.assertNotIn("source-row-inventory-no-table", finding_ids)

    def test_scope_brief_propagates_missing_setup_to_every_dependent_atom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-ACCESS-001` | Шаги подготовки: создать объект по AS.10; данные: наименование=`Тестовый объект`. | `ready` |",
                ).replace(
                    "| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-002` | `needs-test-data` |",
                    "| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-001`; `ATOM-002` | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-data-dependency-status-mismatch", finding_ids)

    def test_scope_brief_rejects_english_visible_handoff_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "# Краткое описание области",
                    "# Scope Brief",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-handoff-non-russian-visible-text", finding_ids)

    def test_scope_brief_rejects_single_english_process_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8") + "\n| Version gate | `passed` |\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-handoff-non-russian-visible-text", finding_ids)

    def test_practical_workflow_rejects_stale_code_version_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            state = {
                "route_profile": "practical_v0_8",
                "root_consistency": {"code_root": str(root)},
                "code_version_gate": {"code_commit": "0" * 40},
            }
            original = self.validator.current_git_commit_for_code_root
            self.validator.current_git_commit_for_code_root = lambda _: "a" * 40
            try:
                findings, _ = self.validator.validate_practical_workflow_version_gate(
                    state,
                    workflow,
                    root,
                )
            finally:
                self.validator.current_git_commit_for_code_root = original

        finding_ids = {finding.id for finding in findings}
        self.assertIn("workflow-state-practical-code-version-stale", finding_ids)

    def test_practical_workflow_requires_current_instruction_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            state = {
                "route_profile": "practical_v0_8",
                "current_stage": "ft-scope-analyzer",
                "root_consistency": {"code_root": str(root)},
                "code_version_gate": {"code_commit": "a" * 40},
            }
            original = self.validator.current_git_commit_for_code_root
            self.validator.current_git_commit_for_code_root = lambda _: "a" * 40
            try:
                findings, _ = self.validator.validate_practical_instruction_context(state, workflow, root)
                state["instruction_context"] = {
                    "loaded_skill": "ft-scope-analyzer",
                    "code_commit": "a" * 40,
                }
                accepted_findings, _ = self.validator.validate_practical_instruction_context(state, workflow, root)
            finally:
                self.validator.current_git_commit_for_code_root = original

        self.assertIn(
            "workflow-state-practical-instruction-context-stale",
            {finding.id for finding in findings},
        )
        self.assertEqual([], accepted_findings)

    def test_practical_scope_input_closure_requires_relevant_figma_and_ba_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ft_root = root / "fts" / "Partners" / "Partners-v1"
            handoff = ft_root / "work" / "stage-handoffs" / "scope"
            handoff.mkdir(parents=True)
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            source_selection = handoff / "source-selection.md"
            source_selection.write_text(
                "# Отбор источников\n\n- `support/figma/figma-design-index.md`\n",
                encoding="utf-8",
            )
            brief = handoff / "scope-brief.md"
            brief.write_text("# Краткое описание области\n\n- `AS.13`\n", encoding="utf-8")
            prompt = handoff / "prompt.scope-to-writer.md"
            prompt.write_text("# Следующий этап\n", encoding="utf-8")
            figma_index = ft_root / "support" / "figma" / "figma-design-index.md"
            figma_index.parent.mkdir(parents=True)
            figma_index.write_text(
                "| figma_id | relevant_scopes |\n| --- | --- |\n| `FIGMA-001` | `9.1–9.3.3` |\n",
                encoding="utf-8",
            )
            ba_answers = ft_root / "support" / "partners-v1-ba-answers.md"
            ba_answers.parent.mkdir(parents=True, exist_ok=True)
            ba_answers.write_text("# Ответы БА\n\n- `AS.13`: уточнение.\n", encoding="utf-8")
            state = {
                "route_profile": "practical_v0_8",
                "current_stage": "ft-scope-analyzer",
                "scope_slug": "9-3-1-partner-directory",
                "required_inputs": ["source/main.docx"],
                "latest_artifacts": {
                    "source_selection": "work/stage-handoffs/scope/source-selection.md",
                    "scope_brief": "work/stage-handoffs/scope/scope-brief.md",
                    "active_transition_prompt": "work/stage-handoffs/scope/prompt.scope-to-writer.md",
                },
            }

            findings, _ = self.validator.validate_practical_scope_input_closure(
                state, workflow, root, ft_root
            )
            required_paths = [
                "support/figma/figma-design-index.md",
                "support/partners-v1-ba-answers.md",
            ]
            state["required_inputs"].extend(required_paths)
            brief.write_text(
                brief.read_text(encoding="utf-8")
                + "\n".join(f"- `{value}`" for value in required_paths)
                + "\n",
                encoding="utf-8",
            )
            prompt.write_text(
                "\n".join(f"- `{value}`" for value in required_paths) + "\n",
                encoding="utf-8",
            )
            accepted_findings, _ = self.validator.validate_practical_scope_input_closure(
                state, workflow, root, ft_root
            )

        self.assertIn("practical-scope-input-closure-incomplete", {finding.id for finding in findings})
        self.assertEqual([], accepted_findings)

    def test_practical_workflow_rejects_english_linked_visual_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ft_root = root / "fts" / "Partners" / "Partners-v1"
            handoff = ft_root / "work" / "stage-handoffs" / "scope"
            handoff.mkdir(parents=True)
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            inventory = handoff / "mockup-visual-inventory.md"
            inventory.write_text("# Mockup Visual Inventory\n\n## Metadata\n", encoding="utf-8")
            state = {
                "route_profile": "practical_v0_8",
                "latest_artifacts": {
                    "mockup_visual_inventory": "work/stage-handoffs/scope/mockup-visual-inventory.md"
                },
            }

            findings, _ = self.validator.validate_practical_linked_visual_inventory_language(
                state, workflow, root, ft_root
            )
            inventory.write_text("# Визуальный инвентарь макета\n\n## Метаданные\n", encoding="utf-8")
            accepted_findings, _ = self.validator.validate_practical_linked_visual_inventory_language(
                state, workflow, root, ft_root
            )

        self.assertIn(
            "practical-linked-visual-inventory-non-russian-visible-text",
            {finding.id for finding in findings},
        )
        self.assertEqual([], accepted_findings)

    def test_practical_writer_prompt_rejects_copied_permanent_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            handoff.mkdir()
            prompt = handoff / "prompt.scope-to-writer.md"
            prompt.write_text(
                "\n".join(
                    [
                        "## Цель этапа",
                        "Подготовить матрицу тест-дизайна.",
                        "## Входные артефакты",
                        "- `scope-brief.md`",
                        "## Обязательные действия",
                        "- Создать матрицу.",
                        "## Не делать",
                        "- Не создавать benchmark.",
                        "## Ожидаемые выходы",
                        "- `test-design-matrix.md`.",
                        "## Gate завершения",
                        "Матрица готова.",
                    ]
                ),
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")

            findings, _ = self.validator.validate_active_transition_prompt(prompt, workflow, root, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-prompt-copies-permanent-guardrails", finding_ids)

    def test_scope_brief_rejects_generic_autofill_target_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Действие выполняется для подготовленного объекта.",
                    "Автозаполнение базовых атрибутов выполняется после выбора подсказки.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-autofill-targets-unspecified", finding_ids)

    def test_scope_brief_rejects_aggregated_field_obligations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Действие выполняется для подготовленного объекта.",
                    "Поля Юр. адрес, КПП и ОГРН имеют корректный формат.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-aggregated-field-obligations", finding_ids)

    def test_scope_brief_rejects_multiple_autofill_targets_in_one_atom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Действие выполняется для подготовленного объекта.",
                    "Выбор подсказки DaData заполняет полное наименование, юридический адрес и ИНН.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-aggregated-autofill-targets", finding_ids)

    def test_scope_brief_rejects_mixed_autofill_and_manual_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Действие выполняется для подготовленного объекта.",
                    "КПП допускает автозаполнение DaData или ручной ввод как текст.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-mixed-input-mechanisms", finding_ids)

    def test_scope_brief_rejects_cancel_and_close_as_one_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Действие выполняется для подготовленного объекта.",
                    "Отмена и закрытие окна закрывают форму без сохранения.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-aggregated-ui-controls", finding_ids)

    def test_scope_brief_rejects_generic_calendar_date_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Действие выполняется для подготовленного объекта.",
                    "Дата аккредитации принимает корректную календарную дату.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-date-constraints-unspecified", finding_ids)

    def test_blocked_scope_transition_cannot_route_writer_conditionally(self) -> None:
        issues = self.validator.practical_scope_transition_decision_issues(
            {
                "scope": "05",
                "verdict": "blocked",
                "next_stage_transition": "writer conditional",
                "source_contradiction": "yes",
                "tc_with_status_decision": "block-source-contradiction",
            }
        )

        self.assertIn("scope=05:verdict=blocked requires next_stage_transition=writer blocked", issues)

    def test_matrix_not_created_is_a_neutral_pre_matrix_state(self) -> None:
        issues = self.validator.practical_scope_transition_decision_issues(
            {
                "scope": "05",
                "verdict": "matrix-not-created",
                "next_stage_transition": "writer conditional",
                "source_contradiction": "no",
                "tc_with_status_decision": "not-applicable",
            }
        )

        self.assertEqual([], issues)

    def test_pre_matrix_state_cannot_make_round_cap_status_decision(self) -> None:
        issues = self.validator.practical_scope_transition_decision_issues(
            {
                "scope": "05",
                "verdict": "matrix-not-created",
                "next_stage_transition": "writer conditional",
                "source_contradiction": "no",
                "tc_with_status_decision": "write-with-statuses",
            }
        )

        self.assertIn(
            "scope=05:verdict=matrix-not-created requires tc_with_status_decision=not-applicable",
            issues,
        )

    def test_practical_handoff_rejects_intermediate_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "05-scope"
            handoff.mkdir(parents=True)
            (handoff / "workflow-state.yaml").write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            (handoff / "chunks").mkdir()

            findings, _ = self.validator.validate_practical_handoff_intermediate_artifacts(
                {"route_profile": "practical_v0_8"},
                handoff / "workflow-state.yaml",
                root,
            )

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-handoff-intermediate-artifacts-present", finding_ids)

    def test_scope_analysis_source_row_count_must_match_linked_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ft_root = root / "fts" / "Sample"
            handoff = ft_root / "work" / "stage-handoffs" / "05-scope"
            handoff.mkdir(parents=True)
            inventory = handoff / "source-row-inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "## Реестр строк источника",
                        "",
                        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                        "| --- | --- | --- | --- | --- | --- | --- |",
                        "| `SRC-001` | `PKG-01` | Поле A | Таблица 1 | `AS.1` | `yes` | `ATOM-001` |",
                        "| `SRC-002` | `PKG-01` | Поле B | Таблица 1 | `AS.2` | `yes` | `ATOM-002` |",
                    ]
                ),
                encoding="utf-8",
            )
            (handoff / "workflow-state.yaml").write_text(
                "\n".join(
                    [
                        "route_profile: practical_v0_8",
                        "latest_artifacts:",
                        "  source_row_inventory: work/stage-handoffs/05-scope/source-row-inventory.md",
                    ]
                ),
                encoding="utf-8",
            )

            issues = self.validator.practical_stage_summary_source_row_count_issues(
                {
                    "summary_stage": "scope-analysis",
                    "ft_package_root": str(ft_root),
                    "active_scope_ids": "05",
                    "source_row_counts": "05=1",
                },
                root,
            )

        self.assertTrue(any("scope=05:declared=1; actual=2" in issue for issue in issues))

    def test_scope_analysis_source_row_count_rejects_duplicate_scope_id(self) -> None:
        issues = self.validator.practical_stage_summary_source_row_count_issues(
            {
                "summary_stage": "scope-analysis",
                "ft_package_root": "C:/sample",
                "active_scope_ids": "05",
                "source_row_counts": "05=2; 05=3",
            },
            Path("C:/"),
        )

        self.assertEqual(["source_row_counts has duplicate scope ids: 05=2; 05=3"], issues)

    def test_practical_writer_prompt_does_not_require_legacy_gap_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            handoff.mkdir()
            for name in ("source-selection.md", "scope-brief.md"):
                (handoff / name).write_text("# Артефакт\n", encoding="utf-8")
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            prompt = handoff / "prompt.scope-to-writer.md"
            prompt.write_text(
                "\n".join(
                    [
                        "## Цель этапа",
                        "Подготовить матрицу тест-дизайна.",
                        "## Входные артефакты",
                        "- `source-selection.md`",
                        "- `scope-brief.md`",
                        "- `workflow-state.yaml`",
                        "## Обязательные действия",
                        "- Создать матрицу.",
                        "## Не делать",
                        "- Не создавать тест-кейсы.",
                        "## Ожидаемые выходы",
                        "- `test-design-matrix.md`.",
                        "## Условие завершения",
                        "Матрица подготовлена.",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_active_transition_prompt(prompt, workflow, root, root)

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("prompt-format-missing-required-scope-inputs", finding_ids)

    def test_practical_scope_analyzer_rejects_legacy_gap_review_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "01-menu"
            handoff.mkdir(parents=True)
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: menu",
                        "route_profile: practical_v0_8",
                        "current_stage: ft-scope-analyzer",
                        "stage_status: ready-for-gap-review",
                        "next_skill: ft-test-case-reviewer",
                        "review_mode: scope_gap_review",
                        "required_inputs: []",
                        "latest_artifacts: {}",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_workflow_state(workflow, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-analyzer-forbidden-gap-review", finding_ids)

    def test_workflow_state_parses_visible_russian_source_inventory_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "fts" / "Sample" / "work" / "stage-handoffs" / "01-menu"
            handoff.mkdir(parents=True)
            inventory = handoff / "source-row-inventory.md"
            inventory.write_text(
                "\n".join(
                    [
                        "# Реестр строк источника",
                        "",
                        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                        "| --- | --- | --- | --- | --- | --- | --- |",
                        "| `SRC-001` | `PKG-01` | Поле | Таблица 1 | `AS.1` | `yes` | `ATOM-001` |",
                        "",
                        "## Source Table Normalization",
                    ]
                ),
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: menu",
                        "route_profile: practical_v0_8",
                        "current_stage: ft-scope-analyzer",
                        "stage_status: blocked-input",
                        "next_skill: none",
                        "required_inputs:",
                        "  - work/stage-handoffs/01-menu/source-row-inventory.md",
                        "latest_artifacts:",
                        "  source_row_inventory: work/stage-handoffs/01-menu/source-row-inventory.md",
                    ]
                ),
                encoding="utf-8",
            )

            findings, checks = self.validator.validate_workflow_state(workflow, root)

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("source-row-inventory-no-table", finding_ids)
        inventory_checks = [
            check for check in checks if check.name == "source-row-inventory"
        ]
        self.assertEqual(["pass"], [check.status for check in inventory_checks])

    def test_practical_scope_analyzer_rejects_legacy_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "01-menu"
            handoff.mkdir(parents=True)
            (handoff / "scope-contract.md").write_text("# Контракт\n", encoding="utf-8")
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: menu",
                        "route_profile: practical_v0_8",
                        "current_stage: ft-scope-analyzer",
                        "stage_status: blocked-input",
                        "next_skill: none",
                        "required_inputs: []",
                        "latest_artifacts: {}",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_workflow_state(workflow, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-analyzer-legacy-artifacts-present", finding_ids)

    def test_practical_route_does_not_emit_legacy_log_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "work" / "stage-handoffs" / "01-menu"
            handoff.mkdir(parents=True)
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                "\n".join(
                    [
                        "ft_slug: Sample",
                        "scope_slug: menu",
                        "route_profile: practical_v0_8",
                        "current_stage: ft-scope-analyzer",
                        "stage_status: blocked-input",
                        "next_skill: none",
                        "required_inputs: []",
                        "latest_artifacts: {}",
                    ]
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_workflow_state(workflow, root)

        finding_ids = {finding.id for finding in findings}
        self.assertNotIn("workflow-state-missing-session-log", finding_ids)
        self.assertNotIn("workflow-state-missing-decision-log", finding_ids)


if __name__ == "__main__":
    unittest.main()
