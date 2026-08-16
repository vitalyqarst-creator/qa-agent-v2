from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TC_HEADING_RE = re.compile(r"^##\s+(TC-[A-Za-z0-9.-]+)\s*$", re.MULTILINE)
NUMBER_RE = re.compile(r"\*\*Сквозной номер:\*\*\s*`TC-(\d{3,})`")
NUMBERED_LINE_RE = re.compile(r"^\d+\.\s+.+", re.MULTILINE)
FIELD_RE = re.compile(r"\*\*(Название|Цель|Тип|Приоритет|Трассировка):\*\*\s*(.+)")
SECTION_RE = re.compile(
    r"\*\*(Предусловия|Тестовые данные|Шаги|Итоговый ожидаемый результат|Постусловия):\*\*[ \t]*(.*?)(?=\n\*\*|\n##\s+TC-|\Z)",
    re.DOTALL,
)
REQUIRED_FIELDS = {"Название", "Цель", "Тип", "Приоритет", "Трассировка"}
REQUIRED_SECTIONS = {"Предусловия", "Тестовые данные", "Шаги", "Итоговый ожидаемый результат", "Постусловия"}
FORBIDDEN_RUNTIME_RE = re.compile(
    r"\b(?:AS\.\d+|GAP-\d+|SRC-\d+|ATOM-\d+|OBL-\d+|FX-[A-Z0-9-]+|FIX-[A-Z0-9-]+|fixture_id|snapshot|sha-?256|needs-test-data|candidate-ui-calibration|blocked-observability)\b",
    re.IGNORECASE,
)
FORBIDDEN_DATA_RE = re.compile(
    r"требу(?:ется|ются)|нуж(?:ен|на|ны)|будут подготовлены|валидн\w* значени|сним(?:ок|ка) ответ|fixture|фикстур|"
    r"фиксированн\w* запрос|организац\w* из|ожидаем\w* реквизит|подтвержд[её]нн\w* место",
    re.IGNORECASE,
)
CONCRETE_DATA_RE = re.compile(r"`[^`\n]+`\s*=\s*`[^`\n]+`")
PRECONDITION_VERB_RE = re.compile(
    r"^\d+\.\s+(?:Открыть|Перейти|Найти|Нажать|Выбрать|Ввести|Заполнить|Создать|Добавить|Подготовить|Установить|Очистить|Загрузить)\b",
    re.IGNORECASE,
)


def sections(block: str) -> dict[str, str]:
    return {match.group(1): match.group(2).strip() for match in SECTION_RE.finditer(block)}


def normalize_action(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^\d+\.\s+", "", line)).strip().lower()


def validate(content: str) -> list[str]:
    errors: list[str] = []
    matches = list(TC_HEADING_RE.finditer(content))
    if not matches:
        return ["no canonical TC headings found"]
    numbers: list[int] = []
    for index, match in enumerate(matches):
        tc_id = match.group(1)
        block = content[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(content)]
        fields = {name: value.strip() for name, value in FIELD_RE.findall(block)}
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
            PRECONDITION_VERB_RE.match(line) for line in preconditions.splitlines() if line.strip()
        ):
            errors.append(f"{tc_id}: preconditions must be numbered setup actions or 'Не требуются.'")
        steps = tc_sections["Шаги"]
        if not NUMBERED_LINE_RE.search(steps):
            errors.append(f"{tc_id}: steps must be numbered")
        data = tc_sections["Тестовые данные"]
        if data != "Не требуются." and FORBIDDEN_DATA_RE.search(data):
            errors.append(f"{tc_id}: test data are a dependency note, not concrete values")
        if data != "Не требуются." and not CONCRETE_DATA_RE.search(data):
            errors.append(f"{tc_id}: test data must include a concrete `field` = `value` literal")
        precondition_actions = {normalize_action(line) for line in preconditions.splitlines() if PRECONDITION_VERB_RE.match(line)}
        step_actions = {normalize_action(line) for line in steps.splitlines() if NUMBERED_LINE_RE.match(line)}
        if precondition_actions & step_actions:
            errors.append(f"{tc_id}: setup action is duplicated in steps")
        if " или " in tc_sections["Итоговый ожидаемый результат"].lower():
            errors.append(f"{tc_id}: expected result must be deterministic")
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        errors.append("sequential TC numbers are not continuous from TC-001")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate lean runtime test cases.")
    parser.add_argument("test_cases", type=Path)
    args = parser.parse_args()
    errors = validate(args.test_cases.read_text(encoding="utf-8"))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
