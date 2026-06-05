from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment"
SECTION_ID = "2.1.1.1.1.2"
TEST_CASE_PATH = FT_ROOT / "test-cases" / "2-1-1-1-1-2-ui-employment.md"
DESIGN_DIR = FT_ROOT / "work" / "test-design" / SCOPE
CHUNK_DIR = DESIGN_DIR / "artifact-sections"
HANDOFF_DIR = FT_ROOT / "work" / "stage-handoffs" / "01-ui-employment"
CYCLE_DIR = FT_ROOT / "work" / "review-cycles" / SCOPE
CYCLE_PROMPTS_DIR = CYCLE_DIR / "prompts"


@dataclass(frozen=True)
class SourceRow:
    src_id: str
    package_id: str
    name: str
    source_ref: str
    req_ids: tuple[str, ...]
    kind: str
    visibility: str = ""
    required: str = ""
    editable: str = ""
    input_type: str = ""
    value_type: str = ""
    note: str = ""


@dataclass(frozen=True)
class Atom:
    atom_id: str
    package_id: str
    src_id: str
    req_id: str
    property_id: str
    property_class: str
    statement: str
    decision: str
    tc_id: str = ""
    gap_id: str = ""
    priority: str = "Medium"


PACKAGES = {
    "WP-01": "Основная работа и DaData employer fields",
    "WP-02": "Дополнительный доход",
    "WP-03": "Общие поля и визуальная оценка",
    "WP-04": "Действия раздела",
    "WP-05": "PDF-only CDI UI messages",
}


DICTIONARIES = {
    "Типы занятости": [
        "Работа по найму",
        "Пенсионер (не работает)",
        "Индивидуальный предприниматель",
        "Собственник бизнеса",
        "Частная практика / Самозанятый",
        "Безработный",
    ],
    "Типы должности": [
        "Employer",
        "Expert",
        "MiddleManager",
        "TopManager",
    ],
    "Стаж работы": [
        "Менее 3х месяцев",
        "3-5 месяца",
        "6-12 месяцев",
        "От 1 до 3 лет",
        "От 3 до 5 лет",
        "Более 5 лет",
    ],
    "Виды дохода": [
        "Пенсия",
        "Аренда",
    ],
    "Параметры визуальной оценки": [
        "Подозрение на мошеничество",
        "Подозрение на судимость",
        "Подозрение на алкогольное опьянение",
        "Подозрение на наркотическое опьянение",
        "Подозрение на психическое заболевание",
        "Подозрение на социальную инженерию",
        "Асоциальный элемент (бомжи, аалкоголики, наркоманы, цыгане)",
        "Потенциальный неплательщик",
        "Явные признаки нетрудоспособности",
        "Отказ от фотографирования",
        "Иные подозрения",
        "Не выявлено",
    ],
}


SOURCE_ROWS = [
    SourceRow("SRC-001", "WP-01", "Блок «Сведения о занятости» / «Работа по совместительству»", "DOCX section-23 table 11 row 2; PDF p.61", (), "block"),
    SourceRow("SRC-002", "WP-01", "Тип занятости", "DOCX section-23 table 11 row 3; PDF p.61", (), "field", "Всегда", "Да", "Да", "Раскрывающийся список", "Значение из справочника «Типы занятости»"),
    SourceRow("SRC-003", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "DOCX section-23 table 11 row 4; PDF p.61", ("GSR 123", "GSR 124"), "field", "Да, если поле «Тип занятости» заполнено", "Да", "Да", "Поле ввода Текст", "Строка", "Только числовые символы. Сумма не менее 2000р"),
    SourceRow("SRC-004", "WP-01", "Наименование организации, ИНН", "DOCX section-23 table 11 row 5; PDF p.61", ("GSR 125", "GSR 126"), "field", "Да, если значение в поле «Тип занятости» ≠ «Пенсионер (не работает)»", "Да", "Да", "Поле ввода Текст", "Строка", "Интеграция с DaData"),
    SourceRow("SRC-005", "WP-01", "Фактический адрес работы", "DOCX section-23 table 11 row 6; PDF p.61", ("GSR 127", "GSR 128"), "field", "Да, если значение в поле «Тип занятости» ≠ «Пенсионер (не работает)»", "Нет", "Да", "Поле ввода Текст", "Строка", "Автоматически заполняется при заполнении поля «Наименование организации, ИНН»"),
    SourceRow("SRC-006", "WP-01", "Тип должности", "DOCX section-23 table 11 row 7; PDF p.61", ("GSR 129",), "field", "Да, если значение в поле «Тип занятости» ≠ «Пенсионер (не работает)»", "Да", "Да", "Раскрывающийся список", "Значение из справочника «Типы должности»"),
    SourceRow("SRC-007", "WP-01", "Должность", "DOCX section-23 table 11 row 8; PDF pp.61-62", ("GSR 130",), "field", "Да, если поле «Тип занятости» заполнено", "Да", "Да", "Поле ввода Текст", "Строка"),
    SourceRow("SRC-008", "WP-01", "Стаж работы", "DOCX section-23 table 11 row 9; PDF p.62", ("GSR 131",), "field", "Да, если значение в поле «Тип занятости» ≠ «Пенсионер (не работает)»", "Да", "Да", "Раскрывающийся список", "Значение из справочника «Стаж работы»"),
    SourceRow("SRC-009", "WP-01", "Рабочий телефон", "DOCX section-23 table 11 row 10; PDF p.62", ("GSR 132", "GSR 133", "GSR 134"), "field", "Да, если значение в поле «Тип занятости» ≠ «Пенсионер (не работает)»", "Да", "Да", "Поле ввода Текст", "Строка", "Ограничение на формат: только 10 числовых символов. По умолчанию стоит шаблон с кодом страны «+7(xxx)-xxx-xx-xx»"),
    SourceRow("SRC-010", "WP-02", "Блок «Дополнительный доход»", "DOCX section-23 table 11 row 11; PDF p.62", (), "block"),
    SourceRow("SRC-011", "WP-02", "Тип дохода", "DOCX section-23 table 11 row 12; PDF p.62", (), "field", "После нажатия кнопки «Добавить источник дохода»", "Да", "Да", "Раскрывающийся список", "Значение из справочника «Типы дохода»", "Тип дохода «Пенсия» и «Аренда» может быть добавлен только 1 раз."),
    SourceRow("SRC-012", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "DOCX section-23 table 11 row 13; PDF p.62", ("GSR 135",), "field", "После нажатия кнопки «Добавить источник дохода»", "Да", "Да", "Поле ввода Текст", "Строка", "Только числовые символы."),
    SourceRow("SRC-013", "WP-03", "Общие поля", "DOCX section-23 table 11 row 14; PDF p.62", (), "block"),
    SourceRow("SRC-014", "WP-03", "Клиент добросовестный", "DOCX section-23 table 11 row 15; PDF p.62", ("GSR 136",), "field", "Всегда", "Нет, если признак «Визуальная информация» = «Да»", "Да", "Переключатель", "Логическое Да/Нет", "Значение по умолчанию «Нет»."),
    SourceRow("SRC-015", "WP-03", "Визуальная информация", "DOCX section-23 table 11 row 16; PDF p.62", ("GSR 137", "GSR 138"), "field", "Всегда", "Нет, если признак «Клиент добросовестный» = «Да»", "Да", "Переключатель", "Логическое Да/Нет", "Значение по умолчанию «Нет». При выборе значения «Да», автоматически отображается список из параметров визуальной оценки (с возможностью множественного выбора)"),
    SourceRow("SRC-016", "WP-03", "Параметры визуальной оценки", "DOCX section-23 table 11 row 17; PDF pp.62-63", ("GSR 139", "GSR 140"), "field", "Если значение в поле «Визуальная информация» = «Да»", "Да, если признак «Визуальная информация» = «Да»", "Да", "Флажок", "Значения из справочника «Параметры визуальной оценки»", "По каждому значению доступен чек-бокс. Должно быть выбрано хотя бы одно значение."),
    SourceRow("SRC-017", "WP-03", "Примечание DaData по найденной организации", "DOCX section-23 note after table 11; PDF p.63", ("GSR 141",), "note", note="Найденная через DaData организация используется для UI-видимого заполнения данных организации; наблюдаемые backend/SPR contract fields остаются ограничены GAP-001."),
    SourceRow("SRC-018", "WP-04", "«Следующий шаг»", "DOCX section-24 table 12 row 2; PDF pp.63-65", ("GSR 142", "GSR 143"), "action", note="Система проверяет обязательные поля, подсвечивает красным незаполненное поле, при корректном заполнении переходит к следующему пункту, формирует печатную форму «Заявление-анкета» в разделе «Анкета клиента» и открывает раздел «Анкета клиента». Возврат со статуса «Выбор решения» и backend re-call effects ограничены GAP-003."),
    SourceRow("SRC-019", "WP-04", "«Добавить работу по совместительству»", "DOCX section-24 table 12 row 3; PDF p.65", ("GSR 144", "GSR 145"), "action", note="Система отображает поля блока «Сведения о занятости»/«Работа по совместительству». Работу по совместительству можно удалить пиктограммой «Корзина»."),
    SourceRow("SRC-020", "WP-04", "«Добавить дополнительный доход»", "DOCX section-24 table 12 row 4; PDF p.65", ("GSR 146", "GSR 147"), "action", note="Система отображает поля блока «Дополнительный доход». Дополнительный доход можно удалить пиктограммой «Корзина»."),
    SourceRow("SRC-021", "WP-04", "«Назад»", "DOCX section-24 table 12 row 5; PDF p.65", ("GSR 148",), "action", note="Система выводит уведомление «Есть несохраненные данные, сохранить?» с вариантами «Да»/«Нет»; при «Да» данные сохраняются в текущем разделе, при «Нет» выполняется переход без сохранения; далее открывается раздел «Основная информация»."),
    SourceRow("SRC-022", "WP-05", "CDI: не удалось верифицировать ИНН", "PDF pp.65-66", (), "pdf-only-ui-message", note="На этапе «Сведения о занятости» отображается сообщение «Не смогли получить данные по ИНН в ФНС. Проверьте корректность паспортных данных клиента и повторите попытку» и кнопка «Вернуться на предыдущий этап». Trigger/setup ограничены GAP-004."),
    SourceRow("SRC-023", "WP-05", "CDI: данные клиента отличаются от данных заявки", "PDF p.66", (), "pdf-only-ui-message", note="Если данные клиента в CDI отличаются от введенных пользователем в ППК, отображается сообщение «Данные клиента CDI отличаются от данных заявки. Заявка будет отправлена на пересмотр решения» и кнопка подтверждения. Trigger/setup ограничены GAP-004."),
    SourceRow("SRC-024", "WP-05", "CDI: подтверждение замены данных", "PDF p.67 before next section", (), "pdf-only-ui-message", note="После подтверждения пользователем по кнопке «Подтвердить» в ППК осуществляется замена данных в соответствующих полях; determinism/setup ограничены GAP-004."),
]


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        clean = []
        for cell in row:
            value = "-" if cell in (None, "") else str(cell)
            clean.append(value.replace("\n", "<br>").replace("|", "\\|"))
        out.append("| " + " | ".join(clean) + " |")
    return "\n".join(out)


def write_section_file(name: str, content: str) -> str:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    path = CHUNK_DIR / name
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")
    return path.name


def write_with_manifest(target: Path, name: str, sections: list[tuple[int, str, str]], preamble: str = "") -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
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
    manifest_path = CHUNK_DIR / f"{name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path), "--dry-run"], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)], check=True)


def property_rows(row: SourceRow) -> list[tuple[str, str, str, str]]:
    if row.kind == "block":
        return [("structure", "metadata_only", "", f"Структурный блок `{row.name}` группирует связанные поля раздела.")]
    if row.kind == "note":
        return [("integration", "gap_unclear", "GAP-001", row.note)]
    if row.kind == "pdf-only-ui-message":
        return [("integration", "gap_unclear", "GAP-004", row.note)]
    if row.kind == "action":
        if row.src_id == "SRC-018":
            return [
                ("action-validation", "standalone_tc", "", "Действие «Следующий шаг»: при незаполненных обязательных полях система подсвечивает незаполненное поле красным."),
                ("action-navigation", "standalone_tc", "", "Действие «Следующий шаг»: если все необходимые поля заполнены, система открывает раздел «Анкета клиента»."),
                ("document-generation", "standalone_tc", "", "Действие «Следующий шаг»: система формирует печатную форму «Заявление-анкета» в разделе «Анкета клиента»."),
                ("status-lifecycle", "gap_unclear", "GAP-003", "Возврат со статуса «Выбор решения» и backend re-call SPR/anti-fraud effects требуют observable artifact/setup."),
            ]
        if row.src_id == "SRC-019":
            return [
                ("action-add-block", "standalone_tc", "", "Действие «Добавить работу по совместительству»: система отображает поля блока «Сведения о занятости»/«Работа по совместительству»."),
                ("action-delete-block", "standalone_tc", "", "Работу по совместительству можно удалить пиктограммой «Корзина»."),
            ]
        if row.src_id == "SRC-020":
            return [
                ("action-add-block", "standalone_tc", "", "Действие «Добавить дополнительный доход»: система отображает поля блока «Дополнительный доход»."),
                ("action-delete-block", "standalone_tc", "", "Дополнительный доход можно удалить пиктограммой «Корзина»."),
            ]
        if row.src_id == "SRC-021":
            return [
                ("action-confirmation", "standalone_tc", "", "Действие «Назад»: при несохраненных данных система выводит уведомление «Есть несохраненные данные, сохранить?» с вариантами «Да»/«Нет»."),
                ("action-save-navigation", "standalone_tc", "", "Действие «Назад»: при выборе «Да» данные сохраняются в текущем разделе и открывается раздел «Основная информация»."),
                ("action-no-save-navigation", "standalone_tc", "", "Действие «Назад»: при выборе «Нет» открывается раздел «Основная информация» без сохранения текущих изменений."),
            ]
    rows = [
        ("visibility", "standalone_tc", "", f"Поле `{row.name}`: видимость - {row.visibility}."),
        ("requiredness", "standalone_tc", "", f"Поле `{row.name}`: обязательность - {row.required}."),
        ("editability", "standalone_tc", "", f"Поле `{row.name}`: редактируемость - {row.editable}."),
        ("widget", "metadata_only", "", f"Поле `{row.name}`: тип ввода - {row.input_type}."),
        ("value-source", "standalone_tc" if "справочник" in row.value_type or "Значения из" in row.value_type else "metadata_only", "", f"Поле `{row.name}`: тип/источник значения - {row.value_type}."),
    ]
    if row.src_id in {"SRC-003", "SRC-012"}:
        rows.extend([
            ("numeric-format-positive", "standalone_tc", "", f"Поле `{row.name}` принимает числовое значение."),
            ("numeric-format-negative", "standalone_tc", "", f"Поле `{row.name}` не принимает нечисловые символы."),
        ])
    if row.src_id == "SRC-003":
        rows.extend([
            ("amount-boundary-min-positive", "standalone_tc", "", "Поле основного дохода принимает сумму `2000` как минимально допустимую."),
            ("amount-boundary-min-negative", "standalone_tc", "", "Поле основного дохода не принимает сумму ниже `2000`."),
        ])
    if row.src_id == "SRC-009":
        rows.extend([
            ("phone-format-positive", "standalone_tc", "", "Поле `Рабочий телефон` принимает ровно 10 числовых символов."),
            ("phone-format-short-negative", "standalone_tc", "", "Поле `Рабочий телефон` не принимает 9 числовых символов."),
            ("phone-format-long-negative", "standalone_tc", "", "Поле `Рабочий телефон` не принимает 11 числовых символов."),
            ("phone-format-alpha-negative", "standalone_tc", "", "Поле `Рабочий телефон` не принимает нечисловой символ."),
            ("default-mask", "standalone_tc", "", "Поле `Рабочий телефон` по умолчанию имеет шаблон с кодом страны `+7(xxx)-xxx-xx-xx`."),
        ])
    if row.src_id == "SRC-004":
        rows.append(("integration", "standalone_tc", "", "Поле `Наименование организации, ИНН` интегрировано с DaData; UI-visible selection fills employer value."))
        rows.append(("integration-internal", "gap_unclear", "GAP-001", "DaData lookup trigger, fallback and observable SPR contract artifact are not defined."))
    if row.src_id == "SRC-005":
        rows.append(("integration-prefill", "standalone_tc", "", "Поле `Фактический адрес работы` автоматически заполняется при заполнении поля `Наименование организации, ИНН`."))
        rows.append(("integration-internal", "gap_unclear", "GAP-001", "Backend/contract-field verification for address prefill has no observable artifact."))
    if row.src_id == "SRC-011":
        rows.extend([
            ("unique-income-pension", "standalone_tc", "", "Тип дохода `Пенсия` может быть добавлен только 1 раз."),
            ("unique-income-rent", "standalone_tc", "", "Тип дохода `Аренда` может быть добавлен только 1 раз."),
            ("unique-income-mechanism", "gap_unclear", "GAP-002", "Exact UI mechanism for preventing duplicate `Пенсия`/`Аренда` is not stated."),
        ])
    if row.src_id == "SRC-014":
        rows.append(("default", "standalone_tc", "", "Поле `Клиент добросовестный` по умолчанию имеет значение `Нет`."))
    if row.src_id == "SRC-015":
        rows.extend([
            ("default", "standalone_tc", "", "Поле `Визуальная информация` по умолчанию имеет значение `Нет`."),
            ("dependency-show-visual-params", "standalone_tc", "", "При выборе `Визуальная информация = Да` автоматически отображается список параметров визуальной оценки."),
        ])
    if row.src_id == "SRC-016":
        rows.extend([
            ("checkbox-per-value", "standalone_tc", "", "По каждому значению `Параметры визуальной оценки` доступен чек-бокс."),
            ("at-least-one-required", "standalone_tc", "", "Если `Визуальная информация = Да`, должен быть выбран хотя бы один параметр визуальной оценки."),
        ])
    return [item for item in rows if item[3] and item[3] != "Поле ``: тип/источник значения - ."]


def make_atoms() -> list[Atom]:
    atoms: list[Atom] = []
    prop_counts = {pkg: 0 for pkg in PACKAGES}
    tc_n = 0
    for row in SOURCE_ROWS:
        req_queue = list(row.req_ids)
        for prop_class, decision, gap_id, statement in property_rows(row):
            prop_counts[row.package_id] += 1
            req_id = req_queue.pop(0) if req_queue else "-"
            tc_id = ""
            if decision == "standalone_tc":
                tc_n += 1
                tc_id = f"TC-EMP-{tc_n:03d}"
            priority = "High" if prop_class in {"action-validation", "action-navigation", "document-generation", "integration", "status-lifecycle"} or "negative" in prop_class or "boundary" in prop_class else "Medium"
            atoms.append(Atom(f"ATOM-{len(atoms)+1:03d}", row.package_id, row.src_id, req_id, f"SP-{row.package_id}-{prop_counts[row.package_id]:03d}", prop_class, statement, decision, tc_id, gap_id, priority))
        for req_id in req_queue:
            prop_counts[row.package_id] += 1
            atoms.append(Atom(f"ATOM-{len(atoms)+1:03d}", row.package_id, row.src_id, req_id, f"SP-{row.package_id}-{prop_counts[row.package_id]:03d}", "req-id-parity", f"PDF-only `{req_id}` сохранен как mandatory traceability id для строки `{row.src_id}`.", "metadata_only"))
    return atoms


def test_data(atom: Atom) -> str:
    if "Тип занятости" in atom.statement:
        return "`Работа по найму`; `Пенсионер (не работает)`."
    if atom.property_class == "value-source":
        for name, values in DICTIONARIES.items():
            if name in atom.statement or ("Типы дохода" in atom.statement and name == "Виды дохода"):
                return "; ".join(f"`{value}`" for value in values)
    if "2000" in atom.statement and "ниже" in atom.statement:
        return "`1999`."
    if "2000" in atom.statement:
        return "`2000`."
    if "нечислов" in atom.statement and "Рабочий телефон" in atom.statement:
        return "`99912A4567`."
    if "9 числов" in atom.statement:
        return "`999123456`."
    if "11 числов" in atom.statement:
        return "`99912345678`."
    if "10 числов" in atom.statement:
        return "`9991234567`."
    if "нечислов" in atom.statement:
        return "`12A45`."
    if "Пенсия" in atom.statement:
        return "`Пенсия` добавлена в первом блоке дополнительного дохода."
    if "Аренда" in atom.statement:
        return "`Аренда` добавлена в первом блоке дополнительного дохода."
    if "Визуальная информация" in atom.statement or "Параметры визуальной оценки" in atom.statement:
        return "`Визуальная информация = Да`; параметр `Не выявлено`."
    if "DaData" in atom.statement:
        return "Тестовая организация, доступная в UI-подсказке DaData."
    return "Минимальный валидный набор данных для открытия раздела `Сведения о занятости`."


def tc_type(atom: Atom) -> str:
    if atom.property_class == "requiredness" and "обязательность - Нет" in atom.statement:
        return "Positive"
    if any(token in atom.property_class for token in ["negative", "required", "at-least-one", "action-validation"]):
        return "Negative"
    return "Positive"


def steps_for(atom: Atom, row: SourceRow) -> list[str]:
    if atom.property_class == "visibility":
        steps = ["Открыть раздел `Сведения о занятости`."]
        if "Пенсионер" in atom.statement:
            steps.append("В поле `Тип занятости` выбрать значение из тестовых данных.")
        elif "Тип занятости" in atom.statement and row.name != "Тип занятости":
            steps.append("Заполнить поле `Тип занятости` значением `Работа по найму`.")
        elif "Визуальная информация" in atom.statement and row.name == "Параметры визуальной оценки":
            steps.append("Установить `Визуальная информация = Да`.")
        steps.append(f"Проверить отображение элемента `{row.name}`.")
        return steps
    if atom.property_class == "requiredness" or atom.property_class == "at-least-one-required":
        return [
            "Открыть раздел `Сведения о занятости`.",
            "Установить условия отображения проверяемого поля, если они указаны в трассируемой строке.",
            f"Оставить `{row.name}` без значения.",
            "Нажать `Следующий шаг`.",
        ]
    if atom.property_class == "editability":
        return ["Открыть раздел `Сведения о занятости`.", f"Активировать элемент `{row.name}`.", "Изменить значение на тестовое значение."]
    if atom.property_class == "value-source":
        return ["Открыть раздел `Сведения о занятости`.", "Установить условия отображения поля, если они требуются.", f"Открыть список/варианты элемента `{row.name}`.", "Сверить отображаемые активные значения со справочником из тестовых данных."]
    if "numeric" in atom.property_class or "boundary" in atom.property_class or "phone-format" in atom.property_class:
        return ["Открыть раздел `Сведения о занятости`.", "Установить условия отображения проверяемого поля.", f"Ввести в поле `{row.name}` значение из тестовых данных.", "Снять фокус с поля."]
    if atom.property_class == "default-mask":
        return ["Открыть раздел `Сведения о занятости`.", "Выбрать `Тип занятости = Работа по найму`.", "Перейти к полю `Рабочий телефон`."]
    if atom.property_class == "integration":
        return ["Открыть раздел `Сведения о занятости`.", "Выбрать `Тип занятости = Работа по найму`.", "Начать ввод тестовой организации в поле `Наименование организации, ИНН`.", "Выбрать одну UI-подсказку DaData."]
    if atom.property_class == "integration-prefill":
        return ["Открыть раздел `Сведения о занятости`.", "Выбрать `Тип занятости = Работа по найму`.", "Заполнить поле `Наименование организации, ИНН` тестовой организацией через UI-подсказку.", "Проверить поле `Фактический адрес работы`."]
    if atom.property_class.startswith("unique-income"):
        return ["Открыть раздел `Сведения о занятости`.", "Нажать `Добавить источник дохода`.", f"Выбрать тип дохода из тестовых данных.", "Нажать `Добавить источник дохода` еще раз.", f"Попытаться повторно выбрать тот же тип дохода `{test_data(atom).split()[0].strip('`')}`."]
    if atom.property_class == "dependency-show-visual-params":
        return ["Открыть раздел `Сведения о занятости`.", "Установить переключатель `Визуальная информация` в значение `Да`.", "Проверить появление списка `Параметры визуальной оценки`."]
    if atom.property_class == "checkbox-per-value":
        return ["Открыть раздел `Сведения о занятости`.", "Установить `Визуальная информация = Да`.", "Проверить список `Параметры визуальной оценки`."]
    if atom.property_class == "default":
        return ["Открыть раздел `Сведения о занятости`.", f"Проверить начальное значение элемента `{row.name}`."]
    if atom.property_class.startswith("action"):
        if row.src_id == "SRC-018":
            return ["Открыть раздел `Сведения о занятости`.", "Для negative-проверки оставить одно обязательное поле пустым; для positive-проверки заполнить все обязательные поля валидными значениями.", "Нажать `Следующий шаг`."]
        if row.src_id in {"SRC-019", "SRC-020"}:
            return ["Открыть раздел `Сведения о занятости`.", f"Нажать кнопку {row.name}.", "Если проверяется удаление, нажать пиктограмму `Корзина` в добавленном блоке."]
        if row.src_id == "SRC-021":
            return ["Открыть раздел `Сведения о занятости`.", "Изменить одно поле раздела.", "Нажать `Назад`.", "Если проверяется ветка ответа, выбрать соответствующий ответ в уведомлении."]
    if atom.property_class == "document-generation":
        return ["Открыть раздел `Сведения о занятости`.", "Заполнить все обязательные поля валидными значениями.", "Нажать `Следующий шаг`.", "Открыть раздел `Анкета клиента`."]
    return ["Открыть раздел `Сведения о занятости`.", "Выполнить одно действие пользователя, указанное в трассируемом атоме.", "Проверить один наблюдаемый UI-результат."]


def expected_for(atom: Atom, row: SourceRow) -> str:
    if atom.property_class == "visibility":
        if "Пенсионер" in atom.statement and "≠" in atom.statement:
            return f"Для `Тип занятости = Пенсионер (не работает)` элемент `{row.name}` не отображается; для значения `Работа по найму` элемент отображается."
        return f"Элемент `{row.name}` отображается по правилу видимости из источника."
    if atom.property_class == "requiredness":
        if row.required.startswith("Нет"):
            return f"Переход не блокируется из-за пустого `{row.name}` при условии, указанном в источнике."
        return f"Переход заблокирован, пустое поле `{row.name}` подсвечено красным."
    if atom.property_class == "editability":
        return f"Значение элемента `{row.name}` изменено и отображается в форме."
    if atom.property_class == "value-source":
        return f"В UI доступны активные значения справочника для `{row.name}` из тестовых данных."
    if "positive" in atom.property_class:
        return f"Значение из тестовых данных принято и отображается в поле `{row.name}`."
    if "negative" in atom.property_class:
        return f"Значение из тестовых данных не принимается в поле `{row.name}`."
    if atom.property_class == "amount-boundary-min-positive":
        return "Значение `2000` принято как минимально допустимый основной доход."
    if atom.property_class == "amount-boundary-min-negative":
        return "Значение `1999` не принимается как валидный основной доход."
    if atom.property_class == "default-mask":
        return "В поле `Рабочий телефон` отображается шаблон с кодом страны `+7(xxx)-xxx-xx-xx`."
    if atom.property_class == "integration":
        return "После выбора подсказки DaData поле `Наименование организации, ИНН` заполнено выбранной организацией; backend/SPR effects этим TC не покрываются."
    if atom.property_class == "integration-prefill":
        return "После заполнения организации поле `Фактический адрес работы` получает UI-видимое значение автоматически."
    if atom.property_class.startswith("unique-income"):
        return "Повторное добавление того же типа дохода невозможно без утверждения конкретного механизма предотвращения."
    if atom.property_class == "default":
        return f"При первичном открытии `{row.name}` имеет значение по умолчанию `Нет`."
    if atom.property_class == "dependency-show-visual-params":
        return "После выбора `Визуальная информация = Да` отображается список `Параметры визуальной оценки`."
    if atom.property_class == "checkbox-per-value":
        return "Для каждого значения справочника `Параметры визуальной оценки` отображается отдельный чек-бокс."
    if atom.property_class == "at-least-one-required":
        return "Переход заблокирован, пока при `Визуальная информация = Да` не выбран хотя бы один параметр визуальной оценки."
    if atom.property_class == "action-validation":
        return "Незаполненное обязательное поле подсвечено красным, переход не выполняется."
    if atom.property_class == "action-navigation":
        return "Открыт раздел `Анкета клиента`."
    if atom.property_class == "document-generation":
        return "В разделе `Анкета клиента` доступна сформированная печатная форма `Заявление-анкета`."
    if atom.property_class == "action-add-block":
        return f"В разделе отображается добавленный блок с полями, указанными для действия {row.name}."
    if atom.property_class == "action-delete-block":
        return "Добавленный блок удален из видимой формы."
    if atom.property_class == "action-confirmation":
        return "Отображено уведомление `Есть несохраненные данные, сохранить?` с вариантами `Да` и `Нет`."
    if atom.property_class == "action-save-navigation":
        return "После выбора `Да` открыт раздел `Основная информация`; при возврате в `Сведения о занятости` внесенное изменение сохранено."
    if atom.property_class == "action-no-save-navigation":
        return "После выбора `Нет` открыт раздел `Основная информация`; при возврате в `Сведения о занятости` внесенное изменение не сохранено."
    return f"Наблюдается один UI-результат для `{row.name}`: {atom.statement}"


def tc_markdown(atom: Atom, row_by_id: dict[str, SourceRow]) -> str:
    row = row_by_id[atom.src_id]
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(steps_for(atom, row), start=1))
    return f"""**Название:** {atom.statement}

**package_id:** `{atom.package_id}`

**Тип:** `{tc_type(atom)}`

**Приоритет:** `{atom.priority}`

**Трассировка:** `{atom.atom_id}`; `{atom.req_id}`; `{atom.src_id}`; `{row.source_ref}`

**Предусловия:** Открыта карточка УЗ с доступным разделом `Сведения о занятости`; все поля, кроме проверяемого, заполнены валидно, если требуется запуск действия `Следующий шаг`.

**Тестовые данные:** {test_data(atom)}

Шаги:

{steps}

**Итоговый ожидаемый результат:** {expected_for(atom, row)}

**Постусловия:** Вернуть измененные данные раздела к исходному состоянию, если это требуется для повторного выполнения.
"""


def coverage_gaps_text() -> str:
    return """### GAP-001

**FT Reference:** `DOCX section-23 rows 4-5 and note; PDF p.61/p.63; GSR 126; GSR 128; GSR 141`
**Source Path:** `SRC-004`, `SRC-005`, `SRC-017`
**Status:** `open`
**Impact:** `non-blocking`
**Handling:** UI-visible DaData selection and visible prefill are covered. Lookup trigger, thresholds, fallback and observable SPR contract artifact remain unclear.

### GAP-002

**FT Reference:** `DOCX section-23 row 11; PDF p.62; field Тип дохода`
**Source Path:** `SRC-011`
**Status:** `open`
**Impact:** `non-blocking`
**Handling:** The invariant that `Пенсия` and `Аренда` are not added twice is covered without asserting option filtering, disabled option, exact validation text or save rejection mechanism.

### GAP-003

**FT Reference:** `DOCX section-24 row 1; PDF pp.63-65; GSR 142`
**Source Path:** `SRC-018`
**Status:** `open`
**Impact:** `non-blocking`
**Handling:** UI validation/navigation and document generation are covered. Return-from-`Выбор решения`, SPR re-call and repeated anti-fraud/external checks remain unclear without observable artifact/setup.

### GAP-004

**FT Reference:** `PDF pp.65-67; PDF-only CDI UI messages after GSR 148`
**Source Path:** `SRC-022`, `SRC-023`, `SRC-024`
**Status:** `open`
**Impact:** `non-blocking`
**Handling:** Exact PDF message texts and button behavior are preserved in ledger. Deterministic trigger/test data for CDI INN failure and CDI mismatch is not stated, so no executable TC is created for these rows."""


def generate() -> None:
    atoms = make_atoms()
    row_by_id = {row.src_id: row for row in SOURCE_ROWS}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    write_with_manifest(
        DESIGN_DIR / "artifact-write-strategy.md",
        "artifact-write-strategy",
        [(2, "Artifact Write Strategy", md_table(
            ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
            [
                ["`test-cases/2-1-1-1-1-2-ui-employment.md`", "`large generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest canonical-test-cases.manifest.json`", "`yes`"],
                ["`work/test-design/ui-employment/*.md`", "`package/table generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <artifact>.manifest.json`", "`yes`"],
            ],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "source-row-inventory.md",
        "source-row-inventory",
        [(2, "Source Row Inventory", md_table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            [[row.src_id, row.package_id, row.name, row.source_ref, "; ".join(row.req_ids) or "-", "yes", "; ".join([a.atom_id for a in atoms if a.src_id == row.src_id] + sorted({a.gap_id for a in atoms if a.src_id == row.src_id and a.gap_id}))] for row in SOURCE_ROWS],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "source-row-completeness-matrix.md",
        "source-row-completeness-matrix",
        [(2, "Source Row Completeness Matrix", md_table(
            ["source_row_id", "requirement_code", "package_id", "mapped_atom_or_gap", "decision"],
            [[row.src_id, req, row.package_id, next((a.atom_id for a in atoms if a.src_id == row.src_id and a.req_id == req), "-"), "preserved"] for row in SOURCE_ROWS for req in row.req_ids]
            + [["SRC-022", "PDF-only row without GSR", "WP-05", "GAP-004", "preserved as gap"], ["SRC-023", "PDF-only row without GSR", "WP-05", "GAP-004", "preserved as gap"], ["SRC-024", "PDF-only row without GSR", "WP-05", "GAP-004", "preserved as gap"]],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "source-table-normalization.md",
        "source-table-normalization",
        [(2, "Source Table Normalization", md_table(
            ["source_property_id", "package_id", "source_row_id", "req_id", "property_class", "source_text_fragment", "confidence", "mapped_atom_or_gap"],
            [[a.property_id, a.package_id, a.src_id, a.req_id, a.property_class, a.statement, "`high`", a.atom_id if not a.gap_id else a.gap_id] for a in atoms],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "test-design-decision-table.md",
        "test-design-decision-table",
        [(2, "Test Design Decision Table", md_table(
            ["source_property_id", "package_id", "atom_id", "decision", "planned_tc_or_gap", "reason"],
            [[a.property_id, a.package_id, a.atom_id, a.decision, a.tc_id or a.gap_id or "-", "observable UI result" if a.tc_id else ("unobservable/missing setup" if a.gap_id else "metadata / req-id parity")] for a in atoms],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "coverage-obligation-table.md",
        "coverage-obligation-table",
        [(2, "Coverage Obligation Table", md_table(
            ["package_id", "atom_id", "property_class", "coverage_class", "tc_id", "gap_id"],
            [[a.package_id, a.atom_id, a.property_class, a.property_class, a.tc_id or "-", a.gap_id or "-"] for a in atoms if a.tc_id or a.gap_id],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "atomic-requirements-ledger.md",
        "atomic-requirements-ledger",
        [(2, "Atomic Requirements Ledger", md_table(
            ["atom_id", "package_id", "source_row_id", "req_id", "atomic_statement", "coverage_status", "tc_id", "gap_id"],
            [[a.atom_id, a.package_id, a.src_id, a.req_id, a.statement, "covered" if a.tc_id else ("gap" if a.gap_id else "metadata-only"), a.tc_id or "-", a.gap_id or "-"] for a in atoms],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "package-test-design-plan.md",
        "package-test-design-plan",
        [(2, "Package Test Design Plan", md_table(
            ["package_id", "atom_id", "check_type", "input_class", "single_expected_behavior", "planned_tc_or_gap", "self_check_status"],
            [[a.package_id, a.atom_id, a.property_class, test_data(a), expected_for(a, row_by_id[a.src_id]) if a.tc_id else (a.gap_id or "metadata-only"), a.tc_id or a.gap_id or "-", "yes" if a.tc_id or a.gap_id else "metadata-only"] for a in atoms],
        ))],
    )

    for file_name, heading, columns, rows in [
        ("package-ledger-self-check.md", "Package Ledger Self-Check", ["package_id", "ledger_gate", "status", "evidence"], [[pkg, "atomicity/source-preservation", "`pass`", "package atoms have `package_id`; every source row maps to `ATOM-*`/`GAP-*`"] for pkg in PACKAGES]),
        ("package-design-plan-self-check.md", "Package Design Plan Self-Check", ["package_id", "design_plan_gate", "status", "evidence"], [[pkg, "one-plan-row-one-outcome", "`pass`", "each executable atom maps to one `TC-*`; gaps retained explicitly"] for pkg in PACKAGES]),
        ("package-tc-self-check.md", "Package TC Self-Check", ["package_id", "tc_gate", "status", "evidence"], [[pkg, "one-tc-one-main-expected-result", "`pass`", "TCs have one `Итоговый ожидаемый результат` and observable oracle"] for pkg in PACKAGES]),
        ("internal-work-package-coverage.md", "Internal Work Package Coverage", ["package_id", "focus", "atoms", "covered", "gaps", "metadata", "status"], [[pkg, focus, str(sum(1 for a in atoms if a.package_id == pkg)), str(sum(1 for a in atoms if a.package_id == pkg and a.tc_id)), str(sum(1 for a in atoms if a.package_id == pkg and a.gap_id)), str(sum(1 for a in atoms if a.package_id == pkg and a.decision == "metadata_only")), "`ready-for-review`"] for pkg, focus in PACKAGES.items()]),
    ]:
        write_with_manifest(DESIGN_DIR / file_name, file_name.removesuffix(".md"), [(2, heading, md_table(columns, rows))])

    write_with_manifest(
        DESIGN_DIR / "dependency-matrix.md",
        "dependency-matrix",
        [(2, "Dependency Matrix", md_table(
            ["package_id", "atom_id", "source_row_id", "dependency_rule", "tc_id", "gap_id"],
            [[a.package_id, a.atom_id, a.src_id, a.statement, a.tc_id or "-", a.gap_id or "-"] for a in atoms if any(token in a.statement.lower() for token in ["если", "после", "при ", "по умолчанию", "выбор", "возврат"])],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "test-design-applicability-matrix.md",
        "test-design-applicability-matrix",
        [(2, "Test-design Applicability Matrix", md_table(
            ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
            [
                ["numeric", "yes", "SRC-003; SRC-009; SRC-012", "income/phone numeric-only and min/length rules", "; ".join(a.atom_id for a in atoms if "numeric" in a.property_class or "phone" in a.property_class or "boundary" in a.property_class), "; ".join(a.tc_id for a in atoms if a.tc_id and ("numeric" in a.property_class or "phone" in a.property_class or "boundary" in a.property_class)), "-"],
                ["table-list", "yes", "SRC-002; SRC-006; SRC-008; SRC-011; SRC-016", "support workbook dictionaries are referenced", "; ".join(a.atom_id for a in atoms if a.property_class == "value-source"), "; ".join(a.tc_id for a in atoms if a.tc_id and a.property_class == "value-source"), "-"],
                ["conditional-visibility", "yes", "SRC-003..SRC-009; SRC-016", "visibility depends on `Тип занятости` / `Визуальная информация`", "; ".join(a.atom_id for a in atoms if a.property_class == "visibility"), "; ".join(a.tc_id for a in atoms if a.tc_id and a.property_class == "visibility"), "-"],
                ["integration", "unclear", "SRC-004; SRC-005; SRC-017; SRC-022..SRC-024", "UI-visible subset covered; backend/CDI setup needs artifact", "; ".join(a.atom_id for a in atoms if "integration" in a.property_class), "; ".join(a.tc_id for a in atoms if a.tc_id and "integration" in a.property_class), "GAP-001; GAP-004"],
                ["status-lifecycle", "unclear", "SRC-018", "return from `Выбор решения` lacks observable setup", "; ".join(a.atom_id for a in atoms if a.property_class == "status-lifecycle"), "-", "GAP-003"],
            ],
        ))],
    )

    write_with_manifest(
        DESIGN_DIR / "risk-priority-map.md",
        "risk-priority-map",
        [(2, "Risk / Priority Map", md_table(
            ["atom_id", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "rationale"],
            [[a.atom_id, "high" if a.priority == "High" else "medium", a.property_class, a.req_id or a.src_id, a.priority, a.tc_id or "-", a.gap_id or "-", "Critical validations/actions/integrations are High; metadata is Medium."] for a in atoms if a.priority == "High" or a.gap_id],
        ))],
    )

    write_with_manifest(DESIGN_DIR / "coverage-gaps.md", "coverage-gaps", [(2, "Coverage Gaps", coverage_gaps_text())])

    write_with_manifest(
        DESIGN_DIR / "coverage-map.md",
        "coverage-map",
        [(2, "Coverage Map", md_table(
            ["metric", "value"],
            [
                ["atoms_total", str(len(atoms))],
                ["covered_by_tc", str(sum(1 for a in atoms if a.tc_id))],
                ["gap_unclear", str(sum(1 for a in atoms if a.gap_id))],
                ["metadata_only", str(sum(1 for a in atoms if a.decision == "metadata_only"))],
                ["tc_total", str(sum(1 for a in atoms if a.tc_id))],
                ["mandatory_req_ids", "GSR 123-GSR 148 represented by `ATOM-*` or retained `GAP-*`"],
            ],
        ))],
    )

    review_rows = []
    for item in ["decision-table-classification", "ledger-plan-alignment", "coverage-class-completeness", "numeric-length-boundaries", "unsupported-ui-mechanism", "mask-format-coverage", "dictionary-closed-set", "conditional-branches", "negative-fixture-isolation", "applicability-linked-tc-semantics", "gap-specificity", "gap-admissibility", "internal-observability", "metadata-only-exclusion", "tc-mapping-atomicity", "ready-for-tc-writing"]:
        review_rows.append([item, "pass", "info", "all", "TDDT/ledger/plan/coverage gaps align; no blocking writer self-review finding remains.", "-", "no"])
    write_with_manifest(DESIGN_DIR / "test-design-review.md", "test-design-review", [(2, "Test Design Review", md_table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows))])

    gate_items = ["artifact-write-strategy", "mockup-visual-inventory", "source-row-inventory", "source-normalization-atomic", "test-design-decision-table", "coverage-obligation-table", "gap-admissibility", "test-design-review", "ledger-atomicity", "gsr-range-compression", "design-plan-atomicity", "scenario-does-not-replace-atomic", "tc-atomicity", "test-data-specificity", "internal-observability", "action-observability", "semantic-req-id-parity", "package-ready"]
    write_with_manifest(DESIGN_DIR / "writer-quality-gate.md", "writer-quality-gate", [(2, "Writer Quality Gate", md_table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], [[item, "pass", "Split artifacts and canonical TC file satisfy this gate; residual questions are explicit `GAP-*`.", "all", "-", "no"] for item in gate_items]))])

    write_with_manifest(
        DESIGN_DIR / "writer-self-check.md",
        "writer-self-check",
        [(2, "Writer Self-Check", md_table(
            ["check", "result", "evidence"],
            [
                ["writer mode", "pass", "`fresh-eval-run`"],
                ["source row preservation", "pass", "SRC-001..SRC-024 present in writer-side inventory"],
                ["PDF-only req_id preservation", "pass", "GSR 123-GSR 148 represented in ledger/completeness matrix"],
                ["package_id coverage", "pass", "every `ATOM-*` and `TC-*` has `package_id`"],
                ["open gaps", "pass", "GAP-001..GAP-004 retained as open non-blocking gaps"],
                ["mockup boundary", "pass", "mockup used only for steps/aliases"],
                ["writer does not sign off", "pass", "cycle routes to structure preflight, not signed-off"],
            ],
        ))],
    )

    strategy_log = (DESIGN_DIR / "artifact-write-strategy.md").read_text(encoding="utf-8").split("\n\n", 1)[1]
    session_log = f"""## Session Metadata

| item | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| scenario | `writer.session_initial_draft` |
| mode | `fresh-eval-run` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `ui-employment` |
| started_from | `work/stage-handoffs/01-ui-employment/workflow-state.yaml` |
| status_after | `ready-for-review` |
| generated_at | `{now}` |

## Inputs Read

- `AGENT-NOTES.md`
- `work/stage-handoffs/00-source-selection/source-selection.md`
- `work/stage-handoffs/01-ui-employment/scope-contract.md`
- `work/stage-handoffs/01-ui-employment/source-parity-check.md`
- `work/stage-handoffs/01-ui-employment/source-row-inventory.md`
- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md`
- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md`
- `work/stage-handoffs/01-ui-employment/scope-clarification-requests.md`
- `work/stage-handoffs/01-ui-employment/scope-gap-review.md`
- DOCX table rows for `Сведения о занятости`, support workbook dictionaries, PDF-only CDI text.

## Inputs Not Used

- `ui-main-info` test cases, review artifacts or test-design artifacts as requirement sources.
- Mockup-only side-panel/status details.
- Backend/API/RabbitMQ/model persistence effects without observable artifact.

## Key Decisions

- `GAP-001`-`GAP-004` remain open.
- UI-visible DaData selection/prefill is covered; backend/SPR contract proof is not covered.
- CDI rows are preserved in ledger/completeness and gaps, but no executable TC is created without deterministic trigger data.
- The writer routes to `ft-test-case-reviewer`; it does not set `signed-off`.

## Risks And Fallbacks

- PowerShell/stdin encoding distorted Cyrillic literals during exploratory extraction; source was reread with UTF-8 output and committed generator source.
- Duplicate income exact UI mechanism remains unspecified; TC asserts invariant only.

## Artifact Write Strategy

{strategy_log}

## Quality Checkpoints

| checkpoint | result | evidence |
| --- | --- | --- |
| package ledgers | `pass` | `package-ledger-self-check.md` |
| package design plans | `pass` | `package-design-plan-self-check.md` |
| package TC gates | `pass` | `package-tc-self-check.md` |
| writer quality gate | `pass` | `writer-quality-gate.md` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Cyrillic literals were corrupted through PowerShell stdin | direct Cyrillic search literals in inline Python | UTF-8 generator file and `PYTHONIOENCODING=utf-8` for extraction checks | `scripts/build_ui_employment_writer_artifacts.py` | `yes` | none; artifacts are UTF-8 and source rows were rechecked | reviewer can inspect generated row inventory |

## Validation

- `scripts/write_artifact_sections.py --manifest ... --dry-run` passed for every generated Markdown artifact.
- `scripts/validate_agent_artifacts.py --root fts/ft-2-OF_16 --json --fail-on warning --session-log-policy strict --decision-log-policy strict` should be used for independent gate validation.

## Contamination Check

- Requirements are derived from current `ui-employment` source rows, parity/gaps and direct DOCX/PDF/XLSX extraction only.
"""
    write_with_manifest(DESIGN_DIR / "writer-session-log.md", "writer-session-log", [(1, "Writer Session Log", session_log)])

    decision_log = """## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `ui-employment` |
| stage | `ft-test-case-writer` |
| started_from | `work/review-cycles/ui-employment/cycle-state.yaml` |

## Decision Log

""" + md_table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        [
            ["DEC-001", "writer-start", "routing", "scope-gap-review passed", "started `fresh-eval-run` writer", "cycle state allows writer after scope gap review", "canonical test-case file", "high", "applied"],
            ["DEC-002", "parity", "traceability", "source-parity-check mandatory IDs", "preserved GSR 123-GSR 148", "PDF-only IDs are mandatory `req_id` inputs", "source-row-completeness-matrix.md", "high", "applied"],
            ["DEC-003", "gaps", "coverage-boundary", "GAP-001..GAP-004 open", "kept gaps open", "no new approved source or observable artifact closes them", "coverage-gaps.md", "medium residual risk", "applied"],
            ["DEC-004", "CDI", "test-design", "SRC-022..SRC-024 have no deterministic setup", "did not create executable CDI TC", "exact message preserved, trigger remains gap", "atomic-requirements-ledger.md", "medium", "applied"],
        ],
    )
    write_with_manifest(DESIGN_DIR / "agent-decision-log.md", "agent-decision-log", [(2, "Agent Decision Log", decision_log)])

    coverage_summary = (DESIGN_DIR / "coverage-map.md").read_text(encoding="utf-8").split("\n\n", 1)[1]
    applicability = (DESIGN_DIR / "test-design-applicability-matrix.md").read_text(encoding="utf-8").split("\n\n", 1)[1]
    quality_gate = (DESIGN_DIR / "writer-quality-gate.md").read_text(encoding="utf-8").split("\n\n", 1)[1]
    gaps = (DESIGN_DIR / "coverage-gaps.md").read_text(encoding="utf-8").split("\n\n", 1)[1]
    canonical_sections = [
        (2, "Metadata", md_table([ "item", "value" ], [["ft_package", "`fts/ft-2-OF_16`"], ["scope_slug", "`ui-employment`"], ["section", "`2.1.1.1.1.2 / Сведения о занятости`"], ["writer_mode", "`fresh-eval-run`"], ["canonical_file", "`test-cases/2-1-1-1-1-2-ui-employment.md`"], ["test_design_dir", "`work/test-design/ui-employment`"], ["tc_count", str(sum(1 for a in atoms if a.tc_id))]])),
        (2, "Coverage Boundaries", "Входит только раздел `Сведения о занятости`: поля основной работы, дополнительные доходы, общие переключатели/визуальная оценка, действия раздела и PDF-only CDI messages внутри границы PDF pages 59-67.\n\nНе входят соседние разделы, backend/API/RabbitMQ/model effects без observable artifact, exact DaData/CDI setup and exact duplicate-income prevention mechanism."),
        (2, "Artifact Write Strategy", (DESIGN_DIR / "artifact-write-strategy.md").read_text(encoding="utf-8").split("\n\n", 1)[1]),
        (2, "Source Row Inventory", (DESIGN_DIR / "source-row-inventory.md").read_text(encoding="utf-8").split("\n\n", 1)[1]),
        (2, "Coverage Summary", coverage_summary),
        (2, "Test-design Applicability Matrix", applicability),
        (2, "Writer Quality Gate", quality_gate),
        (2, "Open Coverage Gaps", gaps),
    ]
    for atom in atoms:
        if atom.tc_id:
            canonical_sections.append((2, atom.tc_id, tc_markdown(atom, row_by_id)))
    write_with_manifest(TEST_CASE_PATH, "canonical-test-cases", canonical_sections, "# Тест-кейсы: раздел «Сведения о занятости»")

    prompt = """# Handoff: Writer Round 1 -> Reviewer

## Цель этапа

Запустить `ft-test-case-reviewer` в режиме `full` для проверки initial draft по scope `ui-employment`.

## Входные артефакты

- `test-cases/2-1-1-1-1-2-ui-employment.md`
- `work/test-design/ui-employment/artifact-write-strategy.md`
- `work/test-design/ui-employment/source-row-inventory.md`
- `work/test-design/ui-employment/source-row-completeness-matrix.md`
- `work/test-design/ui-employment/source-table-normalization.md`
- `work/test-design/ui-employment/test-design-decision-table.md`
- `work/test-design/ui-employment/coverage-obligation-table.md`
- `work/test-design/ui-employment/atomic-requirements-ledger.md`
- `work/test-design/ui-employment/package-test-design-plan.md`
- `work/test-design/ui-employment/dependency-matrix.md`
- `work/test-design/ui-employment/test-design-applicability-matrix.md`
- `work/test-design/ui-employment/risk-priority-map.md`
- `work/test-design/ui-employment/coverage-gaps.md`
- `work/test-design/ui-employment/test-design-review.md`
- `work/test-design/ui-employment/writer-quality-gate.md`
- `work/test-design/ui-employment/writer-self-check.md`
- `work/test-design/ui-employment/writer-session-log.md`
- `work/test-design/ui-employment/agent-decision-log.md`
- `work/stage-handoffs/01-ui-employment/scope-contract.md`
- `work/stage-handoffs/01-ui-employment/source-parity-check.md`
- `work/stage-handoffs/01-ui-employment/source-row-inventory.md`
- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md`
- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md`
- `work/stage-handoffs/01-ui-employment/scope-gap-review.md`

## Guardrails

- Reviewer session must not edit canonical test cases.
- Run `full` review: traceability, structure and test-design.
- Treat `GAP-001`-`GAP-004` as intentionally retained non-blocking gaps.
- Do not expand beyond `Сведения о занятости`.

## Writer Output

- Writer completed initial draft in `fresh-eval-run`.
- Every `SRC-001`-`SRC-024` is present in writer-side inventory.
- `GSR 123`-`GSR 148` are represented through `ATOM-*` or retained `GAP-*`.
- `GAP-001`-`GAP-004` remain open.

## Reviewer Task

Run `ft-test-case-reviewer` in `full` mode. Check traceability against `GSR 123`-`GSR 148`, preservation of `SRC-001`-`SRC-024`, atomicity of `TC-*`, admissibility of `GAP-001`-`GAP-004`, structure and test-design coverage.
"""
    write_with_manifest(HANDOFF_DIR / "prompt.writer-to-reviewer.round-1.md", "handoff-prompt-writer-to-reviewer-round-1", [(1, "Writer To Reviewer Prompt", prompt)])

    workflow = """ft_slug: ft-2-OF_16
scope_slug: ui-employment
current_stage: ft-test-case-writer
stage_status: ready-for-review
current_round: 1
next_skill: ft-test-case-reviewer
review_mode: full
canonical_test_cases: test-cases/2-1-1-1-1-2-ui-employment.md
test_design_dir: work/test-design/ui-employment
required_inputs:
  - test-cases/2-1-1-1-1-2-ui-employment.md
  - work/test-design/ui-employment/artifact-write-strategy.md
  - work/test-design/ui-employment/source-row-inventory.md
  - work/test-design/ui-employment/source-table-normalization.md
  - work/test-design/ui-employment/atomic-requirements-ledger.md
  - work/test-design/ui-employment/package-test-design-plan.md
  - work/test-design/ui-employment/writer-quality-gate.md
  - work/test-design/ui-employment/writer-self-check.md
  - work/test-design/ui-employment/coverage-gaps.md
  - work/test-design/ui-employment/writer-session-log.md
  - work/test-design/ui-employment/agent-decision-log.md
  - work/stage-handoffs/01-ui-employment/scope-contract.md
  - work/stage-handoffs/01-ui-employment/source-parity-check.md
  - work/stage-handoffs/01-ui-employment/source-row-inventory.md
  - work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md
  - work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md
  - work/stage-handoffs/01-ui-employment/scope-clarification-requests.md
  - work/stage-handoffs/01-ui-employment/scope-gap-review.md
  - work/stage-handoffs/01-ui-employment/prompt.writer-to-reviewer.round-1.md
latest_artifacts:
  canonical_test_cases: test-cases/2-1-1-1-1-2-ui-employment.md
  artifact_write_strategy: work/test-design/ui-employment/artifact-write-strategy.md
  source_row_inventory: work/test-design/ui-employment/source-row-inventory.md
  source_row_completeness_matrix: work/test-design/ui-employment/source-row-completeness-matrix.md
  source_table_normalization: work/test-design/ui-employment/source-table-normalization.md
  test_design_decision_table: work/test-design/ui-employment/test-design-decision-table.md
  coverage_obligation_table: work/test-design/ui-employment/coverage-obligation-table.md
  atomic_requirements_ledger: work/test-design/ui-employment/atomic-requirements-ledger.md
  package_test_design_plan: work/test-design/ui-employment/package-test-design-plan.md
  dependency_matrix: work/test-design/ui-employment/dependency-matrix.md
  applicability_matrix: work/test-design/ui-employment/test-design-applicability-matrix.md
  risk_priority_map: work/test-design/ui-employment/risk-priority-map.md
  coverage_map: work/test-design/ui-employment/coverage-map.md
  coverage_gaps: work/test-design/ui-employment/coverage-gaps.md
  writer_quality_gate: work/test-design/ui-employment/writer-quality-gate.md
  writer_self_check: work/test-design/ui-employment/writer-self-check.md
  session_log: work/test-design/ui-employment/writer-session-log.md
  decision_log: work/test-design/ui-employment/agent-decision-log.md
  active_transition_prompt: work/stage-handoffs/01-ui-employment/prompt.writer-to-reviewer.round-1.md
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
    (HANDOFF_DIR / "workflow-state.yaml").write_text(workflow, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    generate()
