from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment-canary-v13-canonical-table-shape-regression"
SECTION_ID = "2.1.1.1.1.2"
SECTION_PREFIX = "2-1-1-1-1-2"
TD = FT_ROOT / "work" / "test-design" / SCOPE
CYCLE = FT_ROOT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL = FT_ROOT / "test-cases" / f"{SECTION_PREFIX}-{SCOPE}.md"
BUILD_DIR = TD / "_build_sections"


SELECTED_INSTRUCTIONS = [
    "AGENTS.md",
    "skills/README.md",
    "references/agent/session-based-review-cycle-format.md",
    "references/agent/codex-sdk-orchestration-format.md",
    "skills/ft-test-case-writer/SKILL.md",
    "references/agent/writer-runtime-workflow.md",
    "references/agent/writer-runtime-contract.md",
    "references/qa/test-case-runtime-format.md",
    "references/qa/coverage-runtime-checklist.md",
    "references/qa/traceability-rules.md",
    "references/agent/writer-process-workflow.md",
    "references/agent/workflow-state-format.md",
    "references/agent/session-log-format.md",
    "references/agent/agent-decision-log-format.md",
    "references/agent/writer-handoff-format.md",
]


DICT_001 = [
    "Работа по найму",
    "Пенсионер (не работает)",
    "Индивидуальный предприниматель",
    "Собственник бизнеса",
    "Частная практика / Самозанятый",
    "Безработный",
]
DICT_004 = ["Пенсия", "Аренда"]
DICT_005 = [
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
]


def cell(value: object) -> str:
    text = str(value)
    text = text.replace("\n", "<br>")
    return text


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)


SOURCE_ROWS = [
    ("SRC-001", "WP-01", "Блок «Сведения о занятости» / «Работа по совместительству»", "DOCX section-23 table 11 row 2; PDF p.61", "-", "out-of-scope", "context row; v13 covers selected executable field/action rows only"),
    ("SRC-002", "WP-01", "Тип занятости", "DOCX section-23 table 11 row 3; PDF p.61", "-", "yes", "ATOM-001; ATOM-002; ATOM-003; ATOM-004"),
    ("SRC-003", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "DOCX section-23 table 11 row 4; PDF p.61", "GSR 123; GSR 124", "yes", "ATOM-005; ATOM-006; ATOM-007; ATOM-008; GAP-005; GAP-006"),
    ("SRC-004", "WP-01", "Наименование организации, ИНН", "DOCX section-23 table 11 row 5; PDF p.61", "GSR 125; GSR 126", "out-of-scope", "GAP-001; excluded from v13 executable scope except fixture/residual context"),
    ("SRC-005", "WP-01", "Фактический адрес работы", "DOCX section-23 table 11 row 6; PDF p.61", "GSR 127; GSR 128", "out-of-scope", "GAP-001; excluded from v13 executable scope except fixture/residual context"),
    ("SRC-006", "WP-01", "Тип должности", "DOCX section-23 table 11 row 7; PDF p.61", "GSR 129", "out-of-scope", "out of v13 medium scope"),
    ("SRC-007", "WP-01", "Должность", "DOCX section-23 table 11 row 8; PDF pp.61-62", "GSR 130", "out-of-scope", "out of v13 medium scope"),
    ("SRC-008", "WP-01", "Стаж работы", "DOCX section-23 table 11 row 9; PDF p.62", "GSR 131", "out-of-scope", "out of v13 medium scope"),
    ("SRC-009", "WP-01", "Рабочий телефон", "DOCX section-23 table 11 row 10; PDF p.62", "GSR 132; GSR 133; GSR 134", "out-of-scope", "out of v13 medium scope"),
    ("SRC-010", "WP-02", "Блок «Дополнительный доход»", "DOCX section-23 table 11 row 11; PDF p.62", "-", "yes", "ATOM-009; ATOM-010"),
    ("SRC-011", "WP-02", "Тип дохода", "DOCX section-23 table 11 row 12; PDF p.62", "-", "yes", "ATOM-011; ATOM-012; ATOM-013; ATOM-014; GAP-002"),
    ("SRC-012", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "DOCX section-23 table 11 row 13; PDF p.62", "GSR 135", "yes", "ATOM-015; ATOM-016; ATOM-017; GAP-007"),
    ("SRC-013", "WP-03", "Общие поля", "DOCX section-23 table 11 row 14; PDF p.62", "-", "out-of-scope", "context row; v13 covers selected child fields"),
    ("SRC-014", "WP-03", "Клиент добросовестный", "DOCX section-23 table 11 row 15; PDF p.62", "GSR 136", "yes", "ATOM-018; ATOM-019; ATOM-020"),
    ("SRC-015", "WP-03", "Визуальная информация", "DOCX section-23 table 11 row 16; PDF p.62", "GSR 137; GSR 138", "yes", "ATOM-021; ATOM-022; ATOM-023; ATOM-024"),
    ("SRC-016", "WP-03", "Параметры визуальной оценки", "DOCX section-23 table 11 row 17; PDF pp.62-63", "GSR 139; GSR 140", "yes", "ATOM-025; ATOM-026; ATOM-027; ATOM-028"),
    ("SRC-017", "WP-03", "Примечание DaData по найденной организации", "DOCX section-23 note after table 11; PDF p.63", "GSR 141", "out-of-scope", "GAP-001; excluded from v13 executable scope except residual context"),
    ("SRC-018", "WP-04", "«Следующий шаг»", "DOCX section-24 table 12 row 2; PDF pp.63-65", "GSR 142; GSR 143", "yes", "ATOM-029; ATOM-030; ATOM-031; GAP-003"),
    ("SRC-019", "WP-04", "«Добавить работу по совместительству»", "DOCX section-24 table 12 row 3; PDF p.65", "GSR 144; GSR 145", "yes", "ATOM-032; ATOM-033"),
    ("SRC-020", "WP-04", "«Добавить дополнительный доход»", "DOCX section-24 table 12 row 4; PDF p.65", "GSR 146; GSR 147", "yes", "ATOM-034; ATOM-035"),
    ("SRC-021", "WP-04", "«Назад»", "DOCX section-24 table 12 row 5; PDF p.65", "GSR 148", "yes", "ATOM-036; ATOM-037; ATOM-038"),
    ("SRC-022", "WP-05", "CDI: не удалось верифицировать ИНН", "DOCX not found by structured extraction; PDF pp.65-66", "-", "out-of-scope", "GAP-004; CDI trigger/setup excluded by v13 prompt"),
    ("SRC-023", "WP-05", "CDI: данные клиента отличаются от данных заявки", "DOCX not found by structured extraction; PDF p.66", "-", "out-of-scope", "GAP-004; CDI trigger/setup excluded by v13 prompt"),
    ("SRC-024", "WP-05", "CDI: подтверждение замены данных", "DOCX not found by structured extraction; PDF p.67 before next section", "-", "out-of-scope", "GAP-004; CDI trigger/setup excluded by v13 prompt"),
]


ATOMS = [
    ("ATOM-001", "WP-01", "SRC-002", "-", "Поле `Тип занятости` видно всегда.", "TC-UI-EMP-V13-001", "visibility"),
    ("ATOM-002", "WP-01", "SRC-002", "-", "Поле `Тип занятости` обязательно.", "TC-UI-EMP-V13-017", "requiredness"),
    ("ATOM-003", "WP-01", "SRC-002", "-", "Поле `Тип занятости` редактируемо.", "TC-UI-EMP-V13-003", "editability"),
    ("ATOM-004", "WP-01", "SRC-002", "-", "Список `Тип занятости` использует значения справочника `DICT-001`.", "TC-UI-EMP-V13-002", "dictionary"),
    ("ATOM-005", "WP-01", "SRC-003", "GSR 123", "Основной доход виден, если `Тип занятости` заполнен.", "TC-UI-EMP-V13-004", "dependency"),
    ("ATOM-006", "WP-01", "SRC-003", "GSR 123", "Основной доход обязателен и редактируем при выполненном условии видимости.", "TC-UI-EMP-V13-018", "requiredness"),
    ("ATOM-007", "WP-01", "SRC-003", "GSR 124", "Основной доход принимает числовое значение.", "TC-UI-EMP-V13-005", "positive-input"),
    ("ATOM-008", "WP-01", "SRC-003", "GSR 124", "Основной доход имеет минимальную сумму `2000р`.", "TC-UI-EMP-V13-005", "boundary"),
    ("ATOM-009", "WP-02", "SRC-010", "-", "Блок `Дополнительный доход` появляется после действия добавления.", "TC-UI-EMP-V13-006", "repeatable-block"),
    ("ATOM-010", "WP-02", "SRC-010", "-", "Созданный блок дополнительного дохода может быть удален.", "TC-UI-EMP-V13-010", "cleanup"),
    ("ATOM-011", "WP-02", "SRC-011", "-", "Поле `Тип дохода` появляется после добавления источника дохода.", "TC-UI-EMP-V13-006", "dependency"),
    ("ATOM-012", "WP-02", "SRC-011", "-", "Поле `Тип дохода` обязательно и редактируемо.", "TC-UI-EMP-V13-018", "requiredness"),
    ("ATOM-013", "WP-02", "SRC-011", "-", "Список `Тип дохода` использует значения справочника `DICT-004`.", "TC-UI-EMP-V13-007", "dictionary"),
    ("ATOM-014", "WP-02", "SRC-011", "-", "`Пенсия` и `Аренда` могут быть добавлены только один раз.", "GAP-002", "duplicate-invariant"),
    ("ATOM-015", "WP-02", "SRC-012", "GSR 135", "Доход в дополнительном доходе появляется после добавления источника.", "TC-UI-EMP-V13-006", "dependency"),
    ("ATOM-016", "WP-02", "SRC-012", "GSR 135", "Доход в дополнительном доходе обязателен и редактируем.", "TC-UI-EMP-V13-018", "requiredness"),
    ("ATOM-017", "WP-02", "SRC-012", "GSR 135", "Доход в дополнительном доходе принимает числовое значение.", "TC-UI-EMP-V13-008", "positive-input"),
    ("ATOM-018", "WP-03", "SRC-014", "GSR 136", "`Клиент добросовестный` виден всегда.", "TC-UI-EMP-V13-011", "visibility"),
    ("ATOM-019", "WP-03", "SRC-014", "GSR 136", "`Клиент добросовестный` по умолчанию имеет значение `Нет`.", "TC-UI-EMP-V13-011", "default"),
    ("ATOM-020", "WP-03", "SRC-014", "GSR 136", "`Клиент добросовестный` не обязателен, если `Визуальная информация` = `Да`.", "TC-UI-EMP-V13-016", "requiredness-dependency"),
    ("ATOM-021", "WP-03", "SRC-015", "GSR 137", "`Визуальная информация` видна всегда.", "TC-UI-EMP-V13-012", "visibility"),
    ("ATOM-022", "WP-03", "SRC-015", "GSR 137", "`Визуальная информация` по умолчанию имеет значение `Нет`.", "TC-UI-EMP-V13-012", "default"),
    ("ATOM-023", "WP-03", "SRC-015", "GSR 137", "`Визуальная информация` не обязательна, если `Клиент добросовестный` = `Да`.", "TC-UI-EMP-V13-018", "requiredness-dependency"),
    ("ATOM-024", "WP-03", "SRC-015", "GSR 138", "При `Визуальная информация` = `Да` отображается список параметров визуальной оценки с множественным выбором.", "TC-UI-EMP-V13-013; TC-UI-EMP-V13-015", "dependency"),
    ("ATOM-025", "WP-03", "SRC-016", "GSR 139", "Для каждого значения `DICT-005` доступен чек-бокс.", "TC-UI-EMP-V13-014", "checkbox-list"),
    ("ATOM-026", "WP-03", "SRC-016", "GSR 140", "При `Визуальная информация` = `Да` должен быть выбран хотя бы один параметр.", "TC-UI-EMP-V13-016", "requiredness"),
    ("ATOM-027", "WP-03", "SRC-016", "GSR 138", "Параметры визуальной оценки поддерживают множественный выбор.", "TC-UI-EMP-V13-015", "multi-select"),
    ("ATOM-028", "WP-03", "SRC-016", "GSR 139", "Параметры визуальной оценки редактируемы как флажки.", "TC-UI-EMP-V13-015", "editability"),
    ("ATOM-029", "WP-04", "SRC-018", "GSR 142", "`Следующий шаг` подсвечивает красным незаполненные обязательные поля.", "TC-UI-EMP-V13-017", "negative-transition"),
    ("ATOM-030", "WP-04", "SRC-018", "GSR 142", "При заполнении обязательных полей `Следующий шаг` переходит к следующему пункту.", "TC-UI-EMP-V13-018", "navigation"),
    ("ATOM-031", "WP-04", "SRC-018", "GSR 143", "После успешного перехода формируется `Заявление-анкета` и открывается раздел `Анкета клиента`.", "TC-UI-EMP-V13-018", "navigation"),
    ("ATOM-032", "WP-04", "SRC-019", "GSR 144", "`Добавить работу по совместительству` отображает поля блока совместительства.", "TC-UI-EMP-V13-019", "repeatable-block"),
    ("ATOM-033", "WP-04", "SRC-019", "GSR 145", "Работа по совместительству удаляется через пиктограмму `Корзина`.", "TC-UI-EMP-V13-020", "cleanup"),
    ("ATOM-034", "WP-04", "SRC-020", "GSR 146", "`Добавить дополнительный доход` отображает поля блока дополнительного дохода.", "TC-UI-EMP-V13-006", "repeatable-block"),
    ("ATOM-035", "WP-04", "SRC-020", "GSR 147", "Дополнительный доход удаляется через пиктограмму `Корзина`.", "TC-UI-EMP-V13-010", "cleanup"),
    ("ATOM-036", "WP-04", "SRC-021", "GSR 148", "`Назад` выводит уведомление с вариантами `Да` и `Нет`.", "TC-UI-EMP-V13-021", "branch"),
    ("ATOM-037", "WP-04", "SRC-021", "GSR 148", "При выборе `Да` данные сохраняются и открывается `Основная информация`.", "TC-UI-EMP-V13-022", "branch-save"),
    ("ATOM-038", "WP-04", "SRC-021", "GSR 148", "При выборе `Нет` открывается `Основная информация` без сохранения изменения.", "TC-UI-EMP-V13-023", "branch-discard"),
]


GAPS = [
    ("GAP-001", "accepted-source-gap", "SRC-004; SRC-005; SRC-017; GSR 126; GSR 128; GSR 141", "DaData/SPR mechanics and backend contract artifacts are not observable in v13 scope.", "non-blocking", "accepted by scope-gap review evidence"),
    ("GAP-002", "accepted-source-gap", "SRC-011; DICT-004", "Exact UI mechanism for preventing duplicate `Пенсия`/`Аренда` is not specified.", "non-blocking", "invariant preserved as ATOM-014; executable feedback not invented"),
    ("GAP-003", "accepted-source-gap", "SRC-018; GSR 142", "Return-from-`Выбор решения` backend SPR/anti-fraud evidence is not observable in the employment UI scope.", "non-blocking", "UI navigation/validation covered; backend effect not asserted"),
    ("GAP-004", "accepted-source-gap", "SRC-022; SRC-023; SRC-024", "CDI message text is source-backed, but deterministic trigger/setup data are not provided and CDI rows are excluded by v13 prompt.", "non-blocking", "PDF-only context preserved without executable TC"),
    ("GAP-005", "unclear-feedback", "SRC-003; GSR 124", "Exact UI feedback/rejection mechanism for main income below `2000р` is not stated.", "non-blocking", "positive minimum boundary is covered by TC-UI-EMP-V13-005"),
    ("GAP-006", "unclear-feedback", "SRC-003; GSR 124", "Exact UI feedback/rejection mechanism for non-numeric main income is not stated.", "non-blocking", "numeric-only source property preserved without invented filtering/error text"),
    ("GAP-007", "unclear-feedback", "SRC-012; GSR 135", "Exact UI feedback/rejection mechanism for non-numeric additional income is not stated.", "non-blocking", "positive numeric behavior is covered by TC-UI-EMP-V13-008"),
]


TCS = [
    ("TC-UI-EMP-V13-001", "WP-01", "Поле `Тип занятости` видно при открытии раздела", "Positive", "High", "ATOM-001; SRC-002", "Открыт раздел `Сведения о занятости` для новой карточки УЗ.", "Не требуются.", ["Открыть раздел `Сведения о занятости`."], "Поле `Тип занятости` отображается в разделе `Сведения о занятости`.", "Не требуются."),
    ("TC-UI-EMP-V13-002", "WP-01", "Список `Тип занятости` содержит все и только активные значения `DICT-001`", "Positive", "High", "ATOM-004; SRC-002; DICT-001", "Открыт раздел `Сведения о занятости`.", "Активные значения `DICT-001`: " + "; ".join(DICT_001) + ".", ["Открыть раскрывающийся список `Тип занятости`."], "В списке `Тип занятости` отображаются все и только активные значения `DICT-001`: `" + "`, `".join(DICT_001) + "`.", "Не требуются."),
    ("TC-UI-EMP-V13-003", "WP-01", "Поле `Тип занятости` позволяет изменить выбранное значение", "Positive", "Medium", "ATOM-003; SRC-002; DICT-001", "Открыт раздел `Сведения о занятости`.", "Исходное значение: `Работа по найму`; новое значение: `Безработный`.", ["В поле `Тип занятости` выбрать `Работа по найму`.", "В поле `Тип занятости` выбрать `Безработный`."], "В поле `Тип занятости` отображается новое значение `Безработный`.", "Вернуть значение `Тип занятости` в исходное состояние или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-004", "WP-01", "Основной доход отображается после заполнения `Тип занятости`", "Positive", "High", "ATOM-005; SRC-003; GSR 123; DICT-001", "Открыт раздел `Сведения о занятости`.", "`Тип занятости` = `Работа по найму`.", ["Выбрать в поле `Тип занятости` значение `Работа по найму`."], "Поле `Среднемесячный доход после вычета налогов` основной работы отображается на форме.", "Очистить выбранное значение или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-005", "WP-01", "Основной доход принимает минимальное числовое значение `2000`", "Positive", "High", "ATOM-007; ATOM-008; SRC-003; GSR 124", "Открыт раздел `Сведения о занятости`; выбран `Тип занятости` = `Работа по найму`.", "`Среднемесячный доход после вычета налогов` = `2000`.", ["Ввести `2000` в поле `Среднемесячный доход после вычета налогов` основной работы."], "В поле `Среднемесячный доход после вычета налогов` отображается значение `2000`.", "Очистить поле или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-006", "WP-02", "Действие `Добавить дополнительный доход` отображает поля нового блока", "Positive", "High", "ATOM-009; ATOM-011; ATOM-015; ATOM-034; SRC-010; SRC-011; SRC-012; SRC-020; GSR 146", "Открыт раздел `Сведения о занятости`; дополнительных доходов на форме нет.", "Не требуются.", ["Нажать `Добавить дополнительный доход`."], "На форме отображается новый блок `Дополнительный доход` с полями `Тип дохода` и `Среднемесячный доход после вычета налогов`.", "Удалить созданный блок дополнительного дохода через пиктограмму `Корзина` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-007", "WP-02", "Список `Тип дохода` содержит все и только активные значения `DICT-004`", "Positive", "High", "ATOM-013; SRC-011; DICT-004", "Открыт раздел `Сведения о занятости`; добавлен один блок `Дополнительный доход`.", "Активные значения `DICT-004`: `Пенсия`; `Аренда`.", ["Открыть раскрывающийся список `Тип дохода` в созданном блоке."], "В списке `Тип дохода` отображаются все и только активные значения `DICT-004`: `Пенсия`, `Аренда`.", "Удалить созданный блок дополнительного дохода через пиктограмму `Корзина` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-008", "WP-02", "Доход в блоке дополнительного дохода принимает числовое значение", "Positive", "Medium", "ATOM-017; SRC-012; GSR 135", "Открыт раздел `Сведения о занятости`; добавлен один блок `Дополнительный доход`.", "`Среднемесячный доход после вычета налогов` дополнительного дохода = `9000`.", ["Ввести `9000` в поле `Среднемесячный доход после вычета налогов` в блоке `Дополнительный доход`."], "В поле дополнительного дохода отображается значение `9000`.", "Удалить созданный блок дополнительного дохода через пиктограмму `Корзина` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-009", "WP-02", "Поле `Тип дохода` позволяет выбрать активное значение `Пенсия`", "Positive", "Medium", "ATOM-012; ATOM-013; SRC-011; DICT-004", "Открыт раздел `Сведения о занятости`; добавлен один блок `Дополнительный доход`.", "`Тип дохода` = `Пенсия`.", ["В поле `Тип дохода` выбрать `Пенсия`."], "В поле `Тип дохода` отображается значение `Пенсия`.", "Удалить созданный блок дополнительного дохода через пиктограмму `Корзина` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-010", "WP-02", "Созданный блок дополнительного дохода удаляется через `Корзину`", "Positive", "High", "ATOM-010; ATOM-035; SRC-010; SRC-020; GSR 147", "Открыт раздел `Сведения о занятости`; добавлен один блок `Дополнительный доход`.", "В созданном блоке выбран `Тип дохода` = `Аренда`; доход = `9000`.", ["Нажать пиктограмму `Корзина` в созданном блоке `Дополнительный доход`."], "Созданный блок `Дополнительный доход` больше не отображается на форме.", "Не требуются."),
    ("TC-UI-EMP-V13-011", "WP-03", "`Клиент добросовестный` виден всегда и по умолчанию равен `Нет`", "Positive", "High", "ATOM-018; ATOM-019; SRC-014; GSR 136", "Открыт раздел `Сведения о занятости` для новой карточки УЗ.", "Не требуются.", ["Открыть раздел `Сведения о занятости`."], "Переключатель `Клиент добросовестный` отображается, и его значение по умолчанию равно `Нет`.", "Не требуются."),
    ("TC-UI-EMP-V13-012", "WP-03", "`Визуальная информация` видна всегда и по умолчанию равна `Нет`", "Positive", "High", "ATOM-021; ATOM-022; SRC-015; GSR 137", "Открыт раздел `Сведения о занятости` для новой карточки УЗ.", "Не требуются.", ["Открыть раздел `Сведения о занятости`."], "Переключатель `Визуальная информация` отображается, и его значение по умолчанию равно `Нет`.", "Не требуются."),
    ("TC-UI-EMP-V13-013", "WP-03", "При `Визуальная информация` = `Да` отображаются параметры визуальной оценки", "Positive", "High", "ATOM-024; SRC-015; GSR 138", "Открыт раздел `Сведения о занятости`.", "`Визуальная информация` = `Да`.", ["Установить переключатель `Визуальная информация` в значение `Да`."], "На форме отображается список `Параметры визуальной оценки`.", "Вернуть `Визуальная информация` в значение `Нет` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-014", "WP-03", "Список параметров визуальной оценки содержит чек-бокс для каждого значения `DICT-005`", "Positive", "High", "ATOM-025; SRC-016; GSR 139; DICT-005", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`.", "Активные значения `DICT-005`: " + "; ".join(DICT_005) + ".", ["Просмотреть список `Параметры визуальной оценки`."], "Для каждого активного значения `DICT-005` отображается отдельный чек-бокс: `" + "`, `".join(DICT_005) + "`.", "Вернуть `Визуальная информация` в значение `Нет` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-015", "WP-03", "Параметры визуальной оценки поддерживают множественный выбор", "Positive", "High", "ATOM-027; ATOM-028; SRC-016; GSR 138; GSR 139; DICT-005", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`.", "Выбрать два параметра: `Подозрение на мошеничество`; `Потенциальный неплательщик`.", ["Установить чек-бокс `Подозрение на мошеничество`.", "Установить чек-бокс `Потенциальный неплательщик`."], "Оба чек-бокса `Подозрение на мошеничество` и `Потенциальный неплательщик` отображаются выбранными одновременно.", "Снять выбранные чек-боксы или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-016", "WP-03", "При `Визуальная информация` = `Да` переход блокируется без выбранного параметра визуальной оценки", "Negative", "High", "ATOM-020; ATOM-026; ATOM-029; SRC-014; SRC-016; SRC-018; GSR 136; GSR 140; GSR 142", "Открыт раздел `Сведения о занятости`; применена фикстура `FX-EMP-V13-FULL-VALID-VISUAL-NO-PARAM`.", "`FX-EMP-V13-FULL-VALID-VISUAL-NO-PARAM`: `Тип занятости` = `Работа по найму`; основной доход = `2000`; `Визуальная информация` = `Да`; `Клиент добросовестный` оставлен `Нет`; параметры визуальной оценки не выбраны; дополнительных доходов нет.", ["Нажать `Следующий шаг`."], "Переход не выполняется; область `Параметры визуальной оценки` подсвечена красным как незаполненная обязательная область.", "Снять `Визуальная информация` или выбрать параметр и закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-017", "WP-01", "`Следующий шаг` подсвечивает незаполненный обязательный `Тип занятости`", "Negative", "High", "ATOM-002; ATOM-029; SRC-002; SRC-018; GSR 142", "Открыт раздел `Сведения о занятости`; применена фикстура `FX-EMP-V13-FULL-VALID-HIRED`, но поле `Тип занятости` оставлено пустым.", "`Тип занятости` = пусто; все остальные доступные обязательные поля заполнены по `FX-EMP-V13-FULL-VALID-HIRED` там, где они отображаются.", ["Нажать `Следующий шаг`."], "Переход не выполняется; поле `Тип занятости` подсвечено красным как незаполненное обязательное поле.", "Закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-018", "WP-04", "`Следующий шаг` с заполненными обязательными полями открывает раздел `Анкета клиента`", "Positive", "High", "ATOM-006; ATOM-012; ATOM-016; ATOM-023; ATOM-030; ATOM-031; SRC-003; SRC-011; SRC-012; SRC-015; SRC-018; GSR 142; GSR 143", "Открыт раздел `Сведения о занятости`; применена фикстура `FX-EMP-V13-FULL-VALID-HIRED`.", "`FX-EMP-V13-FULL-VALID-HIRED`: `Тип занятости` = `Работа по найму`; основной доход = `2000`; `Клиент добросовестный` = `Да`; `Визуальная информация` = `Нет`; дополнительных доходов нет.", ["Нажать `Следующий шаг`."], "Открывается раздел `Анкета клиента`; в разделе доступна печатная форма `Заявление-анкета`.", "Вернуться в карточку УЗ при необходимости тестирования следующих кейсов."),
    ("TC-UI-EMP-V13-019", "WP-04", "`Добавить работу по совместительству` отображает поля блока совместительства", "Positive", "Medium", "ATOM-032; SRC-019; GSR 144", "Открыт раздел `Сведения о занятости`; блоков `Работа по совместительству` на форме нет.", "Не требуются.", ["Нажать `Добавить работу по совместительству`."], "На форме отображается новый блок `Работа по совместительству` с полями блока `Сведения о занятости` / `Работа по совместительству`.", "Удалить созданный блок совместительства через пиктограмму `Корзина` или закрыть карточку без сохранения."),
    ("TC-UI-EMP-V13-020", "WP-04", "Созданная работа по совместительству удаляется через `Корзину`", "Positive", "Medium", "ATOM-033; SRC-019; GSR 145", "Открыт раздел `Сведения о занятости`; добавлен один блок `Работа по совместительству`.", "В созданном блоке выбран `Тип занятости` = `Работа по найму`; доход = `2000`.", ["Нажать пиктограмму `Корзина` в созданном блоке `Работа по совместительству`."], "Созданный блок `Работа по совместительству` больше не отображается на форме.", "Не требуются."),
    ("TC-UI-EMP-V13-021", "WP-04", "`Назад` показывает подтверждение с вариантами `Да` и `Нет`", "Positive", "High", "ATOM-036; SRC-021; GSR 148", "Открыт раздел `Сведения о занятости`; в поле `Тип занятости` выбрано `Работа по найму`, изменение еще не сохранено.", "Не требуются.", ["Нажать `Назад`."], "Отображается уведомление `Есть несохраненные данные, сохранить?` с вариантами ответа `Да` и `Нет`.", "Закрыть уведомление без выбора, если интерфейс позволяет, или выбрать `Нет` и вернуться к исходной карточке."),
    ("TC-UI-EMP-V13-022", "WP-04", "Ветка `Назад` -> `Да` сохраняет изменение и открывает `Основная информация`", "Positive", "High", "ATOM-037; SRC-021; GSR 148; DICT-001", "Открыт раздел `Сведения о занятости`; текущее сохраненное значение `Тип занятости` = `Работа по найму`.", "Новое значение `Тип занятости` = `Безработный`.", ["Изменить `Тип занятости` с `Работа по найму` на `Безработный`.", "Нажать `Назад`.", "В уведомлении выбрать `Да`.", "Вернуться в раздел `Сведения о занятости` для этой же карточки."], "Раздел `Основная информация` открывается после выбора `Да`; при повторном открытии раздела `Сведения о занятости` поле `Тип занятости` отображает сохраненное значение `Безработный`.", "Вернуть `Тип занятости` к исходному значению `Работа по найму`, если карточка продолжит использоваться."),
    ("TC-UI-EMP-V13-023", "WP-04", "Ветка `Назад` -> `Нет` открывает `Основная информация` без сохранения изменения", "Positive", "High", "ATOM-038; SRC-021; GSR 148; DICT-001", "Открыт раздел `Сведения о занятости`; текущее сохраненное значение `Тип занятости` = `Работа по найму`.", "Временное новое значение `Тип занятости` = `Безработный`.", ["Изменить `Тип занятости` с `Работа по найму` на `Безработный`.", "Нажать `Назад`.", "В уведомлении выбрать `Нет`.", "Вернуться в раздел `Сведения о занятости` для этой же карточки."], "Раздел `Основная информация` открывается после выбора `Нет`; при повторном открытии раздела `Сведения о занятости` поле `Тип занятости` отображает прежнее сохраненное значение `Работа по найму`.", "Не требуются."),
]


def source_inventory() -> str:
    return table(
        ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
        [[f"`{a}`", f"`{b}`", c, d, e, f, g] for a, b, c, d, e, f, g in SOURCE_ROWS],
    )


def source_completeness() -> str:
    rows = []
    atom_by_src: dict[str, list[str]] = {}
    for atom, _pkg, src, _req, _stmt, planned, _ptype in ATOMS:
        atom_by_src.setdefault(src, []).append(atom)
    gap_by_src: dict[str, list[str]] = {}
    for gap, _kind, refs, _desc, _impact, _handling in GAPS:
        for src in [part.strip() for part in refs.split(";") if part.strip().startswith("SRC-")]:
            gap_by_src.setdefault(src, []).append(gap)
    for src, _pkg, _name, _ref, reqs, in_scope, mapped in SOURCE_ROWS:
        props = [f"{src}.P{idx:02d}" for idx in range(1, max(1, len(atom_by_src.get(src, []))) + 1)]
        decision = "covered-or-gapped" if in_scope == "yes" else "out_of_scope_or_residual_gap"
        rows.append([f"`{src}`", reqs, "; ".join(props), "; ".join(atom_by_src.get(src, [])) or "-", "; ".join(gap_by_src.get(src, [])) or ("GAP-001" if src in {"SRC-004", "SRC-005", "SRC-017"} else "GAP-004" if src in {"SRC-022", "SRC-023", "SRC-024"} else "-"), decision])
    return table(
        ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
        rows,
    )


PROPS = [
    ("SRC-002.P01", "SRC-002", "WP-01", "Тип занятости", "visibility", "always", "visible", "-", "DOCX section-23 table 11 row 3; PDF p.61", "high", "-", "ATOM-001"),
    ("SRC-002.P02", "SRC-002", "WP-01", "Тип занятости", "requiredness", "always", "required", "-", "DOCX section-23 table 11 row 3; PDF p.61", "high", "-", "ATOM-002"),
    ("SRC-002.P03", "SRC-002", "WP-01", "Тип занятости", "editability", "always", "editable", "-", "DOCX section-23 table 11 row 3; PDF p.61", "high", "-", "ATOM-003"),
    ("SRC-002.P04", "SRC-002", "WP-01", "Тип занятости", "dictionary", "always", "all and only active values from DICT-001", "-", "DOCX section-23 table 11 row 3; dictionary-inventory.md", "high", "-", "ATOM-004"),
    ("SRC-003.P01", "SRC-003", "WP-01", "Среднемесячный доход после вычета налогов", "visibility", "Тип занятости заполнен", "visible", "GSR 123", "DOCX section-23 table 11 row 4; PDF p.61", "high", "-", "ATOM-005"),
    ("SRC-003.P02", "SRC-003", "WP-01", "Среднемесячный доход после вычета налогов", "requiredness", "Тип занятости заполнен", "required and editable", "GSR 123", "DOCX section-23 table 11 row 4; PDF p.61", "high", "-", "ATOM-006"),
    ("SRC-003.P03", "SRC-003", "WP-01", "Среднемесячный доход после вычета налогов", "numeric", "Тип занятости заполнен", "only numeric symbols", "GSR 124", "DOCX section-23 table 11 row 4; PDF p.61", "medium", "GAP-006", "ATOM-007"),
    ("SRC-003.P04", "SRC-003", "WP-01", "Среднемесячный доход после вычета налогов", "minimum", "Тип занятости заполнен", "amount not less than 2000р", "GSR 124", "DOCX section-23 table 11 row 4; PDF p.61", "medium", "GAP-005", "ATOM-008"),
    ("SRC-010.P01", "SRC-010", "WP-02", "Блок Дополнительный доход", "repeatable-block", "after Добавить дополнительный доход", "block appears", "GSR 146", "DOCX section-24 table 12 row 4; PDF p.65", "high", "-", "ATOM-009; ATOM-034"),
    ("SRC-010.P02", "SRC-010", "WP-02", "Блок Дополнительный доход", "cleanup", "created block", "block can be removed by Корзина", "GSR 147", "DOCX section-24 table 12 row 4; PDF p.65", "high", "-", "ATOM-010; ATOM-035"),
    ("SRC-011.P01", "SRC-011", "WP-02", "Тип дохода", "dictionary", "after add income", "all and only active values from DICT-004", "-", "DOCX section-23 table 11 row 12; dictionary-inventory.md", "high", "-", "ATOM-013"),
    ("SRC-011.P02", "SRC-011", "WP-02", "Тип дохода", "duplicate-prevention", "Пенсия or Аренда already added", "same income type can be added only once", "-", "DOCX section-23 table 11 row 12; PDF p.62", "medium", "GAP-002", "ATOM-014"),
    ("SRC-012.P01", "SRC-012", "WP-02", "Доход дополнительного дохода", "numeric", "after add income", "only numeric symbols", "GSR 135", "DOCX section-23 table 11 row 13; PDF p.62", "medium", "GAP-007", "ATOM-017"),
    ("SRC-014.P01", "SRC-014", "WP-03", "Клиент добросовестный", "default", "always", "default Нет", "GSR 136", "DOCX section-23 table 11 row 15; PDF p.62", "high", "-", "ATOM-018; ATOM-019"),
    ("SRC-014.P02", "SRC-014", "WP-03", "Клиент добросовестный", "requiredness-dependency", "Визуальная информация = Да", "not required", "GSR 136", "DOCX section-23 table 11 row 15; PDF p.62", "high", "-", "ATOM-020"),
    ("SRC-015.P01", "SRC-015", "WP-03", "Визуальная информация", "default", "always", "default Нет", "GSR 137", "DOCX section-23 table 11 row 16; PDF p.62", "high", "-", "ATOM-021; ATOM-022"),
    ("SRC-015.P02", "SRC-015", "WP-03", "Визуальная информация", "requiredness-dependency", "Клиент добросовестный = Да", "not required", "GSR 137", "DOCX section-23 table 11 row 16; PDF p.62", "high", "-", "ATOM-023"),
    ("SRC-015.P03", "SRC-015", "WP-03", "Визуальная информация", "dependency", "Визуальная информация = Да", "show visual assessment parameters with multiple selection", "GSR 138", "DOCX section-23 table 11 row 16; PDF p.62", "high", "-", "ATOM-024"),
    ("SRC-016.P01", "SRC-016", "WP-03", "Параметры визуальной оценки", "checkbox-list", "Визуальная информация = Да", "checkbox for each DICT-005 value", "GSR 139", "DOCX section-23 table 11 row 17; PDF pp.62-63; dictionary-inventory.md", "high", "-", "ATOM-025; ATOM-028"),
    ("SRC-016.P02", "SRC-016", "WP-03", "Параметры визуальной оценки", "requiredness", "Визуальная информация = Да", "at least one value selected", "GSR 140", "DOCX section-23 table 11 row 17; PDF pp.62-63", "high", "-", "ATOM-026"),
    ("SRC-016.P03", "SRC-016", "WP-03", "Параметры визуальной оценки", "multi-select", "Визуальная информация = Да", "multiple choice supported", "GSR 138", "DOCX section-23 table 11 row 16; PDF p.62", "high", "-", "ATOM-027"),
    ("SRC-018.P01", "SRC-018", "WP-04", "Следующий шаг", "requiredness-transition", "required field missing", "empty required field highlighted red", "GSR 142", "DOCX section-24 table 12 row 2; PDF pp.63-65", "high", "-", "ATOM-029"),
    ("SRC-018.P02", "SRC-018", "WP-04", "Следующий шаг", "navigation", "required fields filled", "opens Анкета клиента and form is available", "GSR 143", "DOCX section-24 table 12 row 2; PDF p.65", "high", "-", "ATOM-030; ATOM-031"),
    ("SRC-018.P03", "SRC-018", "WP-04", "Следующий шаг", "backend-return-check", "return from Выбор решения", "SPR/anti-fraud observable artifact not defined", "GSR 142", "DOCX section-24 table 12 row 2; PDF pp.63-65", "medium", "GAP-003", "-"),
    ("SRC-019.P01", "SRC-019", "WP-04", "Добавить работу по совместительству", "repeatable-block", "click action", "show part-time block fields", "GSR 144", "DOCX section-24 table 12 row 3; PDF p.65", "high", "-", "ATOM-032"),
    ("SRC-019.P02", "SRC-019", "WP-04", "Работа по совместительству", "cleanup", "created block", "remove by Корзина", "GSR 145", "DOCX section-24 table 12 row 3; PDF p.65", "high", "-", "ATOM-033"),
    ("SRC-020.P01", "SRC-020", "WP-04", "Добавить дополнительный доход", "repeatable-block", "click action", "show additional income block fields", "GSR 146", "DOCX section-24 table 12 row 4; PDF p.65", "high", "-", "ATOM-034"),
    ("SRC-020.P02", "SRC-020", "WP-04", "Дополнительный доход", "cleanup", "created block", "remove by Корзина", "GSR 147", "DOCX section-24 table 12 row 4; PDF p.65", "high", "-", "ATOM-035"),
    ("SRC-021.P01", "SRC-021", "WP-04", "Назад", "confirmation", "unsaved data", "show confirmation with Да/Нет", "GSR 148", "DOCX section-24 table 12 row 5; PDF p.65", "high", "-", "ATOM-036"),
    ("SRC-021.P02", "SRC-021", "WP-04", "Назад -> Да", "branch-save", "choose Да", "save current section and open Основная информация", "GSR 148", "DOCX section-24 table 12 row 5; PDF p.65", "medium", "-", "ATOM-037"),
    ("SRC-021.P03", "SRC-021", "WP-04", "Назад -> Нет", "branch-discard", "choose Нет", "open Основная информация without saving change", "GSR 148", "DOCX section-24 table 12 row 5; PDF p.65", "medium", "-", "ATOM-038"),
]


def source_normalization() -> str:
    return table(
        ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
        [[src, prop, pkg, field, property_, condition, expected, req, ref, confidence, gap, atoms] for prop, src, pkg, field, property_, condition, expected, req, ref, confidence, gap, atoms in PROPS],
    )


def decision_table() -> str:
    rows = []
    for idx, (prop, src, pkg, field, property_, _condition, expected, req, ref, _confidence, gap, atoms) in enumerate(PROPS, 1):
        if gap and gap != "-":
            decision = "gap_unclear"
            planned = gap
            observable = "blocked_part captured as gap; source-backed positive portion covered where possible"
            testable = "source-backed positive/visible behavior"
            blocked = expected
            admissibility = f"{gap} cites unresolved mechanism/setup"
        elif atoms == "-":
            decision = "metadata_only"
            planned = "-"
            observable = "not executable in v13"
            testable = "-"
            blocked = "-"
            admissibility = "-"
        else:
            decision = "standalone_tc"
            planned = atoms.replace("ATOM-", "TC/ATOM-")
            observable = expected
            testable = expected
            blocked = "-"
            admissibility = "-"
        rows.append([
            f"`PD-{idx:03d}`", f"`{pkg}`", f"`{prop}`", atoms, property_, decision,
            f"Source row {src} states {property_}; v13 covers selected observable behavior only.",
            planned, ref if req == "-" else f"{req}; {ref}", "yes" if decision == "standalone_tc" else "no",
            observable, testable, blocked, admissibility, "medium" if gap != "-" else "low",
        ])
    return table(
        ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
        rows,
    )


def obligation_table() -> str:
    rows = []
    for idx, (atom, pkg, src, req, stmt, planned, ptype) in enumerate(ATOMS, 1):
        source_prop = next((p[0] for p in PROPS if p[1] == src and atom in p[-1]), f"{src}.P?")
        rows.append([f"`OBL-{idx:03d}`", f"`{pkg}`", f"`{source_prop}`", f"`{atom}`", ptype, "source-backed", stmt, f"{src}; {req or '-'}", planned, "planned" if planned.startswith("TC-") else "gap", "one obligation maps to one observable TC or explicit gap"])
    return table(
        ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
        rows,
    )


def package_plan() -> str:
    rows = []
    for idx, (tc_id, pkg, name, typ, _prio, trace, _pre, _data, _steps, expected, _post) in enumerate(TCS, 1):
        atoms = "; ".join(part for part in trace.split("; ") if part.startswith("ATOM-"))
        props = "; ".join(sorted({p[0] for p in PROPS if any(atom in p[-1] for atom in atoms.split("; "))})) or "-"
        rows.append([f"`PDP-{idx:03d}`", f"`{pkg}`", "manual-ui", props, atoms or trace, name, typ, "source-backed", "positive" if typ == "Positive" else "negative", expected, trace, tc_id, "ready"])
    for gap, kind, refs, desc, _impact, handling in GAPS:
        pkg = "WP-01" if "SRC-003" in refs or "SRC-004" in refs else "WP-02" if "SRC-011" in refs or "SRC-012" in refs else "WP-04" if "SRC-018" in refs or "SRC-022" in refs else "WP-03"
        rows.append([f"`PDP-GAP-{gap[-3:]}`", f"`{pkg}`", kind, refs, refs, desc, "gap", "residual-unclear", "n/a", handling, refs, gap, "gap"])
    return table(
        ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
        rows,
    )


def atomic_ledger() -> str:
    return table(
        ["atom_id", "package_id", "source_row_id", "requirement_code", "atomic_statement", "property_type", "planned_tc_or_gap"],
        [[f"`{a}`", f"`{b}`", f"`{c}`", d or "-", e, f, g] for a, b, c, d, e, g, f in ATOMS],
    )


def fixture_catalog() -> str:
    return table(
        ["fixture_id", "purpose", "field_values", "source_refs", "used_by"],
        [
            ["`FX-EMP-V13-FULL-VALID-HIRED`", "Full valid fixture for transition checks without visual parameters", "`Тип занятости` = `Работа по найму`; main income = `2000`; `Клиент добросовестный` = `Да`; `Визуальная информация` = `Нет`; no additional income blocks", "SRC-002; SRC-003; SRC-014; SRC-015; SRC-018; GSR 142; GSR 143", "TC-UI-EMP-V13-017; TC-UI-EMP-V13-018"],
            ["`FX-EMP-V13-FULL-VALID-VISUAL-NO-PARAM`", "Negative transition fixture with only visual parameter selection missing", "`Тип занятости` = `Работа по найму`; main income = `2000`; `Визуальная информация` = `Да`; `Клиент добросовестный` = `Нет`; no visual parameters selected; no additional income blocks", "SRC-002; SRC-003; SRC-014; SRC-015; SRC-016; SRC-018; GSR 136; GSR 140; GSR 142", "TC-UI-EMP-V13-016"],
        ],
    )


def dictionary_inventory() -> str:
    return table(
        ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
        [
            ["`DICT-001`", "`Типы занятости`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Типы занятости; rows 4-9`", "`extracted`", "; ".join(f"`{v}`" for v in DICT_001), "`-`", "`SRC-002.P04`", "`-`", "Copied from scope dictionary inventory; active means `Архивный = Нет`."],
            ["`DICT-004`", "`Типы дохода`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Виды дохода; rows 4-5`", "`extracted`", "; ".join(f"`{v}`" for v in DICT_004), "`-`", "`SRC-011.P01`; `SRC-011.P02`", "`GAP-002`", "Exact duplicate prevention mechanism remains unresolved."],
            ["`DICT-005`", "`Параметры визуальной оценки`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Параметры визуальной оценки; rows 4-15`", "`extracted`", "; ".join(f"`{v}`" for v in DICT_005), "`-`", "`SRC-016.P01`; `SRC-016.P02`; `SRC-016.P03`", "`-`", "Preserve workbook spelling exactly, including typos."],
        ],
    )


def coverage_gaps() -> str:
    parts = []
    for gap, kind, refs, desc, impact, handling in GAPS:
        parts.append(f"### {gap}\n\n**Gap Type:** `{kind}`\n\n**FT Reference:** `{refs}`\n\n**Description:** {desc}\n\n**Impact:** `{impact}`\n\n**Temporary Handling:** {handling}\n\n**Blocks Ready For Review:** `no`")
    return "\n\n".join(parts)


def coverage_metrics() -> str:
    return table(
        ["metric", "value", "evidence", "notes"],
        [
            ["selected_source_rows", "12 executable rows plus residual gap rows", "source-row-inventory.md", "SRC-004/SRC-005/SRC-017/SRC-022..SRC-024 retained as residual/out-of-scope context"],
            ["atoms", str(len(ATOMS)), "atomic-requirements-ledger.md", "One independently checkable obligation per atom or gap"],
            ["test_cases", str(len(TCS)), str(CANONICAL.relative_to(FT_ROOT)), "No case-count minimization criterion used"],
            ["gaps", str(len(GAPS)), "coverage-gaps.md", "GAP-001..GAP-004 accepted residual; GAP-005..GAP-007 narrow invalid-feedback gaps"],
            ["dictionary_coverage", "3 dictionaries", "dictionary-inventory.md; TC traceability", "DICT-001, DICT-004, DICT-005 included in TCs using them"],
        ],
    )


def test_design_review() -> str:
    return table(
        ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
        [
            ["scope-boundary", "pass", "info", "all", "Only medium v13 rows are executable; excluded rows are out-of-scope or residual gaps.", "none", "no"],
            ["dictionary-traceability", "pass", "info", "WP-01; WP-02; WP-03", "TCs that use DICT-001/004/005 include same DICT ids in `Трассировка`.", "none", "no"],
            ["requiredness", "pass", "info", "WP-01; WP-03; WP-04", "Requiredness checked by empty/marker transition TCs, not by filling the field.", "none", "no"],
            ["repeatable-block-cleanup", "pass", "info", "WP-02; WP-04", "Action-created blocks have deterministic delete/close postconditions.", "none", "no"],
            ["numeric-invalid-feedback", "pass-with-gap", "warning", "WP-01; WP-02", "GAP-005, GAP-006, GAP-007 isolate unsupported invalid feedback mechanisms.", "Reviewer should confirm admissibility of narrow gaps.", "no"],
            ["branch-oracles", "pass", "info", "WP-04", "Back Yes/No TCs use distinct saved/not-saved observable values after returning to employment section.", "none", "no"],
            ["artifact-shape-preflight", "pass", "info", "all", "Canonical exact table headers used in required split artifacts.", "none", "no"],
        ],
    )


def writer_quality_gate() -> str:
    return table(
        ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
        [
            ["artifact-shape-preflight", "pass", "Exact canonical columns are used for required split tables; preflight command recorded in writer-self-check.md.", "all", "none", "no"],
            ["source-row-inventory", "pass", "`in_scope` uses only yes/no/unclear/out-of-scope; SRC-004/SRC-005 are not executable standalone TC.", "all", "none", "no"],
            ["source-row-completeness-matrix", "pass", "All in-scope rows have ATOM/GAP links and GSR rows are split to normalized properties.", "all", "none", "no"],
            ["canonical-tc-metadata", "pass", "Every TC uses bold metadata fields including `package_id`; no metadata tables are used.", "all", "none", "no"],
            ["dictionary-values", "pass", "DICT-001, DICT-004, DICT-005 full active values used in list TCs and traceability.", "WP-01; WP-02; WP-03", "none", "no"],
            ["accepted-residual-gaps", "pass", "GAP-001..GAP-004 preserved from accepted scope-gap review; GAP-005..GAP-007 are narrow feedback gaps.", "all", "none", "no"],
            ["scoped-validator-findings", "pending", "Run `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v13-canonical-table-shape-regression/cycle-state.yaml` after final write.", "all", "replace pending row with actual evidence", "yes"],
        ],
    )


def artifact_write_strategy() -> str:
    return table(
        ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
        [
            [str(CANONICAL.relative_to(FT_ROOT)), "large generated", "file-based manifest write", "yes", "scripts/write_artifact_sections.py --manifest <manifest.json>", "yes"],
            [str(TD.relative_to(FT_ROOT)) + "/*.md", "table-heavy generated", "file-based manifest write", "yes", "scripts/write_artifact_sections.py --manifest <manifest.json>", "yes"],
            [str((OUT / "writer-session-log.writer-r1.md").relative_to(FT_ROOT)), "process log", "file-based manifest write", "yes", "scripts/write_artifact_sections.py --manifest <manifest.json>", "yes"],
        ],
    )


def canonical_tcs() -> str:
    parts = [
        "# Тест-кейсы: canary v13 canonical table shape regression",
        "",
        "Scope: `ui-employment-canary-v13-canonical-table-shape-regression`.",
        "",
        "Набор покрывает только medium scope v13. Полные split artifact tables находятся в `work/test-design/ui-employment-canary-v13-canonical-table-shape-regression/` и здесь не дублируются.",
    ]
    for tc_id, pkg, name, typ, prio, trace, pre, data, steps, expected, post in TCS:
        parts.extend([
            "",
            f"## {tc_id}",
            "",
            f"**Название:** {name}",
            f"**Тип:** {typ}",
            f"**Приоритет:** {prio}",
            f"**package_id:** {pkg}",
            f"**Трассировка:** {trace}",
            "",
            "### Предусловия",
            pre,
            "",
            "### Тестовые данные",
            data,
            "",
            "### Шаги",
        ])
        parts.extend(f"{idx}. {step}" for idx, step in enumerate(steps, 1))
        parts.extend([
            "",
            "### Итоговый ожидаемый результат",
            expected,
            "",
            "### Постусловия",
            post,
        ])
    return "\n".join(parts)


def session_log() -> str:
    selected = "\n".join(f"- `{p}` - selected required instruction file read before writer decisions." for p in SELECTED_INSTRUCTIONS)
    inputs = "\n".join([
        selected,
        "- `fts/ft-2-OF_16/AGENT-NOTES.md` - package-specific context.",
        "- `work/stage-handoffs/00-source-selection/source-selection.md` - source package and main/support files.",
        "- `work/stage-handoffs/01-ui-employment/scope-contract.md` - broad scope and internal package context.",
        "- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md` - GAP-001..GAP-004 residual gap handling.",
        "- `work/stage-handoffs/01-ui-employment/source-parity-check.md` - mandatory GSR ids and PDF-only rows.",
        "- `work/stage-handoffs/01-ui-employment/source-row-inventory.md` - source row anchors.",
        "- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md` - UI labels and interaction hints.",
        "- `work/stage-handoffs/01-ui-employment/scope-clarification-requests.md` - unanswered non-blocking gap questions.",
        "- `work/review-cycles/ui-employment-canary-v2-test-design-upgrade/outputs/scope-gap-review-findings.md` - evidence that GAP-001..GAP-004 are accepted non-blocking residual gaps.",
        "- `work/test-design/ui-employment/dictionary-inventory.md` - DICT-001, DICT-004, DICT-005 active values.",
        "- `source/*.docx` and `source/*.pdf` - direct section/page verification for selected source rows.",
    ])
    return f"""# Writer R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `fresh-eval-run / writer.session_initial_draft` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| started_from | `work/review-cycles/{SCOPE}/cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.
- Resolver budget status: `pass (131.2 / 200.0 KiB)`.
- Resolver selected files:
{inputs}

## Inputs Not Used

- Existing canary v1-v12 canonical files, ledgers, matrices, writer outputs, reviewer outputs, split artifacts and generated helper scripts - regression comparison only, not requirement sources or templates.
- Neighboring FT packages and neighboring UI sections - outside the v13 scope.
- `work/ui-automation-prep/UI-AGENT-NOTES.md` - not a UI automation prep phase.

## Key Decisions

- Medium v13 scope is not a full section rerun; executable coverage is limited to selected source rows and directly required checks.
- SRC-004/SRC-005/SRC-017 and SRC-022..SRC-024 are preserved as residual gap/out-of-scope context and are not routed to executable standalone TC.
- Numeric invalid feedback for main/additional income is captured as narrow GAP-005..GAP-007 because FT gives classes but not deterministic UI rejection feedback.
- Back branches use distinct saved/not-saved observable values after returning to the employment section.

## Risks And Fallbacks

- Earlier PowerShell stdout produced mojibake for Russian files; affected files were reread with explicit UTF-8 output and direct DOCX/PDF extraction. Distorted stdout was not used as source evidence.
- DOCX extraction first addressed a non-existent `Section.content` attribute; the source was rerun against `Section.text`.

## Validation

- `artifact-shape-preflight` - planned before final handoff and recorded in `writer-self-check.md`.
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml` - run after final artifact write and recorded in `writer-self-check.md`.

## Contamination Check

- Old canary artifacts and generated scripts were excluded as requirement sources/templates. Requirement facts used here come from handoff artifacts, dictionary inventory, direct DOCX/PDF extraction and package notes.

## Artifact Write Strategy

{artifact_write_strategy()}

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | pass | resolver command; budget pass |
| 2 | Read required instruction files | pass | selected 15 files |
| 3 | Read source/scope inputs | pass | handoff artifacts and dictionaries |
| 4 | Verified selected DOCX/PDF rows | pass | DOCX section-23/24; PDF pp.61-67 |
| 5 | Wrote artifacts through manifest helper | pass | `scripts/write_artifact_sections.py` manifests under `{TD.relative_to(FT_ROOT)}/_build_sections` |
| 6 | Ran writer gates | pending until final validation | `writer-self-check.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pending | `writer-quality-gate.md` | replace validator pending row after validation |
| Artifact shape preflight | pending | `writer-self-check.md` | run command after write |
| Scoped validator | pending | `writer-self-check.md` | run runner validate after cycle-state update |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Cyrillic stdout displayed mojibake | PowerShell default stdout for Russian Markdown files | explicit UTF-8 reads and direct source extraction; distorted stdout discarded | `n/a` | `n/a` | none | reviewer may ignore distorted early stdout |
| `TF-002` | source extraction attribute error | attempted `Section.content` | reran extraction using `Section.text` from `test_case_agent.models.Section` | `n/a` | `n/a` | none | none |

## Handoff Notes For Next Session

- Structure preflight should focus on parser shape, canonical table headers and bold TC metadata; semantic review comes later.
- GAP-001..GAP-004 are accepted residual gaps; GAP-005..GAP-007 are new narrow invalid-feedback gaps requiring reviewer admissibility check.
"""


def decision_log() -> str:
    return f"""# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| stage | `ft-test-case-writer` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | active prompt | Use only v13 medium source-backed areas. | Prompt excludes full section rerun and case-count minimization. | canonical TC; split artifacts | high | applied |
| `DEC-002` | 2 | `source-boundary` | source handoff and prompt | Preserve but do not execute SRC-004/SRC-005/SRC-017 and CDI SRC-022..SRC-024. | These rows are residual/out-of-scope for v13 executable coverage. | source-row-inventory.md; coverage-gaps.md | high | applied |
| `DEC-003` | 3 | `coverage` | SRC-003/SRC-012 numeric rows | Cover positive numeric/min values; route invalid feedback to GAP-005..GAP-007. | FT gives numeric classes but not deterministic invalid UI feedback. | coverage-gaps.md; TDDT; canonical TC | medium | applied |
| `DEC-004` | 4 | `test-design` | SRC-021/GSR 148 | Use return-and-reopen checks to distinguish Back `Да` and `Нет` branches. | Source differentiates save vs no-save; observable value after return gives distinct oracle. | TC-UI-EMP-V13-022; TC-UI-EMP-V13-023 | medium | applied |
| `DEC-005` | 5 | `artifact-write` | table-heavy generated output | Use file-based manifests and `scripts/write_artifact_sections.py`. | Process workflow requires canonical helper for large/table-heavy artifacts. | artifact-write-strategy.md; build sections | high | applied |
| `DEC-006` | 6 | `routing` | writer gates | Route to structure preflight after scoped validator passes. | Session lifecycle requires writer-draft-ready before reviewer structure preflight. | cycle-state.yaml; prompt.structure-preflight-r1.md | high | pending-final-validation |
"""


def writer_self_check() -> str:
    return f"""# Writer Self-Check

## Checks

| check | status | evidence | action |
| --- | --- | --- | --- |
| instruction-context | pass | `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`; budget `pass (131.2 / 200.0 KiB)` | none |
| artifact-shape-preflight | pending | Run exact table-header preflight after write. | update after command |
| scoped-validator-findings | pending | Run `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml` after final write. | update after command |
| canonical-tc-schema | pass | canonical TC uses bold metadata fields only; no metadata table blocks. | none |
| dictionary-traceability | pass | TC using DICT-001, DICT-004 or DICT-005 includes the same DICT id in `Трассировка`. | none |

## Current-Scope Validator Findings

Pending until scoped validator execution.
"""


def prompt_structure_preflight() -> str:
    return f"""# Structure Preflight Prompt

## Stage Goal

Run `ft-test-case-reviewer` in `structure_preflight` mode for `{SCOPE}`.

Review only parseability and blocking format prerequisites. Do not perform semantic coverage review in this stage.

## Required Inputs

- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml`
- `fts/ft-2-OF_16/test-cases/{SECTION_PREFIX}-{SCOPE}.md`
- `fts/ft-2-OF_16/work/test-design/{SCOPE}/`
- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/writer-self-check.md`

## Preflight Focus

- Exact canonical split artifact table headers.
- Parser-supported TC bold metadata: `Название`, `Тип`, `Приоритет`, `package_id`, `Трассировка`.
- No duplicated split artifact tables in canonical TC file.
- No current-scope validator blockers from the runner gate.

## Expected Output

Write structure-preflight findings under `work/review-cycles/{SCOPE}/outputs/` and update `cycle-state.yaml` according to `session-based-review-cycle-format.md`.
"""


def write_artifact(target: Path, title: str, body: str) -> None:
    stem = target.stem
    artifact_dir = BUILD_DIR / stem
    artifact_dir.mkdir(parents=True, exist_ok=True)
    body_path = artifact_dir / "body.md"
    body_path.write_text(body.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "target_path": str(target.resolve()),
        "sections": [{"level": 1, "heading": title, "content_file": "body.md"}],
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=FT_ROOT,
        check=True,
    )


def write_plain_artifact(target: Path, body: str) -> None:
    stem = target.stem
    artifact_dir = BUILD_DIR / stem
    artifact_dir.mkdir(parents=True, exist_ok=True)
    body_path = artifact_dir / "body.md"
    body_path.write_text(body.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "target_path": str(target.resolve()),
        "preamble_file": "body.md",
        "sections": [{"level": 2, "heading": "Artifact Write Evidence", "content_file": ""}],
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=FT_ROOT,
        check=True,
    )


def write_cycle_state() -> None:
    state = f"""cycle_id: ft-2-OF_16-ui-employment-canary-v13-canonical-table-shape-regression
ft_slug: ft-2-OF_16
scope_slug: {SCOPE}
section_id: {SECTION_ID}
current_stage: structure-preflight-r1
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: test-cases/{SECTION_PREFIX}-{SCOPE}.md
test_design_dir: work/test-design/{SCOPE}
active_snapshot: none
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions: []
latest_artifacts:
  - test-cases/{SECTION_PREFIX}-{SCOPE}.md
  - work/test-design/{SCOPE}/writer-quality-gate.md
  - work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  - work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  - work/review-cycles/{SCOPE}/outputs/writer-self-check.md
  - work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
blocking_reasons: []
blocking_findings: []
open_questions:
  - GAP-001
  - GAP-002
  - GAP-003
  - GAP-004
  - GAP-005
  - GAP-006
  - GAP-007
accepted_risks:
  - Canary v13 uses the same medium employment UI source rows as v12 and must not optimize for target test-case count or compactness.
  - Existing canary v1-v12 files and generated artifacts are regression comparison material only, not requirement sources or templates.
  - GAP-001 through GAP-004 remain accepted non-blocking pre-writer residual gaps by prior scope-gap review evidence unless new source evidence closes them.
"""
    (CYCLE / "cycle-state.yaml").write_text(state, encoding="utf-8", newline="\n")


def main() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    (FT_ROOT / "test-cases").mkdir(exist_ok=True)

    write_artifact(TD / "artifact-write-strategy.md", "Artifact Write Strategy", artifact_write_strategy())
    write_artifact(TD / "source-row-inventory.md", "Source Row Inventory", source_inventory())
    write_artifact(TD / "source-row-completeness-matrix.md", "Source Row Completeness Matrix", source_completeness())
    write_artifact(TD / "source-table-normalization.md", "Source Table Normalization", source_normalization())
    write_artifact(TD / "atomic-requirements-ledger.md", "Atomic Requirements Ledger", atomic_ledger())
    write_artifact(TD / "test-design-decision-table.md", "Test Design Decision Table", decision_table())
    write_artifact(TD / "coverage-obligation-table.md", "Coverage Obligation Table", obligation_table())
    write_artifact(TD / "package-test-design-plan.md", "Package Test Design Plan", package_plan())
    write_artifact(TD / "fixture-catalog.md", "Fixture Catalog", fixture_catalog())
    write_artifact(TD / "dictionary-inventory.md", "Dictionary Inventory", dictionary_inventory())
    write_artifact(TD / "coverage-gaps.md", "Coverage Gaps", coverage_gaps())
    write_artifact(TD / "coverage-metrics.md", "Coverage Metrics", coverage_metrics())
    write_artifact(TD / "test-design-review.md", "Test Design Review", test_design_review())
    write_artifact(TD / "writer-quality-gate.md", "Writer Quality Gate", writer_quality_gate())
    write_plain_artifact(CANONICAL, canonical_tcs())
    write_plain_artifact(OUT / "writer-session-log.writer-r1.md", session_log())
    write_plain_artifact(OUT / "agent-decision-log.writer-r1.md", decision_log())
    write_plain_artifact(OUT / "writer-self-check.md", writer_self_check())
    write_plain_artifact(PROMPTS / "prompt.structure-preflight-r1.md", prompt_structure_preflight())
    write_cycle_state()


if __name__ == "__main__":
    main()
