from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from scripts.runtime_traceability import extract_anchors, find_markdown_table
    from scripts.runtime_session_registry import canonical_scope, validate_topology
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_scope.py
    from runtime_traceability import extract_anchors, find_markdown_table
    from runtime_session_registry import canonical_scope, validate_topology


REQUIRED_FILES = (
    "source-row-inventory.md",
    "scope-brief.md",
    "coverage-gaps.md",
    "test-data-plan.md",
    "prompt.scope-to-writer.md",
    "workflow-state.yaml",
)
FORBIDDEN_PROCESS_WORDS = {
    "fixture": "тестовый набор данных",
    "gap": "пробел покрытия",
    "handoff": "передача этапа",
    "materialization": "подготовка данных",
    "matrix": "матрица",
    "oracle": "наблюдаемый результат",
    "provider": "источник данных или сервис",
    "scope": "область проверки",
    "setup": "подготовка исходного состояния",
    "snapshot": "сохранённый ответ",
    "trigger": "действие пользователя",
    "waiver": "разрешённое исключение",
    "writer": "этап написания тест-кейсов",
}
QUESTION_HEADING_RE = re.compile(r"^##\s+(CLR-[A-Za-z0-9.-]+)\b", re.MULTILINE)
ANY_QUESTION_HEADING_RE = re.compile(r"^##\s+([^\n]+)$", re.MULTILINE)
ALLOWED_QUESTION_STATUSES = {
    "ожидает-ответа",
    "частичный-ответ",
    "ответ-получен",
    "отменён",
}
QUESTION_ANSWER_PLACEHOLDER_RE = re.compile(r"^_?Введите\s+ответ\s+здесь\.?_?$", re.IGNORECASE)
UNCERTAIN_VERIFIABILITY_RE = re.compile(
    r"не\s+(?:указан\w*|задан\w*|определ[её]н\w*)|требуется\s+уточн|неизвест\w*",
    re.IGNORECASE,
)
CONSISTENCY_ASPECTS = (
    "Идентичность объекта",
    "Представления объекта",
    "Создание, редактирование и повторное открытие",
    "Роли и видимость",
    "Статусы и переходы",
    "Поля, справочники и внешние источники",
    "История изменений и аудит",
)
RESIDUAL_EXPLANATION = "**Почему существующий ответ не закрывает вопрос:**"
WORKING_ASSUMPTION_STATUS_RE = re.compile(
    r"^response_status:\s*(?:answered|resolved|approved)\s*$", re.IGNORECASE | re.MULTILINE
)
WORKING_ASSUMPTION_TYPE_RE = re.compile(
    r"^response_type:\s*working-assumption\s*$", re.IGNORECASE | re.MULTILINE
)
NON_BLOCKING_RE = re.compile(r"^blocking:\s*no\s*$", re.IGNORECASE | re.MULTILINE)
USER_RESPONSE_RE = re.compile(
    r"^user_response:\s*(?:>[-+]?\s*\n(?:[ \t]+\S.*\n?)+|(?!(?:none|null|-)\s*$)\S.+)$",
    re.IGNORECASE | re.MULTILINE,
)
TOKEN_STOPWORDS = {
    "данны",
    "должн",
    "использ",
    "какие",
    "какой",
    "котор",
    "провер",
    "реквиз",
    "систем",
    "требов",
}
OMIT_GAP_RE = re.compile(
    r"не\s+(?:создава(?:й|ть)|включа(?:й|ть))[^\n]{0,100}(?:matrix|матриц)[^\n]{0,80}(?:строк|обязан|gap|пробел)",
    re.IGNORECASE,
)
SOURCE_ROW_ID_RE = re.compile(r"^SR-\d{2,}$")
GAP_ID_RE = re.compile(r"^GAP-\d{2,}$")
SOURCE_ROW_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.-])SR-\d{2,}(?![A-Za-z0-9_.-])")
RESOLVED_EXCLUSION_RE = re.compile(
    r"не\s+образует\s+проверяемого\s+поведения|"
    r"не\s+является\s+проверяемой\s+обязанностью|"
    r"не\s+проверяется\s+по\s+утвержд[её]нному\s+ответу|"
    r"(?:операци[яи]|функциональност[ьи])\s+не\s+будет",
    re.IGNORECASE,
)
TABLE_ROW_REFERENCE_RE = re.compile(
    r"Таблица\s+(\d+)\s*,\s*строка\s+(?:«(.+)»|\"([^\"]+)\")(?:\s*,\s*примечание)?(?=\s*(?:;|$))",
    re.IGNORECASE,
)
TABLE_REFERENCE_RE = re.compile(r"\bТаблица\s+(\d+)\b", re.IGNORECASE)
ABBREVIATED_TABLE_REFERENCE_RE = re.compile(r"\bтабл\.\s*\d+\b", re.IGNORECASE)
TABLE_LABEL_RE = re.compile(r"^Таблица\s+(\d+)\b", re.IGNORECASE)
LOCAL_VISUAL_RE = re.compile(r"`([^`\n]+\.(?:png|jpe?g|webp|svg))`", re.IGNORECASE)
LOCAL_VISUAL_LABEL_RE = re.compile(r"\bРисунок\s+\d+\b", re.IGNORECASE)
LOCAL_VISUAL_EXTENSION_RE = re.compile(r"\.(?:png|jpe?g|webp|svg)\b", re.IGNORECASE)
INDEPENDENT_PROPERTY_PATTERNS = {
    "обязательность": re.compile(r"\bобязатель\w*", re.IGNORECASE),
    "редактируемость": re.compile(r"\b(?:не\s*)?редактир\w*|\bтолько\s+для\s+чтения\b", re.IGNORECASE),
    "представление": re.compile(r"\bинформационн\w*\s+(?:блок\w*|виджет\w*)", re.IGNORECASE),
    "ссылка или переход": re.compile(r"\bссылк\w*|\bпереход\w*", re.IGNORECASE),
}
QUESTION_EXTRA_BEHAVIOR_RE = re.compile(
    r"\bпомимо\b|\b(?:како(?:е|й|ва)|что)\s+ещ[её]\b|\bдополнительн\w*\s+(?:поведени\w*|результат\w*)",
    re.IGNORECASE,
)
DATA_PROVISION_QUESTION_RE = re.compile(
    r"(?:предостав|созда|подготов|выда)[^\n]{0,120}"
    r"(?:стенд|тестов\w*\s+сред|уч[её]тн\w*\s+запис|логин|url|credentials|fixture|фикстур|"
    r"готов\w*\s+(?:партн[её]р|реквизит|сущност|запис))",
    re.IGNORECASE,
)
MISSING_ENVIRONMENT_GAP_RE = re.compile(
    r"(?:нет|отсутств\w*)[^\n|]{0,80}(?:fixture|фикстур|готов\w*\s+)?"
    r"(?:партн[её]р\w*|реквизит\w*|сущност\w*|запис\w*|уч[её]тн\w*|логин\w*|url\b|credentials\b)|"
    r"(?:созда|подготов|предостав)[^\n|]{0,100}"
    r"(?:стендов\w*\s+)?(?:партн[её]р\w*|реквизит\w*|сущност\w*|запис\w*|уч[её]тн\w*)",
    re.IGNORECASE,
)
ALLOWED_GAP_CLASSES = {
    "неоднозначность-требования",
    "противоречие-источников",
    "нет-бизнес-результата",
    "нет-точки-наблюдения",
}
TEST_DATA_PLAN_HEADERS = (
    "Группа проверок",
    "Источник значений",
    "Данные или контракт получения",
    "Воспроизводимая подготовка",
    "Готовность",
)
ALLOWED_DATA_SOURCE_PREFIXES = (
    "первичный источник",
    "утверждённый ответ ба",
    "утвержденный ответ ба",
    "сохранённый ответ",
    "сохраненный ответ",
    "внешний сервис:",
    "проектный справочник",
    "официальный публичный источник",
    "синтетический генератор",
    "стендовая подготовка",
    "не требуются",
)
ALLOWED_DATA_READINESS = {"ready", "готово", "needs-test-data", "требуется получение данных"}


def runtime_root(package_root: Path) -> Path:
    for candidate in (package_root, *package_root.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise ValueError("runtime root was not found above package root")


def locator_sections(package_root: Path) -> dict[str, list[dict[str, str]]]:
    locator_states = sorted((package_root / "work" / "stage-handoffs").glob("00-*/workflow-state.yaml"))
    if not locator_states:
        return {}
    sections: dict[str, list[dict[str, str]]] = {}
    current_section: str | None = None
    current_entry: dict[str, str] | None = None
    for line in locator_states[-1].read_text(encoding="utf-8").splitlines():
        section_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*$", line)
        if section_match:
            current_section = section_match.group(1)
            current_entry = None
            continue
        path_match = re.match(r"\s*-\s+path:\s*(.+?)\s*$", line)
        if current_section and path_match:
            current_entry = {"path": path_match.group(1).strip().strip('"\'')}
            sections.setdefault(current_section, []).append(current_entry)
            continue
        attribute_match = re.match(r"\s+([A-Za-z_][A-Za-z0-9_-]*):\s*(.+?)\s*$", line)
        if current_entry is not None and attribute_match:
            current_entry[attribute_match.group(1)] = attribute_match.group(2).strip().strip('"\'')
    return sections


def resolve_declared_path(package_root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve()
    root = runtime_root(package_root)
    root_relative = (root / candidate).resolve()
    if root_relative.exists():
        return root_relative
    return (package_root / candidate).resolve()


def normalized_source_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split()).casefold()


def table_row_references(value: str) -> list[tuple[str, str]]:
    return [
        (match.group(1), match.group(2) or match.group(3))
        for match in TABLE_ROW_REFERENCE_RE.finditer(value)
    ]


def xhtml_table_rows(path: Path) -> dict[int, set[str]]:
    tree = ET.parse(path)
    current_table_number: int | None = None
    result: dict[int, set[str]] = {}
    for element in tree.iter():
        tag = element.tag.rsplit("}", 1)[-1].casefold()
        text = " ".join("".join(element.itertext()).replace("\u00a0", " ").split())
        if tag in {"h1", "p"}:
            label_match = TABLE_LABEL_RE.match(text)
            if label_match:
                current_table_number = int(label_match.group(1))
        if tag != "table" or current_table_number is None:
            continue
        first_cells: list[str] = []
        for row in (child for child in element.iter() if child.tag.rsplit("}", 1)[-1].casefold() == "tr"):
            cells = [
                child
                for child in list(row)
                if child.tag.rsplit("}", 1)[-1].casefold() in {"td", "th"}
            ]
            if cells:
                first_cells.append(" ".join("".join(cells[0].itertext()).replace("\u00a0", " ").split()))
        # The first row is the column header, not a requirement row.
        result[current_table_number] = {normalized_source_text(value) for value in first_cells[1:] if value}
        current_table_number = None
    return result


def machine_readable_primary(package_root: Path) -> Path | None:
    for entry in locator_sections(package_root).get("primary_sources", []):
        if "machine_readable_primary" in entry.get("role", "").casefold():
            return resolve_declared_path(package_root, entry["path"])
    return None


def yaml_list_values(content: str, key: str) -> list[str]:
    lines = content.splitlines()
    values: list[str] = []
    for index, line in enumerate(lines):
        match = re.match(rf"^(\s*){re.escape(key)}:\s*$", line)
        if not match:
            continue
        base_indent = len(match.group(1))
        for nested in lines[index + 1 :]:
            if nested.strip() and len(nested) - len(nested.lstrip()) <= base_indent:
                break
            item_match = re.match(r"\s*-\s+(.+?)\s*$", nested)
            if item_match:
                values.append(item_match.group(1).strip().strip('"\''))
        break
    return values


def validate_visual_reference(
    package_root: Path,
    value: str,
    registered_paths: set[str],
    origin: str,
) -> list[str]:
    if value.casefold().startswith(("http://", "https://")):
        return []
    resolved = resolve_declared_path(package_root, value)
    errors: list[str] = []
    if not resolved.is_file():
        return [f"{origin}: local visual path does not exist: {value}"]
    canonical = resolved.as_posix().casefold()
    if canonical not in registered_paths:
        errors.append(f"{origin}: local visual path is not registered by source locator: {value}")
    return errors


def approved_support_paths(package_root: Path) -> list[Path]:
    root = runtime_root(package_root)
    paths: list[Path] = []
    for entry in locator_sections(package_root).get("support_sources", []):
        if "approved_ba" not in entry.get("role", "").casefold():
            continue
        candidate = root / entry["path"]
        if not candidate.is_file():
            candidate = package_root / entry["path"]
        if candidate.is_file():
            paths.append(candidate)
    return paths


def question_blocks(content: str) -> list[tuple[str, str]]:
    matches = list(QUESTION_HEADING_RE.finditer(content))
    return [
        (
            match.group(1),
            content[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(content)],
        )
        for index, match in enumerate(matches)
    ]


def meaningful_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for word in re.findall(r"[А-Яа-яЁё]{5,}", value.casefold()):
        stem = word[:7]
        if not any(stem.startswith(stop) for stop in TOKEN_STOPWORDS):
            tokens.add(stem)
    return tokens


def question_text(block: str) -> str:
    match = re.search(r"\*\*Вопрос:\*\*\s*(.+?)(?=\n\n|\Z)", block, re.DOTALL)
    return match.group(1).strip() if match else block


def question_field(block: str, label: str) -> str:
    match = re.search(
        rf"^\*\*{re.escape(label)}:\*\*\s*(.*?)(?=\n\s*\n\*\*|\n##\s|\Z)",
        block,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def duplicates_fully_answered_question(current_question: str, support: str, code: str) -> bool:
    current_tokens = meaningful_tokens(current_question)
    for card in re.split(r"(?=^###\s+CLR-)", support, flags=re.MULTILINE):
        if not re.search(rf"\b{re.escape(code)}\b", card, re.IGNORECASE):
            continue
        if not re.search(r"response_status:\s*(?:answered|resolved|approved)\b", card, re.IGNORECASE):
            continue
        if not re.search(r"residual_missing:\s*none\b", card, re.IGNORECASE):
            continue
        historical_match = re.search(r"^question:\s*(.+?)\s*$", card, re.IGNORECASE | re.MULTILINE)
        if historical_match is None:
            historical_match = re.search(r"\*\*Вопрос:\*\*\s*(.+?)(?=\n\n|\Z)", card, re.DOTALL)
        if historical_match and len(current_tokens & meaningful_tokens(historical_match.group(1))) >= 2:
            return True
    return False


def support_cards(content: str) -> list[str]:
    cards = re.split(r"(?=^###\s+(?:U?CLR)-)", content, flags=re.MULTILINE)
    return [card for card in cards if re.match(r"^###\s+(?:U?CLR)-", card)]


def operational_working_assumption(card: str) -> bool:
    return all(
        pattern.search(card)
        for pattern in (
            WORKING_ASSUMPTION_STATUS_RE,
            WORKING_ASSUMPTION_TYPE_RE,
            NON_BLOCKING_RE,
            USER_RESPONSE_RE,
        )
    )


def operational_assumption_codes(card: str) -> set[str]:
    if not operational_working_assumption(card):
        return set()
    requirement_match = re.search(r"^requirement_codes:\s*(.+?)\s*$", card, re.IGNORECASE | re.MULTILINE)
    if requirement_match and requirement_match.group(1).strip() not in {"-", "none"}:
        return {
            anchor for anchor in extract_anchors(requirement_match.group(1)) if anchor.startswith("CODE:")
        }
    reference_match = re.search(r"^related_ft_reference:\s*(.+?)\s*$", card, re.IGNORECASE | re.MULTILINE)
    if reference_match is None:
        return set()
    primary_parts = [
        part
        for part in reference_match.group(1).split(";")
        if "cross-ref" not in part.casefold() and "cross ref" not in part.casefold()
    ]
    return {
        anchor
        for anchor in extract_anchors(";".join(primary_parts))
        if anchor.startswith("CODE:")
    }


def validate_test_data_plan(content: str) -> list[str]:
    if re.search(r"(?m)^Данные не требуются\.\s*$", content) and "|" not in content:
        return []
    table = find_markdown_table(content, TEST_DATA_PLAN_HEADERS)
    if table is None or not table.rows:
        return [
            "test-data-plan must contain the source-compatible data table from test-data-fixtures.md "
            "or the exact line 'Данные не требуются.'"
        ]
    errors: list[str] = []
    group_index = table.index("Группа проверок")
    source_index = table.index("Источник значений")
    data_index = table.index("Данные или контракт получения")
    readiness_index = table.index("Готовность")
    for row in table.rows:
        group = row[group_index].strip() or "<без группы>"
        source = row[source_index].strip()
        data = row[data_index].strip()
        readiness = row[readiness_index].strip().casefold()
        source_parts = [part.strip().strip("`").casefold() for part in source.split(";") if part.strip()]
        if not source_parts or any(
            not any(part.startswith(prefix) for prefix in ALLOWED_DATA_SOURCE_PREFIXES)
            for part in source_parts
        ):
            errors.append(f"test-data-plan {group}: unsupported or missing value source {source!r}")
        if readiness not in ALLOWED_DATA_READINESS:
            errors.append(f"test-data-plan {group}: unsupported readiness {row[readiness_index]!r}")
        external = any(part.startswith("внешний сервис:") for part in source_parts)
        saved = any(part.startswith(("сохранённый ответ", "сохраненный ответ")) for part in source_parts)
        if external and not saved:
            if not data.casefold().startswith("контракт получения:"):
                errors.append(
                    f"test-data-plan {group}: external value without a saved response must use 'Контракт получения:'"
                )
            if readiness != "требуется получение данных":
                errors.append(
                    f"test-data-plan {group}: external value without a saved response requires readiness "
                    "'требуется получение данных'"
                )
    return errors


def strip_allowed_technical_fragments(content: str) -> str:
    content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    content = re.sub(r"`[^`\n]*`", "", content)
    content = re.sub(r"https?://\S+", "", content)
    content = re.sub(r"\b(?:ATOM|BAQ|CLR|FIX|FX|GAP|OBL|SETUP|SRC|SR|TC|UCLR)-[A-Za-z0-9_.-]+\b", "", content)
    return content


def validate(package_root: Path, scope_dir: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_topology(package_root, "scope-analyzer", canonical_scope(scope_dir.name)))
    missing_files: list[str] = []
    for name in REQUIRED_FILES:
        if not (scope_dir / name).is_file():
            missing_files.append(f"missing scope artifact: {name}")
    errors.extend(missing_files)
    if missing_files:
        return errors

    clarification_register = package_root / "work" / "scope-clarification-requests.md"
    if not clarification_register.is_file():
        errors.append("missing package clarification register: work/scope-clarification-requests.md")
    if (scope_dir / "scope-clarification-requests.md").exists():
        errors.append("scope-local clarification file is forbidden; use work/scope-clarification-requests.md")

    inventory_content = (scope_dir / "source-row-inventory.md").read_text(encoding="utf-8")
    inventory = find_markdown_table(inventory_content, ("ID", "Источник", "Утверждение для покрытия"))
    row_references: list[tuple[str, int, str]] = []
    active_inventory_ids: set[str] = set()
    if inventory is None or not inventory.rows:
        errors.append("source-row-inventory has no required source rows table")
    else:
        inventory_id_index = inventory.index("ID")
        inventory_source_index = inventory.index("Источник")
        inventory_statement_index = inventory.index("Утверждение для покрытия")
        seen_inventory_ids: set[str] = set()
        for row in inventory.rows:
            inventory_id = row[inventory_id_index].strip()
            if not SOURCE_ROW_ID_RE.fullmatch(inventory_id):
                errors.append(f"source-row-inventory has invalid active row ID {inventory_id!r}")
            elif inventory_id in seen_inventory_ids:
                errors.append(f"source-row-inventory has duplicate active row ID {inventory_id}")
            seen_inventory_ids.add(inventory_id)
            active_inventory_ids.add(inventory_id)
            source_value = row[inventory_source_index]
            statement_value = row[inventory_statement_index]
            source_codes = {anchor for anchor in extract_anchors(source_value) if anchor.startswith("CODE:")}
            row_matches = table_row_references(source_value)
            for table_number, row_name in row_matches:
                row_references.append((inventory_id, int(table_number), row_name))
            if ABBREVIATED_TABLE_REFERENCE_RE.search(source_value):
                errors.append(f"{inventory_id}: use canonical 'Таблица N, строка «…»' instead of an abbreviated table reference")
            referenced_tables = {int(value) for value in TABLE_REFERENCE_RE.findall(source_value)}
            row_anchored_tables = {int(value) for value, _row_name in row_matches}
            for table_number in sorted(referenced_tables - row_anchored_tables):
                errors.append(
                    f"{inventory_id}: source cites table {table_number} without the exact first-column row name"
                )
            if len(source_codes) > 1:
                errors.append(f"{inventory_id}: active source row must contain one atomic requirement code")
            matched_properties = [
                name for name, pattern in INDEPENDENT_PROPERTY_PATTERNS.items() if pattern.search(statement_value)
            ]
            if len(matched_properties) > 1:
                errors.append(
                    f"{inventory_id}: active source row aggregates independent properties: "
                    + ", ".join(matched_properties)
                )
            if RESOLVED_EXCLUSION_RE.search(statement_value):
                errors.append(f"{inventory_id}: resolved or cancelled behavior belongs in applied exclusions, not active inventory")
    if row_references:
        xhtml_path = machine_readable_primary(package_root)
        if xhtml_path is None or not xhtml_path.is_file():
            errors.append("source-row-inventory uses table rows but locator has no existing normalized machine-readable primary")
        else:
            try:
                table_rows = xhtml_table_rows(xhtml_path)
            except (ET.ParseError, OSError) as exc:
                errors.append(f"normalized machine-readable primary cannot be parsed for table-row validation: {exc}")
            else:
                for inventory_id, table_number, row_name in row_references:
                    if table_number not in table_rows:
                        errors.append(f"{inventory_id}: source table {table_number} does not exist in normalized primary")
                    elif normalized_source_text(row_name) not in table_rows[table_number]:
                        errors.append(
                            f"{inventory_id}: source row {row_name!r} does not exist in table {table_number} of normalized primary"
                        )
    if not re.search(r"^##\s+Примен[её]нные исключения\s*$", inventory_content, re.MULTILINE):
        errors.append("source-row-inventory must contain an explicit 'Применённые исключения' section")

    verifiability = find_markdown_table(
        inventory_content,
        ("SR", "Объект или UI-уровень", "Актор и условие", "Действие или событие", "Наблюдаемый результат"),
    )
    contract_gap_ids: set[str] = set()
    if verifiability is None or not verifiability.rows:
        errors.append("source-row-inventory must contain a non-empty 'Контракт проверяемости' table")
    else:
        sr_index = verifiability.index("SR")
        contract_indexes = (
            verifiability.index("Объект или UI-уровень"),
            verifiability.index("Актор и условие"),
            verifiability.index("Действие или событие"),
            verifiability.index("Наблюдаемый результат"),
        )
        contract_ids: list[str] = []
        for row in verifiability.rows:
            source_id = row[sr_index].strip()
            contract_ids.append(source_id)
            if not SOURCE_ROW_ID_RE.fullmatch(source_id):
                errors.append(f"verifiability contract has invalid SR reference {source_id!r}")
            for index in contract_indexes:
                value = row[index].strip()
                if not value or value in {"-", "—"}:
                    errors.append(f"{source_id}: verifiability contract contains an empty semantic field")
                if UNCERTAIN_VERIFIABILITY_RE.search(value):
                    linked_gaps = set(re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", value))
                    contract_gap_ids.update(linked_gaps)
                    if not linked_gaps:
                        errors.append(
                            f"{source_id}: unknown verifiability element must link an explicit GAP-*"
                        )
        duplicates = sorted({source_id for source_id in contract_ids if contract_ids.count(source_id) > 1})
        if duplicates:
            errors.append("verifiability contract duplicates source obligations: " + ", ".join(duplicates))
        missing_contract = sorted(active_inventory_ids - set(contract_ids))
        extra_contract = sorted(set(contract_ids) - active_inventory_ids)
        if missing_contract:
            errors.append("verifiability contract misses active obligations: " + ", ".join(missing_contract))
        if extra_contract:
            errors.append("verifiability contract references non-active obligations: " + ", ".join(extra_contract))

    scope_brief_content = (scope_dir / "scope-brief.md").read_text(encoding="utf-8")
    workflow_content = (scope_dir / "workflow-state.yaml").read_text(encoding="utf-8")
    if not re.search(
        r"(?m)^clarification_register:\s*[\"']?work/scope-clarification-requests\.md[\"']?\s*$",
        workflow_content,
    ):
        errors.append("workflow-state must reference work/scope-clarification-requests.md as clarification_register")
    visual_check = find_markdown_table(
        scope_brief_content,
        ("UI-уровень", "Визуальный источник", "Результат сверки"),
    )
    if visual_check is None or not visual_check.rows:
        errors.append("scope-brief must contain a visual cross-check row for every included UI level")
    else:
        visual_index = visual_check.index("Визуальный источник")
        registered_visuals = {
            resolve_declared_path(package_root, entry["path"]).as_posix().casefold()
            for entry in locator_sections(package_root).get("visual_sources", [])
            if entry.get("path")
        }
        for row_number, row in enumerate(visual_check.rows, start=1):
            visual_source = row[visual_index]
            declared_paths = LOCAL_VISUAL_RE.findall(visual_source)
            visible_without_urls = re.sub(r"https?://\S+", "", visual_source)
            if not declared_paths and (
                LOCAL_VISUAL_LABEL_RE.search(visible_without_urls)
                or LOCAL_VISUAL_EXTENSION_RE.search(visible_without_urls)
            ):
                errors.append(
                    f"scope-brief visual cross-check row {row_number}: local visual must use an exact registered path in backticks"
                )
            for value in declared_paths:
                errors.extend(
                    validate_visual_reference(
                        package_root,
                        value,
                        registered_visuals,
                        f"scope-brief visual cross-check row {row_number}",
                    )
                )

        for value in yaml_list_values(workflow_content, "local_mockups"):
            errors.extend(
                validate_visual_reference(
                    package_root,
                    value,
                    registered_visuals,
                    "workflow-state local_mockups",
                )
            )

    consistency = find_markdown_table(
        scope_brief_content,
        ("Аспект", "Вывод анализа", "Связанные обязанности/пробелы"),
    )
    consistency_refs: set[str] = set()
    if consistency is None or not consistency.rows:
        errors.append("scope-brief must contain the complete consistency analysis table")
    else:
        aspect_index = consistency.index("Аспект")
        conclusion_index = consistency.index("Вывод анализа")
        refs_index = consistency.index("Связанные обязанности/пробелы")
        aspects = [row[aspect_index].strip() for row in consistency.rows]
        for required_aspect in CONSISTENCY_ASPECTS:
            count = sum(aspect.casefold() == required_aspect.casefold() for aspect in aspects)
            if count != 1:
                errors.append(
                    f"scope-brief consistency analysis must contain aspect {required_aspect!r} exactly once"
                )
        for row in consistency.rows:
            aspect = row[aspect_index].strip() or "<без аспекта>"
            conclusion = row[conclusion_index].strip()
            references = row[refs_index].strip()
            if not conclusion:
                errors.append(f"scope-brief consistency aspect {aspect!r} has no conclusion")
                continue
            if conclusion.casefold().startswith("не применимо"):
                if not re.match(r"(?i)^не применимо:\s*.{5,}$", conclusion):
                    errors.append(
                        f"scope-brief consistency aspect {aspect!r} needs a concrete reason after 'Не применимо:'"
                    )
                continue
            linked = set(SOURCE_ROW_TOKEN_RE.findall(references)) | set(
                re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", references)
            )
            consistency_refs.update(linked)
            if not linked:
                errors.append(f"scope-brief consistency aspect {aspect!r} must link SR-* or GAP-*")

    support_files = approved_support_paths(package_root)
    support_contents = [(path, path.read_text(encoding="utf-8")) for path in support_files]
    assumption_codes = {
        code
        for _path, support in support_contents
        for card in support_cards(support)
        for code in operational_assumption_codes(card)
    }

    gaps_content = (scope_dir / "coverage-gaps.md").read_text(encoding="utf-8")
    gaps = find_markdown_table(
        gaps_content,
        ("ID", "Связанная обязанность", "Источник", "Класс", "Недостаток источника", "Что требуется для закрытия"),
    )
    gap_ids: list[str] = []
    if "GAP-" in gaps_content:
        if gaps is None or not gaps.rows:
            errors.append("coverage-gaps contains GAP IDs but has no typed source-level gap table")
        else:
            gap_id_index = gaps.index("ID")
            linked_source_index = gaps.index("Связанная обязанность")
            gap_source_index = gaps.index("Источник")
            gap_class_index = gaps.index("Класс")
            gap_deficit_index = gaps.index("Недостаток источника")
            gap_resolution_index = gaps.index("Что требуется для закрытия")
            for row in gaps.rows:
                gap_id = row[gap_id_index].strip()
                gap_ids.append(gap_id)
                if not GAP_ID_RE.fullmatch(gap_id):
                    errors.append(f"coverage-gaps has invalid ID {gap_id!r}")
                linked_sources = SOURCE_ROW_TOKEN_RE.findall(row[linked_source_index])
                if len(linked_sources) != 1:
                    errors.append(f"{gap_id}: coverage gap must link exactly one atomic SR obligation")
                elif linked_sources[0] not in active_inventory_ids:
                    errors.append(f"{gap_id}: linked source obligation {linked_sources[0]} is absent from active inventory")
                gap_class = row[gap_class_index].strip()
                if gap_class not in ALLOWED_GAP_CLASSES:
                    errors.append(f"{gap_id}: unsupported coverage-gap class {gap_class!r}")
                gap_details = " | ".join((row[gap_deficit_index], row[gap_resolution_index]))
                if MISSING_ENVIRONMENT_GAP_RE.search(gap_details):
                    errors.append(
                        f"{gap_id}: missing environment data is execution readiness, not a coverage gap"
                    )
                source_codes = {
                    anchor for anchor in extract_anchors(row[gap_source_index]) if anchor.startswith("CODE:")
                }
                covered_assumptions = sorted(source_codes & assumption_codes)
                if covered_assumptions:
                    errors.append(
                        f"{gap_id}: non-blocking working assumption provides current behavior for "
                        + ", ".join(code.removeprefix("CODE:") for code in covered_assumptions)
                        + "; record future update instead of a coverage gap"
                    )

    known_gap_ids = set(gap_ids)
    unknown_contract_gaps = sorted(contract_gap_ids - known_gap_ids)
    if unknown_contract_gaps:
        errors.append("verifiability contract references unknown gaps: " + ", ".join(unknown_contract_gaps))
    unknown_consistency_refs = sorted(
        reference
        for reference in consistency_refs
        if reference not in active_inventory_ids and reference not in known_gap_ids
    )
    if unknown_consistency_refs:
        errors.append("scope-brief consistency analysis references unknown IDs: " + ", ".join(unknown_consistency_refs))

    prompt = (scope_dir / "prompt.scope-to-writer.md").read_text(encoding="utf-8")
    combined_scope_text = "\n".join(
        (scope_dir / name).read_text(encoding="utf-8") for name in REQUIRED_FILES if name.endswith(".md")
    )
    if OMIT_GAP_RE.search(combined_scope_text):
        errors.append("scope handoff tells writer to omit coverage-gap obligations from the matrix")
    if gap_ids:
        if "coverage-gap" not in prompt or "матриц" not in prompt.casefold():
            errors.append("writer prompt must preserve unresolved obligations in the matrix as coverage-gap")
        for gap_id in gap_ids:
            if gap_id not in prompt:
                errors.append(f"writer prompt does not carry {gap_id}")

    test_data_plan_content = (scope_dir / "test-data-plan.md").read_text(encoding="utf-8")
    errors.extend(validate_test_data_plan(test_data_plan_content))

    questions_content = clarification_register.read_text(encoding="utf-8") if clarification_register.is_file() else ""
    for heading in ANY_QUESTION_HEADING_RE.findall(questions_content):
        if heading != "Реестр вопросов к БА" and not heading.startswith("CLR-"):
            errors.append(f"clarification question heading must use CLR-* ID, got {heading!r}")
    question_cards = question_blocks(questions_content)
    question_ids = [question_id for question_id, _block in question_cards]
    duplicate_question_ids = sorted({question_id for question_id in question_ids if question_ids.count(question_id) > 1})
    if duplicate_question_ids:
        errors.append("clarification register contains duplicate IDs: " + ", ".join(duplicate_question_ids))
    for question_id, block in question_cards:
        question_scope = question_field(block, "Область проверки").strip("` ")
        status = question_field(block, "Статус").strip("` ").casefold()
        explicit_question = question_field(block, "Вопрос")
        requirement_basis = question_field(block, "Основание в ФТ")
        coverage_impact = question_field(block, "Влияние на покрытие")
        answer = question_field(block, "Ответ БА")
        if not question_scope:
            errors.append(f"{question_id}: clarification card has no scope")
        if status not in ALLOWED_QUESTION_STATUSES:
            errors.append(f"{question_id}: unsupported clarification status {status!r}")
        if not explicit_question:
            errors.append(f"{question_id}: clarification card has no explicit question")
        if not requirement_basis:
            errors.append(f"{question_id}: clarification card has no FT basis")
        if not coverage_impact:
            errors.append(f"{question_id}: clarification card has no coverage impact")
        if not answer:
            errors.append(f"{question_id}: clarification card has no editable 'Ответ БА' field")
        placeholder = bool(QUESTION_ANSWER_PLACEHOLDER_RE.fullmatch(answer.strip()))
        if status == "ожидает-ответа" and not placeholder:
            errors.append(f"{question_id}: pending clarification must keep the explicit editable answer placeholder")
        if status in {"ответ-получен", "отменён", "частичный-ответ"} and (not answer or placeholder):
            errors.append(f"{question_id}: status {status!r} requires a recorded answer or reason")
        if status == "частичный-ответ" and not question_field(block, "Осталось уточнить"):
            errors.append(f"{question_id}: partial answer requires 'Осталось уточнить'")
        current_question = explicit_question or question_text(block)
        if QUESTION_EXTRA_BEHAVIOR_RE.search(current_question):
            errors.append(
                f"{question_id}: question asks for behavior beyond the source-backed result instead of only missing facts"
            )
        if DATA_PROVISION_QUESTION_RE.search(current_question):
            errors.append(
                f"{question_id}: environment or test-data provisioning belongs in test-data-plan, not BA questions"
            )
        codes = sorted(anchor.removeprefix("CODE:") for anchor in extract_anchors(block) if anchor.startswith("CODE:"))
        if not codes:
            errors.append(f"{question_id}: question has no requirement code")
            continue
        provisional_codes = {f"CODE:{code}" for code in codes} & assumption_codes
        if provisional_codes and status not in {"ответ-получен", "отменён"}:
            errors.append(
                f"{question_id}: non-blocking working assumption already provides current behavior for "
                + ", ".join(sorted(code.removeprefix("CODE:") for code in provisional_codes))
                + "; preserve a future-update note instead of a BA question"
            )
        matching_support: list[Path] = []
        for path, support in support_contents:
            for code in codes:
                if re.search(rf"\b{re.escape(code)}\b", support, re.IGNORECASE):
                    matching_support.append(path)
                if status not in {"ответ-получен", "отменён"} and duplicates_fully_answered_question(
                    current_question, support, code
                ):
                    errors.append(f"{question_id}: duplicates a fully answered approved clarification for {code}")
        if matching_support and status not in {"ответ-получен", "отменён"} and RESIDUAL_EXPLANATION not in block:
            names = sorted({path.name for path in matching_support})
            errors.append(f"{question_id}: approved answer source mentions its requirement; residual explanation is required: {names}")

    for name in REQUIRED_FILES:
        if not name.endswith(".md"):
            continue
        visible = strip_allowed_technical_fragments((scope_dir / name).read_text(encoding="utf-8"))
        for word, replacement in FORBIDDEN_PROCESS_WORDS.items():
            if re.search(rf"\b{re.escape(word)}s?\b", visible, re.IGNORECASE):
                errors.append(f"{name}: use Russian wording instead of {word!r} ({replacement})")
    visible_questions = strip_allowed_technical_fragments(questions_content)
    for word, replacement in FORBIDDEN_PROCESS_WORDS.items():
        if re.search(rf"\b{re.escape(word)}s?\b", visible_questions, re.IGNORECASE):
            errors.append(
                "work/scope-clarification-requests.md: use Russian wording instead of "
                f"{word!r} ({replacement})"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a lean runtime scope handoff.")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("scope_dir", type=Path)
    args = parser.parse_args()
    errors = validate(args.package_root.resolve(), args.scope_dir.resolve())
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
