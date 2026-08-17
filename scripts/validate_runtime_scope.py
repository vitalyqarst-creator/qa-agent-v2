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
    "scope-clarification-requests.md",
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
RESIDUAL_EXPLANATION = "**Почему существующий ответ не закрывает вопрос:**"
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
    r"Таблица\s+(\d+)\s*,\s*строка\s+[«\"](.+?)[»\"](?:\s*,\s*примечание)?(?=\s*(?:;|$))",
    re.IGNORECASE,
)
TABLE_REFERENCE_RE = re.compile(r"\bТаблица\s+(\d+)\b", re.IGNORECASE)
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
            row_matches = TABLE_ROW_REFERENCE_RE.findall(source_value)
            for table_number, row_name in row_matches:
                row_references.append((inventory_id, int(table_number), row_name))
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
            errors.append("source-row-inventory uses table rows but locator has no existing machine-readable primary XHTML")
        else:
            try:
                table_rows = xhtml_table_rows(xhtml_path)
            except (ET.ParseError, OSError) as exc:
                errors.append(f"machine-readable primary XHTML cannot be parsed for table-row validation: {exc}")
            else:
                for inventory_id, table_number, row_name in row_references:
                    if table_number not in table_rows:
                        errors.append(f"{inventory_id}: source table {table_number} does not exist in primary XHTML")
                    elif normalized_source_text(row_name) not in table_rows[table_number]:
                        errors.append(
                            f"{inventory_id}: source row {row_name!r} does not exist in table {table_number} of primary XHTML"
                        )
    if not re.search(r"^##\s+Примен[её]нные исключения\s*$", inventory_content, re.MULTILINE):
        errors.append("source-row-inventory must contain an explicit 'Применённые исключения' section")

    scope_brief_content = (scope_dir / "scope-brief.md").read_text(encoding="utf-8")
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

        workflow_content = (scope_dir / "workflow-state.yaml").read_text(encoding="utf-8")
        for value in yaml_list_values(workflow_content, "local_mockups"):
            errors.extend(
                validate_visual_reference(
                    package_root,
                    value,
                    registered_visuals,
                    "workflow-state local_mockups",
                )
            )

    gaps_content = (scope_dir / "coverage-gaps.md").read_text(encoding="utf-8")
    gaps = find_markdown_table(gaps_content, ("ID", "Связанная обязанность", "Источник"))
    gap_ids: list[str] = []
    if "GAP-" in gaps_content:
        if gaps is None or not gaps.rows:
            errors.append("coverage-gaps contains GAP IDs but has no table with ID, Связанная обязанность and Источник")
        else:
            gap_id_index = gaps.index("ID")
            linked_source_index = gaps.index("Связанная обязанность")
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

    questions_content = (scope_dir / "scope-clarification-requests.md").read_text(encoding="utf-8")
    support_files = approved_support_paths(package_root)
    support_contents = [(path, path.read_text(encoding="utf-8")) for path in support_files]
    for question_id, block in question_blocks(questions_content):
        current_question = question_text(block)
        if QUESTION_EXTRA_BEHAVIOR_RE.search(current_question):
            errors.append(
                f"{question_id}: question asks for behavior beyond the source-backed result instead of only missing facts"
            )
        codes = sorted(anchor.removeprefix("CODE:") for anchor in extract_anchors(block) if anchor.startswith("CODE:"))
        if not codes:
            errors.append(f"{question_id}: question has no requirement code")
            continue
        matching_support: list[Path] = []
        for path, support in support_contents:
            for code in codes:
                if re.search(rf"\b{re.escape(code)}\b", support, re.IGNORECASE):
                    matching_support.append(path)
                if duplicates_fully_answered_question(current_question, support, code):
                    errors.append(f"{question_id}: duplicates a fully answered approved clarification for {code}")
        if matching_support and RESIDUAL_EXPLANATION not in block:
            names = sorted({path.name for path in matching_support})
            errors.append(f"{question_id}: approved answer source mentions its requirement; residual explanation is required: {names}")

    for name in REQUIRED_FILES:
        if not name.endswith(".md"):
            continue
        visible = strip_allowed_technical_fragments((scope_dir / name).read_text(encoding="utf-8"))
        for word, replacement in FORBIDDEN_PROCESS_WORDS.items():
            if re.search(rf"\b{re.escape(word)}s?\b", visible, re.IGNORECASE):
                errors.append(f"{name}: use Russian wording instead of {word!r} ({replacement})")
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
