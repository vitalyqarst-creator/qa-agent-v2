from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from scripts.runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from scripts.runtime_session_registry import canonical_scope, find_package_root, validate_topology
    from scripts.validate_runtime_matrix import validate_layout as validate_matrix_layout
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_tc.py
    from runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from runtime_session_registry import canonical_scope, find_package_root, validate_topology
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
    r"\b(?:AS\.\d+|GAP-[A-Z0-9.-]+|SRC-[A-Z0-9.-]+|ATOM-[A-Z0-9.-]+|OBL-[A-Z0-9.-]+|FX-[A-Z0-9-]+|FIX-[A-Z0-9-]+|fixture_id|snapshot|sha-?256|needs-test-data|candidate-ui-calibration|blocked-observability)\b",
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
STATUS_RE = re.compile(r"\*\*Статус исполнения:\*\*\s*([^\n]+)")
CONFIRMATION_RE = re.compile(r"\*\*Требуется подтверждение:\*\*\s*([^\n]+)")
PRECONDITION_ITEM_RE = re.compile(
    r"^\d+\.\s+(?:(?:Открыть|Перейти|Найти|Нажать|Выбрать|Ввести|Заполнить|Создать|Добавить|Подготовить|Очистить|Загрузить|Войти|Выполнить|Подтвердить)\b|(?:Пользователь|Партн[её]р|Реквизит|Объект|Запись|У\s+партн[её]ра)\b)",
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
LOOKUP_LINE_RE = re.compile(r"^\d+\.\s+Найти\b", re.IGNORECASE)
UI_LOOKUP_RE = re.compile(r"\b(?:кнопк\w*|пол[ея]\b|раздел\w*|вкладк\w*|ссылк\w*|действи\w*)\b", re.IGNORECASE)
OBJECT_OBSERVATION_RE = re.compile(r"\b(?:виджет\w*|блок\w*|карточк\w*|партн[её]р\w*|реквизит\w*|объект\w*)\b", re.IGNORECASE)
VISIBILITY_RESULT_RE = re.compile(r"\b(?:отображ\w*|видим\w*|отсутств\w*|открыт\w*)\b", re.IGNORECASE)
IDENTITY_REFERENCE_RE = re.compile(r"\b(?:найденн\w*|выбранн\w*|указанн\w*|подготовленн\w*|этого|этот|этой)\b", re.IGNORECASE)
EDIT_PREFILL_RESULT_RE = re.compile(r"\bоткрыт\w*\s+(?:окн\w*|форм\w*|карточк\w*)\s+редактирован", re.IGNORECASE)
QUOTED_CONTROL_RE = re.compile(
    r"(?:кнопк\w*\s+)?(?:«([^»]+)»|`([^`]+)`)(?=\s+(?:видим\w*|доступ\w*))|"
    r"(?:видим\w*|доступ\w*)(?:\s+и\s+(?:видим\w*|доступ\w*))?\s+(?:кнопк\w*\s+)?(?:«([^»]+)»|`([^`]+)`)|"
    r"(?:кнопк\w*|действи\w*)\s+(?:«([^»]+)»|`([^`]+)`)",
    re.IGNORECASE,
)


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
    values = [value.strip().casefold() for _key, value in DATA_PAIR_RE.findall(tc_sections.get("Тестовые данные", ""))]
    values = [value for value in values if len(value) >= 3]
    if not values:
        return []
    errors: list[str] = []
    for section_name in ("Предусловия", "Шаги", "Постусловия"):
        for line in tc_sections.get(section_name, "").splitlines():
            if not LOOKUP_LINE_RE.match(line) or UI_LOOKUP_RE.search(line):
                continue
            if not any(value in line.casefold() for value in values):
                errors.append(f"{section_name}: {line.strip()}")
    return errors


def validate(content: str) -> list[str]:
    errors: list[str] = []
    matches = list(TC_HEADING_RE.finditer(content))
    if not matches:
        return ["no canonical TC headings found"]
    numbers: list[int] = []
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
        for lookup in unqualified_object_lookups(block):
            errors.append(f"{tc_id}: object lookup must use a concrete literal from test data ({lookup})")
        data = tc_sections["Тестовые данные"]
        if data != "Не требуются." and FORBIDDEN_DATA_RE.search(data):
            errors.append(f"{tc_id}: test data are a dependency note, not concrete values")
        if data != "Не требуются." and not CONCRETE_DATA_RE.search(data) and not has_parameter_table(data):
            errors.append(f"{tc_id}: test data must include a concrete `field` = `value` literal")
        data_pairs = DATA_PAIR_RE.findall(data)
        data_keys = [key.strip().casefold() for key, _value in data_pairs]
        duplicate_keys = sorted({key for key in data_keys if data_keys.count(key) > 1})
        if duplicate_keys:
            errors.append(f"{tc_id}: duplicate test-data keys require a parameter table: {duplicate_keys}")
        if PROCESS_PLACEHOLDER_RE.search(data):
            errors.append(f"{tc_id}: process placeholder in test data")
        expected = tc_sections["Итоговый ожидаемый результат"]
        data_values = [value.strip().casefold() for _key, value in data_pairs if len(value.strip()) >= 3]
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
        if " или " in expected.lower():
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
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        errors.append("sequential TC numbers are not continuous from TC-001")
    return errors


def validate_layout(test_cases_path: Path, matrix_path: Path, package_root: Path) -> list[str]:
    errors = validate_matrix_layout(matrix_path, package_root)
    expected_tc_root = (package_root / "test-cases").resolve()
    try:
        test_cases_path.resolve().relative_to(expected_tc_root)
    except ValueError:
        errors.append(f"test cases must be stored under {expected_tc_root}")
    state_path = matrix_path.parent / "workflow-state.yaml"
    if not state_path.is_file():
        return errors
    state = state_path.read_text(encoding="utf-8")
    try:
        tc_relative = test_cases_path.resolve().relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return errors
    if not re.search(r"(?m)^test_case_status:\s*completed\s*$", state):
        errors.append("writer workflow-state is missing completed test-case status")
    if not re.search(rf"(?m)^test_cases:\s*[\"']?{re.escape(tc_relative)}[\"']?\s*$", state):
        errors.append("writer workflow-state does not reference the validated test-case file")
    review_path = package_root / "work" / "reviews" / matrix_path.parent.name / "tc-review.json"
    if review_path.is_file():
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            review = None
        if (
            isinstance(review, dict)
            and review.get("schema_version") == 1
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
    hover_controls = hover_revealed_controls(matrix.rows, check_index, result_index)
    required_anchors: set[str] = set()
    all_matrix_anchors: set[str] = set()
    executable_rows: dict[str, set[str]] = {}
    row_profiles: dict[str, str] = {}
    all_matrix_ids: set[str] = set()
    for row in matrix.rows:
        matrix_id = row[matrix_id_index].strip()
        all_matrix_ids.add(matrix_id)
        anchors = extract_anchors(row[source_index])
        all_matrix_anchors.update(anchors)
        if row[decision_index] == "TC":
            required_anchors.update(anchors)
            executable_rows[matrix_id] = anchors
            row_profiles[matrix_id] = row[profile_index].casefold()

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
        linked_profiles = {row_profiles.get(matrix_id, "") for matrix_id in linked_ids}
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
    for matrix_id in sorted(executable_rows.keys() - referenced_matrix_ids):
        errors.append(f"test cases do not project executable matrix row {matrix_id}")
    for missing in sorted(required_anchors - tc_anchors):
        errors.append(f"test cases do not project matrix obligation {anchor_label(missing)}")
    for extra in sorted(tc_anchors - all_matrix_anchors):
        errors.append(f"test-case traceability is absent from the matrix: {anchor_label(extra)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate lean runtime test cases.")
    parser.add_argument("test_cases", type=Path)
    parser.add_argument("--matrix", type=Path, required=True)
    args = parser.parse_args()
    content = args.test_cases.read_text(encoding="utf-8")
    errors = validate(content)
    errors.extend(validate_projection(content, args.matrix.read_text(encoding="utf-8")))
    package_root = find_package_root(args.matrix)
    if package_root is None:
        errors.append("cannot locate FT package root for session topology validation")
    else:
        errors.extend(validate_layout(args.test_cases, args.matrix, package_root))
        errors.extend(validate_topology(package_root, "writer", canonical_scope(args.matrix.parent.name)))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
