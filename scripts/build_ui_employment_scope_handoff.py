from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_15_clean_before_writer"
SCOPE = "ui-employment"
HANDOFF_DIR = FT_ROOT / "work" / "stage-handoffs" / "02-ui-employment"
SECTION_DIR = HANDOFF_DIR / "artifact-sections"

DOCX = "source/ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.docx"
PDF = "source/ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.pdf"
SOURCE_SELECTION = "work/stage-handoffs/00-source-selection/source-selection.md"
AGENT_NOTES = "AGENT-NOTES.md"
WIDGET_DOC = "support/PostFinal v12 Описание базовых возможностей интерфейсных виджетов_24.02.2026.docx"
DICTIONARY_XLSX = "support/Наполнение справочников_v1.xlsx"
MOCKUP_1 = "mockups/Сведения о занятости.png"
MOCKUP_2 = "mockups/Сведения о занятости2.png"


@dataclass(frozen=True)
class SourceRow:
    src_id: str
    package_id: str
    name: str
    docx_ref: str
    pdf_ref: str
    req_ids: str
    row_type: str
    status: str = "match"
    action: str = "use"


ROWS = [
    SourceRow("SRC-001", "WP-01", "Блок «Сведения о занятости» / «Работа по совместительству»", "DOCX section-23 table 10 row 1", "PDF p.61", "-", "block"),
    SourceRow("SRC-002", "WP-01", "Тип занятости", "DOCX section-23 table 10 row 2", "PDF p.61", "-", "field"),
    SourceRow("SRC-003", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "DOCX section-23 table 10 row 3", "PDF p.61", "GSR 123; GSR 124", "field", "pdf-code-only"),
    SourceRow("SRC-004", "WP-01", "Наименование организации, ИНН", "DOCX section-23 table 10 row 4", "PDF p.61", "GSR 125; GSR 126", "field", "pdf-code-only", "use; GAP-001"),
    SourceRow("SRC-005", "WP-01", "Фактический адрес работы", "DOCX section-23 table 10 row 5", "PDF p.61", "GSR 127; GSR 128", "field", "pdf-code-only", "use; GAP-001"),
    SourceRow("SRC-006", "WP-01", "Тип должности", "DOCX section-23 table 10 row 6", "PDF p.61", "GSR 129", "field", "pdf-code-only"),
    SourceRow("SRC-007", "WP-01", "Должность", "DOCX section-23 table 10 row 7", "PDF pp.61-62", "GSR 130", "field", "pdf-code-only"),
    SourceRow("SRC-008", "WP-01", "Стаж работы", "DOCX section-23 table 10 row 8", "PDF p.62", "GSR 131", "field", "pdf-code-only"),
    SourceRow("SRC-009", "WP-01", "Рабочий телефон", "DOCX section-23 table 10 row 9", "PDF p.62", "GSR 132; GSR 133; GSR 134", "field", "pdf-code-only"),
    SourceRow("SRC-010", "WP-02", "Блок «Дополнительный доход»", "DOCX section-23 table 10 row 10", "PDF p.62", "-", "block"),
    SourceRow("SRC-011", "WP-02", "Тип дохода", "DOCX section-23 table 10 row 11", "PDF p.62", "-", "field", "match", "use; GAP-002"),
    SourceRow("SRC-012", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "DOCX section-23 table 10 row 12", "PDF p.62", "GSR 135", "field", "pdf-code-only"),
    SourceRow("SRC-013", "WP-03", "Общие поля", "DOCX section-23 table 10 row 13", "PDF p.62", "-", "block"),
    SourceRow("SRC-014", "WP-03", "Клиент добросовестный", "DOCX section-23 table 10 row 14", "PDF p.62", "GSR 136", "field", "pdf-code-only"),
    SourceRow("SRC-015", "WP-03", "Визуальная информация", "DOCX section-23 table 10 row 15", "PDF p.62", "GSR 137; GSR 138", "field", "pdf-code-only"),
    SourceRow("SRC-016", "WP-03", "Параметры визуальной оценки", "DOCX section-23 table 10 row 16", "PDF pp.62-63", "GSR 139; GSR 140", "field", "pdf-code-only"),
    SourceRow("SRC-017", "WP-03", "Примечание DaData по найденной организации", "DOCX section-23 note after table 10", "PDF p.63", "GSR 141", "note", "pdf-code-only", "use; GAP-001"),
    SourceRow("SRC-018", "WP-04", "«Следующий шаг»", "DOCX section-24 table 11 row 1", "PDF pp.63-65", "GSR 142; GSR 143", "action", "pdf-code-only", "use; GAP-003"),
    SourceRow("SRC-019", "WP-04", "«Добавить работу по совместительству»", "DOCX section-24 table 11 row 2", "PDF p.65", "GSR 144; GSR 145", "action", "pdf-code-only"),
    SourceRow("SRC-020", "WP-04", "«Добавить дополнительный доход»", "DOCX section-24 table 11 row 3", "PDF p.65", "GSR 146; GSR 147", "action", "pdf-code-only"),
    SourceRow("SRC-021", "WP-04", "«Назад»", "DOCX section-24 table 11 row 4", "PDF p.65", "GSR 148", "action", "pdf-code-only"),
    SourceRow("SRC-022", "WP-05", "CDI: не удалось верифицировать ИНН", "DOCX not found by structured extraction", "PDF pp.65-66", "-", "pdf-only-ui-message", "pdf-only", "use; GAP-004"),
    SourceRow("SRC-023", "WP-05", "CDI: данные клиента отличаются от данных заявки", "DOCX not found by structured extraction", "PDF p.66", "-", "pdf-only-ui-message", "pdf-only", "use; GAP-004"),
    SourceRow("SRC-024", "WP-05", "CDI: подтверждение замены данных", "DOCX not found by structured extraction", "PDF p.67 before next section", "-", "pdf-only-ui-message", "pdf-only", "use; GAP-004"),
]


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        clean = []
        for cell in row:
            value = str(cell) if cell not in (None, "") else "-"
            clean.append(value.replace("\n", "<br>").replace("|", "\\|"))
        out.append("| " + " | ".join(clean) + " |")
    return "\n".join(out)


def req_ids() -> list[str]:
    ids: list[str] = []
    for row in ROWS:
        if row.req_ids == "-":
            continue
        ids.extend(part.strip() for part in row.req_ids.split(";") if part.strip())
    return ids


def write_section_file(name: str, text: str) -> str:
    SECTION_DIR.mkdir(parents=True, exist_ok=True)
    path = SECTION_DIR / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
    return path.name


def write_artifact(target: Path, name: str, sections: list[tuple[int, str, str]], preamble: str = "") -> None:
    SECTION_DIR.mkdir(parents=True, exist_ok=True)
    preamble_file = write_section_file(f"{name}.00.preamble.md", preamble) if preamble else ""
    manifest = {
        "target_path": str(target),
        "preamble_file": preamble_file,
        "sections": [
            {
                "level": level,
                "heading": heading,
                "content_file": write_section_file(f"{name}.{index:02d}.section.md", content),
            }
            for index, (level, heading, content) in enumerate(sections, start=1)
        ],
    }
    manifest_path = SECTION_DIR / f"{name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path), "--dry-run"], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)], check=True)


def source_row_inventory() -> str:
    table_rows = [
        [
            row.src_id,
            row.package_id,
            row.name,
            f"{row.docx_ref}; {row.pdf_ref}",
            row.req_ids,
            "unclear",
            row.action if "GAP" in row.action else "pending-writer-normalization",
        ]
        for row in ROWS
    ]
    return md_table(
        ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
        table_rows,
    ) + """

## Inventory Notes

- `in_scope = unclear` means the row is inside the confirmed scope, but final `ATOM-*` mapping is intentionally deferred to writer-side normalization.
- Writer must preserve every `SRC-*` row in writer-side inventory before atomic ledger creation.
- Rows with multiple `GSR` values require Source Row Completeness Matrix before Source Table Normalization.
- `SRC-022`-`SRC-024` are PDF-only in-section UI message fragments. They must not be dropped merely because DOCX structured extraction did not expose them.
"""


def source_parity_check() -> str:
    boundary = md_table(
        ["item", "docx_ref", "pdf_ref", "status", "note"],
        [
            ["Макет раздела", "section-22 / «Макет раздела...»", "2.1.1.1.1.2.1, pp.59-60", "match", "PDF has numbered subsection and figures 7/8; DOCX extraction has figure captions."],
            ["Описание свойств полей", "section-23 / table 10 + note", "2.1.1.1.1.2.2, pp.61-63", "pass-with-pdf-code-only", "DOCX has field text; PDF adds GSR 123-141."],
            ["Описание действий", "section-24 / table 11", "2.1.1.1.1.2.3, pp.63-65", "pass-with-pdf-code-only", "DOCX has action text; PDF adds GSR 142-148."],
            ["CDI UI messages", "not found by structured DOCX extraction", "pp.65-67 before next section", "pdf-only", "Text is inside the employment-section flow before `Раздел «Анкета клиента»`; preserve as PDF-only scope input."],
            ["End boundary", "after section-24 text", "p.67 before `Раздел «Анкета клиента»`; p.68 starts `2.1.1.1.1.4.1`", "match-with-extraction-risk", "Do not include `Анкета клиента` requirements except direct navigation result from employment action."],
        ],
    )
    req_table = md_table(
        ["req_id", "docx_ref", "pdf_ref", "status", "source_decision", "note"],
        [[rid, "-", f"PDF pp.61-65 / row inventory", "pdf-only", "mandatory-req-id", "Use as `req_id`; behavior text is mirrored in DOCX table/note where available."] for rid in req_ids()],
    )
    row_table = md_table(
        ["row_anchor", "docx_ref", "pdf_ref", "docx_text", "pdf_text", "status", "action"],
        [
            [
                row.src_id,
                row.docx_ref,
                row.pdf_ref,
                row.name,
                row.name,
                row.status,
                row.action,
            ]
            for row in ROWS
        ],
    )
    return f"""## Source Parity Check

- FT package: `fts/ft-2-OF_15_clean_before_writer`
- Scope: `ui-employment`
- DOCX source: `{DOCX}`
- PDF source: `{PDF}`
- DOCX extraction: `test_case_agent.resolve_sections()` + `python-docx` table extraction
- PDF extraction: `pypdf` text extraction + Poppler render of pages 59-67
- DOCX scope refs: `section-22`, `section-23`, `section-24`
- PDF scope refs: `2.1.1.1.1.2.1`-`2.1.1.1.1.2.3`, pages 59-67 before `Раздел «Анкета клиента»`

## Boundary Parity

{boundary}

## Requirement Id Inventory

{req_table}

## Table / Row Parity

{row_table}

## Mandatory Traceability Inputs

- Requirement IDs to preserve: `{'; '.join(req_ids())}`
- PDF-only IDs to preserve: `{'; '.join(req_ids())}`
- DOCX-only IDs to preserve: `none`
- Semantic mismatches requiring gaps: `none`
- PDF-only semantic rows without GSR: `SRC-022`; `SRC-023`; `SRC-024`

## Decision

- Scope parity status: `pass-with-extraction-risk`
- Writer/reviewer rule: downstream must preserve PDF-only `GSR 123`-`GSR 148` and `SRC-022`-`SRC-024`; DOCX remains primary for text where both sources carry the same requirement.
- Open gaps/questions: `GAP-001`; `GAP-002`; `GAP-003`; `GAP-004`
"""


def scope_contract() -> str:
    sources = md_table(
        ["source", "type", "usage_rule"],
        [
            [SOURCE_SELECTION, "source-selection", "Confirms selected package and main DOCX/PDF; not a requirement source by itself."],
            [DOCX, "main-ft", "Primary requirement source for included DOCX sections `section-22`-`section-24`."],
            [PDF, "pdf", "Structural parity and mandatory PDF-only GSR/source rows inside confirmed scope."],
            [AGENT_NOTES, "package-notes", "Mandatory package context; UI table `О` = обязательность, `Р` = редактируемость."],
            [WIDGET_DOC, "support", "Widget behavior reference only; does not change FT field properties."],
            [DICTIONARY_XLSX, "support", "Allowed values for employment dictionaries only where FT references a dictionary."],
            [MOCKUP_1, "mockup", "Visual order and interaction hints only."],
            [MOCKUP_2, "mockup", "Visual order and interaction hints only."],
        ],
    )
    complexity = md_table(
        ["factor", "value", "risk", "note"],
        [
            ["fields_or_blocks", "16 DOCX field-table rows + DaData note + 4 action rows + 3 PDF-only CDI UI message fragments", "medium", "Table-driven UI scope with conditional fields and action flows."],
            ["conditional_dependencies", "Тип занятости; Добавить источник дохода; Клиент добросовестный vs Визуальная информация; CDI outcome", "medium", "Several fields change visibility/requiredness from other field values or actions."],
            ["validation_domains", "numeric; length; dictionary; boolean; conditional-requiredness", "medium", "Income and phone constraints need boundary/equivalence design."],
            ["action_flows", "Следующий шаг; add/delete part-time; add/delete income; Назад; CDI messages", "medium", "Some flows have downstream/back-end effects that are not fully observable in UI."],
            ["integrations_api_async", "DaData; СПР; CDI; антифрод/external sources", "high", "Only UI-visible initiation/results may be covered without evidence."],
            ["status_lifecycle", "Return from status `Выбор решения`", "medium", "Status list and activation mechanics are outside this UI section."],
            ["expected_gaps_or_unclear", "4 non-blocking gaps", "medium", "Gaps constrain expected results but do not block UI-visible coverage."],
        ],
    )
    packages = md_table(
        ["package_id", "focus", "source_refs", "included_requirements", "design_method", "expected_outputs", "split_required"],
        [
            ["WP-01", "Основная работа и DaData employer fields", "SRC-001..SRC-009; SRC-017", "GSR 123-134; GSR 141", "field-property coverage; equivalence-boundary; integration artifact gate", "field atoms, dictionary/value coverage, DaData observable/gap split", "no"],
            ["WP-02", "Дополнительный доход", "SRC-010..SRC-012", "GSR 135 plus source row without GSR for unique income type rule", "field-property coverage; decision table", "add-income action dependencies and duplicate income-type handling", "no"],
            ["WP-03", "Общие поля и визуальная оценка", "SRC-013..SRC-016", "GSR 136-140", "dependency matrix; decision table", "mutual requiredness/visibility and checkbox selection coverage", "no"],
            ["WP-04", "Действия раздела", "SRC-018..SRC-021", "GSR 142-148", "scenario-use-case; integration artifact gate", "navigation, validation, add/delete blocks, back-confirmation coverage", "no"],
            ["WP-05", "PDF-only CDI UI messages", "SRC-022..SRC-024", "PDF-only rows without GSR", "scenario-use-case; integration artifact gate", "message/button behavior if triggerable; setup limitations as gap handling", "no"],
        ],
    )
    return f"""## Контекст

- FT-пакет: `fts/ft-2-OF_15_clean_before_writer`
- Основной FT DOCX: `{DOCX}`
- PDF для structural cross-check: `есть`
- `AGENT-NOTES.md`: `есть`
- Source-selection: `{SOURCE_SELECTION}`

## Scope Identity

- `scope_slug`: `ui-employment`
- Рабочее название: `UI-раздел «Сведения о занятости»`
- `source_path`: DOCX `section-22`-`section-24`; PDF `2.1.1.1.1.2.1`-`2.1.1.1.1.2.3`, pages 59-67 before next section
- Режим получения: `manual-scope`

## Что Входит В Scope

- DOCX `section-22` - макет раздела `Сведения о занятости`.
- DOCX `section-23` - таблица свойств полей формы и примечание DaData для раздела.
- DOCX `section-24` - таблица действий раздела.
- PDF pages 59-67 within `2.1.1.1.1.2.*`, including PDF-only `GSR 123`-`GSR 148` and PDF-only CDI UI messages before the next section.
- Support dictionaries referenced by included rows: `Типы занятости`, `Типы должности`, `Стаж работы`, `Виды дохода`, `Параметры визуальной оценки`.
- Mockup visual inventory: `work/stage-handoffs/02-ui-employment/mockup-visual-inventory.md`

## Что Не Входит В Scope

- Neighboring UI sections: `Основная информация`, `Анкета клиента`, `Документы клиента`, `Подготовка к сделке`, except direct navigation targets named by included actions.
- Already created `ui-main-info` test cases, review artifacts and test-design artifacts as requirement sources.
- Backend/API/RabbitMQ/model persistence effects unless an included source row gives a UI-observable artifact.
- Mockup-only side-panel statuses, decorative layout and exact sample values unless supported by FT/support text.

## Разрешенные Источники

{sources}

## Scope Complexity Assessment

{complexity}

Complexity decision:

- `single_scope_with_internal_packages`
- Обоснование: scope is one confirmed UI section with coherent field/action flow; internal `WP-*` packages are enough and do not create external scope expansion.

## Внутренние Рабочие Пакеты

{packages}

## Целевые Артефакты

- Канонический файл тест-кейсов: `test-cases/2-1-1-1-1-2-ui-employment.md`
- Handoff-папка: `work/stage-handoffs/02-ui-employment/`
- Review-cycle папка: `work/review-cycles/ui-employment/`

## Условия Старта Следующего Этапа

- Because `scope-coverage-gaps.md` contains `GAP-*`, active next stage is pre-writer `scope_gap_review`.
- Writer may start only after gap review passes or after explicit routing update.
- Writer/iteration must use `source-selection.md`, `scope-contract.md`, `source-parity-check.md`, `source-row-inventory.md`, `mockup-visual-inventory.md`, `scope-coverage-gaps.md`, `scope-clarification-requests.md`, `AGENT-NOTES.md` and the active prompt.
- Each `ATOM-*` and `TC-*` must carry `package_id`.
- For every package, run package ledger self-check, Package Test Design Plan self-check, and package TC self-check before moving to the next package.

## Ограничения И Правила Интерпретации

- Do not expand beyond `Сведения о занятости`.
- Do not invent behavior for DaData, CDI, SPR, anti-fraud, external checks, duplicate prevention UI, statuses, exact dropdown behavior, retry or error texts not stated in FT/support.
- Main FT text has priority over mockups; mockups only refine visual inventory and manual interaction hints.
- PDF-only `GSR 123`-`GSR 148` are mandatory traceability IDs.
"""


def mockup_visual_inventory() -> str:
    metadata = md_table(
        ["item", "value", "evidence"],
        [
            ["mockup_path", MOCKUP_1, "opened by visual inspection; size 68327 bytes"],
            ["mockup_path", MOCKUP_2, "opened by visual inspection; size 101802 bytes"],
            ["opened", "yes", "Codex `view_image`, 2026-06-03"],
            ["method", "visual-inspection", "manual visual review of both PNG files"],
            ["screen_name", "Сведения о занятости", "screen heading on both mockups"],
            ["source_priority", "FT-over-mockup", "AGENTS.md / scope-contract.md"],
            ["contract_terms", "visible_blocks; visible_fields; visible_actions; interaction_hints; mockup_only_items; ft_conflicts", "validator-readable aliases for canonical sections"],
        ],
    )
    visual = md_table(
        ["item_type", "label_from_mockup", "canonical_ft_name", "visible_state", "notes"],
        [
            ["visible_blocks", "Основная работа / Сведения о работе", "Блок «Сведения о занятости»", "visible", "Top form card."],
            ["visible_fields", "Тип занятости", "Тип занятости", "visible/select", "Dropdown arrow visible."],
            ["visible_fields", "Среднемесячный доход после вычета налогов", "Среднемесячный доход после вычета налогов", "visible/input", "Currency suffix shown on mockup; currency behavior comes from FT/support only if stated."],
            ["visible_blocks", "Работа по совместительству", "Работа по совместительству", "visible", "First mockup shows dashed add area; second shows added card."],
            ["visible_actions", "Добавить работу по совместительству", "«Добавить работу по совместительству»", "visible", "Dashed add button with plus icon."],
            ["visible_actions", "Корзина", "Удалить работу по совместительству", "visible in second mockup", "Deletion icon visible in added part-time block."],
            ["visible_blocks", "Дополнительный доход", "Блок «Дополнительный доход»", "visible", "First mockup shows add area; second shows added income card."],
            ["visible_actions", "Добавить источник дохода", "«Добавить дополнительный доход»", "visible", "Mockup label differs from FT button name; treat as UI alias."],
            ["visible_actions", "Корзина", "Удалить дополнительный доход", "visible in second mockup", "Deletion icon visible in added income block."],
            ["visible_fields", "Клиент добросовестный", "Клиент добросовестный", "visible/toggle", "Mockup 1/2 show switch enabled/on."],
            ["visible_fields", "Визуальная оценка", "Визуальная информация", "visible/toggle", "Mockup label differs from FT field name; alias only."],
            ["visible_actions", "Назад", "«Назад»", "visible", "Bottom left action."],
            ["visible_actions", "Следующий шаг", "«Следующий шаг»", "visible", "Bottom primary action."],
            ["validation_hint", "Выберите значение", "Required-field validation", "visible in second mockup", "Red border/text shown after added empty blocks; exact trigger stays FT-defined."],
        ],
    )
    hints = md_table(
        ["element", "interaction_hint", "source", "used_for_steps", "limitation"],
        [
            ["Тип занятости", "open dropdown and select value", "mockup", "yes", "Allowed values from support XLSX/FT only."],
            ["Среднемесячный доход", "type numeric value in text input", "mockup", "yes", "Currency suffix is visual; validation from FT."],
            ["Добавить работу по совместительству", "click dashed plus area", "mockup", "yes", "FT defines resulting fields/deletion."],
            ["Добавить источник дохода", "click dashed plus area", "mockup", "yes", "Treat as alias of FT action `Добавить дополнительный доход`."],
            ["Корзина", "click icon to delete added block", "mockup", "yes", "No confirmation behavior stated."],
            ["Клиент добросовестный / Визуальная оценка", "toggle switch", "mockup", "yes", "Business dependency from FT only."],
            ["Назад / Следующий шаг", "click button", "mockup", "yes", "Expected results from FT actions only."],
        ],
    )
    only = md_table(
        ["item", "mockup_observation", "ft_reference", "handling"],
        [
            ["Left side application summary/status cards", "Visible in both mockups", "Not part of employment section source rows", "ignore-out-of-scope"],
            ["Sample values `Пенсионер (не работает)` and `9 000`", "Visible in both mockups", "FT/support define allowed values and min income", "interaction/sample-only"],
            ["Red validation text `Выберите значение`", "Visible in second mockup", "FT says required fields are highlighted red; exact message not stated in DOCX/PDF field table", "gap-not-required; do not assert exact message unless UI evidence confirms"],
            ["Label `Визуальная оценка`", "Mockup uses shorter label", "FT row name is `Визуальная информация`", "alias-only"],
        ],
    )
    return f"""## Metadata

{metadata}

## Visual Inventory

{visual}

## Interaction Hints

{hints}

## Mockup-Only Items

{only}

## FT Conflicts

| item | ft_statement | mockup_observation | decision |
| --- | --- | --- | --- |
| `Визуальная информация` label | `DOCX section-23 row 15` uses `Визуальная информация` | mockup label is `Визуальная оценка` | `FT wins`; mockup label may be used as UI alias only |
| exact validation text | `GSR 142` says required empty fields are highlighted red | second mockup shows `Выберите значение` | `gap/limitation`; do not require exact text in FT-first baseline |

## Usage Decision

| item | value | evidence |
| --- | --- | --- |
| used_for_steps | `yes` | interaction hints for dropdowns, add buttons, trash icons, toggles, bottom actions |
| not_used_as_requirement_source | `yes` | mockup refines interaction only; FT/support define behavior |
| open_questions | `GAP-002`; `GAP-004` | duplicate prevention/CDI trigger setup are not derivable from mockup |
"""


def gaps() -> str:
    return """## Контекст

- `scope_slug`: `ui-employment`
- Основной FT: `source/ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.docx`
- PDF parity: `source-parity-check.md`

## Summary

- Найдено gaps: `4`
- Есть blocking gaps: `no`
- Writing можно стартовать: `partial`, после pre-writer `scope_gap_review`

## Coverage Gaps

### GAP-001
**FT Reference:** `DOCX section-23 rows 4-5 and note; PDF p.61/p.63; GSR 126; GSR 128; GSR 141`
**Source Path:** `source-row-inventory.md` rows `SRC-004`, `SRC-005`, `SRC-017`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** DaData is integrated with employer search; work address/other fields are prefilled when organization is selected/found.
**Gap Type:** `integration`
**Description:** FT does not define DaData lookup trigger, minimum input, no-result handling, exact dropdown behavior, or observable artifact for SPR contract fields.
**Impact:** `non-blocking`
**Coverage Impact:** `partial`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** exact DaData interaction and observable verification of non-UI SPR contract fields.
**Why Expected Result Not Derivable:** main FT names integration and prefill effects but not UI mechanics/fallbacks or backend evidence.
**Affected Test-design Dimension:** `integration`
**Risk:** `medium`
**Blocks Ready For Review:** `no`
**Question To Analyst:** Should tests cover only UI-visible employer/address prefill, or is there an approved observable artifact for SPR contract field prefill?
**Temporary Handling:** Writer may cover UI-visible selection/prefill if observable; backend/contract fields remain `unclear` unless evidence is provided.
**Writer Rule:** Do not invent DaData dropdown thresholds, sorting, fallback messages, or backend assertions.
**Reviewer Rule:** Treat backend-only DaData assertions as defects unless tied to evidence.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-002
**FT Reference:** `DOCX section-23 row 11; PDF p.62; field «Тип дохода»`
**Source Path:** `source-row-inventory.md` row `SRC-011`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** Income types `Пенсия` and `Аренда` can be added only once.
**Gap Type:** `missing-rule`
**Description:** FT does not state the UI mechanism for preventing the second addition: option filtering, disabled option, validation error, or save rejection.
**Impact:** `non-blocking`
**Coverage Impact:** `design-constraint-on-covered-atom`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** exact duplicate-prevention mechanism and expected UI feedback.
**Why Expected Result Not Derivable:** invariant is clear, but the observable UI result is not specified.
**Affected Test-design Dimension:** `dependency`
**Risk:** `medium`
**Blocks Ready For Review:** `no`
**Question To Analyst:** How should UI prevent adding `Пенсия` or `Аренда` more than once?
**Temporary Handling:** Writer may test that duplicate addition is not possible, but must not assert a specific error text/mechanism.
**Writer Rule:** Keep exact prevention feedback as `unclear` unless support/UI evidence confirms it.
**Reviewer Rule:** Reject tests that invent a duplicate-income error message or exact control state.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-003
**FT Reference:** `DOCX section-24 row 1; PDF pp.63-65; GSR 142`
**Source Path:** `source-row-inventory.md` row `SRC-018`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** When returning from status `Выбор решения`, critical field edits send the application to SPR; FIO/birth/passport edits trigger repeated anti-fraud/external checks if they were called earlier.
**Gap Type:** `cross-ft-dependency`
**Description:** The employment UI section does not provide full status lifecycle/setup, observable SPR result, or observable anti-fraud/external-check artifact.
**Impact:** `non-blocking`
**Coverage Impact:** `partial`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** observable evidence and setup for SPR/anti-fraud/external checks.
**Why Expected Result Not Derivable:** source states backend routing/checks but not UI-visible proof or complete lifecycle preconditions.
**Affected Test-design Dimension:** `status-lifecycle`
**Risk:** `high`
**Blocks Ready For Review:** `no`
**Question To Analyst:** Is there an observable UI/status/log artifact that confirms SPR re-call and repeated checks for this flow?
**Temporary Handling:** Cover UI-visible validation/navigation and critical-field dependency; keep backend routing/check effects as `unclear`.
**Writer Rule:** Do not treat hidden SPR/anti-fraud side effects as manually verified by a UI click alone.
**Reviewer Rule:** Require observable artifact for backend effects, or keep them as residual gap.
**Needs User Input:** `yes`
**Status:** `open`

### GAP-004
**FT Reference:** `PDF pp.65-67; PDF-only CDI UI messages after GSR 148, before next section`
**Source Path:** `source-row-inventory.md` rows `SRC-022`, `SRC-023`, `SRC-024`
**Related Atomic Statement(s):** `not-yet-assigned`
**Source Statement:** Employment stage shows CDI/INN verification failure or CDI mismatch messages; buttons return to previous stage or confirm replacement of data.
**Gap Type:** `missing-constraint`
**Description:** PDF provides message text and button behavior, but DOCX structured extraction did not expose these rows and the trigger/setup for CDI outcomes is not described in the employment table.
**Impact:** `non-blocking`
**Coverage Impact:** `partial`
**Affected Atom ID:** `not-yet-assigned`
**Missing Behavior:** deterministic test setup/trigger for CDI failure and mismatch states.
**Why Expected Result Not Derivable:** expected message text is present in PDF, but how to create the source condition in UI/manual setup is not stated.
**Affected Test-design Dimension:** `integration`
**Risk:** `medium`
**Blocks Ready For Review:** `no`
**Question To Analyst:** What approved precondition/test data should be used to produce CDI INN verification failure and CDI data mismatch?
**Temporary Handling:** Preserve PDF-only rows; writer may create cases with explicit preconditions or leave setup as `unclear`.
**Writer Rule:** Do not drop PDF-only CDI rows; do not invent data setup.
**Reviewer Rule:** Check that PDF-only CDI requirements are either covered with explicit setup or retained as unresolved.
**Needs User Input:** `yes`
**Status:** `open`

## Что Можно Покрывать Несмотря На Gaps

- Field visibility, requiredness, editability, widget type and value source from DOCX/PDF rows.
- Numeric constraints explicitly stated in FT: main income minimum `2000р`, numeric-only income inputs, work phone `10` numeric symbols and default `+7(xxx)-xxx-xx-xx` mask.
- Dictionary values from support XLSX for referenced dictionaries.
- UI-visible add/delete block behavior and navigation actions.
- Exact PDF message text for CDI rows, if a valid trigger/precondition is provided.

## Что Нельзя Домысливать

- DaData thresholds, sorting, fallback/retry behavior and exact dropdown UI beyond visible interaction hints.
- Backend verification of SPR contract fields, anti-fraud/external checks, CDI integration, status changes or persistence without observable artifact.
- Exact duplicate-income prevention mechanism for `Пенсия`/`Аренда`.
- Exact validation text from mockup unless confirmed by UI evidence or FT/support text.

## Требуемые Уточнения

- `GAP-001`: observable artifact for DaData/SPR contract field prefill.
- `GAP-002`: UI mechanism for preventing duplicate `Пенсия`/`Аренда`.
- `GAP-003`: observable artifact/setup for SPR re-call and repeated checks.
- `GAP-004`: test data/precondition for CDI failure and mismatch messages.
"""


def clarification_requests() -> str:
    rows = [
        ["GAP-001", "`GSR 126`; `GSR 128`; `GSR 141`; `SRC-004/SRC-005/SRC-017`", "Should tests cover only UI-visible employer/address prefill, or is there an approved observable artifact for SPR contract field prefill?", "Full integration coverage boundary", "no", "analyst", "-", "unanswered", "not-provided", "-"],
        ["GAP-002", "`SRC-011`; field `Тип дохода`", "How should UI prevent adding `Пенсия` or `Аренда` more than once?", "Exact expected result for duplicate-income test", "no", "analyst", "-", "unanswered", "not-provided", "-"],
        ["GAP-003", "`GSR 142`; `SRC-018`", "Is there an observable UI/status/log artifact that confirms SPR re-call and repeated checks for return-from-`Выбор решения` flow?", "Backend-effect coverage or explicit residual gap", "no", "analyst", "-", "unanswered", "not-provided", "-"],
        ["GAP-004", "`PDF pp.65-67`; `SRC-022..SRC-024`", "What approved precondition/test data should be used to produce CDI INN verification failure and CDI data mismatch?", "Executable setup for PDF-only CDI message cases", "no", "analyst", "-", "unanswered", "not-provided", "-"],
    ]
    return f"""## Контекст

- `scope_slug`: `ui-employment`
- Coverage gaps: `scope-coverage-gaps.md`

## Как Заполнять

- Заполняйте только колонки `user_response`, `response_status`, `response_type`, `updated_at`.
- Не удаляйте `gap_id`.
- Если ответ заменен более новым, установите `response_status = superseded` и добавьте новую строку с тем же `gap_id`.

## Clarification Requests

{md_table(["gap_id", "related_ft_reference", "question", "needed_for", "blocking", "requested_from", "user_response", "response_status", "response_type", "updated_at"], rows)}

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| - | - | Все текущие gaps требуют уточнения аналитика или подтвержденного observable artifact. |

## Правила Использования Ответов

- Ответы в этом файле не заменяют основной FT.
- Writer may use `analyst-confirmed` or `product-confirmed` answers only with explicit traceability.
- If an answer contradicts main FT, main FT wins and the contradiction remains a gap.
"""


def prompts() -> dict[str, str]:
    common_inputs = f"""- `{SOURCE_SELECTION}`
- `work/stage-handoffs/02-ui-employment/scope-contract.md`
- `work/stage-handoffs/02-ui-employment/source-parity-check.md`
- `work/stage-handoffs/02-ui-employment/source-row-inventory.md`
- `work/stage-handoffs/02-ui-employment/mockup-visual-inventory.md`
- `work/stage-handoffs/02-ui-employment/scope-coverage-gaps.md`
- `work/stage-handoffs/02-ui-employment/scope-clarification-requests.md`
- `work/stage-handoffs/02-ui-employment/workflow-state.yaml`
- `{AGENT_NOTES}`
- `{DOCX}`
- `{PDF}`
- `{WIDGET_DOC}`
- `{DICTIONARY_XLSX}`
- `{MOCKUP_1}`
- `{MOCKUP_2}`"""
    gaps_prompt = f"""## Цель этапа

Запустить `ft-test-case-reviewer` в режиме `scope_gap_review` для pre-writer проверки gaps по scope `ui-employment`.

## Входные артефакты

{common_inputs}

## Обязательные действия

- Проверить source anchors, classification, clarification requests and downstream handling for every `GAP-*`.
- Проверить, что PDF-only `GSR 123`-`GSR 148` and `SRC-022`-`SRC-024` preserved.
- Проверить, что gaps are non-blocking and do not hide missing source rows.
- If review passes, route to `prompt.scope-to-writer.md`; if it fails, route back to `ft-scope-analyzer` or `blocked-input`.

## Не делать

- Не писать и не review-ить тест-кейсы в этом режиме.
- Не расширять scope за пределы `Сведения о занятости`.
- Не использовать `ui-main-info` test cases/review/test-design as requirement sources.

## Ожидаемые выходы

- `work/stage-handoffs/02-ui-employment/scope-gap-review.md`
- Updated `workflow-state.yaml` with passed/failed gap review routing.

## Gate завершения

Этап завершен, когда reviewer explicitly accepts or rejects each `GAP-*` anchor/classification/routing decision.
"""
    writer_prompt = f"""## Цель этапа

Запустить `ft-test-case-writer` по подтвержденному scope `ui-employment` после passed `scope_gap_review`.

## Входные артефакты

{common_inputs}
- `work/stage-handoffs/02-ui-employment/scope-gap-review.md`, если gap review уже выполнен

## Обязательные действия

- Режим writer-а: `fresh-eval-run`.
- Работать package-by-package по `WP-01`..`WP-05`; каждый `ATOM-*` и `TC-*` обязан иметь `package_id`.
- Перед atomic ledger сверить writer-side `Source Row Inventory` with handoff `source-row-inventory.md`, then create `Source Table Normalization`.
- Preserve PDF-only `GSR 123`-`GSR 148` as mandatory `req_id`; preserve PDF-only rows `SRC-022`-`SRC-024`.
- For every package run package ledger self-check, Package Test Design Plan self-check, and package TC self-check.
- Use `mockup-visual-inventory.md` only for interaction mechanics and aliases, not as business-rule source.
- For generated/table-heavy artifacts and canonical file use `scripts/write_artifact_sections.py --manifest <manifest.json>` from the start.
- Keep `GAP-001`-`GAP-004` open unless a new approved source or observable artifact closes them.

## Не делать

- Не расширять scope beyond `Сведения о занятости`.
- Не использовать already created `ui-main-info` test cases, review artifacts or test-design artifacts as requirement sources.
- Не invent DaData/CDI/SPR/backend behavior, duplicate-income UI mechanism, exact validation text or status lifecycle details.
- Writer does not set `signed-off`.

## Ожидаемые выходы

- `test-cases/2-1-1-1-1-2-ui-employment.md`
- `work/test-design/ui-employment/source-row-inventory.md`
- `work/test-design/ui-employment/source-table-normalization.md`
- `work/test-design/ui-employment/atomic-requirements-ledger.md`
- `work/test-design/ui-employment/package-test-design-plan.md`
- dependency/applicability/risk matrices, coverage gaps, writer self-check, writer session log
- `prompt.writer-to-reviewer.round-1.md`
- `workflow-state.yaml` with `stage_status: ready-for-review`

## Gate завершения

Writer-pass complete only when all source rows and mandatory PDF-only GSR IDs are represented by `ATOM-*` or retained `GAP-*`, package gates pass, and workflow routes to reviewer.
"""
    iteration_prompt = writer_prompt.replace(
        "Запустить `ft-test-case-writer` по подтвержденному scope `ui-employment` после passed `scope_gap_review`.",
        "Запустить `ft-test-case-iteration` для полного writer-reviewer session-based loop по `ui-employment` после passed `scope_gap_review`.",
    ).replace(
        "## Ожидаемые выходы\n\n- `test-cases/2-1-1-1-1-2-ui-employment.md`",
        "## Ожидаемые выходы\n\n- Full writer/reviewer cycle artifacts under `work/review-cycles/ui-employment/`\n- `test-cases/2-1-1-1-1-2-ui-employment.md`",
    ).replace(
        "`workflow-state.yaml` with `stage_status: ready-for-review`",
        "`workflow-state.yaml` with loop status: `signed-off`, `ready-for-writer-revision`, `round-cap-reached`, or `blocked-input`",
    )
    return {
        "prompt.scope-gaps-to-reviewer.md": gaps_prompt,
        "prompt.scope-to-writer.md": writer_prompt,
        "prompt.scope-to-iteration.md": iteration_prompt,
    }


def workflow_state() -> str:
    req = "\n".join(
        f"  - {p}"
        for p in [
            SOURCE_SELECTION,
            "work/stage-handoffs/02-ui-employment/scope-contract.md",
            "work/stage-handoffs/02-ui-employment/source-parity-check.md",
            "work/stage-handoffs/02-ui-employment/source-row-inventory.md",
            "work/stage-handoffs/02-ui-employment/mockup-visual-inventory.md",
            "work/stage-handoffs/02-ui-employment/scope-coverage-gaps.md",
            "work/stage-handoffs/02-ui-employment/scope-clarification-requests.md",
            "work/stage-handoffs/02-ui-employment/prompt.scope-gaps-to-reviewer.md",
            "work/stage-handoffs/02-ui-employment/workflow-state.yaml",
            AGENT_NOTES,
        ]
    )
    return f"""ft_slug: ft-2-OF_15_clean_before_writer
scope_slug: ui-employment
current_stage: ft-scope-analyzer
stage_status: ready-for-gap-review
current_round: 0
next_skill: ft-test-case-reviewer
review_mode: scope_gap_review
required_inputs:
{req}
latest_artifacts:
  source_selection: {SOURCE_SELECTION}
  scope_contract: work/stage-handoffs/02-ui-employment/scope-contract.md
  source_parity_check: work/stage-handoffs/02-ui-employment/source-parity-check.md
  source_row_inventory: work/stage-handoffs/02-ui-employment/source-row-inventory.md
  mockup_visual_inventory: work/stage-handoffs/02-ui-employment/mockup-visual-inventory.md
  scope_coverage_gaps: work/stage-handoffs/02-ui-employment/scope-coverage-gaps.md
  scope_clarification_requests: work/stage-handoffs/02-ui-employment/scope-clarification-requests.md
  active_transition_prompt: work/stage-handoffs/02-ui-employment/prompt.scope-gaps-to-reviewer.md
  writer_transition_prompt: work/stage-handoffs/02-ui-employment/prompt.scope-to-writer.md
  iteration_transition_prompt: work/stage-handoffs/02-ui-employment/prompt.scope-to-iteration.md
  session_log: work/stage-handoffs/02-ui-employment/scope-analyzer-session-log.md
  decision_log: work/stage-handoffs/02-ui-employment/agent-decision-log.md
coverage_gaps:
  blocking: 0
  non_blocking: 4
open_questions:
  - GAP-001: DaData employer/address and SPR contract observable artifact.
  - GAP-002: exact UI mechanism for preventing duplicate `Пенсия`/`Аренда`.
  - GAP-003: observable artifact/setup for SPR re-call and repeated checks after return from `Выбор решения`.
  - GAP-004: test data/precondition for PDF-only CDI failure/mismatch messages.
blocking_reasons: []
accepted_risks: []
"""


def session_log(now: str) -> str:
    strategy = md_table(
        ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
        [
            ["`work/stage-handoffs/02-ui-employment/source-row-inventory.md`", "`table-heavy generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest source-row-inventory.manifest.json`", "`yes`"],
            ["`work/stage-handoffs/02-ui-employment/*.md`", "`generated handoff`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <artifact>.manifest.json`", "`yes`"],
        ],
    )
    return f"""## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-scope-analyzer` |
| mode | `manual-scope` |
| ft_slug | `ft-2-OF_15_clean_before_writer` |
| scope_slug | `ui-employment` |
| started_from | `{SOURCE_SELECTION}` |
| status_after | `ready-for-gap-review` |
| generated_at | `{now}` |

## Inputs Read

- `{SOURCE_SELECTION}` - selected package and main DOCX/PDF/support/mockups.
- `{DOCX}` - DOCX sections `section-22`-`section-24` and tables 10/11.
- `{PDF}` - PDF pages 59-67, GSR parity and PDF-only CDI message rows.
- `{AGENT_NOTES}` - package UI table abbreviations and DaData caveats.
- `{WIDGET_DOC}` - widget behavior support for dropdown/input/toggle/checkbox context.
- `{DICTIONARY_XLSX}` - referenced dictionary values for employment fields.
- `{MOCKUP_1}` and `{MOCKUP_2}` - visual UI inventory.

## Inputs Not Used

- Existing `ui-main-info` test cases, review artifacts and test-design artifacts - explicitly excluded as requirement sources.
- Neighboring FT packages - out of scope and not opened.
- Non-target mockups - not needed for `ui-employment`.

## Key Decisions

- Confirmed DOCX boundary as `section-22`-`section-24`; PDF boundary as pages 59-67 before next section.
- Preserved PDF-only `GSR 123`-`GSR 148` as mandatory traceability IDs.
- Included PDF-only CDI message fragments `SRC-022`-`SRC-024` because they appear before the next section and explicitly name the employment stage.
- Created 5 internal work packages for field groups, actions and PDF-only CDI messages.
- Classified 4 gaps as non-blocking and routed to pre-writer `scope_gap_review`.

## Risks And Fallbacks

- DOCX structured extraction omits PDF GSR numbering and CDI message rows; handled through `source-parity-check.md`.
- PowerShell Cyrillic stdout distorted two exploratory queries; those outputs were discarded and rerun with Python Unicode escape literals.
- Backend/integration effects are not promoted to covered behavior without observable artifacts.

## Artifact Write Strategy

{strategy}

## Validation

- `test_case_agent.resolve_sections()` - found `section-22`, `section-23`, `section-24` for `Сведения о занятости`.
- `python-docx` - extracted DOCX tables 10 and 11.
- `pypdf` + Poppler render - checked PDF pages 59-67.
- `scripts/validate_agent_artifacts.py --root ... --json` - see final command output after generation.

## Contamination Check

- Did not use `ui-main-info` test cases/review/test-design artifacts as requirement sources.
- Did not expand to neighboring UI sections except direct navigation targets and PDF text before next section boundary.
- Mockups used only for visual/interaction inventory, not business rules.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Routed task | `ft-scope-analyzer` + PDF technical workflow selected | user request; `SKILL.md` |
| 2 | Read source selection and package notes | required inputs confirmed | `{SOURCE_SELECTION}`; `{AGENT_NOTES}` |
| 3 | Extracted DOCX sections/tables | sections `section-22`-`section-24`, tables 10/11 | `scope-contract.md`; `source-row-inventory.md` |
| 4 | Extracted and rendered PDF | pages 59-67; `GSR 123`-`GSR 148`; PDF-only CDI rows | `source-parity-check.md`; `tmp/pdfs/ui-employment/page-*.png` |
| 5 | Opened mockups | both target PNG files visually inspected | `mockup-visual-inventory.md` |
| 6 | Wrote handoff artifacts | manifest helper used | `artifact-sections/*.manifest.json` |
| 7 | Ran validator | final status reported in conversation | `workflow-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Scope boundary | `pass` | DOCX `section-22`-`section-24`; PDF pp.59-67 | reviewer checks PDF-only CDI inclusion |
| Source parity | `pass-with-extraction-risk` | PDF-only IDs and rows preserved | writer must preserve IDs/rows |
| Mockup opened | `pass` | `opened = yes` in inventory | writer must use hints only |
| Gap classification | `needs-review` | 4 non-blocking gaps | run `scope_gap_review` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Cyrillic query distortion in PowerShell here-string | PowerShell stdout/query literals for Russian search terms | Python extraction rerun with Unicode escape literals and UTF-8 environment | `n/a` | `n/a` | none; distorted stdout was not used as evidence | reviewer may verify anchors in parity/inventory |

## Handoff Notes For Next Session

- Run `prompt.scope-gaps-to-reviewer.md` first because gaps exist.
- Reviewer should focus on PDF-only `SRC-022`-`SRC-024` boundary and whether their inclusion is acceptable for writer.
- Writer must preserve `GSR 123`-`GSR 148` and must not invent integration/backend behavior.
"""


def decision_log() -> str:
    rows = [
        ["`DEC-001`", "1", "`source-boundary`", "DOCX resolve_sections", "Confirmed DOCX sections `section-22`-`section-24`", "These are the only DOCX sections matching `Сведения о занятости`", "`scope-contract.md`", "high", "applied"],
        ["`DEC-002`", "2", "`source-boundary`", "PDF pages 59-67", "Confirmed PDF boundary through p.67 before next section", "PDF contains subsection 2.1.1.1.1.2 and then starts `Анкета клиента`", "`source-parity-check.md`", "medium", "applied"],
        ["`DEC-003`", "3", "`traceability`", "PDF-only GSR numbers", "Preserve `GSR 123`-`GSR 148` as mandatory IDs", "AGENTS/source parity rules require PDF-only codes to be retained", "`source-parity-check.md`; `source-row-inventory.md`", "high", "applied"],
        ["`DEC-004`", "4", "`coverage`", "PDF-only CDI message text", "Include `SRC-022`-`SRC-024` as PDF-only in-scope rows", "They appear before the next section and explicitly state employment-stage UI messages", "`source-row-inventory.md`; `GAP-004`", "risk:review boundary check needed", "applied"],
        ["`DEC-005`", "5", "`gap`", "DaData/SPР/CDI/backend effects", "Keep integration/backend behavior as gaps unless observable", "Manual UI tests cannot prove hidden effects from source text alone", "`scope-coverage-gaps.md`", "medium", "applied"],
        ["`DEC-006`", "6", "`routing`", "4 non-blocking gaps", "Route to `ft-test-case-reviewer` mode `scope_gap_review` before writer", "Skill requires gap review prompt when `GAP-*` exists", "`workflow-state.yaml`", "high", "applied"],
    ]
    return f"""## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_15_clean_before_writer` |
| scope_slug | `ui-employment` |
| stage | `ft-scope-analyzer` |
| started_from | `{SOURCE_SELECTION}` |

## Decision Log

{md_table(["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"], rows)}
"""


def main() -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    write_artifact(HANDOFF_DIR / "scope-contract.md", "scope-contract", [(2, "Scope Contract", scope_contract())])
    write_artifact(HANDOFF_DIR / "source-parity-check.md", "source-parity-check", [(2, "Source Parity Check", source_parity_check())])
    write_artifact(HANDOFF_DIR / "source-row-inventory.md", "source-row-inventory", [(2, "Source Row Inventory", source_row_inventory())])
    write_artifact(HANDOFF_DIR / "mockup-visual-inventory.md", "mockup-visual-inventory", [(1, "Mockup Visual Inventory", mockup_visual_inventory())])
    write_artifact(HANDOFF_DIR / "scope-coverage-gaps.md", "scope-coverage-gaps", [(2, "Scope Coverage Gaps", gaps())])
    write_artifact(HANDOFF_DIR / "scope-clarification-requests.md", "scope-clarification-requests", [(2, "Scope Clarification Requests", clarification_requests())])
    for filename, content in prompts().items():
        write_artifact(HANDOFF_DIR / filename, filename.removesuffix(".md"), [(2, "Handoff Prompt", content)])
    write_artifact(HANDOFF_DIR / "scope-analyzer-session-log.md", "scope-analyzer-session-log", [(1, "Scope Analyzer Session Log", session_log(now))])
    write_artifact(HANDOFF_DIR / "agent-decision-log.md", "agent-decision-log", [(1, "Agent Decision Log", decision_log())])
    (HANDOFF_DIR / "workflow-state.yaml").write_text(workflow_state(), encoding="utf-8", newline="\n")
    print(f"generated scope handoff at {HANDOFF_DIR}")
    print(f"source_rows={len(ROWS)} gsr_count={len(req_ids())}")


if __name__ == "__main__":
    main()
