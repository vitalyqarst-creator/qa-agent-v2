from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from scripts.runtime_cleanliness import validate_no_repository_temp
    from scripts.runtime_traceability import extract_anchors, find_markdown_table
    from scripts.runtime_session_registry import canonical_scope, validate_topology
except ModuleNotFoundError:  # Direct invocation: python scripts/validate_runtime_scope.py
    from runtime_cleanliness import validate_no_repository_temp
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
BOUNDARY_FRAGMENTS = (
    "Выбранный раздел",
    "Вводный текст родительского раздела",
    "Завершающий текст родительского раздела",
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
    r"(?:операци[яи]|функциональност[ьи])\s+не\s+будет|"
    r"\bне\s+реализу\w*",
    re.IGNORECASE,
)
RESOLVED_GAP_RE = re.compile(r"^\s*Закрыт(?:о|а|ы)?(?:\s+[^:|]{1,60})?\s*:", re.IGNORECASE)
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
MULTI_SURFACE_RE = re.compile(r"\s(?:и|или)\s|(?<=\w)\s*/\s*(?=\w)", re.IGNORECASE)
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
    "Границы и классы",
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
QUANTITATIVE_DATA_RE = re.compile(
    r"\b(?:размер|длин|количеств|диапазон|предел|максим|миним)\w*\b|"
    r"\bне\s+(?:более|менее)\b|"
    r"\b\d+(?:[.,]\d+)?\s*(?:байт|кб|мб|гб|символ\w*|знак\w*|цифр\w*|дн\w*|лет\w*|сек\w*|мин\w*|%)\b",
    re.IGNORECASE,
)
BOUNDARY_PLAN_RE = re.compile(
    r"шаг\s+представления\s*:.+?валидная\s+граница\s*:.+?ближайшее\s+недопустимое\s*:",
    re.IGNORECASE | re.DOTALL,
)
BOUNDARY_CLARIFICATION_RE = re.compile(r"требуется\s+уточнение\s*:\s*GAP-\d{2,}", re.IGNORECASE)
BOUNDARY_SOURCE_RE = re.compile(r"основание\s+границы\s*:\s*(.+?)\s*$", re.IGNORECASE | re.DOTALL)
VALID_BOUNDARY_VALUE_RE = re.compile(r"валидная\s+граница\s*:\s*(.+?)(?:;|$)", re.IGNORECASE | re.DOTALL)
DATE_LITERAL_RE = re.compile(r"(?<!\d)(?:0?[1-9]|[12]\d|3[01])[./-](?:0?[1-9]|1[0-2])[./-]\d{4}(?!\d)")
CONTEXT_ONLY_DEFINITION_RE = re.compile(r"\b(?:обозначает|бизнес-смысл|определение\s+термина)\b", re.IGNORECASE)
OBSERVABLE_BEHAVIOR_RE = re.compile(
    r"\b(?:отображ|показы|доступ|недоступ|сохраня|заполня|созда|измен|блокир|принима|отклон|разреш|запрещ)",
    re.IGNORECASE,
)
REQUIRED_UI_MECHANISM_RE = re.compile(
    r"(?:кнопк\w*[^|\n]{0,80}(?:недоступ|заблок)|сохранени\w*[^|\n]{0,80}(?:недоступ|заблок))",
    re.IGNORECASE,
)
VISUAL_INCOMPLETE_RE = re.compile(
    r"(?:макет|локальн\w*\s+материал\w*)[^|\n]{0,220}"
    r"(?:не\s+показыва|не\s+содерж|не\s+подтвержда|не\s+позволя)",
    re.IGNORECASE,
)
TABLE_COVERAGE_NUMBER_RE = re.compile(r"^(?:Таблица\s+)?(\d+)$", re.IGNORECASE)
OPAQUE_TABLE_HEADER_RE = re.compile(r"^[A-Za-zА-Яа-яЁё]{1,2}$")
UNAMBIGUOUS_SHORT_HEADERS = {"id"}
REACTIVE_RESULT_RE = re.compile(
    r"\b(?:подсказк|сообщен|ошиб|уведомл|предупрежд|диалог)\w*\b",
    re.IGNORECASE,
)
SOURCE_TRIGGER_RE = re.compile(
    r"\bпри\s+(?:ввод|выбор|нажат|сохран|попытк|поиск|открыт|закрыт|загруз|снятии\s+фокус)\w*|"
    r"\bпосле\s+(?:ввод|выбор|нажат|сохран|открыт|закрыт|загруз)\w*",
    re.IGNORECASE,
)
EXPLICIT_ACTION_TRIGGER_RE = re.compile(
    r"\b(?:нажима|выбира|сохраня|открыва|закрыва|заверша|снимает\s+фокус|переводит\s+фокус)\w*",
    re.IGNORECASE,
)
HIGH_CONFIDENCE_TEXT_ERRORS = (
    (re.compile(r"\bТабица\b", re.IGNORECASE), "опечатка 'Табица'"),
    (re.compile(r"\bотсутствуюют\b", re.IGNORECASE), "опечатка 'отсутствуюют'"),
    (re.compile(r"\bданны\b", re.IGNORECASE), "незавершённое слово 'данны'"),
    (
        re.compile(r"\bодин\s+вариант\s*:[^\n|]{0,160}\bлибо\b", re.IGNORECASE),
        "противоречивая фраза 'один вариант ... либо'",
    ),
)
def runtime_root(package_root: Path) -> Path:
    for candidate in (package_root, *package_root.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise ValueError("runtime root was not found above package root")


def public_contract(scope: str | None = None) -> dict[str, object]:
    """Return the small, stable authoring contract without exposing validator internals."""
    scope_value = canonical_scope(scope or "scope")
    scope_digits = "".join(re.findall(r"\d+", scope_value)) or "00"
    section_match = re.match(r"(\d+(?:\.\d+)*)", scope_value)
    section_id = section_match.group(1) if section_match else scope_digits
    return {
        "contract_version": 1,
        "scope": scope_value,
        "required_files": list(REQUIRED_FILES),
        "id_formats": {
            "source_row": {
                "pattern": r"SR-\d{2,}",
                "example": f"SR-{scope_digits}001",
            },
            "coverage_gap": {
                "pattern": r"GAP-\d{2,}",
                "example": f"GAP-{scope_digits}001",
            },
            "clarification": {
                "pattern": "CLR-<section>-<sequence>",
                "example": f"CLR-{section_id}-001",
            },
        },
        "required_tables": {
            "source_inventory": ["ID", "Источник", "Утверждение для покрытия"],
            "verifiability": [
                "SR",
                "Объект или UI-уровень",
                "Актор и условие",
                "Действие или событие",
                "Наблюдаемый результат",
            ],
            "boundaries": [
                "Фрагмент",
                "Структурный якорь",
                "Решение",
                "Связанные обязанности или область",
            ],
            "consistency": ["Аспект", "Вывод анализа", "Связанные обязанности/пробелы"],
            "coverage_gaps": [
                "ID",
                "Связанная обязанность",
                "Источник",
                "Класс",
                "Недостаток источника",
                "Что требуется для закрытия",
            ],
            "test_data": list(TEST_DATA_PLAN_HEADERS),
        },
        "conditional_controls": {
            "table_rows": "только если область использует таблицу ФТ",
            "opaque_headers": "только для используемых коротких заголовков без явной семантики",
            "visual_crosscheck": "только для включённых UI-уровней",
            "figma": "только если релевантного локального визуального материала недостаточно",
            "second_pass": "только при сигнале сложности из ft-scope-analyzer",
        },
        "human_language": "русский",
        "russian_process_terms": FORBIDDEN_PROCESS_WORDS,
    }


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
        item_match = re.match(r"\s*-\s+(path|url):\s*(.+?)\s*$", line)
        if current_section and item_match:
            current_entry = {item_match.group(1): item_match.group(2).strip().strip('"\'')}
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


def strip_optional_outer_quotes(value: str) -> str:
    result = value.strip()
    quote_pairs = {"«": "»", '"': '"'}
    closing = quote_pairs.get(result[:1])
    if closing and result.endswith(closing) and len(result) >= 2:
        return result[1:-1].strip()
    return result


def canonical_source_reference(value: str) -> str:
    return normalized_source_text(value.strip().strip("` ").rstrip(".;"))


def xhtml_cell_text(cell: ET.Element) -> str:
    block_tags = {"address", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "p", "table"}
    direct_blocks = [
        child for child in list(cell) if child.tag.rsplit("}", 1)[-1].casefold() in block_tags
    ]
    if direct_blocks:
        parts: list[str] = []
        if cell.text and cell.text.strip():
            parts.append(cell.text)
        for child in direct_blocks:
            parts.append("".join(child.itertext()))
            if child.tail and child.tail.strip():
                parts.append(child.tail)
        return " ".join(" ".join(parts).replace("\u00a0", " ").split())
    return " ".join("".join(cell.itertext()).replace("\u00a0", " ").split())


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
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}:
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
                first_cells.append(xhtml_cell_text(cells[0]))
        # The first row is the column header, not a requirement row.
        result[current_table_number] = {normalized_source_text(value) for value in first_cells[1:] if value}
        current_table_number = None
    return result


def xhtml_table_headers(path: Path) -> dict[int, tuple[str, ...]]:
    tree = ET.parse(path)
    current_table_number: int | None = None
    result: dict[int, tuple[str, ...]] = {}
    for element in tree.iter():
        tag = element.tag.rsplit("}", 1)[-1].casefold()
        text = " ".join("".join(element.itertext()).replace("\u00a0", " ").split())
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}:
            label_match = TABLE_LABEL_RE.match(text)
            if label_match:
                current_table_number = int(label_match.group(1))
        if tag != "table" or current_table_number is None:
            continue
        first_row = next(
            (child for child in element.iter() if child.tag.rsplit("}", 1)[-1].casefold() == "tr"),
            None,
        )
        if first_row is not None:
            headers = tuple(
                xhtml_cell_text(child)
                for child in list(first_row)
                if child.tag.rsplit("}", 1)[-1].casefold() in {"td", "th"}
            )
            result[current_table_number] = headers
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


def precise_source_anchors(value: str) -> set[str]:
    anchors = extract_anchors(value)
    codes = {anchor for anchor in anchors if anchor.startswith("CODE:")}
    table_rows = {anchor for anchor in anchors if anchor.startswith("TABLE:") and anchor.count(":") == 2}
    sections = {anchor for anchor in anchors if anchor.startswith("SECTION:")}
    quoted_text = {anchor for anchor in anchors if anchor.startswith("TEXT:")}
    if codes or table_rows or (sections and quoted_text):
        return codes | table_rows | sections | quoted_text
    return set()


def single_observation_surface(value: str) -> bool:
    without_labels = re.sub(r"`[^`\n]*`|«[^»\n]*»|\"[^\"\n]*\"", "", value)
    return not MULTI_SURFACE_RE.search(without_labels)


def duplicates_fully_answered_question(current_question: str, support: str, anchors: set[str]) -> bool:
    current_tokens = meaningful_tokens(current_question)
    for card in re.split(r"(?=^###\s+CLR-)", support, flags=re.MULTILINE):
        if not anchors.intersection(precise_source_anchors(card)):
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


def operational_assumption_anchors(card: str) -> set[str]:
    if not operational_working_assumption(card):
        return set()
    requirement_match = re.search(r"^requirement_codes:\s*(.+?)\s*$", card, re.IGNORECASE | re.MULTILINE)
    if requirement_match and requirement_match.group(1).strip() not in {"-", "none"}:
        return precise_source_anchors(requirement_match.group(1))
    reference_match = re.search(r"^related_ft_reference:\s*(.+?)\s*$", card, re.IGNORECASE | re.MULTILINE)
    if reference_match is None:
        return set()
    primary_parts = [
        part
        for part in reference_match.group(1).split(";")
        if "cross-ref" not in part.casefold() and "cross ref" not in part.casefold()
    ]
    return precise_source_anchors(";".join(primary_parts))


def validate_test_data_plan(content: str, source_evidence: str = "") -> list[str]:
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
    preparation_index = table.index("Воспроизводимая подготовка")
    boundaries_index = table.index("Границы и классы")
    readiness_index = table.index("Готовность")
    for row in table.rows:
        group = row[group_index].strip() or "<без группы>"
        source = row[source_index].strip()
        data = row[data_index].strip()
        preparation = row[preparation_index].strip()
        boundaries = row[boundaries_index].strip()
        readiness = row[readiness_index].strip().casefold()
        source_parts = [part.strip().strip("`").casefold() for part in source.split(";") if part.strip()]
        if not source_parts or any(
            not any(part.startswith(prefix) for prefix in ALLOWED_DATA_SOURCE_PREFIXES)
            for part in source_parts
        ):
            errors.append(f"test-data-plan {group}: unsupported or missing value source {source!r}")
        if readiness not in ALLOWED_DATA_READINESS:
            errors.append(f"test-data-plan {group}: unsupported readiness {row[readiness_index]!r}")
        if not boundaries:
            errors.append(f"test-data-plan {group}: 'Границы и классы' must not be empty")
        quantitative = bool(QUANTITATIVE_DATA_RE.search(" | ".join((group, data, preparation))))
        boundary_plan = BOUNDARY_PLAN_RE.search(boundaries)
        if quantitative and not (boundary_plan or BOUNDARY_CLARIFICATION_RE.search(boundaries)):
            errors.append(
                f"test-data-plan {group}: quantitative requirement needs 'Шаг представления: ...; "
                "валидная граница: ...; ближайшее недопустимое: ...; Основание границы: ...' "
                "or 'Требуется уточнение: GAP-*'"
            )
        if quantitative and boundary_plan:
            source_match = BOUNDARY_SOURCE_RE.search(boundaries)
            source_basis = source_match.group(1).strip() if source_match else ""
            if not source_basis or not precise_source_anchors(source_basis):
                errors.append(
                    f"test-data-plan {group}: exact boundary needs 'Основание границы:' with a precise source anchor"
                )
            if source_evidence:
                valid_boundary = VALID_BOUNDARY_VALUE_RE.search(boundaries)
                if valid_boundary:
                    for literal in DATE_LITERAL_RE.findall(valid_boundary.group(1)):
                        if literal not in source_evidence:
                            errors.append(
                                f"test-data-plan {group}: date boundary {literal!r} is absent from primary/approved sources"
                            )
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
    errors.extend(validate_no_repository_temp(package_root))
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
    normalized_table_rows: dict[int, set[str]] = {}
    normalized_table_headers: dict[int, tuple[str, ...]] = {}
    active_inventory_ids: set[str] = set()
    inventory_statements: dict[str, str] = {}
    inventory_sources: dict[str, str] = {}
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
            inventory_statements[inventory_id] = statement_value
            inventory_sources[inventory_id] = source_value
            source_codes = {anchor for anchor in extract_anchors(source_value) if anchor.startswith("CODE:")}
            if not precise_source_anchors(source_value):
                errors.append(
                    f"{inventory_id}: source needs an exact requirement code or an uncoded structural anchor "
                    "(exact table row, or section plus quoted paragraph/list text)"
                )
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
            if CONTEXT_ONLY_DEFINITION_RE.search(statement_value) and not OBSERVABLE_BEHAVIOR_RE.search(statement_value):
                errors.append(
                    f"{inventory_id}: definition or business context without observable system behavior is not an active obligation"
                )
    xhtml_path = machine_readable_primary(package_root)
    machine_source_text = ""
    if xhtml_path is not None and xhtml_path.is_file():
        machine_source_text = xhtml_path.read_text(encoding="utf-8")
    if row_references:
        if xhtml_path is None or not xhtml_path.is_file():
            errors.append("source-row-inventory uses table rows but locator has no existing normalized machine-readable primary")
        else:
            try:
                table_rows = xhtml_table_rows(xhtml_path)
                normalized_table_rows = table_rows
                normalized_table_headers = xhtml_table_headers(xhtml_path)
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
            observation_surface = row[contract_indexes[0]].strip()
            if observation_surface and not single_observation_surface(observation_surface):
                errors.append(
                    f"{source_id}: verifiability contract must name one object or UI level; split mixed surfaces"
                )
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
            statement = inventory_statements.get(source_id, "")
            action = row[contract_indexes[2]].strip()
            observed_result = row[contract_indexes[3]].strip()
            if (
                re.search(r"\bобязатель\w*", statement, re.IGNORECASE)
                and REQUIRED_UI_MECHANISM_RE.search(observed_result)
                and not REQUIRED_UI_MECHANISM_RE.search(statement)
            ):
                errors.append(
                    f"{source_id}: requiredness alone supports 'object is not saved', not an exact disabled UI mechanism"
                )
            linked_contract_gaps = set(
                re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", " | ".join(row))
            )
            if (
                REACTIVE_RESULT_RE.search(observed_result)
                and not linked_contract_gaps
                and not SOURCE_TRIGGER_RE.search(statement)
                and not EXPLICIT_ACTION_TRIGGER_RE.search(action)
            ):
                errors.append(
                    f"{source_id}: message, hint or notification needs a source-backed trigger/action or an explicit GAP-*"
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
    boundary_refs: set[str] = set()
    boundary_code_anchors: set[str] = set()
    selected_section_refs: set[str] = set()
    distributed_parent = False
    parent_decisions: list[str] = []
    boundary_control = find_markdown_table(
        scope_brief_content,
        ("Фрагмент", "Структурный якорь", "Решение", "Связанные обязанности или область"),
    )
    if boundary_control is None or not boundary_control.rows:
        errors.append("scope-brief must contain the source boundary control table")
    else:
        fragment_index = boundary_control.index("Фрагмент")
        anchor_index = boundary_control.index("Структурный якорь")
        decision_index = boundary_control.index("Решение")
        related_index = boundary_control.index("Связанные обязанности или область")
        fragments = [row[fragment_index].strip() for row in boundary_control.rows]
        for required_fragment in BOUNDARY_FRAGMENTS:
            count = sum(fragment.casefold() == required_fragment.casefold() for fragment in fragments)
            if count != 1:
                errors.append(
                    f"scope-brief source boundary control must contain fragment {required_fragment!r} exactly once"
                )
        for row in boundary_control.rows:
            fragment = row[fragment_index].strip() or "<без фрагмента>"
            anchor = row[anchor_index].strip()
            boundary_code_anchors.update(
                item for item in extract_anchors(anchor) if item.startswith("CODE:")
            )
            decision = row[decision_index].strip()
            related = row[related_index].strip()
            if fragment.casefold() == "выбранный раздел" and decision.casefold() != "включён":
                errors.append("scope-brief selected section must use decision 'Включён'")
            elif fragment.casefold() != "выбранный раздел":
                parent_decisions.append(decision.casefold())
            if not anchor or anchor in {"-", "—"}:
                errors.append(f"scope-brief source boundary fragment {fragment!r} has no structural anchor")
            if decision.casefold() == "включён":
                if fragment.casefold() != "выбранный раздел":
                    errors.append(
                        f"scope-brief parent fragment {fragment!r} must distribute obligations by target scope "
                        "instead of including the whole fragment"
                    )
                linked = set(SOURCE_ROW_TOKEN_RE.findall(related)) | set(
                    re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", related)
                )
                boundary_refs.update(linked)
                if fragment.casefold() == "выбранный раздел":
                    selected_section_refs.update(
                        item for item in linked if SOURCE_ROW_ID_RE.fullmatch(item)
                    )
                if not linked:
                    errors.append(
                        f"scope-brief source boundary fragment {fragment!r} is included but has no SR-* or GAP-* links"
                    )
            elif decision.casefold() == "распределён":
                if fragment.casefold() == "выбранный раздел":
                    errors.append("scope-brief selected section cannot use decision 'Распределён'")
                distributed_parent = True
            elif decision.casefold().startswith("ранее покрыт:"):
                previous_scope = decision.split(":", 1)[1].strip().strip("` ")
                previous_matches = [
                    candidate
                    for candidate in (package_root / "work" / "stage-handoffs").glob("*")
                    if candidate.is_dir()
                    and candidate.resolve() != scope_dir.resolve()
                    and canonical_scope(candidate.name) == canonical_scope(previous_scope)
                    and (candidate / "source-row-inventory.md").is_file()
                ]
                if not previous_scope or not previous_matches:
                    errors.append(
                        f"scope-brief source boundary fragment {fragment!r} references no completed earlier scope"
                    )
            elif decision.casefold().startswith("не применимо:"):
                reason = decision.split(":", 1)[1].strip()
                if len(reason) < 5:
                    errors.append(
                        f"scope-brief source boundary fragment {fragment!r} needs a concrete non-applicability reason"
                    )
            else:
                errors.append(
                    f"scope-brief source boundary fragment {fragment!r} has unsupported decision {decision!r}"
                )

        if active_inventory_ids:
            ordered_source_rows = sorted(
                active_inventory_ids,
                key=lambda value: int(value.removeprefix("SR-")),
            )
            required_edges = {ordered_source_rows[0], ordered_source_rows[-1]}
            missing_edges = sorted(required_edges - selected_section_refs)
            if missing_edges:
                errors.append(
                    "scope-brief selected section must include the first and final active source-row IDs: "
                    + ", ".join(missing_edges)
                )

        inventory_code_anchors = {
            anchor
            for source in inventory_sources.values()
            for anchor in extract_anchors(source)
            if anchor.startswith("CODE:")
        }
        declared_inventory_codes = boundary_code_anchors & inventory_code_anchors
        if declared_inventory_codes:
            missing_codes = sorted(inventory_code_anchors - boundary_code_anchors)
            if missing_codes:
                errors.append(
                    "scope-brief requirement-code boundary is partial; omitted active codes: "
                    + ", ".join(missing_codes)
                )

    ownership = find_markdown_table(
        scope_brief_content,
        ("Источник", "Родительская обязанность", "Целевая область", "Связанные обязанности или решение"),
    )
    ownership_refs: set[str] = set()
    if distributed_parent:
        if ownership is None or not ownership.rows:
            errors.append("scope-brief distributed parent text requires the parent requirement ownership table")
        else:
            source_index = ownership.index("Источник")
            duty_index = ownership.index("Родительская обязанность")
            target_index = ownership.index("Целевая область")
            resolution_index = ownership.index("Связанные обязанности или решение")
            current_scope = canonical_scope(scope_dir.name)
            for row_number, row in enumerate(ownership.rows, start=1):
                source = row[source_index].strip()
                duty = row[duty_index].strip()
                target = row[target_index].strip().strip("` ")
                resolution = row[resolution_index].strip()
                if not precise_source_anchors(source):
                    errors.append(f"parent ownership row {row_number}: source lacks an exact requirement anchor")
                if not duty or duty in {"-", "—"}:
                    errors.append(f"parent ownership row {row_number}: atomic parent obligation is missing")
                if not target or re.search(r"\b(?:будущ|друг\w*\s+scope|не\s+определ)\w*", target, re.IGNORECASE):
                    errors.append(f"parent ownership row {row_number}: target scope must be explicit")
                linked = set(SOURCE_ROW_TOKEN_RE.findall(resolution)) | set(
                    re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", resolution)
                )
                if canonical_scope(target) == current_scope:
                    ownership_refs.update(linked)
                    if not linked:
                        errors.append(
                            f"parent ownership row {row_number}: current-scope obligation must link SR-* or GAP-*"
                        )
                elif linked:
                    errors.append(
                        f"parent ownership row {row_number}: another scope must not link current inventory IDs"
                    )
    elif ownership is not None and ownership.rows:
        errors.append("scope-brief has parent ownership rows but boundary control does not use 'Распределён'")
    elif (
        parent_decisions
        and all(decision.startswith("не применимо:") for decision in parent_decisions)
        and "Нормативные родительские обязанности отсутствуют." not in scope_brief_content
    ):
        errors.append(
            "scope-brief must state 'Нормативные родительские обязанности отсутствуют.' "
            "when parent fragments are not applicable"
        )

    referenced_table_numbers = {table_number for _inventory_id, table_number, _row_name in row_references}
    table_coverage_refs: set[str] = set()
    header_semantics_gap_ids: set[str] = set()
    table_coverage = find_markdown_table(
        scope_brief_content,
        ("Таблица", "Строка", "Решение", "Связанные обязанности/пробелы"),
    )
    if referenced_table_numbers:
        if table_coverage is None or not table_coverage.rows:
            errors.append("scope-brief must contain complete table-row coverage for every referenced source table")
        else:
            table_index = table_coverage.index("Таблица")
            row_index = table_coverage.index("Строка")
            decision_index = table_coverage.index("Решение")
            refs_index = table_coverage.index("Связанные обязанности/пробелы")
            declared: dict[int, list[str]] = {}
            for row_number, row in enumerate(table_coverage.rows, start=1):
                table_match = TABLE_COVERAGE_NUMBER_RE.fullmatch(row[table_index].strip())
                if table_match is None:
                    errors.append(f"table-row coverage row {row_number}: invalid table label {row[table_index]!r}")
                    continue
                table_number = int(table_match.group(1))
                source_row = strip_optional_outer_quotes(row[row_index])
                normalized_row = normalized_source_text(source_row)
                declared.setdefault(table_number, []).append(normalized_row)
                if table_number not in normalized_table_rows:
                    errors.append(f"table-row coverage row {row_number}: table {table_number} is absent from XHTML")
                elif normalized_row not in normalized_table_rows[table_number]:
                    errors.append(
                        f"table-row coverage row {row_number}: row {source_row!r} is absent from table {table_number}"
                    )
                decision = row[decision_index].strip()
                linked = set(SOURCE_ROW_TOKEN_RE.findall(row[refs_index])) | set(
                    re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", row[refs_index])
                )
                if decision.casefold() == "включена":
                    table_coverage_refs.update(linked)
                    if not linked:
                        errors.append(f"table-row coverage row {row_number}: included row must link SR-* or GAP-*")
                elif decision.casefold().startswith("передана:"):
                    if len(decision.split(":", 1)[1].strip()) < 2:
                        errors.append(f"table-row coverage row {row_number}: transferred row needs a target scope")
                elif decision.casefold().startswith("не применимо:"):
                    if len(decision.split(":", 1)[1].strip()) < 5:
                        errors.append(f"table-row coverage row {row_number}: non-applicability needs a reason")
                elif decision.casefold().startswith("исключена утверждённым ответом:"):
                    if len(decision.split(":", 1)[1].strip()) < 3:
                        errors.append(f"table-row coverage row {row_number}: excluded row needs an answer source")
                else:
                    errors.append(f"table-row coverage row {row_number}: unsupported decision {decision!r}")
            for table_number in sorted(referenced_table_numbers):
                declared_rows = declared.get(table_number, [])
                duplicates = sorted({value for value in declared_rows if declared_rows.count(value) > 1})
                if duplicates:
                    errors.append(f"table-row coverage duplicates rows in table {table_number}: {duplicates}")
                missing_rows = sorted(normalized_table_rows.get(table_number, set()) - set(declared_rows))
                extra_rows = sorted(set(declared_rows) - normalized_table_rows.get(table_number, set()))
                if missing_rows:
                    errors.append(f"table-row coverage misses table {table_number} rows: {missing_rows}")
                if extra_rows:
                    errors.append(f"table-row coverage has extra table {table_number} rows: {extra_rows}")

    opaque_headers = {
        (table_number, header)
        for table_number in referenced_table_numbers
        for header in normalized_table_headers.get(table_number, ())
        if OPAQUE_TABLE_HEADER_RE.fullmatch(header.strip())
        and header.strip().casefold() not in UNAMBIGUOUS_SHORT_HEADERS
    }
    semantics = find_markdown_table(
        scope_brief_content,
        ("Таблица", "Заголовок", "Значение", "Основание или пробел"),
    )
    if opaque_headers:
        if semantics is None or not semantics.rows:
            labels = ", ".join(f"Таблица {number}: {header}" for number, header in sorted(opaque_headers))
            errors.append(
                "scope-brief must resolve or explicitly gap opaque table headers: " + labels
            )
        else:
            semantics_table_index = semantics.index("Таблица")
            semantics_header_index = semantics.index("Заголовок")
            semantics_value_index = semantics.index("Значение")
            semantics_basis_index = semantics.index("Основание или пробел")
            declared_semantics: list[tuple[int, str]] = []
            approved_support = approved_support_paths(package_root)
            root = runtime_root(package_root)
            support_labels: set[str] = set()
            for path in approved_support:
                support_labels.add(path.name.casefold())
                support_labels.add(path.as_posix().casefold())
                try:
                    support_labels.add(path.relative_to(root).as_posix().casefold())
                except ValueError:
                    pass
            for row_number, row in enumerate(semantics.rows, start=1):
                table_match = TABLE_COVERAGE_NUMBER_RE.fullmatch(row[semantics_table_index].strip())
                if table_match is None:
                    errors.append(
                        f"table-header semantics row {row_number}: invalid table label {row[semantics_table_index]!r}"
                    )
                    continue
                key = (int(table_match.group(1)), row[semantics_header_index].strip())
                declared_semantics.append(key)
                value = row[semantics_value_index].strip()
                basis = row[semantics_basis_index].strip()
                gaps = set(re.findall(r"(?<![A-Za-z0-9_.-])GAP-\d{2,}(?![A-Za-z0-9_.-])", basis))
                header_semantics_gap_ids.update(gaps)
                if re.search(r"\bне\s+определ", value, re.IGNORECASE):
                    if not gaps:
                        errors.append(
                            f"table-header semantics row {row_number}: unresolved meaning must link GAP-*"
                        )
                else:
                    anchors = precise_source_anchors(basis)
                    exact_semantic_anchor = any(
                        anchor.startswith(("CODE:", "TEXT:"))
                        or (anchor.startswith("TABLE:") and anchor.count(":") >= 2)
                        for anchor in anchors
                    )
                    registered_support = any(label in basis.casefold() for label in support_labels)
                    if not value or value in {"-", "—"}:
                        errors.append(f"table-header semantics row {row_number}: meaning is empty")
                    elif not exact_semantic_anchor and not registered_support:
                        errors.append(
                            f"table-header semantics row {row_number}: interpreted meaning needs an exact source legend or approved support path"
                        )
            for key in sorted(opaque_headers):
                if declared_semantics.count(key) != 1:
                    errors.append(
                        f"opaque table header must appear exactly once in semantics control: Таблица {key[0]}, {key[1]!r}"
                    )
            extras = sorted(set(declared_semantics) - opaque_headers)
            if extras:
                errors.append("table-header semantics contains non-opaque or unreferenced headers: " + repr(extras))
    elif semantics is not None and semantics.rows:
        errors.append("scope-brief has table-header semantics rows but referenced tables have no opaque headers")
    visual_check = find_markdown_table(
        scope_brief_content,
        ("UI-уровень", "Визуальный источник", "Результат сверки"),
    )
    incomplete_local_visual = False
    no_visual_reason = re.search(
        r"(?im)^Визуальная\s+сверка\s+не\s+требуется:\s*(.{5,})$",
        scope_brief_content,
    )
    registered_sections = locator_sections(package_root)
    registered_visuals = {
        resolve_declared_path(package_root, entry["path"]).as_posix().casefold()
        for entry in registered_sections.get("visual_sources", [])
        if entry.get("path")
    }
    registered_figma = {
        entry["url"]
        for entry in registered_sections.get("figma_sources", [])
        if entry.get("url")
    }
    if visual_check is None or not visual_check.rows:
        if no_visual_reason is None:
            errors.append(
                "scope-brief must contain visual cross-check rows for included UI levels "
                "or 'Визуальная сверка не требуется: <причина>'"
            )
    else:
        visual_index = visual_check.index("Визуальный источник")
        visual_result_index = visual_check.index("Результат сверки")
        for row_number, row in enumerate(visual_check.rows, start=1):
            visual_source = row[visual_index]
            visual_result = row[visual_result_index].strip()
            if not visual_result or visual_result in {"-", "—"}:
                errors.append(f"scope-brief visual cross-check row {row_number}: result is missing")
            if VISUAL_INCOMPLETE_RE.search(visual_result):
                incomplete_local_visual = True
            declared_paths = LOCAL_VISUAL_RE.findall(visual_source)
            declared_urls = re.findall(r"https?://[^\s|]+", visual_source)
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
            for value in declared_urls:
                if value not in registered_figma:
                    errors.append(
                        f"scope-brief visual cross-check row {row_number}: "
                        f"Figma URL is not registered by source locator: {value}"
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

    if incomplete_local_visual and registered_figma:
        figma_recorded = any(url in scope_brief_content for url in registered_figma)
        figma_unavailable = re.search(r"(?im)^Figma\s+недоступна:\s*.{5,}$", scope_brief_content)
        if not figma_recorded and figma_unavailable is None:
            errors.append(
                "scope-brief records incomplete local visual evidence; use one registered Figma URL "
                "or state 'Figma недоступна: <причина>'"
            )

    consistency = find_markdown_table(
        scope_brief_content,
        ("Аспект", "Вывод анализа", "Связанные обязанности/пробелы"),
    )
    consistency_refs: set[str] = set()
    if consistency is None or not consistency.rows:
        errors.append("scope-brief must contain applicable consistency analysis rows")
    else:
        aspect_index = consistency.index("Аспект")
        conclusion_index = consistency.index("Вывод анализа")
        refs_index = consistency.index("Связанные обязанности/пробелы")
        aspects = [row[aspect_index].strip() for row in consistency.rows]
        normalized_allowed = {aspect.casefold(): aspect for aspect in CONSISTENCY_ASPECTS}
        for aspect in aspects:
            if aspect.casefold() not in normalized_allowed:
                errors.append(
                    f"scope-brief consistency analysis has unsupported aspect {aspect!r}"
                )
            if sum(value.casefold() == aspect.casefold() for value in aspects) != 1:
                errors.append(f"scope-brief consistency aspect {aspect!r} must appear exactly once")
        for row in consistency.rows:
            aspect = row[aspect_index].strip() or "<без аспекта>"
            conclusion = row[conclusion_index].strip()
            references = row[refs_index].strip()
            if not conclusion:
                errors.append(f"scope-brief consistency aspect {aspect!r} has no conclusion")
                continue
            if conclusion.casefold().startswith("не применимо"):
                errors.append(
                    f"scope-brief consistency aspect {aspect!r}: omit non-applicable aspects instead of adding a row"
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
    assumption_anchors = {
        anchor
        for _path, support in support_contents
        for card in support_cards(support)
        for anchor in operational_assumption_anchors(card)
    }

    gaps_content = (scope_dir / "coverage-gaps.md").read_text(encoding="utf-8")
    gaps = find_markdown_table(
        gaps_content,
        ("ID", "Связанная обязанность", "Источник", "Класс", "Недостаток источника", "Что требуется для закрытия"),
    )
    gap_ids: list[str] = []
    resolved_gap_ids: set[str] = set()
    gap_sources: dict[str, str] = {}
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
                gap_sources[gap_id] = row[gap_source_index].strip()
                if not GAP_ID_RE.fullmatch(gap_id):
                    errors.append(f"coverage-gaps has invalid ID {gap_id!r}")
                linked_sources = SOURCE_ROW_TOKEN_RE.findall(row[linked_source_index])
                if len(linked_sources) != 1:
                    errors.append(f"{gap_id}: coverage gap must link exactly one atomic SR obligation")
                elif linked_sources[0] not in active_inventory_ids:
                    errors.append(f"{gap_id}: linked source obligation {linked_sources[0]} is absent from active inventory")
                elif canonical_source_reference(row[gap_source_index]) != canonical_source_reference(
                    inventory_sources.get(linked_sources[0], "")
                ):
                    errors.append(
                        f"{gap_id}: source reference must exactly reuse the linked {linked_sources[0]} source anchor"
                    )
                gap_class = row[gap_class_index].strip()
                if gap_class not in ALLOWED_GAP_CLASSES:
                    errors.append(f"{gap_id}: unsupported coverage-gap class {gap_class!r}")
                gap_details = " | ".join((row[gap_deficit_index], row[gap_resolution_index]))
                if RESOLVED_GAP_RE.search(row[gap_resolution_index]):
                    resolved_gap_ids.add(gap_id)
                if MISSING_ENVIRONMENT_GAP_RE.search(gap_details):
                    errors.append(
                        f"{gap_id}: missing environment data is execution readiness, not a coverage gap"
                    )
                source_anchors = precise_source_anchors(row[gap_source_index])
                covered_assumptions = sorted(source_anchors & assumption_anchors)
                if covered_assumptions:
                    errors.append(
                        f"{gap_id}: non-blocking working assumption provides current behavior for "
                        + ", ".join(covered_assumptions)
                        + "; record future update instead of a coverage gap"
                    )

    known_gap_ids = set(gap_ids)
    unknown_header_semantics_gaps = sorted(header_semantics_gap_ids - known_gap_ids)
    if unknown_header_semantics_gaps:
        errors.append(
            "table-header semantics references unknown gaps: " + ", ".join(unknown_header_semantics_gaps)
        )
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
    unknown_boundary_refs = sorted(
        reference
        for reference in boundary_refs
        if reference not in active_inventory_ids and reference not in known_gap_ids
    )
    if unknown_boundary_refs:
        errors.append("scope-brief source boundary control references unknown IDs: " + ", ".join(unknown_boundary_refs))
    unknown_ownership_refs = sorted(
        reference
        for reference in ownership_refs
        if reference not in active_inventory_ids and reference not in known_gap_ids
    )
    if unknown_ownership_refs:
        errors.append("parent requirement ownership references unknown IDs: " + ", ".join(unknown_ownership_refs))
    unknown_table_refs = sorted(
        reference
        for reference in table_coverage_refs
        if reference not in active_inventory_ids and reference not in known_gap_ids
    )
    if unknown_table_refs:
        errors.append("table-row coverage references unknown IDs: " + ", ".join(unknown_table_refs))

    prompt = (scope_dir / "prompt.scope-to-writer.md").read_text(encoding="utf-8")
    unknown_prompt_source_rows = sorted(set(SOURCE_ROW_TOKEN_RE.findall(prompt)) - active_inventory_ids)
    if unknown_prompt_source_rows:
        errors.append(
            "writer prompt references source rows absent from active inventory: "
            + ", ".join(unknown_prompt_source_rows)
        )
    combined_scope_text = "\n".join(
        (scope_dir / name).read_text(encoding="utf-8") for name in REQUIRED_FILES if name.endswith(".md")
    )
    if OMIT_GAP_RE.search(combined_scope_text):
        errors.append("scope handoff tells writer to omit coverage-gap obligations from the matrix")
    unresolved_gap_ids = [gap_id for gap_id in gap_ids if gap_id not in resolved_gap_ids]
    if unresolved_gap_ids:
        if "coverage-gap" not in prompt or "матриц" not in prompt.casefold():
            errors.append("writer prompt must preserve unresolved obligations in the matrix as coverage-gap")
        for gap_id in unresolved_gap_ids:
            if gap_id not in prompt:
                errors.append(f"writer prompt does not carry {gap_id}")
    for gap_id in sorted(resolved_gap_ids):
        resolved_gap_as_matrix = re.compile(
            rf"(?:{re.escape(gap_id)}[^\n]{{0,140}}coverage-gap|coverage-gap[^\n]{{0,140}}{re.escape(gap_id)})",
            re.IGNORECASE,
        )
        if resolved_gap_as_matrix.search(prompt):
            errors.append(f"writer prompt carries resolved {gap_id} as coverage-gap")

    test_data_plan_content = (scope_dir / "test-data-plan.md").read_text(encoding="utf-8")
    source_evidence = "\n".join([machine_source_text, *(support for _path, support in support_contents)])
    errors.extend(validate_test_data_plan(test_data_plan_content, source_evidence))

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
        linked_gaps = set(re.findall(r"\bGAP-\d{2,}\b", coverage_impact))
        if not linked_gaps:
            errors.append(
                f"{question_id}: clarification card must track at least one independently resolvable GAP-*"
            )
        elif len(linked_gaps) == 1:
            linked_gap = next(iter(linked_gaps))
            if linked_gap not in gap_sources:
                if status not in {"ответ-получен", "отменён"}:
                    errors.append(f"{question_id}: clarification card references unknown coverage gap {linked_gap}")
            elif canonical_source_reference(requirement_basis) != canonical_source_reference(
                gap_sources[linked_gap]
            ):
                errors.append(
                    f"{question_id}: FT basis must exactly reuse the linked coverage-gap source anchor"
                )
        else:
            question_basis_anchors = precise_source_anchors(requirement_basis)
            for linked_gap in sorted(linked_gaps):
                if linked_gap not in gap_sources:
                    if status not in {"ответ-получен", "отменён"}:
                        errors.append(f"{question_id}: clarification card references unknown coverage gap {linked_gap}")
                    continue
                gap_anchors = precise_source_anchors(gap_sources[linked_gap])
                if not gap_anchors or not gap_anchors.issubset(question_basis_anchors):
                    errors.append(
                        f"{question_id}: multi-gap FT basis must include the exact source anchor of {linked_gap}"
                    )
        if status in {"ответ-получен", "отменён"}:
            still_open = sorted(linked_gaps - resolved_gap_ids)
            if still_open:
                errors.append(
                    f"{question_id}: answered or cancelled clarification still links open coverage gaps: "
                    + ", ".join(still_open)
                )
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
        question_anchors = precise_source_anchors(requirement_basis)
        if not question_anchors:
            errors.append(
                f"{question_id}: question needs an exact requirement code or an uncoded structural anchor "
                "(exact table row, or section plus quoted paragraph/list text)"
            )
            continue
        provisional_anchors = question_anchors & assumption_anchors
        if provisional_anchors and status not in {"ответ-получен", "отменён"}:
            errors.append(
                f"{question_id}: non-blocking working assumption already provides current behavior for "
                + ", ".join(sorted(provisional_anchors))
                + "; preserve a future-update note instead of a BA question"
            )
        matching_support: list[Path] = []
        for path, support in support_contents:
            if question_anchors.intersection(precise_source_anchors(support)):
                matching_support.append(path)
            if status not in {"ответ-получен", "отменён"} and duplicates_fully_answered_question(
                current_question, support, question_anchors
            ):
                errors.append(
                    f"{question_id}: duplicates a fully answered approved clarification for "
                    + ", ".join(sorted(question_anchors))
                )
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
        for pattern, description in HIGH_CONFIDENCE_TEXT_ERRORS:
            if pattern.search(visible):
                errors.append(f"{name}: high-confidence user-facing text error: {description}")
    visible_questions = strip_allowed_technical_fragments(questions_content)
    for word, replacement in FORBIDDEN_PROCESS_WORDS.items():
        if re.search(rf"\b{re.escape(word)}s?\b", visible_questions, re.IGNORECASE):
            errors.append(
                "work/scope-clarification-requests.md: use Russian wording instead of "
                f"{word!r} ({replacement})"
            )
    for pattern, description in HIGH_CONFIDENCE_TEXT_ERRORS:
        if pattern.search(visible_questions):
            errors.append(
                "work/scope-clarification-requests.md: high-confidence user-facing text error: "
                + description
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a lean runtime scope handoff.")
    parser.add_argument("package_root", type=Path, nargs="?")
    parser.add_argument("scope_dir", type=Path, nargs="?")
    parser.add_argument(
        "--print-contract",
        action="store_true",
        help="Print the stable authoring contract without reading validator implementation.",
    )
    parser.add_argument("--scope", help="Scope identifier used to build non-normative ID examples.")
    args = parser.parse_args()
    if args.print_contract:
        print(json.dumps(public_contract(args.scope), ensure_ascii=False, indent=2))
        return 0
    if args.package_root is None or args.scope_dir is None:
        parser.error("package_root and scope_dir are required unless --print-contract is used")
    errors = validate(args.package_root.resolve(), args.scope_dir.resolve())
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
