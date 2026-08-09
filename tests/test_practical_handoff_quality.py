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
                    "| Идентификатор | Проверяемое утверждение | Статус исполнения |",
                    "| --- | --- | --- |",
                    "| `ATOM-001` | Действие выполняется для подготовленного объекта. | `ready` |",
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | `needs-test-data` |",
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
                    "## Source Row Inventory",
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
                    "| Идентификатор | Проверяемое утверждение | Статус исполнения |",
                    "| --- | --- | --- |",
                    "| `ATOM-001` | Архивирование доступно. | `needs-test-data` |",
                    "| `ATOM-002` | Архивирование разрешено администратору. | `needs-test-data` |",
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
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | `SO-NEG-001`; `SO-NEG-002` требуют разной проверки. | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-aggregated-oracle-obligations", finding_ids)

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


if __name__ == "__main__":
    unittest.main()
