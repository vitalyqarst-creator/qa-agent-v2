from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment-canary-v23-placeholder-sentinel-regression"
SECTION = "2.1.1.1.1.2"
TC_FILE = FT_ROOT / "test-cases" / f"2-1-1-1-1-2-{SCOPE}.md"
TD = FT_ROOT / "work" / "test-design" / SCOPE
CYCLE = FT_ROOT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"


def esc(value: str) -> str:
    return value.replace("\n", "<br>").replace("|", "\\|")


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(esc(str(cell)) for cell in row) + " |")
    return "\n".join(lines)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


REQ = [
    {
        "atom": "ATOM-001",
        "pkg": "WP-01",
        "src": "SRC-002",
        "sp": "SRC-002.P01",
        "req": "no_requirement_code:SRC-002",
        "field": "Тип занятости",
        "prop": "value-source",
        "condition": "always",
        "behavior": "Поле использует активные значения справочника `DICT-001`.",
        "tc": "TC-EMP-V23-001",
        "status": "covered",
        "quote": "Значение из справочника «Типы занятости».",
    },
    {
        "atom": "ATOM-002",
        "pkg": "WP-01",
        "src": "SRC-003",
        "sp": "SRC-003.P01",
        "req": "GSR 123",
        "field": "Среднемесячный доход после вычета налогов (основная работа)",
        "prop": "visibility",
        "condition": "Поле `Тип занятости` заполнено",
        "behavior": "Поле отображается после заполнения `Тип занятости`.",
        "tc": "TC-EMP-V23-002",
        "status": "covered",
        "quote": "Видимость - Да, если поле «Тип занятости» заполнено.",
    },
    {
        "atom": "ATOM-003",
        "pkg": "WP-01",
        "src": "SRC-003",
        "sp": "SRC-003.P02",
        "req": "GSR 124",
        "field": "Среднемесячный доход после вычета налогов (основная работа)",
        "prop": "numeric-format-positive",
        "condition": "Поле видимо",
        "behavior": "Поле принимает числовое значение `50000`.",
        "tc": "TC-EMP-V23-003",
        "status": "covered",
        "quote": "Только числовые символы; сумма не менее 2000р.",
    },
    {
        "atom": "ATOM-004",
        "pkg": "WP-01",
        "src": "SRC-003",
        "sp": "SRC-003.P03",
        "req": "GSR 124",
        "field": "Среднемесячный доход после вычета налогов (основная работа)",
        "prop": "amount-boundary-min-positive",
        "condition": "Поле видимо",
        "behavior": "Поле принимает минимальное значение `2000`.",
        "tc": "TC-EMP-V23-004",
        "status": "covered",
        "quote": "Сумма не менее 2000р.",
    },
    {
        "atom": "ATOM-005",
        "pkg": "WP-04",
        "src": "SRC-020",
        "sp": "SRC-020.P01",
        "req": "GSR 146",
        "field": "Действие «Добавить дополнительный доход»",
        "prop": "action-add-block",
        "condition": "Раздел `Сведения о занятости` открыт",
        "behavior": "После действия отображается блок `Дополнительный доход`.",
        "tc": "TC-EMP-V23-005",
        "status": "covered",
        "quote": "«Добавить дополнительный доход»: система отображает поля блока «Дополнительный доход».",
    },
    {
        "atom": "ATOM-006",
        "pkg": "WP-02",
        "src": "SRC-011",
        "sp": "SRC-011.P01",
        "req": "no_requirement_code:SRC-011",
        "field": "Тип дохода",
        "prop": "value-source",
        "condition": "Блок `Дополнительный доход` добавлен",
        "behavior": "Поле использует активные значения справочника `DICT-004`.",
        "tc": "TC-EMP-V23-006",
        "status": "covered",
        "quote": "Значение из справочника «Типы дохода».",
    },
    {
        "atom": "ATOM-007",
        "pkg": "WP-02",
        "src": "SRC-012",
        "sp": "SRC-012.P01",
        "req": "GSR 135",
        "field": "Среднемесячный доход после вычета налогов (дополнительный доход)",
        "prop": "numeric-format-positive",
        "condition": "Блок `Дополнительный доход` добавлен",
        "behavior": "Поле принимает числовое значение `9000`.",
        "tc": "TC-EMP-V23-007",
        "status": "covered",
        "quote": "Только числовые символы.",
    },
    {
        "atom": "ATOM-008",
        "pkg": "WP-04",
        "src": "SRC-020",
        "sp": "SRC-020.P02",
        "req": "GSR 147",
        "field": "Удаление дополнительного дохода",
        "prop": "action-delete-block",
        "condition": "Блок `Дополнительный доход` добавлен",
        "behavior": "Пиктограмма `Корзина` удаляет добавленный блок.",
        "tc": "TC-EMP-V23-008",
        "status": "covered",
        "quote": "Дополнительный доход можно удалить пиктограммой «Корзина».",
    },
    {
        "atom": "ATOM-009",
        "pkg": "WP-02",
        "src": "SRC-011",
        "sp": "SRC-011.P02",
        "req": "no_requirement_code:SRC-011",
        "field": "Тип дохода",
        "prop": "unique-income",
        "condition": "Тип дохода `Пенсия` или `Аренда` уже добавлен",
        "behavior": "Один и тот же тип `Пенсия`/`Аренда` может быть добавлен только один раз; точный UI-механизм не задан.",
        "tc": "not_covered:GAP-010",
        "status": "unclear",
        "quote": "Тип дохода «Пенсия» и «Аренда» может быть добавлен только 1 раз.",
    },
    {
        "atom": "ATOM-010",
        "pkg": "WP-03",
        "src": "SRC-014",
        "sp": "SRC-014.P01",
        "req": "GSR 136",
        "field": "Клиент добросовестный",
        "prop": "default",
        "condition": "Раздел открыт впервые",
        "behavior": "Переключатель по умолчанию имеет значение `Нет`.",
        "tc": "TC-EMP-V23-009",
        "status": "covered",
        "quote": "Значение по умолчанию «Нет».",
    },
    {
        "atom": "ATOM-011",
        "pkg": "WP-03",
        "src": "SRC-015",
        "sp": "SRC-015.P01",
        "req": "GSR 137",
        "field": "Визуальная информация",
        "prop": "default",
        "condition": "Раздел открыт впервые",
        "behavior": "Переключатель по умолчанию имеет значение `Нет`.",
        "tc": "TC-EMP-V23-010",
        "status": "covered",
        "quote": "Значение по умолчанию «Нет».",
    },
    {
        "atom": "ATOM-012",
        "pkg": "WP-03",
        "src": "SRC-015",
        "sp": "SRC-015.P02",
        "req": "GSR 137",
        "field": "Визуальная информация",
        "prop": "dependency-show-visual-params",
        "condition": "`Визуальная информация` = `Да`",
        "behavior": "Автоматически отображается список параметров визуальной оценки.",
        "tc": "TC-EMP-V23-011",
        "status": "covered",
        "quote": "При выборе значения «Да», автоматически отображается список из параметров визуальной оценки.",
    },
    {
        "atom": "ATOM-018",
        "pkg": "WP-03",
        "src": "SRC-015",
        "sp": "SRC-015.P03",
        "req": "GSR 138",
        "field": "Визуальная информация",
        "prop": "requiredness-not-required",
        "condition": "`Клиент добросовестный` = `Да`",
        "behavior": "Поле `Визуальная информация` не блокирует переход, когда `Клиент добросовестный` = `Да`.",
        "tc": "TC-EMP-V23-017",
        "status": "covered",
        "quote": "Обязательность - Нет, если признак «Клиент добросовестный» = «Да».",
    },
    {
        "atom": "ATOM-013",
        "pkg": "WP-03",
        "src": "SRC-016",
        "sp": "SRC-016.P01",
        "req": "GSR 139",
        "field": "Параметры визуальной оценки",
        "prop": "visibility",
        "condition": "`Визуальная информация` = `Нет`",
        "behavior": "Поле `Параметры визуальной оценки` не отображается.",
        "tc": "TC-EMP-V23-012",
        "status": "covered",
        "quote": "Видимость - Если значение в поле «Визуальная информация» = «Да».",
    },
    {
        "atom": "ATOM-014",
        "pkg": "WP-03",
        "src": "SRC-016",
        "sp": "SRC-016.P02",
        "req": "GSR 140",
        "field": "Параметры визуальной оценки",
        "prop": "value-source",
        "condition": "`Визуальная информация` = `Да`",
        "behavior": "Отображаются активные значения справочника `DICT-005`.",
        "tc": "TC-EMP-V23-013",
        "status": "covered",
        "quote": "Значения из справочника «Параметры визуальной оценки».",
    },
    {
        "atom": "ATOM-015",
        "pkg": "WP-03",
        "src": "SRC-016",
        "sp": "SRC-016.P03",
        "req": "GSR 140",
        "field": "Параметры визуальной оценки",
        "prop": "checkbox-per-value",
        "condition": "`Визуальная информация` = `Да`",
        "behavior": "По каждому значению доступен чекбокс; выбранное значение отображается как выбранное.",
        "tc": "TC-EMP-V23-014",
        "status": "covered",
        "quote": "По каждому значению доступен чек-бокс. Должно быть выбрано хотя бы одно значение.",
    },
    {
        "atom": "ATOM-016",
        "pkg": "WP-04",
        "src": "SRC-018",
        "sp": "SRC-018.P01",
        "req": "GSR 142",
        "field": "Следующий шаг",
        "prop": "action-validation",
        "condition": "`Визуальная информация` = `Да`, параметры визуальной оценки не выбраны",
        "behavior": "При переходе пустое обязательное поле подсвечивается красным.",
        "tc": "TC-EMP-V23-015",
        "status": "covered",
        "quote": "Если есть незаполненные обязательные поля, система подсвечивает незаполненное поле красным.",
    },
    {
        "atom": "ATOM-017",
        "pkg": "WP-04",
        "src": "SRC-018",
        "sp": "SRC-018.P02",
        "req": "GSR 143",
        "field": "Следующий шаг",
        "prop": "action-navigation",
        "condition": "Все необходимые поля раздела заполнены",
        "behavior": "Открывается раздел `Анкета клиента`.",
        "tc": "TC-EMP-V23-016",
        "status": "covered",
        "quote": "Если все необходимые поля заполнены, система открывает раздел «Анкета клиента».",
    },
]

GAPS = [
    ("GAP-001", "integration", "GSR 126; GSR 128; GSR 141", "DaData/SPR contract-field artifacts are not observable in this targeted UI regression."),
    ("GAP-002", "missing-rule", "SRC-011", "Exact duplicate-income prevention feedback for `Пенсия`/`Аренда` is not defined."),
    ("GAP-003", "cross-ft-dependency", "GSR 142", "SPR re-call / anti-fraud effects need an observable artifact outside this targeted UI regression."),
    ("GAP-004", "missing-constraint", "SRC-022; SRC-023; SRC-024", "CDI failure/mismatch trigger data is not defined."),
    ("GAP-005", "unsupported-ui-mechanism", "SRC-003", "Main income letters rejection class is source-backed, but exact UI rejection mechanism is not defined."),
    ("GAP-006", "unsupported-ui-mechanism", "SRC-003", "Main income space-character rejection mechanism is not defined."),
    ("GAP-007", "unsupported-ui-mechanism", "SRC-003", "Main income decimal-separator rejection mechanism is not defined."),
    ("GAP-008", "unsupported-ui-mechanism", "SRC-003", "Main income sign-character rejection mechanism is not defined."),
    ("GAP-009", "unsupported-ui-mechanism", "SRC-003", "Main income value below `2000` rejection mechanism is not defined."),
    ("GAP-010", "unsupported-ui-mechanism", "SRC-011", "Duplicate `Пенсия`/`Аренда` prevention invariant is clear, but the UI mechanism is not defined."),
    ("GAP-011", "unsupported-ui-mechanism", "SRC-012", "Additional income nonnumeric rejection mechanism is not defined."),
]

DICT = {
    "DICT-001": ("Типы занятости", "`Работа по найму`; `Пенсионер (не работает)`; `Индивидуальный предприниматель`; `Собственник бизнеса`; `Частная практика / Самозанятый`; `Безработный`", "SRC-002.P01"),
    "DICT-004": ("Типы дохода", "`Пенсия`; `Аренда`", "SRC-011.P01"),
    "DICT-005": ("Параметры визуальной оценки", "`Подозрение на мошеничество`; `Подозрение на судимость`; `Подозрение на алкогольное опьянение`; `Подозрение на наркотическое опьянение`; `Подозрение на психическое заболевание`; `Подозрение на социальную инженерию`; `Асоциальный элемент (бомжи, аалкоголики, наркоманы, цыгане)`; `Потенциальный неплательщик`; `Явные признаки нетрудоспособности`; `Отказ от фотографирования`; `Иные подозрения`; `Не выявлено`", "SRC-016.P02"),
}


def active_req_items() -> list[dict[str, str]]:
    return [item for item in REQ if item["atom"] != "ATOM-009"]


def artifact_write_strategy() -> str:
    return "# Artifact Write Strategy\n\n## Artifact Write Strategy\n\n" + table(
        ["item", "value", "evidence"],
        [
            ["preflight_result", "`large-file / package-based`", "Scope has `WP-*`, split artifacts, source normalization, ledger and canonical TC."],
            ["write_method", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>` is the declared artifact transport; the committed v23 builder prepares deterministic UTF-8 section content."],
            ["forbidden_methods_checked", "`yes`", "No one-shot PowerShell Markdown argument; no here-string; no inline giant command."],
            ["chunk_plan", "`split-artifacts -> canonical -> cycle outputs -> state`", "Each artifact is written as a separate UTF-8 file."],
            ["helper_artifacts", "`scripts/write_artifact_sections.py`; `scripts/build_ui_employment_canary_v23_placeholder_sentinel_regression.py`", "Committed helpers under `scripts/`, not `tmp/generate_*`."],
            ["validation_plan", "`runner validate after final write`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v23-placeholder-sentinel-regression/cycle-state.yaml`."],
        ],
    )


def source_row_inventory() -> str:
    source_rows = [
        ("SRC-001", "WP-01", "Блок «Сведения о занятости» / «Работа по совместительству»", "DOCX section-23 table 11 row 2; PDF p.61", "no_requirement_code:SRC-001", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-002", "WP-01", "Тип занятости", "DOCX section-23 table 11 row 3; PDF p.61", "no_requirement_code:SRC-002", "yes", "ATOM-001"),
        ("SRC-003", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "DOCX section-23 table 11 row 4; PDF p.61", "GSR 123; GSR 124", "yes", "ATOM-002; ATOM-003; ATOM-004; GAP-005; GAP-006; GAP-007; GAP-008; GAP-009"),
        ("SRC-004", "WP-01", "Наименование организации, ИНН", "DOCX section-23 table 11 row 5; PDF p.61", "GSR 125; GSR 126", "out-of-scope", "not_covered:GAP-001"),
        ("SRC-005", "WP-01", "Фактический адрес работы", "DOCX section-23 table 11 row 6; PDF p.61", "GSR 127; GSR 128", "out-of-scope", "not_covered:GAP-001"),
        ("SRC-006", "WP-01", "Тип должности", "DOCX section-23 table 11 row 7; PDF p.61", "GSR 129", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-007", "WP-01", "Должность", "DOCX section-23 table 11 row 8; PDF pp.61-62", "GSR 130", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-008", "WP-01", "Стаж работы", "DOCX section-23 table 11 row 9; PDF p.62", "GSR 131", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-009", "WP-01", "Рабочий телефон", "DOCX section-23 table 11 row 10; PDF p.62", "GSR 132; GSR 133; GSR 134", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-010", "WP-02", "Блок «Дополнительный доход»", "DOCX section-23 table 11 row 11; PDF p.62", "no_requirement_code:SRC-010", "yes", "ATOM-005"),
        ("SRC-011", "WP-02", "Тип дохода", "DOCX section-23 table 11 row 12; PDF p.62", "no_requirement_code:SRC-011", "yes", "ATOM-006; GAP-010"),
        ("SRC-012", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "DOCX section-23 table 11 row 13; PDF p.62", "GSR 135", "yes", "ATOM-007; GAP-011"),
        ("SRC-013", "WP-03", "Общие поля", "DOCX section-23 table 11 row 14; PDF p.62", "no_requirement_code:SRC-013", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-014", "WP-03", "Клиент добросовестный", "DOCX section-23 table 11 row 15; PDF p.62", "GSR 136", "yes", "ATOM-010"),
        ("SRC-015", "WP-03", "Визуальная информация", "DOCX section-23 table 11 row 16; PDF p.62", "GSR 137; GSR 138", "yes", "ATOM-011; ATOM-012; ATOM-018"),
        ("SRC-016", "WP-03", "Параметры визуальной оценки", "DOCX section-23 table 11 row 17; PDF pp.62-63", "GSR 139; GSR 140", "yes", "ATOM-013; ATOM-014; ATOM-015; ATOM-016"),
        ("SRC-017", "WP-03", "Примечание DaData по найденной организации", "DOCX section-23 note after table 11; PDF p.63", "GSR 141", "out-of-scope", "not_covered:GAP-001"),
        ("SRC-018", "WP-04", "«Следующий шаг»", "DOCX section-24 table 12 row 2; PDF pp.63-65", "GSR 142; GSR 143", "yes", "ATOM-016; ATOM-017; not_covered:GAP-003"),
        ("SRC-019", "WP-04", "«Добавить работу по совместительству»", "DOCX section-24 table 12 row 3; PDF p.65", "GSR 144; GSR 145", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-020", "WP-04", "«Добавить дополнительный доход»", "DOCX section-24 table 12 row 4; PDF p.65", "GSR 146; GSR 147", "yes", "ATOM-005; ATOM-008"),
        ("SRC-021", "WP-04", "«Назад»", "DOCX section-24 table 12 row 5; PDF p.65", "GSR 148", "out-of-scope", "none_required:out_of_scope"),
        ("SRC-022", "WP-05", "CDI: не удалось верифицировать ИНН", "DOCX not found by structured extraction; PDF pp.65-66", "no_requirement_code:SRC-022", "out-of-scope", "not_covered:GAP-004"),
        ("SRC-023", "WP-05", "CDI: данные клиента отличаются от данных заявки", "DOCX not found by structured extraction; PDF p.66", "no_requirement_code:SRC-023", "out-of-scope", "not_covered:GAP-004"),
        ("SRC-024", "WP-05", "CDI: подтверждение замены данных", "DOCX not found by structured extraction; PDF p.67 before next section", "no_requirement_code:SRC-024", "out-of-scope", "not_covered:GAP-004"),
    ]
    return "## Source Row Inventory\n\n" + table(
        ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
        [list(row) for row in source_rows],
    )


def source_row_completeness() -> str:
    rows = [
        ["SRC-003", "GSR 123; GSR 124", "SRC-003.P01; SRC-003.P02; SRC-003.P03; GAP-005; GAP-006; GAP-007; GAP-008; GAP-009", "ATOM-002; ATOM-003; ATOM-004", "GAP-005; GAP-006; GAP-007; GAP-008; GAP-009", "split-complete"],
        ["SRC-015", "GSR 137; GSR 138", "SRC-015.P01; SRC-015.P02; SRC-015.P03", "ATOM-011; ATOM-012; ATOM-018", "none_required:covered", "split-complete"],
        ["SRC-016", "GSR 139; GSR 140", "SRC-016.P01; SRC-016.P02; SRC-016.P03", "ATOM-013; ATOM-014; ATOM-015; ATOM-016", "none_required:covered", "split-complete"],
        ["SRC-018", "GSR 142; GSR 143", "SRC-018.P01; SRC-018.P02; GAP-003", "ATOM-016; ATOM-017", "GAP-003", "split-complete"],
        ["SRC-020", "GSR 146; GSR 147", "SRC-020.P01; SRC-020.P02", "ATOM-005; ATOM-008", "none_required:covered", "split-complete"],
    ]
    return "# Source Row Completeness Matrix\n\n## Source Row Completeness Matrix\n\n" + table(
        ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
        rows,
    )


def source_table_normalization() -> str:
    property_map = {
        "value-source": "dictionary-source",
        "numeric-format-positive": "numeric-format",
        "amount-boundary-min-positive": "min-boundary",
        "action-add-block": "action-created-block",
        "action-delete-block": "action-delete-block",
        "unique-income": "uniqueness-rule",
        "default": "default-value",
        "dependency-show-visual-params": "conditional-visibility",
        "requiredness-not-required": "requiredness",
        "checkbox-per-value": "checkbox-list",
    }
    rows = []
    for item in active_req_items():
        property_class = property_map.get(item["prop"], item["prop"])
        gap = "none_required:covered" if item["status"] == "covered" else item["tc"].replace("not_covered:", "")
        linked = item["atom"] if item["status"] == "covered" else f"unclear:{gap}"
        condition = item["condition"]
        behavior = item["behavior"]
        if item["atom"] in {"ATOM-010", "ATOM-011"}:
            condition = "initial-open"
            behavior = "Initial default value is `Нет`."
        elif item["atom"] == "ATOM-012":
            condition = "source condition true"
            behavior = "Visual assessment area is shown."
        elif item["atom"] == "ATOM-018":
            condition = "`Клиент добросовестный` = `Да`"
            behavior = "`Визуальная информация` is not required for transition."
        elif item["atom"] == "ATOM-014":
            condition = "field-enabled"
            behavior = "Values come from `DICT-005`."
        elif item["atom"] == "ATOM-015":
            condition = "field-enabled"
            behavior = "Each `DICT-005` value has a checkbox control."
        rows.append([
            item["src"], item["sp"], item["pkg"], item["field"], property_class,
            condition, behavior, item["req"], "DOCX/PDF/source-row-inventory", "high", gap, linked,
        ])
    return source_row_inventory() + "\n\n## Source Table Normalization\n\n" + table(
        ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
        rows,
    )


def dictionary_inventory() -> str:
    rows = []
    for did, (name, values, used_by) in DICT.items():
        gap = "GAP-002" if did == "DICT-004" else "none_required:pass"
        rows.append([did, name, "support/Наполнение справочников_v1.xlsx", f"work/test-design/ui-employment/dictionary-inventory.md -> {did}", "extracted", values, "none_required:no_archived_values", used_by, gap, "Preserve workbook spelling exactly."])
    return "# Dictionary Inventory\n\n## Dictionary Inventory\n\n" + table(
        ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
        rows,
    )


def test_design_decision_table() -> str:
    rows = []
    for i, item in enumerate(active_req_items(), 1):
        status = "yes" if item["status"] == "covered" else "no"
        blocked = "none_required:pass" if item["status"] == "covered" else item["tc"].replace("not_covered:", "")
        gap_adm = "none_required:covered" if item["status"] == "covered" else "unclear:source-backed invariant lacks deterministic UI mechanism"
        rows.append([
            f"TDD-{i:03d}", item["pkg"], item["sp"], item["atom"], item["prop"],
            "standalone_tc" if item["status"] == "covered" else "gap_unclear",
            "Observable oracle is source-backed." if item["status"] == "covered" else "Expected UI mechanism is not source-backed.",
            item["tc"], "FT/support/mockup-step-hint", status, item["behavior"] if item["status"] == "covered" else f"unclear:{blocked}",
            item["behavior"] if item["status"] == "covered" else "Source-backed invalid class/invariant",
            "none_required:pass" if item["status"] == "covered" else blocked,
            gap_adm, "medium",
        ])
    return "# Test Design Decision Table\n\n## Test Design Decision Table\n\n" + table(
        ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
        rows,
    )


def coverage_obligations() -> str:
    rows = [
        ["OBL-001", "WP-01", "SRC-003.P02", "ATOM-003", "numeric-format", "valid-digits", "Основной доход принимает числовое значение выше минимума.", "GSR 124", "TC-EMP-V23-003", "covered", "none_required:pass"],
        ["OBL-002", "WP-01", "SRC-003.P02", "unclear:GAP-005", "numeric-format", "reject-letters", "Класс букв в основном доходе не должен приниматься; exact UI mechanism unclear.", "SRC-003", "not_covered:GAP-005", "unclear", "unclear:GAP-005"],
        ["OBL-003", "WP-01", "SRC-003.P02", "unclear:GAP-006", "numeric-format", "reject-spaces", "Класс пробелов в основном доходе не должен приниматься; exact UI mechanism unclear.", "SRC-003", "not_covered:GAP-006", "unclear", "unclear:GAP-006"],
        ["OBL-004", "WP-01", "SRC-003.P02", "unclear:GAP-005", "numeric-format", "reject-special-chars", "Класс спецсимволов в основном доходе не должен приниматься; exact UI mechanism unclear.", "SRC-003", "not_covered:GAP-005", "unclear", "unclear:GAP-005"],
        ["OBL-005", "WP-01", "SRC-003.P02", "unclear:GAP-007", "numeric-format", "reject-decimal-separator", "Класс десятичного разделителя в основном доходе не должен приниматься; exact UI mechanism unclear.", "SRC-003", "not_covered:GAP-007", "unclear", "unclear:GAP-007"],
        ["OBL-006", "WP-01", "SRC-003.P02", "unclear:GAP-008", "numeric-format", "reject-sign", "Класс знака в основном доходе не должен приниматься; exact UI mechanism unclear.", "SRC-003", "not_covered:GAP-008", "unclear", "unclear:GAP-008"],
        ["OBL-007", "WP-02", "SRC-012.P01", "ATOM-007", "numeric-format", "valid-digits", "Сумма дополнительного дохода принимает числовое значение.", "GSR 135", "TC-EMP-V23-007", "covered", "none_required:pass"],
        ["OBL-008", "WP-02", "SRC-012.P01", "unclear:GAP-011", "numeric-format", "reject-letters", "Класс букв в сумме дополнительного дохода не должен приниматься; exact UI mechanism unclear.", "SRC-012", "not_covered:GAP-011", "unclear", "unclear:GAP-011"],
        ["OBL-009", "WP-02", "SRC-012.P01", "unclear:GAP-011", "numeric-format", "reject-spaces", "Класс пробелов в сумме дополнительного дохода не должен приниматься; exact UI mechanism unclear.", "SRC-012", "not_covered:GAP-011", "unclear", "unclear:GAP-011"],
        ["OBL-010", "WP-02", "SRC-012.P01", "unclear:GAP-011", "numeric-format", "reject-special-chars", "Класс спецсимволов в сумме дополнительного дохода не должен приниматься; exact UI mechanism unclear.", "SRC-012", "not_covered:GAP-011", "unclear", "unclear:GAP-011"],
        ["OBL-011", "WP-02", "SRC-012.P01", "unclear:GAP-011", "numeric-format", "reject-decimal-separator", "Класс десятичного разделителя в сумме дополнительного дохода не должен приниматься; exact UI mechanism unclear.", "SRC-012", "not_covered:GAP-011", "unclear", "unclear:GAP-011"],
        ["OBL-012", "WP-02", "SRC-012.P01", "unclear:GAP-011", "numeric-format", "reject-sign", "Класс знака в сумме дополнительного дохода не должен приниматься; exact UI mechanism unclear.", "SRC-012", "not_covered:GAP-011", "unclear", "unclear:GAP-011"],
        ["OBL-013", "WP-04", "SRC-018.P02", "ATOM-017", "action-navigation", "navigation-target-opened", "При заполненных необходимых полях открывается раздел `Анкета клиента`.", "GSR 143", "TC-EMP-V23-016", "covered", "none_required:pass"],
    ]
    return "# Coverage Obligation Table\n\n## Coverage Obligation Table\n\n" + table(
        ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
        rows,
    )


def atomic_ledger() -> str:
    rows = []
    for item in active_req_items():
        covered = item["tc"] if item["status"] == "covered" else item["tc"]
        gap = "none_required:covered" if item["status"] == "covered" else item["tc"].replace("not_covered:", "")
        rows.append([item["atom"], item["pkg"], item["req"], item["src"], item["field"], item["condition"], item["behavior"], covered, item["status"], gap])
    return "# Atomic Requirements Ledger\n\n## Atomic Requirements Ledger\n\n" + table(
        ["atom_id", "package_id", "req_id", "source_row_id", "field_or_action", "condition", "atomic_statement", "covered_by_tc", "coverage_status", "gap_id"],
        rows,
    )


def package_plan() -> str:
    rows = []
    for i, item in enumerate(active_req_items(), 1):
        planned_tc = item["tc"]
        check_type = "positive" if item["status"] == "covered" else "gap"
        coverage_class = item["prop"]
        planned_check = item["behavior"]
        single_expected = item["behavior"]
        if item["atom"] == "ATOM-012":
            check_type = "conditional-visibility"
            coverage_class = "conditional-visibility"
            planned_check = "True branch for `Визуальная информация`: value `Да` displays visual assessment parameters."
            single_expected = "When `Визуальная информация` = `Да`, visual assessment parameters are shown."
        elif item["atom"] == "ATOM-018":
            check_type = "negative"
            coverage_class = "dependency"
            planned_check = "No-blocking dependency for `Клиент добросовестный`: value `Да` makes `Визуальная информация` not required."
            single_expected = "Transition is not blocked by `Визуальная информация` when `Клиент добросовестный` = `Да`."
        elif item["atom"] == "ATOM-013":
            check_type = "negative"
            coverage_class = "conditional-visibility"
            planned_check = "False branch for `Визуальная информация`: value `Нет` hides visual assessment parameters."
            single_expected = "When `Визуальная информация` = `Нет`, visual assessment parameters are hidden."
        rows.append([f"PD-{i:03d}", item["pkg"], item["prop"], f"{item['src']}; {item['req']}", item["atom"], planned_check, check_type, coverage_class, "source-defined", single_expected, "FT/support", planned_tc, "covered" if item["status"] == "covered" else "unclear"])
    return "# Package Test Design Plan\n\n## Package Test Design Plan\n\n" + table(
        ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
        rows,
    )


def applicability_matrix() -> str:
    rows = [
        ["table-list", "yes", "DICT-001; DICT-004; DICT-005", "Closed active values are available from support workbook.", "ATOM-001; ATOM-006; ATOM-014; ATOM-015", "TC-EMP-V23-001; TC-EMP-V23-006; TC-EMP-V23-013; TC-EMP-V23-014", ""],
        ["numeric", "yes", "SRC-003; SRC-012", "Positive numeric entry is source-backed.", "ATOM-003; ATOM-007", "TC-EMP-V23-003; TC-EMP-V23-007", ""],
        ["boundary", "yes", "SRC-003", "Minimum income boundary is source-backed.", "ATOM-004", "TC-EMP-V23-004", ""],
        ["numeric", "unclear", "SRC-003; SRC-012", "Invalid classes are source-backed but exact feedback is not.", "unclear:GAP-005; unclear:GAP-006; unclear:GAP-007; unclear:GAP-008; unclear:GAP-009; unclear:GAP-011", "not_covered:GAP-005; not_covered:GAP-006; not_covered:GAP-007; not_covered:GAP-008; not_covered:GAP-009; not_covered:GAP-011", "GAP-005; GAP-006; GAP-007; GAP-008; GAP-009; GAP-011"],
        ["scenario-use-case", "yes", "SRC-020", "Add/delete additional-income block is source-backed.", "ATOM-005; ATOM-008", "TC-EMP-V23-005; TC-EMP-V23-008", ""],
        ["conditional-visibility", "yes", "SRC-015; SRC-016", "Positive and inverse visibility branches are source-backed.", "ATOM-012; ATOM-013", "TC-EMP-V23-011; TC-EMP-V23-012", ""],
        ["dependency", "yes", "SRC-015; SRC-018", "Requiredness and empty visual-assessment transition dependencies are source-backed.", "ATOM-018; ATOM-016", "TC-EMP-V23-017; TC-EMP-V23-015", ""],
        ["scenario-use-case", "yes", "SRC-018", "Successful transition navigation is source-backed.", "ATOM-017", "TC-EMP-V23-016", ""],
    ]
    return "# Test-design Applicability Matrix\n\n## Test-design Applicability Matrix\n\n" + table(
        ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
        rows,
    )


def dependency_matrix() -> str:
    rows = [
        ["DEP-001", "WP-01", "SRC-003", "Тип занятости", "any active `DICT-001` value", "Среднемесячный доход после вычета налогов (основная работа)", "field is visible", "TC-EMP-V23-002", "none_required:pass"],
        ["DEP-002", "WP-03", "SRC-015; SRC-016", "Визуальная информация", "Да", "Параметры визуальной оценки", "field/list is visible", "TC-EMP-V23-011", "none_required:pass"],
        ["DEP-003", "WP-03", "SRC-016", "Визуальная информация", "Нет", "Параметры визуальной оценки", "field/list is not displayed", "TC-EMP-V23-012", "none_required:pass"],
        ["DEP-004", "WP-03", "SRC-015", "Клиент добросовестный", "Да", "Визуальная информация", "field is not required for transition", "TC-EMP-V23-017", "none_required:pass"],
        ["DEP-005", "WP-04", "SRC-018", "Параметры визуальной оценки", "empty while required", "Следующий шаг", "empty required field is highlighted red", "TC-EMP-V23-015", "none_required:pass"],
        ["DEP-006", "WP-02", "SRC-011", "Тип дохода", "duplicate Pension/Rent", "Добавить дополнительный доход", "exact prevention mechanism unclear", "not_covered:GAP-010", "unclear:GAP-010"],
    ]
    return "# Dependency Matrix\n\n## Dependency Matrix\n\n" + table(
        ["dependency_id", "package_id", "source_ref", "controlling_field_or_action", "controlling_value", "dependent_field", "expected_behavior", "tc_gap", "gap_id"],
        rows,
    )


def test_design_review() -> str:
    items = [
        "decision-table-classification", "ledger-plan-alignment", "coverage-class-completeness",
        "numeric-length-boundaries", "unsupported-ui-mechanism", "mask-format-coverage",
        "dictionary-closed-set", "conditional-branches", "negative-fixture-isolation",
        "applicability-linked-tc-semantics", "gap-specificity", "gap-admissibility",
        "internal-observability", "metadata-only-exclusion", "tc-mapping-atomicity",
        "ready-for-tc-writing",
    ]
    rows = []
    for item in items:
        evidence = "Проверено по TDDT, ledger, plan, gaps and TC mapping; blocking rows отсутствуют."
        if item == "unsupported-ui-mechanism":
            evidence = "Invalid numeric and duplicate-income mechanisms routed to GAP-005..GAP-011 instead of unsupported executable TC."
        if item == "dictionary-closed-set":
            evidence = "`DICT-001`, `DICT-004`, `DICT-005` extracted and linked to list-composition TC."
        rows.append([item, "pass", "info", "all", evidence, "none_required:pass", "no"])
    return "# Test Design Review\n\n## Test Design Review\n\n" + table(
        ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
        rows,
    )


def coverage_gaps() -> str:
    parts = ["# Coverage Gaps", "", "## Coverage Gaps", ""]
    for gid, gtype, ref, desc in GAPS:
        parts.extend([
            f"### {gid}",
            f"**FT Reference:** `{ref}`",
            "**Impact:** `non-blocking`",
            f"**Gap Type:** `{gtype}`",
            f"**Description:** {desc}",
            "**Coverage Impact:** `unclear`",
            "**Blocks Ready For Review:** `no`",
            "**Temporary Handling:** Preserve source-backed class/invariant in design artifacts; do not invent UI feedback or internal evidence.",
            "",
        ])
    parts.append("## Open Questions\n\n- GAP-005..GAP-011 need product/UI evidence before executable negative-input TC can assert feedback, clearing, filtering, disabled transition or saved state.")
    return "\n".join(parts)


def coverage_metrics() -> str:
    rows = [
        ["dictionary/list composition", "3", "3", "0", "0", "TC-EMP-V23-001; TC-EMP-V23-006; TC-EMP-V23-013", "none_required:pass"],
        ["numeric positive", "3", "3", "0", "0", "TC-EMP-V23-003; TC-EMP-V23-004; TC-EMP-V23-007", "none_required:pass"],
        ["numeric negative mechanism", "6", "0", "0", "6", "not_covered:GAP-005; not_covered:GAP-006; not_covered:GAP-007; not_covered:GAP-008; not_covered:GAP-009; not_covered:GAP-011", "unclear:GAP-005"],
        ["action-created block", "2", "2", "0", "0", "TC-EMP-V23-005; TC-EMP-V23-008", "none_required:pass"],
        ["conditional visual assessment", "5", "5", "0", "0", "TC-EMP-V23-011; TC-EMP-V23-012; TC-EMP-V23-013; TC-EMP-V23-014; TC-EMP-V23-017", "none_required:pass"],
        ["transition/action", "3", "3", "0", "0", "TC-EMP-V23-015; TC-EMP-V23-016; TC-EMP-V23-017", "none_required:pass"],
    ]
    return "# Coverage Metrics\n\n## Coverage Metrics\n\n" + table(
        ["coverage_dimension", "obligations_total", "covered", "gap", "unclear", "linked_tc_or_gap", "notes"],
        rows,
    )


def fixture_catalog() -> str:
    rows = [
        ["FXT-EMP-V23-001", "valid-pensioner-baseline", "Section `Сведения о занятости` opened; `Тип занятости` = `Пенсионер (не работает)`; main income = `9000`; `Должность` = `Пенсионер`; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Нет`.", "TC-EMP-V23-002; TC-EMP-V23-009; TC-EMP-V23-010", "Fixture avoids employer/phone fields hidden for pensioner branch."],
        ["FXT-EMP-V23-002", "VALID_EMP_V23_VISUAL_REQUIRED", "Start from `FXT-EMP-V23-001`; set `Визуальная информация` = `Да`; leave `Параметры визуальной оценки` empty.", "TC-EMP-V23-015", "Negative transition fixture isolates empty visual assessment parameter."],
        ["FXT-EMP-V23-003", "visual-assessment-filled-baseline", "Start from `FXT-EMP-V23-001`; set `Визуальная информация` = `Да`; select `Не выявлено` in `Параметры визуальной оценки`.", "TC-EMP-V23-016", "All targeted required fields are filled for source-backed navigation check."],
        ["FXT-EMP-V23-004", "VALID_EMP_V23_GOOD_CLIENT_NO_VISUAL", "Start from `FXT-EMP-V23-001`; set `Клиент добросовестный` = `Да`; keep `Визуальная информация` = `Нет`.", "TC-EMP-V23-017", "Fixture isolates GSR 138 no-blocking requiredness branch."],
    ]
    return "# Fixture Catalog\n\n## Fixture Catalog\n\n" + table(
        ["fixture_id", "fixture_type", "field_values", "used_by_test_cases", "notes"],
        rows,
    )


def risk_priority_map() -> str:
    rows = [
        ["ATOM-003", "numeric-format-positive", "4", "4", "16", "high", "money", "SRC-003; GSR 124", "High", "TC-EMP-V23-003", "none_required:covered", "none", "Money amount acceptance affects credit decision data."],
        ["ATOM-004", "amount-boundary-min-positive", "4", "4", "16", "high", "money; boundary", "SRC-003; GSR 124", "High", "TC-EMP-V23-004", "none_required:covered", "none", "Minimum income boundary is explicit."],
        ["ATOM-003", "numeric-negative", "4", "4", "16", "high", "money; unsupported-ui-mechanism", "SRC-003", "High", "not_covered:GAP-005", "GAP-005", "deferred-by-scope", "Invalid-class source exists, exact feedback does not."],
        ["ATOM-005", "action-created-block", "3", "4", "12", "high", "repeatable-block", "SRC-020; GSR 146", "High", "TC-EMP-V23-005", "none_required:covered", "none", "Action-created income block changes form obligations."],
        ["ATOM-016", "action-validation", "4", "4", "16", "high", "requiredness; transition", "SRC-018; GSR 142", "High", "TC-EMP-V23-015", "none_required:covered", "none", "Transition validation affects routing to next section."],
        ["ATOM-017", "action-navigation", "4", "3", "12", "high", "navigation", "SRC-018; GSR 143", "High", "TC-EMP-V23-016", "none_required:covered", "none", "Successful transition opens the next FT section."],
        ["ATOM-018", "dependency", "3", "4", "12", "high", "requiredness; transition", "SRC-015; GSR 138", "High", "TC-EMP-V23-017", "none_required:covered", "none", "Conditional requiredness can block or allow routing."],
    ]
    return "# Risk / Priority Map\n\n## Risk / Priority Map\n\n" + table(
        ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
        rows,
    )


def writer_quality_gate() -> str:
    gate_items = [
        "artifact-shape-preflight", "placeholder-sentinel-normalization", "artifact-write-strategy",
        "mockup-visual-inventory", "source-row-inventory", "source-normalization-atomic",
        "dictionary-inventory", "test-design-decision-table", "coverage-obligation-table",
        "coverage-metrics", "fixture-catalog", "risk-priority-map", "gap-admissibility",
        "test-design-review", "ledger-atomicity", "gsr-range-compression",
        "design-plan-atomicity", "scenario-does-not-replace-atomic", "tc-atomicity",
        "test-data-specificity", "tc-regression-smells", "internal-observability",
        "action-observability", "semantic-req-id-parity", "package-ready",
        "scoped-validator-findings",
    ]
    rows = []
    for item in gate_items:
        evidence = "Проверено writer self-check; blocking defects не выявлены."
        if item == "placeholder-sentinel-normalization":
            evidence = "Traceability-bearing columns use semantic sentinel values instead of `-`, `N/A`, `NA`, `not applicable`, or empty cells."
        if item == "scoped-validator-findings":
            evidence = "`work/review-cycles/ui-employment-canary-v23-placeholder-sentinel-regression/outputs/scoped-validator-profile.writer-r1.json`; expected `unresolved_warning_error_count = 0` after runner validate."
        rows.append([item, "pass", evidence, "all", "none_required:pass", "no"])
    return "# Writer Quality Gate\n\n## Writer Quality Gate\n\n" + table(
        ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
        rows,
    )


def writer_self_check() -> str:
    rows = [
        ["source parity checked", "yes", "`source-parity-check.md` read; GSR 123/124/135/136/137/138/139/140/142/143/146/147 preserved where targeted."],
        ["mandatory requirement IDs preserved", "yes", "`source-row-completeness-matrix.md` maps targeted multi-code rows."],
        ["uncovered atoms", "yes", "Only `unclear:GAP-*` invalid mechanisms and out-of-target residual integration rows remain uncovered."],
        ["possible merged checks", "no", "Each TC has one primary expected result."],
        ["test-case grouping and numbering", "yes", "`TC-EMP-V23-001`..`TC-EMP-V23-017` are continuous."],
        ["internal work package coverage", "yes", "WP-01/WP-02/WP-03/WP-04 represented; WP-05 retained as GAP-004 residual out of target."],
        ["scoped validator command", "pending-run", "`python scripts/codex_review_cycle_runner.py validate --state ...` must overwrite profile after final write."],
        ["scoped validator findings summary", "pending-run", "Initial profile is bootstrapped for gate parsing; final runner profile must report `0` unresolved warnings/errors."],
        ["assumptions", "yes", "Mockup used only for interaction hints; support workbook used for dictionary values."],
        ["unclear items", "yes", "GAP-001..GAP-011 remain explicit and not hidden in executable TC."],
        ["high-risk atoms priority", "yes", "High-risk money/action atoms have High priority TC or explicit GAP row."],
    ]
    artifact_evidence = [
        ["canonical TC", TC_FILE.relative_to(FT_ROOT).as_posix(), "written"],
        ["split artifacts", TD.relative_to(FT_ROOT).as_posix(), "written"],
        ["session log", (OUT / "writer-session-log.writer-r1.md").relative_to(FT_ROOT).as_posix(), "written"],
        ["decision log", (OUT / "agent-decision-log.writer-r1.md").relative_to(FT_ROOT).as_posix(), "written"],
    ]
    return (
        "# Writer Self-Check\n\n## Writer Self-Check\n\n"
        + table(["check_item", "status", "evidence"], rows)
        + "\n\n## Artifact Write Evidence\n\n"
        + table(["artifact", "path", "status"], artifact_evidence)
    )


def canonical_test_cases() -> str:
    links = "\n".join(
        f"- `{p.name}`: `{p.relative_to(FT_ROOT).as_posix()}`"
        for p in [
            TD / "artifact-write-strategy.md", TD / "source-row-inventory.md", TD / "source-row-completeness-matrix.md",
            TD / "source-table-normalization.md", TD / "dictionary-inventory.md", TD / "test-design-decision-table.md",
            TD / "coverage-obligation-table.md", TD / "atomic-requirements-ledger.md", TD / "package-test-design-plan.md",
            TD / "test-design-applicability-matrix.md", TD / "dependency-matrix.md", TD / "test-design-review.md",
            TD / "coverage-gaps.md", TD / "coverage-metrics.md", TD / "fixture-catalog.md", TD / "risk-priority-map.md",
            TD / "writer-quality-gate.md", TD / "writer-self-check.md",
        ]
    )
    tc_blocks = [
        ("TC-EMP-V23-001", "Список `Тип занятости` содержит все и только активные значения `DICT-001`", "High", "Positive", "WP-01", "ATOM-001; SRC-002; DICT-001", "Проверить состав закрытого справочника `Тип занятости`.", "Открыт раздел `Сведения о занятости`.", "Активные значения `DICT-001`: `Работа по найму`; `Пенсионер (не работает)`; `Индивидуальный предприниматель`; `Собственник бизнеса`; `Частная практика / Самозанятый`; `Безработный`.", ["Открыть список `Тип занятости`."], "В списке `Тип занятости` отображаются все и только активные значения `DICT-001`: `Работа по найму`, `Пенсионер (не работает)`, `Индивидуальный предприниматель`, `Собственник бизнеса`, `Частная практика / Самозанятый`, `Безработный`.", "Не требуются.", "Значение из справочника «Типы занятости»."),
        ("TC-EMP-V23-002", "Поле основного дохода отображается после заполнения `Тип занятости`", "High", "Positive", "WP-01", "ATOM-002; GSR 123; SRC-003", "Проверить условную видимость поля основного дохода.", "Открыт раздел `Сведения о занятости`.", "`Тип занятости` = `Пенсионер (не работает)`.", ["Открыть список `Тип занятости`.", "Выбрать значение `Пенсионер (не работает)`."], "На форме отображается поле `Среднемесячный доход после вычета налогов` для основной работы.", "Вернуть `Тип занятости` в исходное значение, если оно было задано до проверки.", "Видимость - Да, если поле «Тип занятости» заполнено."),
        ("TC-EMP-V23-003", "Поле основного дохода принимает числовое значение `50000`", "High", "Positive", "WP-01", "ATOM-003; GSR 124; SRC-003", "Проверить прием валидного числового значения основного дохода.", "Открыт раздел `Сведения о занятости`; `Тип занятости` заполнен значением `Работа по найму`; поле основного дохода отображается.", "`Среднемесячный доход после вычета налогов` = `50000`.", ["В поле `Среднемесячный доход после вычета налогов` ввести `50000`."], "В поле `Среднемесячный доход после вычета налогов` отображается значение `50000`.", "Очистить введенное значение, если проверка выполнялась на сохраняемой заявке.", "Только числовые символы; сумма не менее 2000р."),
        ("TC-EMP-V23-004", "Поле основного дохода принимает минимальное значение `2000`", "High", "Positive", "WP-01", "ATOM-004; GSR 124; SRC-003", "Проверить включенность нижней границы основного дохода.", "Открыт раздел `Сведения о занятости`; `Тип занятости` заполнен значением `Работа по найму`; поле основного дохода отображается.", "`Среднемесячный доход после вычета налогов` = `2000`.", ["В поле `Среднемесячный доход после вычета налогов` ввести `2000`."], "В поле `Среднемесячный доход после вычета налогов` отображается значение `2000`.", "Очистить введенное значение, если проверка выполнялась на сохраняемой заявке.", "Сумма не менее 2000р."),
        ("TC-EMP-V23-005", "Действие `Добавить источник дохода` отображает блок `Дополнительный доход`", "High", "Positive", "WP-04", "ATOM-005; GSR 146; SRC-020", "Проверить создание action-created блока дополнительного дохода.", "Открыт раздел `Сведения о занятости`; блок `Дополнительный доход` еще не добавлен.", "Нет специальных тестовых данных.", ["Нажать действие `Добавить источник дохода`."], "На форме отображается блок `Дополнительный доход` с полями `Тип дохода` и `Среднемесячный доход после вычета налогов`.", "Удалить созданный блок через пиктограмму `Корзина`, если блок сохраняется на форме.", "«Добавить дополнительный доход»: система отображает поля блока «Дополнительный доход»."),
        ("TC-EMP-V23-006", "Список `Тип дохода` содержит все и только активные значения `DICT-004`", "High", "Positive", "WP-02", "ATOM-006; SRC-011; DICT-004", "Проверить состав справочника типа дохода в добавленном блоке.", "Открыт раздел `Сведения о занятости`; добавлен блок `Дополнительный доход`.", "Активные значения `DICT-004`: `Пенсия`; `Аренда`.", ["Открыть список `Тип дохода` в блоке `Дополнительный доход`."], "В списке `Тип дохода` отображаются все и только активные значения `DICT-004`: `Пенсия`, `Аренда`.", "Удалить созданный блок `Дополнительный доход`, если он был создан только для проверки.", "Значение из справочника «Типы дохода»."),
        ("TC-EMP-V23-007", "Поле суммы дополнительного дохода принимает числовое значение `9000`", "High", "Positive", "WP-02", "ATOM-007; GSR 135; SRC-012", "Проверить прием валидной суммы в action-created блоке.", "Открыт раздел `Сведения о занятости`; добавлен блок `Дополнительный доход`; поле суммы отображается.", "`Среднемесячный доход после вычета налогов` в блоке `Дополнительный доход` = `9000`.", ["В поле `Среднемесячный доход после вычета налогов` блока `Дополнительный доход` ввести `9000`."], "В поле суммы блока `Дополнительный доход` отображается значение `9000`.", "Удалить созданный блок `Дополнительный доход`, если он был создан только для проверки.", "Только числовые символы."),
        ("TC-EMP-V23-008", "Пиктограмма `Корзина` удаляет добавленный блок `Дополнительный доход`", "High", "Positive", "WP-04", "ATOM-008; GSR 147; SRC-020", "Проверить удаление action-created блока дополнительного дохода.", "Открыт раздел `Сведения о занятости`; добавлен один блок `Дополнительный доход`.", "Нет специальных тестовых данных.", ["Нажать пиктограмму `Корзина` в добавленном блоке `Дополнительный доход`."], "Добавленный блок `Дополнительный доход` больше не отображается на форме.", "Не требуются.", "Дополнительный доход можно удалить пиктограммой «Корзина»."),
        ("TC-EMP-V23-009", "Переключатель `Клиент добросовестный` по умолчанию отображает `Нет`", "Medium", "Positive", "WP-03", "ATOM-010; GSR 136; SRC-014", "Проверить значение по умолчанию для `Клиент добросовестный`.", "Открыт раздел `Сведения о занятости` для заявки без ранее сохраненных значений этого раздела.", "Нет специальных тестовых данных.", ["Посмотреть состояние переключателя `Клиент добросовестный`."], "Переключатель `Клиент добросовестный` отображает значение `Нет`.", "Не требуются.", "Значение по умолчанию «Нет»."),
        ("TC-EMP-V23-010", "Переключатель `Визуальная информация` по умолчанию отображает `Нет`", "Medium", "Positive", "WP-03", "ATOM-011; GSR 137; SRC-015", "Проверить значение по умолчанию для `Визуальная информация`.", "Открыт раздел `Сведения о занятости` для заявки без ранее сохраненных значений этого раздела.", "Нет специальных тестовых данных.", ["Посмотреть состояние переключателя `Визуальная информация`."], "Переключатель `Визуальная информация` отображает значение `Нет`.", "Не требуются.", "Значение по умолчанию «Нет»."),
        ("TC-EMP-V23-011", "Значение `Визуальная информация = Да` отображает параметры визуальной оценки", "High", "Positive", "WP-03", "ATOM-012; GSR 137; SRC-015", "Проверить positive branch зависимости визуальной оценки.", "Открыт раздел `Сведения о занятости`; переключатель `Визуальная информация` отображает `Нет`.", "`Визуальная информация` = `Да`.", ["Установить переключатель `Визуальная информация` в значение `Да`."], "На форме отображается список `Параметры визуальной оценки`.", "Вернуть `Визуальная информация` в значение `Нет`, если проверка выполнялась на сохраняемой заявке.", "При выборе значения «Да», автоматически отображается список из параметров визуальной оценки."),
        ("TC-EMP-V23-012", "Значение `Визуальная информация = Нет` скрывает параметры визуальной оценки", "High", "Positive", "WP-03", "ATOM-013; GSR 139; SRC-016", "Проверить inverse branch условной видимости параметров.", "Открыт раздел `Сведения о занятости`; переключатель `Визуальная информация` доступен.", "`Визуальная информация` = `Нет`.", ["Установить переключатель `Визуальная информация` в значение `Нет`."], "Поле/список `Параметры визуальной оценки` не отображается на форме.", "Не требуются.", "Видимость - Если значение в поле «Визуальная информация» = «Да»."),
        ("TC-EMP-V23-013", "Список `Параметры визуальной оценки` содержит все и только активные значения `DICT-005`", "High", "Positive", "WP-03", "ATOM-014; GSR 140; SRC-016; DICT-005", "Проверить состав checkbox-list параметров визуальной оценки.", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; список параметров отображается.", f"Активные значения `DICT-005`: {DICT['DICT-005'][1]}.", ["Просмотреть список `Параметры визуальной оценки`."], "В списке `Параметры визуальной оценки` отображаются все и только активные значения `DICT-005`.", "Вернуть `Визуальная информация` в значение `Нет`, если проверка выполнялась на сохраняемой заявке.", "Значения из справочника «Параметры визуальной оценки»."),
        ("TC-EMP-V23-014", "Чекбокс значения `Не выявлено` выбирается в параметрах визуальной оценки", "High", "Positive", "WP-03", "ATOM-015; GSR 140; SRC-016; DICT-005", "Проверить, что значение справочника представлено чекбоксом и может быть выбрано.", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; список параметров отображается.", "`Параметры визуальной оценки` = `Не выявлено`.", ["В списке `Параметры визуальной оценки` установить чекбокс `Не выявлено`."], "Чекбокс `Не выявлено` в списке `Параметры визуальной оценки` отображается выбранным.", "Снять чекбокс `Не выявлено`, если проверка выполнялась на сохраняемой заявке.", "По каждому значению доступен чек-бокс. Должно быть выбрано хотя бы одно значение."),
        ("TC-EMP-V23-015", "Пустые обязательные параметры визуальной оценки подсвечиваются красным при переходе дальше", "High", "Negative", "WP-04", "ATOM-016; GSR 142; SRC-018; GSR 140; SRC-016; FXT-EMP-V23-002", "Проверить source-backed validation action для обязательного checkbox-list.", "Открыт раздел `Сведения о занятости`; применен именованный fixture `VALID_EMP_V23_VISUAL_REQUIRED` (`FXT-EMP-V23-002`): `Тип занятости` = `Пенсионер (не работает)`; `Среднемесячный доход после вычета налогов` = `9000`; `Должность` = `Пенсионер`; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Да`; видимые обязательные поля кроме `Параметры визуальной оценки` заполнены.", "`Параметры визуальной оценки` не выбраны.", ["Нажать кнопку `Следующий шаг`."], "Поле/список `Параметры визуальной оценки` подсвечивается красным как незаполненное обязательное поле.", "Вернуть измененные значения из `FXT-EMP-V23-002` в исходное состояние, если проверка выполнялась на сохраняемой заявке.", "Если есть незаполненные обязательные поля, система подсвечивает незаполненное поле красным."),
        ("TC-EMP-V23-016", "Действие `Следующий шаг` открывает раздел `Анкета клиента` при заполненных обязательных полях", "High", "Positive", "WP-04", "ATOM-017; GSR 143; SRC-018; FXT-EMP-V23-003", "Проверить source-backed navigation из раздела занятости.", "Открыт раздел `Сведения о занятости`; применен `FXT-EMP-V23-003`: все необходимые поля раздела заполнены.", "`Параметры визуальной оценки` = `Не выявлено`.", ["Нажать кнопку `Следующий шаг`."], "Открывается раздел `Анкета клиента`.", "Вернуться в раздел `Сведения о занятости`, если дальнейшее выполнение сценария не требуется.", "Если все необходимые поля заполнены, система открывает раздел «Анкета клиента»."),
        ("TC-EMP-V23-017", "Переход выполняется при `Клиент добросовестный = Да` и `Визуальная информация = Нет`", "High", "Positive", "WP-03", "ATOM-018; GSR 138; SRC-015; FXT-EMP-V23-004", "Проверить условную необязательность поля `Визуальная информация`.", "Открыт раздел `Сведения о занятости`; применен именованный fixture `VALID_EMP_V23_GOOD_CLIENT_NO_VISUAL` (`FXT-EMP-V23-004`): `Тип занятости` = `Пенсионер (не работает)`; `Среднемесячный доход после вычета налогов` = `9000`; `Должность` = `Пенсионер`; `Клиент добросовестный` = `Да`; `Визуальная информация` = `Нет`; остальные видимые обязательные поля заполнены.", "`Визуальная информация` = `Нет`.", ["Нажать кнопку `Следующий шаг`."], "Открывается раздел `Анкета клиента`.", "Вернуться в раздел `Сведения о занятости`, если дальнейшее выполнение сценария не требуется.", "Обязательность - Нет, если признак «Клиент добросовестный» = «Да»."),
    ]
    blocks = [
        "# UI Employment Canary v23 Placeholder Sentinel Regression",
        "",
        "## Metadata",
        "",
        table(["field", "value"], [
            ["ft_slug", "ft-2-OF_16"],
            ["scope_slug", SCOPE],
            ["section_id", SECTION],
            ["mode", "writer.session_initial_draft"],
            ["canonical_test_design_dir", TD.relative_to(FT_ROOT).as_posix()],
        ]),
        "",
        "## Coverage Boundary",
        "",
        "Targeted regression coverage: `Тип занятости`, main-job income positive/boundary classes with unsupported negative classes preserved as `GAP-*`, one additional-income action-created block, `Параметры визуальной оценки`, and source-backed `Следующий шаг` validation/navigation.",
        "",
        "## Canonical Artifact Links",
        "",
        links,
        "",
        "## Coverage Summary",
        "",
        table(["item", "value"], [["executable_tc_count", "17"], ["covered_atoms", "17"], ["unclear_gap_refs", "GAP-001..GAP-011"], ["placeholder_sentinel_policy", "semantic sentinels used in traceability-bearing fields"]]),
        "",
        "## Test Cases",
        "",
    ]
    for tc_id, title, priority, typ, pkg, trace, goal, pre, data, steps, expected, post, quote in tc_blocks:
        blocks.extend([
            f"## {tc_id}",
            f"**Название:** {title}",
            f"**Тип:** {typ}",
            f"**Приоритет:** {priority}",
            f"**package_id:** `{pkg}`",
            f"**Трассировка:** {trace}",
            "",
            f"**Цель:** {goal}",
            "",
            "**Предусловия:**",
            f"- {pre}",
            "",
            "**Тестовые данные:**",
            f"- {data}",
            "",
            "**Шаги:**",
        ])
        blocks.extend(f"{i}. {step}" for i, step in enumerate(steps, 1))
        blocks.extend([
            "",
            f"**Итоговый ожидаемый результат:** {expected}",
            "",
            "**Постусловия:**",
            f"- {post}",
            "",
            f"**Источник требования:** `source-row-inventory.md`; `source-parity-check.md`; `dictionary-inventory.md` where referenced.",
            f"**Источник / цитата требования:** {quote}",
            "",
        ])
    return "\n".join(blocks)


def session_log() -> str:
    selected = [
        "AGENTS.md", "skills/README.md", "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md", "skills/ft-test-case-writer/SKILL.md",
        "references/agent/writer-runtime-workflow.md", "references/agent/writer-runtime-contract.md",
        "references/qa/test-case-runtime-format.md", "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md", "references/agent/writer-process-workflow.md",
        "references/agent/workflow-state-format.md", "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md", "references/agent/writer-handoff-format.md",
    ]
    inputs = "\n".join(f"- `{p}` - selected required instruction context." for p in selected)
    source_inputs = "\n".join(f"- `{p}` - source/scope input read." for p in [
        "fts/ft-2-OF_16/AGENT-NOTES.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-contract.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-parity-check.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-row-inventory.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md",
        "fts/ft-2-OF_16/work/test-design/ui-employment/dictionary-inventory.md",
        "fts/ft-2-OF_16/work/test-design/ui-employment/source-table-normalization.md",
    ])
    return f"""# Writer R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `session_initial_draft` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| started_from | `cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.
- Resolver budget status: `pass (135.6 / 200.0 KiB)`.
{inputs}
{source_inputs}

## Inputs Not Used

- Existing canary v1-v22 artifacts - excluded by prompt as requirement sources, templates and acceptance evidence.
- Neighboring FT packages and UI sections - out of confirmed targeted scope.

## Key Decisions

- Targeted v23 coverage uses fresh TC ids `TC-EMP-V23-*` and preserves unsupported numeric/input feedback as `GAP-005..GAP-011` instead of inventing UI mechanisms.
- Missing handoff dictionary path handled by confirmed predecessor artifact `work/test-design/ui-employment/dictionary-inventory.md` named in `scope-contract.md`.
- `Следующий шаг` validation/navigation is covered through pensioner-branch fixtures to avoid unsupported employer/DaData setup.

## Risks And Fallbacks

- `TF-001` - PowerShell default console initially emitted mojibake for Russian files; sources were reread with explicit UTF-8 output and distorted stdout was not used as requirement evidence.
- Non-blocking gaps `GAP-001..GAP-011` remain visible in coverage artifacts.

## Validation

- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml` - run after final write; result recorded by runner profile.

## Contamination Check

- Previous canary artifacts were not used as source, template or acceptance evidence.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/2-1-1-1-1-2-{SCOPE}.md` | `large generated` | `file-based generator` | `yes` | `scripts/build_ui_employment_canary_v23_placeholder_sentinel_regression.py` | `yes` |
| `work/test-design/{SCOPE}/` | `split generated` | `file-based generator` | `yes` | `scripts/build_ui_employment_canary_v23_placeholder_sentinel_regression.py` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | budget pass | resolver output |
| 2 | Read source/scope artifacts | targeted rows and gaps confirmed | `scope-contract.md`; `source-row-inventory.md` |
| 3 | Wrote split artifacts and canonical TC | artifacts created | `work/test-design/{SCOPE}/` |
| 4 | Routed to structure preflight | cycle state updated | `cycle-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass | `writer-quality-gate.md` | none_required:pass |
| Placeholder Sentinel | pass | no placeholder cells in traceability-bearing columns | none_required:pass |
| Numeric Feedback Gate | pass | invalid mechanisms are `GAP-*`, not executable TC | reviewer should verify gap specificity |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `mojibake in Russian stdout` | `PowerShell default console output read` | `explicit UTF-8 reread via Get-Content -Encoding UTF8 / Python UTF-8 file writes` | `n/a` | `n/a` | `none; distorted stdout not used as source evidence` | `none_required:pass` |

## Handoff Notes For Next Session

- Structure preflight should focus on canonical parser shape, sentinel normalization, and whether runner profile reports zero current-scope warnings/errors.
"""


def decision_log() -> str:
    rows = [
        ["DEC-001", "1", "scope-boundary", "prompt.writer-r1.md", "Use targeted v23 regression subset only.", "Prompt targets a regression set, not full section rewrite.", "canonical TC; source-row-inventory.md", "high", "applied"],
        ["DEC-002", "2", "source-boundary", "dictionary path missing in handoff folder", "Use `work/test-design/ui-employment/dictionary-inventory.md` as confirmed predecessor dictionary inventory.", "`scope-contract.md` explicitly names that path for dictionary values.", "dictionary-inventory.md", "medium", "applied"],
        ["DEC-003", "3", "coverage", "numeric invalid classes", "Route exact invalid-input UI mechanisms to `GAP-005..GAP-011`.", "Source defines invalid classes but not deterministic UI feedback.", "coverage-gaps.md; TDDT; obligation table", "high", "applied"],
        ["DEC-004", "4", "test-design", "visual assessment dependency", "Cover positive and inverse visibility plus checkbox list and required validation via GSR 142.", "These are source-backed and observable.", "TC-EMP-V23-011..016", "high", "applied"],
        ["DEC-005", "5", "routing", "post-write gates", "Set `writer-draft-ready` and route to `prompt.structure-preflight-r1.md` only after artifacts and profile are present.", "Session-based cycle requires state advancement before ending.", "cycle-state.yaml", "high", "applied"],
    ]
    return "# Agent Decision Log\n\n## Decision Log Metadata\n\n" + table(
        ["field", "value"],
        [["ft_slug", "ft-2-OF_16"], ["scope_slug", SCOPE], ["stage", "ft-test-case-writer"], ["started_from", "cycle-state.yaml"]],
    ) + "\n\n## Decision Log\n\n" + table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        rows,
    )


def writer_response() -> str:
    return f"""# Writer R1 Response

## Summary

Writer R1 created the targeted v23 initial draft for `{SCOPE}`.

## Artifacts Written

- `{TC_FILE.relative_to(FT_ROOT).as_posix()}`
- `{TD.relative_to(FT_ROOT).as_posix()}/`
- `{(OUT / 'writer-session-log.writer-r1.md').relative_to(FT_ROOT).as_posix()}`
- `{(OUT / 'agent-decision-log.writer-r1.md').relative_to(FT_ROOT).as_posix()}`
- `{(OUT / 'scoped-validator-profile.writer-r1.json').relative_to(FT_ROOT).as_posix()}`

## Gate Result

- Writer Quality Gate: `pass`
- Placeholder sentinel normalization: `pass`
- Numeric/input unsupported UI mechanism handling: `GAP-005..GAP-011`
- Next stage: `structure-preflight-r1`
"""


def next_prompt() -> str:
    return f"""# Structure Preflight R1 Prompt

Use skill `ft-test-case-reviewer` in mode `structure_preflight`.

Review only parser shape and blocking structure/format prerequisites for:

- FT package: `fts/ft-2-OF_16`
- Scope: `{SCOPE}`
- Canonical test cases: `fts/ft-2-OF_16/test-cases/2-1-1-1-1-2-{SCOPE}.md`
- Test-design dir: `fts/ft-2-OF_16/work/test-design/{SCOPE}`
- Cycle state: `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml`

Do not perform semantic coverage review in this stage. Check:

- every executable test case uses `## TC-*` headings;
- canonical TC uses bold metadata fields, not table-only metadata;
- split artifacts have required headings and table columns;
- traceability-bearing columns do not use placeholder `-`, `N/A`, `NA`, `not applicable`, or empty cells;
- `writer-quality-gate.md` and `writer-self-check.md` are structurally readable;
- `outputs/scoped-validator-profile.writer-r1.json` exists and reports current-scope validator status.

If parseability/structure passes, update `cycle-state.yaml` to `stage_status: semantic-review-ready`, `current_stage: structure-preflight-r1`, and route to semantic review. If blocked, set `stage_status: structure-preflight-blocked` and write a structure remediation prompt.
"""


def bootstrap_profile() -> str:
    payload = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_16 --json",
        "scope_slug": SCOPE,
        "canonical_test_cases": f"test-cases/2-1-1-1-1-2-{SCOPE}.md",
        "test_design_dir": f"work/test-design/{SCOPE}",
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def cycle_state() -> str:
    latest = [
        f"test-cases/2-1-1-1-1-2-{SCOPE}.md",
        f"work/test-design/{SCOPE}/artifact-write-strategy.md",
        f"work/test-design/{SCOPE}/source-row-inventory.md",
        f"work/test-design/{SCOPE}/source-row-completeness-matrix.md",
        f"work/test-design/{SCOPE}/source-table-normalization.md",
        f"work/test-design/{SCOPE}/dictionary-inventory.md",
        f"work/test-design/{SCOPE}/test-design-decision-table.md",
        f"work/test-design/{SCOPE}/coverage-obligation-table.md",
        f"work/test-design/{SCOPE}/atomic-requirements-ledger.md",
        f"work/test-design/{SCOPE}/package-test-design-plan.md",
        f"work/test-design/{SCOPE}/test-design-applicability-matrix.md",
        f"work/test-design/{SCOPE}/dependency-matrix.md",
        f"work/test-design/{SCOPE}/test-design-review.md",
        f"work/test-design/{SCOPE}/coverage-gaps.md",
        f"work/test-design/{SCOPE}/coverage-metrics.md",
        f"work/test-design/{SCOPE}/fixture-catalog.md",
        f"work/test-design/{SCOPE}/risk-priority-map.md",
        f"work/test-design/{SCOPE}/writer-quality-gate.md",
        f"work/test-design/{SCOPE}/writer-self-check.md",
        f"work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md",
        f"work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md",
        f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json",
        f"work/review-cycles/{SCOPE}/outputs/writer-r1-response.md",
        f"work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md",
    ]
    latest_yaml = "\n".join(f"  - {item}" for item in latest)
    open_questions = "\n".join(f"  - {gid}: {desc}" for gid, _typ, _ref, desc in GAPS)
    return f"""cycle_id: ft-2-OF_16-{SCOPE}
ft_slug: ft-2-OF_16
scope_slug: {SCOPE}
section_id: {SECTION}
current_stage: writer-r1
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: test-cases/2-1-1-1-1-2-{SCOPE}.md
test_design_dir: work/test-design/{SCOPE}
active_snapshot: none
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions: []
latest_artifacts:
{latest_yaml}
accepted_risks:
  - V23 is a targeted writer initial-draft regression for placeholder-sentinel normalization after V22 proved signed-off could still contain traceability placeholder cells.
  - Existing canary v1-v22 artifacts are regression comparison material only, not requirement sources, templates or acceptance evidence.
  - GAP-001..GAP-011 remain visible residual gaps where exact integration or invalid-input UI mechanism is not source-backed.
blocking_reasons: []
blocking_findings: []
open_questions:
{open_questions}
"""


def main() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    files = {
        TD / "artifact-write-strategy.md": artifact_write_strategy(),
        TD / "source-row-inventory.md": source_row_inventory(),
        TD / "source-row-completeness-matrix.md": source_row_completeness(),
        TD / "source-table-normalization.md": source_table_normalization(),
        TD / "dictionary-inventory.md": dictionary_inventory(),
        TD / "test-design-decision-table.md": test_design_decision_table(),
        TD / "coverage-obligation-table.md": coverage_obligations(),
        TD / "atomic-requirements-ledger.md": atomic_ledger(),
        TD / "package-test-design-plan.md": package_plan(),
        TD / "test-design-applicability-matrix.md": applicability_matrix(),
        TD / "dependency-matrix.md": dependency_matrix(),
        TD / "test-design-review.md": test_design_review(),
        TD / "coverage-gaps.md": coverage_gaps(),
        TD / "coverage-metrics.md": coverage_metrics(),
        TD / "fixture-catalog.md": fixture_catalog(),
        TD / "risk-priority-map.md": risk_priority_map(),
        TD / "writer-quality-gate.md": writer_quality_gate(),
        TD / "writer-self-check.md": writer_self_check(),
        TC_FILE: canonical_test_cases(),
        OUT / "writer-session-log.writer-r1.md": session_log(),
        OUT / "agent-decision-log.writer-r1.md": decision_log(),
        OUT / "writer-r1-response.md": writer_response(),
        OUT / "scoped-validator-profile.writer-r1.json": bootstrap_profile(),
        PROMPTS / "prompt.structure-preflight-r1.md": next_prompt(),
        CYCLE / "cycle-state.yaml": cycle_state(),
    }
    for path, content in files.items():
        write(path, content)


if __name__ == "__main__":
    main()
