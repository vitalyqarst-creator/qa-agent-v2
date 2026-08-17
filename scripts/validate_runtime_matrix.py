from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from scripts.runtime_traceability import anchor_label, extract_anchors, find_markdown_table
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_matrix.py
    from runtime_traceability import anchor_label, extract_anchors, find_markdown_table


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
SOURCE_ROW_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.-])SR-\d{2,}(?![A-Za-z0-9_.-])")


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


def validate_projection(content: str, inventory_content: str, gaps_content: str) -> list[str]:
    errors: list[str] = []
    inventory = find_markdown_table(inventory_content, ("ID", "Источник", "Утверждение для покрытия"))
    matrix = find_markdown_table(content, REQUIRED_HEADERS)
    if inventory is None or not inventory.rows:
        return ["source-row-inventory has no required source rows table"]
    if matrix is None or not matrix.rows:
        return ["matrix projection cannot be checked without matrix rows"]

    inventory_anchors: set[str] = set()
    inventory_ids: set[str] = set()
    inventory_id_index = inventory.index("ID")
    inventory_source_index = inventory.index("Источник")
    for row in inventory.rows:
        inventory_id = row[inventory_id_index].strip()
        if not inventory_id:
            errors.append("source-row-inventory contains an empty ID")
            continue
        inventory_ids.add(inventory_id)
        inventory_anchors.update(extract_anchors(row[inventory_source_index]))

    matrix_source_index = matrix.index("Источник требования")
    matrix_decision_index = matrix.index("Решение")
    matrix_id_index = matrix.index("ID")
    matrix_anchors: set[str] = set()
    matrix_rows_by_id: dict[str, tuple[str, ...]] = {}
    for row in matrix.rows:
        matrix_source = row[matrix_source_index]
        matrix_anchors.update(extract_anchors(matrix_source))
        matrix_rows_by_id[row[matrix_id_index]] = row
    matrix_sources = "\n".join(row[matrix_source_index] for row in matrix.rows)
    for inventory_id in sorted(inventory_ids):
        if not re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(inventory_id)}(?![A-Za-z0-9_.-])", matrix_sources):
            errors.append(f"matrix does not project source-row inventory item {inventory_id}")
    for missing in sorted(inventory_anchors - matrix_anchors):
        errors.append(f"matrix does not project source obligation {anchor_label(missing)}")

    gaps = find_markdown_table(gaps_content, ("ID", "Связанная обязанность", "Источник"))
    if "GAP-" in gaps_content and (gaps is None or not gaps.rows):
        errors.append("coverage-gaps contains GAP IDs but has no table with ID, Связанная обязанность and Источник")
    elif gaps is not None:
        for gap_row in gaps.rows:
            gap_id = gap_row[gaps.index("ID")]
            linked_sources = SOURCE_ROW_TOKEN_RE.findall(gap_row[gaps.index("Связанная обязанность")])
            if len(linked_sources) != 1:
                errors.append(f"{gap_id}: coverage gap must link exactly one atomic SR obligation")
                continue
            if linked_sources[0] not in inventory_ids:
                errors.append(f"{gap_id}: linked source obligation {linked_sources[0]} is absent from active inventory")
                continue
            matrix_row = matrix_rows_by_id.get(gap_id)
            if matrix_row is None:
                errors.append(f"matrix omits unresolved obligation {gap_id}")
            elif matrix_row[matrix_decision_index] != "coverage-gap":
                errors.append(f"{gap_id}: matrix decision must be coverage-gap")
            else:
                projected_sources = set(SOURCE_ROW_TOKEN_RE.findall(matrix_row[matrix_source_index]))
                if projected_sources != {linked_sources[0]}:
                    errors.append(
                        f"{gap_id}: matrix coverage-gap row must project only linked obligation {linked_sources[0]}"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the compact runtime test-design matrix.")
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--source-inventory", type=Path, required=True)
    parser.add_argument("--coverage-gaps", type=Path, required=True)
    args = parser.parse_args()
    content = args.matrix.read_text(encoding="utf-8")
    errors = validate(content)
    errors.extend(
        validate_projection(
            content,
            args.source_inventory.read_text(encoding="utf-8"),
            args.coverage_gaps.read_text(encoding="utf-8"),
        )
    )
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
