from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_HEADERS = (
    "ID",
    "Источник требования",
    "Проверка",
    "Профили тест-дизайна",
    "Предусловие/исходное состояние",
    "Конкретные тестовые данные",
    "Ожидаемый результат",
    "Решение",
)
ALLOWED_PROFILES = {
    "базовый",
    "обязательность",
    "только-чтение",
    "автозаполнение",
    "допустимые-классы",
    "границы",
    "справочник",
    "ролевой-доступ",
    "переход-состояния",
    "жизненный-цикл-создания",
    "согласованность-представлений",
    "аудит-история",
    "файл",
}
ALLOWED_DECISIONS = {"TC", "coverage-gap"}
EMPTY_RE = re.compile(r"^(?:-|—|n/?a|не определен[оы]?|требу(?:ется|ются))\.?$", re.IGNORECASE)


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def find_matrix(lines: list[str]) -> tuple[list[str], list[list[str]]] | None:
    for index, line in enumerate(lines[:-1]):
        header = cells(line)
        if not all(name in header for name in REQUIRED_HEADERS):
            continue
        separator = cells(lines[index + 1])
        if len(separator) != len(header) or not all(re.fullmatch(r":?-{3,}:?", item) for item in separator):
            continue
        rows: list[list[str]] = []
        for candidate in lines[index + 2 :]:
            if not candidate.strip().startswith("|"):
                break
            row = cells(candidate)
            if len(row) == len(header):
                rows.append(row)
        return header, rows
    return None


def validate(content: str) -> list[str]:
    errors: list[str] = []
    matrix = find_matrix(content.splitlines())
    if matrix is None:
        return ["required test-design matrix table was not found"]
    header, rows = matrix
    missing = [name for name in REQUIRED_HEADERS if name not in header]
    if missing:
        errors.append(f"missing matrix headers: {missing}")
    if not rows:
        errors.append("matrix has no data rows")
        return errors

    index_by_name = {name: header.index(name) for name in REQUIRED_HEADERS if name in header}
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        row_id = row[index_by_name["ID"]]
        if not row_id or EMPTY_RE.fullmatch(row_id):
            errors.append(f"row {row_number}: ID is empty")
        elif row_id in seen_ids:
            errors.append(f"row {row_number}: duplicate ID {row_id}")
        else:
            seen_ids.add(row_id)

        for field in ("Источник требования", "Проверка", "Предусловие/исходное состояние", "Ожидаемый результат"):
            value = row[index_by_name[field]]
            if not value or EMPTY_RE.fullmatch(value):
                errors.append(f"{row_id or f'row {row_number}'}: empty {field}")

        profiles_raw = row[index_by_name["Профили тест-дизайна"]]
        profiles = [item.strip() for item in re.split(r"[,;]", profiles_raw) if item.strip()]
        if not profiles:
            errors.append(f"{row_id}: no test-design profile")
        for profile in profiles:
            if profile not in ALLOWED_PROFILES and not profile.startswith("другой:"):
                errors.append(f"{row_id}: unknown test-design profile {profile!r}")

        decision = row[index_by_name["Решение"]]
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{row_id}: decision must be TC or coverage-gap")
        data = row[index_by_name["Конкретные тестовые данные"]]
        if decision == "TC" and (not data or EMPTY_RE.fullmatch(data)):
            errors.append(f"{row_id}: TC decision requires concrete data or 'Не требуются.'")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the compact runtime test-design matrix.")
    parser.add_argument("matrix", type=Path)
    args = parser.parse_args()
    errors = validate(args.matrix.read_text(encoding="utf-8"))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
