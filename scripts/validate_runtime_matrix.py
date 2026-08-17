from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from scripts.runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from scripts.runtime_session_registry import canonical_scope, find_package_root, validate_topology
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_matrix.py
    from runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from runtime_session_registry import canonical_scope, find_package_root, validate_topology


REQUIRED_HEADERS = (
    "ID",
    "Источник требования",
    "Проверка",
    "Профили тест-дизайна",
    "Предусловие/исходное состояние",
    "Конкретные тестовые данные",
    "Ожидаемый результат",
    "Решение",
    "Готовность",
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
ALLOWED_TC_READINESS = {"ready", "needs-test-data", "candidate-ui-calibration"}
ALLOWED_GAP_CLASSES = {
    "неоднозначность-требования",
    "противоречие-источников",
    "нет-бизнес-результата",
    "нет-точки-наблюдения",
}
EMPTY_RE = re.compile(r"^(?:-|—|n/?a|не определен[оы]?|требу(?:ется|ются))\.?$", re.IGNORECASE)
SOURCE_ROW_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.-])SR-\d{2,}(?![A-Za-z0-9_.-])")
CONCRETE_DATA_RE = re.compile(r"`[^`\n]+`\s*=\s*`[^`\n]+`")
MISSING_ENVIRONMENT_DATA_RE = re.compile(
    r"(?:fixture|фикстур)\w*\s+(?:отсутств\w*|нет)|"
    r"(?:нет|отсутств\w*)\s+(?:готов\w*\s+)?(?:партн[её]р\w*|реквизит\w*|сущност\w*|запис\w*|рол\w*|уч[её]тн\w*)|"
    r"данн\w*\s+(?:будут|должны\s+быть)\s+подготовлен\w*",
    re.IGNORECASE,
)
MISSING_ENVIRONMENT_GAP_RE = re.compile(
    r"(?:нет|отсутств\w*)[^\n|]{0,80}(?:fixture|фикстур|готов\w*\s+)?"
    r"(?:партн[её]р\w*|реквизит\w*|сущност\w*|запис\w*|уч[её]тн\w*|логин\w*|url\b|credentials\b)|"
    r"(?:созда|подготов|предостав)[^\n|]{0,100}"
    r"(?:стендов\w*\s+)?(?:партн[её]р\w*|реквизит\w*|сущност\w*|запис\w*|уч[её]тн\w*)",
    re.IGNORECASE,
)


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
        readiness = row[index_by_name["Готовность"]]
        if decision == "TC" and readiness not in ALLOWED_TC_READINESS:
            errors.append(
                f"{row_id}: TC readiness must be ready, needs-test-data or candidate-ui-calibration"
            )
        if decision == "coverage-gap" and readiness != "blocked-observability":
            errors.append(f"{row_id}: coverage-gap readiness must be blocked-observability")
        if decision == "TC" and not row_id.startswith("M-"):
            errors.append(f"{row_id}: TC decision must use an M-* ID")
        if decision == "coverage-gap" and not row_id.startswith("GAP-"):
            errors.append(f"{row_id}: coverage-gap decision must use a GAP-* ID")
        data = row[index_by_name["Конкретные тестовые данные"]]
        if decision == "TC" and (not data or EMPTY_RE.fullmatch(data)):
            errors.append(f"{row_id}: TC decision requires concrete data or 'Не требуются.'")
        if decision == "TC" and data != "Не требуются." and not CONCRETE_DATA_RE.search(data):
            errors.append(f"{row_id}: TC matrix row requires a concrete `field` = `value` literal")
        if decision == "TC" and MISSING_ENVIRONMENT_DATA_RE.search(data):
            errors.append(
                f"{row_id}: missing environment binding requires needs-test-data, not absent test data"
            )
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

    gaps = find_markdown_table(
        gaps_content,
        ("ID", "Связанная обязанность", "Источник", "Класс", "Недостаток источника", "Что требуется для закрытия"),
    )
    if "GAP-" in gaps_content and (gaps is None or not gaps.rows):
        errors.append("coverage-gaps contains GAP IDs but has no typed source-level gap table")
    elif gaps is not None:
        for gap_row in gaps.rows:
            gap_id = gap_row[gaps.index("ID")]
            gap_class = gap_row[gaps.index("Класс")]
            if gap_class not in ALLOWED_GAP_CLASSES:
                errors.append(f"{gap_id}: unsupported coverage-gap class {gap_class!r}")
            gap_details = " | ".join(
                gap_row[gaps.index(name)] for name in ("Недостаток источника", "Что требуется для закрытия")
            )
            if MISSING_ENVIRONMENT_GAP_RE.search(gap_details):
                errors.append(
                    f"{gap_id}: missing environment data is execution readiness, not a coverage gap"
                )
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


def validate_layout(matrix_path: Path, package_root: Path) -> list[str]:
    errors: list[str] = []
    scope = matrix_path.parent.name
    expected = package_root / "work" / "practical" / scope / "test-design-matrix.md"
    if matrix_path.resolve() != expected.resolve():
        return [f"matrix must be stored at {expected}"]
    state_path = matrix_path.parent / "workflow-state.yaml"
    if not state_path.is_file():
        return ["writer workflow-state.yaml is missing next to the matrix"]
    state = state_path.read_text(encoding="utf-8")
    expected_relative = f"work/practical/{scope}/test-design-matrix.md"
    required_patterns = {
        "writer role": r"(?m)^role:\s*writer\s*$",
        "scope": rf"(?m)^scope:\s*[\"']?{re.escape(scope)}[\"']?\s*$",
        "completed matrix status": r"(?m)^matrix_status:\s*completed\s*$",
        "matrix path": rf"(?m)^test_design_matrix:\s*[\"']?{re.escape(expected_relative)}[\"']?\s*$",
    }
    for label, pattern in required_patterns.items():
        if not re.search(pattern, state):
            errors.append(f"writer workflow-state is missing {label}")
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
    package_root = find_package_root(args.matrix)
    if package_root is None:
        errors.append("cannot locate FT package root for session topology validation")
    else:
        errors.extend(validate_layout(args.matrix, package_root))
        errors.extend(validate_topology(package_root, "writer", canonical_scope(args.matrix.parent.name)))
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
