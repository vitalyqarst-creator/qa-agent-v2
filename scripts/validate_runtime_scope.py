from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from scripts.runtime_traceability import extract_anchors, find_markdown_table
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_scope.py
    from runtime_traceability import extract_anchors, find_markdown_table


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
RESOLVED_EXCLUSION_RE = re.compile(
    r"не\s+образует\s+проверяемого\s+поведения|"
    r"не\s+является\s+проверяемой\s+обязанностью|"
    r"не\s+проверяется\s+по\s+утвержд[её]нному\s+ответу|"
    r"(?:операци[яи]|функциональност[ьи])\s+не\s+будет",
    re.IGNORECASE,
)


def runtime_root(package_root: Path) -> Path:
    for candidate in (package_root, *package_root.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise ValueError("runtime root was not found above package root")


def approved_support_paths(package_root: Path) -> list[Path]:
    root = runtime_root(package_root)
    locator_states = sorted((package_root / "work" / "stage-handoffs").glob("00-*/workflow-state.yaml"))
    if not locator_states:
        return []
    paths: list[Path] = []
    current_path: str | None = None
    for line in locator_states[-1].read_text(encoding="utf-8").splitlines():
        path_match = re.match(r"\s*-\s+path:\s*(.+?)\s*$", line)
        if path_match:
            current_path = path_match.group(1).strip().strip('"\'')
            continue
        role_match = re.match(r"\s+role:\s*(.+?)\s*$", line)
        if current_path and role_match:
            role = role_match.group(1).strip().strip('"\'').casefold()
            if "approved_ba" in role:
                candidate = root / current_path
                if not candidate.is_file():
                    candidate = package_root / current_path
                if candidate.is_file():
                    paths.append(candidate)
            current_path = None
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
    for name in REQUIRED_FILES:
        if not (scope_dir / name).is_file():
            errors.append(f"missing scope artifact: {name}")
    if errors:
        return errors

    inventory_content = (scope_dir / "source-row-inventory.md").read_text(encoding="utf-8")
    inventory = find_markdown_table(inventory_content, ("ID", "Источник", "Утверждение для покрытия"))
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
            source_codes = {
                anchor for anchor in extract_anchors(row[inventory_source_index]) if anchor.startswith("CODE:")
            }
            if len(source_codes) > 1:
                errors.append(f"{inventory_id}: active source row must contain one atomic requirement code")
            if RESOLVED_EXCLUSION_RE.search(row[inventory_statement_index]):
                errors.append(f"{inventory_id}: resolved or cancelled behavior belongs in applied exclusions, not active inventory")
    if not re.search(r"^##\s+Примен[её]нные исключения\s*$", inventory_content, re.MULTILINE):
        errors.append("source-row-inventory must contain an explicit 'Применённые исключения' section")

    scope_brief_content = (scope_dir / "scope-brief.md").read_text(encoding="utf-8")
    visual_check = find_markdown_table(
        scope_brief_content,
        ("UI-уровень", "Визуальный источник", "Результат сверки"),
    )
    if visual_check is None or not visual_check.rows:
        errors.append("scope-brief must contain a visual cross-check row for every included UI level")

    gaps_content = (scope_dir / "coverage-gaps.md").read_text(encoding="utf-8")
    gaps = find_markdown_table(gaps_content, ("ID", "Источник"))
    gap_ids: list[str] = []
    if "GAP-" in gaps_content:
        if gaps is None or not gaps.rows:
            errors.append("coverage-gaps contains GAP IDs but has no required table")
        else:
            gap_ids = [row[gaps.index("ID")].strip() for row in gaps.rows]

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
