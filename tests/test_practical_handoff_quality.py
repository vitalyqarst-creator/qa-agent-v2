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
                        "## Source Row Inventory",
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
                        "## Source Row Inventory",
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
                        "## Source Row Inventory",
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
