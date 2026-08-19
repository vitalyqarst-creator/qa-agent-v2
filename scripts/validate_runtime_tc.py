from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_state import scalar_values as state_scalar_values
    from scripts.runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from scripts.runtime_session_registry import canonical_scope, find_package_root, validate_topology
    from scripts.validate_runtime_test_data import ROLE_RE as DATA_ROLE_RE, validate as validate_test_data
    from scripts.validate_runtime_matrix import validate_layout as validate_matrix_layout
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_tc.py
    from runtime_io import configure_utf8_stdio
    from runtime_state import scalar_values as state_scalar_values
    from runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from runtime_session_registry import canonical_scope, find_package_root, validate_topology
    from validate_runtime_test_data import ROLE_RE as DATA_ROLE_RE, validate as validate_test_data
    from validate_runtime_matrix import validate_layout as validate_matrix_layout


TC_HEADING_RE = re.compile(r"^##\s+(TC-[A-Za-z0-9.-]+)\s*$", re.MULTILINE)
NUMBER_RE = re.compile(r"\*\*Сквозной номер:\*\*\s*`TC-(\d{3,})`")
NUMBERED_LINE_RE = re.compile(r"^\d+\.\s+.+", re.MULTILINE)
FIELD_RE = re.compile(r"\*\*(Название|Цель|Тип|Приоритет|Трассировка|Статус исполнения):\*\*\s*(.+)")
SECTION_RE = re.compile(
    r"\*\*(Предусловия|Тестовые данные|Шаги|Итоговый ожидаемый результат|Постусловия):\*\*[ \t]*(.*?)(?=\n\*\*|\n##\s+TC-|\Z)",
    re.DOTALL,
)
REQUIRED_FIELDS = {"Название", "Цель", "Тип", "Приоритет", "Трассировка"}
REQUIRED_SECTIONS = {"Предусловия", "Тестовые данные", "Шаги", "Итоговый ожидаемый результат", "Постусловия"}
FORBIDDEN_RUNTIME_RE = re.compile(
    r"\b(?:AS\.\d+|GAP-[A-Z0-9.-]+|SRC-[A-Z0-9.-]+|ATOM-[A-Z0-9.-]+|OBL-[A-Z0-9.-]+|TD-[A-Z0-9.-]+|REL-[A-Z0-9.-]+|FX-[A-Z0-9-]+|FIX-[A-Z0-9-]+|fixture_id|snapshot|sha-?256|needs-test-data|candidate-ui-calibration|blocked-observability)\b",
    re.IGNORECASE,
)
FORBIDDEN_DATA_RE = re.compile(
    r"требу(?:ется|ются)|нуж(?:ен|на|ны)|будут подготовлены|валидн\w* значени|сним(?:ок|ка) ответ|fixture|фикстур|"
    r"фиксированн\w* запрос|организац\w* из|ожидаем\w* реквизит|подтвержд[её]нн\w* место",
    re.IGNORECASE,
)
CONCRETE_DATA_RE = re.compile(r"`[^`\n]+`\s*=\s*`[^`\n]+`")
DATA_PAIR_RE = re.compile(r"`([^`\n]+)`\s*=\s*`([^`\n]+)`")
PARAMETER_TABLE_HEADER_RE = re.compile(
    r"^\|[^\n]*(?:Вариант|Параметр)[^\n]*\|[^\n]*Значение[^\n]*\|\s*$",
    re.IGNORECASE | re.MULTILINE,
)
PROCESS_PLACEHOLDER_RE = re.compile(
    r"\b(?:edit\s+TC|несохран[её]нн\w*\s+значени\w*|данн\w*\s+предыдущ\w*\s+TC|значени\w*\s+из\s+fixture)\b",
    re.IGNORECASE,
)
UNBOUND_RUNTIME_REFERENCE_RE = re.compile(
    r"зафиксирован\w*\s+в\s+(?:протокол|отч[её]т)\w*\s+(?:текущ\w*\s+)?прогон\w*",
    re.IGNORECASE,
)
STATUS_RE = re.compile(r"\*\*Статус исполнения:\*\*\s*([^\n]+)")
CONFIRMATION_RE = re.compile(r"\*\*Требуется подтверждение:\*\*\s*([^\n]+)")
PRECONDITION_ITEM_RE = re.compile(
    r"^\d+\.\s+(?:(?:Открыть|Перейти|Найти|Нажать|Выбрать|Ввести|Заполнить|Создать|Добавить|Подготовить|Очистить|Загрузить|Войти|Выполнить|Подтвердить|Зафиксировать)\b|(?:Пользователь|Партн[её]р|Реквизит|Объект|Запись|Файл|У\s+партн[её]ра)\b)",
    re.IGNORECASE,
)
AMBIGUOUS_STATE_SETUP_RE = re.compile(
    r"^\d+\.\s+(?:Установить|Перевести|Задать|Изменить|Привести)\b.*\bстатус",
    re.IGNORECASE,
)
LOGIN_PRECONDITION_RE = re.compile(r"^\d+\.\s+Войти\s+пользовател", re.IGNORECASE | re.MULTILINE)
PREPARED_USER_RE = re.compile(r"^\d+\.\s+Подготовить\s+пользовател", re.IGNORECASE | re.MULTILINE)
INLINE_POSTCONDITION_ACTOR_RE = re.compile(
    r"^\d+\.\s+(?!Войти\b).*\bпользовател(?:ем|ь)\s+(?:с|без)\s+роль",
    re.IGNORECASE | re.MULTILINE,
)
POSTCONDITION_LOGIN_RE = re.compile(r"^\d+\.\s+Войти\s+пользовател", re.IGNORECASE | re.MULTILINE)
POSTCONDITION_NAVIGATION_RE = re.compile(r"^\d+\.\s+(?:Открыть|Перейти)\b", re.IGNORECASE | re.MULTILINE)
POSTCONDITION_FIND_RE = re.compile(r"^\d+\.\s+Найти\b", re.IGNORECASE | re.MULTILINE)
OPAQUE_DELEGATE_STEP_RE = re.compile(r"^\d+\.\s+Выполнить\b", re.IGNORECASE | re.MULTILINE)
LOOKUP_ANYWHERE_LINE_RE = re.compile(r"^\d+\..*\bНайти\b", re.IGNORECASE)
UI_LOOKUP_RE = re.compile(r"\b(?:кнопк\w*|пол[ея]\b|раздел\w*|вкладк\w*|ссылк\w*|действи\w*)\b", re.IGNORECASE)
OBJECT_OBSERVATION_RE = re.compile(r"\b(?:виджет\w*|блок\w*|карточк\w*|партн[её]р\w*|реквизит\w*|объект\w*)\b", re.IGNORECASE)
VISIBILITY_RESULT_RE = re.compile(r"\b(?:отображ\w*|видим\w*|отсутств\w*|открыт\w*)\b", re.IGNORECASE)
ABSENCE_RESULT_RE = re.compile(
    r"\b(?:не\s+отображ\w*|не\s+видим\w*|отсутств\w*)\b",
    re.IGNORECASE,
)
IDENTITY_REFERENCE_RE = re.compile(r"\b(?:найденн\w*|выбранн\w*|указанн\w*|подготовленн\w*|этого|этот|этой)\b", re.IGNORECASE)
EDIT_PREFILL_RESULT_RE = re.compile(r"\bоткрыт\w*\s+(?:окн\w*|форм\w*|карточк\w*)\s+редактирован", re.IGNORECASE)
QUOTED_CONTROL_RE = re.compile(
    r"(?:кнопк\w*\s+)?(?:«([^»]+)»|`([^`]+)`)(?=\s+(?:видим\w*|доступ\w*))|"
    r"(?:видим\w*|доступ\w*)(?:\s+и\s+(?:видим\w*|доступ\w*))?\s+(?:кнопк\w*\s+)?(?:«([^»]+)»|`([^`]+)`)|"
    r"(?:кнопк\w*|действи\w*)\s+(?:«([^»]+)»|`([^`]+)`)",
    re.IGNORECASE,
)
BACKTICK_LITERAL_RE = re.compile(r"`([^`\n]+)`")
QUOTED_LABEL_RE = re.compile(r"«([^»]+)»")
ACTION_VERB_RE = re.compile(
    r"\b(?:Открыть|Перейти|Найти|Нажать|Выбрать|Ввести|Заполнить|Очистить|Загрузить|Скачать|"
    r"Навести|Установить|Снять|Подтвердить|Отменить|Закрыть|Сохранить|Изменить|Удалить|Добавить|"
    r"Создать|Вернуть|Архивировать|Разархивировать|Войти|Выйти|Проверить|Убедиться|Зафиксировать|"
    r"Скопировать|Вставить|Раскрыть|Свернуть|Обновить|Прокрутить)\b",
    re.IGNORECASE,
)
QUOTED_FRAGMENT_RE = re.compile(r"`[^`\n]*`|«[^»\n]*»|\"[^\"\n]*\"")
RUNTIME_BINDING_RE = re.compile(
    r"^\d+\.\s+Зафиксировать\b[^\n]*?\bкак\s+`([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9_-]{2,63})`\s*\.?$",
    re.IGNORECASE | re.MULTILINE,
)
RUNTIME_BINDING_LINE_RE = re.compile(
    r"^(?P<line>\d+\.\s+Зафиксировать\b[^\n]*?\bкак\s+`(?P<binding>[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9_-]{2,63})`\s*\.?)$",
    re.IGNORECASE | re.MULTILINE,
)
ONE_TIME_ISOLATION_RE = re.compile(r"\bодноразов\w*\b[^\n]{0,80}\bизолирован\w*\b", re.IGNORECASE)
TARGET_KIND_RE = re.compile(
    r"\b(виджет|блок|карточк|партн[её]р|реквизит|кнопк|действи|пол[ея]|строк|ссылк|вкладк)\w*\b",
    re.IGNORECASE,
)
OBSERVATION_SURFACE_RE = re.compile(
    r"\b(виджет|блок|карточк|форм|окн|спис|таблиц|строк|ответ|уведомлен|сообщен|журнал|api)\w*\b",
    re.IGNORECASE,
)
VALUE_PRESERVING_TRANSITION_RE = re.compile(
    r"\b(?:Сохранить|Создать|Добавить|Изменить|Удалить|Архивировать|Разархивировать|Вернуть|Подтвердить|Отправить|Обновить)\b",
    re.IGNORECASE,
)


def normalized_label(value: str) -> str:
    folded = value.casefold().replace("ё", "е")
    folded = re.sub(r"[^a-zа-я0-9]+", " ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def visible_selector_values(data: str) -> list[str]:
    selector_keys = {
        "партнер",
        "наименование партнера",
        "организация",
        "объект",
        "запись",
        "реквизит",
        "бик",
        "расчетный счет",
        "расч счет",
        "р с",
    }
    return [
        value.strip()
        for key, value in DATA_PAIR_RE.findall(data)
        if normalized_label(key) in selector_keys and len(value.strip()) >= 3
    ]


def isolation_identity(data: str) -> tuple[tuple[str, str], ...]:
    identity_keys = {
        "партнер",
        "партнеры",
        "наименование партнера",
        "наименование",
        "организация",
        "объект",
        "запись",
        "реквизит",
        "бик",
        "расчетный счет",
        "расч счет",
        "р с",
        "инн",
        "id",
    }
    return tuple(
        sorted(
            (normalized_label(key), value.strip().casefold())
            for key, value in DATA_PAIR_RE.findall(data)
            if normalized_label(key) in identity_keys and value.strip()
        )
    )


def action_count(line: str) -> int:
    without_labels = QUOTED_FRAGMENT_RE.sub("", line)
    count = 0
    for match in ACTION_VERB_RE.finditer(without_labels):
        prefix = without_labels[max(0, match.start() - 24) : match.start()]
        if re.search(r"(?:кнопк|действи|ссылк)\w*\s+$", prefix, re.IGNORECASE):
            continue
        count += 1
    return count


def composite_numbered_actions(value: str) -> list[str]:
    return [
        line.strip()
        for line in value.splitlines()
        if NUMBERED_LINE_RE.match(line.strip()) and action_count(line) > 1
    ]


def has_nondeterministic_outcome(value: str) -> bool:
    without_labels = QUOTED_FRAGMENT_RE.sub("", value)
    return re.search(r"\bили\b", without_labels, re.IGNORECASE) is not None


def impossible_absence_lookups(steps: str, expected: str) -> list[str]:
    """Return lookups that try to find the same target whose absence is the oracle."""
    if not ABSENCE_RESULT_RE.search(expected):
        return []
    expected_kind = TARGET_KIND_RE.search(expected)
    expected_literals = {
        literal.strip().casefold()
        for literal in BACKTICK_LITERAL_RE.findall(expected)
        if len(literal.strip()) >= 3
    }
    if not expected_kind or not expected_literals:
        return []
    expected_target_kind = normalized_label(expected_kind.group(1))
    violations: list[str] = []
    for raw_line in steps.splitlines():
        line = raw_line.strip()
        if not NUMBERED_LINE_RE.match(line) or not re.search(r"\bНайти\b", line, re.IGNORECASE):
            continue
        lookup_kind = TARGET_KIND_RE.search(line)
        if not lookup_kind or normalized_label(lookup_kind.group(1)) != expected_target_kind:
            continue
        lookup_literals = {
            literal.strip().casefold()
            for literal in BACKTICK_LITERAL_RE.findall(line)
            if len(literal.strip()) >= 3
        }
        if expected_literals & lookup_literals:
            violations.append(line)
    return violations


def circular_runtime_bindings(preconditions: str, steps: str, expected: str) -> list[str]:
    issues: list[str] = []
    step_lines = [line.strip() for line in steps.splitlines() if NUMBERED_LINE_RE.match(line.strip())]
    captures: list[tuple[str, int, str, str]] = []
    for section_name, section_value in (("Предусловия", preconditions), ("Шаги", steps)):
        numbered_lines = [
            line.strip() for line in section_value.splitlines() if NUMBERED_LINE_RE.match(line.strip())
        ]
        for index, line in enumerate(numbered_lines):
            match = RUNTIME_BINDING_LINE_RE.fullmatch(line)
            if match:
                captures.append((section_name, index, line, match.group("binding")))

    expected_clauses = [clause.strip() for clause in re.split(r"\s*;\s*", expected) if clause.strip()]
    for section_name, line_index, line, binding in captures:
        source_surface = OBSERVATION_SURFACE_RE.search(line)
        if source_surface is None:
            issues.append(f"runtime binding {binding} does not name its capture observation surface")
            continue
        clause = next((item for item in expected_clauses if f"`{binding}`" in item), expected)
        assertion_surface = OBSERVATION_SURFACE_RE.search(clause)
        if assertion_surface is None:
            issues.append(f"runtime binding {binding} does not name its assertion observation surface")
            continue
        capture_literals = {
            value.strip().casefold()
            for value in BACKTICK_LITERAL_RE.findall(line)
            if value != binding and len(value.strip()) >= 3
        }
        assertion_literals = {
            value.strip().casefold()
            for value in BACKTICK_LITERAL_RE.findall(clause)
            if value != binding and len(value.strip()) >= 3
        }
        if section_name == "Предусловия":
            following_actions = step_lines
        else:
            following_actions = step_lines[line_index + 1 :]
        has_transition = any(VALUE_PRESERVING_TRANSITION_RE.search(item) for item in following_actions)
        same_surface = normalized_label(source_surface.group(1)) == normalized_label(assertion_surface.group(1))
        same_object = bool(capture_literals & assertion_literals)
        if same_surface and same_object and not has_transition:
            issues.append(
                f"runtime binding {binding} is captured from and asserted against the same observation without a transition"
            )
    return issues


def sections(block: str) -> dict[str, str]:
    return {match.group(1): match.group(2).strip() for match in SECTION_RE.finditer(block)}


def normalize_action(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^\d+\.\s+", "", line)).strip().lower()


def has_parameter_table(value: str) -> bool:
    header = PARAMETER_TABLE_HEADER_RE.search(value)
    if not header:
        return False
    following = value[header.end() :].splitlines()
    table_lines = [line for line in following if line.strip().startswith("|")]
    return len(table_lines) >= 2


def hover_revealed_controls(matrix_rows: list[list[str]], check_index: int, result_index: int) -> set[str]:
    controls: set[str] = set()
    for row in matrix_rows:
        if not re.search(r"\bНавести\b", row[check_index], re.IGNORECASE):
            continue
        for match in QUOTED_CONTROL_RE.finditer(row[result_index]):
            label = next((group for group in match.groups() if group), "").strip().casefold()
            if label:
                controls.add(label)
    return controls


def missing_hover_prerequisites(block: str, controls: set[str]) -> list[str]:
    missing: list[str] = []
    tc_sections = sections(block)
    for section_name in ("Предусловия", "Шаги", "Постусловия"):
        lines = [line.strip() for line in tc_sections.get(section_name, "").splitlines() if NUMBERED_LINE_RE.match(line)]
        for index, line in enumerate(lines):
            line_folded = line.casefold()
            for control in controls:
                quoted = (f"«{control}»", f"`{control}`")
                if "нажать" not in line_folded or not any(value in line_folded for value in quoted):
                    continue
                previous = lines[index - 1].casefold() if index else ""
                if "навести" not in line_folded and "навести" not in previous:
                    missing.append(f"{section_name}: {control}")
    return missing


def unqualified_object_lookups(block: str) -> list[str]:
    tc_sections = sections(block)
    values = visible_selector_values(tc_sections.get("Тестовые данные", ""))
    if not values:
        return []
    errors: list[str] = []
    for section_name in ("Предусловия", "Шаги", "Постусловия"):
        lookup_lines = [
            line.strip()
            for line in tc_sections.get(section_name, "").splitlines()
            if LOOKUP_ANYWHERE_LINE_RE.match(line) and not UI_LOOKUP_RE.search(line)
        ]
        if not lookup_lines:
            continue
        lookup_text = "\n".join(lookup_lines).casefold()
        missing = [value for value in values if value.casefold() not in lookup_text]
        if missing:
            errors.append(f"{section_name}: missing visible selector literals {missing}")
    return errors


def validate(content: str) -> list[str]:
    errors: list[str] = []
    matches = list(TC_HEADING_RE.finditer(content))
    if not matches:
        return ["no canonical TC headings found"]
    numbers: list[int] = []
    one_time_identities: dict[tuple[tuple[str, str], ...], list[str]] = {}
    for index, match in enumerate(matches):
        tc_id = match.group(1)
        block = content[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(content)]
        field_pairs = FIELD_RE.findall(block)
        fields = {name: value.strip() for name, value in field_pairs}
        for field_name in {name for name, _value in field_pairs}:
            if sum(1 for name, _value in field_pairs if name == field_name) > 1:
                errors.append(f"{tc_id}: duplicate metadata field {field_name}")
        missing_fields = REQUIRED_FIELDS - fields.keys()
        if missing_fields:
            errors.append(f"{tc_id}: missing fields {sorted(missing_fields)}")
        elif fields.get("Тип") not in {"Positive", "Negative"}:
            errors.append(f"{tc_id}: Type must be Positive or Negative")
        elif fields.get("Приоритет") not in {"High", "Medium", "Low"}:
            errors.append(f"{tc_id}: Priority must be High, Medium or Low")
        tc_sections = sections(block)
        missing_sections = REQUIRED_SECTIONS - tc_sections.keys()
        if missing_sections:
            errors.append(f"{tc_id}: missing sections {sorted(missing_sections)}")
            continue
        sequential = NUMBER_RE.search(block)
        if not sequential:
            errors.append(f"{tc_id}: missing sequential number")
        else:
            numbers.append(int(sequential.group(1)))

        for section_name in ("Предусловия", "Тестовые данные", "Шаги", "Итоговый ожидаемый результат", "Постусловия"):
            value = tc_sections[section_name]
            if FORBIDDEN_RUNTIME_RE.search(value):
                errors.append(f"{tc_id}: internal marker in {section_name}")
            if UNBOUND_RUNTIME_REFERENCE_RE.search(value):
                errors.append(
                    f"{tc_id}: runtime-generated value must use an explicit capture binding, not an external run report"
                )
        preconditions = tc_sections["Предусловия"]
        if preconditions != "Не требуются." and not all(
            PRECONDITION_ITEM_RE.match(line) for line in preconditions.splitlines() if line.strip()
        ):
            errors.append(f"{tc_id}: preconditions must be numbered setup actions/state conditions or 'Не требуются.'")
        if any(AMBIGUOUS_STATE_SETUP_RE.match(line) for line in preconditions.splitlines() if line.strip()):
            errors.append(
                f"{tc_id}: ambiguous one-line state setup; declare the concrete initial state or list the full source-backed transition"
            )
        if PREPARED_USER_RE.search(preconditions):
            errors.append(
                f"{tc_id}: preparing a user does not establish the current actor; use an explicit login when the actor is needed"
            )
        steps = tc_sections["Шаги"]
        if not NUMBERED_LINE_RE.search(steps):
            errors.append(f"{tc_id}: steps must be numbered")
        if OPAQUE_DELEGATE_STEP_RE.search(steps):
            errors.append(
                f"{tc_id}: a step starting with 'Выполнить' delegates an unspecified flow; list the observable user actions explicitly"
            )
        for line in composite_numbered_actions(steps):
            errors.append(f"{tc_id}: one numbered step must contain one user action or one verification ({line})")
        for lookup in unqualified_object_lookups(block):
            errors.append(f"{tc_id}: object lookup must use a concrete literal from test data ({lookup})")
        data = tc_sections["Тестовые данные"]
        if data != "Не требуются." and FORBIDDEN_DATA_RE.search(data):
            errors.append(f"{tc_id}: test data are a dependency note, not concrete values")
        if data != "Не требуются." and not CONCRETE_DATA_RE.search(data) and not has_parameter_table(data):
            errors.append(f"{tc_id}: test data must include a concrete `field` = `value` literal")
        data_pairs = DATA_PAIR_RE.findall(data)
        if ONE_TIME_ISOLATION_RE.search(f"{preconditions}\n{tc_sections['Постусловия']}"):
            identity = isolation_identity(data)
            if identity:
                one_time_identities.setdefault(identity, []).append(tc_id)
        data_keys = [key.strip().casefold() for key, _value in data_pairs]
        duplicate_keys = sorted({key for key in data_keys if data_keys.count(key) > 1})
        if duplicate_keys:
            errors.append(f"{tc_id}: duplicate test-data keys require a parameter table: {duplicate_keys}")
        if PROCESS_PLACEHOLDER_RE.search(data):
            errors.append(f"{tc_id}: process placeholder in test data")
        expected = tc_sections["Итоговый ожидаемый результат"]
        for lookup in impossible_absence_lookups(steps, expected):
            errors.append(
                f"{tc_id}: a step cannot find the same target whose absence is required by the expected result ({lookup})"
            )
        runtime_bindings = set(RUNTIME_BINDING_RE.findall(f"{preconditions}\n{steps}"))
        for issue in circular_runtime_bindings(preconditions, steps, expected):
            errors.append(f"{tc_id}: {issue}")
        data_values = [value.strip().casefold() for _key, value in data_pairs if len(value.strip()) >= 3]
        declared_values = {value.strip() for _key, value in data_pairs}.union(runtime_bindings)
        undeclared_identifiers = sorted(
            {
                literal
                for literal in BACKTICK_LITERAL_RE.findall(expected)
                if len(literal) >= 6
                and any(character.isdigit() for character in literal)
                and re.fullmatch(r"[A-Za-zА-Яа-я0-9_.:/+\-]+", literal)
                and literal not in declared_values
            }
        )
        if undeclared_identifiers:
            errors.append(
                f"{tc_id}: expected-result identifiers must be declared in test data: {undeclared_identifiers}"
            )
        unused_bindings = sorted(
            binding for binding in runtime_bindings if f"`{binding}`" not in expected
        )
        if unused_bindings:
            errors.append(f"{tc_id}: captured runtime bindings must be reused in the expected result: {unused_bindings}")
        if (
            data_values
            and OBJECT_OBSERVATION_RE.search(expected)
            and VISIBILITY_RESULT_RE.search(expected)
            and not IDENTITY_REFERENCE_RE.search(expected)
            and not any(value in expected.casefold() for value in data_values)
        ):
            errors.append(f"{tc_id}: object visibility/opening result must identify the observed test-data object")
        if EDIT_PREFILL_RESULT_RE.search(expected) and data_values and not any(
            value in expected.casefold() for value in data_values
        ):
            errors.append(f"{tc_id}: edit-form prefill result must list concrete expected literals")
        precondition_actions = {normalize_action(line) for line in preconditions.splitlines() if PRECONDITION_ITEM_RE.match(line)}
        step_actions = {normalize_action(line) for line in steps.splitlines() if NUMBERED_LINE_RE.match(line)}
        if precondition_actions & step_actions:
            errors.append(f"{tc_id}: setup action is duplicated in steps")
        if has_nondeterministic_outcome(expected):
            errors.append(f"{tc_id}: expected result must be deterministic")
        status_match = STATUS_RE.search(block)
        status = status_match.group(1).strip().strip("`") if status_match else "ready"
        if status not in {"ready", "needs-test-data", "candidate-ui-calibration"}:
            errors.append(f"{tc_id}: unsupported canonical execution status {status}")
        if status == "candidate-ui-calibration" and not CONFIRMATION_RE.search(block):
            errors.append(f"{tc_id}: candidate-ui-calibration requires 'Требуется подтверждение'")
        postconditions = tc_sections["Постусловия"]
        empty_postconditions = postconditions in {"Не требуются.", "- Не требуются."}
        if not empty_postconditions and not all(
            NUMBERED_LINE_RE.fullmatch(line) for line in postconditions.splitlines() if line.strip()
        ):
            errors.append(f"{tc_id}: non-empty postconditions must be numbered executable actions")
        if INLINE_POSTCONDITION_ACTOR_RE.search(postconditions):
            errors.append(f"{tc_id}: actor switch in postconditions must be a separate explicit login action")
        if POSTCONDITION_LOGIN_RE.search(postconditions):
            if not POSTCONDITION_NAVIGATION_RE.search(postconditions) or not POSTCONDITION_FIND_RE.search(postconditions):
                errors.append(
                    f"{tc_id}: postcondition actor switch requires renewed navigation and object lookup before cleanup"
                )
        for line in composite_numbered_actions(postconditions):
            errors.append(
                f"{tc_id}: one numbered postcondition must contain one user action or one verification ({line})"
            )
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        errors.append("sequential TC numbers are not continuous from TC-001")
    for tc_ids in one_time_identities.values():
        if len(tc_ids) > 1:
            errors.append(
                "one-time isolated identity tuple is reused across test cases: " + ", ".join(tc_ids)
            )
    return errors


def validate_layout(
    test_cases_path: Path,
    matrix_path: Path,
    package_root: Path,
    data_materialization_path: Path | None = None,
) -> list[str]:
    errors = validate_matrix_layout(matrix_path, package_root)
    expected_tc_root = (package_root / "test-cases").resolve()
    try:
        test_cases_path.resolve().relative_to(expected_tc_root)
    except ValueError:
        errors.append(f"test cases must be stored under {expected_tc_root}")
    state_path = matrix_path.parent / "workflow-state.yaml"
    if not state_path.is_file():
        return errors
    state = state_scalar_values(state_path.read_text(encoding="utf-8"))
    try:
        tc_relative = test_cases_path.resolve().relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return errors
    if state.get("test_case_status") != "completed":
        errors.append("writer workflow-state is missing completed test-case status")
    if state.get("test_cases") != tc_relative:
        errors.append("writer workflow-state does not reference the validated test-case file")
    matrix_content = matrix_path.read_text(encoding="utf-8")
    if DATA_ROLE_RE.search(matrix_content):
        if data_materialization_path is None:
            errors.append("matrix uses TD-* roles but --data-materialization was not provided")
        else:
            try:
                data_relative = data_materialization_path.resolve().relative_to(package_root.resolve()).as_posix()
            except ValueError:
                data_relative = ""
                errors.append("data materialization escapes FT package")
            if state.get("data_status") != "completed":
                errors.append("writer workflow-state is missing completed data status")
            if data_relative and state.get("data_materialization") != data_relative:
                errors.append("writer workflow-state does not reference the validated data materialization")
    review_path = package_root / "work" / "reviews" / matrix_path.parent.name / "tc-review.json"
    if review_path.is_file():
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            review = None
        if (
            isinstance(review, dict)
            and review.get("schema_version") in {1, 2}
            and review.get("review_kind") == "tc"
            and review.get("verdict") == "tc-changes-required"
            and review.get("artifact_sha256") == hashlib.sha256(test_cases_path.read_bytes()).hexdigest()
        ):
            findings = review.get("findings")
            if isinstance(findings, list) and any(
                isinstance(finding, dict) and finding.get("origin_stage") in {"tc", "both"}
                for finding in findings
            ):
                errors.append(
                    "canonical TC bytes are unchanged after unresolved tc/both review findings"
                )
    return errors


def validate_materialized_projection(
    content: str,
    matrix_content: str,
    materialization_path: Path,
) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(materialization_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot project invalid data materialization into TC: {exc}"]
    bindings = {
        binding.get("role_id"): binding
        for binding in payload.get("bindings", [])
        if isinstance(binding, dict) and isinstance(binding.get("role_id"), str)
    }
    matrix = find_markdown_table(matrix_content, ("ID", "Тестовые данные и отношения", "Решение"))
    if matrix is None:
        return ["cannot project materialized data without matrix data roles"]
    roles_by_matrix: dict[str, set[str]] = {}
    for row in matrix.rows:
        if row[matrix.index("Решение")] == "TC":
            roles_by_matrix[row[matrix.index("ID")]] = set(
                DATA_ROLE_RE.findall(row[matrix.index("Тестовые данные и отношения")])
            )
    matches = list(TC_HEADING_RE.finditer(content))
    for index, match in enumerate(matches):
        tc_id = match.group(1)
        block = content[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(content)]
        fields = {name: value.strip() for name, value in FIELD_RE.findall(block)}
        traceability = fields.get("Трассировка", "")
        tc_data = sections(block).get("Тестовые данные", "")
        linked_matrix = {
            matrix_id
            for matrix_id in roles_by_matrix
            if re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(matrix_id)}(?![A-Za-z0-9_.-])", traceability)
        }
        roles = {role for matrix_id in linked_matrix for role in roles_by_matrix[matrix_id]}
        for role in sorted(roles):
            binding = bindings.get(role)
            if not isinstance(binding, dict):
                continue
            values = binding.get("values")
            if not isinstance(values, dict):
                continue
            for field, value in values.items():
                if str(value) not in tc_data:
                    errors.append(f"{tc_id}: materialized value {role}.{field} is absent from test data")
    return errors


def validate_projection(content: str, matrix_content: str) -> list[str]:
    errors: list[str] = []
    matrix = find_markdown_table(
        matrix_content,
        ("ID", "Источник требования", "Проверка", "Профили тест-дизайна", "Решение"),
    )
    if matrix is None or not matrix.rows:
        return ["TC projection cannot be checked without matrix rows"]
    source_index = matrix.index("Источник требования")
    check_index = matrix.index("Проверка")
    profile_index = matrix.index("Профили тест-дизайна")
    decision_index = matrix.index("Решение")
    matrix_id_index = matrix.index("ID")
    result_index = matrix.index("Ожидаемый результат")
    data_index = matrix.index("Тестовые данные и отношения")
    coverage_index = matrix.index("Элемент покрытия")
    hover_controls = hover_revealed_controls(matrix.rows, check_index, result_index)
    required_anchors: set[str] = set()
    all_matrix_anchors: set[str] = set()
    matrix_requirement_codes: set[str] = set()
    executable_rows: dict[str, set[str]] = {}
    row_profiles: dict[str, str] = {}
    row_data_pairs: dict[str, list[tuple[str, str]]] = {}
    row_prefill_labels: dict[str, list[str]] = {}
    all_matrix_ids: set[str] = set()
    for row in matrix.rows:
        matrix_id = row[matrix_id_index].strip()
        all_matrix_ids.add(matrix_id)
        anchors = extract_anchors(row[source_index])
        all_matrix_anchors.update(anchors)
        matrix_requirement_codes.update(anchor for anchor in anchors if anchor.startswith("CODE:"))
        if row[decision_index] == "TC":
            required_anchors.update(anchors)
            executable_rows[matrix_id] = anchors
            row_profiles[matrix_id] = row[profile_index].casefold()
            row_data_pairs[matrix_id] = DATA_PAIR_RE.findall(row[data_index])
            if "предзаполн" in " ".join((row[check_index], row[coverage_index], row[result_index])).casefold():
                row_prefill_labels[matrix_id] = QUOTED_LABEL_RE.findall(row[result_index])

    tc_matches = list(TC_HEADING_RE.finditer(content))
    tc_traceability_values: list[str] = []
    tc_blocks: list[tuple[str, str, str]] = []
    for index, match in enumerate(tc_matches):
        tc_id = match.group(1)
        block = content[match.end() : tc_matches[index + 1].start() if index + 1 < len(tc_matches) else len(content)]
        fields = {name: value.strip() for name, value in FIELD_RE.findall(block)}
        traceability = fields.get("Трассировка", "")
        tc_traceability_values.append(traceability)
        tc_blocks.append((tc_id, block, traceability))
    tc_traceability = "\n".join(tc_traceability_values)
    tc_anchors = extract_anchors(tc_traceability)
    referenced_matrix_ids: set[str] = set()
    for tc_id, block, traceability in tc_blocks:
        linked_ids = {
            matrix_id
            for matrix_id in all_matrix_ids
            if re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(matrix_id)}(?![A-Za-z0-9_.-])", traceability)
        }
        referenced_matrix_ids.update(linked_ids)
        traceability_anchors = extract_anchors(traceability)
        runtime_text = "\n".join(sections(block).values())
        leaked_codes = sorted(
            matrix_requirement_codes.intersection(
                anchor for anchor in extract_anchors(runtime_text) if anchor.startswith("CODE:")
            )
        )
        if leaked_codes:
            errors.append(
                f"{tc_id}: requirement codes are allowed only in traceability: "
                + ", ".join(anchor_label(anchor) for anchor in leaked_codes)
            )
        linked_profiles = {row_profiles.get(matrix_id, "") for matrix_id in linked_ids}
        tc_sections = sections(block)
        tc_data = tc_sections.get("Тестовые данные", "")
        tc_expected = tc_sections.get("Итоговый ожидаемый результат", "")
        if any("ролевой-доступ" in profiles for profiles in linked_profiles):
            preconditions = sections(block).get("Предусловия", "")
            if not LOGIN_PRECONDITION_RE.search(preconditions):
                errors.append(f"{tc_id}: role-based matrix row requires an explicit login precondition")
        for missing in missing_hover_prerequisites(block, hover_controls):
            errors.append(f"{tc_id}: hover-revealed control requires an explicit hover immediately before click ({missing})")
        for matrix_id in linked_ids:
            if matrix_id not in executable_rows:
                errors.append(f"test case links non-executable matrix row {matrix_id}")
                continue
            for missing in sorted(executable_rows[matrix_id] - traceability_anchors):
                errors.append(f"test case linked to {matrix_id} omits {anchor_label(missing)}")
            for _field, value in row_data_pairs.get(matrix_id, []):
                if value.strip() not in tc_data:
                    errors.append(
                        f"{tc_id}: exact matrix test-data literal from {matrix_id} is absent: {value.strip()}"
                    )
            tc_pairs = {normalized_label(field): value.strip() for field, value in DATA_PAIR_RE.findall(tc_data)}
            for label in row_prefill_labels.get(matrix_id, []):
                normalized = normalized_label(label)
                value = tc_pairs.get(normalized)
                if value is None:
                    errors.append(f"{tc_id}: prefill field from {matrix_id} is absent from test data: {label}")
                    continue
                if label.casefold() not in tc_expected.casefold() or value not in tc_expected:
                    errors.append(
                        f"{tc_id}: prefill oracle must state the field-value pair from {matrix_id}: {label} = {value}"
                    )
    for matrix_id in sorted(executable_rows.keys() - referenced_matrix_ids):
        errors.append(f"test cases do not project executable matrix row {matrix_id}")
    for missing in sorted(required_anchors - tc_anchors):
        errors.append(f"test cases do not project matrix obligation {anchor_label(missing)}")
    for extra in sorted(tc_anchors - all_matrix_anchors):
        errors.append(f"test-case traceability is absent from the matrix: {anchor_label(extra)}")
    return errors


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate lean runtime test cases.")
    parser.add_argument("test_cases", type=Path)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--data-materialization", type=Path)
    args = parser.parse_args()
    content = args.test_cases.read_text(encoding="utf-8")
    matrix_content = args.matrix.read_text(encoding="utf-8")
    errors = validate(content)
    errors.extend(validate_projection(content, matrix_content))
    package_root = find_package_root(args.matrix)
    if package_root is None:
        errors.append("cannot locate FT package root for session topology validation")
    else:
        materialization = args.data_materialization.resolve() if args.data_materialization else None
        errors.extend(validate_layout(args.test_cases, args.matrix, package_root, materialization))
        if materialization is not None:
            data_plan = (
                package_root
                / "work"
                / "stage-handoffs"
                / args.matrix.parent.name
                / "test-data-plan.md"
            )
            if not data_plan.is_file():
                errors.append(f"data plan is missing for materialization validation: {data_plan}")
            else:
                errors.extend(validate_test_data(materialization, args.matrix.resolve(), data_plan))
                errors.extend(validate_materialized_projection(content, matrix_content, materialization))
        errors.extend(validate_topology(package_root, "writer", canonical_scope(args.matrix.parent.name)))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
