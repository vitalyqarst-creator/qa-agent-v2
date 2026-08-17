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
from scripts.runtime_traceability import extract_anchors
from scripts.validate_fixture_catalog import validate as validate_catalog
from scripts.validate_runtime_matrix import validate as validate_matrix, validate_projection as validate_matrix_projection
from scripts.validate_runtime_review import validate as validate_review
from scripts.validate_runtime_scope import validate as validate_scope
from scripts.validate_runtime_tc import validate as validate_tc, validate_projection as validate_tc_projection
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

| ID | Источник требования | Проверка | Профили тест-дизайна | Предусловие/исходное состояние | Конкретные тестовые данные | Ожидаемый результат | Решение |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M-001 | SR-001; AS.38; Таблица 7, строка «Сохранить» | Сохранить карточку | базовый, жизненный-цикл-создания | Открыта форма добавления | `Наименование` = `ПАО СБЕРБАНК` | Карточка сохранена | TC |
| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap |
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

| ID | Связанная обязанность | Источник | Ограничение |
| --- | --- | --- | --- |
| GAP-001 | SR-002 | AS.39 | Не определён наблюдаемый результат |
"""


def create_matrix_dispatch(root: Path, artifact: Path, thread_id: str = "12345678-1234-1234-1234-123456789abc") -> Path:
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


class RuntimeContractTests(unittest.TestCase):
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

    def test_runtime_matrix_requires_profiles_and_valid_decisions(self) -> None:
        self.assertEqual([], validate_matrix(VALID_MATRIX))
        invalid = VALID_MATRIX.replace("базовый, жизненный-цикл-создания", "")
        self.assertTrue(any("no test-design profile" in error for error in validate_matrix(invalid)))

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

    def test_tc_projection_requires_every_executable_matrix_source(self) -> None:
        self.assertEqual([], validate_tc_projection(VALID_TC, VALID_MATRIX))
        expanded = VALID_MATRIX.replace(
            "| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap |",
            "| M-002 | SR-002; AS.39 | Проверить второе правило | базовый | Открыта форма | Не требуются. | Второе правило выполнено | TC |",
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
                "# План тестовых данных\n\nКонкретные данные определены источником.\n", encoding="utf-8"
            )
            (scope / "prompt.scope-to-writer.md").write_text(
                "Создай матрицу по всем строкам инвентаря. Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text("stage: ft-scope-analyzer\n", encoding="utf-8")
            self.assertEqual([], validate_scope(package, scope))

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
