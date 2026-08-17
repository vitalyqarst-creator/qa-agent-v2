from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.capture_dadata_fixture import capture_fixture
from scripts.create_ft_package import PACKAGE_DIRS, create_package
from scripts.runtime_review_dispatch import create_dispatch, sha256, validate_dispatch
from scripts.runtime_session_registry import (
    acknowledge_runtime,
    initialize_registry,
    record_role,
    validate_controller,
    validate_topology,
)
from scripts.runtime_traceability import extract_anchors
from scripts.validate_fixture_catalog import validate as validate_catalog
from scripts.validate_runtime_matrix import (
    validate as validate_matrix,
    validate_layout as validate_matrix_layout,
    validate_projection as validate_matrix_projection,
)
from scripts.validate_runtime_review import validate as validate_review
from scripts.validate_runtime_scope import (
    table_row_references,
    validate as validate_scope,
    validate_test_data_plan,
)
from scripts.validate_runtime_source import validate as validate_source
from scripts.validate_runtime_tc import (
    validate as validate_tc,
    validate_layout as validate_tc_layout,
    validate_projection as validate_tc_projection,
)
from scripts.validate_runtime_tree import validate as validate_tree


VALID_TC = """## TC-9.3.2-001

**Сквозной номер:** `TC-001`

**Название:** Сохранение карточки партнёра с уникальным наименованием

**Цель:** Проверить сохранение карточки с уникальным наименованием.

**Тип:** Positive

**Приоритет:** High

**Трассировка:** `M-001`; `AS.38`; Таблица 7, строка «Сохранить».

**Предусловия:**

1. Открыть карточку добавления партнёра.

**Тестовые данные:**

- `Наименование партнёра` = `ПАО СБЕРБАНК`.

**Шаги:**

1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.
2. Нажать `СОХРАНИТЬ`.

**Итоговый ожидаемый результат:** Карточка партнёра сохранена.

**Постусловия:**

- Не требуются.
"""

VALID_MATRIX = """# Матрица

| ID | Источник требования | Проверка | Профили тест-дизайна | Предусловие/исходное состояние | Конкретные тестовые данные | Ожидаемый результат | Решение | Готовность |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M-001 | SR-001; AS.38; Таблица 7, строка «Сохранить» | Сохранить карточку | базовый, жизненный-цикл-создания | Открыта форма добавления | `Наименование` = `ПАО СБЕРБАНК` | Карточка сохранена | TC | ready |
| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap | blocked-observability |
"""

VALID_INVENTORY = """# Инвентарь

| ID | Источник | Утверждение для покрытия |
| --- | --- | --- |
| SR-001 | AS.38; Таблица 7, строка «Сохранить» | Карточка сохраняется |
| SR-002 | AS.39 | Реакция на ограничение должна быть определена |

## Применённые исключения

Исключения отсутствуют.
"""

VALID_GAPS = """# Пробелы покрытия

| ID | Связанная обязанность | Источник | Класс | Недостаток источника | Что требуется для закрытия |
| --- | --- | --- | --- | --- | --- |
| GAP-001 | SR-002 | AS.39 | нет-бизнес-результата | Не определён наблюдаемый результат | Ответ БА |
"""

VALID_DATA_PLAN = """# План тестовых данных

| Группа проверок | Источник значений | Данные или контракт получения | Воспроизводимая подготовка | Готовность |
| --- | --- | --- | --- | --- |
| Сохранение карточки | первичный источник; стендовая подготовка | `Наименование` = `Проверка 001` | Создать запись с указанным наименованием. | needs-test-data |
"""

CONTROLLER_THREAD = "00000000-0000-4000-8000-000000000001"
LOCATOR_THREAD = "00000000-0000-4000-8000-000000000002"
ANALYZER_THREAD = "00000000-0000-4000-8000-000000000003"
WRITER_THREAD = "00000000-0000-4000-8000-000000000004"
MATRIX_REVIEWER_THREAD = "12345678-1234-1234-1234-123456789abc"


def create_session_topology(root: Path, scope: str) -> None:
    initialize_registry(root, CONTROLLER_THREAD, "local")
    record_role(root, "source-locator", LOCATOR_THREAD, "local")
    record_role(root, "scope-analyzer", ANALYZER_THREAD, "local", scope)
    record_role(root, "writer", WRITER_THREAD, "local", scope)


def create_matrix_dispatch(root: Path, artifact: Path, thread_id: str = "12345678-1234-1234-1234-123456789abc") -> Path:
    create_session_topology(root, "reviews")
    prompt = root / "matrix-review-prompt.md"
    prompt.write_text("Проведи независимое review matrix.\n", encoding="utf-8")
    return create_dispatch(
        root,
        artifact,
        prompt,
        root / "reviews",
        "matrix",
        thread_id,
        "local",
        "2026-08-17T00:00:00Z",
    )


def create_scope_locator(package: Path) -> None:
    source = package / "source"
    source.mkdir(parents=True, exist_ok=True)
    xhtml = source / "requirements.xhtml"
    xhtml.write_text(
        "<html><body><h1>Таблица 7 Требования</h1><table>"
        "<tr><td>Название</td><td>Примечание</td></tr>"
        "<tr><td>Сохранить</td><td>Карточка сохраняется</td></tr>"
        "</table></body></html>",
        encoding="utf-8",
    )
    mockups = package / "mockups"
    mockups.mkdir(parents=True, exist_ok=True)
    (mockups / "form.png").write_bytes(b"png")
    locator = package / "work" / "stage-handoffs" / "00-ft"
    locator.mkdir(parents=True, exist_ok=True)
    (locator / "workflow-state.yaml").write_text(
        "primary_sources:\n"
        "  - path: fts/Project/FT/source/requirements.xhtml\n"
        "    role: machine_readable_primary\n"
        "visual_sources:\n"
        "  - path: fts/Project/FT/mockups/form.png\n",
        encoding="utf-8",
    )
    initialize_registry(package, CONTROLLER_THREAD, "local")
    record_role(package, "source-locator", LOCATOR_THREAD, "local")
    record_role(package, "scope-analyzer", ANALYZER_THREAD, "local", "scope")


def create_valid_source_stage(root: Path) -> tuple[Path, Path]:
    (root / ".git").mkdir()
    package = root / "fts" / "Project" / "FT"
    source = package / "source"
    source.mkdir(parents=True)
    inputs = {
        "requirements.docx": (b"docx", "semantic_primary"),
        "requirements.xhtml": (b"<html/>", "machine_readable_primary"),
        "requirements.pdf": (b"pdf", "visual_structural_crosscheck_only"),
    }
    entries: list[tuple[str, str, str]] = []
    for name, (content, role) in inputs.items():
        path = source / name
        path.write_bytes(content)
        relative = path.relative_to(root).as_posix()
        entries.append((relative, role, hashlib.sha256(content).hexdigest()))
    (package / "support").mkdir()
    (package / "mockups").mkdir()
    (package / "test-cases").mkdir()
    (package / "AGENT-NOTES.md").write_text(
        "# Контекст\n\nrequirements.docx\nrequirements.xhtml\nrequirements.pdf\n",
        encoding="utf-8",
    )
    initialize_registry(package, CONTROLLER_THREAD, "local")
    record_role(package, "source-locator", LOCATOR_THREAD, "local")
    handoff = package / "work" / "stage-handoffs" / "00-FT"
    handoff.mkdir(parents=True)
    selection_lines = ["# Выбор источников", ""]
    workflow_lines = [
        "stage: source-locator",
        "status: completed",
        'source_selection: "fts/Project/FT/work/stage-handoffs/00-FT/source-selection.md"',
        "primary_sources:",
    ]
    for relative, role, digest in entries:
        selection_lines.append(f"- `{relative}` `{digest}` `{role}`")
        workflow_lines.extend(
            [
                f'  - path: "{relative}"',
                f"    role: {role}",
                f'    sha256: "{digest}"',
            ]
        )
    workflow_lines.extend(["support_sources:", "visual_sources:"])
    (handoff / "source-selection.md").write_text("\n".join(selection_lines) + "\n", encoding="utf-8")
    (handoff / "workflow-state.yaml").write_text("\n".join(workflow_lines) + "\n", encoding="utf-8")
    return package, handoff


class RuntimeContractTests(unittest.TestCase):
    def test_valid_source_stage_passes_projection_and_cleanliness_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package, handoff = create_valid_source_stage(Path(temporary_directory))
            self.assertEqual([], validate_source(package, handoff))

    def test_source_stage_rejects_stale_hash_and_downstream_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            (package / "source" / "requirements.docx").write_bytes(b"changed")
            (package / "test-cases" / "premature.md").write_text("# premature\n", encoding="utf-8")
            errors = validate_source(package, handoff)
            self.assertTrue(any("SHA-256 mismatch" in error for error in errors))
            self.assertTrue(any("test-case artifact" in error for error in errors))

    def test_source_stage_rejects_repository_local_temporary_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            rendered = root / "tmp" / "pdfs" / "source-locator" / "page-01.png"
            rendered.parent.mkdir(parents=True)
            rendered.write_bytes(b"png")
            errors = validate_source(package, handoff)
            self.assertTrue(any("repository-local temporary file" in error for error in errors))

    def test_late_support_update_allows_existing_downstream_but_still_requires_registration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            downstream = package / "work" / "stage-handoffs" / "9.3.1" / "scope-brief.md"
            downstream.parent.mkdir(parents=True, exist_ok=True)
            downstream.write_text("# Scope\n", encoding="utf-8")
            self.assertTrue(any("downstream" in error for error in validate_source(package, handoff)))
            self.assertEqual([], validate_source(package, handoff, allow_downstream=True))

            late_support = package / "support" / "answers.md"
            late_support.write_text("# Answers\n", encoding="utf-8")
            errors = validate_source(package, handoff, allow_downstream=True)
            self.assertTrue(any("local FT input is not registered" in error for error in errors))

    def test_existing_source_selection_can_be_reused_with_downstream_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            downstream = package / "test-cases" / "existing.md"
            downstream.parent.mkdir(parents=True, exist_ok=True)
            downstream.write_text("# Existing\n", encoding="utf-8")

            self.assertTrue(any("test-case artifact" in error for error in validate_source(package, handoff)))
            self.assertEqual([], validate_source(package, handoff, allow_downstream=True))

    def test_session_topology_requires_distinct_top_level_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            create_session_topology(root, "9.3.1-partners")
            self.assertEqual([], validate_topology(root, "writer", "9.3.1-partners"))
            self.assertEqual(
                [],
                validate_topology(
                    root,
                    "writer",
                    "9.3.1-partners",
                    "writer",
                    WRITER_THREAD,
                ),
            )

    def test_session_topology_rejects_role_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialize_registry(root, CONTROLLER_THREAD, "local")
            with self.assertRaisesRegex(ValueError, "already assigned"):
                record_role(root, "source-locator", CONTROLLER_THREAD, "local")

    def test_controller_must_acknowledge_changed_runtime_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialize_registry(root, CONTROLLER_THREAD, "local")
            with patch("scripts.runtime_session_registry.runtime_code_commit", return_value="a" * 40):
                errors = validate_controller(root, CONTROLLER_THREAD)
                self.assertTrue(any("runtime code commit changed" in error for error in errors))
                acknowledge_runtime(root, CONTROLLER_THREAD)
                self.assertEqual([], validate_controller(root, CONTROLLER_THREAD))

    def test_writer_session_cannot_be_shared_between_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            create_session_topology(root, "9.3.1-partners")
            record_role(
                root,
                "scope-analyzer",
                "00000000-0000-4000-8000-000000000005",
                "local",
                "9.3.2-card",
            )
            with self.assertRaisesRegex(ValueError, "already assigned"):
                record_role(root, "writer", WRITER_THREAD, "local", "9.3.2-card")

    def test_registered_writer_is_reused_for_bounded_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            create_session_topology(root, "9.3.1-partners")
            first = record_role(root, "writer", WRITER_THREAD, "local", "9.3.1-partners")
            second = record_role(root, "writer", WRITER_THREAD, "local", "9.3.1-partners")
            self.assertEqual(first, second)

    def test_stale_semantic_role_requires_a_fresh_session_after_runtime_update(self) -> None:
        fresh_writer = "00000000-0000-4000-8000-000000000005"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with patch("scripts.runtime_session_registry.runtime_code_commit", return_value="a" * 40):
                create_session_topology(root, "9.3.1-partners")
            with patch("scripts.runtime_session_registry.runtime_code_commit", return_value="b" * 40):
                acknowledge_runtime(root, CONTROLLER_THREAD)
                errors = validate_topology(
                    root,
                    "writer",
                    "9.3.1-partners",
                    "writer",
                    WRITER_THREAD,
                )
                self.assertTrue(any("fresh top-level session" in error for error in errors))
                with self.assertRaisesRegex(ValueError, "fresh top-level session"):
                    record_role(root, "writer", WRITER_THREAD, "local", "9.3.1-partners")
                record_role(root, "writer", fresh_writer, "local", "9.3.1-partners")
                self.assertEqual(
                    [],
                    validate_topology(
                        root,
                        "writer",
                        "9.3.1-partners",
                        "writer",
                        fresh_writer,
                    ),
                )

    def test_matrix_and_tc_reviewers_cannot_share_a_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            create_matrix_dispatch(root, artifact, MATRIX_REVIEWER_THREAD)
            prompt = root / "tc-review-prompt.md"
            prompt.write_text("Проведи независимое review тест-кейсов.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already assigned"):
                create_dispatch(
                    root,
                    artifact,
                    prompt,
                    root / "reviews",
                    "tc",
                    MATRIX_REVIEWER_THREAD,
                    "local",
                    "2026-08-17T00:02:00Z",
                )

    def test_valid_runtime_test_case_passes(self) -> None:
        self.assertEqual([], validate_tc(VALID_TC))

    def test_internal_gap_and_fixture_request_are_rejected(self) -> None:
        invalid = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- Требуется fixture DaData (`GAP-005`).",
        )
        errors = validate_tc(invalid)
        self.assertTrue(any("internal marker" in error for error in errors))
        self.assertTrue(any("dependency note" in error for error in errors))

    def test_descriptive_data_instead_of_literal_are_rejected(self) -> None:
        invalid = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- Требуется фиксированный запрос и организация из снимка DaData.",
        )
        errors = validate_tc(invalid)
        self.assertTrue(any("dependency note" in error for error in errors))
        self.assertTrue(any("concrete" in error for error in errors))

    def test_duplicate_setup_action_is_rejected(self) -> None:
        invalid = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Открыть карточку добавления партнёра.",
        )
        self.assertTrue(any("duplicated" in error for error in validate_tc(invalid)))

    def test_duplicate_test_data_keys_require_parameter_table(self) -> None:
        invalid = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.\n- `Наименование партнёра` = `ООО РОМАШКА`.",
        )
        self.assertTrue(any("duplicate test-data keys" in error for error in validate_tc(invalid)))

    def test_parameter_table_is_accepted_for_repeated_field_variants(self) -> None:
        parameterized = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "| Вариант | Поле | Значение |\n| --- | --- | --- |\n| P1 | Наименование партнёра | ПАО СБЕРБАНК |\n| P2 | Наименование партнёра | ООО РОМАШКА |",
        )
        self.assertEqual([], validate_tc(parameterized))

    def test_process_placeholder_in_test_data_is_rejected(self) -> None:
        invalid = VALID_TC.replace("`ПАО СБЕРБАНК`.", "`edit TC`.", 1)
        self.assertTrue(any("process placeholder" in error for error in validate_tc(invalid)))

    def test_candidate_ui_calibration_requires_explicit_confirmation(self) -> None:
        candidate = VALID_TC.replace(
            "**Приоритет:** High",
            "**Приоритет:** High\n\n**Статус исполнения:** candidate-ui-calibration",
        )
        self.assertTrue(any("requires 'Требуется подтверждение'" in error for error in validate_tc(candidate)))
        candidate = candidate.replace(
            "**Статус исполнения:** candidate-ui-calibration",
            "**Статус исполнения:** candidate-ui-calibration\n\n**Требуется подтверждение:** Уточнить точный вид подсветки поля.",
        )
        self.assertEqual([], validate_tc(candidate))

    def test_needs_test_data_is_allowed_only_with_concrete_tc_data(self) -> None:
        needs_data = VALID_TC.replace(
            "**Приоритет:** High",
            "**Приоритет:** High\n\n**Статус исполнения:** needs-test-data",
        )
        self.assertEqual([], validate_tc(needs_data))
        invalid = needs_data.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- Требуется подготовить запись на стенде.",
        )
        self.assertTrue(any("dependency note" in error for error in validate_tc(invalid)))

    def test_writer_and_reviewer_require_execution_gates(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runtime = (root / "references" / "runtime" / "test-case-runtime.md").read_text(encoding="utf-8")
        writer = (root / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (root / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")

        for gate in (
            "Наблюдаемость перехода",
            "Восстановление состояния",
            "Допустимость очистки",
            "Конкретность идентичности и предзаполнения",
        ):
            self.assertIn(gate, runtime)
        self.assertIn("обязательные gates", writer)
        self.assertIn("переход, изменение значения или счётчика", reviewer)
        self.assertIn("изменяющий состояние TC", reviewer)
        self.assertIn("выдуманный cleanup", reviewer)
        self.assertIn("проверки конкретной идентичности объекта", reviewer)
        self.assertIn("невидим текущему актору", reviewer)
        self.assertIn("не fail-fast проверкой", reviewer)
        self.assertIn("проверь каждый TC", reviewer)
        self.assertIn("число проверенных TC", reviewer)

    def test_matrix_roles_require_reachable_observation_points(self) -> None:
        root = Path(__file__).resolve().parents[1]
        profiles = (root / "references" / "runtime" / "test-design-profiles.md").read_text(encoding="utf-8")
        matrix = (root / "references" / "runtime" / "test-design-matrix.md").read_text(encoding="utf-8")
        writer = (root / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (root / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("достижимость точки наблюдения", profiles)
        self.assertIn("невидимость самого объекта", profiles)
        self.assertIn("gate достижимости", matrix)
        self.assertIn("достижимость каждой точки наблюдения", writer)
        self.assertIn("недостижим ему", reviewer)
        self.assertIn("логического покрытия другой строкой matrix", reviewer)

    def test_controller_operational_prompts_are_semantically_neutral(self) -> None:
        root = Path(__file__).resolve().parents[1]
        topology = (root / "references" / "runtime" / "session-topology.md").read_text(encoding="utf-8")
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("только транспортный конверт этапа", topology)
        self.assertIn("не пересказывает findings", topology)
        self.assertIn("не вводит дополнительные решения", topology)
        self.assertIn("не придумывает путь результата", topology)
        self.assertIn("нейтральным транспортным конвертом", agents)
        self.assertIn("первого отсутствующего, stale или невалидного артефакта", topology)
        self.assertIn("новый route не означает повторный source locator", agents)

    def test_tc_rejects_hybrid_state_setup_and_accepts_declarative_state(self) -> None:
        ambiguous = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Установить для партнёра статус «Скрыт» архивированием.",
        )
        errors = validate_tc(ambiguous)
        self.assertTrue(any("ambiguous one-line state setup" in error for error in errors))

        declarative = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Партнёр с ИНН `7707083893` находится в статусе `Скрыт`.",
        )
        self.assertEqual([], validate_tc(declarative))

    def test_role_based_matrix_projection_requires_explicit_login(self) -> None:
        role_matrix = VALID_MATRIX.replace(
            "базовый, жизненный-цикл-создания",
            "базовый, ролевой-доступ",
        )
        errors = validate_tc_projection(VALID_TC, role_matrix)
        self.assertTrue(any("explicit login precondition" in error for error in errors))

        with_login = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Войти пользователем с ролью `Администратор`.\n2. Открыть карточку добавления партнёра.",
        )
        self.assertEqual([], validate_tc_projection(with_login, role_matrix))

    def test_user_preparation_does_not_replace_login(self) -> None:
        invalid = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Подготовить пользователя с ролью `Администратор`.\n2. Открыть карточку добавления партнёра.",
        )
        self.assertTrue(any("does not establish the current actor" in error for error in validate_tc(invalid)))

    def test_postcondition_actor_switch_requires_login_navigation_and_lookup(self) -> None:
        inline = VALID_TC.replace(
            "- Не требуются.",
            "1. Нажать `Вернуть из архива` пользователем с ролью `Администратор`.",
        )
        self.assertTrue(any("separate explicit login" in error for error in validate_tc(inline)))

        incomplete = VALID_TC.replace(
            "- Не требуются.",
            "1. Войти пользователем с ролью `Администратор`.\n2. Нажать `Вернуть из архива`.",
        )
        self.assertTrue(any("renewed navigation and object lookup" in error for error in validate_tc(incomplete)))

        complete = VALID_TC.replace(
            "- Не требуются.",
            "1. Войти пользователем с ролью `Администратор`.\n2. Открыть список партнёров.\n3. Найти партнёра с ИНН `7707083893`.\n4. Нажать `Вернуть из архива`.",
        )
        self.assertEqual([], validate_tc(complete))

    def test_opaque_execute_step_is_rejected_but_measured_baseline_is_allowed(self) -> None:
        opaque = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Выполнить добавление партнёра с указанными данными.",
        )
        self.assertTrue(any("delegates an unspecified flow" in error for error in validate_tc(opaque)))

        measured = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.\n2. Нажать `СОХРАНИТЬ`.",
            "1. Зафиксировать исходное число карточек N.\n2. Нажать `Добавить`.\n3. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.\n4. Нажать `СОХРАНИТЬ`.\n5. Повторно определить число карточек.",
        ).replace(
            "Карточка партнёра сохранена.",
            "После сохранения число карточек равно N+1.",
        )
        self.assertEqual([], validate_tc(measured))

    def test_hover_revealed_control_requires_hover_before_every_click(self) -> None:
        hover_matrix = VALID_MATRIX.replace(
            "Сохранить карточку | базовый, жизненный-цикл-создания",
            "Навести курсор на карточку | базовый, жизненный-цикл-создания",
        ).replace(
            "Карточка сохранена | TC",
            "Доступна кнопка «Редактировать» | TC",
        )
        without_hover = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.\n2. Нажать `СОХРАНИТЬ`.",
            "1. Нажать «Редактировать».",
        )
        errors = validate_tc_projection(without_hover, hover_matrix)
        self.assertTrue(any("hover-revealed control" in error for error in errors))

        with_hover = without_hover.replace(
            "1. Нажать «Редактировать».",
            "1. Навести курсор на карточку партнёра.\n2. Нажать «Редактировать».",
        )
        self.assertEqual([], validate_tc_projection(with_hover, hover_matrix))

        postfix_matrix = hover_matrix.replace(
            "Доступна кнопка «Редактировать»",
            "Кнопка видима и доступна «Редактировать»",
        )
        self.assertTrue(any("hover-revealed control" in error for error in validate_tc_projection(without_hover, postfix_matrix)))

    def test_runtime_matrix_requires_profiles_and_valid_decisions(self) -> None:
        self.assertEqual([], validate_matrix(VALID_MATRIX))
        invalid = VALID_MATRIX.replace("базовый, жизненный-цикл-создания", "")
        self.assertTrue(any("no test-design profile" in error for error in validate_matrix(invalid)))

    def test_matrix_separates_coverage_from_execution_readiness(self) -> None:
        needs_data = VALID_MATRIX.replace("| TC | ready |", "| TC | needs-test-data |", 1)
        self.assertEqual([], validate_matrix(needs_data))
        missing_record = needs_data.replace(
            "`Наименование` = `ПАО СБЕРБАНК`",
            "Fixture отсутствует",
        )
        self.assertTrue(any("environment binding" in error for error in validate_matrix(missing_record)))
        descriptive = needs_data.replace(
            "`Наименование` = `ПАО СБЕРБАНК`",
            "Подготовленный партнёр",
        )
        self.assertTrue(any("concrete `field` = `value`" in error for error in validate_matrix(descriptive)))
        wrong_gap_readiness = VALID_MATRIX.replace(
            "| coverage-gap | blocked-observability |",
            "| coverage-gap | needs-test-data |",
        )
        self.assertTrue(any("coverage-gap readiness" in error for error in validate_matrix(wrong_gap_readiness)))

    def test_matrix_layout_requires_practical_directory_and_writer_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.1" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(VALID_MATRIX, encoding="utf-8")
            (matrix.parent / "workflow-state.yaml").write_text(
                "role: writer\n"
                'scope: "9.3.1"\n'
                "matrix_status: completed\n"
                'test_design_matrix: "work/practical/9.3.1/test-design-matrix.md"\n'
                "test_case_status: not-started\n",
                encoding="utf-8",
            )
            self.assertEqual([], validate_matrix_layout(matrix, package))
            wrong = package / "work" / "stage-handoffs" / "9.3.1" / "test-design-matrix.md"
            wrong.parent.mkdir(parents=True)
            wrong.write_text(VALID_MATRIX, encoding="utf-8")
            self.assertTrue(any("work" in error and "practical" in error for error in validate_matrix_layout(wrong, package)))

    def test_tc_layout_requires_writer_state_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.1" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(VALID_MATRIX, encoding="utf-8")
            test_cases = package / "test-cases" / "9.3.1-partners.md"
            test_cases.parent.mkdir()
            test_cases.write_text(VALID_TC, encoding="utf-8")
            (matrix.parent / "workflow-state.yaml").write_text(
                "role: writer\n"
                'scope: "9.3.1"\n'
                "matrix_status: completed\n"
                'test_design_matrix: "work/practical/9.3.1/test-design-matrix.md"\n'
                "test_case_status: completed\n"
                'test_cases: "test-cases/9.3.1-partners.md"\n',
                encoding="utf-8",
            )
            self.assertEqual([], validate_tc_layout(test_cases, matrix, package))
            (matrix.parent / "workflow-state.yaml").write_text(
                "role: writer\n"
                'scope: "9.3.1"\n'
                "matrix_status: completed\n"
                'test_design_matrix: "work/practical/9.3.1/test-design-matrix.md"\n'
                "test_case_status: not-started\n",
                encoding="utf-8",
            )
            self.assertTrue(any("test-case status" in error for error in validate_tc_layout(test_cases, matrix, package)))

    def test_requirement_ranges_expand_to_individual_traceability_anchors(self) -> None:
        self.assertTrue({"CODE:AS.6", "CODE:AS.7", "CODE:AS.8"}.issubset(extract_anchors("AS.6-AS.8")))

    def test_matrix_projection_preserves_inventory_and_coverage_gaps(self) -> None:
        self.assertEqual([], validate_matrix_projection(VALID_MATRIX, VALID_INVENTORY, VALID_GAPS))
        missing_gap = VALID_MATRIX.replace("GAP-001", "M-002", 1)
        self.assertTrue(any("GAP-001" in error for error in validate_matrix_projection(missing_gap, VALID_INVENTORY, VALID_GAPS)))
        missing_source = VALID_MATRIX.replace("AS.38; Таблица 7", "Таблица 7", 1)
        self.assertTrue(any("AS.38" in error for error in validate_matrix_projection(missing_source, VALID_INVENTORY, VALID_GAPS)))
        missing_inventory_row = VALID_MATRIX.replace("SR-002; AS.39", "AS.39", 1)
        self.assertTrue(any("SR-002" in error for error in validate_matrix_projection(missing_inventory_row, VALID_INVENTORY, VALID_GAPS)))
        aggregated_gap = VALID_MATRIX.replace(
            "| GAP-001 | SR-002; AS.39",
            "| GAP-001 | SR-001; SR-002; AS.39",
        )
        self.assertTrue(
            any(
                "must project only linked obligation SR-002" in error
                for error in validate_matrix_projection(aggregated_gap, VALID_INVENTORY, VALID_GAPS)
            )
        )
        malformed_gaps = VALID_GAPS.replace("| GAP-001 | SR-002 |", "| GAP-001 | SR-001; SR-002 |")
        self.assertTrue(
            any(
                "must link exactly one atomic SR obligation" in error
                for error in validate_matrix_projection(VALID_MATRIX, VALID_INVENTORY, malformed_gaps)
            )
        )
        unknown_source_gap = VALID_GAPS.replace("| GAP-001 | SR-002 |", "| GAP-001 | SR-999 |")
        self.assertTrue(
            any(
                "SR-999 is absent from active inventory" in error
                for error in validate_matrix_projection(VALID_MATRIX, VALID_INVENTORY, unknown_source_gap)
            )
        )
        invalid_class = VALID_GAPS.replace("нет-бизнес-результата", "нет-тестовых-данных")
        self.assertTrue(
            any(
                "unsupported coverage-gap class" in error
                for error in validate_matrix_projection(VALID_MATRIX, VALID_INVENTORY, invalid_class)
            )
        )
        environment_gap = VALID_GAPS.replace(
            "Не определён наблюдаемый результат | Ответ БА",
            "Нет готового партнёра на стенде | Предоставить стендовую запись",
        )
        self.assertTrue(
            any(
                "execution readiness, not a coverage gap" in error
                for error in validate_matrix_projection(VALID_MATRIX, VALID_INVENTORY, environment_gap)
            )
        )

    def test_tc_projection_requires_every_executable_matrix_source(self) -> None:
        self.assertEqual([], validate_tc_projection(VALID_TC, VALID_MATRIX))
        expanded = VALID_MATRIX.replace(
            "| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap | blocked-observability |",
            "| M-002 | SR-002; AS.39 | Проверить второе правило | базовый | Открыта форма | Не требуются. | Второе правило выполнено | TC | ready |",
        )
        errors = validate_tc_projection(VALID_TC, expanded)
        self.assertTrue(any("M-002" in error for error in errors))
        self.assertTrue(any("AS.39" in error for error in errors))

    def test_tc_projection_requires_matrix_row_and_its_primary_source_in_same_tc(self) -> None:
        missing_matrix_id = VALID_TC.replace("`M-001`; ", "")
        self.assertTrue(any("M-001" in error for error in validate_tc_projection(missing_matrix_id, VALID_MATRIX)))
        missing_primary_source = VALID_TC.replace("`AS.38`; ", "")
        self.assertTrue(any("linked to M-001 omits AS.38" in error for error in validate_tc_projection(missing_primary_source, VALID_MATRIX)))

    def test_scope_validator_rejects_answered_question_and_omitted_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            support = package / "support"
            support.mkdir(parents=True)
            answers = support / "answers.md"
            answers.write_text(
                "### CLR-OLD\n"
                "related_ft_reference: AS.7\n"
                "question: Как выполняется подтверждение вторым сотрудником?\n"
                "response_status: answered\n"
                "residual_missing: none\n",
                encoding="utf-8",
            )
            locator = package / "work" / "stage-handoffs" / "00-ft"
            locator.mkdir(parents=True)
            (locator / "workflow-state.yaml").write_text(
                "support_sources:\n"
                "  - path: fts/Project/FT/support/answers.md\n"
                "    role: approved_ba_answers\n",
                encoding="utf-8",
            )
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(VALID_INVENTORY, encoding="utf-8")
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text(
                "# Вопросы\n\n## CLR-001 — подтверждение\n\n"
                "**Вопрос:** Как выполняется подтверждение вторым сотрудником?\n\n"
                "**Основание в ФТ:** AS.7.\n\n"
                "**Влияние на покрытие:** Проверка невозможна.\n\n"
                "**Текущее состояние:** Ответ не получен.\n",
                encoding="utf-8",
            )
            (scope / "scope-brief.md").write_text("# Границы\n\nРаздел подтверждён.\n", encoding="utf-8")
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Не создавай matrix-строки для GAP-001.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("approved answer" in error for error in errors))
            self.assertTrue(any("fully answered" in error for error in errors))
            self.assertTrue(any("omit coverage-gap" in error for error in errors))
            self.assertTrue(any("Russian wording" in error for error in errors))
            self.assertTrue(any("visual cross-check" in error for error in errors))

    def test_scope_validator_accepts_compact_russian_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Сохранить», примечание"),
                encoding="utf-8",
            )
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\nОткрытые вопросы отсутствуют.\n", encoding="utf-8"
            )
            (scope / "scope-brief.md").write_text(
                "# Границы\n\nРаздел подтверждён.\n\n"
                "## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма добавления | `fts/Project/FT/mockups/form.png` | Подтверждены подписи и путь открытия. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text(
                VALID_DATA_PLAN, encoding="utf-8"
            )
            (scope / "prompt.scope-to-writer.md").write_text(
                "Создай матрицу по всем строкам инвентаря. Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            self.assertEqual([], validate_scope(package, scope))

            (scope / "coverage-gaps.md").write_text(
                VALID_GAPS.replace(
                    "Не определён наблюдаемый результат | Ответ БА",
                    "Нет готового партнёра на стенде | Подготовить стендовую запись",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("execution readiness, not a coverage gap" in error for error in errors))
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")

            (scope / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\n## CLR-001 — стендовые записи\n\n"
                "**Вопрос:** Предоставьте готового партнёра и учётную запись тестовой среды для AS.39.\n\n"
                "**Основание в ФТ:** AS.39.\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("test-data provisioning" in error for error in errors))

            (scope / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\n## Q-001 — неверный идентификатор\n\n"
                "**Вопрос:** Какое поведение задано AS.39?\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("must use CLR-* ID" in error for error in errors))

    def test_test_data_plan_requires_provenance_and_provider_acquisition_contract(self) -> None:
        invalid = """# План тестовых данных

| Группа проверок | Источник значений | Данные или контракт получения | Воспроизводимая подготовка | Готовность |
| --- | --- | --- | --- | --- |
| Подсказка организации | внешний сервис: Provider | `Наименование` = `ООО Тест` | Выбрать подсказку. | needs-test-data |
"""
        errors = validate_test_data_plan(invalid)
        self.assertTrue(any("must use 'Контракт получения:'" in error for error in errors))
        self.assertTrue(any("requires readiness 'требуется получение данных'" in error for error in errors))

        valid = invalid.replace(
            "`Наименование` = `ООО Тест` | Выбрать подсказку. | needs-test-data",
            "Контракт получения: запрос `Тест`; сохранить выбранное наименование и связанные реквизиты одной записи | Выбрать сохранённую подсказку. | требуется получение данных",
        )
        self.assertEqual([], validate_test_data_plan(valid))
        self.assertTrue(validate_test_data_plan("# План\n\nЗначения будут подготовлены.\n"))

    def test_scope_validator_rejects_gap_and_question_covered_by_nonblocking_working_assumption(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            support = package / "support"
            support.mkdir(exist_ok=True)
            answer = support / "working-assumption.md"
            answer.write_text(
                "### CLR-OLD\n"
                "related_ft_reference: AS.39\n"
                "question: Какая роль выполняет действие?\n"
                "user_response: >-\n"
                "  Пока использовать роль Администратор; после новой ролевой модели актуализировать проверку.\n"
                "response_status: answered\n"
                "response_type: working-assumption\n"
                "blocking: no\n"
                "residual_missing: Финальная ролевая модель появится позднее.\n",
                encoding="utf-8",
            )
            locator = package / "work" / "stage-handoffs" / "00-ft" / "workflow-state.yaml"
            locator.write_text(
                locator.read_text(encoding="utf-8")
                + "support_sources:\n"
                + "  - path: fts/Project/FT/support/working-assumption.md\n"
                + "    role: approved_ba_answers\n",
                encoding="utf-8",
            )
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(VALID_INVENTORY, encoding="utf-8")
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\n## CLR-001 — роль\n\n"
                "**Вопрос:** Какая роль выполняет действие?\n\n"
                "**Основание в ФТ:** AS.39.\n\n"
                "**Влияние на покрытие:** Нельзя определить доступ.\n\n"
                "**Текущее состояние:** Ответ не получен.\n\n"
                "**Почему существующий ответ не закрывает вопрос:** Нет финальной ролевой модели.\n",
                encoding="utf-8",
            )
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("working assumption provides current behavior" in error for error in errors))
            self.assertTrue(any("working assumption already provides current behavior" in error for error in errors))

    def test_scope_validator_rejects_invented_xhtml_table_row(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Несуществующая кнопка»"),
                encoding="utf-8",
            )
            (scope / "coverage-gaps.md").write_text("# Пробелы покрытия\n\nПробелы отсутствуют.\n", encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text("# Вопросы\n\nВопросы отсутствуют.\n", encoding="utf-8")
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text("Создай матрицу по активным строкам.\n", encoding="utf-8")
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("does not exist in table 7" in error for error in errors))

    def test_scope_validator_requires_exact_row_for_every_table_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace("Таблица 7, строка «Сохранить»", "Таблица 7"),
                encoding="utf-8",
            )
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text("# Вопросы\n\nВопросы отсутствуют.\n", encoding="utf-8")
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("without the exact first-column row name" in error for error in errors))

            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace(
                    "AS.38; Таблица 7, строка «Сохранить»",
                    "AS.38; строка «Сохранить»; табл. 7",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("instead of an abbreviated table reference" in error for error in errors))

    def test_table_row_parser_supports_nested_source_quotes(self) -> None:
        self.assertEqual(
            [("3", "Виждет «Партнер»")],
            table_row_references("AS.11; Таблица 3, строка «Виждет «Партнер»», примечание"),
        )

    def test_scope_validator_rejects_compound_table_properties_and_broad_ba_question(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            inventory = VALID_INVENTORY.replace(
                "Карточка сохраняется",
                "Поле обязательное, не редактируется и отображается информационным блоком со ссылкой",
            )
            (scope / "source-row-inventory.md").write_text(inventory, encoding="utf-8")
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\n## CLR-001 Уточнение результата\n\n"
                "**Вопрос:** Какой результат возникает помимо сохранения карточки?\n\n"
                "**Основание в ФТ:** AS.38.\n\n"
                "**Влияние на покрытие:** Нельзя завершить проверку.\n\n"
                "**Текущее состояние:** Ответ не получен.\n",
                encoding="utf-8",
            )
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("aggregates independent properties" in error for error in errors))
            self.assertTrue(any("behavior beyond the source-backed result" in error for error in errors))

    def test_scope_validator_rejects_unregistered_or_missing_visual_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            unregistered = package / "mockups" / "alias.png"
            unregistered.write_bytes(b"png")
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(VALID_INVENTORY, encoding="utf-8")
            (scope / "coverage-gaps.md").write_text("# Пробелы покрытия\n\nПробелы отсутствуют.\n", encoding="utf-8")
            (scope / "scope-clarification-requests.md").write_text("# Вопросы\n\nВопросы отсутствуют.\n", encoding="utf-8")
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `mockups/alias.png`; `mockups/missing.png` | Подтверждена форма. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text("Создай матрицу по активным строкам.\n", encoding="utf-8")
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\n"
                "visual_cross_check:\n"
                "  local_mockups:\n"
                "    - fts/Project/FT/mockups/not-there.png\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("not registered by source locator" in error and "alias.png" in error for error in errors))
            self.assertTrue(any("does not exist" in error and "missing.png" in error for error in errors))
            self.assertTrue(any("does not exist" in error and "not-there.png" in error for error in errors))

    def test_scope_validator_rejects_aggregated_and_cancelled_active_source_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir(parents=True)
            invalid_inventory = VALID_INVENTORY.replace(
                "| SR-001 | AS.38; Таблица 7, строка «Сохранить» | Карточка сохраняется |",
                "| SR-001 | AS.38-AS.39; Таблица 7, строка «Сохранить» | Операции не будет; строка не образует проверяемого поведения. |",
            )
            (scope / "source-row-inventory.md").write_text(invalid_inventory, encoding="utf-8")
            (scope / "coverage-gaps.md").write_text(
                VALID_GAPS.replace("| GAP-001 | SR-002 |", "| GAP-001 | SR-001; SR-002 |"),
                encoding="utf-8",
            )
            (scope / "scope-clarification-requests.md").write_text("# Вопросы\n\nВопросы отсутствуют.\n", encoding="utf-8")
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Список | Макет отсутствует | Использован только текст ФТ. |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text("Создай матрицу по активным строкам.\n", encoding="utf-8")
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("atomic requirement code" in error for error in errors))
            self.assertTrue(any("applied exclusions" in error for error in errors))
            self.assertTrue(any("must link exactly one atomic SR obligation" in error for error in errors))

    def test_review_record_is_bound_to_current_artifact_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            dispatch_path = create_matrix_dispatch(root, artifact)
            record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": dispatch_path.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(dispatch_path),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": "12345678-1234-1234-1234-123456789abc",
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "matrix-accepted",
                "findings": [],
            }
            review_path = root / "matrix-review.json"
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")
            self.assertEqual([], validate_review(artifact, review_path, "matrix", require_accepted=True))
            artifact.write_text(VALID_MATRIX + "\n", encoding="utf-8")
            self.assertTrue(any("stale" in error for error in validate_review(artifact, review_path, "matrix", True)))

    def test_tc_review_record_requires_proof_of_full_set_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-cases.md"
            artifact.write_text("# Набор\n\n## TC-001\n\n## TC-002\n", encoding="utf-8")
            create_session_topology(root, "reviews")
            record_role(root, "matrix-reviewer", MATRIX_REVIEWER_THREAD, "local", "reviews")
            prompt = root / "tc-review-prompt.md"
            prompt.write_text("Проведи независимое review тест-кейсов.\n", encoding="utf-8")
            reviewer_thread = "22345678-1234-1234-1234-123456789abc"
            dispatch_path = create_dispatch(
                root,
                artifact,
                prompt,
                root / "reviews",
                "tc",
                reviewer_thread,
                "local",
                "2026-08-17T00:00:00Z",
            )
            record = {
                "schema_version": 1,
                "review_kind": "tc",
                "artifact_path": "test-cases.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": dispatch_path.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(dispatch_path),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": reviewer_thread,
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "tc-accepted",
                "findings": [],
                "total_tc_count": 2,
                "reviewed_tc_count": 1,
                "review_scope_complete": False,
            }
            review_path = root / "tc-review.json"
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")

            errors = validate_review(artifact, review_path, "tc", require_accepted=True)
            self.assertTrue(any("reviewed_tc_count" in error for error in errors))
            self.assertTrue(any("review_scope_complete" in error for error in errors))
            self.assertTrue(any("Проверено TC: 2/2" in error for error in errors))

            record["reviewed_tc_count"] = 2
            record["review_scope_complete"] = True
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n\nПроверено TC: 2/2\n", encoding="utf-8")
            self.assertEqual([], validate_review(artifact, review_path, "tc", require_accepted=True))

    def test_historical_review_survives_runtime_role_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            first_dispatch = create_matrix_dispatch(root, artifact, MATRIX_REVIEWER_THREAD)
            record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": first_dispatch.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(first_dispatch),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": MATRIX_REVIEWER_THREAD,
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "matrix-accepted",
                "findings": [],
            }
            review_path = root / "matrix-review.json"
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")

            registry_path = root / "work" / "runtime-session-registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["scopes"]["reviews"]["matrix_reviewer"]["runtime_commit"] = "stale-runtime"
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            second_thread = "32345678-1234-1234-1234-123456789abc"
            second_dispatch = create_dispatch(
                root,
                artifact,
                root / "matrix-review-prompt.md",
                root / "reviews",
                "matrix",
                second_thread,
                "local",
                "2026-08-17T00:02:00Z",
            )

            self.assertNotEqual(first_dispatch, second_dispatch)
            self.assertTrue(first_dispatch.is_file())
            self.assertTrue(second_dispatch.is_file())
            self.assertEqual([], validate_review(artifact, review_path, "matrix", require_accepted=True))

    def test_subagent_cannot_be_recorded_as_independent_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            dispatch_path = create_matrix_dispatch(root, artifact)
            record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": dispatch_path.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(dispatch_path),
                "reviewer_session_type": "codex-task",
                "reviewer_session_id": "12345678-1234-1234-1234-123456789abc",
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "matrix-accepted",
                "findings": [],
            }
            review_path = root / "matrix-review.json"
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")
            self.assertTrue(any("codex-thread" in error for error in validate_review(artifact, review_path, "matrix")))

    def test_controller_dispatch_binds_artifact_prompt_and_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            dispatch_path = create_matrix_dispatch(root, artifact)
            prompt = root / "matrix-review-prompt.md"
            self.assertEqual([], validate_dispatch(root, artifact, prompt, dispatch_path, "matrix", "12345678-1234-1234-1234-123456789abc"))
            prompt.write_text("Изменённый prompt.\n", encoding="utf-8")
            self.assertTrue(any("prompt SHA-256 mismatch" in error for error in validate_dispatch(root, artifact, prompt, dispatch_path, "matrix")))

    def test_review_record_rejects_thread_id_not_owned_by_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            dispatch_path = create_matrix_dispatch(root, artifact)
            record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": dispatch_path.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(dispatch_path),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": "87654321-4321-4321-4321-cba987654321",
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "matrix-accepted",
                "findings": [],
            }
            review_path = root / "matrix-review.json"
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")
            self.assertTrue(any("differs from the review record" in error for error in validate_review(artifact, review_path, "matrix")))

    def test_review_record_without_controller_dispatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": "12345678-1234-1234-1234-123456789abc",
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "matrix-accepted",
                "findings": [],
            }
            review_path = root / "matrix-review.json"
            review_path.write_text(json.dumps(record), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")
            self.assertTrue(any("dispatch_path is required" in error for error in validate_review(artifact, review_path, "matrix")))

    def test_provider_fixture_requires_existing_snapshot_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fixtures = root / "fixtures"
            fixtures.mkdir()
            snapshot = fixtures / "FX-DADATA-PARTNER-001.response.json"
            snapshot.write_text('{"suggestions":[{"value":"ПАО СБЕРБАНК"}]}', encoding="utf-8")
            catalog = {
                "fixtures": [
                    {
                        "fixture_id": "FX-DADATA-PARTNER-001",
                        "purpose": "Подсказка организации",
                        "source_type": "provider",
                        "provider": "DaData",
                        "request": {"query": "СБЕРБАНК"},
                        "runtime_data": {"suggestion": "ПАО СБЕРБАНК"},
                        "snapshot_path": "fixtures/FX-DADATA-PARTNER-001.response.json",
                        "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                    }
                ]
            }
            catalog_path = root / "fixture-catalog.json"
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_catalog(catalog_path))
            catalog["fixtures"][0]["runtime_data"]["suggestion"] = "ООО ВЫДУМАННАЯ ОРГАНИЗАЦИЯ"
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(any("absent from provider snapshot" in error for error in validate_catalog(catalog_path)))
            catalog["fixtures"][0]["runtime_data"]["suggestion"] = "ПАО СБЕРБАНК"
            catalog["fixtures"][0]["snapshot_sha256"] = "0" * 64
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(any("SHA-256 mismatch" in error for error in validate_catalog(catalog_path)))

    def test_dadata_capture_creates_concrete_fixture_without_token(self) -> None:
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def getcode(self):
                return 200

            def read(self):
                return json.dumps(
                    {
                        "suggestions": [
                            {
                                "value": "ПАО СБЕРБАНК",
                                "data": {"inn": "7707083893", "ogrn": "1027700132195"},
                            }
                        ]
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "fixtures"
            with patch("scripts.capture_dadata_fixture.urlopen", side_effect=[Response(), Response()]):
                entry = capture_fixture(
                    kind="party",
                    query="СБЕРБАНК",
                    fixture_id="FX-DADATA-PARTNER-001",
                    purpose="Подсказка партнёра",
                    fixture_root=fixture_root,
                    token="not-written",
                )
            self.assertEqual("ПАО СБЕРБАНК", entry["runtime_data"]["suggestion"])
            self.assertEqual([], validate_catalog(fixture_root / "fixture-catalog.json"))
            snapshot = fixture_root / "FX-DADATA-PARTNER-001" / "response.json"
            self.assertNotIn("not-written", snapshot.read_text(encoding="utf-8"))

    def test_package_creator_does_not_copy_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "Partners-v1"
            create_package(package)
            self.assertEqual(set(PACKAGE_DIRS) | {"AGENT-NOTES.md"}, {item.name for item in package.iterdir()})
            self.assertFalse((package / "evals").exists())
            self.assertFalse((package / "references").exists())
            self.assertFalse((package / "scripts").exists())

    def test_runtime_tree_has_no_evals_or_legacy_skills(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], validate_tree(root))
        self.assertFalse((root / "evals").exists())
        self.assertFalse((root / "release").exists())
        self.assertFalse((root / "references" / "agent").exists())
        self.assertFalse((root / "test_case_agent").exists())
        self.assertFalse((root / "skills" / "ft-test-case-iteration").exists())
        self.assertFalse((root / "skills" / "ft-ui-automation-prep").exists())


if __name__ == "__main__":
    unittest.main()
