from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from scripts.capture_dadata_fixture import capture_fixture
from scripts.cleanup_runtime_temp import cleanup
from scripts.create_ft_package import PACKAGE_DIRS, create_package
from scripts.normalize_ft_source import normalize_docx
from scripts.render_runtime_pdf import parse_pages, render_pdf
from scripts.runtime_review_dispatch import create_dispatch, sha256, validate_dispatch
from scripts.runtime_review_delta import artifact_index, enrich_review_record, semantic_input_hashes, write_revision_manifest
from scripts.runtime_session_registry import (
    acknowledge_runtime,
    canonical_scope,
    inherit_scope_analyzer,
    inherit_source_locator,
    initialize_registry,
    record_role,
    required_skill_contract,
    validate_controller,
    validate_topology,
)
from scripts.runtime_traceability import diagnose_markdown_table, extract_anchors, find_markdown_table
from scripts.runtime_workflow_state import apply_review, set_pending, validate_state
from scripts.validate_fixture_catalog import validate as validate_catalog
from scripts.validate_runtime_matrix import (
    DATA_RELATION_RE as MATRIX_DATA_RELATION_RE,
    DATA_ROLE_RE as MATRIX_DATA_ROLE_RE,
    MISSING_ENVIRONMENT_GAP_RE as MATRIX_MISSING_ENVIRONMENT_GAP_RE,
    validate as validate_matrix,
    validate_layout as validate_matrix_layout,
    validate_projection as validate_matrix_projection,
)
from scripts.validate_runtime_review import (
    matrix_review_quality_blocking,
    tc_repair_stage,
    validate as validate_review,
)
from scripts.validate_runtime_scope import (
    MISSING_ENVIRONMENT_GAP_RE as SCOPE_MISSING_ENVIRONMENT_GAP_RE,
    classify_scope_error,
    duplicates_fully_answered_question,
    generic_unavailability_without_observation,
    independent_property_conflicts,
    partition_scope_findings,
    public_contract,
    scope_stage_decision,
    semantically_matching_question,
    source_row_tokens,
    table_property_coverage_errors,
    table_row_references,
    unbounded_requirement_coverage_errors,
    validate as validate_scope,
    validate_test_data_plan,
    xhtml_table_rows,
)
from scripts.validate_runtime_source import input_inventory, validate as validate_source
from scripts.validate_runtime_test_data import validate as validate_test_data
from scripts.validate_runtime_tc import (
    validate as validate_tc,
    validate_layout as validate_tc_layout,
    validate_materialized_projection,
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

| ID | Источник требования | Проверка | Профили тест-дизайна | Элемент покрытия | Предусловие/исходное состояние | Тестовые данные и отношения | Ожидаемый результат | Решение | Готовность |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M-001 | SR-001; AS.38; Таблица 7, строка «Сохранить» | Сохранить карточку | базовый, жизненный-цикл-создания | Сохранение валидной карточки | Открыта форма добавления | `Наименование` = `ПАО СБЕРБАНК` | Карточка сохранена | TC | ready |
| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | GAP-001 | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap | blocked-observability |
"""

VALID_INVENTORY = """# Инвентарь

| ID | Источник | Утверждение для покрытия |
| --- | --- | --- |
| SR-001 | AS.38; Таблица 7, строка «Сохранить» | Карточка сохраняется |
| SR-002 | AS.39 | Реакция на ограничение должна быть определена |

## Контракт проверяемости

| SR | Объект или UI-уровень | Актор и условие | Действие или событие | Наблюдаемый результат |
| --- | --- | --- | --- | --- |
| SR-001 | Карточка партнёра | Пользователь с доступом к добавлению | Нажатие кнопки сохранения после заполнения | Карточка сохранена |
| SR-002 | Карточка партнёра | Пользователь с доступом к добавлению | Нарушение ограничения AS.39 | Наблюдаемый результат не определён источником; GAP-001 |

## Применённые исключения

Исключения отсутствуют.
"""

VALID_CONSISTENCY = """

## Проверка согласованности

| Аспект | Вывод анализа | Связанные обязанности/пробелы |
| --- | --- | --- |
| Идентичность объекта | Проверяется одна создаваемая карточка партнёра. | SR-001 |
| Создание, редактирование и повторное открытие | Источник задаёт сохранение создаваемой карточки. | SR-001 |
| Поля, справочники и внешние источники | Реакция на ограничение не определена. | SR-002; GAP-001 |
"""

VALID_BOUNDARY_CONTROL = """

## Контроль границ источника

| Фрагмент | Структурный якорь | Решение | Связанные обязанности или область |
| --- | --- | --- | --- |
| Выбранный раздел | Раздел 9.3.2 — до раздела 9.3.3 | Включён | SR-001; SR-002; GAP-001 |
| Вводный текст родительского раздела | Раздел 9.3 — до раздела 9.3.1 | Не применимо: нормативный вводный текст отсутствует. | — |
| Завершающий текст родительского раздела | После раздела 9.3.3 — до раздела 9.4 | Не применимо: нормативный завершающий текст отсутствует. | — |

Нормативные родительские обязанности отсутствуют.
"""

VALID_TABLE_COVERAGE = """

## Контроль полноты строк таблиц

| Таблица | Строка | Решение | Связанные обязанности/пробелы |
| --- | --- | --- | --- |
| Таблица 7 | Сохранить | Включена | SR-001 |
"""

EMPTY_CLARIFICATION_REGISTER = """# Реестр вопросов к БА

Вопросы пока не сформированы.
"""

VALID_GAPS = """# Пробелы покрытия

| ID | Связанная обязанность | Источник | Класс | Недостаток источника | Что требуется для закрытия |
| --- | --- | --- | --- | --- | --- |
| GAP-001 | SR-002 | AS.39 | нет-бизнес-результата | Не определён наблюдаемый результат | Ответ БА |
"""

VALID_DATA_PLAN = """# План тестовых данных

| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |
| --- | --- | --- | --- | --- | --- | --- |
| Сохранение карточки | TD-PARTNER-A | первичный источник | Уникальное наименование; отсутствие дубля. | Не применимо: количественное ограничение отсутствует. | Подготовить запись на стенде с указанным в источнике наименованием. | требуется |
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


def create_accepted_matrix_review(package: Path, matrix: Path, scope: str) -> Path:
    create_session_topology(package, scope)
    prompt = package / "matrix-review-prompt.md"
    prompt.write_text("Проведи независимое review matrix.\n", encoding="utf-8")
    review_dir = package / "work" / "reviews" / scope
    dispatch_path = create_dispatch(
        package,
        matrix,
        prompt,
        review_dir,
        "matrix",
        MATRIX_REVIEWER_THREAD,
        "local",
        "2026-08-17T00:00:00Z",
    )
    record = {
        "schema_version": 1,
        "review_kind": "matrix",
        "artifact_path": matrix.relative_to(package).as_posix(),
        "artifact_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
        "dispatch_path": dispatch_path.relative_to(package).as_posix(),
        "dispatch_sha256": sha256(dispatch_path),
        "reviewer_session_type": "codex-thread",
        "reviewer_session_id": MATRIX_REVIEWER_THREAD,
        "reviewed_at": "2026-08-17T00:01:00Z",
        "verdict": "matrix-accepted",
        "findings": [],
    }
    review_path = review_dir / "matrix-review.json"
    review_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    review_path.with_suffix(".md").write_text("# Review\n", encoding="utf-8")
    return review_path


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
    (package / "work" / "scope-clarification-requests.md").write_text(
        EMPTY_CLARIFICATION_REGISTER,
        encoding="utf-8",
    )
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


def write_requirement_catalog_xhtml(package: Path) -> None:
    (package / "source" / "requirements.xhtml").write_text(
        "<html><body>"
        "<h1>9.3 Партнёры</h1>"
        "<p>AS.5 Правила уникальности:</p>"
        '<p data-list-id="as5">a. Одинаковые значения разрешены в разных карточках.</p>'
        "<h2>9.3.1 Список</h2>"
        "<p>Таблица 5 Действия</p>"
        "<table><tr><td>Название</td><td>Описание</td></tr>"
        "<tr><td>Редактировать</td><td>AS.23 Открыть окно. AS.24 Макет на Рисунок 5.</td></tr>"
        "<tr><td>Добавить</td><td>AS.25 Открыть окно на Рисунок 5.</td></tr></table>"
        "<h2>9.3.3 Карточка реквизитов</h2>"
        "<p>AS.39 Можно добавить неограниченное количество реквизитов.</p>"
        "<p>AS.40 Перевод использует реквизит.</p>"
        "<p>Рисунок 5 — карточка.</p>"
        "<h2>9.4 Следующий раздел</h2>"
        "</body></html>",
        encoding="utf-8",
    )


def create_valid_source_stage(root: Path) -> tuple[Path, Path]:
    (root / ".git").mkdir()
    package = root / "fts" / "Project" / "FT"
    source = package / "source"
    source.mkdir(parents=True)
    inputs = {
        "requirements.docx": (b"docx", "semantic_primary"),
        "requirements.xhtml": (b"<html/>", "machine_readable_primary"),
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
        "# Контекст\n\nrequirements.docx\nrequirements.xhtml\n",
        encoding="utf-8",
    )
    initialize_registry(package, CONTROLLER_THREAD, "local")
    record_role(package, "source-locator", LOCATOR_THREAD, "local")
    handoff = package / "work" / "stage-handoffs" / "00-FT"
    handoff.mkdir(parents=True)
    selection_lines = ["# Выбор источников", ""]
    workflow_lines = [
        "source_contract_version: 2",
        "stage: source-locator",
        "status: completed",
        "visual_crosscheck: not_required",
        'visual_crosscheck_reason: "Тестовый пакет не содержит визуально значимой разметки."',
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
        if role == "machine_readable_primary":
            semantic_relative, _, semantic_digest = entries[0]
            workflow_lines.extend(
                [
                    "    origin: generated",
                    f'    derived_from: "{semantic_relative}"',
                    f'    derived_from_sha256: "{semantic_digest}"',
                    '    generator: "scripts/normalize_ft_source.py"',
                ]
            )
    workflow_lines.extend(["support_sources:", "visual_sources:"])
    (handoff / "source-selection.md").write_text("\n".join(selection_lines) + "\n", encoding="utf-8")
    (handoff / "workflow-state.yaml").write_text("\n".join(workflow_lines) + "\n", encoding="utf-8")
    return package, handoff


def create_scope_handoff_inputs(package: Path, scope: str) -> Path:
    handoff = package / "work" / "stage-handoffs" / scope
    handoff.mkdir(parents=True, exist_ok=True)
    contents = {
        "workflow-state.yaml": f'scope: "{scope}"\nstage: scope-analyzer\nstatus: completed\n',
        "scope-brief.md": "# Область проверки\n\nГраница подтверждена.\n",
        "source-row-inventory.md": "# Инвентарь\n\n| ID | Источник | Утверждение |\n| --- | --- | --- |\n| SR-001 | Раздел 1 | Объект сохраняется |\n",
        "coverage-gaps.md": "# Пробелы покрытия\n\nОткрытые пробелы отсутствуют.\n",
        "test-data-plan.md": "# План тестовых данных\n\nДанные определены логически.\n",
        "prompt.scope-to-writer.md": "# Передача writer\n\nСоздай матрицу по активному инвентарю.\n",
    }
    for name, content in contents.items():
        (handoff / name).write_text(content, encoding="utf-8")
    (package / "work" / "scope-clarification-requests.md").write_text(
        "# Реестр вопросов к БА\n\nОткрытые вопросы отсутствуют.\n",
        encoding="utf-8",
    )
    return handoff


class RuntimeContractTests(unittest.TestCase):
    def test_review_validator_supports_direct_invocation(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "scripts/validate_runtime_review.py", "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_valid_source_stage_passes_projection_and_cleanliness_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package, handoff = create_valid_source_stage(Path(temporary_directory))
            self.assertEqual([], validate_source(package, handoff))

    def test_source_stage_rejects_handoff_named_after_target_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package, handoff = create_valid_source_stage(Path(temporary_directory))
            wrong = handoff.parent / "00-9.3.3"
            handoff.rename(wrong)

            errors = validate_source(package, wrong)

            self.assertTrue(
                any("do not derive the source handoff name from the target scope" in error for error in errors)
            )

    def test_scope_stage_rejects_source_handoff_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package, handoff = create_valid_source_stage(Path(temporary_directory))

            errors = validate_scope(package, handoff)

            self.assertTrue(
                any("scope handoff directory must be separate from the source handoff" in error for error in errors)
            )

    def test_source_stage_normalizes_figma_url_from_markdown_code_span(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            figma_url = "https://www.figma.com/design/file-id/design?node-id=1-2&p=f"
            (package / "AGENT-NOTES.md").write_text(
                f"- Figma: `{figma_url}`. Использовать только как визуальный вход.\n",
                encoding="utf-8",
            )
            (package / "work" / "runtime-session-registry.json").unlink()
            initialize_registry(package, CONTROLLER_THREAD, "local")
            record_role(package, "source-locator", LOCATOR_THREAD, "local")
            selection = handoff / "source-selection.md"
            selection.write_text(
                selection.read_text(encoding="utf-8")
                + f"- `{figma_url}` — Figma, visual reference only.\n",
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                workflow.read_text(encoding="utf-8")
                + "figma_sources:\n"
                + f'  - url: "{figma_url}"\n'
                + "    role: visual_reference_only\n",
                encoding="utf-8",
            )

            self.assertEqual([], validate_source(package, handoff))

    def test_source_contract_v2_requires_visual_input_only_when_declared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    "visual_crosscheck: not_required", "visual_crosscheck: required"
                ),
                encoding="utf-8",
            )
            errors = validate_source(package, handoff)
            self.assertTrue(any("no visual source is registered" in error for error in errors))

            visual = package / "source" / "requirements.pdf"
            visual.write_bytes(b"pdf")
            relative = visual.relative_to(root).as_posix()
            digest = hashlib.sha256(visual.read_bytes()).hexdigest()
            (handoff / "source-selection.md").write_text(
                (handoff / "source-selection.md").read_text(encoding="utf-8")
                + f"- `{relative}` `{digest}` `visual_structural_crosscheck_only`\n",
                encoding="utf-8",
            )
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    "visual_sources:\n",
                    "visual_sources:\n"
                    f'  - path: "{relative}"\n'
                    "    role: visual_structural_crosscheck_only\n"
                    f'    sha256: "{digest}"\n',
                ),
                encoding="utf-8",
            )
            self.assertEqual([], validate_source(package, handoff))

    def test_source_stage_enforces_input_directory_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            support = package / "support" / "cities.md"
            mockup = package / "mockups" / "form.png"
            support.write_text("Москва\n", encoding="utf-8")
            mockup.write_bytes(b"png")
            support_relative = support.relative_to(root).as_posix()
            mockup_relative = mockup.relative_to(root).as_posix()
            support_digest = hashlib.sha256(support.read_bytes()).hexdigest()
            mockup_digest = hashlib.sha256(mockup.read_bytes()).hexdigest()

            selection = handoff / "source-selection.md"
            selection.write_text(
                selection.read_text(encoding="utf-8")
                + f"- `{support_relative}` `{support_digest}` `dictionary`\n"
                + f"- `{mockup_relative}` `{mockup_digest}` `ui_mockup_reference`\n",
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            original = workflow.read_text(encoding="utf-8")
            wrong = original.replace(
                "support_sources:\nvisual_sources:\n",
                "support_sources:\n"
                f'  - path: "{mockup_relative}"\n'
                "    role: ui_mockup_reference\n"
                f'    sha256: "{mockup_digest}"\n'
                "visual_sources:\n"
                f'  - path: "{support_relative}"\n'
                "    role: dictionary\n"
                f'    sha256: "{support_digest}"\n',
            )
            workflow.write_text(wrong, encoding="utf-8")

            errors = validate_source(package, handoff)
            self.assertTrue(any("support/ must be registered in support_sources" in error for error in errors))
            self.assertTrue(any("mockups/ must be registered in visual_sources" in error for error in errors))

            correct = original.replace(
                "support_sources:\nvisual_sources:\n",
                "support_sources:\n"
                f'  - path: "{support_relative}"\n'
                "    role: dictionary\n"
                f'    sha256: "{support_digest}"\n'
                "visual_sources:\n"
                f'  - path: "{mockup_relative}"\n'
                "    role: ui_mockup_reference\n"
                f'    sha256: "{mockup_digest}"\n',
            )
            workflow.write_text(correct, encoding="utf-8")
            self.assertEqual([], validate_source(package, handoff))

    def test_source_contract_v2_accepts_native_xhtml_as_single_canonical_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            (package / "source" / "requirements.docx").unlink()
            xhtml = package / "source" / "requirements.xhtml"
            relative = xhtml.relative_to(root).as_posix()
            digest = hashlib.sha256(xhtml.read_bytes()).hexdigest()
            selection_relative = (handoff / "source-selection.md").relative_to(root).as_posix()
            (handoff / "source-selection.md").write_text(
                f"# Выбор источников\n\n- `{relative}` `{digest}` `semantic_primary+machine_readable_primary`\n",
                encoding="utf-8",
            )
            (handoff / "workflow-state.yaml").write_text(
                "source_contract_version: 2\n"
                "stage: source-locator\n"
                "status: completed\n"
                "visual_crosscheck: not_required\n"
                'visual_crosscheck_reason: "Нативный XHTML не содержит визуально значимой разметки."\n'
                f'source_selection: "{selection_relative}"\n'
                "primary_sources:\n"
                f'  - path: "{relative}"\n'
                "    role: semantic_primary+machine_readable_primary\n"
                f'    sha256: "{digest}"\n'
                "    origin: canonical\n"
                "support_sources:\n"
                "visual_sources:\n",
                encoding="utf-8",
            )
            self.assertEqual([], validate_source(package, handoff))

    def test_source_inventory_computes_hashes_and_agent_notes_role_hints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, _handoff = create_valid_source_stage(root)
            (package / "AGENT-NOTES.md").write_text(
                "- Основное ФТ (DOCX): `source/requirements.docx`.\n"
                "- Машиночитаемая версия ФТ (XHTML): `source/requirements.xhtml`.\n",
                encoding="utf-8",
            )

            inventory = input_inventory(package)

            self.assertTrue(inventory["valid"])
            self.assertEqual(
                "fts/Project/FT/source/requirements.docx",
                inventory["agent_notes_role_hints"]["semantic_primary"],
            )
            docx = next(item for item in inventory["inputs"] if item["path"].endswith("requirements.docx"))
            self.assertEqual(hashlib.sha256(b"docx").hexdigest(), docx["sha256"])

    def test_source_contract_enforces_explicit_agent_notes_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            (package / "AGENT-NOTES.md").write_text(
                "- Основное ФТ (DOCX): `source/requirements.docx`.\n"
                "- Машиночитаемая версия ФТ (XHTML): `source/requirements.xhtml`.\n",
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            content = workflow.read_text(encoding="utf-8")
            content = content.replace("role: semantic_primary", "role: temporary_role", 1)
            content = content.replace("role: machine_readable_primary", "role: semantic_primary", 1)
            content = content.replace("role: temporary_role", "role: machine_readable_primary", 1)
            workflow.write_text(content, encoding="utf-8")

            errors = validate_source(package, handoff)

            self.assertTrue(any("AGENT-NOTES.md declares" in error for error in errors))

    def test_legacy_three_file_source_selection_remains_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package, handoff = create_valid_source_stage(root)
            visual = package / "source" / "requirements.pdf"
            visual.write_bytes(b"pdf")
            sources = [
                (package / "source" / "requirements.docx", "semantic_primary"),
                (package / "source" / "requirements.xhtml", "machine_readable_primary"),
                (visual, "visual_structural_crosscheck_only"),
            ]
            selection_lines = ["# Выбор источников", ""]
            workflow_lines = [
                "stage: source-locator",
                "status: completed",
                f'source_selection: "{(handoff / "source-selection.md").relative_to(root).as_posix()}"',
                "primary_sources:",
            ]
            for source, role in sources:
                relative = source.relative_to(root).as_posix()
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
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
            self.assertEqual([], validate_source(package, handoff))

    def test_source_contract_v2_rejects_generated_extraction_from_wrong_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package, handoff = create_valid_source_stage(Path(temporary_directory))
            workflow = handoff / "workflow-state.yaml"
            content = workflow.read_text(encoding="utf-8")
            content = re.sub(r"derived_from_sha256: \"[0-9a-f]{64}\"", f'derived_from_sha256: "{"0" * 64}"', content)
            workflow.write_text(content, encoding="utf-8")
            errors = validate_source(package, handoff)
            self.assertTrue(any("derives from a different semantic hash" in error for error in errors))

    def test_docx_normalizer_preserves_headings_paragraphs_and_table_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "requirements.docx"
            destination = root / "requirements.normalized.xhtml"
            document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
  <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Раздел 9</w:t></w:r></w:p>
  <w:p><w:r><w:t>Таблица 7</w:t></w:r></w:p>
  <w:tbl>
    <w:tr><w:tc><w:p><w:r><w:t>Название</w:t></w:r></w:p></w:tc></w:tr>
    <w:tr><w:tc><w:p><w:r><w:t>Сохранить</w:t></w:r></w:p></w:tc></w:tr>
    <w:tr><w:tc><w:p><w:r><w:t>Отменить</w:t></w:r></w:p><w:p><w:r><w:t>или кнопка</w:t></w:r></w:p></w:tc></w:tr>
  </w:tbl>
</w:body></w:document>"""
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("word/document.xml", document_xml)

            normalize_docx(source, destination)

            tree = ET.parse(destination)
            visible_text = " ".join("".join(tree.getroot().itertext()).split())
            self.assertIn("Раздел 9", visible_text)
            self.assertIn("Таблица 7", visible_text)
            self.assertIn("Сохранить", visible_text)
            self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(), destination.read_text(encoding="utf-8"))
            self.assertIn("сохранить", xhtml_table_rows(destination)[7])
            self.assertIn("отменить или кнопка", xhtml_table_rows(destination)[7])

    def test_docx_normalizer_materializes_word_numbering_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "requirements.docx"
            destination = root / "requirements.normalized.xhtml"
            document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
  <w:p><w:pPr><w:pStyle w:val="CaptionTable"/></w:pPr><w:r><w:t>Требования к карточке</w:t></w:r></w:p>
  <w:tbl>
    <w:tr><w:tc><w:p><w:r><w:t>Название</w:t></w:r></w:p></w:tc></w:tr>
    <w:tr><w:tc><w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="8"/></w:numPr></w:pPr><w:r><w:t>Сохранить</w:t></w:r></w:p></w:tc></w:tr>
  </w:tbl>
</w:body></w:document>"""
            styles_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="CaptionTable"><w:name w:val="heading 5"/><w:pPr><w:numPr><w:numId w:val="12"/></w:numPr></w:pPr></w:style>
</w:styles>"""
            numbering_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="16"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="AS.%1"/></w:lvl></w:abstractNum>
  <w:abstractNum w:abstractNumId="18"><w:lvl w:ilvl="0"><w:start w:val="7"/><w:numFmt w:val="decimal"/><w:pStyle w:val="CaptionTable"/><w:lvlText w:val="Таблица %1 "/></w:lvl></w:abstractNum>
  <w:num w:numId="8"><w:abstractNumId w:val="16"/></w:num>
  <w:num w:numId="12"><w:abstractNumId w:val="18"/></w:num>
</w:numbering>"""
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
                archive.writestr("word/styles.xml", styles_xml)
                archive.writestr("word/numbering.xml", numbering_xml)

            normalize_docx(source, destination)

            tree = ET.parse(destination)
            visible_text = " ".join("".join(tree.getroot().itertext()).split())
            self.assertIn("Таблица 7 Требования к карточке", visible_text)
            self.assertIn("AS.1 Сохранить", visible_text)
            self.assertIn("as.1 сохранить", xhtml_table_rows(destination)[7])

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

    def test_session_registry_persists_explicit_dispatch_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            initialize_registry(root, CONTROLLER_THREAD, "local")
            record_role(
                root,
                "source-locator",
                LOCATOR_THREAD,
                "local",
                model="gpt-5.6-sol",
                thinking="high",
            )
            payload = json.loads((root / "work" / "runtime-session-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {"source": "explicit", "model": "gpt-5.6-sol", "thinking": "high"},
                payload["source_locator"]["dispatch_profile"],
            )
            with self.assertRaisesRegex(ValueError, "another dispatch profile"):
                record_role(root, "source-locator", LOCATOR_THREAD, "local")
            with self.assertRaisesRegex(ValueError, "requires both model and thinking"):
                record_role(
                    root,
                    "scope-analyzer",
                    ANALYZER_THREAD,
                    "local",
                    "scope",
                    model="gpt-5.6-sol",
                )

    def test_source_locator_record_is_inherited_without_fabrication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "source-run").mkdir()
            (root / "destination-run").mkdir()
            source_package, _ = create_valid_source_stage(root / "source-run")
            destination_package, _ = create_valid_source_stage(root / "destination-run")
            destination_registry = destination_package / "work" / "runtime-session-registry.json"
            destination_payload = json.loads(destination_registry.read_text(encoding="utf-8"))
            destination_payload["source_locator"] = None
            destination_registry.write_text(
                json.dumps(destination_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            source_payload = json.loads(
                (source_package / "work" / "runtime-session-registry.json").read_text(encoding="utf-8")
            )

            inherit_source_locator(destination_package, source_package)

            inherited_payload = json.loads(destination_registry.read_text(encoding="utf-8"))
            self.assertEqual(source_payload["source_locator"], inherited_payload["source_locator"])
            self.assertEqual([], validate_topology(destination_package, "source-locator"))

    def test_source_locator_inheritance_rejects_different_package_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "source-run").mkdir()
            (root / "destination-run").mkdir()
            source_package, _ = create_valid_source_stage(root / "source-run")
            destination_package, _ = create_valid_source_stage(root / "destination-run")
            destination_registry = destination_package / "work" / "runtime-session-registry.json"
            destination_payload = json.loads(destination_registry.read_text(encoding="utf-8"))
            destination_payload["source_locator"] = None
            (destination_package / "AGENT-NOTES.md").write_text("# Другой пакет\n", encoding="utf-8")
            destination_payload["package_inputs"] = {
                "agent_notes_sha256": hashlib.sha256(
                    (destination_package / "AGENT-NOTES.md").read_bytes()
                ).hexdigest()
            }
            destination_registry.write_text(
                json.dumps(destination_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "same SHA-256"):
                inherit_source_locator(destination_package, source_package)

    def test_scope_analyzer_record_is_inherited_only_for_identical_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "source-run").mkdir()
            (root / "destination-run").mkdir()
            source_package, _ = create_valid_source_stage(root / "source-run")
            destination_package, _ = create_valid_source_stage(root / "destination-run")
            create_scope_handoff_inputs(source_package, "9.3.3")
            create_scope_handoff_inputs(destination_package, "9.3.3")
            record_role(source_package, "scope-analyzer", ANALYZER_THREAD, "local", "9.3.3")

            destination_registry = destination_package / "work" / "runtime-session-registry.json"
            destination_payload = json.loads(destination_registry.read_text(encoding="utf-8"))
            destination_payload["source_locator"] = None
            destination_registry.write_text(
                json.dumps(destination_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            inherit_source_locator(destination_package, source_package)
            workflow = destination_package / "work" / "stage-handoffs" / "9.3.3" / "workflow-state.yaml"
            workflow.write_bytes(workflow.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
            inherit_scope_analyzer(destination_package, source_package, "9.3.3")

            source_payload = json.loads(
                (source_package / "work" / "runtime-session-registry.json").read_text(encoding="utf-8")
            )
            inherited_payload = json.loads(destination_registry.read_text(encoding="utf-8"))
            self.assertEqual(
                source_payload["scopes"]["9.3.3"]["scope_analyzer"],
                inherited_payload["scopes"]["9.3.3"]["scope_analyzer"],
            )
            record_role(destination_package, "writer", WRITER_THREAD, "local", "9.3.3")
            self.assertEqual([], validate_topology(destination_package, "writer", "9.3.3"))

    def test_scope_analyzer_inheritance_rejects_changed_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "source-run").mkdir()
            (root / "destination-run").mkdir()
            source_package, _ = create_valid_source_stage(root / "source-run")
            destination_package, _ = create_valid_source_stage(root / "destination-run")
            create_scope_handoff_inputs(source_package, "9.3.3")
            destination_handoff = create_scope_handoff_inputs(destination_package, "9.3.3")
            record_role(source_package, "scope-analyzer", ANALYZER_THREAD, "local", "9.3.3")

            destination_registry = destination_package / "work" / "runtime-session-registry.json"
            destination_payload = json.loads(destination_registry.read_text(encoding="utf-8"))
            destination_payload["source_locator"] = None
            destination_registry.write_text(
                json.dumps(destination_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            inherit_source_locator(destination_package, source_package)
            (destination_handoff / "scope-brief.md").write_text(
                "# Область проверки\n\nГраница изменена.\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "identical normalized"):
                inherit_scope_analyzer(destination_package, source_package, "9.3.3")

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

    def test_expected_result_allows_or_inside_quoted_ui_label(self) -> None:
        labelled = VALID_TC.replace(
            "Карточка партнёра сохранена.",
            "В форме указаны `Наименование банка или БИК` = `ПАО СБЕРБАНК`.",
        )
        self.assertEqual([], validate_tc(labelled))

    def test_expected_result_rejects_alternative_outcomes(self) -> None:
        alternative = VALID_TC.replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра сохранена или отображается ошибка.",
        )
        self.assertTrue(any("expected result must be deterministic" in error for error in validate_tc(alternative)))

    def test_system_generated_identifier_can_use_runtime_binding(self) -> None:
        bound = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Партнёр `ПАО СБЕРБАНК` создан.\n2. Зафиксировать системный ID из уведомления о создании партнёра `ПАО СБЕРБАНК` как `PARTNER-ID-01`.",
        ).replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра `ПАО СБЕРБАНК` отображает системный ID `PARTNER-ID-01`.",
        )
        self.assertEqual([], validate_tc(bound))

    def test_runtime_binding_cannot_assert_the_same_observation_it_was_captured_from(self) -> None:
        circular = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Партнёр `ПАО СБЕРБАНК` создан.",
        ).replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Зафиксировать отображаемый системный ID карточки партнёра `ПАО СБЕРБАНК` как `PARTNER-ID-01`.",
        ).replace(
            "2. Нажать `СОХРАНИТЬ`.",
            "2. Просмотреть карточку партнёра `ПАО СБЕРБАНК`.",
        ).replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра `ПАО СБЕРБАНК` отображает системный ID `PARTNER-ID-01`.",
        )
        self.assertTrue(any("same observation" in error for error in validate_tc(circular)))

        property_check = VALID_TC.replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра `ПАО СБЕРБАНК` отображает непустое значение системного ID.",
        )
        self.assertEqual([], validate_tc(property_check))

        preserved_after_transition = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Открыть карточку партнёра `ПАО СБЕРБАНК`.\n2. Зафиксировать системный ID карточки партнёра `ПАО СБЕРБАНК` как `PARTNER-ID-01`.",
        ).replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра `ПАО СБЕРБАНК` после сохранения отображает системный ID `PARTNER-ID-01`.",
        )
        self.assertEqual([], validate_tc(preserved_after_transition))

    def test_runtime_binding_must_be_reused_in_expected_result(self) -> None:
        unused = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Партнёр `ПАО СБЕРБАНК` создан.\n2. Зафиксировать системный ID из уведомления о создании партнёра `ПАО СБЕРБАНК` как `PARTNER-ID-01`.",
        )
        self.assertTrue(any("captured runtime bindings must be reused" in error for error in validate_tc(unused)))

    def test_external_run_report_does_not_define_runtime_value(self) -> None:
        external = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Партнёр имеет системный ID, зафиксированный в протоколе текущего прогона.",
        )
        self.assertTrue(any("must use an explicit capture binding" in error for error in validate_tc(external)))

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

    def test_tc_rejects_lookup_of_the_same_target_expected_to_be_absent(self) -> None:
        invalid = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Найти карточку партнёра `ПАО СБЕРБАНК`.",
        ).replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра `ПАО СБЕРБАНК` не отображается.",
        )
        self.assertTrue(any("cannot find the same target" in error for error in validate_tc(invalid)))

        valid_parent_lookup = invalid.replace(
            "Найти карточку партнёра `ПАО СБЕРБАНК`.",
            "Найти виджет группы `ПАО СБЕРБАНК`.",
        )
        self.assertFalse(any("cannot find the same target" in error for error in validate_tc(valid_parent_lookup)))

    def test_tc_rejects_reused_one_time_isolated_identity(self) -> None:
        first = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Партнёр `ПАО СБЕРБАНК` подготовлен как одноразовый изолированный объект.",
        )
        second = first.replace("TC-9.3.2-001", "TC-9.3.2-002", 1).replace("`TC-001`", "`TC-002`", 1)
        errors = validate_tc(f"{first}\n\n{second}")
        self.assertTrue(any("one-time isolated identity tuple is reused" in error for error in errors))

        distinct_second = second.replace("ПАО СБЕРБАНК", "ООО РОМАШКА")
        distinct_errors = validate_tc(f"{first}\n\n{distinct_second}")
        self.assertFalse(any("one-time isolated identity tuple is reused" in error for error in distinct_errors))

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
        fixtures = (root / "references" / "runtime" / "test-data-fixtures.md").read_text(encoding="utf-8")
        self.assertIn("Значения, создаваемые системой", fixtures)
        self.assertIn("runtime binding", fixtures)
        self.assertIn("не требуй заранее известный литерал", reviewer.casefold())
        self.assertIn("системно создаваемый output выдан за заранее известный вход", reviewer)

    def test_matrix_roles_consume_scope_quality_findings_without_reopening_scope(self) -> None:
        root = Path(__file__).resolve().parents[1]
        writer = (root / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (root / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        for instructions in (writer, reviewer):
            self.assertIn("validate_runtime_scope.py", instructions)
            self.assertIn("writer_allowed", instructions)
            self.assertIn("quality_findings", instructions)
            self.assertIn("analyzer-owned", instructions)

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

    def test_matrix_projection_preserves_exact_negative_role_visibility(self) -> None:
        inventory = VALID_INVENTORY.replace(
            "Карточка сохраняется",
            "Кнопка видима и доступна только пользователю с ролью Администратор",
        )
        matrix = VALID_MATRIX.replace(
            "Сохранить карточку",
            "Навести курсор пользователем без роли Администратор",
        ).replace(
            "Карточка сохранена",
            "Архивирование недоступно",
        )
        errors = validate_matrix_projection(matrix, inventory, VALID_GAPS)
        self.assertTrue(any("must require element absence" in error for error in errors))

        matrix = matrix.replace("Архивирование недоступно", "Кнопка Архивировать отсутствует")
        self.assertEqual([], validate_matrix_projection(matrix, inventory, VALID_GAPS))

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
        self.assertIn("repair_stage: matrix", topology)
        self.assertIn("Controller не определяет происхождение дефекта сам", topology)

        writer = (root / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(encoding="utf-8")
        reviewer = (root / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("origin_stage", reviewer)
        self.assertIn("repair_stage: matrix", writer)

    def test_scope_analyzer_has_lean_progressive_disclosure_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        skill = (root / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(encoding="utf-8")
        reference = (root / "references" / "runtime" / "scope-analysis.md").read_text(encoding="utf-8")

        self.assertLessEqual(len(agents.split()), 800)
        self.assertLessEqual(len(skill.split()), 600)
        self.assertLessEqual(len(reference.split()), 800)
        self.assertIn("AGENTS.md` уже загружен средой: не перечитывай", skill)
        self.assertIn("Один содержательный проход — default", skill)
        self.assertIn("только применимые аспекты", skill)
        self.assertIn("Сравнивай видимые подписи буквально", skill)
        self.assertIn("Не перечитывай весь DOCX/PDF", skill)
        self.assertIn("Альтернативные ключи/способы ввода", skill)
        self.assertIn("системно заполненного read-only поля", skill)
        self.assertIn("включая общее ограничение, помечай `Распределён`", reference)
        self.assertIn("Альтернативные ключи поиска или способы ввода", reference)
        self.assertIn("не проектируй недостижимое пустое состояние", reference)
        self.assertNotIn("прочитай `AGENTS.md`", skill.casefold())

    def test_scope_public_contract_exposes_authoring_schema_and_id_examples(self) -> None:
        contract = public_contract("9.1-menu-upravleniya-partnerami")

        self.assertEqual("SR-91001", contract["id_formats"]["source_row"]["example"])
        self.assertEqual(r"SR-\d{2,}", contract["id_formats"]["source_row"]["pattern"])
        self.assertIn("source-row-inventory.md", contract["required_files"])
        self.assertIn("visual_crosscheck", contract["conditional_controls"])
        self.assertEqual(["готово", "не требуется", "требуется"], contract["accepted_values"]["test_data_materialization_readiness"])
        self.assertEqual(
            "**Осталось уточнить:**",
            contract["clarification_fields"]["partial_answer_residual_heading"],
        )
        self.assertIn("| ID | Связанная обязанность |", contract["markdown_templates"]["coverage_gaps"])
        self.assertIn("**Ответ БА:** _Введите ответ здесь._", contract["markdown_templates"]["clarification_card"])
        self.assertEqual(4, contract["correction_policy"]["maximum_scope_revision_count"])
        self.assertIn("blocking_errors", contract["correction_policy"]["before_validation"])
        self.assertTrue(
            any("один основной наблюдаемый результат" in item for item in contract["atomicity_checks"])
        )
        self.assertIn("scope_revision_count: 0", contract["markdown_templates"]["workflow_state"])
        self.assertIn("status: draft", contract["markdown_templates"]["workflow_state"])
        self.assertNotIn("стендовая подготовка |", contract["markdown_templates"]["test_data"])
        self.assertIn("Контракт подтверждения:", contract["markdown_templates"]["test_data"])

        rendered_plan = "# План тестовых данных\n\n" + contract["markdown_templates"]["test_data"]
        self.assertEqual([], validate_test_data_plan(rendered_plan))

    def test_scope_public_contract_catalogs_selected_parent_and_incoming_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            write_requirement_catalog_xhtml(package)

            contract = public_contract("9.3.3", package)

            self.assertEqual(
                {"CODE:AS.39", "CODE:AS.40"},
                set(contract["selected_requirement_catalog"]),
            )
            self.assertEqual(
                ["a. Одинаковые значения разрешены в разных карточках."],
                contract["parent_intro_requirement_catalog"]["CODE:AS.5"]["list_fragments"],
            )
            self.assertEqual(
                [("AS.23", "Редактировать"), ("AS.24", "Редактировать"), ("AS.25", "Добавить")],
                [(item["code"], item["action"]) for item in contract["incoming_action_catalog"]],
            )

    def test_unbounded_requirement_needs_one_explicit_gap_per_requirement(self) -> None:
        catalog = {
            "CODE:AS.39": {
                "text": "AS.39 Система разрешает неограниченное количество объектов.",
                "list_fragments": [],
            }
        }
        inventory = {"SR-001": "AS.39", "SR-002": "AS.39"}

        errors = unbounded_requirement_coverage_errors(catalog, inventory, {})
        self.assertEqual(1, len(errors))
        self.assertIn("AS.39", errors[0])

        self.assertEqual(
            [],
            unbounded_requirement_coverage_errors(catalog, inventory, {"SR-002": {"GAP-001"}}),
        )

    def test_scope_validator_blocks_omitted_selected_parent_and_incoming_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            write_requirement_catalog_xhtml(package)
            record_role(package, "scope-analyzer", WRITER_THREAD, "local", "9.3.3")
            scope = package / "work" / "stage-handoffs" / "9.3.3"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(
                "# Инвентарь\n\n"
                "| ID | Источник | Утверждение для покрытия |\n"
                "| --- | --- | --- |\n"
                "| SR-001 | AS.39 | Реквизит можно добавить. |\n"
                "| SR-002 | AS.39 | Предел количества не доказуется конечной выборкой. |\n\n"
                "## Контракт проверяемости\n\n"
                "| SR | Объект или UI-уровень | Актор и условие | Действие или событие | Наблюдаемый результат |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| SR-001 | Карточка реквизита | Пользователь | Добавить реквизит | Реквизит добавлен |\n"
                "| SR-002 | Карточка реквизита | Пользователь | Увеличивать количество | Результат не определён; GAP-001 |\n\n"
                "## Применённые исключения\n\nИсключения отсутствуют.\n",
                encoding="utf-8",
            )
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-brief.md").write_text(
                "# Область\n\n"
                "## Контроль границ источника\n\n"
                "| Фрагмент | Структурный якорь | Решение | Связанные обязанности или область |\n"
                "| --- | --- | --- | --- |\n"
                "| Выбранный раздел | Раздел 9.3.3; AS.39; AS.40 | Включён | SR-001; SR-002; GAP-001 |\n"
                "| Вводный текст родительского раздела | AS.5 | Распределён | См. таблицу владения. |\n"
                "| Завершающий текст родительского раздела | Раздел 9.3 | Не применимо: текст отсутствует. | — |\n\n"
                "## Распределение родительских обязанностей\n\n"
                "| Источник | Родительская обязанность | Целевая область | Связанные обязанности или решение |\n"
                "| --- | --- | --- | --- |\n"
                "| AS.5 | Общее правило. | 9.3.3 | SR-002 |\n",
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text(VALID_DATA_PLAN, encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Перенеси GAP-001 в матрицу как пробел покрытия.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\nstatus: draft\nscope_revision_count: 0\n"
                'clarification_register: "work/scope-clarification-requests.md"\n',
                encoding="utf-8",
            )

            errors = validate_scope(package, scope)

            self.assertTrue(any("selected scope requirements" in error and "AS.40" in error for error in errors))
            self.assertTrue(any("incoming actions" in error and "AS.23" in error for error in errors))
            self.assertTrue(any("parent requirement AS.5 list fragment" in error for error in errors))

    def test_scope_public_contract_exposes_exact_xhtml_table_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            xhtml = package / "source" / "requirements.xhtml"
            xhtml.write_text(
                xhtml.read_text(encoding="utf-8").replace(
                    "</table>",
                    "<tr><td><p>Отменить</p><p>или кнопка</p></td><td>Карточка закрывается</td></tr></table>",
                ),
                encoding="utf-8",
            )

            contract = public_contract("9.3.3", package)
            table = contract["source_table_catalog"]["tables"]["Таблица 7"]

            self.assertTrue(contract["source_table_catalog"]["available"])
            self.assertEqual(["Название", "Примечание"], table["headers"])
            self.assertEqual(["Сохранить", "Отменить или кнопка"], table["first_column_values"])

    def test_scope_contract_cli_emits_utf8_on_windows_console(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "scripts/validate_runtime_scope.py", "--print-contract", "--scope", "9.3.3"],
            cwd=root,
            capture_output=True,
            check=False,
        )

        decoded = result.stdout.decode("utf-8")
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8", errors="replace"))
        self.assertIn("Связанная обязанность", decoded)
        self.assertNotIn("�", decoded)

    def test_scope_cli_owns_truthful_terminal_status_and_bounded_corrections(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            scope = package / "work" / "stage-handoffs" / "9.3.3"
            scope.mkdir(parents=True)
            workflow = scope / "workflow-state.yaml"
            workflow.write_text("status: completed\nscope_revision_count: 0\n", encoding="utf-8")

            first = subprocess.run(
                [sys.executable, "scripts/validate_runtime_scope.py", str(package), str(scope)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            first_payload = json.loads(first.stdout)
            self.assertTrue(first_payload["correction_allowed"])
            self.assertFalse(first_payload["writer_allowed"])
            self.assertTrue(first_payload["blocking_errors"])
            self.assertEqual("draft", first_payload["workflow_status"])
            self.assertIn("status: draft", workflow.read_text(encoding="utf-8"))

            workflow.write_text("status: completed\nscope_revision_count: 1\n", encoding="utf-8")
            second = subprocess.run(
                [sys.executable, "scripts/validate_runtime_scope.py", str(package), str(scope)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            second_payload = json.loads(second.stdout)
            self.assertTrue(second_payload["correction_allowed"])
            self.assertFalse(second_payload["writer_allowed"])
            self.assertEqual("draft", second_payload["workflow_status"])
            self.assertIn("status: draft", workflow.read_text(encoding="utf-8"))

            workflow.write_text("status: completed\nscope_revision_count: 2\n", encoding="utf-8")
            final = subprocess.run(
                [sys.executable, "scripts/validate_runtime_scope.py", str(package), str(scope)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            final_payload = json.loads(final.stdout)
            self.assertFalse(final_payload["final_closure_allowed"])
            self.assertFalse(final_payload["correction_allowed"])
            self.assertFalse(final_payload["writer_allowed"])
            self.assertEqual("failed", final_payload["workflow_status"])
            self.assertIn("status: failed", workflow.read_text(encoding="utf-8"))

    def test_scope_decision_allows_only_narrow_final_closure(self) -> None:
        eligible = scope_stage_decision(
            [
                "SR-001: active source row must contain one atomic requirement code",
                "AS.39: an unbounded quantitative requirement needs an explicit GAP-*",
            ],
            2,
        )
        self.assertTrue(eligible["final_closure_allowed"])
        self.assertTrue(eligible["correction_allowed"])
        self.assertEqual("draft", eligible["workflow_status"])

        too_many = scope_stage_decision(
            [
                "SR-001: active source row must contain one atomic requirement code",
                "AS.39: an unbounded quantitative requirement needs an explicit GAP-*",
                "source-row-inventory has no required source rows table",
            ],
            2,
        )
        self.assertFalse(too_many["final_closure_allowed"])
        self.assertFalse(too_many["correction_allowed"])

        workflow_failed = scope_stage_decision(
            ["workflow-state must reference work/scope-clarification-requests.md"],
            2,
        )
        self.assertFalse(workflow_failed["final_closure_allowed"])
        self.assertFalse(workflow_failed["correction_allowed"])

    def test_scope_decision_allows_one_approved_answer_reconciliation(self) -> None:
        eligible = scope_stage_decision(
            [
                "GAP-002: missing environment data is execution readiness, not a coverage gap",
                "CLR-002: duplicates a fully answered approved clarification for CODE:AS.39",
                "CLR-002: approved answer source mentions its requirement; add 'Источник ответа'",
            ],
            3,
        )
        self.assertTrue(eligible["answer_reconciliation_allowed"])
        self.assertTrue(eligible["correction_allowed"])

        unrelated = scope_stage_decision(
            ["SR-001: active source row must contain one atomic requirement code"],
            3,
        )
        self.assertFalse(unrelated["answer_reconciliation_allowed"])
        self.assertFalse(unrelated["correction_allowed"])

        exhausted = scope_stage_decision(
            ["CLR-002: approved answer source mentions its requirement"],
            4,
        )
        self.assertFalse(exhausted["answer_reconciliation_allowed"])
        self.assertFalse(exhausted["correction_allowed"])

    def test_scope_decision_allows_narrow_validator_repair_at_count_four(self) -> None:
        eligible = scope_stage_decision(
            [
                "AS.39: an unbounded quantitative requirement needs an explicit GAP-*; a finite sample cannot prove absence of a limit",
                "CLR-002: answered or cancelled clarification still links open coverage gaps: GAP-002",
            ],
            4,
        )
        self.assertTrue(eligible["validator_repair_allowed"])
        self.assertTrue(eligible["correction_allowed"])
        self.assertEqual(4, eligible["scope_revision_count"])

        unrelated = scope_stage_decision(
            [
                "AS.39: an unbounded quantitative requirement needs an explicit GAP-*; a finite sample cannot prove absence of a limit",
                "SR-001: active source row must contain one atomic requirement code",
            ],
            4,
        )
        self.assertFalse(unrelated["validator_repair_allowed"])
        self.assertFalse(unrelated["correction_allowed"])

    def test_missing_environment_gap_does_not_match_absence_of_business_limit(self) -> None:
        quantitative_gap = (
            "Конечная проверка не подтверждает отсутствие предела. Второй реквизит подтверждает только нижний порог."
        )
        missing_fixture = "Отсутствует подготовленный реквизит со статусом Подтвержден."
        for pattern in (SCOPE_MISSING_ENVIRONMENT_GAP_RE, MATRIX_MISSING_ENVIRONMENT_GAP_RE):
            self.assertIsNone(pattern.search(quantitative_gap))
            self.assertIsNotNone(pattern.search(missing_fixture))

    def test_approved_answer_matching_distinguishes_quantity_from_duplicate_identity(self) -> None:
        quantity_question = (
            "Какой проверяемый критерий подтверждает неограниченное количество реквизитов у одного партнера?"
        )
        duplicate_question = "Какие поля карточки реквизитов образуют дубль внутри одного партнера?"
        self.assertFalse(semantically_matching_question(quantity_question, duplicate_question))

        support = """### CLR-002 — status `answered`

```yaml
related_ft_reference: AS.5 cross-reference; AS.39-AS.42
question: Какие поля карточки реквизитов образуют дубль внутри одного партнера?
response_status: answered
residual_missing: none
```
"""
        self.assertFalse(
            duplicates_fully_answered_question(quantity_question, support, {"CODE:AS.39"})
        )
        self.assertTrue(
            duplicates_fully_answered_question(duplicate_question, support, {"CODE:AS.39"})
        )

    def test_scope_findings_partition_blocks_atomicity_property_and_format_defects(self) -> None:
        blocking, quality = partition_scope_findings(
            [
                "SR-001: active source row aggregates independent properties: editability, format",
                "table 8 row 'БИК': full property coverage misses autofill behavior",
                "coverage-gaps table row 1 has 5 cells but expected 6",
            ]
        )
        self.assertEqual(3, len(blocking))
        self.assertEqual(0, len(quality))
        decision = scope_stage_decision(blocking, 0)
        self.assertFalse(decision["writer_allowed"])
        self.assertEqual("draft", decision["workflow_status"])
        self.assertTrue(decision["preflight_repair_allowed"])
        self.assertFalse(decision["correction_allowed"])
        self.assertEqual(0, decision["scope_revision_count"])

        format_only = scope_stage_decision(["coverage-gaps table row 1 has 5 cells but expected 6"], 0)
        self.assertTrue(format_only["preflight_repair_allowed"])
        self.assertFalse(format_only["correction_allowed"])

    def test_scope_identity_uses_section_for_label_and_slug(self) -> None:
        self.assertEqual("9.3.3", canonical_scope("9.3.3 Карточка реквизита"))
        self.assertEqual("9.3.3", canonical_scope("9.3.3-kartochka-rekvizita"))

    def test_session_registry_accepts_and_migrates_a_legacy_human_scope_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            create_session_topology(root, "9.3.3")
            registry = root / "work" / "runtime-session-registry.json"
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["scopes"]["9.3.3 Карточка реквизита"] = payload["scopes"].pop("9.3.3")
            registry.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            self.assertEqual([], validate_topology(root, "scope-analyzer", "9.3.3-kartochka-rekvizita"))
            record_role(root, "scope-analyzer", ANALYZER_THREAD, "local", "9.3.3")
            migrated = json.loads(registry.read_text(encoding="utf-8"))
            self.assertIn("9.3.3", migrated["scopes"])
            self.assertNotIn("9.3.3 Карточка реквизита", migrated["scopes"])

    def test_atomicity_allows_one_autofill_of_required_field_but_not_format_plus_editing(self) -> None:
        self.assertEqual(
            [],
            independent_property_conflicts(
                "Система автоматически заполняет обязательное поле БИК данными банка."
            ),
        )
        self.assertEqual(
            {"редактируемость", "формат значения"},
            set(independent_property_conflicts("Пользователь может редактировать дату в формате дд.мм.гггг.")),
        )

    def test_markdown_table_rejects_a_malformed_later_row(self) -> None:
        content = (
            "| ID | SR | Источник | Класс | Недостаток | Закрытие |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| GAP-001 | SR-001 | Раздел 1 | неоднозначность-требования | Нет правила | Ответ БА |\n"
            "| GAP-002 | SR-002 | Раздел 1 | Пропущена ячейка | Ответ БА |\n"
        )
        headers = ("ID", "SR", "Источник", "Класс", "Недостаток", "Закрытие")
        self.assertIsNone(find_markdown_table(content, headers))
        self.assertIn("row 2 has 5 cells instead of 6", diagnose_markdown_table(content, headers) or "")

    def test_scope_helpers_accept_punctuated_table_anchor_and_expand_sr_ranges(self) -> None:
        self.assertEqual(
            [("8", "Расчетный счет")],
            table_row_references("Таблица 8, строка «Расчетный счет»."),
        )
        self.assertEqual(
            {"SR-933010", "SR-933011", "SR-933012"},
            source_row_tokens("SR-933010–SR-933012"),
        )
        self.assertIn(
            "TEXT:точная цитата элемента",
            extract_anchors("элемент списка «Точная цитата элемента»."),
        )

    def test_table_property_gate_detects_omitted_mandatory_behavior(self) -> None:
        errors = table_property_coverage_errors(
            8,
            "Расчетный счет",
            ("Название", "О", "Р", "Тип значения"),
            ("Расчетный счет", "Да", "Да", "Текст, только цифры"),
            {(8, "о"): "Обязательность", (8, "р"): "Редактируемость"},
            {"SR-933021"},
            {"SR-933021": "Расчётный счёт не принимает нецифровой символ."},
        )

        self.assertEqual(1, len(errors))
        self.assertIn("mandatory-field behavior", errors[0])
        self.assertEqual("completeness", classify_scope_error(errors[0]))

    def test_invalid_logical_data_origin_blocks_scope_handoff(self) -> None:
        error = (
            "test-data-plan Партнёр: 'стендовая подготовка' is an execution method, "
            "not a tester-facing value source"
        )
        self.assertEqual("source-contract", classify_scope_error(error))
        blocking, quality = partition_scope_findings([error])
        self.assertEqual([error], blocking)
        self.assertEqual([], quality)

        partial_answer = "CLR-001: partial answer requires 'Осталось уточнить'"
        blocking, quality = partition_scope_findings([partial_answer])
        self.assertEqual([partial_answer], blocking)
        self.assertEqual([], quality)

    def test_session_topology_uses_cost_aware_role_defaults(self) -> None:
        root = Path(__file__).resolve().parents[1]
        topology = (root / "references" / "runtime" / "session-topology.md").read_text(encoding="utf-8")

        self.assertIn("| `source-locator` | `gpt-5.6-luna` | `medium` |", topology)
        self.assertIn("| `scope-analyzer` | `gpt-5.6-terra` | `xhigh` |", topology)
        self.assertIn("| `writer` | `gpt-5.6-terra` | `high` |", topology)
        self.assertIn("| `matrix-reviewer` | `gpt-5.6-terra` | `xhigh` |", topology)
        self.assertIn("| `tc-reviewer` | `gpt-5.6-terra` | `xhigh` |", topology)
        self.assertIn("Модель `gpt-5.6-sol` в default route не используется", topology)

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
            "1. Войти пользователем с ролью `Администратор`.\n2. Открыть список партнёров.\n3. Найти партнёра `ПАО СБЕРБАНК`.\n4. Нажать `Вернуть из архива`.",
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

    def test_one_numbered_step_contains_one_user_action_or_verification(self) -> None:
        composite = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Открыть экран, найти партнёра и нажать его виджет.",
        )
        self.assertTrue(any("one numbered step must contain one user action" in error for error in validate_tc(composite)))

        split = VALID_TC.replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Открыть экран.\n2. Найти партнёра `ПАО СБЕРБАНК`.\n3. Нажать его виджет.",
        ).replace("2. Нажать `СОХРАНИТЬ`.", "4. Нажать `СОХРАНИТЬ`.")
        self.assertEqual([], validate_tc(split))

        quoted_button = VALID_TC.replace(
            "2. Нажать `СОХРАНИТЬ`.",
            "2. Нажать кнопку «Добавить».",
        )
        self.assertEqual([], validate_tc(quoted_button))

    def test_numbered_postcondition_cannot_combine_multiple_actions(self) -> None:
        composite = VALID_TC.replace(
            "- Не требуются.",
            "1. Открыть список и удалить созданного партнёра.",
        )
        self.assertTrue(any("one numbered postcondition" in error for error in validate_tc(composite)))

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

    def test_matrix_requires_hover_before_clicking_a_hover_revealed_control(self) -> None:
        inventory = VALID_INVENTORY.replace(
            "Карточка сохраняется",
            "При наведении на карточку доступна кнопка «Редактировать»",
        )
        matrix = VALID_MATRIX.replace(
            "Сохранить карточку",
            "Нажать «Редактировать»",
        )
        errors = validate_matrix_projection(matrix, inventory, VALID_GAPS)
        self.assertTrue(any("hover-revealed control" in error for error in errors))

        fixed = matrix.replace(
            "Нажать «Редактировать»",
            "Навести курсор на карточку и нажать «Редактировать»",
        )
        self.assertEqual([], validate_matrix_projection(fixed, inventory, VALID_GAPS))

    def test_role_only_matrix_obligation_requires_negative_branch_or_stronger_link(self) -> None:
        inventory = VALID_INVENTORY.replace(
            "Карточка сохраняется",
            "Кнопка видима и доступна только администратору",
        ).replace(
            "| SR-002 | AS.39 | Реакция на ограничение должна быть определена |",
            "| SR-002 | AS.39 | Реакция на ограничение должна быть определена |\n"
            "| SR-003 | AS.40 | Скрытая карточка не отображается пользователю без роли администратора |",
        )
        matrix = VALID_MATRIX.replace(
            "Карточка сохранена | TC | ready |",
            "Кнопка доступна администратору | TC | ready |\n"
            "| M-002 | SR-003; AS.40 | Неадминистратору открыть список | ролевой-доступ | Скрытая карточка | Карточка скрыта | `Наименование` = `ПАО СБЕРБАНК` | Карточка не отображается | TC | ready |",
        )
        errors = validate_matrix_projection(matrix, inventory, VALID_GAPS)
        self.assertTrue(any("role-only obligation" in error for error in errors))

        linked = matrix.replace(
            "Кнопка доступна администратору",
            "Кнопка доступна администратору; отрицательная ветка покрыта M-002",
        )
        self.assertEqual([], validate_matrix_projection(linked, inventory, VALID_GAPS))

    def test_generic_unavailability_requires_a_concrete_observation_surface(self) -> None:
        self.assertTrue(
            generic_unavailability_without_observation(
                "Сущность в кредитном процессе",
                "Сущность недоступна.",
            )
        )
        self.assertFalse(
            generic_unavailability_without_observation(
                "Список выбора партнёра",
                "Партнёр не отображается в списке.",
            )
        )

    def test_object_lookup_requires_concrete_test_data_literal(self) -> None:
        generic = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Найти партнёра в статусе `Подтвержден`.",
        )
        self.assertTrue(any("object lookup must use a concrete literal" in error for error in validate_tc(generic)))

        exact = generic.replace(
            "1. Найти партнёра в статусе `Подтвержден`.",
            "1. Найти партнёра `ПАО СБЕРБАНК` в статусе `Подтвержден`.",
        )
        self.assertEqual([], validate_tc(exact))

    def test_lookup_path_requires_every_declared_visible_selector_literal(self) -> None:
        nested = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- `Партнёр` = `ПАО СБЕРБАНК`.\n- `БИК` = `044525225`.\n- `Расчетный счет` = `40702810100000000001`.",
        ).replace(
            "1. В поле `Наименование партнёра` ввести `ПАО СБЕРБАНК`.",
            "1. Найти партнёра `ПАО СБЕРБАНК`, открыть его и найти реквизит по БИК `044525225`.",
        )
        errors = validate_tc(nested)
        self.assertTrue(any("missing visible selector literals" in error for error in errors))

        exact = nested.replace(
            "1. Найти партнёра `ПАО СБЕРБАНК`, открыть его и найти реквизит по БИК `044525225`.",
            "1. Найти партнёра `ПАО СБЕРБАНК`.\n"
            "2. Нажать найденный виджет.\n"
            "3. Найти реквизит по БИК `044525225` и расчетному счету `40702810100000000001`.",
        ).replace("2. Нажать `СОХРАНИТЬ`.", "4. Нажать `СОХРАНИТЬ`.")
        self.assertEqual([], validate_tc(exact))

    def test_expected_identifier_must_be_declared_in_test_data(self) -> None:
        undeclared = VALID_TC.replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра с ID `12345678` сохранена.",
        )
        self.assertTrue(any("must be declared in test data" in error for error in validate_tc(undeclared)))

        declared = undeclared.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.\n- `ID` = `12345678`.",
        )
        self.assertEqual([], validate_tc(declared))

    def test_visibility_result_identifies_the_observed_object(self) -> None:
        generic = VALID_TC.replace(
            "Карточка партнёра сохранена.",
            "Карточка партнёра отображается в списке.",
        )
        self.assertTrue(any("must identify the observed test-data object" in error for error in validate_tc(generic)))

        exact = generic.replace(
            "Карточка партнёра отображается в списке.",
            "Карточка партнёра `ПАО СБЕРБАНК` отображается в списке.",
        )
        self.assertEqual([], validate_tc(exact))

    def test_edit_prefill_result_lists_concrete_literals(self) -> None:
        generic = VALID_TC.replace(
            "Карточка партнёра сохранена.",
            "Открыто окно редактирования с заданными значениями.",
        )
        self.assertTrue(any("edit-form prefill result" in error for error in validate_tc(generic)))

        exact = generic.replace(
            "Открыто окно редактирования с заданными значениями.",
            "Открыто окно редактирования: поле `Наименование партнёра` содержит `ПАО СБЕРБАНК`.",
        )
        self.assertEqual([], validate_tc(exact))

    def test_runtime_matrix_requires_profiles_and_valid_decisions(self) -> None:
        self.assertEqual([], validate_matrix(VALID_MATRIX))
        invalid = VALID_MATRIX.replace("базовый, жизненный-цикл-создания", "")
        self.assertTrue(any("no test-design profile" in error for error in validate_matrix(invalid)))

    def test_matrix_requires_explicit_contract_for_system_generated_output(self) -> None:
        dynamic = VALID_MATRIX.replace(
            "`Наименование` = `ПАО СБЕРБАНК`",
            "`Системный ID` = `ID текущего прогона`",
        )
        self.assertTrue(any("system-generated output requires" in error for error in validate_matrix(dynamic)))

        property_contract = dynamic.replace(
            "Карточка сохранена",
            "Проверка свойства: отображается непустой системный ID",
        )
        self.assertEqual([], validate_matrix(property_contract))

    def test_traceability_supports_project_specific_codes_and_uncoded_anchors(self) -> None:
        anchors = extract_anchors(
            "REQ-7-REQ-9; BR_12; GSR 22; AS.5; Раздел 9.3.2, абзац «Карточка сохраняется»"
        )
        self.assertTrue(
            {
                "CODE:REQ-7",
                "CODE:REQ-8",
                "CODE:REQ-9",
                "CODE:BR_12",
                "CODE:GSR 22",
                "CODE:AS.5",
                "SECTION:9.3.2",
                "TEXT:карточка сохраняется",
            }.issubset(anchors)
        )

    def test_traceability_does_not_turn_lowercase_prose_before_a_number_into_a_code(self) -> None:
        anchors = extract_anchors("AS.43; размер файла не более 40 МБ")
        self.assertIn("CODE:AS.43", anchors)
        self.assertNotIn("CODE:БОЛЕЕ 40", anchors)

    def test_tc_projection_keeps_any_project_requirement_code_in_traceability_only(self) -> None:
        matrix = VALID_MATRIX.replace("AS.38", "REQ-7")
        test_case = VALID_TC.replace("AS.38", "REQ-7")
        self.assertEqual([], validate_tc_projection(test_case, matrix))

        leaked = test_case.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Согласно REQ-7 открыть карточку добавления партнёра.",
        )
        self.assertTrue(
            any("requirement codes are allowed only in traceability" in error for error in validate_tc_projection(leaked, matrix))
        )

    def test_uniqueness_requirement_requires_matching_matrix_profile(self) -> None:
        inventory = VALID_INVENTORY.replace(
            "Карточка сохраняется",
            "Дубликаты по наименованию не допускаются",
        )
        errors = validate_matrix_projection(VALID_MATRIX, inventory, VALID_GAPS)
        self.assertTrue(any("уникальность-и-дубли" in error for error in errors))

        profiled = VALID_MATRIX.replace(
            "базовый, жизненный-цикл-создания",
            "базовый, уникальность-и-дубли",
        )
        self.assertTrue(
            any("uniqueness control table" in error for error in validate_matrix(profiled))
        )
        profiled += """

## Контроль уникальности

| Бизнес-ключ и область | Создание дубликата | Самосовпадение при редактировании | Конфликт при редактировании | Тот же ключ, другое неключевое поле | Основание или исключение |
| --- | --- | --- | --- | --- | --- |
| Наименование партнёра в пределах реестра | M-001 | Не применимо: AS.1 содержит только создание. | Не применимо: AS.1 содержит только создание. | Не применимо: AS.1 содержит только создание. | SR-001; проверка создания |
"""
        self.assertEqual([], validate_matrix(profiled))
        self.assertEqual([], validate_matrix_projection(profiled, inventory, VALID_GAPS))
        unanchored = profiled.replace("Не применимо: AS.1 содержит только создание.", "Не применимо: доступно только создание.")
        self.assertTrue(
            any("must contain its own precise source anchor" in error for error in validate_matrix(unanchored))
        )

    def test_matrix_requires_explicit_coverage_item(self) -> None:
        invalid = VALID_MATRIX.replace("Сохранение валидной карточки", "")
        self.assertTrue(any("empty Элемент покрытия" in error for error in validate_matrix(invalid)))

    def test_formal_profiles_require_coverage_model_and_exact_projection(self) -> None:
        formal = VALID_MATRIX.replace(
            "базовый, жизненный-цикл-создания | Сохранение валидной карточки",
            "допустимые-классы, границы | EP-01; BVA-LOW; BVA-BOUND; BVA-ABOVE",
        )
        self.assertTrue(any("coverage model" in error for error in validate_matrix(formal)))

        formal_without_boundary_control = formal + """

## Модель покрытия

| Элемент покрытия | Техника | Параметр или условия | Класс, точка, переход или комбинация | Представитель | Ожидаемый результат | Основание |
| --- | --- | --- | --- | --- | --- | --- |
| EP-01 | классы-эквивалентности | Наименование | Допустимое значение | `ПАО СБЕРБАНК` | Значение принимается | AS.38 |
| BVA-LOW | граничные-значения | Длина наименования | Ниже нижней границы | `0 символов` | Значение не принимается | AS.38 |
| BVA-BOUND | граничные-значения | Длина наименования | На нижней границе | `1 символ` | Значение принимается | AS.38 |
| BVA-ABOVE | граничные-значения | Длина наименования | Выше нижней границы | `2 символа` | Значение принимается | AS.38 |
"""
        self.assertTrue(
            any(
                "boundary family table" in error
                for error in validate_matrix(formal_without_boundary_control)
            )
        )

        formal = formal_without_boundary_control + """

## Контроль граничных семейств

| Семейство границы | Тип границы | Точка ниже | Точка на границе | Точка выше | Ожидаемая допустимость | Основание |
| --- | --- | --- | --- | --- | --- | --- |
| Минимальная длина наименования | нижняя | BVA-LOW | BVA-BOUND | BVA-ABOVE | нет/да/да | AS.38 |
"""
        self.assertEqual([], validate_matrix(formal))

        missing_projection = formal.replace(
            "EP-01; BVA-LOW; BVA-BOUND; BVA-ABOVE",
            "EP-01; BVA-BOUND; BVA-ABOVE",
        )
        self.assertTrue(
            any("BVA-LOW is not projected" in error for error in validate_matrix(missing_projection))
        )

        wrong_technique = formal.replace(
            "| BVA-LOW | граничные-значения |",
            "| BVA-LOW | таблица-решений |",
        )
        self.assertTrue(any("technique must be" in error for error in validate_matrix(wrong_technique)))

        duplicate_projection = formal.replace(
            "EP-01; BVA-LOW; BVA-BOUND; BVA-ABOVE",
            "EP-01; BVA-LOW; BVA-BOUND; BVA-ABOVE; EP-01",
        )
        self.assertTrue(
            any("already projected" in error for error in validate_matrix(duplicate_projection))
        )

    def test_decision_state_and_combinatorial_profiles_require_matching_items(self) -> None:
        replacements = {
            "таблица-решений": "DT-R1",
            "переход-состояния": "ST-T1",
            "комбинаторный": "CT-C1",
        }
        for profile, item in replacements.items():
            with self.subTest(profile=profile):
                invalid = VALID_MATRIX.replace(
                    "базовый, жизненный-цикл-создания | Сохранение валидной карточки",
                    f"{profile} | Сохранение валидной карточки",
                )
                errors = validate_matrix(invalid)
                self.assertTrue(any(f"requires a {item[:-1]}" in error for error in errors))

    def test_dependent_mandatory_outputs_form_one_save_oracle(self) -> None:
        grouped = VALID_MATRIX.replace(
            "| M-001 | SR-001; AS.38; Таблица 7, строка «Сохранить» | Сохранить карточку | базовый, жизненный-цикл-создания | Сохранение валидной карточки | Открыта форма добавления | `Наименование` = `ПАО СБЕРБАНК` | Карточка сохранена | TC | ready |",
            "| M-001 | SR-001; SR-003; AS.38; Таблица 7, строка «Сохранить» | Нажать «Сохранить» при незаполненной зависимой группе | зависимая-обязательность | Общий отказ сохранения | Открыта форма добавления | TD-CHOICE-A; REL-FILLS-OUTPUTS | Карточка не сохраняется | TC | needs-test-data |",
        )
        self.assertEqual([], validate_matrix(grouped))
        split = grouped.replace("SR-001; SR-003", "SR-001").replace("REL-FILLS-OUTPUTS", "TD-OUTPUT-A")
        errors = validate_matrix(split)
        self.assertTrue(any("at least two SR" in error for error in errors))
        self.assertTrue(any("requires one REL" in error for error in errors))

    def test_data_role_tokens_exclude_trailing_punctuation(self) -> None:
        self.assertEqual(["TD-ACCOUNT-A"], MATRIX_DATA_ROLE_RE.findall("TD-ACCOUNT-A."))
        self.assertEqual(["REL-DIFFERENT-ACCOUNT"], MATRIX_DATA_RELATION_RE.findall("REL-DIFFERENT-ACCOUNT;"))

    def test_writer_matrix_data_plan_may_extend_but_not_weaken_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            scope = "9.3.3"
            baseline = package / "work" / "stage-handoffs" / scope / "test-data-plan.md"
            baseline.parent.mkdir(parents=True)
            baseline.write_text(VALID_DATA_PLAN, encoding="utf-8")
            matrix = package / "work" / "practical" / scope / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(
                VALID_MATRIX.replace(
                    "`Наименование` = `ПАО СБЕРБАНК`",
                    "TD-PARTNER-A; TD-ACCOUNT-B; REL-DIFFERENT-ACCOUNT",
                ),
                encoding="utf-8",
            )
            final_plan = VALID_DATA_PLAN + (
                "| Второй счёт | TD-ACCOUNT-B | синтетический генератор | "
                "REL-DIFFERENT-ACCOUNT: счёт отличается от первого. | Не применимо. | "
                "Подготовить второй счёт на стенде. | требуется |\n"
            )
            data_plan = matrix.parent / "matrix-data-plan.md"
            data_plan.write_text(final_plan, encoding="utf-8")
            set_pending(matrix)
            self.assertEqual([], validate_matrix_layout(matrix, package))

            data_plan.write_text(
                final_plan.replace(
                    "первичный источник",
                    "первичный источник; синтетический генератор",
                    1,
                ),
                encoding="utf-8",
            )
            set_pending(matrix)
            self.assertTrue(any("weakens TD-PARTNER-A" in error for error in validate_matrix_layout(matrix, package)))

    def test_matrix_workflow_state_is_hash_bound_and_rejects_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.1" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(VALID_MATRIX, encoding="utf-8")
            (matrix.parent / "matrix-data-plan.md").write_text(
                "# План данных\n\nДанные не требуются.\n", encoding="utf-8"
            )
            state = set_pending(matrix)
            self.assertEqual("review-pending", state["matrix_status"])
            self.assertEqual([], validate_state(matrix))
            state_path = matrix.parent / "workflow-state.yaml"
            state_path.write_text(
                state_path.read_text(encoding="utf-8").replace("review-pending", "completed"),
                encoding="utf-8",
            )
            self.assertTrue(any("unsupported matrix_status" in error for error in validate_state(matrix)))
            set_pending(matrix)
            state_path.write_text(
                state_path.read_text(encoding="utf-8").replace("review-pending", "accepted"),
                encoding="utf-8",
            )
            self.assertTrue(any("matrix review path is missing" in error for error in validate_state(matrix)))

            state_path.write_text(
                state_path.read_text(encoding="utf-8")
                + 'data_materialization: "work/test-data/9.3.1/data-materialization.json"\n'
                + 'test_cases: "test-cases/9.3.1.md"\n',
                encoding="utf-8",
            )
            state = set_pending(matrix)
            self.assertEqual("not-started", state["data_status"])
            self.assertEqual("not-started", state["test_case_status"])
            self.assertNotIn("data_materialization", state)
            self.assertNotIn("test_cases", state)

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
        self.assertTrue(any("requires TD-*/REL-*" in error for error in validate_matrix(descriptive)))
        wrong_gap_readiness = VALID_MATRIX.replace(
            "| coverage-gap | blocked-observability |",
            "| coverage-gap | needs-test-data |",
        )
        self.assertTrue(any("coverage-gap readiness" in error for error in validate_matrix(wrong_gap_readiness)))

    def test_workflow_apply_review_may_atomically_supersede_same_path_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.1" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(VALID_MATRIX, encoding="utf-8")
            (matrix.parent / "matrix-data-plan.md").write_text(
                "# План данных\n\nДанные не требуются.\n", encoding="utf-8"
            )
            set_pending(matrix)
            review_path = create_accepted_matrix_review(package, matrix, "9.3.1")
            first_state = apply_review(matrix, review_path)
            self.assertEqual("accepted", first_state["matrix_status"])

            replacement = json.loads(review_path.read_text(encoding="utf-8"))
            replacement["reviewed_at"] = "2026-08-17T00:02:00Z"
            replacement["verdict"] = "matrix-changes-required"
            replacement["findings"] = [
                {
                    "id": "M-R-001",
                    "severity": "material",
                    "affected_items": ["M-001"],
                    "description": "Источник идентичности не подтверждён.",
                    "required_correction": "Указать source-compatible источник.",
                }
            ]
            review_path.write_text(json.dumps(replacement, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(["matrix review SHA-256 mismatch"], validate_state(matrix))
            replacement_state = apply_review(matrix, review_path)
            self.assertEqual("changes-required", replacement_state["matrix_status"])
            self.assertEqual([], validate_state(matrix))

    def test_matrix_layout_requires_practical_directory_and_writer_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.1" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(VALID_MATRIX, encoding="utf-8")
            baseline = package / "work" / "stage-handoffs" / "9.3.1" / "test-data-plan.md"
            baseline.parent.mkdir(parents=True)
            baseline.write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            data_plan = matrix.parent / "matrix-data-plan.md"
            data_plan.write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (matrix.parent / "workflow-state.yaml").write_text(
                "role: writer\n"
                'scope: "9.3.1"\n'
                "matrix_status: review-pending\n"
                'test_design_matrix: "work/practical/9.3.1/test-design-matrix.md"\n'
                f'matrix_sha256: "{hashlib.sha256(matrix.read_bytes()).hexdigest()}"\n'
                'matrix_data_plan: "work/practical/9.3.1/matrix-data-plan.md"\n'
                "test_case_status: not-started\n",
                encoding="utf-8",
            )
            self.assertEqual([], validate_matrix_layout(matrix, package))
            wrong = package / "work" / "stage-handoffs" / "9.3.1" / "test-design-matrix.md"
            wrong.parent.mkdir(parents=True, exist_ok=True)
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
            baseline = package / "work" / "stage-handoffs" / "9.3.1" / "test-data-plan.md"
            baseline.parent.mkdir(parents=True)
            baseline.write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            data_plan = matrix.parent / "matrix-data-plan.md"
            data_plan.write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            test_cases = package / "test-cases" / "9.3.1-partners.md"
            test_cases.parent.mkdir()
            test_cases.write_text(VALID_TC, encoding="utf-8")
            set_pending(matrix)
            review_path = create_accepted_matrix_review(package, matrix, "9.3.1")
            apply_review(matrix, review_path)
            state_path = matrix.parent / "workflow-state.yaml"
            state_path.write_text(
                state_path.read_text(encoding="utf-8").replace(
                    "test_case_status: not-started",
                    "test_case_status: completed\n"
                    'test_cases: "test-cases/9.3.1-partners.md"',
                ),
                encoding="utf-8",
            )
            self.assertEqual([], validate_tc_layout(test_cases, matrix, package))
            state_path.write_text(
                state_path.read_text(encoding="utf-8").replace(
                    "test_case_status: completed", "test_case_status: not-started"
                ),
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
        resolved_gaps = VALID_GAPS.replace("Ответ БА", "Закрыт: ответ БА применён.")
        resolved_matrix = VALID_MATRIX.replace(
            "| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | GAP-001 | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap | blocked-observability |",
            "| M-002 | SR-002; AS.39 | Проверить уточнённую реакцию | базовый | Уточнённый результат | Открыта форма | `Значение` = `проверка` | Сохранение блокируется | TC | ready |",
        )
        self.assertEqual([], validate_matrix_projection(resolved_matrix, VALID_INVENTORY, resolved_gaps))
        self.assertTrue(
            any(
                "must not project resolved coverage gap GAP-001" in error
                for error in validate_matrix_projection(VALID_MATRIX, VALID_INVENTORY, resolved_gaps)
            )
        )

    def test_tc_projection_requires_every_executable_matrix_source(self) -> None:
        self.assertEqual([], validate_tc_projection(VALID_TC, VALID_MATRIX))
        expanded = VALID_MATRIX.replace(
            "| GAP-001 | SR-002; AS.39 | Проверить неизвестную реакцию | допустимые-классы | GAP-001 | Открыта форма | Не определены | Требуется уточнение результата | coverage-gap | blocked-observability |",
            "| M-002 | SR-002; AS.39 | Проверить второе правило | базовый | Второе source-backed правило | Открыта форма | Не требуются. | Второе правило выполнено | TC | ready |",
        )
        errors = validate_tc_projection(VALID_TC, expanded)
        self.assertTrue(any("M-002" in error for error in errors))
        self.assertTrue(any("AS.39" in error for error in errors))

    def test_tc_projection_preserves_exact_matrix_test_data_literal(self) -> None:
        matrix = VALID_MATRIX.replace("`ПАО СБЕРБАНК`", '`ПАО "СБЕРБАНК"`', 1)
        errors = validate_tc_projection(VALID_TC, matrix)
        self.assertTrue(any("exact matrix test-data literal" in error for error in errors))

        exact = VALID_TC.replace("ПАО СБЕРБАНК", 'ПАО "СБЕРБАНК"')
        self.assertEqual([], validate_tc_projection(exact, matrix))

    def test_prefill_projection_requires_explicit_field_value_oracle(self) -> None:
        matrix = VALID_MATRIX.replace(
            "Сохранить карточку | базовый, жизненный-цикл-создания | Сохранение валидной карточки",
            "Открыть предзаполненную форму | базовый, жизненный-цикл-создания | Предзаполнение формы",
        ).replace(
            "Карточка сохранена | TC | ready |",
            "Поля «Наименование» и «ИНН» предзаполнены | TC | ready |",
        ).replace(
            "`Наименование` = `ПАО СБЕРБАНК`",
            "`Наименование` = `ПАО СБЕРБАНК`; `ИНН` = `7707083893`",
        )
        test_case = VALID_TC.replace(
            "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
            "- `Наименование` = `ПАО СБЕРБАНК`.\n- `ИНН` = `7707083893`.",
        ).replace(
            "Карточка партнёра сохранена.",
            "Поле «Наименование» содержит `ПАО СБЕРБАНК`.",
        )
        errors = validate_tc_projection(test_case, matrix)
        self.assertTrue(any("prefill oracle must state" in error and "ИНН" in error for error in errors))

        exact = test_case.replace(
            "Поле «Наименование» содержит `ПАО СБЕРБАНК`.",
            "Поле «Наименование» содержит `ПАО СБЕРБАНК`; поле «ИНН» содержит `7707083893`.",
        )
        self.assertEqual([], validate_tc_projection(exact, matrix))

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
            (package / "work" / "scope-clarification-requests.md").write_text(
                "# Вопросы\n\n## CLR-001 — подтверждение\n\n"
                "**Вопрос:** Как выполняется подтверждение вторым сотрудником?\n\n"
                "**Основание в ФТ:** AS.7.\n\n"
                "**Влияние на покрытие:** Нельзя выполнить GAP-001.\n\n"
                "**Текущее состояние:** Ответ не получен.\n",
                encoding="utf-8",
            )
            (scope / "scope-brief.md").write_text("# Границы\n\nРаздел подтверждён.\n", encoding="utf-8")
            (scope / "test-data-plan.md").write_text("# План данных\n\nДанные не требуются.\n", encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Не создавай matrix-строки для GAP-001.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\n"
                "scope_revision_count: 0\n"
                'clarification_register: "work/scope-clarification-requests.md"\n',
                encoding="utf-8",
            )
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
            (package / "work" / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\nОткрытые вопросы отсутствуют.\n", encoding="utf-8"
            )
            (scope / "scope-brief.md").write_text(
                "# Границы\n\nРаздел подтверждён.\n\n"
                "## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма добавления | `fts/Project/FT/mockups/form.png` | Подтверждены подписи и путь открытия. |\n"
                + VALID_BOUNDARY_CONTROL
                + VALID_TABLE_COVERAGE
                + VALID_CONSISTENCY,
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text(
                VALID_DATA_PLAN, encoding="utf-8"
            )
            (scope / "prompt.scope-to-writer.md").write_text(
                "Создай матрицу по всем строкам инвентаря. Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\n"
                "scope_revision_count: 0\n"
                'clarification_register: "work/scope-clarification-requests.md"\n',
                encoding="utf-8",
            )
            self.assertEqual([], validate_scope(package, scope))

            brief_path = scope / "scope-brief.md"
            valid_brief = brief_path.read_text(encoding="utf-8")
            malformed_table_coverage = VALID_TABLE_COVERAGE.replace(
                "| --- | --- | --- | --- |",
                "| --- | --- | --- |",
            )
            brief_path.write_text(
                valid_brief.replace(VALID_TABLE_COVERAGE, malformed_table_coverage),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(
                any(
                    "complete table-row coverage" in error
                    and "4 header columns but 3 separator columns" in error
                    for error in errors
                )
            )
            brief_path.write_text(valid_brief, encoding="utf-8")

            workflow_path = scope / "workflow-state.yaml"
            valid_workflow = workflow_path.read_text(encoding="utf-8")
            workflow_path.write_text(valid_workflow.replace("scope_revision_count: 0\n", ""), encoding="utf-8")
            self.assertTrue(
                any("scope_revision_count" in error for error in validate_scope(package, scope))
            )
            workflow_path.write_text(valid_workflow, encoding="utf-8")

            brief_path = scope / "scope-brief.md"
            valid_brief = brief_path.read_text(encoding="utf-8")
            brief_path.write_text(
                valid_brief.replace(
                    "Раздел 9.3.2 — до раздела 9.3.3",
                    "Раздел 9.3.2; AS.38",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("requirement-code boundary is partial" in error for error in errors))
            brief_path.write_text(
                valid_brief.replace(
                    "SR-001; SR-002; GAP-001",
                    "SR-001; GAP-001",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("first and final active source-row IDs" in error for error in errors))
            brief_path.write_text(valid_brief, encoding="utf-8")

            xhtml_path = package / "source" / "requirements.xhtml"
            original_xhtml = xhtml_path.read_text(encoding="utf-8")
            xhtml_path.write_text(
                original_xhtml.replace(">Сохранить<", ">Виждет «Партнер»<"),
                encoding="utf-8",
            )
            inventory_path = scope / "source-row-inventory.md"
            original_inventory = inventory_path.read_text(encoding="utf-8")
            inventory_path.write_text(
                original_inventory.replace("Сохранить", "Виждет «Партнер»"),
                encoding="utf-8",
            )
            brief_path.write_text(
                valid_brief.replace("| Таблица 7 | Сохранить |", "| Таблица 7 | Виждет «Партнер» |"),
                encoding="utf-8",
            )
            self.assertEqual([], validate_scope(package, scope))
            xhtml_path.write_text(original_xhtml, encoding="utf-8")
            inventory_path.write_text(original_inventory, encoding="utf-8")
            brief_path.write_text(valid_brief, encoding="utf-8")

            xhtml_path.write_text(
                original_xhtml.replace(
                    "<tr><td>Название</td><td>Примечание</td></tr>",
                    "<tr><td>Название</td><td>О</td></tr>",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("opaque table headers" in error for error in errors))
            brief_path = scope / "scope-brief.md"
            brief_without_semantics = brief_path.read_text(encoding="utf-8")
            brief_path.write_text(
                brief_without_semantics
                + "\n## Семантика заголовков таблиц\n\n"
                + "| Таблица | Заголовок | Значение | Основание или пробел |\n"
                + "| --- | --- | --- |\n"
                + "| Таблица 7 | О | Не определено | GAP-001 |\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(
                any(
                    "opaque table headers" in error
                    and "4 header columns but 3 separator columns" in error
                    for error in errors
                )
            )
            brief_path.write_text(
                brief_without_semantics
                + "\n## Семантика заголовков таблиц\n\n"
                + "| Таблица | Заголовок | Значение | Основание или пробел |\n"
                + "| --- | --- | --- | --- |\n"
                + "| Таблица 7 | О | Не определено | GAP-001 |\n",
                encoding="utf-8",
            )
            self.assertEqual([], validate_scope(package, scope))
            brief_path.write_text(
                brief_path.read_text(encoding="utf-8").replace(
                    "| Таблица 7 | О | Не определено | GAP-001 |",
                    "| Таблица 7 | О | Обязательность | Таблица 7 |",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("exact source legend" in error for error in errors))
            brief_path.write_text(brief_without_semantics, encoding="utf-8")
            xhtml_path.write_text(original_xhtml, encoding="utf-8")

            inventory_path = scope / "source-row-inventory.md"
            original_inventory = inventory_path.read_text(encoding="utf-8")
            inventory_path.write_text(
                original_inventory.replace(
                    "| Карточка сохраняется |",
                    "| Термин обозначает бизнес-смысл карточки |",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("business context" in error for error in errors))

            inventory_path.write_text(
                original_inventory.replace(
                    "| Карточка сохраняется |",
                    "| Поле обязательно |",
                ).replace(
                    "| SR-001 | Карточка партнёра | Пользователь с доступом к добавлению | Нажатие кнопки сохранения после заполнения | Карточка сохранена |",
                    "| SR-001 | Карточка партнёра | Пользователь с доступом к добавлению | Оставить поле пустым | Сохранение недоступно |",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("requiredness alone" in error for error in errors))
            inventory_path.write_text(original_inventory, encoding="utf-8")

            reactive_inventory = original_inventory.replace(
                "Карточка сохраняется",
                "При создании дубля система отображает подсказку",
            ).replace(
                "Нажатие кнопки сохранения после заполнения | Карточка сохранена",
                "Указывает существующее наименование | Отображается подсказка о дубле",
            )
            inventory_path.write_text(reactive_inventory, encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("source-backed trigger/action" in error for error in errors))
            inventory_path.write_text(original_inventory, encoding="utf-8")

            mixed_upload_inventory = original_inventory.replace(
                "| Карточка сохраняется |",
                "| Система принимает допустимый файл, а недопустимый файл не загружает и выводит ошибку |",
            ).replace(
                "Нажатие кнопки сохранения после заполнения | Карточка сохранена",
                "Пользователь пытается прикрепить файл | Допустимый файл прикреплён, недопустимый файл не загружен и отображается ошибка",
            )
            inventory_path.write_text(mixed_upload_inventory, encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("split mixed accepted and rejected outcomes" in error for error in errors))
            self.assertFalse(any("source-backed trigger/action" in error for error in errors))
            inventory_path.write_text(original_inventory, encoding="utf-8")

            gaps_path = scope / "coverage-gaps.md"
            gaps_path.write_text(VALID_GAPS.replace("AS.39", "AS.40"), encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("exactly reuse the linked SR-002 source anchor" in error for error in errors))
            gaps_path.write_text(VALID_GAPS, encoding="utf-8")
            inventory_path.write_text(
                VALID_INVENTORY.replace(
                    "AS.38; Таблица 7, строка «Сохранить»",
                    "Таблица 7, строка «Сохранить»",
                ).replace(
                    "AS.39",
                    "Раздел 9.3.2; абзац «Реакция на ограничение должна быть определена»",
                ),
                encoding="utf-8",
            )
            gaps_path.write_text(
                VALID_GAPS.replace(
                    "AS.39",
                    "Раздел 9.3.2; абзац «Реакция на ограничение должна быть определена»",
                ),
                encoding="utf-8",
            )
            self.assertEqual([], validate_scope(package, scope))
            inventory_path.write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Сохранить», примечание"),
                encoding="utf-8",
            )
            gaps_path.write_text(VALID_GAPS, encoding="utf-8")

            pending_question = (
                "# Реестр вопросов к БА\n\n"
                "## CLR-scope-001 — реакция на ограничение\n\n"
                "**Область проверки:** `scope`\n\n"
                "**Статус:** `ожидает-ответа`\n\n"
                "**Вопрос:** Какой наблюдаемый результат возникает при нарушении ограничения AS.39?\n\n"
                "**Основание в ФТ:** AS.39.\n\n"
                "**Влияние на покрытие:** Нельзя определить ожидаемый результат GAP-001.\n\n"
                "**Ответ БА:** _Введите ответ здесь._\n"
            )
            register = package / "work" / "scope-clarification-requests.md"
            register.write_text(pending_question, encoding="utf-8")
            self.assertEqual([], validate_scope(package, scope))

            compact_pending_question = pending_question.replace("\n\n**", "\n**")
            register.write_text(compact_pending_question, encoding="utf-8")
            self.assertEqual([], validate_scope(package, scope))
            register.write_text(pending_question, encoding="utf-8")

            cancelled_without_gap = (
                "# Реестр вопросов к БА\n\n"
                "## CLR-scope-002 — отменённое поведение\n\n"
                "**Область проверки:** `scope`\n\n"
                "**Статус:** `отменён`\n\n"
                "**Вопрос:** Как выполняется подтверждение вторым сотрудником?\n\n"
                "**Основание в ФТ:** AS.7.\n\n"
                "**Влияние на покрытие:** AS.7 исключён из покрытия.\n\n"
                "**Ответ БА:** Подтверждение вторым сотрудником отменено.\n"
            )
            register.write_text(cancelled_without_gap, encoding="utf-8")
            self.assertEqual([], validate_scope(package, scope))
            register.write_text(pending_question, encoding="utf-8")

            register.write_text(
                pending_question.replace("GAP-001.", "GAP-001 и GAP-002."),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("unknown coverage gap GAP-002" in error for error in errors))
            register.write_text(pending_question, encoding="utf-8")

            multi_inventory = inventory_path.read_text(encoding="utf-8").replace(
                "| SR-002 | AS.39 | Реакция на ограничение должна быть определена |",
                "| SR-002 | AS.39 | Реакция на ограничение должна быть определена |\n"
                "| SR-003 | AS.40 | Значение общего термина должно быть определено |",
            ).replace(
                "| SR-002 | Карточка партнёра | Пользователь с доступом к добавлению | Нарушение ограничения AS.39 | Наблюдаемый результат не определён источником; GAP-001 |",
                "| SR-002 | Карточка партнёра | Пользователь с доступом к добавлению | Нарушение ограничения AS.39 | Наблюдаемый результат не определён источником; GAP-001 |\n"
                "| SR-003 | Карточка партнёра | Пользователь с доступом к добавлению | Проверяет общий термин | Значение не определено источником; GAP-002 |",
            )
            inventory_path.write_text(multi_inventory, encoding="utf-8")
            gaps_path = scope / "coverage-gaps.md"
            gaps_path.write_text(
                VALID_GAPS
                + "| GAP-002 | SR-003 | AS.40 | неоднозначность-требования | Не определён общий термин | Ответ БА |\n",
                encoding="utf-8",
            )
            brief_path.write_text(
                valid_brief.replace(
                    "SR-001; SR-002; GAP-001",
                    "SR-001; SR-002; SR-003; GAP-001; GAP-002",
                ),
                encoding="utf-8",
            )
            writer_prompt = scope / "prompt.scope-to-writer.md"
            original_prompt = writer_prompt.read_text(encoding="utf-8")
            writer_prompt.write_text(original_prompt + " Для GAP-002 создай строку `coverage-gap`.\n", encoding="utf-8")
            register.write_text(
                pending_question.replace(
                    "Какой наблюдаемый результат возникает при нарушении ограничения AS.39?",
                    "Какое единое правило разрешает неоднозначность AS.39 и AS.40?",
                ).replace(
                    "**Основание в ФТ:** AS.39.",
                    "**Основание в ФТ:** AS.39; AS.40.",
                ).replace(
                    "GAP-001.",
                    "GAP-001 и GAP-002.",
                ),
                encoding="utf-8",
            )
            self.assertEqual([], validate_scope(package, scope))
            inventory_path.write_text(original_inventory, encoding="utf-8")
            gaps_path.write_text(VALID_GAPS, encoding="utf-8")
            brief_path.write_text(valid_brief, encoding="utf-8")
            writer_prompt.write_text(original_prompt, encoding="utf-8")
            register.write_text(pending_question, encoding="utf-8")

            uncoded_question = pending_question.replace(
                "при нарушении ограничения AS.39?",
                "при нарушении ограничения?",
            ).replace(
                "**Основание в ФТ:** AS.39.",
                "**Основание в ФТ:** Раздел 9.3.2; абзац «При нарушении ограничения карточка не сохраняется».",
            )
            register.write_text(uncoded_question, encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("exactly reuse the linked coverage-gap source anchor" in error for error in errors))

            answered_question = pending_question.replace(
                "`ожидает-ответа`", "`ответ-получен`"
            ).replace("_Введите ответ здесь._", "Сохранение блокируется, поле подсвечивается красным.")
            register.write_text(answered_question, encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("still links open coverage gaps" in error for error in errors))

            gaps_path.write_text(
                VALID_GAPS.replace("Ответ БА", "Закрыт: ответ БА применён."),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("carries resolved GAP-001 as coverage-gap" in error for error in errors))
            writer_prompt.write_text("Создай матрицу по всем активным строкам инвентаря.\n", encoding="utf-8")
            self.assertEqual([], validate_scope(package, scope))
            gaps_path.write_text(VALID_GAPS, encoding="utf-8")
            writer_prompt.write_text(original_prompt, encoding="utf-8")

            register.write_text(
                answered_question.replace(
                    "Сохранение блокируется, поле подсвечивается красным.",
                    "_Введите ответ здесь._",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("requires a recorded answer" in error for error in errors))

            register.write_text(answered_question + "\n" + answered_question.split("\n", 2)[2], encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("duplicate IDs" in error for error in errors))
            register.write_text(EMPTY_CLARIFICATION_REGISTER, encoding="utf-8")

            writer_prompt.write_text(original_prompt + " Передай SR-999 в следующий этап.\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("absent from active inventory" in error and "SR-999" in error for error in errors))
            writer_prompt.write_text(original_prompt, encoding="utf-8")

            inventory_path.write_text(
                original_inventory.replace("Карточка сохраняется", "Поведение не реализуется", 1),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("belongs in applied exclusions" in error for error in errors))
            inventory_path.write_text(original_inventory, encoding="utf-8")

            inventory_path = scope / "source-row-inventory.md"
            inventory_path.write_text(
                inventory_path.read_text(encoding="utf-8").replace(
                    "| SR-002 | Карточка партнёра | Пользователь с доступом к добавлению | Нарушение ограничения AS.39 | Наблюдаемый результат не определён источником; GAP-001 |\n",
                    "",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("misses active obligations" in error and "SR-002" in error for error in errors))
            inventory_path.write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Сохранить», примечание"),
                encoding="utf-8",
            )

            inventory_path.write_text(
                inventory_path.read_text(encoding="utf-8").replace(
                    "| SR-001 | Карточка партнёра |",
                    "| SR-001 | Карточка партнёра или реквизита |",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("split mixed surfaces" in error for error in errors))
            inventory_path.write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Сохранить», примечание"),
                encoding="utf-8",
            )

            brief_path = scope / "scope-brief.md"
            brief_path.write_text(
                brief_path.read_text(encoding="utf-8").replace(
                    "| Выбранный раздел | Раздел 9.3.2 — до раздела 9.3.3 | Включён |",
                    "| Выбранный раздел | Раздел 9.3.2 — до раздела 9.3.3 | Не применимо: требований нет. |",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("selected section must use decision" in error for error in errors))

            brief_path = scope / "scope-brief.md"
            valid_brief = brief_path.read_text(encoding="utf-8")
            brief_path.write_text(valid_brief + "\nТабица 7.\n", encoding="utf-8")
            errors = validate_scope(package, scope)
            self.assertTrue(any("high-confidence user-facing text error" in error for error in errors))
            brief_path.write_text(valid_brief, encoding="utf-8")
            brief_path.write_text(
                valid_brief.replace(
                    "| Поля, справочники и внешние источники | Реакция на ограничение не определена. | SR-002; GAP-001 |\n",
                    "| Поля, справочники и внешние источники | Реакция на ограничение не определена. | SR-002; GAP-001 |\n"
                    "| История изменений и аудит | Не применимо: источник не содержит требований к аудиту. | — |\n",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("История изменений и аудит" in error and "omit non-applicable" in error for error in errors))
            brief_path.write_text(valid_brief, encoding="utf-8")

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

            (package / "work" / "scope-clarification-requests.md").write_text(
                "# Реестр вопросов к БА\n\n## CLR-scope-001 — стендовые записи\n\n"
                "**Область проверки:** `scope`\n\n"
                "**Статус:** `ожидает-ответа`\n\n"
                "**Вопрос:** Предоставьте готового партнёра и учётную запись тестовой среды для AS.39.\n\n"
                "**Основание в ФТ:** AS.39.\n\n"
                "**Влияние на покрытие:** Нельзя выполнить GAP-001.\n\n"
                "**Ответ БА:** _Введите ответ здесь._\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("test-data provisioning" in error for error in errors))

            (package / "work" / "scope-clarification-requests.md").write_text(
                "# Вопросы к БА\n\n## Q-001 — неверный идентификатор\n\n"
                "**Вопрос:** Какое поведение задано AS.39?\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("must use CLR-* ID" in error for error in errors))

    def test_test_data_plan_requires_provenance_and_provider_acquisition_contract(self) -> None:
        invalid = """# План тестовых данных

| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |
| --- | --- | --- | --- | --- | --- | --- |
| Подсказка организации | TD-PARTNER-A | внешний сервис: Provider | Выбрать одну связную запись. | Не применимо: количественное ограничение отсутствует. | Выбрать подсказку. | готово |
"""
        errors = validate_test_data_plan(invalid)
        self.assertTrue(any("must define 'Контракт получения:'" in error for error in errors))
        self.assertTrue(any("requires readiness 'требуется'" in error for error in errors))

        valid = invalid.replace(
            "Выбрать одну связную запись. | Не применимо: количественное ограничение отсутствует. | Выбрать подсказку. | готово",
            "Контракт получения: запрос `Тест`; сохранить выбранное наименование и связанные реквизиты одной записи. | Не применимо: количественное ограничение отсутствует. | Выбрать сохранённую подсказку. | требуется",
        )
        self.assertEqual([], validate_test_data_plan(valid))
        self.assertTrue(validate_test_data_plan("# План\n\nЗначения будут подготовлены.\n"))

        contract_in_preparation = invalid.replace(
            "Выбрать одну связную запись. | Не применимо: количественное ограничение отсутствует. | Выбрать подсказку. | готово",
            "Выбрать одну связную запись. | Не применимо: количественное ограничение отсутствует. | Контракт получения: запрос `Тест`; сохранить наименование и реквизиты одной записи. | требуется",
        )
        self.assertEqual([], validate_test_data_plan(contract_in_preparation))

    def test_test_data_plan_allows_compatible_role_reuse_and_rejects_source_conflicts(self) -> None:
        reused_role = VALID_DATA_PLAN + (
            "| Отмена карточки | TD-PARTNER-A | первичный источник | "
            "Тот же партнёр используется для проверки отмены. | "
            "Не применимо: количественное ограничение отсутствует. | "
            "Открыть новую карточку того же партнёра на стенде. | требуется |\n"
        )
        self.assertEqual([], validate_test_data_plan(reused_role))

        conflicting_source = reused_role.replace(
            "| Отмена карточки | TD-PARTNER-A | первичный источник |",
            "| Отмена карточки | TD-PARTNER-A | синтетический генератор |",
        )
        errors = validate_test_data_plan(conflicting_source)
        self.assertTrue(any("conflicting allowed sources" in error for error in errors))

    def test_matrix_accepts_consolidated_compatible_baseline_role_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            scope = "9.3.3"
            baseline = package / "work" / "stage-handoffs" / scope / "test-data-plan.md"
            baseline.parent.mkdir(parents=True)
            baseline.write_text(
                VALID_DATA_PLAN
                + "| Отмена карточки | TD-PARTNER-A | первичный источник | "
                "Тот же партнёр используется для проверки отмены. | "
                "Не применимо: количественное ограничение отсутствует. | "
                "Открыть новую карточку того же партнёра на стенде. | требуется |\n",
                encoding="utf-8",
            )
            matrix = package / "work" / "practical" / scope / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(VALID_MATRIX, encoding="utf-8")
            (matrix.parent / "matrix-data-plan.md").write_text(VALID_DATA_PLAN, encoding="utf-8")
            set_pending(matrix)

            self.assertEqual([], validate_matrix_layout(matrix, package))

    def test_test_data_plan_requires_explicit_quantitative_boundary_contract(self) -> None:
        plan = """# План тестовых данных

| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |
| --- | --- | --- | --- | --- | --- | --- |
| Размер файла не более 40 МБ | TD-FILE-LIMIT; TD-FILE-OVER | синтетический генератор | Два открываемых файла допустимого формата. | Допустимо 40 МБ; недопустимо 41 МБ. | Создать файлы до проверки на стенде. | требуется |
"""
        errors = validate_test_data_plan(plan)
        self.assertTrue(any("Шаг представления" in error for error in errors))

        valid = plan.replace(
            "Допустимо 40 МБ; недопустимо 41 МБ.",
            "Шаг представления: 1 КБ; валидная граница: 40 МБ; ближайшее недопустимое: 40 МБ + 1 КБ; Основание границы: AS.35.",
        )
        self.assertEqual([], validate_test_data_plan(valid))

    def test_test_data_plan_separates_value_source_from_stand_preparation(self) -> None:
        stand_only = VALID_DATA_PLAN.replace("первичный источник", "стендовая подготовка")
        self.assertTrue(
            any("not a value source" in error for error in validate_test_data_plan(stand_only))
        )

        combined = VALID_DATA_PLAN.replace(
            "первичный источник",
            "первичный источник; стендовая подготовка",
        )
        self.assertTrue(any("not a value source" in error for error in validate_test_data_plan(combined)))

        unqualified_acquisition = VALID_DATA_PLAN.replace(
            "Подготовить запись на стенде с указанным в источнике наименованием.",
            "Контракт получения: запросить запись внешнего реестра.",
        )
        self.assertTrue(
            any("requires an explicit provider" in error for error in validate_test_data_plan(unqualified_acquisition))
        )

        confirmed_environment = VALID_DATA_PLAN.replace(
            "первичный источник",
            "подтверждённая стендовая привязка",
        )
        self.assertTrue(
            any("Контракт подтверждения:" in error for error in validate_test_data_plan(confirmed_environment))
        )
        confirmed_environment = confirmed_environment.replace(
            "Подготовить запись на стенде с указанным в источнике наименованием.",
            "Контракт подтверждения: сохранить evidence, путь и SHA-256.",
        )
        self.assertEqual([], validate_test_data_plan(confirmed_environment))

    def test_test_data_plan_reports_root_column_mismatch(self) -> None:
        malformed = """# План тестовых данных

| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |
| --- | --- | --- | --- | --- | --- |
| Сохранение | TD-A | стендовая подготовка | Уникальность | Не применимо: нет границы | Подготовить | требуется |
"""

        errors = validate_test_data_plan(malformed)

        self.assertEqual(1, len(errors))
        self.assertIn("7 header columns but 6 separator columns", errors[0])

    def test_test_data_plan_rejects_unsourced_date_limits(self) -> None:
        plan = """# План тестовых данных

| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |
| --- | --- | --- | --- | --- | --- | --- |
| Диапазон даты | TD-DATE-LIMIT | первичный источник | Валидная и ближайшая недопустимая дата. | Шаг представления: 1 день; валидная граница: 01.01.1900; ближайшее недопустимое: 31.12.1899; Основание границы: Таблица 6, строка «Дата». | Ввести дату. | готово |
"""
        errors = validate_test_data_plan(plan, "<td>Дата</td><td>Дата</td>")
        self.assertTrue(any("date boundary" in error and "absent" in error for error in errors))
        self.assertEqual([], validate_test_data_plan(plan, "Источник устанавливает границу 01.01.1900."))

    def test_post_matrix_materialization_enforces_provider_provenance_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.2" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix_content = VALID_MATRIX.replace(
                "`Наименование` = `ПАО СБЕРБАНК`",
                "TD-PARTNER-A; TD-PARTNER-B; REL-DIFFERENT-INN",
            )
            matrix.write_text(matrix_content, encoding="utf-8")
            data_plan = package / "work" / "stage-handoffs" / "9.3.2" / "test-data-plan.md"
            data_plan.parent.mkdir(parents=True)
            data_plan.write_text(
                "# План данных\n\n"
                "| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| Два партнёра | TD-PARTNER-A; TD-PARTNER-B | внешний сервис: Provider | Контракт получения: сохранить две разные организации; REL-DIFFERENT-INN. | Не применимо: количественное ограничение отсутствует. | Выбрать две подсказки. | требуется |\n",
                encoding="utf-8",
            )
            fixtures = package / "work" / "test-data" / "9.3.2" / "fixtures"
            fixtures.mkdir(parents=True)
            snapshot_payload = {
                "suggestions": [
                    {"value": "ПАО СБЕРБАНК", "data": {"inn": "7707083893"}},
                    {"value": "АО АЛЬФА-БАНК", "data": {"inn": "7728168971"}},
                ]
            }
            snapshot = fixtures / "provider.json"
            snapshot.write_text(json.dumps(snapshot_payload, ensure_ascii=False), encoding="utf-8")
            catalog = {
                "fixtures": [
                    {
                        "fixture_id": "FX-PARTNER-A",
                        "purpose": "Первая организация",
                        "source_type": "provider",
                        "provider": "Provider",
                        "request": {"query": "СБЕРБАНК"},
                        "runtime_data": {"name": "ПАО СБЕРБАНК", "inn": "7707083893"},
                        "snapshot_path": "provider.json",
                        "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                    },
                    {
                        "fixture_id": "FX-PARTNER-B",
                        "purpose": "Вторая организация",
                        "source_type": "provider",
                        "provider": "Provider",
                        "request": {"query": "АЛЬФА"},
                        "runtime_data": {"name": "АО АЛЬФА-БАНК", "inn": "7728168971"},
                        "snapshot_path": "provider.json",
                        "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                    },
                ]
            }
            catalog_path = fixtures / "fixture-catalog.json"
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
            materialization = package / "work" / "test-data" / "9.3.2" / "data-materialization.json"
            payload = {
                "schema_version": 1,
                "scope": "9.3.2",
                "status": "completed",
                "matrix_path": "work/practical/9.3.2/test-design-matrix.md",
                "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
                "fixture_catalog": "work/test-data/9.3.2/fixtures/fixture-catalog.json",
                "bindings": [
                    {
                        "role_id": "TD-PARTNER-A",
                        "used_by": ["M-001"],
                        "source_type": "provider",
                        "source_name": "Provider",
                        "fixture_id": "FX-PARTNER-A",
                        "values": {"Наименование партнёра": "ПАО СБЕРБАНК", "ИНН": "7707083893"},
                    },
                    {
                        "role_id": "TD-PARTNER-B",
                        "used_by": ["M-001"],
                        "source_type": "provider",
                        "source_name": "Provider",
                        "fixture_id": "FX-PARTNER-B",
                        "values": {"Наименование партнёра": "АО АЛЬФА-БАНК", "ИНН": "7728168971"},
                    },
                ],
                "relations": [
                    {
                        "id": "REL-DIFFERENT-INN",
                        "used_by": ["M-001"],
                        "left": "TD-PARTNER-A.ИНН",
                        "operator": "not-equal",
                        "right": "TD-PARTNER-B.ИНН",
                    }
                ],
            }
            materialization.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_test_data(materialization, matrix, data_plan))
            projected_tc = VALID_TC.replace(
                "- `Наименование партнёра` = `ПАО СБЕРБАНК`.",
                "- `Наименование партнёра A` = `ПАО СБЕРБАНК`.\n"
                "- `ИНН A` = `7707083893`.\n"
                "- `Наименование партнёра B` = `АО АЛЬФА-БАНК`.\n"
                "- `ИНН B` = `7728168971`.",
            )
            self.assertEqual([], validate_materialized_projection(projected_tc, matrix_content, materialization))

            payload["bindings"][0]["values"]["Наименование партнёра"] = "ПАО СБЕРБАНК RUN-ID"
            materialization.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            errors = validate_test_data(materialization, matrix, data_plan)
            self.assertTrue(any("RUN-ID/timestamp is forbidden" in error for error in errors))

    def test_environment_materialization_requires_confirmed_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "FT"
            (package / "AGENT-NOTES.md").parent.mkdir(parents=True)
            (package / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
            matrix = package / "work" / "practical" / "9.3.3" / "test-design-matrix.md"
            matrix.parent.mkdir(parents=True)
            matrix_content = VALID_MATRIX.replace(
                "`Наименование` = `ПАО СБЕРБАНК`",
                "TD-PARTNER-A",
            )
            matrix.write_text(matrix_content, encoding="utf-8")
            data_plan = package / "work" / "stage-handoffs" / "9.3.3" / "test-data-plan.md"
            data_plan.parent.mkdir(parents=True)
            data_plan.write_text(
                "# План данных\n\n"
                "| Группа проверок | Роли данных | Допустимый источник | Ограничения и отношения | Границы и классы | Воспроизводимая подготовка | Готовность материализации |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| Партнёр | TD-PARTNER-A | подтверждённая стендовая привязка | Конкретная запись. | Не применимо: границ нет. | Контракт подтверждения: сохранить evidence конкретной записи, путь и SHA-256. | требуется |\n",
                encoding="utf-8",
            )
            materialization = package / "work" / "test-data" / "9.3.3" / "data-materialization.json"
            materialization.parent.mkdir(parents=True)
            payload = {
                "schema_version": 1,
                "scope": "9.3.3",
                "status": "completed",
                "matrix_path": "work/practical/9.3.3/test-design-matrix.md",
                "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
                "bindings": [
                    {
                        "role_id": "TD-PARTNER-A",
                        "used_by": ["M-001"],
                        "source_type": "environment",
                        "source_name": "подтверждённая стендовая привязка",
                        "values": {"Наименование партнёра": "ООО Тестовый партнёр"},
                    }
                ],
                "relations": [],
            }
            materialization.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            errors = validate_test_data(materialization, matrix, data_plan)
            self.assertTrue(any("confirmed environment_binding" in error for error in errors))

            evidence = package / "work" / "test-data" / "9.3.3" / "environment-evidence.md"
            evidence.write_text("Подтверждённая запись: ООО Тестовый партнёр\n", encoding="utf-8")
            payload["bindings"][0]["environment_binding"] = {
                "status": "confirmed",
                "evidence_path": "work/test-data/9.3.3/environment-evidence.md",
                "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            }
            materialization.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_test_data(materialization, matrix, data_plan))

    def test_tc_accepts_concrete_file_preparation_in_preconditions(self) -> None:
        test_case = VALID_TC.replace(
            "1. Открыть карточку добавления партнёра.",
            "1. Файл `document.pdf` формата PDF размером 40 МБ создан и доступен для выбора.",
        )
        self.assertEqual([], validate_tc(test_case))

    def test_scope_validator_blocks_bulk_parent_ownership_row_loss_visual_omission_and_repo_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            xhtml = package / "source" / "requirements.xhtml"
            xhtml.write_text(
                xhtml.read_text(encoding="utf-8").replace(
                    "</table>",
                    "<tr><td>ИНН</td><td>Отдельное поле</td></tr></table>",
                ),
                encoding="utf-8",
            )
            locator = package / "work" / "stage-handoffs" / "00-ft" / "workflow-state.yaml"
            locator.write_text(
                locator.read_text(encoding="utf-8")
                + "figma_sources:\n"
                + "  - url: https://www.figma.com/design/example?node-id=1-2\n",
                encoding="utf-8",
            )
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Сохранить», примечание"),
                encoding="utf-8",
            )
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n"
                "## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n"
                + VALID_BOUNDARY_CONTROL.replace(
                    "| Вводный текст родительского раздела | Раздел 9.3 — до раздела 9.3.1 | Не применимо: нормативный вводный текст отсутствует. | — |",
                    "| Вводный текст родительского раздела | Раздел 9.3 — до раздела 9.3.1 | Включён | SR-001 |",
                )
                + VALID_TABLE_COVERAGE
                + VALID_CONSISTENCY,
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text(VALID_DATA_PLAN, encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\n"
                "scope_revision_count: 0\n"
                'clarification_register: "work/scope-clarification-requests.md"\n',
                encoding="utf-8",
            )
            repository_temp = root / "tmp" / "pdfs" / "page-01.png"
            repository_temp.parent.mkdir(parents=True)
            repository_temp.write_bytes(b"png")

            errors = validate_scope(package, scope)
            self.assertTrue(any("instead of including the whole fragment" in error for error in errors))
            self.assertTrue(any("misses table 7 rows" in error and "инн" in error for error in errors))
            self.assertTrue(any("repository-local temporary file" in error for error in errors))

    def test_scope_validator_uses_figma_only_when_local_visual_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            figma_url = "https://www.figma.com/design/example?node-id=1-2"
            locator = package / "work" / "stage-handoffs" / "00-ft" / "workflow-state.yaml"
            locator.write_text(
                locator.read_text(encoding="utf-8")
                + "figma_sources:\n"
                + f"  - url: {figma_url}\n",
                encoding="utf-8",
            )
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace("строка «Сохранить»", "строка «Сохранить», примечание"),
                encoding="utf-8",
            )
            (scope / "coverage-gaps.md").write_text(VALID_GAPS, encoding="utf-8")
            boundary = VALID_BOUNDARY_CONTROL.replace(
                "| Вводный текст родительского раздела | Раздел 9.3 — до раздела 9.3.1 | Не применимо: нормативный вводный текст отсутствует. | — |",
                "| Вводный текст родительского раздела | Раздел 9.3 — до раздела 9.3.1 | Распределён | См. таблицу владения. |",
            ).replace("\nНормативные родительские обязанности отсутствуют.\n", "\n")
            ownership = """

## Распределение родительских обязанностей

| Источник | Родительская обязанность | Целевая область | Связанные обязанности или решение |
| --- | --- | --- | --- |
| AS.38 | Сохранение карточки доступно в текущем подразделе. | `scope` | SR-001 |
"""
            (scope / "scope-brief.md").write_text(
                "# Границы\n\n"
                "## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n"
                + boundary
                + ownership
                + VALID_TABLE_COVERAGE
                + VALID_CONSISTENCY,
                encoding="utf-8",
            )
            (scope / "test-data-plan.md").write_text(VALID_DATA_PLAN, encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Для `GAP-001` создай строку матрицы с решением `coverage-gap`.\n",
                encoding="utf-8",
            )
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\n"
                "scope_revision_count: 0\n"
                'clarification_register: "work/scope-clarification-requests.md"\n',
                encoding="utf-8",
            )

            self.assertEqual([], validate_scope(package, scope))

            brief_path = scope / "scope-brief.md"
            complete_brief = brief_path.read_text(encoding="utf-8")
            brief_path.write_text(
                complete_brief.replace(
                    "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |",
                    "| Форма | `fts/Project/FT/mockups/form.png` | Локальный макет не показывает релевантное поле. |",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(any("incomplete local visual evidence" in error for error in errors))

            brief_path.write_text(
                brief_path.read_text(encoding="utf-8")
                + "\nFigma недоступна: у пользователя нет доступа к макету.\n",
                encoding="utf-8",
            )
            self.assertEqual([], validate_scope(package, scope))

    def test_scope_gap_propagates_to_dependent_result_with_same_source_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            (root / "scripts").mkdir()
            package = root / "fts" / "Project" / "FT"
            create_scope_locator(package)
            scope = package / "work" / "stage-handoffs" / "01-scope"
            scope.mkdir()
            shared_anchor = "AS.38; Таблица 7, строка «Сохранить»"
            inventory = VALID_INVENTORY.replace("AS.39 | Реакция", f"{shared_anchor} | Реакция")
            gaps = VALID_GAPS.replace("| AS.39 |", f"| {shared_anchor} |")
            (scope / "source-row-inventory.md").write_text(inventory, encoding="utf-8")
            (scope / "coverage-gaps.md").write_text(gaps, encoding="utf-8")
            brief = (
                "# Границы\n\n"
                "## Визуальная сверка\n\n"
                "| UI-уровень | Визуальный источник | Результат сверки |\n"
                "| --- | --- | --- |\n"
                "| Форма | `fts/Project/FT/mockups/form.png` | Подтверждена форма. |\n"
                + VALID_BOUNDARY_CONTROL
                + VALID_TABLE_COVERAGE
                + VALID_CONSISTENCY
            )
            brief_path = scope / "scope-brief.md"
            brief_path.write_text(brief, encoding="utf-8")
            (scope / "test-data-plan.md").write_text(VALID_DATA_PLAN, encoding="utf-8")
            (scope / "prompt.scope-to-writer.md").write_text(
                "Создай матрицу по активным строкам.\n", encoding="utf-8"
            )
            (scope / "workflow-state.yaml").write_text(
                "stage: ft-scope-analyzer\nscope_revision_count: 0\n"
                'clarification_register: "work/scope-clarification-requests.md"\n',
                encoding="utf-8",
            )

            errors = validate_scope(package, scope)
            self.assertTrue(any("requires 'Контроль зависимых результатов'" in error for error in errors))

            brief_path.write_text(
                brief
                + "\n## Контроль зависимых результатов\n\n"
                + "| Причинная обязанность | Зависимая обязанность | Связь | Обработка неопределённости |\n"
                + "| --- | --- | --- | --- |\n"
                + "| SR-002 | SR-001 | Общий источник, но независимые oracles. | Независима: SR-001 имеет отдельный наблюдаемый результ. |\n",
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertFalse(any("requires 'Контроль зависимых результатов'" in error for error in errors))
            self.assertFalse(any("dependent-results control omits SR-002 -> SR-001" in error for error in errors))

            (scope / "source-row-inventory.md").write_text(
                inventory.replace(
                    f"| SR-001 | {shared_anchor} |", "| SR-001 | AS.37 |"
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertFalse(any("dependent-results row" in error for error in errors))

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
            (package / "work" / "scope-clarification-requests.md").write_text(
                "# Реестр вопросов к БА\n\n## CLR-scope-001 — роль\n\n"
                "**Область проверки:** `scope`\n\n"
                "**Статус:** `ожидает-ответа`\n\n"
                "**Вопрос:** Какая роль выполняет действие?\n\n"
                "**Основание в ФТ:** AS.39.\n\n"
                "**Влияние на покрытие:** Нельзя определить GAP-001.\n\n"
                "**Ответ БА:** _Введите ответ здесь._\n\n"
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
            (package / "work" / "scope-clarification-requests.md").write_text(
                "# Реестр вопросов к БА\n\n## CLR-scope-001 Уточнение результата\n\n"
                "**Область проверки:** `scope`\n\n"
                "**Статус:** `ожидает-ответа`\n\n"
                "**Вопрос:** Какой результат возникает помимо сохранения карточки?\n\n"
                "**Основание в ФТ:** AS.38.\n\n"
                "**Влияние на покрытие:** Нельзя завершить GAP-001.\n\n"
                "**Ответ БА:** _Введите ответ здесь._\n",
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

            (scope / "source-row-inventory.md").write_text(
                VALID_INVENTORY.replace(
                    "Карточка сохраняется",
                    "Нажатие открывает окно редактирования с предзаполненными данными",
                ),
                encoding="utf-8",
            )
            errors = validate_scope(package, scope)
            self.assertTrue(
                any(
                    "aggregates independent properties" in error
                    and "открытие интерфейса" in error
                    and "предзаполнение данных" in error
                    and "редактируемость" not in error
                    for error in errors
                )
            )

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

    def test_tc_changes_required_classifies_finding_origin_and_repair_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = root / "test-cases.md"
            artifact.write_text("# Набор\n\n## TC-001\n", encoding="utf-8")
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
            finding = {
                "id": "TC-R-001",
                "severity": "material",
                "affected_tc": ["TC-001"],
                "description": "В принятой matrix отсутствует обязательная ветка.",
                "required_correction": "Исправить matrix.",
            }
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
                "verdict": "tc-changes-required",
                "findings": [finding],
                "total_tc_count": 1,
                "reviewed_tc_count": 1,
                "review_scope_complete": True,
            }
            review_path = root / "tc-review.json"
            review_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n\nПроверено TC: 1/1\n", encoding="utf-8")

            self.assertTrue(any("origin_stage" in error for error in validate_review(artifact, review_path, "tc")))
            finding["origin_stage"] = "tc"
            review_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_review(artifact, review_path, "tc"))
            self.assertEqual("tc", tc_repair_stage(record["findings"]))

            record["findings"].append({**finding, "id": "TC-R-002", "origin_stage": "matrix"})
            review_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            self.assertEqual([], validate_review(artifact, review_path, "tc"))
            self.assertEqual("matrix", tc_repair_stage(record["findings"]))

    def test_schema_v2_delta_rereview_checks_only_declared_changed_tc(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            (source / "requirements.xhtml").write_text("<p>Требование</p>", encoding="utf-8")
            artifact = root / "test-cases.md"
            artifact.write_text(
                "# Набор\n\n## TC-001\n\nПервый результат.\n\n## TC-002\n\nВторой результат.\n",
                encoding="utf-8",
            )
            create_session_topology(root, "reviews")
            record_role(root, "matrix-reviewer", MATRIX_REVIEWER_THREAD, "local", "reviews")
            reviewer_thread = "22345678-1234-1234-1234-123456789abc"
            prompt = root / "tc-review-prompt.md"
            prompt.write_text("Проведи независимое review тест-кейсов.\n", encoding="utf-8")
            review_dir = root / "reviews"
            dispatch_path = create_dispatch(
                root,
                artifact,
                prompt,
                review_dir,
                "tc",
                reviewer_thread,
                "local",
                "2026-08-17T00:00:00Z",
            )
            first_record = {
                "schema_version": 1,
                "review_kind": "tc",
                "artifact_path": "test-cases.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": dispatch_path.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(dispatch_path),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": reviewer_thread,
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "tc-changes-required",
                "findings": [
                    {
                        "id": "TC-R-001",
                        "severity": "material",
                        "affected_items": ["TC-001"],
                        "origin_stage": "tc",
                        "description": "Исправить первый TC.",
                        "required_correction": "Уточнить результат.",
                    }
                ],
                "total_tc_count": 2,
                "reviewed_tc_count": 2,
                "reviewed_items": ["TC-001", "TC-002"],
                "review_scope_complete": True,
            }
            review_path = review_dir / "tc-review.json"
            review_path.write_text(json.dumps(first_record, ensure_ascii=False), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n\nПроверено TC: 2/2\n", encoding="utf-8")
            enrich_review_record(root, artifact, review_path, "tc", "reviews")
            self.assertEqual([], validate_review(artifact, review_path, "tc"))

            artifact.write_text(
                "# Набор\n\n## TC-001\n\nПервый уточнённый результат.\n\n## TC-002\n\nВторой результат.\n",
                encoding="utf-8",
            )
            second_dispatch = create_dispatch(
                root,
                artifact,
                prompt,
                review_dir,
                "tc",
                reviewer_thread,
                "local",
                "2026-08-17T00:02:00Z",
                previous_review=review_path,
            )
            dispatch_payload = json.loads(second_dispatch.read_text(encoding="utf-8"))
            self.assertEqual("delta", dispatch_payload["review_mode"])

            second_record = {
                "schema_version": 1,
                "review_kind": "tc",
                "artifact_path": "test-cases.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": second_dispatch.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(second_dispatch),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": reviewer_thread,
                "reviewed_at": "2026-08-17T00:03:00Z",
                "verdict": "tc-accepted",
                "findings": [],
                "total_tc_count": 2,
                "reviewed_tc_count": 1,
                "reviewed_items": ["TC-001"],
                "review_scope_complete": True,
            }
            review_path.write_text(json.dumps(second_record, ensure_ascii=False), encoding="utf-8")
            review_path.with_suffix(".md").write_text(
                "# Review\n\nПроверено изменённых TC: 1/2\n", encoding="utf-8"
            )
            enrich_review_record(root, artifact, review_path, "tc", "reviews")
            self.assertEqual([], validate_review(artifact, review_path, "tc", require_accepted=True))

            wrong_delta = json.loads(review_path.read_text(encoding="utf-8"))
            wrong_delta["reviewed_items"] = ["TC-002"]
            review_path.write_text(json.dumps(wrong_delta, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(
                any("must equal revision manifest changed_items" in error for error in validate_review(artifact, review_path, "tc"))
            )

    def test_schema_v2_matrix_revision_completes_delta_rereview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            (source / "requirements.xhtml").write_text("<p>Требование</p>", encoding="utf-8")
            artifact = root / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            create_session_topology(root, "reviews")
            reviewer_thread = "22345678-1234-1234-1234-123456789abc"
            prompt = root / "matrix-review-prompt.md"
            prompt.write_text("Проведи независимое review matrix.\n", encoding="utf-8")
            review_dir = root / "reviews"
            first_dispatch = create_dispatch(
                root,
                artifact,
                prompt,
                review_dir,
                "matrix",
                reviewer_thread,
                "local",
                "2026-08-17T00:00:00Z",
            )
            first_record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": first_dispatch.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(first_dispatch),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": reviewer_thread,
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "matrix-changes-required",
                "findings": [
                    {
                        "id": "M-R-001",
                        "severity": "material",
                        "affected_items": ["M-001"],
                        "description": "Ожидаемый результат строки M-001 недостаточно точен.",
                        "required_correction": "Уточнить ожидаемый результат M-001.",
                    }
                ],
                "reviewed_items": ["M-001", "GAP-001"],
                "review_scope_complete": True,
                "matrix_review_checklist": {
                    "source-coverage": {"status": "checked", "evidence": ["SR-001; SR-002"]},
                    "formal-techniques": {"status": "checked", "evidence": ["M-001; GAP-001"]},
                    "uniqueness-lifecycle": {
                        "status": "not-applicable",
                        "evidence": ["Не применимо: источник не задаёт уникальность."],
                    },
                    "save-data-closure": {"status": "checked", "evidence": ["M-001"]},
                    "identity-provenance": {
                        "status": "checked",
                        "evidence": ["TD-PARTNER-A; TD-PARTNER-B -> Provider"],
                    },
                    "reachability-oracles": {"status": "checked", "evidence": ["M-001; GAP-001"]},
                    "duplication-parameterization": {"status": "checked", "evidence": ["M-001"]},
                },
            }
            review_path = review_dir / "matrix-review.json"
            review_path.write_text(json.dumps(first_record, ensure_ascii=False), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Ревью матрицы\n", encoding="utf-8")
            enrich_review_record(root, artifact, review_path, "matrix", "reviews")
            self.assertEqual([], validate_review(artifact, review_path, "matrix"))

            missing_checklist = json.loads(review_path.read_text(encoding="utf-8"))
            checklist = missing_checklist.pop("matrix_review_checklist")
            review_path.write_text(json.dumps(missing_checklist, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(
                any("requires matrix_review_checklist" in error for error in validate_review(artifact, review_path, "matrix"))
            )
            missing_checklist["matrix_review_checklist"] = checklist
            review_path.write_text(json.dumps(missing_checklist, ensure_ascii=False), encoding="utf-8")

            invalid_identity = json.loads(review_path.read_text(encoding="utf-8"))
            invalid_identity["matrix_review_checklist"]["identity-provenance"] = {
                "status": "checked",
                "evidence": ["TD-PARTNER-A -> стендовая подготовка"],
            }
            review_path.write_text(json.dumps(invalid_identity, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(
                any("stand reference" in error for error in validate_review(artifact, review_path, "matrix"))
            )
            invalid_identity["matrix_review_checklist"]["identity-provenance"] = {
                "status": "checked",
                "evidence": ["TD-PARTNER-A -> стендовая привязка"],
            }
            review_path.write_text(json.dumps(invalid_identity, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(
                any("stand reference" in error for error in validate_review(artifact, review_path, "matrix"))
            )
            review_path.write_text(json.dumps(missing_checklist, ensure_ascii=False), encoding="utf-8")

            artifact.write_text(
                VALID_MATRIX.replace("Карточка сохранена", "Карточка сохранена и доступна для повторного открытия"),
                encoding="utf-8",
            )
            second_dispatch = create_dispatch(
                root,
                artifact,
                prompt,
                review_dir,
                "matrix",
                reviewer_thread,
                "local",
                "2026-08-17T00:02:00Z",
                previous_review=review_path,
            )
            dispatch_payload = json.loads(second_dispatch.read_text(encoding="utf-8"))
            self.assertEqual("delta", dispatch_payload["review_mode"])

            second_record = {
                "schema_version": 1,
                "review_kind": "matrix",
                "artifact_path": "test-design-matrix.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": second_dispatch.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(second_dispatch),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": reviewer_thread,
                "reviewed_at": "2026-08-17T00:03:00Z",
                "verdict": "matrix-accepted",
                "findings": [],
                "reviewed_items": ["M-001"],
                "review_scope_complete": True,
                "review_quality_status": "complete",
            }
            review_path.write_text(json.dumps(second_record, ensure_ascii=False), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Повторное review matrix\n", encoding="utf-8")
            enrich_review_record(root, artifact, review_path, "matrix", "reviews")
            self.assertEqual([], validate_review(artifact, review_path, "matrix", require_accepted=True))
            manifest_backed_record = json.loads(review_path.read_text(encoding="utf-8"))
            manifest_backed_record["review_quality_status"] = "failed-prior-review-incomplete"
            self.assertTrue(matrix_review_quality_blocking(manifest_backed_record))
            manifest_backed_record.pop("revision_manifest_path")
            self.assertFalse(matrix_review_quality_blocking(manifest_backed_record))

            missing_quality_status = json.loads(review_path.read_text(encoding="utf-8"))
            missing_quality_status.pop("review_quality_status")
            review_path.write_text(json.dumps(missing_quality_status, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(
                any("review_quality_status must be complete" in error for error in validate_review(artifact, review_path, "matrix"))
            )

    def test_matrix_item_index_localizes_row_change_without_structure_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = Path(temporary_directory) / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            before = artifact_index(artifact, "matrix")
            artifact.write_text(
                VALID_MATRIX.replace("Карточка сохранена", "Карточка успешно сохранена"),
                encoding="utf-8",
            )
            after = artifact_index(artifact, "matrix")
            changed = {
                item for item in set(before["items"]) | set(after["items"])
                if before["items"].get(item) != after["items"].get(item)
            }
            self.assertEqual({"M-001"}, changed)
            self.assertEqual(before["structure_sha256"], after["structure_sha256"])

    def test_data_materialization_is_a_tc_review_input_but_not_a_matrix_review_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory)
            artifact = package / "test-design-matrix.md"
            artifact.write_text(VALID_MATRIX, encoding="utf-8")
            data = package / "work" / "test-data" / "scope" / "data-materialization.json"
            data.parent.mkdir(parents=True)
            data.write_text('{"schema_version": 1}', encoding="utf-8")
            relative = data.relative_to(package).as_posix()
            self.assertNotIn(relative, semantic_input_hashes(package, artifact, "matrix", "scope"))
            self.assertIn(relative, semantic_input_hashes(package, artifact, "tc", "scope"))

    def test_revision_manifest_falls_back_to_full_for_undeclared_or_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            source.mkdir()
            source_file = source / "requirements.xhtml"
            source_file.write_text("<p>Требование</p>", encoding="utf-8")
            artifact = root / "test-cases.md"
            original = "# Набор\n\n## TC-001\n\nПервый.\n\n## TC-002\n\nВторой.\n"
            artifact.write_text(original, encoding="utf-8")
            review_dir = root / "reviews"
            create_session_topology(root, "reviews")
            record_role(root, "matrix-reviewer", MATRIX_REVIEWER_THREAD, "local", "reviews")
            reviewer_thread = "22345678-1234-1234-1234-123456789abc"
            prompt = root / "tc-review-prompt.md"
            prompt.write_text("Проведи независимое review тест-кейсов.\n", encoding="utf-8")
            dispatch_path = create_dispatch(
                root,
                artifact,
                prompt,
                review_dir,
                "tc",
                reviewer_thread,
                "local",
                "2026-08-17T00:00:00Z",
            )
            previous = {
                "schema_version": 1,
                "review_kind": "tc",
                "artifact_path": "test-cases.md",
                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "dispatch_path": dispatch_path.relative_to(root).as_posix(),
                "dispatch_sha256": sha256(dispatch_path),
                "reviewer_session_type": "codex-thread",
                "reviewer_session_id": reviewer_thread,
                "reviewed_at": "2026-08-17T00:01:00Z",
                "verdict": "tc-changes-required",
                "findings": [
                    {
                        "id": "TC-R-001",
                        "affected_items": ["TC-001"],
                        "origin_stage": "tc",
                    }
                ],
                "total_tc_count": 2,
                "reviewed_tc_count": 2,
                "reviewed_items": ["TC-001", "TC-002"],
                "review_scope_complete": True,
            }
            review_path = review_dir / "tc-review.json"
            review_path.write_text(json.dumps(previous), encoding="utf-8")
            review_path.with_suffix(".md").write_text("# Review\n\nПроверено TC: 2/2\n", encoding="utf-8")
            enrich_review_record(root, artifact, review_path, "tc", "reviews")

            artifact.write_text(original.replace("Первый.", "Первый исправлен.").replace("Второй.", "Второй изменён."), encoding="utf-8")
            manifest_path = write_revision_manifest(root, artifact, review_path, review_dir, "tc", "reviews")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("full", manifest["review_mode"])
            self.assertIn("undeclared-items-changed", manifest["fallback_reasons"])

            artifact.write_text(original.replace("Первый.", "Первый исправлен."), encoding="utf-8")
            source_file.write_text("<p>Изменённое требование</p>", encoding="utf-8")
            manifest_path.unlink()
            manifest_path = write_revision_manifest(root, artifact, review_path, review_dir, "tc", "reviews")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("full", manifest["review_mode"])
            self.assertIn("semantic-inputs-changed", manifest["fallback_reasons"])

    def test_tc_layout_rejects_noop_repair_with_tc_or_both_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            package = root / "fts" / "Project" / "FT"
            matrix_dir = package / "work" / "practical" / "9.3.1"
            review_dir = package / "work" / "reviews" / "9.3.1"
            tc_dir = package / "test-cases"
            matrix_dir.mkdir(parents=True)
            review_dir.mkdir(parents=True)
            tc_dir.mkdir(parents=True)
            matrix_path = matrix_dir / "test-design-matrix.md"
            matrix_path.write_text(VALID_MATRIX, encoding="utf-8")
            tc_path = tc_dir / "9.3.1-test-cases.md"
            tc_path.write_text(VALID_TC, encoding="utf-8")
            (matrix_dir / "workflow-state.yaml").write_text(
                "role: writer\nscope: 9.3.1\nmatrix_status: completed\n"
                'test_design_matrix: "work/practical/9.3.1/test-design-matrix.md"\n'
                "test_case_status: completed\n"
                'test_cases: "test-cases/9.3.1-test-cases.md"\n',
                encoding="utf-8",
            )
            review = {
                "schema_version": 1,
                "review_kind": "tc",
                "artifact_sha256": hashlib.sha256(tc_path.read_bytes()).hexdigest(),
                "verdict": "tc-changes-required",
                "findings": [{"id": "TC-R-001", "origin_stage": "both"}],
            }
            review_path = review_dir / "tc-review.json"
            review_path.write_text(json.dumps(review), encoding="utf-8")

            errors = validate_tc_layout(tc_path, matrix_path, package)
            self.assertTrue(any("unchanged after unresolved tc/both" in error for error in errors))

            review["findings"][0]["origin_stage"] = "matrix"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            self.assertFalse(any("unchanged after unresolved" in error for error in validate_tc_layout(tc_path, matrix_path, package)))

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

            with patch("scripts.capture_dadata_fixture.urlopen", side_effect=[Response(), Response()]):
                bank_entry = capture_fixture(
                    kind="bank",
                    query="СБЕРБАНК",
                    fixture_id="FX-DADATA-BANK-001",
                    purpose="Подсказка банка",
                    fixture_root=fixture_root,
                    token="not-written",
                )
            self.assertEqual("bank", bank_entry["request"]["suggestion_kind"])
            self.assertEqual([], validate_catalog(fixture_root / "fixture-catalog.json"))

    def test_package_creator_does_not_copy_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "Partners-v1"
            create_package(package)
            self.assertEqual(set(PACKAGE_DIRS) | {"AGENT-NOTES.md"}, {item.name for item in package.iterdir()})
            self.assertTrue((package / "work" / "scope-clarification-requests.md").is_file())
            self.assertFalse((package / "evals").exists())
            self.assertFalse((package / "references").exists())
            self.assertFalse((package / "scripts").exists())

    def test_runtime_temp_cleanup_is_limited_to_isolated_system_temp_directory(self) -> None:
        holder = tempfile.TemporaryDirectory(prefix="ft-runtime-test-")
        target = Path(holder.name)
        (target / "render.png").write_bytes(b"png")
        removed, errors = cleanup([target])
        self.assertEqual([], errors)
        self.assertEqual([str(target.resolve())], removed)
        self.assertFalse(target.exists())
        holder.cleanup()

        unsafe = Path(tempfile.gettempdir()) / "unscoped-runtime-temp"
        removed, errors = cleanup([unsafe])
        self.assertEqual([], removed)
        self.assertTrue(any("not an isolated" in error for error in errors))

        removed, errors = cleanup([Path(__file__).resolve().parents[1]])
        self.assertEqual([], removed)
        self.assertTrue(any("outside system temp" in error for error in errors))

    def test_runtime_pdf_renderer_handles_cyrillic_path_and_contact_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_dir = Path(temporary_directory) / "Исходные материалы"
            source_dir.mkdir()
            pdf_path = source_dir / "Требования Партнёры.pdf"
            import fitz

            document = fitz.open()
            document.new_page(width=300, height=400)
            document.new_page(width=400, height=300)
            document.save(pdf_path)
            document.close()

            result = render_pdf(pdf_path, "1-2", dpi=72, contact_columns=2)
            output_dir = Path(result["output_dir"])
            try:
                self.assertEqual([1, 2], result["selected_pages"])
                self.assertEqual(2, len(result["rendered_pages"]))
                self.assertEqual(1, len(result["contact_sheets"]))
                self.assertTrue(all(Path(path).is_file() for path in result["rendered_pages"]))
                self.assertTrue(Path(result["contact_sheets"][0]).is_file())
                self.assertTrue(output_dir.name.startswith("ft-runtime-pdf-visual-"))
            finally:
                cleanup([output_dir])

    def test_runtime_pdf_page_selection_is_one_based_and_bounded(self) -> None:
        self.assertEqual([0, 2, 3], parse_pages("1,3-4", 4))
        with self.assertRaises(ValueError):
            parse_pages("0", 4)
        with self.assertRaises(ValueError):
            parse_pages("4-3", 4)

    def test_semantic_roles_have_exact_skill_contracts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for role, expected_path in {
            "source-locator": "skills/ft-source-locator/SKILL.md",
            "scope-analyzer": "skills/ft-scope-analyzer/SKILL.md",
            "writer": "skills/ft-test-case-writer/SKILL.md",
            "matrix-reviewer": "skills/ft-test-case-reviewer/SKILL.md",
            "tc-reviewer": "skills/ft-test-case-reviewer/SKILL.md",
        }.items():
            contract = required_skill_contract(root, role)
            self.assertEqual(expected_path, contract["path"])
            self.assertRegex(contract["sha256"], r"^[0-9a-f]{64}$")

    def test_session_registry_detects_agent_notes_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory)
            (package / "AGENT-NOTES.md").write_text("# Вход пользователя\n", encoding="utf-8")
            initialize_registry(package, CONTROLLER_THREAD, "local")
            (package / "AGENT-NOTES.md").write_text("# Изменено во время route\n", encoding="utf-8")
            errors = validate_controller(package, CONTROLLER_THREAD)
            self.assertTrue(any("immutable package input" in error for error in errors))

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
