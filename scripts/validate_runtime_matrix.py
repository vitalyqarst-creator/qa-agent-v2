from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from scripts.runtime_cleanliness import validate_no_repository_temp
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from scripts.runtime_workflow_state import validate_state as validate_workflow_state
    from scripts.runtime_session_registry import canonical_scope, find_package_root, validate_topology
    from scripts.validate_runtime_scope import (
        TEST_DATA_PLAN_HEADERS,
        precise_source_anchors,
        validate_test_data_plan,
    )
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_matrix.py
    from runtime_cleanliness import validate_no_repository_temp
    from runtime_io import configure_utf8_stdio
    from runtime_traceability import anchor_label, extract_anchors, find_markdown_table
    from runtime_workflow_state import validate_state as validate_workflow_state
    from runtime_session_registry import canonical_scope, find_package_root, validate_topology
    from validate_runtime_scope import TEST_DATA_PLAN_HEADERS, precise_source_anchors, validate_test_data_plan


REQUIRED_HEADERS = (
    "ID",
    "Источник требования",
    "Проверка",
    "Профили тест-дизайна",
    "Элемент покрытия",
    "Предусловие/исходное состояние",
    "Тестовые данные и отношения",
    "Ожидаемый результат",
    "Решение",
    "Готовность",
)
ALLOWED_PROFILES = {
    "базовый",
    "обязательность",
    "зависимая-обязательность",
    "только-чтение",
    "автозаполнение",
    "допустимые-классы",
    "границы",
    "таблица-решений",
    "комбинаторный",
    "справочник",
    "уникальность-и-дубли",
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
RESOLVED_GAP_RE = re.compile(r"^\s*Закрыт(?:о|а|ы)?(?:\s+[^:|]{1,60})?\s*:", re.IGNORECASE)
EMPTY_RE = re.compile(r"^(?:-|—|n/?a|не определен[оы]?|требу(?:ется|ются))\.?$", re.IGNORECASE)
SOURCE_ROW_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.-])SR-\d{2,}(?![A-Za-z0-9_.-])")
MATRIX_ROW_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.-])M-\d{2,}(?![A-Za-z0-9_.-])")
CONCRETE_DATA_RE = re.compile(r"`[^`\n]+`\s*=\s*`[^`\n]+`")
DATA_ROLE_RE = re.compile(r"(?<![A-Za-z0-9_-])TD-[A-Z0-9]+(?:-[A-Z0-9]+)*(?![A-Za-z0-9_-])")
DATA_RELATION_RE = re.compile(r"(?<![A-Za-z0-9_-])REL-[A-Z0-9]+(?:-[A-Z0-9]+)*(?![A-Za-z0-9_-])")
DYNAMIC_OUTPUT_RE = re.compile(
    r"\b(?:системн\w*\s+(?:id|идентификатор\w*|номер\w*|timestamp|sequence)|"
    r"(?:id|идентификатор\w*|номер\w*|timestamp|sequence)\s+текущ\w*\s+прогон\w*|"
    r"выданн\w*\s+систем\w*\s+(?:id|идентификатор\w*|номер\w*))\b",
    re.IGNORECASE,
)
DYNAMIC_PROPERTY_RE = re.compile(r"\bпроверк\w*\s+свойств\w*\s*:", re.IGNORECASE)
DYNAMIC_BINDING_RE = re.compile(
    r"\b(?:runtime\s+binding|связыван\w*\s+(?:динамическ\w*\s+)?значен\w*)\b",
    re.IGNORECASE,
)
BINDING_CAPTURE_POINT_RE = re.compile(r"\bточк\w*\s+фиксац\w*\s*:", re.IGNORECASE)
BINDING_ASSERTION_POINT_RE = re.compile(r"\bточк\w*\s+сверк\w*\s*:", re.IGNORECASE)
HOVER_REVEALED_CONTROL_RE = re.compile(
    r"\bпри\s+наведени\w*[^|\n.]{0,180}?\bкнопк\w*\s+[«\"`]([^»\"`]+)[»\"`]",
    re.IGNORECASE,
)
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
ONLY_ROLE_VISIBILITY_RE = re.compile(
    r"(?:видим\w*\s+и\s+доступ\w*|доступ\w*\s+и\s+видим\w*)\s+только",
    re.IGNORECASE,
)
UNIQUENESS_REQUIREMENT_RE = re.compile(
    r"\bуникальн\w*|\bдубл\w*|\bповторн\w*\s+(?:запис\w*|сущност\w*|объект\w*)|"
    r"\bне\s+допуска\w*\s+(?:одинаков\w*|повторн\w*)",
    re.IGNORECASE,
)
NEGATIVE_ACTOR_RE = re.compile(
    r"(?:без\s+(?:роли|права)|не\s+име\w*\s+(?:роль|прав)|неадминистратор\w*)",
    re.IGNORECASE,
)
ABSENCE_ORACLE_RE = re.compile(
    r"(?:не\s+отображ\w*|не\s+видим\w*|отсутств\w*)",
    re.IGNORECASE,
)
FORMAL_COVERAGE_ITEM_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?:EP-[A-Za-z0-9_.-]+|BVA-[A-Za-z0-9_.-]+|"
    r"DT-R[A-Za-z0-9_.-]+|ST-T[A-Za-z0-9_.-]+|CT-C[A-Za-z0-9_.-]+)"
    r"(?![A-Za-z0-9_.-])"
)
PROFILE_COVERAGE_PREFIXES = {
    "допустимые-классы": "EP-",
    "границы": "BVA-",
    "таблица-решений": "DT-R",
    "переход-состояния": "ST-T",
    "комбинаторный": "CT-C",
}
COVERAGE_MODEL_HEADERS = (
    "Элемент покрытия",
    "Техника",
    "Параметр или условия",
    "Класс, точка, переход или комбинация",
    "Представитель",
    "Ожидаемый результат",
    "Основание",
)
COVERAGE_TECHNIQUES = {
    "EP-": "классы-эквивалентности",
    "BVA-": "граничные-значения",
    "DT-R": "таблица-решений",
    "ST-T": "переходы-состояний",
    "CT-C": "комбинаторное-покрытие",
}
BOUNDARY_FAMILY_HEADERS = (
    "Семейство границы",
    "Тип границы",
    "Точка ниже",
    "Точка на границе",
    "Точка выше",
    "Ожидаемая допустимость",
    "Основание",
)
BOUNDARY_TYPES = {
    "нижняя": "нет/да/да",
    "верхняя": "да/да/нет",
    "точная": "нет/да/нет",
}
UNIQUENESS_CONTROL_HEADERS = (
    "Бизнес-ключ и область",
    "Создание дубликата",
    "Самосовпадение при редактировании",
    "Конфликт при редактировании",
    "Тот же ключ, другое неключевое поле",
    "Основание или исключение",
)
MATRIX_ID_FULL_RE = re.compile(r"M-[A-Za-z0-9.-]+")
NOT_APPLICABLE_RE = re.compile(r"^Не применимо:\s+\S", re.IGNORECASE)
SAVE_ACTION_RE = re.compile(r"\bсохран", re.IGNORECASE)
NOT_SAVED_RE = re.compile(r"\bне\s+сохраня", re.IGNORECASE)


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


def coverage_prefix(item: str) -> str | None:
    for prefix in COVERAGE_TECHNIQUES:
        if item.startswith(prefix):
            return prefix
    return None


def validate_coverage_model(content: str, used_items: dict[str, str]) -> list[str]:
    errors: list[str] = []
    model = find_markdown_table(content, COVERAGE_MODEL_HEADERS)
    if model is None:
        return ["formal test-design profiles require a non-empty coverage model table"] if used_items else []
    if not model.rows:
        return ["coverage model table has no data rows"]

    item_index = model.index("Элемент покрытия")
    technique_index = model.index("Техника")
    model_items: set[str] = set()
    for row_number, row in enumerate(model.rows, start=1):
        item = row[item_index].strip()
        if not FORMAL_COVERAGE_ITEM_RE.fullmatch(item):
            errors.append(f"coverage model row {row_number}: invalid formal coverage item {item!r}")
            continue
        if item in model_items:
            errors.append(f"coverage model row {row_number}: duplicate coverage item {item}")
        model_items.add(item)
        prefix = coverage_prefix(item)
        expected_technique = COVERAGE_TECHNIQUES[prefix] if prefix else None
        if row[technique_index].strip() != expected_technique:
            errors.append(
                f"{item}: technique must be {expected_technique!r}, got {row[technique_index].strip()!r}"
            )
        for name in COVERAGE_MODEL_HEADERS[2:]:
            value = row[model.index(name)].strip()
            if not value or EMPTY_RE.fullmatch(value):
                errors.append(f"{item}: coverage model field {name} is empty")

    for item, row_id in sorted(used_items.items()):
        if item not in model_items:
            errors.append(f"{row_id}: formal coverage item {item} is absent from coverage model")
    for item in sorted(model_items - set(used_items)):
        errors.append(f"coverage model item {item} is not projected into the matrix")
    return errors


def validate_boundary_families(content: str, used_items: dict[str, str]) -> list[str]:
    errors: list[str] = []
    projected = {item for item in used_items if item.startswith("BVA-")}
    if not projected:
        return errors
    table = find_markdown_table(content, BOUNDARY_FAMILY_HEADERS)
    if table is None or not table.rows:
        return ["boundary profile requires a non-empty boundary family table"]

    seen_items: set[str] = set()
    seen_families: set[str] = set()
    for row_number, row in enumerate(table.rows, start=1):
        family = row[table.index("Семейство границы")].strip()
        boundary_type = row[table.index("Тип границы")].strip().casefold()
        expected = row[table.index("Ожидаемая допустимость")].strip().casefold().replace(" ", "")
        basis = row[table.index("Основание")].strip()
        if not family or EMPTY_RE.fullmatch(family):
            errors.append(f"boundary family row {row_number}: family is empty")
        elif family in seen_families:
            errors.append(f"boundary family row {row_number}: duplicate family {family!r}")
        else:
            seen_families.add(family)
        if boundary_type not in BOUNDARY_TYPES:
            errors.append(
                f"boundary family {family or row_number!r}: type must be нижняя, верхняя or точная"
            )
        elif expected != BOUNDARY_TYPES[boundary_type]:
            errors.append(
                f"boundary family {family!r}: expected admissibility must be "
                f"{BOUNDARY_TYPES[boundary_type]} for type {boundary_type}"
            )
        if not basis or EMPTY_RE.fullmatch(basis):
            errors.append(f"boundary family {family or row_number!r}: basis is empty")
        for column in ("Точка ниже", "Точка на границе", "Точка выше"):
            item = row[table.index(column)].strip()
            if not re.fullmatch(r"BVA-[A-Za-z0-9.-]+", item):
                errors.append(f"boundary family {family or row_number!r}: {column} must contain one BVA-* item")
                continue
            if item in seen_items:
                errors.append(f"boundary family {family or row_number!r}: duplicate boundary point {item}")
            seen_items.add(item)

    for item in sorted(projected - seen_items):
        errors.append(f"boundary coverage item {item} is absent from boundary family table")
    for item in sorted(seen_items - projected):
        errors.append(f"boundary family item {item} is not projected into the matrix")
    return errors


def validate_uniqueness_control(
    content: str,
    header: list[str],
    rows: list[list[str]],
) -> list[str]:
    errors: list[str] = []
    profile_index = header.index("Профили тест-дизайна")
    id_index = header.index("ID")
    uniqueness_ids = {
        row[id_index]
        for row in rows
        if "уникальность-и-дубли" in row[profile_index]
    }
    if not uniqueness_ids:
        return errors
    table = find_markdown_table(content, UNIQUENESS_CONTROL_HEADERS)
    if table is None or not table.rows:
        return ["uniqueness profile requires a non-empty uniqueness control table"]

    scenario_columns = UNIQUENESS_CONTROL_HEADERS[1:5]
    referenced: set[str] = set()
    seen_keys: set[str] = set()
    for row_number, row in enumerate(table.rows, start=1):
        key_scope = row[table.index("Бизнес-ключ и область")].strip()
        basis = row[table.index("Основание или исключение")].strip()
        if not key_scope or EMPTY_RE.fullmatch(key_scope):
            errors.append(f"uniqueness control row {row_number}: business key and scope are empty")
        elif key_scope in seen_keys:
            errors.append(f"uniqueness control row {row_number}: duplicate business key {key_scope!r}")
        else:
            seen_keys.add(key_scope)
        if not basis or EMPTY_RE.fullmatch(basis):
            errors.append(f"uniqueness control row {row_number}: basis is empty")
        executable_count = 0
        for column in scenario_columns:
            value = row[table.index(column)].strip()
            if NOT_APPLICABLE_RE.match(value):
                if not precise_source_anchors(value):
                    errors.append(
                        f"uniqueness control row {row_number}: {column} not-applicable reason "
                        "must contain its own precise source anchor"
                    )
                continue
            if not MATRIX_ID_FULL_RE.fullmatch(value):
                errors.append(
                    f"uniqueness control row {row_number}: {column} must contain one M-* item "
                    "or 'Не применимо: <source-backed reason>'"
                )
                continue
            executable_count += 1
            referenced.add(value)
            if value not in uniqueness_ids:
                errors.append(f"uniqueness control row {row_number}: {value} is not a uniqueness-profile matrix row")
        if executable_count == 0:
            errors.append(f"uniqueness control row {row_number}: at least one executable uniqueness scenario is required")

    for row_id in sorted(uniqueness_ids - referenced):
        errors.append(f"uniqueness-profile matrix row {row_id} is absent from uniqueness control table")
    return errors


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
    used_formal_items: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=1):
        row_id = row[index_by_name["ID"]]
        if not row_id or EMPTY_RE.fullmatch(row_id):
            errors.append(f"row {row_number}: ID is empty")
        elif row_id in seen_ids:
            errors.append(f"row {row_number}: duplicate ID {row_id}")
        else:
            seen_ids.add(row_id)

        for field in (
            "Источник требования",
            "Проверка",
            "Элемент покрытия",
            "Предусловие/исходное состояние",
            "Ожидаемый результат",
        ):
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

        if "зависимая-обязательность" in profiles:
            linked_sources = SOURCE_ROW_TOKEN_RE.findall(row[index_by_name["Источник требования"]])
            if len(set(linked_sources)) < 2:
                errors.append(f"{row_id}: dependent mandatory group must project at least two SR-* obligations")
            if not DATA_RELATION_RE.search(row[index_by_name["Тестовые данные и отношения"]]):
                errors.append(f"{row_id}: dependent mandatory group requires one REL-* dependency")
            if not SAVE_ACTION_RE.search(row[index_by_name["Проверка"]]):
                errors.append(f"{row_id}: dependent mandatory group requires an explicit save attempt")
            if not NOT_SAVED_RE.search(row[index_by_name["Ожидаемый результат"]]):
                errors.append(f"{row_id}: dependent mandatory group requires a common not-saved oracle")

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
        coverage_raw = row[index_by_name["Элемент покрытия"]]
        formal_items = FORMAL_COVERAGE_ITEM_RE.findall(coverage_raw)
        if decision == "coverage-gap" and row_id and row_id not in coverage_raw:
            errors.append(f"{row_id}: coverage-gap row must name its GAP ID as the coverage item")
        if decision == "TC":
            for profile, prefix in PROFILE_COVERAGE_PREFIXES.items():
                if profile in profiles and not any(item.startswith(prefix) for item in formal_items):
                    errors.append(f"{row_id}: profile {profile!r} requires a {prefix}* coverage item")
            for item in formal_items:
                previous_row = used_formal_items.get(item)
                if previous_row is not None:
                    errors.append(
                        f"{row_id}: formal coverage item {item} is already projected by {previous_row}"
                    )
                else:
                    used_formal_items[item] = row_id
        data = row[index_by_name["Тестовые данные и отношения"]]
        if decision == "TC" and (not data or EMPTY_RE.fullmatch(data)):
            errors.append(f"{row_id}: TC decision requires data roles, exact coverage literals or 'Не требуются.'")
        if (
            decision == "TC"
            and data != "Не требуются."
            and not CONCRETE_DATA_RE.search(data)
            and not DATA_ROLE_RE.search(data)
            and not DATA_RELATION_RE.search(data)
        ):
            errors.append(f"{row_id}: TC matrix row requires TD-*/REL-* or a concrete `field` = `value` literal")
        if decision == "TC" and MISSING_ENVIRONMENT_DATA_RE.search(data):
            errors.append(
                f"{row_id}: missing environment binding requires needs-test-data, not absent test data"
            )
        row_text = " | ".join(row)
        if decision == "TC" and DYNAMIC_OUTPUT_RE.search(row_text):
            has_property_contract = bool(DYNAMIC_PROPERTY_RE.search(row_text))
            has_binding_contract = bool(
                DYNAMIC_BINDING_RE.search(row_text)
                and BINDING_CAPTURE_POINT_RE.search(row_text)
                and BINDING_ASSERTION_POINT_RE.search(row_text)
            )
            if not (has_property_contract or has_binding_contract):
                errors.append(
                    f"{row_id}: system-generated output requires a property-check or runtime-binding "
                    "contract with separate capture and assertion points"
                )
    errors.extend(validate_coverage_model(content, used_formal_items))
    errors.extend(validate_boundary_families(content, used_formal_items))
    errors.extend(validate_uniqueness_control(content, header, rows))
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
    inventory_statements: dict[str, str] = {}
    inventory_sources: dict[str, str] = {}
    inventory_id_index = inventory.index("ID")
    inventory_source_index = inventory.index("Источник")
    inventory_statement_index = inventory.index("Утверждение для покрытия")
    for row in inventory.rows:
        inventory_id = row[inventory_id_index].strip()
        if not inventory_id:
            errors.append("source-row-inventory contains an empty ID")
            continue
        inventory_ids.add(inventory_id)
        inventory_sources[inventory_id] = row[inventory_source_index]
        inventory_statements[inventory_id] = row[inventory_statement_index]
        inventory_anchors.update(extract_anchors(row[inventory_source_index]))

    hover_revealed_controls = {
        match.casefold().strip()
        for statement in inventory_statements.values()
        for match in HOVER_REVEALED_CONTROL_RE.findall(statement)
    }

    matrix_source_index = matrix.index("Источник требования")
    matrix_check_index = matrix.index("Проверка")
    matrix_expected_index = matrix.index("Ожидаемый результат")
    matrix_decision_index = matrix.index("Решение")
    matrix_profile_index = matrix.index("Профили тест-дизайна")
    matrix_id_index = matrix.index("ID")
    matrix_anchors: set[str] = set()
    matrix_rows_by_id: dict[str, tuple[str, ...]] = {}
    matrix_rows_by_source_id: dict[str, list[tuple[str, ...]]] = {}
    for row in matrix.rows:
        matrix_source = row[matrix_source_index]
        matrix_anchors.update(extract_anchors(matrix_source))
        matrix_rows_by_id[row[matrix_id_index]] = row
        linked_inventory_ids = SOURCE_ROW_TOKEN_RE.findall(matrix_source)
        for linked_inventory_id in linked_inventory_ids:
            matrix_rows_by_source_id.setdefault(linked_inventory_id, []).append(row)
        check = row[matrix_check_index]
        for control in sorted(hover_revealed_controls) if row[matrix_decision_index] == "TC" else ():
            click = re.search(
                rf"\bнажа\w*[^|\n.]{{0,100}}[«\"`]{re.escape(control)}[»\"`]",
                check,
                re.IGNORECASE,
            )
            if click and not re.search(r"\bнаве\w*[^|\n.]{0,180}\bнажа\w*", check, re.IGNORECASE):
                errors.append(
                    f"{row[matrix_id_index]}: hover-revealed control {control!r} requires an explicit "
                    "hover immediately before the click in the matrix check"
                )
        source_requires_uniqueness = any(
            UNIQUENESS_REQUIREMENT_RE.search(
                f"{inventory_sources.get(inventory_id, '')} {inventory_statements.get(inventory_id, '')}"
            )
            for inventory_id in linked_inventory_ids
        )
        if (
            source_requires_uniqueness
            and row[matrix_decision_index] == "TC"
            and "уникальность-и-дубли" not in row[matrix_profile_index]
        ):
            errors.append(
                f"{row[matrix_id_index]}: source-backed uniqueness or duplicate rule requires "
                "the 'уникальность-и-дубли' profile"
            )
        source_requires_absence = any(
            ONLY_ROLE_VISIBILITY_RE.search(inventory_statements.get(inventory_id, ""))
            for inventory_id in linked_inventory_ids
        )
        if source_requires_absence and NEGATIVE_ACTOR_RE.search(row[matrix_check_index]):
            if not ABSENCE_ORACLE_RE.search(row[matrix_expected_index]):
                errors.append(
                    f"{row[matrix_id_index]}: source says the element is visible and available only to the role; "
                    "negative-role expected result must require element absence, not generic unavailability"
                )

    for inventory_id, statement in inventory_statements.items():
        if not ONLY_ROLE_VISIBILITY_RE.search(statement):
            continue
        projected_rows = matrix_rows_by_source_id.get(inventory_id, [])
        has_direct_negative = any(
            NEGATIVE_ACTOR_RE.search(
                f"{row[matrix_check_index]} {row[matrix.index('Предусловие/исходное состояние')]}"
            )
            and ABSENCE_ORACLE_RE.search(row[matrix_expected_index])
            for row in projected_rows
        )
        if has_direct_negative:
            continue
        referenced_rows = {
            reference
            for row in projected_rows
            for reference in MATRIX_ROW_TOKEN_RE.findall(" | ".join(row))
            if reference != row[matrix_id_index]
        }
        has_stronger_absence_link = any(
            (target := matrix_rows_by_id.get(reference)) is not None
            and NEGATIVE_ACTOR_RE.search(
                f"{target[matrix_check_index]} {target[matrix.index('Предусловие/исходное состояние')]}"
            )
            and ABSENCE_ORACLE_RE.search(target[matrix_expected_index])
            for reference in referenced_rows
        )
        if not has_stronger_absence_link:
            errors.append(
                f"{inventory_id}: role-only obligation requires an explicit negative branch or an M-* link "
                "to stronger source-backed absence coverage"
            )
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
            resolved = bool(RESOLVED_GAP_RE.search(gap_row[gaps.index("Что требуется для закрытия")]))
            if resolved:
                if gap_id in matrix_rows_by_id:
                    errors.append(f"matrix must not project resolved coverage gap {gap_id}")
                continue
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


def data_plan_contract(content: str) -> tuple[dict[str, set[str]], set[str], list[str]]:
    errors = validate_test_data_plan(content)
    if re.search(r"(?m)^Данные не требуются\.\s*$", content) and "|" not in content:
        return {}, set(), errors
    table = find_markdown_table(content, TEST_DATA_PLAN_HEADERS)
    if table is None or not table.rows:
        return {}, set(), errors
    roles_index = table.index("Роли данных")
    sources_index = table.index("Допустимый источник")
    role_sources: dict[str, set[str]] = {}
    for row in table.rows:
        sources = {part.strip().strip("`").casefold() for part in row[sources_index].split(";") if part.strip()}
        for role in DATA_ROLE_RE.findall(row[roles_index]):
            role_sources[role] = sources
    return role_sources, set(DATA_RELATION_RE.findall(content)), errors


def validate_layout(matrix_path: Path, package_root: Path) -> list[str]:
    errors: list[str] = validate_no_repository_temp(package_root)
    scope = matrix_path.parent.name
    expected = package_root / "work" / "practical" / scope / "test-design-matrix.md"
    if matrix_path.resolve() != expected.resolve():
        return [f"matrix must be stored at {expected}"]
    errors.extend(f"writer workflow-state: {error}" for error in validate_workflow_state(matrix_path))
    matrix_content = matrix_path.read_text(encoding="utf-8")
    matrix_roles = set(DATA_ROLE_RE.findall(matrix_content))
    matrix_relations = set(DATA_RELATION_RE.findall(matrix_content))
    baseline_plan = package_root / "work" / "stage-handoffs" / scope / "test-data-plan.md"
    matrix_plan = matrix_path.parent / "matrix-data-plan.md"
    if not baseline_plan.is_file():
        errors.append(f"analyzer baseline data plan is missing: {baseline_plan}")
        return errors
    if not matrix_plan.is_file():
        errors.append(f"writer-owned matrix data plan is missing: {matrix_plan}")
        return errors
    baseline_roles, baseline_relations, baseline_errors = data_plan_contract(
        baseline_plan.read_text(encoding="utf-8")
    )
    final_roles, final_relations, final_errors = data_plan_contract(matrix_plan.read_text(encoding="utf-8"))
    errors.extend(f"analyzer baseline: {error}" for error in baseline_errors)
    errors.extend(f"matrix data plan: {error}" for error in final_errors)
    for role in sorted(set(baseline_roles) - set(final_roles)):
        errors.append(f"matrix data plan omits analyzer baseline role {role}")
    for role in sorted(set(baseline_roles) & set(final_roles)):
        added_sources = final_roles[role] - baseline_roles[role]
        if added_sources:
            errors.append(f"matrix data plan weakens {role} with unapproved sources: {sorted(added_sources)}")
    for relation in sorted(baseline_relations - final_relations):
        errors.append(f"matrix data plan omits analyzer baseline relation {relation}")
    for role in sorted(matrix_roles - set(final_roles)):
        errors.append(f"matrix data role {role} is absent from matrix-data-plan")
    for relation in sorted(matrix_relations - final_relations):
        errors.append(f"matrix data relation {relation} is absent from matrix-data-plan")
    return errors


def main() -> int:
    configure_utf8_stdio()
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
