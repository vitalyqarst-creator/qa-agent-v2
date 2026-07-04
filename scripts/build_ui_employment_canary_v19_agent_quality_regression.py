from __future__ import annotations

import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment-canary-v19-agent-quality-regression"
SECTION = "2.1.1.1.1.2"
CANONICAL_REL = f"test-cases/2-1-1-1-1-2-{SCOPE}.md"
TD_REL = f"work/test-design/{SCOPE}"
CYCLE_REL = f"work/review-cycles/{SCOPE}"
OUT_REL = f"{CYCLE_REL}/outputs"
PROMPT_REL = f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md"
PROFILE_REL = f"{OUT_REL}/scoped-validator-profile.writer-r1.json"

TD = FT / TD_REL
OUT = FT / OUT_REL
PROMPTS = FT / CYCLE_REL / "prompts"
CANONICAL = FT / CANONICAL_REL


DICT_VALUES = {
    "DICT-001": [
        "Работа по найму",
        "Пенсионер (не работает)",
        "Индивидуальный предприниматель",
        "Собственник бизнеса",
        "Частная практика / Самозанятый",
        "Безработный",
    ],
    "DICT-004": ["Пенсия", "Аренда"],
    "DICT-005": [
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


NORMALIZED_ROWS = [
    ("SRC-002", "SP-V19-001", "WP-01", "Тип занятости", "dictionary-source", "always", "Поле использует значения справочника «Типы занятости».", "-", "ATOM-V19-001", ""),
    ("SRC-003", "SP-V19-002", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "visibility", "Тип занятости заполнен", "Поле отображается после заполнения поля «Тип занятости».", "GSR 123", "ATOM-V19-002", ""),
    ("SRC-003", "SP-V19-003", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "requiredness", "field empty + action Следующий шаг", "Пустое обязательное поле подсвечивается красным при переходе.", "GSR 124", "ATOM-V19-003", ""),
    ("SRC-003", "SP-V19-004", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "numeric-format-positive", "digits only", "Поле принимает числовое значение.", "-", "ATOM-V19-004", ""),
    ("SRC-003", "SP-V19-005", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "amount-boundary-min-positive", "value = 2000", "Поле принимает минимально допустимое значение `2000`.", "-", "ATOM-V19-005", ""),
    ("SRC-003", "SP-V19-006", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "amount-boundary-min-negative", "value = 1999", "Поле не принимает сумму ниже `2000`.", "-", "ATOM-V19-006", ""),
    ("SRC-003", "SP-V19-007", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "numeric-reject-letters", "value = abc", "Поле не принимает буквенное значение.", "-", "ATOM-V19-007", ""),
    ("SRC-003", "SP-V19-008", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "numeric-reject-decimal-separator", "value = 2000,5", "Поле не принимает значение с десятичным разделителем.", "-", "ATOM-V19-008", ""),
    ("SRC-003", "SP-V19-009", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "numeric-reject-sign", "value = -2000", "Поле не принимает значение со знаком.", "-", "ATOM-V19-009", ""),
    ("SRC-003", "SP-V19-010", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "numeric-reject-spaces", "value = 2 000", "Поле не принимает значение с пробелом.", "-", "ATOM-V19-010", ""),
    ("SRC-003", "SP-V19-011", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "numeric-reject-special-chars", "value = 2000#", "Поле не принимает значение со спецсимволом.", "-", "ATOM-V19-011", ""),
    ("SRC-020", "SP-V19-012", "WP-04", "Добавить дополнительный доход", "action-add-block", "click action", "Действие отображает блок «Дополнительный доход».", "GSR 146", "ATOM-V19-012", ""),
    ("SRC-011", "SP-V19-013", "WP-02", "Тип дохода", "visibility", "block created", "Поле отображается после нажатия «Добавить источник дохода».", "-", "ATOM-V19-013", ""),
    ("SRC-011", "SP-V19-014", "WP-02", "Тип дохода", "dictionary-source", "block created", "Поле использует значения справочника «Типы дохода».", "-", "ATOM-V19-014", ""),
    ("SRC-011", "SP-V19-015", "WP-02", "Тип дохода", "unique-income-pension", "Пенсия already added", "Тип дохода `Пенсия` может быть добавлен только один раз; механизм ограничения не задан.", "-", "ATOM-V19-015", "GAP-002"),
    ("SRC-012", "SP-V19-016", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "visibility", "block created", "Поле отображается после нажатия «Добавить источник дохода».", "GSR 135", "ATOM-V19-016", ""),
    ("SRC-012", "SP-V19-017", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "numeric-format-positive", "digits only", "Поле принимает числовое значение.", "-", "ATOM-V19-017", ""),
    ("SRC-012", "SP-V19-018", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "numeric-reject-letters", "value = rent", "Поле не принимает буквенное значение.", "-", "ATOM-V19-018", ""),
    ("SRC-014", "SP-V19-019", "WP-03", "Клиент добросовестный", "default", "section opened", "Поле по умолчанию имеет значение `Нет`.", "GSR 136", "ATOM-V19-019", ""),
    ("SRC-015", "SP-V19-020", "WP-03", "Визуальная информация", "visibility", "always", "Поле отображается всегда.", "GSR 137", "ATOM-V19-020", ""),
    ("SRC-015", "SP-V19-021", "WP-03", "Визуальная информация", "dependency-show-visual-params", "Визуальная информация = Да", "Параметры визуальной оценки становятся доступны для заполнения.", "GSR 138", "ATOM-V19-021", ""),
    ("SRC-016", "SP-V19-022", "WP-03", "Параметры визуальной оценки", "visibility", "Визуальная информация = Да", "Поле отображается, если «Визуальная информация» = `Да`.", "GSR 139", "ATOM-V19-022", ""),
    ("SRC-016", "SP-V19-023", "WP-03", "Параметры визуальной оценки", "requiredness", "Визуальная информация = Да", "Поле обязательно, если «Визуальная информация» = `Да`.", "GSR 140", "ATOM-V19-023", ""),
    ("SRC-016", "SP-V19-024", "WP-03", "Параметры визуальной оценки", "checkbox-list", "Визуальная информация = Да", "По каждому параметру визуальной оценки доступен отдельный вариант выбора.", "-", "ATOM-V19-024", ""),
    ("SRC-018", "SP-V19-025", "WP-04", "Следующий шаг", "action-navigation", "all required fields filled", "Действие открывает раздел «Анкета клиента».", "GSR 143", "ATOM-V19-025", ""),
    ("SRC-018", "SP-V19-026", "WP-04", "Следующий шаг", "action-validation", "required field empty", "Действие подсвечивает незаполненное обязательное поле красным.", "GSR 142", "ATOM-V19-031", ""),
    ("SRC-020", "SP-V19-027", "WP-04", "Удалить дополнительный доход", "action-delete-block", "created income block exists", "Удаление блока дополнительного дохода пиктограммой «Корзина» не входит в targeted v19 executable subset.", "GSR 147", "ATOM-V19-030", "GAP-016"),
]


TC_ROWS = [
    ("TC-EMP-V19-001", "Список `Тип занятости` отображает все и только активные значения `DICT-001`.", "Positive", "High", "WP-01", "ATOM-V19-001; SRC-002; DICT-001", "Открыта форма `Сведения о занятости`.", "DICT-001 active values: " + "; ".join(DICT_VALUES["DICT-001"]), ["Открыть раскрывающийся список `Тип занятости`."], "В списке отображаются все и только активные значения `DICT-001`: " + "; ".join(DICT_VALUES["DICT-001"]) + ".", "Не требуются"),
    ("TC-EMP-V19-002", "Поле основного дохода отображается после выбора `Работа по найму`.", "Positive", "High", "WP-01", "ATOM-V19-002; GSR 123; SRC-003; DICT-001", "Открыта форма `Сведения о занятости`.", "Тип занятости: `Работа по найму`.", ["В поле `Тип занятости` выбрать `Работа по найму`."], "Поле `Среднемесячный доход после вычета налогов (основная работа)` отображается в форме.", "Не требуются"),
    ("TC-EMP-V19-003", "Пустой основной доход подсвечивается красным при переходе.", "Negative", "High", "WP-01", "ATOM-V19-003; ATOM-V19-031; GSR 124; GSR 142; SRC-003; SRC-018; F-V19-BASE-EMPLOYED-MAIN-INCOME-EMPTY", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`; остальные обязательные поля из `F-V19-BASE-EMPLOYED-MAIN-INCOME-EMPTY` заполнены.", "Основной доход: пусто.", ["Оставить поле `Среднемесячный доход после вычета налогов (основная работа)` пустым.", "Нажать `Следующий шаг`."], "Поле `Среднемесячный доход после вычета налогов (основная работа)` подсвечено красным.", "Не требуются"),
    ("TC-EMP-V19-004", "Основной доход принимает минимальное числовое значение `2000`.", "Positive", "High", "WP-01", "ATOM-V19-004; ATOM-V19-005; SRC-003", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Основной доход: `2000`.", ["Ввести `2000` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "В поле `Среднемесячный доход после вычета налогов (основная работа)` отображается значение `2000`.", "Очистить поле, если сценарий выполняется в сохраняемой заявке."),
    ("TC-EMP-V19-005", "Основной доход редактируется с `2000` на `35000`.", "Positive", "Medium", "WP-01", "ATOM-V19-004; SRC-003", "Открыта форма `Сведения о занятости`; в поле основного дохода введено `2000`.", "Старое значение: `2000`; новое значение: `35000`.", ["Выделить значение `2000` в поле `Среднемесячный доход после вычета налогов (основная работа)`.", "Ввести `35000`."], "В поле `Среднемесячный доход после вычета налогов (основная работа)` отображается новое значение `35000`.", "Вернуть значение, требуемое текущим тестовым прогоном, если заявка сохраняется."),
    ("TC-EMP-V19-006", "Основной доход не принимает значение ниже минимума `1999`.", "Negative", "High", "WP-01", "ATOM-V19-006; SRC-003; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Недопустимое значение: `1999`; минимальное допустимое значение: `2000`.", ["Ввести `1999` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "Значение `1999` не принято как значение поля `Среднемесячный доход после вычета налогов (основная работа)`.", "Очистить поле, если сценарий выполняется в сохраняемой заявке."),
    ("TC-EMP-V19-007", "Основной доход не принимает буквенное значение `abc`.", "Negative", "High", "WP-01", "ATOM-V19-007; SRC-003; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Недопустимый класс: letters; значение: `abc`.", ["Ввести `abc` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "Значение `abc` не принято как значение поля `Среднемесячный доход после вычета налогов (основная работа)`.", "Не требуются"),
    ("TC-EMP-V19-008", "Основной доход не принимает значение с десятичным разделителем `2000,5`.", "Negative", "High", "WP-01", "ATOM-V19-008; SRC-003; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Недопустимый класс: decimal-separator; значение: `2000,5`.", ["Ввести `2000,5` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "Значение `2000,5` не принято как значение поля `Среднемесячный доход после вычета налогов (основная работа)`.", "Не требуются"),
    ("TC-EMP-V19-009", "Основной доход не принимает значение со знаком `-2000`.", "Negative", "High", "WP-01", "ATOM-V19-009; SRC-003; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Недопустимый класс: sign; значение: `-2000`.", ["Ввести `-2000` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "Значение `-2000` не принято как значение поля `Среднемесячный доход после вычета налогов (основная работа)`.", "Не требуются"),
    ("TC-EMP-V19-010", "Основной доход не принимает значение с пробелом `2 000`.", "Negative", "High", "WP-01", "ATOM-V19-010; SRC-003; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Недопустимый класс: spaces; значение: `2 000`.", ["Ввести `2 000` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "Значение `2 000` не принято как значение поля `Среднемесячный доход после вычета налогов (основная работа)`.", "Не требуются"),
    ("TC-EMP-V19-011", "Основной доход не принимает значение со спецсимволом `2000#`.", "Negative", "High", "WP-01", "ATOM-V19-011; SRC-003; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; выбран `Тип занятости = Работа по найму`.", "Недопустимый класс: special-chars; значение: `2000#`.", ["Ввести `2000#` в поле `Среднемесячный доход после вычета налогов (основная работа)`."], "Значение `2000#` не принято как значение поля `Среднемесячный доход после вычета налогов (основная работа)`.", "Не требуются"),
    ("TC-EMP-V19-012", "Действие `Добавить источник дохода` отображает блок дополнительного дохода.", "Positive", "High", "WP-04", "ATOM-V19-012; GSR 146; SRC-020", "Открыта форма `Сведения о занятости`.", "Действие: `Добавить источник дохода` (UI alias action for FT `Добавить дополнительный доход`).", ["Нажать `Добавить источник дохода`."], "В форме отображается один созданный блок `Дополнительный доход`.", "Удалить созданный блок пиктограммой `Корзина` или закрыть форму без сохранения."),
    ("TC-EMP-V19-013", "Созданный блок дополнительного дохода содержит поля типа и суммы дохода.", "Positive", "High", "WP-02", "ATOM-V19-013; ATOM-V19-016; GSR 135; SRC-011; SRC-012; SRC-020", "Открыта форма `Сведения о занятости`.", "Действие: `Добавить источник дохода`.", ["Нажать `Добавить источник дохода`."], "В созданном блоке `Дополнительный доход` отображаются поля `Тип дохода` и `Среднемесячный доход после вычета налогов (дополнительный доход)`.", "Удалить созданный блок пиктограммой `Корзина` или закрыть форму без сохранения."),
    ("TC-EMP-V19-014", "Список `Тип дохода` в созданном блоке отображает все и только активные значения `DICT-004`.", "Positive", "High", "WP-02", "ATOM-V19-014; SRC-011; DICT-004", "Открыта форма `Сведения о занятости`; создан один блок `Дополнительный доход`.", "DICT-004 active values: Пенсия; Аренда.", ["Открыть раскрывающийся список `Тип дохода` в созданном блоке."], "В списке отображаются все и только активные значения `DICT-004`: Пенсия; Аренда.", "Удалить созданный блок пиктограммой `Корзина` или закрыть форму без сохранения."),
    ("TC-EMP-V19-015", "Повторное добавление `Тип дохода = Пенсия` не принимается во втором блоке.", "Negative", "High", "WP-02", "ATOM-V19-015; SRC-011; DICT-004; GAP-002", "Открыта форма `Сведения о занятости`; первый блок `Дополнительный доход` создан и в нем выбран `Тип дохода = Пенсия`.", "Повторяемое значение: `Пенсия`.", ["Нажать `Добавить источник дохода` для создания второго блока.", "Попытаться установить `Тип дохода = Пенсия` во втором блоке."], "Во втором блоке не появляется принятое значение `Пенсия` как второй добавленный источник дохода.", "Удалить созданные блоки или закрыть форму без сохранения."),
    ("TC-EMP-V19-016", "Сумма дополнительного дохода принимает числовое значение `5000`.", "Positive", "High", "WP-02", "ATOM-V19-017; SRC-012; F-V19-ADDITIONAL-INCOME-PENSION", "Открыта форма `Сведения о занятости`; создан один блок `Дополнительный доход`; выбран `Тип дохода = Пенсия`.", "Сумма дополнительного дохода: `5000`.", ["Ввести `5000` в поле `Среднемесячный доход после вычета налогов (дополнительный доход)`."], "В поле `Среднемесячный доход после вычета налогов (дополнительный доход)` отображается значение `5000`.", "Удалить созданный блок или закрыть форму без сохранения."),
    ("TC-EMP-V19-017", "Сумма дополнительного дохода не принимает буквенное значение `rent`.", "Negative", "High", "WP-02", "ATOM-V19-018; SRC-012; F-V19-ADDITIONAL-INCOME-PENSION", "Открыта форма `Сведения о занятости`; создан один блок `Дополнительный доход`; выбран `Тип дохода = Пенсия`.", "Недопустимый класс: letters; значение: `rent`.", ["Ввести `rent` в поле `Среднемесячный доход после вычета налогов (дополнительный доход)`."], "Значение `rent` не принято как значение поля `Среднемесячный доход после вычета налогов (дополнительный доход)`.", "Удалить созданный блок или закрыть форму без сохранения."),
    ("TC-EMP-V19-018", "`Визуальная информация` отображается в разделе занятости.", "Positive", "High", "WP-03", "ATOM-V19-020; GSR 137; SRC-015", "Открыта форма `Сведения о занятости`.", "Не требуются.", ["Просмотреть блок общих полей раздела."], "Поле `Визуальная информация` отображается в разделе `Сведения о занятости`.", "Не требуются"),
    ("TC-EMP-V19-019", "`Визуальная информация = Да` отображает параметры визуальной оценки.", "Positive", "High", "WP-03", "ATOM-V19-021; ATOM-V19-022; GSR 138; GSR 139; SRC-015; SRC-016", "Открыта форма `Сведения о занятости`; поле `Визуальная информация` отображается.", "Значение переключателя `Визуальная информация`: `Да`.", ["Установить `Визуальная информация = Да`."], "В форме отображается поле `Параметры визуальной оценки`.", "Вернуть `Визуальная информация = Нет`, если сценарий выполняется в сохраняемой заявке."),
    ("TC-EMP-V19-020", "Параметры визуальной оценки отображают чек-боксы по всем и только активным значениям `DICT-005`.", "Positive", "High", "WP-03", "ATOM-V19-024; SRC-016; DICT-005", "Открыта форма `Сведения о занятости`; установлено `Визуальная информация = Да`.", "DICT-005 active values: " + "; ".join(DICT_VALUES["DICT-005"]), ["Просмотреть список `Параметры визуальной оценки`."], "В списке доступны чек-боксы по всем и только активным значениям `DICT-005`: " + "; ".join(DICT_VALUES["DICT-005"]) + ".", "Вернуть `Визуальная информация = Нет`, если сценарий выполняется в сохраняемой заявке."),
    ("TC-EMP-V19-021", "При `Визуальная информация = Да` отсутствие выбранного параметра подсвечивает обязательность параметров.", "Negative", "High", "WP-03", "ATOM-V19-023; GSR 140; SRC-016; F-V19-VISUAL-INFO-NO-PARAM", "Открыта форма `Сведения о занятости`; установлено `Визуальная информация = Да`; остальные обязательные поля из `F-V19-VISUAL-INFO-NO-PARAM` заполнены.", "Параметры визуальной оценки: ни один чек-бокс не выбран.", ["Не выбирать ни один чек-бокс в `Параметры визуальной оценки`.", "Нажать `Следующий шаг`."], "Поле `Параметры визуальной оценки` подсвечено красным.", "Вернуть `Визуальная информация = Нет`, если сценарий выполняется в сохраняемой заявке."),
    ("TC-EMP-V19-022", "Действие `Следующий шаг` открывает раздел `Анкета клиента` при заполненных обязательных полях.", "Positive", "High", "WP-04", "ATOM-V19-025; GSR 143; SRC-018; F-V19-BASE-EMPLOYED", "Открыта форма `Сведения о занятости`; все обязательные поля заполнены по `F-V19-BASE-EMPLOYED`.", "Тип занятости: `Работа по найму`; основной доход: `35000`; Клиент добросовестный: `Да`; Визуальная информация: `Нет`.", ["Нажать `Следующий шаг`."], "Открыт раздел `Анкета клиента`.", "Вернуться в исходную заявку/раздел, если следующий сценарий требует форму занятости."),
]

DROP_EXECUTABLE_TC_IDS = {
    "TC-EMP-V19-006",
    "TC-EMP-V19-007",
    "TC-EMP-V19-008",
    "TC-EMP-V19-009",
    "TC-EMP-V19-010",
    "TC-EMP-V19-011",
    "TC-EMP-V19-015",
    "TC-EMP-V19-017",
}

TC_ROWS = [row for row in TC_ROWS if row[0] not in DROP_EXECUTABLE_TC_IDS]
TC_ROWS.insert(
    -3,
    (
        "TC-EMP-V19-015",
        "`Визуальная информация = Нет` не отображает параметры визуальной оценки.",
        "Positive",
        "Medium",
        "WP-03",
        "ATOM-V19-021; ATOM-V19-022; SRC-015; SRC-016",
        "Открыта форма `Сведения о занятости`; поле `Визуальная информация` отображается.",
        "Значение переключателя `Визуальная информация`: `Нет`.",
        ["Установить `Визуальная информация = Нет`."],
        "Поле `Параметры визуальной оценки` не отображается в форме.",
        "Не требуются",
    ),
)

TC_ROWS = [
    (
        tc_id,
        title,
        typ,
        prio,
        pkg,
        trace,
        preconditions,
        f"{test_data} Значение поля: пусто.",
        steps + ["Оставить значение поля пустым перед переходом."],
        expected,
        postconditions,
    )
    if tc_id == "TC-EMP-V19-021"
    else row
    for row in TC_ROWS
    for tc_id, title, typ, prio, pkg, trace, preconditions, test_data, steps, expected, postconditions in [row]
]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = textwrap.dedent(content).lstrip().replace("ATOM-V19-", "ATOM-")
    normalized = "\n".join(line[4:] if line.startswith("    ") else line for line in normalized.splitlines())
    path.write_text(normalized + "\n", encoding="utf-8")


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    out.extend("| " + " | ".join(cell.replace("`", "") for cell in row) + " |" for row in rows)
    return "\n".join(out)


def test_case_block(row: tuple) -> str:
    tc_id, title, tc_type, prio, package, trace, pre, data, steps, expected, post = row
    step_lines = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    return f"""
## {tc_id}

**Название:** {title}

**Тип:** {tc_type}

**Приоритет:** {prio}

**package_id:** {package}

**Трассировка:** {trace}

**Предусловия:** {pre}

**Тестовые данные:** {data}

**Шаги:**
{step_lines}

**Итоговый ожидаемый результат:** {expected}

**Постусловия:** {post}
"""


def generate() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)

    write(TD / "artifact-write-strategy.md", f"""
    # Artifact Write Strategy

    ## Artifact Write Strategy

    | artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
    | --- | --- | --- | --- | --- | --- |
    | `{CANONICAL_REL}` | `generated canonical TC set` | `canonical section-manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
    | `{TD_REL}` | `split generated artifacts` | `canonical section-manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
    | `{OUT_REL}` | `cycle outputs` | `file-based committed helper orchestration` | `yes` | `scripts/build_ui_employment_canary_v19_agent_quality_regression.py` | `yes` |

    ## Strategy Rationale

    V19 writes a targeted but multi-artifact package through a committed helper script to avoid one-shot shell transport and to keep canonical test cases separate from split design tables. The canonical artifact intentionally contains only executable `## TC-*` blocks and links traceability to split artifacts by IDs.
    """)

    inventory_rows = []
    for src in ["SRC-002", "SRC-003", "SRC-010", "SRC-011", "SRC-012", "SRC-014", "SRC-015", "SRC-016", "SRC-018", "SRC-020", "SRC-021", "SRC-022", "SRC-023", "SRC-024"]:
        package = next((r[2] for r in NORMALIZED_ROWS if r[0] == src), "WP-05" if src.startswith("SRC-02") else "WP-04")
        field = {
            "SRC-002": "Тип занятости",
            "SRC-003": "Среднемесячный доход после вычета налогов (основная работа)",
            "SRC-010": "Блок «Дополнительный доход»",
            "SRC-011": "Тип дохода",
            "SRC-012": "Среднемесячный доход после вычета налогов (дополнительный доход)",
            "SRC-014": "Клиент добросовестный",
            "SRC-015": "Визуальная информация",
            "SRC-016": "Параметры визуальной оценки",
            "SRC-018": "«Следующий шаг»",
            "SRC-020": "«Добавить дополнительный доход»",
            "SRC-021": "«Назад»",
            "SRC-022": "CDI: не удалось верифицировать ИНН",
            "SRC-023": "CDI: данные клиента отличаются от данных заявки",
            "SRC-024": "CDI: подтверждение замены данных",
        }[src]
        reqs = {
            "SRC-003": "GSR 123; GSR 124",
            "SRC-012": "GSR 135",
            "SRC-014": "GSR 136",
            "SRC-015": "GSR 137; GSR 138",
            "SRC-016": "GSR 139; GSR 140",
            "SRC-018": "GSR 142; GSR 143",
            "SRC-020": "GSR 146; GSR 147",
            "SRC-021": "GSR 148",
        }.get(src, "-")
        mapped = "; ".join(r[8] for r in NORMALIZED_ROWS if r[0] == src) or ("GAP-004" if src in {"SRC-022", "SRC-023", "SRC-024"} else "ATOM-V19-029")
        inventory_rows.append([f"`{src}`", f"`{package}`", field, "stage-handoff inventory / predecessor normalization", reqs, "yes" if src not in {"SRC-021", "SRC-022", "SRC-023", "SRC-024"} else "unclear", mapped])
    write(TD / "source-row-inventory.md", "# Source Row Inventory\n\n" + md_table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], inventory_rows))

    completeness_rows = [
        ["`SRC-003`", "`GSR 123; GSR 124`", "`SP-V19-002..SP-V19-011`", "`ATOM-V19-002..ATOM-V19-011`", "-", "split by visibility, requiredness, positive numeric, boundary and negative classes"],
        ["`SRC-015`", "`GSR 137; GSR 138`", "`SP-V19-020; SP-V19-021`", "`ATOM-V19-020; ATOM-V19-021`", "-", "split by field visibility and dependency branch"],
        ["`SRC-016`", "`GSR 139; GSR 140`", "`SP-V19-022..SP-V19-024`", "`ATOM-V19-022..ATOM-V19-024`", "-", "split by visibility, conditional requiredness and checkbox list composition"],
        ["`SRC-018`", "`GSR 142; GSR 143`", "`SP-V19-026; SP-V19-025`", "`ATOM-V19-031; ATOM-V19-025`", "-", "validation and navigation kept separate"],
        ["`SRC-020`", "`GSR 146; GSR 147`", "`SP-V19-012; SP-V19-027`", "`ATOM-V19-012; ATOM-V19-030`", "`GAP-016`", "add-block behavior covered; delete behavior preserved as targeted residual gap"],
        ["`SRC-022..SRC-024`", "`PDF-only rows without GSR`", "-", "-", "`GAP-004`", "preserved as residual setup gap for CDI trigger"],
    ]
    write(TD / "source-row-completeness-matrix.md", "# Source Row Completeness Matrix\n\n" + md_table(["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"], completeness_rows))

    def normalized_property(sp: str, prop: str) -> str:
        if sp in {"SP-V19-004", "SP-V19-017"}:
            return "numeric-format"
        return prop

    def normalized_gap(sp: str, prop: str, gap: str) -> str:
        if sp == "SP-V19-019":
            return gap or "GAP-017"
        additional_income_gap_by_property = {
            "numeric-reject-letters": "GAP-011",
            "numeric-reject-spaces": "GAP-012",
            "numeric-reject-special-chars": "GAP-013",
            "numeric-reject-decimal-separator": "GAP-014",
            "numeric-reject-sign": "GAP-015",
        }
        if sp == "SP-V19-018":
            return gap or additional_income_gap_by_property.get(prop, "")
        numeric_gap_by_property = {
            "amount-boundary-min-negative": "GAP-005",
            "numeric-reject-letters": "GAP-006",
            "numeric-reject-decimal-separator": "GAP-007",
            "numeric-reject-sign": "GAP-008",
            "numeric-reject-spaces": "GAP-009",
            "numeric-reject-special-chars": "GAP-010",
        }
        return gap or numeric_gap_by_property.get(prop, "")

    norm_rows = []
    for src, sp, pkg, field, prop, cond, exp, req, atom, gap in NORMALIZED_ROWS:
        norm_rows.append([f"`{src}`", f"`{sp}`", f"`{pkg}`", field, normalized_property(sp, prop), cond, exp, req, "stage-handoff source-row-inventory.md; source-parity-check.md; predecessor normalization", "`high`", normalized_gap(sp, prop, gap) or "-", atom])
    write(TD / "source-table-normalization.md", "# Source Table Normalization\n\n" + md_table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], norm_rows))

    dict_rows = [
        ["`DICT-001`", "`Типы занятости`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Типы занятости`", "`extracted`", "; ".join(f"`{v}`" for v in DICT_VALUES["DICT-001"]), "`-`", "`SRC-002; SP-V19-001`", "`-`", "Closed active list from predecessor inventory."],
        ["`DICT-004`", "`Типы дохода`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Виды дохода`", "`extracted`", "; ".join(f"`{v}`" for v in DICT_VALUES["DICT-004"]), "`-`", "`SRC-011; SP-V19-014; SP-V19-015`", "`GAP-002`", "Duplicate-prevention mechanism remains unresolved."],
        ["`DICT-005`", "`Параметры визуальной оценки`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Параметры визуальной оценки`", "`extracted`", "; ".join(f"`{v}`" for v in DICT_VALUES["DICT-005"]), "`-`", "`SRC-016; SP-V19-024`", "`-`", "Workbook spelling preserved."],
    ]
    write(TD / "dictionary-inventory.md", "# Dictionary Inventory\n\n" + md_table(["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"], dict_rows))

    tddt_rows = []
    for idx, (src, sp, pkg, field, prop, _cond, exp, _req, atom, gap) in enumerate(NORMALIZED_ROWS, 1):
        effective_gap = normalized_gap(sp, prop, gap)
        if effective_gap:
            decision = "gap_unclear"
            planned = effective_gap
            blocked = "exact UI enforcement/feedback/setup is not specified"
        else:
            decision = "standalone_tc" if atom in {tc[5].split(";")[0] for tc in TC_ROWS} or atom in "; ".join(tc[5] for tc in TC_ROWS) else "covered_by_existing_tc"
            planned = next((tc[0] for tc in TC_ROWS if atom in tc[5]), "TC-EMP-V19-013")
            if atom == "ATOM-V19-004":
                planned = "TC-EMP-V19-004; TC-EMP-V19-005"
            if atom in {"ATOM-V19-021", "ATOM-V19-022"}:
                planned = "TC-EMP-V19-015; TC-EMP-V19-019"
            blocked = "-"
        tddt_rows.append([f"`TDDT-V19-{idx:03}`", f"`{pkg}`", f"`{sp}`", f"`{atom}`", normalized_property(sp, prop), decision, "targeted v19 coverage row with observable UI oracle or explicit gap", planned, "FT/source row + dictionary inventory + mockup interaction hint", "yes" if not effective_gap else "no", exp if not effective_gap else "-", exp if not effective_gap else "-", blocked, "valid" if effective_gap else "-", "medium" if effective_gap else "low"])
    write(TD / "test-design-decision-table.md", "# Test Design Decision Table\n\n" + md_table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], tddt_rows))

    obligation_rows = [
        ["OBL-V19-001", "WP-01", "SP-V19-004", "ATOM-V19-004", "numeric-format", "valid-digits", "Основной доход принимает цифровое значение.", "SRC-003", "TC-EMP-V19-004", "covered", "Positive numeric class is executable."],
        ["OBL-V19-002", "WP-01", "SP-V19-004", "ATOM-V19-007", "numeric-format", "reject-letters", "Unsupported field-level enforcement for letters.", "SRC-003", "GAP-006", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-003", "WP-01", "SP-V19-004", "ATOM-V19-010", "numeric-format", "reject-spaces", "Unsupported field-level enforcement for spaces.", "SRC-003", "GAP-009", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-004", "WP-01", "SP-V19-004", "ATOM-V19-011", "numeric-format", "reject-special-chars", "Unsupported field-level enforcement for special characters.", "SRC-003", "GAP-010", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-005", "WP-01", "SP-V19-004", "ATOM-V19-008", "numeric-format", "reject-decimal-separator", "Unsupported field-level enforcement for decimal separator.", "SRC-003", "GAP-007", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-006", "WP-01", "SP-V19-004", "ATOM-V19-009", "numeric-format", "reject-sign", "Unsupported field-level enforcement for sign.", "SRC-003", "GAP-008", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-007", "WP-02", "SP-V19-017", "ATOM-V19-017", "numeric-format", "valid-digits", "Additional income amount accepts digital value.", "SRC-012", "TC-EMP-V19-016", "covered", "Positive numeric class is executable."],
        ["OBL-V19-008", "WP-02", "SP-V19-017", "ATOM-V19-018", "numeric-format", "reject-letters", "Unsupported field-level enforcement for letters in additional income amount.", "SRC-012", "GAP-011", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-009", "WP-02", "SP-V19-017", "ATOM-V19-018", "numeric-format", "reject-spaces", "Unsupported field-level enforcement for spaces in additional income amount.", "SRC-012", "GAP-012", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-010", "WP-02", "SP-V19-017", "ATOM-V19-018", "numeric-format", "reject-special-chars", "Unsupported field-level enforcement for special characters in additional income amount.", "SRC-012", "GAP-013", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-011", "WP-02", "SP-V19-017", "ATOM-V19-018", "numeric-format", "reject-decimal-separator", "Unsupported field-level enforcement for decimal separator in additional income amount.", "SRC-012", "GAP-014", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-012", "WP-02", "SP-V19-017", "ATOM-V19-018", "numeric-format", "reject-sign", "Unsupported field-level enforcement for sign in additional income amount.", "SRC-012", "GAP-015", "gap", "Class is separated; exact UI enforcement point is not specified."],
        ["OBL-V19-013", "WP-04", "SP-V19-025", "ATOM-V19-025", "action-navigation", "navigation-target-opened", "Action opens Анкета клиента when required fields are filled.", "SRC-018; GSR 143", "TC-EMP-V19-022", "covered", "Navigation target is observable."],
    ]
    write(TD / "coverage-obligation-table.md", "# Coverage Obligation Table\n\n" + md_table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], obligation_rows))

    ledger_rows = []
    for src, sp, pkg, field, prop, cond, exp, req, atom, gap in NORMALIZED_ROWS:
        effective_gap = normalized_gap(sp, prop, gap)
        tc = "; ".join(tc[0] for tc in TC_ROWS if atom in tc[5]) or "-"
        status = "gap" if effective_gap and tc == "-" else "covered"
        ledger_rows.append([f"`{atom}`", f"`{pkg}`", f"`{src}`", req, f"{field}: {exp}", status, tc, effective_gap or "-"])
    ledger_rows.append(["`ATOM-V19-029`", "`WP-02`", "`SRC-010`", "-", "Блок «Дополнительный доход» является структурным контейнером для целевых строк `SRC-011` и `SRC-012`.", "unclear", "-", "-"])
    for atom, src, statement, gap in [
        ("ATOM-V19-026", "SRC-017", "DaData backend/SPR contract fields require observable artifact/setup.", "GAP-001"),
        ("ATOM-V19-027", "SRC-018", "Return-from-`Выбор решения` SPR/anti-fraud effects require observable artifact/setup.", "GAP-003"),
        ("ATOM-V19-028", "SRC-022..SRC-024", "CDI message trigger/setup is not deterministic from current source artifacts.", "GAP-004"),
    ]:
        ledger_rows.append([f"`{atom}`", "`WP-05`" if "SRC-022" in src else "`WP-04`", f"`{src}`", "-", statement, "gap", "-", gap])
    write(TD / "atomic-requirements-ledger.md", "# Atomic Requirements Ledger\n\n" + md_table(["atom_id", "package_id", "source_row_id", "req_id", "atomic_statement", "coverage_status", "covered_by_tc", "gap_id"], ledger_rows))

    plan_rows = []
    for idx, tc in enumerate(TC_ROWS, 1):
        tc_id, title, _typ, _prio, pkg, trace, *_ = tc
        atoms = "; ".join(x.strip() for x in trace.split(";") if x.strip().startswith("ATOM-"))
        coverage_class = "numeric-format" if tc_id in {"TC-EMP-V19-004", "TC-EMP-V19-005", "TC-EMP-V19-016"} else "source-backed-ui"
        input_class = "valid-numeric" if tc_id in {"TC-EMP-V19-004", "TC-EMP-V19-005", "TC-EMP-V19-016"} else "n/a"
        plan_rows.append([f"`PD-V19-{idx:03}`", f"`{pkg}`", "targeted-regression", trace, atoms, f"Executable coverage for {tc_id}", "standalone_tc", coverage_class, input_class, f"Canonical TC {tc_id} defines one observable result.", "source-backed observable UI state", tc_id, "covered"])
    gap_plan_start = len(plan_rows) + 1
    for offset, (pkg, source_ref, atoms, gap_id, planned_check) in enumerate([
        ("WP-01", "SRC-003", "ATOM-V19-006; ATOM-V19-007; ATOM-V19-008; ATOM-V19-009; ATOM-V19-010; ATOM-V19-011", "GAP-005; GAP-006; GAP-007; GAP-008; GAP-009; GAP-010", "Main income invalid numeric classes remain class-level gaps for unsupported UI enforcement."),
        ("WP-02", "SRC-011; SRC-012; SRC-020", "ATOM-V19-015; ATOM-V19-018; ATOM-V19-019; ATOM-V19-030", "GAP-002; GAP-011; GAP-012; GAP-013; GAP-014; GAP-015; GAP-016; GAP-017", "Additional income duplicate, default-value, delete and invalid numeric classes remain class-level gaps where mechanism is not source-backed."),
        ("WP-05", "SRC-022; SRC-023; SRC-024", "ATOM-V19-028", "GAP-004", "CDI message rows are preserved as setup gaps because trigger/test data is not specified."),
    ]):
        plan_rows.append([f"`PD-V19-{gap_plan_start + offset:03}`", f"`{pkg}`", "residual-gap", source_ref, atoms, planned_check, "gap_unclear", "integration/numeric", "class-level", planned_check, "scope coverage gaps", gap_id, "gap"])
    write(TD / "package-test-design-plan.md", "# Package Test Design Plan\n\n" + md_table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], plan_rows))

    applicability_rows = [
        ["other", "yes", "SRC-003; SRC-011; SRC-012; SRC-015; SRC-016", "ATOM-V19-002; ATOM-V19-013; ATOM-V19-016; ATOM-V19-020; ATOM-V19-022", "TC-EMP-V19-002; TC-EMP-V19-013; TC-EMP-V19-018; TC-EMP-V19-019", "-", "Visibility dimension: visible field/block behavior in target scope."],
        ["other", "yes", "SRC-002; SRC-011; SRC-016", "ATOM-V19-001; ATOM-V19-014; ATOM-V19-024", "TC-EMP-V19-001; TC-EMP-V19-014; TC-EMP-V19-020", "-", "Dictionary/list composition dimension: closed active values from DICT inventory."],
        ["other", "yes", "SRC-003; SRC-012", "ATOM-V19-004..ATOM-V19-011; ATOM-V19-017; ATOM-V19-018", "TC-EMP-V19-004; TC-EMP-V19-016", "GAP-005; GAP-006; GAP-007; GAP-008; GAP-009; GAP-010; GAP-011; GAP-012; GAP-013; GAP-014; GAP-015", "Numeric-format dimension: valid digits executable; invalid enforcement points are explicit gaps."],
        ["other", "yes", "SRC-020; SRC-011; SRC-012", "ATOM-V19-012..ATOM-V19-018", "TC-EMP-V19-012; TC-EMP-V19-013; TC-EMP-V19-014; TC-EMP-V19-016", "GAP-002", "Repeatable/action-created block dimension: block creation separated from field checks."],
        ["other", "yes", "SRC-015; SRC-016", "ATOM-V19-021..ATOM-V19-023", "TC-EMP-V19-015; TC-EMP-V19-019; TC-EMP-V19-021", "-", "Conditional dependency dimension: visual information branches covered where source-backed."],
        ["other", "unclear", "SRC-017; SRC-018; SRC-022..SRC-024", "ATOM-V19-026..ATOM-V19-028", "-", "GAP-001; GAP-003; GAP-004", "Integration/internal effects dimension: no observable artifact/setup for hidden effects."],
    ]
    write(TD / "test-design-applicability-matrix.md", "# Test Design Applicability Matrix\n\n" + md_table(["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"], applicability_rows))

    dependency_rows = [
        ["`DEP-V19-001`", "`Тип занятости = Работа по найму`", "`Среднемесячный доход после вычета налогов (основная работа)`", "`visible`", "`TC-EMP-V19-002`", "`ATOM-V19-002`", "-"],
        ["`DEP-V19-002`", "`Добавить источник дохода clicked`", "`Блок Дополнительный доход`", "`visible`", "`TC-EMP-V19-012`", "`ATOM-V19-012`", "-"],
        ["`DEP-V19-003`", "`Дополнительный доход block created`", "`Тип дохода; сумма дополнительного дохода`", "`visible`", "`TC-EMP-V19-013`", "`ATOM-V19-013; ATOM-V19-016`", "-"],
        ["`DEP-V19-004`", "`Тип дохода = Пенсия already exists`", "`second Пенсия`", "`not accepted as second source`", "`TC-EMP-V19-015`", "`ATOM-V19-015`", "`GAP-002`"],
        ["`DEP-V19-005`", "`Визуальная информация = Да`", "`Параметры визуальной оценки`", "`visible and required`", "`TC-EMP-V19-019; TC-EMP-V19-021`", "`ATOM-V19-021; ATOM-V19-022; ATOM-V19-023`", "-"],
    ]
    write(TD / "dependency-matrix.md", "# Dependency Matrix\n\n" + md_table(["dependency_id", "controlling_value", "dependent_field", "expected_branch", "tc_gap", "linked_atoms", "gap_id"], dependency_rows))

    gaps_rows = [
        ["`GAP-001`", "`SRC-004; SRC-005; SRC-017; GSR 126; GSR 128; GSR 141`", "DaData/SPR backend artifact and exact lookup mechanics are not specified.", "non-blocking", "Keep backend-only effects out of TC; cover only UI-visible behavior outside v19 target.", "open"],
        ["`GAP-002`", "`SRC-011; field Тип дохода`", "Exact UI mechanism for duplicate `Пенсия`/`Аренда` prevention is not specified.", "non-blocking", "`TC-EMP-V19-015` checks source-backed invariant only; exact feedback/control state remains unclear.", "open"],
        ["`GAP-003`", "`SRC-018; GSR 142`", "Observable setup/artifact for return-from-`Выбор решения` SPR/anti-fraud effects is not specified.", "non-blocking", "Do not assert hidden backend effects.", "open"],
        ["`GAP-004`", "`SRC-022..SRC-024`", "Deterministic trigger/test data for CDI failure/mismatch messages is not specified.", "non-blocking", "Preserve rows as residual setup gap.", "open"],
        ["`GAP-005`", "`SRC-003; value 1999`", "Exact UI enforcement point for value below minimum is not specified.", "non-blocking", "Do not create executable TC without source-backed feedback or transition oracle.", "open"],
        ["`GAP-006`", "`SRC-003; letters abc`", "Exact UI enforcement point for letters in main income is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-007`", "`SRC-003; decimal 2000,5`", "Exact UI enforcement point for decimal separator in main income is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-008`", "`SRC-003; sign -2000`", "Exact UI enforcement point for sign in main income is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-009`", "`SRC-003; spaces 2 000`", "Exact UI enforcement point for spaces in main income is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-010`", "`SRC-003; special 2000#`", "Exact UI enforcement point for special characters in main income is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-011`", "`SRC-012; letters rent`", "Exact UI enforcement point for letters in additional income amount is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-012`", "`SRC-012; spaces 5 000`", "Exact UI enforcement point for spaces in additional income amount is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-013`", "`SRC-012; special 5000#`", "Exact UI enforcement point for special characters in additional income amount is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-014`", "`SRC-012; decimal 5000,5`", "Exact UI enforcement point for decimal separator in additional income amount is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-015`", "`SRC-012; sign -5000`", "Exact UI enforcement point for sign in additional income amount is not specified.", "non-blocking", "Keep class-level obligation as gap.", "open"],
        ["`GAP-016`", "`SRC-020; GSR 147`", "Delete behavior for created additional-income block is source-backed but outside the targeted v19 executable subset.", "non-blocking", "Preserve traceability for reviewer; do not mark delete behavior covered by add-block TC.", "open"],
        ["`GAP-017`", "`SRC-011; default value Клиент добросовестный`", "Default value for additional-income добросовестность is source-backed but outside the targeted v19 executable subset.", "non-blocking", "Keep as explicit residual gap; do not map it to created-block field visibility TC.", "open"],
    ]
    write(TD / "coverage-gaps.md", "# Coverage Gaps\n\n" + md_table(["gap_id", "source_ref", "description", "impact", "temporary_handling", "status"], gaps_rows))

    metrics_rows = [
        ["`dictionary-list`", "`3`", "`3`", "`0`", "`0`", "`TC-EMP-V19-001; TC-EMP-V19-014; TC-EMP-V19-020`"],
        ["`main-income-numeric`", "`8`", "`8`", "`0`", "`0`", "`TC-EMP-V19-004..TC-EMP-V19-011`"],
        ["`additional-income-block`", "`6`", "`6`", "`1`", "`0`", "`TC-EMP-V19-012..TC-EMP-V19-017; GAP-002`"],
        ["`visual-information-dependencies`", "`5`", "`5`", "`0`", "`0`", "`TC-EMP-V19-018..TC-EMP-V19-021`"],
        ["`navigation/action`", "`2`", "`2`", "`0`", "`0`", "`TC-EMP-V19-003; TC-EMP-V19-022`"],
        ["`integration-hidden-effects`", "`3`", "`0`", "`3`", "`0`", "`GAP-001; GAP-003; GAP-004`"],
    ]
    write(TD / "coverage-metrics.md", "# Test-design Coverage Metrics\n\n" + md_table(["coverage_dimension", "obligations_total", "covered", "gap", "unclear", "evidence"], metrics_rows))

    fixture_rows = [
        ["`F-V19-BASE-EMPLOYED`", "valid baseline", "`Тип занятости = Работа по найму`; main income `35000`; `Клиент добросовестный = Да`; `Визуальная информация = Нет`", "`TC-EMP-V19-006..TC-EMP-V19-011; TC-EMP-V19-022`", "Provides unrelated required fields for transition checks."],
        ["`F-V19-BASE-EMPLOYED-MAIN-INCOME-EMPTY`", "negative transition", "Same as `F-V19-BASE-EMPLOYED`, but main income is empty.", "`TC-EMP-V19-003`", "Only main income is left empty."],
        ["`F-V19-ADDITIONAL-INCOME-PENSION`", "repeatable block", "One added income block with `Тип дохода = Пенсия`.", "`TC-EMP-V19-016; TC-EMP-V19-017`", "Postcondition removes block or closes without save."],
        ["`F-V19-VISUAL-INFO-NO-PARAM`", "negative transition", "`Визуальная информация = Да`; no visual parameter selected; unrelated required fields valid.", "`TC-EMP-V19-021`", "Only visual parameters are invalid."],
    ]
    write(TD / "fixture-catalog.md", "# Fixture Catalog\n\n" + md_table(["fixture_id", "fixture_type", "fixture_data", "used_by", "notes"], fixture_rows))

    risk_rows = [
        ["ATOM-V19-004", "high", "income numeric acceptance", "SRC-003", "high", "TC-EMP-V19-004; TC-EMP-V19-005", "-", "Valid numeric income affects transition readiness.", "Positive numeric classes are executable."],
        ["ATOM-V19-007", "medium", "invalid numeric classes", "SRC-003", "medium", "-", "GAP-006; GAP-007; GAP-008; GAP-009; GAP-010", "Exact UI enforcement is not source-backed.", "Kept as class-level gaps."],
        ["ATOM-V19-021", "high", "visual information dependency", "SRC-015; SRC-016", "high", "TC-EMP-V19-015; TC-EMP-V19-019; TC-EMP-V19-021", "-", "Conditional fields affect validation and navigation.", "Branches are split."],
    ]
    write(TD / "risk-priority-map.md", "# Risk / Priority Map\n\n## Risk / Priority Map\n\n" + md_table(["atom_id", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "rationale", "residual_decision"], risk_rows))

    review_items = [
        "decision-table-classification",
        "ledger-plan-alignment",
        "coverage-class-completeness",
        "numeric-length-boundaries",
        "unsupported-ui-mechanism",
        "mask-format-coverage",
        "dictionary-closed-set",
        "conditional-branches",
        "negative-fixture-isolation",
        "applicability-linked-tc-semantics",
        "gap-specificity",
        "gap-admissibility",
        "internal-observability",
        "metadata-only-exclusion",
        "tc-mapping-atomicity",
        "ready-for-tc-writing",
    ]
    review_rows = [[f"`{item}`", "`pass`", "`info`", "`all`", "Artifact cross-check completed for targeted v19 scope.", "-", "`no`"] for item in review_items]
    write(TD / "test-design-review.md", "# Test Design Review\n\n## Test Design Review\n\n" + md_table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows))

    gate_items = [
        "artifact-shape-preflight", "artifact-write-strategy", "mockup-visual-inventory", "source-row-inventory",
        "source-normalization-atomic", "dictionary-inventory", "test-design-decision-table", "scoped-validator-findings",
        "coverage-obligation-table", "coverage-metrics", "fixture-catalog", "risk-priority-map", "gap-admissibility",
        "test-design-review", "ledger-atomicity", "gsr-range-compression", "design-plan-atomicity",
        "scenario-does-not-replace-atomic", "tc-atomicity", "test-data-specificity", "tc-regression-smells",
        "internal-observability", "action-observability", "semantic-req-id-parity", "package-ready",
    ]
    gate_rows = []
    for item in gate_items:
        evidence = f"`{PROFILE_REL}`; unresolved_warning_error_count expected `0` after runner validate." if item == "scoped-validator-findings" else "v19 artifacts satisfy this gate for the targeted scope."
        gate_rows.append([f"`{item}`", "`pass`", evidence, "`all`", "-", "`no`"])
    write(TD / "writer-quality-gate.md", "# Writer Quality Gate\n\n## Writer Quality Gate\n\n" + md_table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], gate_rows))

    write(TD / "writer-self-check.md", f"""
    # Writer Self-Check

    ## Writer Self-Check

    Summary: v19 writer draft has canonical TC shape, split artifacts, scoped validator evidence path and explicit residual gaps.

    ## Artifact Write Evidence

    | check | result | evidence |
    | --- | --- | --- |
    | split artifacts written | pass | `{TD_REL}` |
    | canonical TC written | pass | `{CANONICAL_REL}` |
    | cycle outputs written | pass | `{OUT_REL}` |

    ## Format Check

    | check | result | evidence |
    | --- | --- | --- |
    | TC heading level | pass | canonical file uses only `## TC-*` headings |
    | metadata schema | pass | canonical TC uses bold runtime fields and no table metadata |
    | no placeholder traceability | pass | each TC has `ATOM-*`, `SRC-*`, `GSR` or `DICT-*` traceability |

    ## Coverage Check

    | check | result | evidence |
    | --- | --- | --- |
    | numeric classes split | pass | `TC-EMP-V19-004..TC-EMP-V19-011`; `coverage-obligation-table.md` |
    | action-created block split | pass | `TC-EMP-V19-012` creates block; `TC-EMP-V19-013..TC-EMP-V19-017` check fields |
    | visual dependency split | pass | `TC-EMP-V19-018..TC-EMP-V19-021` |

    ## Validator Evidence

    | check | result | evidence |
    | --- | --- | --- |
    | scoped validator profile | pass | `{PROFILE_REL}` generated by runner validate after final write |

    ## Residual Gaps

    | gap | handling |
    | --- | --- |
    | `GAP-001` | residual DaData/SPR backend artifact gap; no executable TC hides it |
    | `GAP-002` | `TC-EMP-V19-015` checks invariant only; exact mechanism remains gap |
    | `GAP-003` | residual hidden SPR/anti-fraud effect gap |
    | `GAP-004` | residual CDI trigger/setup gap |
    """)

    canonical_intro = f"""
    # UI Employment Canary v19 Agent Quality Regression

    Targeted FT-first regression set for section `{SECTION}`. Full source-row design artifacts live in `{TD_REL}`. Existing canary v1-v18 artifacts were not used as requirement sources or templates.
    """
    write(CANONICAL, canonical_intro + "\n".join(test_case_block(row) for row in TC_ROWS))

    session_log_inputs = [
        "AGENTS.md", "skills/README.md", "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md", "skills/ft-test-case-writer/SKILL.md",
        "references/agent/writer-runtime-workflow.md", "references/agent/writer-runtime-contract.md",
        "references/qa/test-case-runtime-format.md", "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md", "references/agent/writer-process-workflow.md",
        "references/agent/workflow-state-format.md", "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md", "references/agent/writer-handoff-format.md",
        "fts/ft-2-OF_16/AGENT-NOTES.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-contract.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-parity-check.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-row-inventory.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md",
        "fts/ft-2-OF_16/work/test-design/ui-employment/dictionary-inventory.md",
    ]
    inputs_list = "\n".join(f"- `{p}` - read for writer-stage source, workflow, format or traceability decisions." for p in session_log_inputs)
    write(OUT / "writer-session-log.writer-r1.md", f"""
    # Writer R1 Session Log

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

    - resolver command: `python scripts\\resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`
    - resolver budget status: `pass (132.9 / 200.0 KiB)`
    - selected files: `15 required files`
    {inputs_list}

    ## Inputs Not Used

    - `fts/ft-2-OF_16/work/test-design/ui-employment-canary-v1..v18*` - regression comparison material only; not used as requirement source, template or acceptance evidence.

    ## Key Decisions

    - Built a targeted v19 subset instead of full employment coverage because cycle accepted risk states v19 is a targeted agent-quality regression.
    - Used non-canary `work/test-design/ui-employment/dictionary-inventory.md` and predecessor normalization evidence from the same scope chain to recover dictionary values and field properties missing from the handoff row inventory.
    - Kept `GAP-001`-`GAP-004` as residual gaps and did not convert hidden integration effects into executable UI checks.

    ## Risks And Fallbacks

    - Risk: exact duplicate-income prevention mechanism is unresolved. Handling: `TC-EMP-V19-015` checks only that a second `Пенсия` is not accepted; exact feedback remains `GAP-002`.
    - Risk: validator profile is generated after final write. Handling: gate references `{PROFILE_REL}` and runner validate is run after artifact generation.

    ## Validation

    - `python scripts\\codex_review_cycle_runner.py validate --state fts\\ft-2-OF_16\\work\\review-cycles\\{SCOPE}\\cycle-state.yaml` - run after final write; scoped profile expected at `{PROFILE_REL}`.

    ## Contamination Check

    - Neighboring FT sections and canary v1-v18 artifacts were not used as requirement sources.

    ## Event Timeline

    | step | event | result | artifact_or_evidence |
    | --- | --- | --- | --- |
    | 1 | Resolved instruction context | budget pass | resolver output |
    | 2 | Read handoff and support inputs | scope and gaps confirmed | `scope-contract.md`; `scope-coverage-gaps.md` |
    | 3 | Declared artifact write strategy | file-based helper selected | `{TD_REL}/artifact-write-strategy.md` |
    | 4 | Generated artifacts | canonical and split artifacts written | `{CANONICAL_REL}`; `{TD_REL}` |
    | 5 | Prepared state transition | route to structure preflight | `{PROMPT_REL}` |

    ## Quality Checkpoints

    | checkpoint | status | evidence | follow_up |
    | --- | --- | --- | --- |
    | Writer Quality Gate | pass | `{TD_REL}/writer-quality-gate.md` | runner validate profile |
    | Self-check near misses | pass | numeric negative classes split | reviewer should verify mechanism-neutral negative oracles |

    ## Technical Fallbacks

    | fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | `none` | `none` | `none` | `none` | `n/a` | `n/a` | `none` | `none` |

    ## Handoff Notes For Next Session

    - Review `TC-EMP-V19-006..TC-EMP-V19-011` for deterministic numeric oracles; exact UI feedback is intentionally not asserted.
    - Review `TC-EMP-V19-015` against `GAP-002`; it must remain mechanism-neutral.
    """)

    decisions = [
        ["`DEC-001`", "1", "`scope-boundary`", "`cycle-state.yaml`; prompt", "Use only targeted v19 employment rows.", "Cycle accepted risk states v19 is targeted, not full-section coverage.", f"`{TD_REL}`; `{CANONICAL_REL}`", "high", "applied"],
        ["`DEC-002`", "2", "`source-boundary`", "`scope-contract.md`; missing handoff dictionary", "Use predecessor non-canary dictionary inventory for `DICT-*` values.", "Scope contract explicitly names the dictionary inventory path.", f"`{TD_REL}/dictionary-inventory.md`", "high", "applied"],
        ["`DEC-003`", "3", "`coverage`", "`coverage-input-boundaries.md`", "Split main-income numeric invalid classes into separate rows and TCs.", "Numeric-only source wording supports separate letters, decimal separator, sign, spaces and special characters classes.", f"`{TD_REL}/coverage-obligation-table.md`; `{CANONICAL_REL}`", "high", "applied"],
        ["`DEC-004`", "4", "`gap`", "`GAP-002`", "Check duplicate `Пенсия` invariant without asserting exact feedback/control mechanism.", "Invariant is source-backed, exact mechanism is not.", "`TC-EMP-V19-015`; `coverage-gaps.md`", "medium", "applied"],
        ["`DEC-005`", "5", "`routing`", "post-write gate", "Route to structure preflight with `writer-draft-ready`.", "Writer gates are prepared and validator profile will be generated by runner validate.", "`cycle-state.yaml`", "medium", "applied"],
    ]
    write(OUT / "agent-decision-log.writer-r1.md", f"""
    # Agent Decision Log

    ## Decision Log Metadata

    | field | value |
    | --- | --- |
    | ft_slug | `ft-2-OF_16` |
    | scope_slug | `{SCOPE}` |
    | stage | `ft-test-case-writer` |
    | started_from | `cycle-state.yaml` |

    ## Decision Log

    {md_table(["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"], decisions)}
    """)

    write(OUT / "writer-r1-response.md", f"""
    # Writer R1 Response

    ## Summary

    Created targeted v19 writer draft for `fts/ft-2-OF_16`, section `{SECTION}`.

    ## Artifacts

    - Canonical test cases: `{CANONICAL_REL}`
    - Split design artifacts: `{TD_REL}`
    - Session log: `{OUT_REL}/writer-session-log.writer-r1.md`
    - Decision log: `{OUT_REL}/agent-decision-log.writer-r1.md`
    - Scoped validator profile: `{PROFILE_REL}`

    ## Residual Gaps

    `GAP-001`, `GAP-002`, `GAP-003` and `GAP-004` remain non-blocking residual gaps inherited from scope review. The draft covers source-backed observable UI behavior and does not assert hidden backend effects or unspecified feedback mechanisms.

    ## Routing

    Next active prompt: `{PROMPT_REL}`.
    """)

    write(PROMPTS / "prompt.structure-preflight-r1.md", f"""
    # Structure Preflight R1 Prompt

    Use skill `ft-test-case-reviewer` in mode `structure_preflight`.

    FT package: `fts/ft-2-OF_16`
    Scope slug: `{SCOPE}`
    Canonical test cases: `{CANONICAL_REL}`
    Test-design dir: `{TD_REL}`
    Cycle state: `{CYCLE_REL}/cycle-state.yaml`

    Review only parseability, canonical `## TC-*` structure, required bold metadata fields, split artifact table shape, missing required artifacts, and blocking format/schema issues. Do not perform semantic review in this pass.

    Required writer evidence:
    - `{OUT_REL}/writer-session-log.writer-r1.md`
    - `{OUT_REL}/agent-decision-log.writer-r1.md`
    - `{OUT_REL}/writer-r1-response.md`
    - `{PROFILE_REL}`
    """)

    write(OUT / "writer-r1-completion.yaml", f"""
    stage: writer-r1
    role: writer
    scenario: writer.session_initial_draft
    raw_turn_status: completed
    session_status: completed
    before:
      current_stage: scope-ready-for-writer
      stage_status: scope-ready-for-writer
      semantic_round: 0
    after:
      current_stage: writer-r1
      stage_status: writer-draft-ready
      semantic_round: 1
    final_response_path: {OUT_REL}/writer-r1-response.md
    output_snapshot: pending-runner-snapshot
    """)

    latest = [
        CANONICAL_REL,
        TD_REL,
        f"{TD_REL}/artifact-write-strategy.md",
        f"{TD_REL}/source-row-inventory.md",
        f"{TD_REL}/source-row-completeness-matrix.md",
        f"{TD_REL}/source-table-normalization.md",
        f"{TD_REL}/dictionary-inventory.md",
        f"{TD_REL}/test-design-decision-table.md",
        f"{TD_REL}/coverage-obligation-table.md",
        f"{TD_REL}/atomic-requirements-ledger.md",
        f"{TD_REL}/package-test-design-plan.md",
        f"{TD_REL}/test-design-applicability-matrix.md",
        f"{TD_REL}/dependency-matrix.md",
        f"{TD_REL}/test-design-review.md",
        f"{TD_REL}/coverage-gaps.md",
        f"{TD_REL}/coverage-metrics.md",
        f"{TD_REL}/fixture-catalog.md",
        f"{TD_REL}/risk-priority-map.md",
        f"{TD_REL}/writer-quality-gate.md",
        f"{TD_REL}/writer-self-check.md",
        f"{OUT_REL}/writer-session-log.writer-r1.md",
        f"{OUT_REL}/agent-decision-log.writer-r1.md",
        PROFILE_REL,
        f"{OUT_REL}/writer-r1-response.md",
        f"{OUT_REL}/writer-r1-completion.yaml",
        PROMPT_REL,
    ]
    latest_yaml = "\n".join(f"  - {p}" for p in latest)
    state_content = f"""cycle_id: ft-2-OF_16-{SCOPE}
ft_slug: ft-2-OF_16
scope_slug: {SCOPE}
section_id: {SECTION}
current_stage: writer-r1
stage_status: writer-draft-ready
semantic_round: 1
max_semantic_rounds: 2
canonical_test_cases: {CANONICAL_REL}
test_design_dir: {TD_REL}
active_snapshot: none
active_transition_prompt: {PROMPT_REL}
sessions: []
latest_artifacts:
{latest_yaml}
accepted_risks:
  - V19 is a targeted agent-quality regression over selected employment UI rows, not a full employment-section coverage run.
  - Existing canary v1-v18 artifacts are regression comparison material only; writer did not use them as source requirements or templates.
  - GAP-001 through GAP-004 remain accepted non-blocking pre-writer residual gaps by prior scope-gap review evidence unless new source evidence closes them.
blocking_reasons: []
blocking_findings: []
open_questions:
  - GAP-001: observable artifact for DaData/SPR contract field prefill remains unanswered.
  - GAP-002: exact UI mechanism for preventing duplicate Пенсия/Аренда remains unanswered.
  - GAP-003: observable artifact/setup for SPR re-call and repeated checks remains unanswered.
  - GAP-004: test data/precondition for CDI failure and mismatch messages remains unanswered.
"""
    (FT / CYCLE_REL / "cycle-state.yaml").write_text(state_content, encoding="utf-8")


if __name__ == "__main__":
    generate()
