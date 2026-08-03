from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path("fts/ft-2-OF_16")
SCOPE = "ui-employment-canary-v9-agent-gate-regression"
TD = ROOT / "work" / "test-design" / SCOPE
SECTIONS = TD / "artifact-sections"
MANIFESTS = SECTIONS / "manifests"
CANONICAL = ROOT / "test-cases" / "2-1-1-1-1-2-ui-employment-canary-v9-agent-gate-regression.md"
CYCLE = ROOT / "work" / "review-cycles" / SCOPE
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def manifest(name: str, target: Path, title: str, body: str) -> None:
    chunk = SECTIONS / f"{name}.body.md"
    write(chunk, body)
    data = {
        "target_path": str(target.resolve()),
        "sections": [
            {
                "level": 2,
                "heading": title,
                "content_file": os.path.relpath(chunk, MANIFESTS),
            }
        ],
    }
    path = MANIFESTS / f"{name}.manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def manifest_with_preamble(name: str, target: Path, preamble: str, sections: list[tuple[int, str, str]]) -> None:
    preamble_path = SECTIONS / f"{name}.preamble.md"
    write(preamble_path, preamble)
    rendered = []
    for idx, (level, heading, body) in enumerate(sections, start=1):
        chunk = SECTIONS / f"{name}.{idx:02d}.md"
        write(chunk, body)
        rendered.append(
            {
                "level": level,
                "heading": heading,
                "content_file": os.path.relpath(chunk, MANIFESTS),
            }
        )
    data = {
        "target_path": str(target.resolve()),
        "preamble_file": os.path.relpath(preamble_path, MANIFESTS),
        "sections": rendered,
    }
    path = MANIFESTS / f"{name}.manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


DICT_001 = "`Работа по найму`; `Пенсионер (не работает)`; `Индивидуальный предприниматель`; `Собственник бизнеса`; `Частная практика / Самозанятый`; `Безработный`"
DICT_004 = "`Пенсия`; `Аренда`"
DICT_005 = "`Подозрение на мошеничество`; `Подозрение на судимость`; `Подозрение на алкогольное опьянение`; `Подозрение на наркотическое опьянение`; `Подозрение на психическое заболевание`; `Подозрение на социальную инженерию`; `Асоциальный элемент (бомжи, аалкоголики, наркоманы, цыгане)`; `Потенциальный неплательщик`; `Явные признаки нетрудоспособности`; `Отказ от фотографирования`; `Иные подозрения`; `Не выявлено`"


TC_ROWS = [
    ("TC-UI-EMP-V9-001", "WP-01", "Positive", "Medium", "`ATOM-001`; `SRC-002`", "Поле `Тип занятости` отображается при открытии раздела", "Открыт раздел `Сведения о занятости`.", "Не требуются.", ["Просмотреть верхний блок `Сведения о занятости`."], "Поле `Тип занятости` отображается в разделе.", "Не требуются."),
    ("TC-UI-EMP-V9-002", "WP-01", "Negative", "High", "`ATOM-002`; `ATOM-030`; `SRC-002`; `SRC-018`; `GSR 142`", "Пустое обязательное поле `Тип занятости` подсвечивается при переходе дальше", "Открыт раздел `Сведения о занятости`; поле `Тип занятости` не заполнено.", "Все поля, кроме проверяемого, заполнены валидными значениями: `Среднемесячный доход после вычета налогов` не отображается до выбора типа занятости; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Нет`; дополнительные блоки не созданы.", ["Нажать кнопку `Следующий шаг`."], "Поле `Тип занятости` подсвечено красным как незаполненное обязательное поле; раздел `Анкета клиента` не открыт.", "Не требуются."),
    ("TC-UI-EMP-V9-003", "WP-01", "Positive", "High", "`ATOM-004`; `SRC-002`; `DICT-001`", "Список `Тип занятости` содержит все и только активные значения `DICT-001`", "Открыт раздел `Сведения о занятости`.", f"Активные значения `DICT-001`: {DICT_001}.", ["Открыть раскрывающийся список `Тип занятости`.", "Сравнить значения списка с активными значениями `DICT-001`."], f"В списке отображаются все активные значения `DICT-001` и отсутствуют значения вне этого перечня: {DICT_001}.", "Не требуются."),
    ("TC-UI-EMP-V9-004", "WP-01", "Positive", "Medium", "`ATOM-003`; `SRC-002`; `DICT-001`", "Поле `Тип занятости` позволяет изменить выбранное значение", "Открыт раздел `Сведения о занятости`; в поле `Тип занятости` выбрано `Работа по найму`.", "Новое значение: `Пенсионер (не работает)`.", ["Открыть раскрывающийся список `Тип занятости`.", "Выбрать значение `Пенсионер (не работает)`."], "В поле `Тип занятости` отображается значение `Пенсионер (не работает)`.", "Вернуть значение `Работа по найму`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-005", "WP-01", "Positive", "High", "`ATOM-005`; `SRC-003`; `GSR 123`", "Основной доход не отображается до заполнения `Тип занятости`", "Открыт раздел `Сведения о занятости`; поле `Тип занятости` пустое.", "Не требуются.", ["Просмотреть блок `Сведения о занятости`."], "Поле `Среднемесячный доход после вычета налогов` основной работы не отображается.", "Не требуются."),
    ("TC-UI-EMP-V9-006", "WP-01", "Positive", "High", "`ATOM-006`; `SRC-003`; `GSR 123`; `DICT-001`", "Основной доход отображается после заполнения `Тип занятости`", "Открыт раздел `Сведения о занятости`; поле `Тип занятости` пустое.", "Значение `Тип занятости`: `Пенсионер (не работает)`.", ["В поле `Тип занятости` выбрать `Пенсионер (не работает)`."], "Поле `Среднемесячный доход после вычета налогов` основной работы отображается.", "Не требуются."),
    ("TC-UI-EMP-V9-007", "WP-01", "Negative", "High", "`ATOM-007`; `ATOM-030`; `SRC-003`; `SRC-018`; `GSR 123`; `GSR 142`; `DICT-001`", "Пустой основной доход подсвечивается после заполнения `Тип занятости`", "Открыт раздел `Сведения о занятости`; `Тип занятости` = `Пенсионер (не работает)`; поле основного дохода отображается и пустое.", "Все поля, кроме проверяемого, заполнены валидными значениями: `Должность` = `Пенсионер`; дополнительные блоки не созданы; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Нет`.", ["Нажать кнопку `Следующий шаг`."], "Поле `Среднемесячный доход после вычета налогов` основной работы подсвечено красным как незаполненное обязательное поле; раздел `Анкета клиента` не открыт.", "Не требуются."),
    ("TC-UI-EMP-V9-008", "WP-01", "Positive", "Medium", "`ATOM-008`; `SRC-003`; `GSR 124`", "Поле основного дохода позволяет заменить одно числовое значение другим", "Открыт раздел `Сведения о занятости`; поле основного дохода отображается; в поле указано `3000`.", "Новое значение: `3500`.", ["Выделить значение `3000` в поле основного дохода.", "Ввести значение `3500`."], "В поле `Среднемесячный доход после вычета налогов` основной работы отображается значение `3500`.", "Вернуть значение `3000`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-009", "WP-01", "Positive", "High", "`ATOM-009`; `SRC-003`; `GSR 124`", "Поле основного дохода принимает числовое значение больше минимума", "Открыт раздел `Сведения о занятости`; поле основного дохода отображается и пустое.", "Значение: `3500`.", ["Ввести в поле основного дохода значение `3500`."], "В поле `Среднемесячный доход после вычета налогов` основной работы отображается значение `3500`.", "Очистить поле, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-010", "WP-01", "Positive", "High", "`ATOM-010`; `SRC-003`; `GSR 124`", "Поле основного дохода принимает минимальное значение `2000`", "Открыт раздел `Сведения о занятости`; поле основного дохода отображается и пустое.", "Граничное значение: `2000`.", ["Ввести в поле основного дохода значение `2000`."], "В поле `Среднемесячный доход после вычета налогов` основной работы отображается значение `2000`.", "Очистить поле, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-011", "WP-02", "Positive", "Medium", "`ATOM-012`; `SRC-010`; `SRC-020`; `GSR 146`", "Блок `Дополнительный доход` отсутствует до нажатия кнопки добавления", "Открыт раздел `Сведения о занятости`; пользователь еще не нажимал `Добавить источник дохода`.", "Не требуются.", ["Просмотреть область `Дополнительный доход`."], "Поля `Тип дохода` и `Среднемесячный доход после вычета налогов` дополнительного дохода не отображаются как созданный блок дохода.", "Не требуются."),
    ("TC-UI-EMP-V9-012", "WP-02", "Positive", "High", "`ATOM-013`; `SRC-010`; `SRC-020`; `GSR 146`", "Кнопка `Добавить источник дохода` создает блок `Дополнительный доход`", "Открыт раздел `Сведения о занятости`; созданных блоков `Дополнительный доход` нет.", "Не требуются.", ["Нажать кнопку `Добавить источник дохода`."], "В разделе отображается созданный блок `Дополнительный доход` с полями `Тип дохода` и `Среднемесячный доход после вычета налогов`.", "Удалить созданный блок `Дополнительный доход` кнопкой-пиктограммой `Корзина`."),
    ("TC-UI-EMP-V9-013", "WP-02", "Positive", "High", "`ATOM-014`; `SRC-020`; `GSR 147`", "Созданный блок `Дополнительный доход` удаляется через `Корзина`", "Открыт раздел `Сведения о занятости`; создан один блок `Дополнительный доход`.", "Не требуются.", ["В созданном блоке `Дополнительный доход` нажать кнопку-пиктограмму `Корзина`."], "Созданный блок `Дополнительный доход` больше не отображается в разделе.", "Не требуются."),
    ("TC-UI-EMP-V9-014", "WP-02", "Negative", "High", "`ATOM-015`; `ATOM-018`; `ATOM-030`; `SRC-011`; `SRC-012`; `SRC-018`; `SRC-020`; `GSR 142`; `GSR 146`", "Обязательные поля созданного дополнительного дохода подсвечиваются при переходе дальше", "Открыт раздел `Сведения о занятости`; создан один блок `Дополнительный доход`; поля `Тип дохода` и `Среднемесячный доход после вычета налогов` в нем пустые.", "Все поля, кроме проверяемых полей созданного блока, заполнены валидными значениями: `Тип занятости` = `Пенсионер (не работает)`; основной доход = `2000`; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Нет`.", ["Нажать кнопку `Следующий шаг`."], "Поля `Тип дохода` и `Среднемесячный доход после вычета налогов` в созданном блоке подсвечены красным как незаполненные обязательные поля; раздел `Анкета клиента` не открыт.", "Удалить созданный блок `Дополнительный доход` кнопкой-пиктограммой `Корзина`."),
    ("TC-UI-EMP-V9-015", "WP-02", "Positive", "High", "`ATOM-016`; `SRC-011`; `DICT-004`", "Список `Тип дохода` содержит все и только активные значения `DICT-004`", "Открыт раздел `Сведения о занятости`; создан один блок `Дополнительный доход`.", f"Активные значения `DICT-004`: {DICT_004}.", ["Открыть раскрывающийся список `Тип дохода` в созданном блоке.", "Сравнить значения списка с активными значениями `DICT-004`."], f"В списке отображаются все активные значения `DICT-004` и отсутствуют значения вне этого перечня: {DICT_004}.", "Удалить созданный блок `Дополнительный доход` кнопкой-пиктограммой `Корзина`."),
    ("TC-UI-EMP-V9-016", "WP-02", "Positive", "High", "`ATOM-019`; `SRC-012`; `GSR 135`", "Поле суммы дополнительного дохода принимает числовое значение", "Открыт раздел `Сведения о занятости`; создан один блок `Дополнительный доход`; поле суммы дополнительного дохода пустое.", "Значение: `12000`.", ["Ввести `12000` в поле `Среднемесячный доход после вычета налогов` созданного блока."], "В поле суммы созданного блока `Дополнительный доход` отображается значение `12000`.", "Удалить созданный блок `Дополнительный доход` кнопкой-пиктограммой `Корзина`."),
    ("TC-UI-EMP-V9-017", "WP-03", "Positive", "Medium", "`ATOM-021`; `ATOM-022`; `SRC-014`; `SRC-015`; `GSR 136`; `GSR 137`", "Переключатели визуальной оценки имеют значение по умолчанию `Нет`", "Открыт раздел `Сведения о занятости` впервые для текущей заявки.", "Не требуются.", ["Просмотреть переключатели `Клиент добросовестный` и `Визуальная информация`."], "У переключателей `Клиент добросовестный` и `Визуальная информация` отображается значение `Нет`.", "Не требуются."),
    ("TC-UI-EMP-V9-018", "WP-03", "Positive", "High", "`ATOM-023`; `ATOM-024`; `SRC-015`; `SRC-016`; `GSR 138`; `GSR 139`", "Выбор `Визуальная информация = Да` отображает параметры визуальной оценки", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Нет`; список параметров визуальной оценки не отображается.", "Не требуются.", ["Переключить `Визуальная информация` в значение `Да`."], "Отображается список `Параметры визуальной оценки`.", "Вернуть `Визуальная информация` в значение `Нет`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-019", "WP-03", "Positive", "High", "`ATOM-025`; `SRC-016`; `GSR 139`; `DICT-005`", "Список `Параметры визуальной оценки` содержит все и только активные значения `DICT-005`", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; список параметров отображается.", f"Активные значения `DICT-005`: {DICT_005}.", ["Просмотреть список `Параметры визуальной оценки`.", "Сравнить значения списка с активными значениями `DICT-005`."], f"В списке отображаются все активные значения `DICT-005`, по каждому значению доступен чек-бокс, и отсутствуют значения вне этого перечня: {DICT_005}.", "Вернуть `Визуальная информация` в значение `Нет`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-020", "WP-03", "Negative", "High", "`ATOM-026`; `ATOM-030`; `SRC-016`; `SRC-018`; `GSR 140`; `GSR 142`", "Пустой список параметров визуальной оценки подсвечивается при переходе дальше", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; ни один параметр визуальной оценки не выбран.", "Все поля, кроме проверяемого списка параметров, заполнены валидными значениями: `Тип занятости` = `Пенсионер (не работает)`; основной доход = `2000`; дополнительные блоки не созданы.", ["Нажать кнопку `Следующий шаг`."], "Список `Параметры визуальной оценки` подсвечен красным как незаполненное обязательное поле; раздел `Анкета клиента` не открыт.", "Выключить `Визуальная информация`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-021", "WP-03", "Positive", "High", "`ATOM-027`; `SRC-016`; `GSR 139`; `GSR 140`; `DICT-005`", "Один параметр визуальной оценки отображается как выбранный", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; ни один параметр визуальной оценки не выбран.", "Выбранное значение: `Не выявлено`.", ["Отметить чек-бокс `Не выявлено`."], "В списке `Параметры визуальной оценки` выбрано значение `Не выявлено`.", "Снять отметку `Не выявлено` и выключить `Визуальная информация`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-022", "WP-03", "Positive", "High", "`ATOM-028`; `SRC-016`; `GSR 138`; `GSR 139`; `DICT-005`", "Список параметров визуальной оценки поддерживает множественный выбор", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; ни один параметр визуальной оценки не выбран.", "Значения: `Не выявлено`; `Иные подозрения`.", ["Отметить чек-бокс `Не выявлено`.", "Отметить чек-бокс `Иные подозрения`."], "В списке `Параметры визуальной оценки` одновременно выбраны значения `Не выявлено` и `Иные подозрения`.", "Снять выбранные отметки и выключить `Визуальная информация`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-023", "WP-03", "Negative", "High", "`ATOM-029`; `ATOM-030`; `SRC-016`; `SRC-018`; `GSR 139`; `GSR 140`; `GSR 142`; `DICT-005`", "Снятие всех отметок снова нарушает обязательность параметров визуальной оценки", "Открыт раздел `Сведения о занятости`; `Визуальная информация` = `Да`; выбрано значение `Не выявлено`.", "Все поля, кроме проверяемого списка параметров, заполнены валидными значениями: `Тип занятости` = `Пенсионер (не работает)`; основной доход = `2000`; дополнительные блоки не созданы.", ["Снять отметку `Не выявлено`.", "Нажать кнопку `Следующий шаг`."], "Ни один параметр визуальной оценки не выбран; список `Параметры визуальной оценки` подсвечен красным как незаполненное обязательное поле; раздел `Анкета клиента` не открыт.", "Выключить `Визуальная информация`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-024", "WP-04", "Positive", "High", "`ATOM-031`; `SRC-018`; `GSR 143`; `DICT-001`", "Кнопка `Следующий шаг` открывает раздел `Анкета клиента` при заполненных обязательных полях", "Открыт раздел `Сведения о занятости`; заявка не находится в возврате со статуса `Выбор решения`.", "Заполнены обязательные поля: `Тип занятости` = `Пенсионер (не работает)`; основной доход = `2000`; `Должность` = `Пенсионер`; дополнительные блоки не созданы; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Нет`.", ["Нажать кнопку `Следующий шаг`."], "Открыт раздел `Анкета клиента`; печатная форма `Заявление-анкета` отображается в этом разделе как сформированная форма.", "Вернуться к разделу `Сведения о занятости`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-025", "WP-04", "Positive", "High", "`ATOM-032`; `SRC-019`; `GSR 144`", "Кнопка `Добавить работу по совместительству` отображает блок совместительства", "Открыт раздел `Сведения о занятости`; блок `Работа по совместительству` еще не создан.", "Не требуются.", ["Нажать кнопку `Добавить работу по совместительству`."], "В разделе отображается блок `Работа по совместительству` с полями из блока `Сведения о занятости` / `Работа по совместительству`.", "Удалить созданный блок `Работа по совместительству` кнопкой-пиктограммой `Корзина`."),
    ("TC-UI-EMP-V9-026", "WP-04", "Positive", "High", "`ATOM-033`; `SRC-019`; `GSR 145`", "Созданный блок `Работа по совместительству` удаляется через `Корзина`", "Открыт раздел `Сведения о занятости`; создан один блок `Работа по совместительству`.", "Не требуются.", ["В созданном блоке `Работа по совместительству` нажать кнопку-пиктограмму `Корзина`."], "Созданный блок `Работа по совместительству` больше не отображается в разделе.", "Не требуются."),
    ("TC-UI-EMP-V9-027", "WP-04", "Positive", "High", "`ATOM-034`; `SRC-021`; `GSR 148`", "Кнопка `Назад` при несохраненных данных показывает подтверждение с вариантами `Да` и `Нет`", "Открыт раздел `Сведения о занятости`; в поле основного дохода было значение `3000`.", "Новое несохраненное значение: `3500`.", ["Изменить значение основного дохода с `3000` на `3500`.", "Нажать кнопку `Назад`."], "Отображается уведомление о подтверждении действия с вариантами ответа `Да` и `Нет`.", "В уведомлении выбрать вариант, нужный для продолжения проверки; если проверка прекращается, вернуться в раздел без изменения данных."),
    ("TC-UI-EMP-V9-028", "WP-04", "Positive", "High", "`ATOM-035`; `SRC-021`; `GSR 148`", "Ветка `Назад` -> `Да` сохраняет данные и открывает `Основная информация`", "Открыт раздел `Сведения о занятости`; в поле основного дохода сохранено значение `3000`; уведомление `Назад` с вариантами `Да`/`Нет` отображается после изменения значения на `3500`.", "Выбор в уведомлении: `Да`.", ["В уведомлении нажать `Да`.", "Вернуться в раздел `Сведения о занятости` из карточки УЗ."], "Открыт раздел `Основная информация`; после повторного открытия раздела `Сведения о занятости` в поле основного дохода отображается значение `3500`.", "Вернуть значение основного дохода `3000`, если это нужно для продолжения проверки в той же заявке."),
    ("TC-UI-EMP-V9-029", "WP-04", "Positive", "High", "`ATOM-036`; `SRC-021`; `GSR 148`", "Ветка `Назад` -> `Нет` не сохраняет данные и открывает `Основная информация`", "Открыт раздел `Сведения о занятости`; в поле основного дохода сохранено значение `3000`; уведомление `Назад` с вариантами `Да`/`Нет` отображается после изменения значения на `3500`.", "Выбор в уведомлении: `Нет`.", ["В уведомлении нажать `Нет`.", "Вернуться в раздел `Сведения о занятости` из карточки УЗ."], "Открыт раздел `Основная информация`; после повторного открытия раздела `Сведения о занятости` в поле основного дохода отображается прежнее значение `3000`.", "Не требуются."),
]


def tc_markdown() -> str:
    blocks = []
    for tc_id, package, typ, priority, trace, title, pre, data, steps, expected, post in TC_ROWS:
        step_text = "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))
        blocks.append(
            f"""### {tc_id} — {title}

**Название:** {title}

**Тип:** {typ}

**Приоритет:** {priority}

**package_id:** `{package}`

**Трассировка:** {trace}

**Предусловия:** {pre}

**Тестовые данные:** {data}

**Шаги:**

{step_text}

**Итоговый ожидаемый результат:** {expected}

**Постусловия:** {post}
"""
        )
    return "\n".join(blocks)


def main() -> None:
    for path in [TD, SECTIONS, MANIFESTS, OUTPUTS, PROMPTS, CANONICAL.parent]:
        path.mkdir(parents=True, exist_ok=True)

    manifest(
        "artifact-write-strategy",
        TD / "artifact-write-strategy.md",
        "Artifact Write Strategy",
        """
| item | value | evidence |
| --- | --- | --- |
| preflight_result | `large-file / package-based` | v9 scope has multiple `WP-*`, table normalization, dictionaries, coverage obligations and canonical TC file. |
| write_method | `file-based manifest/chunked writing` | `scripts/write_artifact_sections.py --manifest <manifest.json>` is used for each target artifact. |
| forbidden_methods_checked | `yes` | No one-shot PowerShell argument, no PowerShell here-string as final artifact writer, no inline giant command. |
| chunk_plan | `design artifacts -> canonical TC -> cycle outputs -> next prompt` | Generated UTF-8 chunks live under `work/test-design/ui-employment-canary-v9-agent-gate-regression/artifact-sections/`. |
| helper_artifacts | `scripts/build_ui_employment_canary_v9_sections.py`; `artifact-sections/manifests/*.manifest.json` | Builder creates chunks/manifests; committed `scripts/write_artifact_sections.py` writes final Markdown targets. |
| validation_plan | `python scripts\\validate_agent_artifacts.py --root fts\\ft-2-OF_16 --json` | Run after final artifact write and before cycle-state advancement. |
""",
    )

    manifest(
        "mockup-usage",
        TD / "mockup-usage.md",
        "Mockup Usage",
        """
| item | value | evidence |
| --- | --- | --- |
| inventory | `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md` | `opened = yes`; mockups `Сведения о занятости.png` and `Сведения о занятости2.png`. |
| used_for_steps | `yes` | Dropdown, add-area, trash icon, toggles, `Назад`, `Следующий шаг` interaction hints are used only as UI mechanics. |
| not_used_as_requirement_source | `yes` | Field behavior comes from DOCX/PDF/support rows; mockup-only sample values and validation text are not asserted. |
| mockup_only_items | `left side status cards; sample values; exact text Выберите значение` | Excluded from executable requirements unless FT/support/evidence states them. |
| ft_conflicts | `Визуальная оценка` mockup label vs FT `Визуальная информация` | FT name is canonical; mockup label may be treated only as an alias during manual execution. |
""",
    )

    selected_rows = [
        ("SRC-002", "WP-01", "Тип занятости", "DOCX section-23 table 11 row 3; PDF p.61", "-", "yes", "ATOM-001; ATOM-002; ATOM-003; ATOM-004"),
        ("SRC-003", "WP-01", "Среднемесячный доход после вычета налогов (основная работа)", "DOCX section-23 table 11 row 4; PDF p.61", "GSR 123; GSR 124", "yes", "ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011; GAP-005"),
        ("SRC-010", "WP-02", "Блок «Дополнительный доход»", "DOCX section-23 table 11 row 11; PDF p.62", "-", "yes", "ATOM-012"),
        ("SRC-011", "WP-02", "Тип дохода", "DOCX section-23 table 11 row 12; PDF p.62", "-", "yes", "ATOM-015; ATOM-016; ATOM-017; GAP-002"),
        ("SRC-012", "WP-02", "Среднемесячный доход после вычета налогов (дополнительный доход)", "DOCX section-23 table 11 row 13; PDF p.62", "GSR 135", "yes", "ATOM-018; ATOM-019; ATOM-020; GAP-006"),
        ("SRC-014", "WP-03", "Клиент добросовестный", "DOCX section-23 table 11 row 15; PDF p.62", "GSR 136", "yes", "ATOM-021"),
        ("SRC-015", "WP-03", "Визуальная информация", "DOCX section-23 table 11 row 16; PDF p.62", "GSR 137; GSR 138", "yes", "ATOM-022; ATOM-023"),
        ("SRC-016", "WP-03", "Параметры визуальной оценки", "DOCX section-23 table 11 row 17; PDF pp.62-63", "GSR 139; GSR 140", "yes", "ATOM-024; ATOM-025; ATOM-026; ATOM-027; ATOM-028; ATOM-029"),
        ("SRC-018", "WP-04", "«Следующий шаг»", "DOCX section-24 table 12 row 2; PDF pp.63-65", "GSR 142; GSR 143", "yes", "ATOM-030; ATOM-031; GAP-003"),
        ("SRC-019", "WP-04", "«Добавить работу по совместительству»", "DOCX section-24 table 12 row 3; PDF p.65", "GSR 144; GSR 145", "yes", "ATOM-032; ATOM-033"),
        ("SRC-020", "WP-02", "«Добавить дополнительный доход»", "DOCX section-24 table 12 row 4; PDF p.65", "GSR 146; GSR 147", "yes", "ATOM-013; ATOM-014"),
        ("SRC-021", "WP-04", "«Назад»", "DOCX section-24 table 12 row 5; PDF p.65", "GSR 148", "yes", "ATOM-034; ATOM-035; ATOM-036"),
        ("SRC-004", "WP-01", "Наименование организации, ИНН", "DOCX section-23 table 11 row 5; PDF p.61", "GSR 125; GSR 126", "unclear", "GAP-001"),
        ("SRC-005", "WP-01", "Фактический адрес работы", "DOCX section-23 table 11 row 6; PDF p.61", "GSR 127; GSR 128", "unclear", "GAP-001"),
        ("SRC-017", "WP-03", "Примечание DaData по найденной организации", "DOCX section-23 note; PDF p.63", "GSR 141", "unclear", "GAP-001"),
        ("SRC-022", "WP-05", "CDI: не удалось верифицировать ИНН", "PDF pp.65-66", "-", "unclear", "GAP-004"),
        ("SRC-023", "WP-05", "CDI: данные клиента отличаются от данных заявки", "PDF p.66", "-", "unclear", "GAP-004"),
        ("SRC-024", "WP-05", "CDI: подтверждение замены данных", "PDF p.67", "-", "unclear", "GAP-004"),
    ]
    manifest(
        "source-row-inventory",
        TD / "source-row-inventory.md",
        "Source Row Inventory",
        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(f"| `{r}` | `{p}` | {f} | {s} | {g} | `{i}` | {m} |" for r, p, f, s, g, i, m in selected_rows)
        + "\n\nNotes: `fixture-only` rows are not executable v9 scope rows; they may be used only to build valid UI fixture context. `SRC-022`-`SRC-024` stay visible through `GAP-004` but are out of v9 executable scope by active prompt.",
    )

    completeness = """
| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision |
| --- | --- | --- | --- | --- | --- |
| `SRC-003` | `GSR 123; GSR 124` | `SRC-003.P01; SRC-003.P02; SRC-003.P03; SRC-003.P04; SRC-003.P05; SRC-003.P06` | `ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011` | `GAP-005` | `split-complete` |
| `SRC-011` | `no GSR` | `SRC-011.P01; SRC-011.P02; SRC-011.P03; SRC-011.P04` | `ATOM-015; ATOM-016; ATOM-017` | `GAP-002` | `split-complete` |
| `SRC-012` | `GSR 135` | `SRC-012.P01; SRC-012.P02; SRC-012.P03` | `ATOM-018; ATOM-019; ATOM-020` | `GAP-006` | `split-complete` |
| `SRC-015` | `GSR 137; GSR 138` | `SRC-015.P01; SRC-015.P02` | `ATOM-022; ATOM-023` | `-` | `split-complete` |
| `SRC-016` | `GSR 139; GSR 140` | `SRC-016.P01; SRC-016.P02; SRC-016.P03; SRC-016.P04; SRC-016.P05; SRC-016.P06; SRC-016.P07` | `ATOM-024; ATOM-025; ATOM-026; ATOM-027; ATOM-028; ATOM-029` | `-` | `split-complete` |
| `SRC-018` | `GSR 142; GSR 143` | `SRC-018.P01; SRC-018.P02; SRC-018.P03; SRC-018.P04` | `ATOM-030; ATOM-031` | `GAP-003; GAP-007` | `split-complete` |
| `SRC-019` | `GSR 144; GSR 145` | `SRC-019.P01; SRC-019.P02` | `ATOM-032; ATOM-033` | `-` | `split-complete` |
| `SRC-020` | `GSR 146; GSR 147` | `SRC-020.P01; SRC-020.P02` | `ATOM-013; ATOM-014` | `-` | `split-complete` |
| `SRC-021` | `GSR 148` | `SRC-021.P01; SRC-021.P02; SRC-021.P03` | `ATOM-034; ATOM-035; ATOM-036` | `-` | `split-complete` |
| `SRC-004` | `GSR 125; GSR 126` | `SRC-004.P01; SRC-004.P02; SRC-004.P03; SRC-004.P04; SRC-004.P05` | `-` | `GAP-001` | `gap-only-fixture-context` |
| `SRC-005` | `GSR 127; GSR 128` | `SRC-005.P01; SRC-005.P02; SRC-005.P03` | `-` | `GAP-001` | `gap-only-fixture-context` |
"""
    norm_rows = [
        ("SRC-002","SRC-002.P01","WP-01","Тип занятости","visibility","always","field is visible","-","DOCX table 11 row 3; PDF p.61","high","-","ATOM-001"),
        ("SRC-002","SRC-002.P02","WP-01","Тип занятости","requiredness","always","field is required","-","DOCX table 11 row 3; PDF p.61","high","-","ATOM-002"),
        ("SRC-002","SRC-002.P03","WP-01","Тип занятости","editability","always","field is editable","-","DOCX table 11 row 3; PDF p.61","high","-","ATOM-003"),
        ("SRC-002","SRC-002.P04","WP-01","Тип занятости","dictionary-source","always","value source is dictionary `Типы занятости`","-","DOCX table 11 row 3; support DICT-001","high","-","ATOM-004"),
        ("SRC-003","SRC-003.P01","WP-01","Среднемесячный доход после вычета налогов","conditional-visibility","`Тип занятости` empty","field is not displayed before employment type is filled","GSR 123","PDF p.61","high","-","ATOM-005"),
        ("SRC-003","SRC-003.P02","WP-01","Среднемесячный доход после вычета налогов","conditional-visibility","`Тип занятости` filled","field is displayed","GSR 123","PDF p.61","high","-","ATOM-006"),
        ("SRC-003","SRC-003.P03","WP-01","Среднемесячный доход после вычета налогов","requiredness","`Тип занятости` filled","field is required","GSR 123","DOCX table 11 row 4; PDF p.61","high","-","ATOM-007"),
        ("SRC-003","SRC-003.P04","WP-01","Среднемесячный доход после вычета налогов","editability","field displayed","field is editable","GSR 123","DOCX table 11 row 4; PDF p.61","high","-","ATOM-008"),
        ("SRC-003","SRC-003.P05","WP-01","Среднемесячный доход после вычета налогов","numeric-format","field displayed","only numeric symbols are allowed","GSR 124","PDF p.61","medium","GAP-005","ATOM-009; ATOM-011"),
        ("SRC-003","SRC-003.P06","WP-01","Среднемесячный доход после вычета налогов","min-boundary","field displayed","amount is not less than 2000 rubles","GSR 124","PDF p.61","medium","GAP-005","ATOM-010; ATOM-011"),
        ("SRC-010","SRC-010.P01","WP-02","Блок Дополнительный доход","action-created-optional-block","before add action","income fields appear after pressing add action, so no created block exists before action","-","DOCX table 11 row 11; row 12 visibility","high","-","ATOM-012"),
        ("SRC-020","SRC-020.P01","WP-02","Добавить дополнительный доход","action-created-optional-block","button pressed","system displays fields in block `Дополнительный доход`","GSR 146","PDF p.65","high","-","ATOM-013"),
        ("SRC-020","SRC-020.P02","WP-02","Дополнительный доход","repeatable-block-lifecycle","created block exists","created additional income can be deleted by trash icon","GSR 147","PDF p.65","high","-","ATOM-014"),
        ("SRC-011","SRC-011.P01","WP-02","Тип дохода","requiredness","after add income action","field is required","-","DOCX table 11 row 12","high","-","ATOM-015"),
        ("SRC-011","SRC-011.P02","WP-02","Тип дохода","dictionary-source","after add income action","value source is dictionary `Типы дохода`","-","DOCX table 11 row 12; DICT-004","high","-","ATOM-016"),
        ("SRC-011","SRC-011.P03","WP-02","Тип дохода","duplicate-prevention-invariant","for values `Пенсия` and `Аренда`","each of these income types can be added only once","-","DOCX table 11 row 12","medium","GAP-002","ATOM-017"),
        ("SRC-011","SRC-011.P04","WP-02","Тип дохода","duplicate-prevention-feedback","duplicate attempt","exact UI prevention mechanism is not defined","-","DOCX table 11 row 12","unclear","GAP-002","-"),
        ("SRC-012","SRC-012.P01","WP-02","Среднемесячный доход после вычета налогов дополнительного дохода","requiredness","after add income action","field is required","-","DOCX table 11 row 13","high","-","ATOM-018"),
        ("SRC-012","SRC-012.P02","WP-02","Среднемесячный доход после вычета налогов дополнительного дохода","numeric-format","after add income action","only numeric symbols are allowed","GSR 135","PDF p.62","medium","GAP-006","ATOM-019; ATOM-020"),
        ("SRC-012","SRC-012.P03","WP-02","Среднемесячный доход после вычета налогов дополнительного дохода","invalid-feedback","non-numeric input","exact observable feedback is not defined","GSR 135","PDF p.62","unclear","GAP-006","-"),
        ("SRC-014","SRC-014.P01","WP-03","Клиент добросовестный","default-value","section opened","default value is `Нет`","GSR 136","PDF p.62","high","-","ATOM-021"),
        ("SRC-015","SRC-015.P01","WP-03","Визуальная информация","default-value","section opened","default value is `Нет`","GSR 137","PDF p.62","high","-","ATOM-022"),
        ("SRC-015","SRC-015.P02","WP-03","Визуальная информация","conditional-visibility","value is `Да`","list of visual assessment parameters is automatically displayed","GSR 138","PDF p.62","high","-","ATOM-023"),
        ("SRC-016","SRC-016.P01","WP-03","Параметры визуальной оценки","conditional-visibility","`Визуальная информация` = `Да`","field is displayed","-","DOCX table 11 row 17; PDF pp.62-63","high","-","ATOM-024"),
        ("SRC-016","SRC-016.P02","WP-03","Параметры визуальной оценки","checkbox-list","list displayed","each listed value has a checkbox","GSR 139","PDF p.63","high","-","ATOM-025"),
        ("SRC-016","SRC-016.P03","WP-03","Параметры визуальной оценки","requiredness","`Визуальная информация` = `Да`","at least one value must be selected","GSR 140","PDF p.63","high","-","ATOM-026"),
        ("SRC-016","SRC-016.P04","WP-03","Параметры визуальной оценки","checkbox-list","list displayed","one selected checkbox satisfies at-least-one rule","GSR 140","PDF p.63","high","-","ATOM-027"),
        ("SRC-016","SRC-016.P05","WP-03","Параметры визуальной оценки","checkbox-list","list displayed","multiple values can be selected","GSR 138","PDF p.62","high","-","ATOM-028"),
        ("SRC-016","SRC-016.P06","WP-03","Параметры визуальной оценки","editability","selection exists","selection can be cleared; after clearing all selected values the at-least-one rule is not satisfied","GSR 140","DOCX table 11 row 17; PDF p.63","medium","-","ATOM-029"),
        ("SRC-016","SRC-016.P07","WP-03","Параметры визуальной оценки","dictionary-source","list displayed","value source is `DICT-005`","GSR 139","support DICT-005","high","-","ATOM-025"),
        ("SRC-018","SRC-018.P01","WP-04","Следующий шаг","red-highlight","required field empty","system highlights empty required field red","GSR 142","PDF p.63","high","-","ATOM-030"),
        ("SRC-018","SRC-018.P02","WP-04","Следующий шаг","action-navigation","all required fields filled","system opens section `Анкета клиента`","GSR 143","PDF p.65","high","-","ATOM-031"),
        ("SRC-018","SRC-018.P04","WP-04","Следующий шаг","print-form-output","valid section data","print form `Заявление-анкета` is formed","GSR 143","PDF p.65","high","GAP-007","ATOM-031"),
        ("SRC-018","SRC-018.P03","WP-04","Следующий шаг","integration-internal","return from `Выбор решения` with critical fields edited","SPR/anti-fraud repeated checks need observable artifact","GSR 142","PDF pp.63-64","unclear","GAP-003","-"),
        ("SRC-019","SRC-019.P01","WP-04","Добавить работу по совместительству","action-created-optional-block","button pressed","system displays fields in block `Сведения о занятости` / `Работа по совместительству`","GSR 144","PDF p.65","high","-","ATOM-032"),
        ("SRC-019","SRC-019.P02","WP-04","Работа по совместительству","repeatable-block-lifecycle","created block exists","created part-time work can be deleted by trash icon","GSR 145","PDF p.65","high","-","ATOM-033"),
        ("SRC-021","SRC-021.P01","WP-04","Назад","action-confirmation","unsaved data exists","system displays confirmation with `Да` and `Нет`","GSR 148","PDF p.65","high","-","ATOM-034"),
        ("SRC-021","SRC-021.P02","WP-04","Назад","save-branch","choose `Да`","current section data is saved, then `Основная информация` opens","GSR 148","PDF p.65","high","-","ATOM-035"),
        ("SRC-021","SRC-021.P03","WP-04","Назад","discard-branch","choose `Нет`","system opens `Основная информация` without saving current changes","GSR 148","PDF p.65","high","-","ATOM-036"),
        ("SRC-004","SRC-004.P01","WP-01","DaData employer/address context","integration-prefill","organization selected through DaData","exact trigger and non-UI SPR contract artifact not defined","GSR 141","PDF p.63","unclear","GAP-001","-"),
        ("SRC-004","SRC-004.P02","WP-01","Наименование организации, ИНН","conditional-visibility","`Тип занятости` is not `Пенсионер (не работает)`","field is visible","GSR 125","PDF p.61","unclear","GAP-001","-"),
        ("SRC-004","SRC-004.P04","WP-01","Наименование организации, ИНН","requiredness","`Тип занятости` is not `Пенсионер (не работает)`","field is required","GSR 125","PDF p.61","unclear","GAP-001","-"),
        ("SRC-004","SRC-004.P05","WP-01","Наименование организации, ИНН","editability","`Тип занятости` is not `Пенсионер (не работает)`","field is editable","GSR 125","PDF p.61","unclear","GAP-001","-"),
        ("SRC-004","SRC-004.P03","WP-01","Наименование организации, ИНН","integration-prefill","organization selected","DaData exact trigger and dropdown behavior are not defined","GSR 126","PDF p.61","unclear","GAP-001","-"),
        ("SRC-005","SRC-005.P01","WP-01","Фактический адрес работы","conditional-visibility","`Тип занятости` is not `Пенсионер (не работает)`","field is visible","GSR 127","PDF p.61","unclear","GAP-001","-"),
        ("SRC-005","SRC-005.P03","WP-01","Фактический адрес работы","editability","`Тип занятости` is not `Пенсионер (не работает)`","field is editable","GSR 127","PDF p.61","unclear","GAP-001","-"),
        ("SRC-005","SRC-005.P02","WP-01","Фактический адрес работы","integration-prefill","organization selected","value is auto-filled from selected organization context; exact observable setup is not defined","GSR 128","PDF p.61","unclear","GAP-001","-"),
        ("SRC-022","SRC-022.P01","WP-05","CDI INN verification failure","integration-message-setup","CDI failure condition","deterministic trigger/test data not defined","-","PDF pp.65-66","unclear","GAP-004","-"),
    ]
    norm_table = "| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    norm_table += "\n".join("| " + " | ".join(f"`{x}`" if i in [0,1,2,8,9,10] and x != "-" else x for i, x in enumerate(row)) + " |" for row in norm_rows)
    manifest_with_preamble(
        "source-table-normalization",
        TD / "source-table-normalization.md",
        "",
        [(2, "Source Row Completeness Matrix", completeness), (2, "Source Table Normalization", norm_table)],
    )

    dict_body = f"""
| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DICT-001` | `Типы занятости` | `support/Наполнение справочников_v1.xlsx` | `sheet: Типы занятости; rows 4-9` | `extracted` | {DICT_001} | `-` | `SRC-002.P04` | `-` | Copied from `work/test-design/ui-employment/dictionary-inventory.md`; active means `Архивный = Нет`. |
| `DICT-004` | `Типы дохода` | `support/Наполнение справочников_v1.xlsx` | `sheet: Виды дохода; rows 4-5` | `extracted` | {DICT_004} | `-` | `SRC-011.P02; SRC-011.P03` | `GAP-002` | Values are source-backed; exact duplicate prevention mechanism remains gap. |
| `DICT-005` | `Параметры визуальной оценки` | `support/Наполнение справочников_v1.xlsx` | `sheet: Параметры визуальной оценки; rows 4-15` | `extracted` | {DICT_005} | `-` | `SRC-016.P07` | `-` | Preserve workbook spelling exactly, including typos. |
"""
    manifest("dictionary-inventory", TD / "dictionary-inventory.md", "Dictionary Inventory", dict_body)

    # Design support tables are intentionally dense but canonical-column compatible.
    tdd_rows = []
    tc_by_atom = {
        "ATOM-001":"TC-UI-EMP-V9-001","ATOM-002":"TC-UI-EMP-V9-002","ATOM-003":"TC-UI-EMP-V9-004","ATOM-004":"TC-UI-EMP-V9-003",
        "ATOM-005":"TC-UI-EMP-V9-005","ATOM-006":"TC-UI-EMP-V9-006","ATOM-007":"TC-UI-EMP-V9-007","ATOM-008":"TC-UI-EMP-V9-008","ATOM-009":"TC-UI-EMP-V9-009","ATOM-010":"TC-UI-EMP-V9-010",
        "ATOM-012":"TC-UI-EMP-V9-011","ATOM-013":"TC-UI-EMP-V9-012","ATOM-014":"TC-UI-EMP-V9-013","ATOM-015":"TC-UI-EMP-V9-014","ATOM-016":"TC-UI-EMP-V9-015","ATOM-018":"TC-UI-EMP-V9-014","ATOM-019":"TC-UI-EMP-V9-016",
        "ATOM-021":"TC-UI-EMP-V9-017","ATOM-022":"TC-UI-EMP-V9-017","ATOM-023":"TC-UI-EMP-V9-018","ATOM-024":"TC-UI-EMP-V9-018","ATOM-025":"TC-UI-EMP-V9-019","ATOM-026":"TC-UI-EMP-V9-020","ATOM-027":"TC-UI-EMP-V9-021","ATOM-028":"TC-UI-EMP-V9-022","ATOM-029":"TC-UI-EMP-V9-023",
        "ATOM-030":"TC-UI-EMP-V9-002; TC-UI-EMP-V9-007; TC-UI-EMP-V9-014; TC-UI-EMP-V9-020; TC-UI-EMP-V9-023","ATOM-031":"TC-UI-EMP-V9-024","ATOM-032":"TC-UI-EMP-V9-025","ATOM-033":"TC-UI-EMP-V9-026","ATOM-034":"TC-UI-EMP-V9-027","ATOM-035":"TC-UI-EMP-V9-028","ATOM-036":"TC-UI-EMP-V9-029"
    }
    for idx, row in enumerate(norm_rows, start=1):
        src, prop, pkg, field, ptype, cond, exp, req, sref, conf, gap, atoms = row
        atom = atoms.split(";")[0].strip() if atoms != "-" else "-"
        if conf == "unclear" or (gap in ["GAP-001","GAP-002","GAP-003","GAP-004","GAP-005","GAP-006"] and atom == "-"):
            decision = "gap_unclear"
            planned = gap
            exec_ = "no"
            observable = "none" if gap in ["GAP-001","GAP-003","GAP-004"] else "source-backed invariant exists; exact feedback is unclear"
            testable = "-" if atom == "-" else "covered invariant or positive classes split in linked atoms"
            blocked = "exact observable mechanism/setup"
            admiss = f"{gap} documents unresolved source mechanism"
        elif ptype in ["dictionary-source","checkbox-list","numeric-format","min-boundary","conditional-visibility","requiredness","editability","default-value","red-highlight","action-navigation","action-created-optional-block","repeatable-block-lifecycle","action-confirmation","save-branch","discard-branch"]:
            decision = "standalone_tc"
            planned = tc_by_atom.get(atom, "-")
            exec_ = "yes"
            observable = "UI state/value/highlight/navigation is observable"
            testable = exp
            blocked = "-" if gap == "-" else gap
            admiss = "not-a-gap" if gap == "-" else f"testable part split from {gap}"
        else:
            decision = "metadata_only"
            planned = "-"
            exec_ = "no"
            observable = "none"
            testable = "-"
            blocked = "-"
            admiss = "not-a-gap"
        tdd_rows.append((f"TDD-{idx:03d}", pkg, prop, atom if atom != "-" else "-", ptype, decision, "Решение принято после source normalization; visible behavior split from gaps.", planned, sref if gap == "-" else f"{sref}; {gap}", exec_, observable, testable, blocked, admiss, "medium" if gap != "-" else "none"))
    tdd_body = "| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    tdd_body += "\n".join("| " + " | ".join(f"`{x}`" if i in [0,1,2,3,5,7,9,14] and x != "-" else x for i, x in enumerate(row)) + " |" for row in tdd_rows)
    manifest("test-design-decision-table", TD / "test-design-decision-table.md", "Test Design Decision Table", tdd_body)

    obligations = [
        ("OBL-001","WP-01","SRC-003.P05","ATOM-009","numeric-format","valid-digits","Основной доход принимает значение из цифр.","GSR 124; SRC-003","TC-UI-EMP-V9-009","covered","-"),
        ("OBL-002","WP-01","SRC-003.P05","ATOM-011","numeric-format","reject-letters","Класс букв для основного дохода требует observable feedback.","GSR 124; SRC-003","GAP-005","gap","Exact UI reaction is not stated."),
        ("OBL-003","WP-01","SRC-003.P05","ATOM-011","numeric-format","reject-spaces","Класс пробелов для основного дохода требует observable feedback.","GSR 124; SRC-003","GAP-005","gap","Exact UI reaction is not stated."),
        ("OBL-004","WP-01","SRC-003.P05","ATOM-011","numeric-format","reject-special-chars","Класс спецсимволов для основного дохода требует observable feedback.","GSR 124; SRC-003","GAP-005","gap","Exact UI reaction is not stated."),
        ("OBL-005","WP-01","SRC-003.P05","ATOM-011","numeric-format","reject-decimal-separator","Десятичный разделитель для основного дохода требует observable feedback.","GSR 124; SRC-003","GAP-005","gap","Exact UI reaction is not stated."),
        ("OBL-006","WP-01","SRC-003.P05","ATOM-011","numeric-format","reject-sign","Знак плюс/минус для основного дохода требует observable feedback.","GSR 124; SRC-003","GAP-005","gap","Exact UI reaction is not stated."),
        ("OBL-007","WP-01","SRC-003.P06","ATOM-010","min-boundary","min-accepted","Основной доход принимает минимальное значение `2000`.","GSR 124; SRC-003","TC-UI-EMP-V9-010","covered","-"),
        ("OBL-008","WP-01","SRC-003.P06","ATOM-011","min-boundary","below-min-rejected","Значение ниже `2000` требует observable feedback.","GSR 124; SRC-003","GAP-005","gap","Exact UI reaction is not stated."),
        ("OBL-009","WP-02","SRC-020.P01","ATOM-013","action-created-optional-block","action-reveals-block","Действие добавления отображает блок дополнительного дохода.","GSR 146; SRC-020","TC-UI-EMP-V9-012","covered","-"),
        ("OBL-010","WP-02","SRC-010.P01","ATOM-012","action-created-optional-block","block-absent-before-action","Созданный блок отсутствует до действия добавления.","SRC-010; SRC-011 visibility","TC-UI-EMP-V9-011","covered","-"),
        ("OBL-011","WP-02","SRC-011.P01","ATOM-015","action-created-optional-block","created-block-required-fields-enforced","Обязательные поля созданного блока подсвечиваются при переходе.","SRC-011; SRC-012; GSR 142","TC-UI-EMP-V9-014","covered","-"),
        ("OBL-012","WP-02","SRC-020.P02","ATOM-014","repeatable-block-lifecycle","delete-last-removes-block","Удаление созданного блока убирает его с формы.","GSR 147; SRC-020","TC-UI-EMP-V9-013","covered","-"),
        ("OBL-013","WP-02","SRC-011.P03","ATOM-017","duplicate-prevention","duplicate-feedback","Точный механизм запрета дубля `Пенсия`/`Аренда` не задан.","SRC-011","GAP-002","gap","Invariant retained; no executable mechanism asserted."),
        ("OBL-014","WP-02","SRC-012.P02","ATOM-019","numeric-format","valid-digits","Сумма дополнительного дохода принимает значение из цифр.","GSR 135; SRC-012","TC-UI-EMP-V9-016","covered","-"),
        ("OBL-015","WP-02","SRC-012.P02","ATOM-020","numeric-format","reject-letters","Класс букв для дополнительного дохода требует observable feedback.","GSR 135; SRC-012","GAP-006","gap","Exact UI reaction is not stated."),
        ("OBL-016","WP-02","SRC-012.P02","ATOM-020","numeric-format","reject-spaces","Класс пробелов для дополнительного дохода требует observable feedback.","GSR 135; SRC-012","GAP-006","gap","Exact UI reaction is not stated."),
        ("OBL-017","WP-02","SRC-012.P02","ATOM-020","numeric-format","reject-special-chars","Класс спецсимволов для дополнительного дохода требует observable feedback.","GSR 135; SRC-012","GAP-006","gap","Exact UI reaction is not stated."),
        ("OBL-018","WP-02","SRC-012.P02","ATOM-020","numeric-format","reject-decimal-separator","Десятичный разделитель для дополнительного дохода требует observable feedback.","GSR 135; SRC-012","GAP-006","gap","Exact UI reaction is not stated."),
        ("OBL-019","WP-02","SRC-012.P02","ATOM-020","numeric-format","reject-sign","Знак плюс/минус для дополнительного дохода требует observable feedback.","GSR 135; SRC-012","GAP-006","gap","Exact UI reaction is not stated."),
        ("OBL-020","WP-03","SRC-016.P02","ATOM-025","checkbox-list","dictionary-values-shown","Список содержит все и только активные значения `DICT-005`.","GSR 139; DICT-005","TC-UI-EMP-V9-019","covered","-"),
        ("OBL-021","WP-03","SRC-016.P03","ATOM-026","checkbox-list","no-selection-rejected","Отсутствие выбора подсвечивается при переходе.","GSR 140; GSR 142","TC-UI-EMP-V9-020","covered","-"),
        ("OBL-022","WP-03","SRC-016.P04","ATOM-027","checkbox-list","single-selection-accepted","Один чекбокс может быть выбран.","GSR 139; GSR 140","TC-UI-EMP-V9-021","covered","-"),
        ("OBL-023","WP-03","SRC-016.P05","ATOM-028","checkbox-list","multiple-selection-accepted","Несколько чекбоксов можно выбрать одновременно.","GSR 138","TC-UI-EMP-V9-022","covered","-"),
        ("OBL-024","WP-03","SRC-016.P06","ATOM-029","checkbox-list","selection-can-be-cleared","Выбранный чекбокс можно снять, после чего обязательность снова нарушена.","GSR 139; GSR 140","TC-UI-EMP-V9-023","covered","-"),
        ("OBL-025","WP-04","SRC-018.P02","ATOM-031","print-form-output","print-form-generated","Печатная форма сформирована и отображается в разделе `Анкета клиента`.","GSR 143","TC-UI-EMP-V9-024","covered","Content mapping is out of v9 scope."),
        ("OBL-026","WP-04","SRC-018.P02","ATOM-031","print-form-output","print-form-content-mapping","Состав данных печатной формы не задан в v9 rows.","GSR 143","GAP-007","gap","No source-backed content mapping in selected rows."),
        ("OBL-027","WP-04","SRC-018.P01","ATOM-030","red-highlight","highlight-triggered","Пустое обязательное поле подсвечивается красным.","GSR 142; SRC-018","TC-UI-EMP-V9-002","covered","Also exercised by other requiredness TCs."),
        ("OBL-028","WP-04","SRC-018.P02","ATOM-031","action-navigation","navigation-target-opened","Раздел `Анкета клиента` открыт после заполнения обязательных полей.","GSR 143; SRC-018","TC-UI-EMP-V9-024","covered","-"),
        ("OBL-029","WP-04","SRC-021.P01","ATOM-034","action-confirmation","confirmation-message-shown","При несохраненных данных показывается подтверждение `Да`/`Нет`.","GSR 148; SRC-021","TC-UI-EMP-V9-027","covered","-"),
        ("OBL-030","WP-04","SRC-021.P01","ATOM-035","action-confirmation","confirmation-accept-continues","Ветка `Да` сохраняет данные и открывает `Основная информация`.","GSR 148; SRC-021","TC-UI-EMP-V9-028","covered","-"),
        ("OBL-031","WP-04","SRC-021.P01","ATOM-036","action-confirmation","confirmation-cancel-stays","Ветка `Нет` не сохраняет данные и открывает `Основная информация`.","GSR 148; SRC-021","TC-UI-EMP-V9-029","covered","Source names this branch `Нет`, not cancel/stay; obligation class reused for no/discard branch."),
    ]
    obligation_supported_properties = {"SRC-003.P05", "SRC-012.P02", "SRC-018.P01", "SRC-018.P02", "SRC-021.P01"}
    obligations = [row for row in obligations if row[2] in obligation_supported_properties]
    obl_body = "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    obl_body += "\n".join("| " + " | ".join(f"`{x}`" if i in [0,1,2,3,4,5,8,9] and x != "-" else x for i, x in enumerate(row)) + " |" for row in obligations)
    manifest("coverage-obligation-table", TD / "coverage-obligation-table.md", "Coverage Obligation Table", obl_body)

    atoms = [
        ("ATOM-001","WP-01","SRC-002.P01","-","Поле `Тип занятости` отображается всегда.","covered","TC-UI-EMP-V9-001","medium"),
        ("ATOM-002","WP-01","SRC-002.P02","-","Поле `Тип занятости` обязательно к заполнению.","covered","TC-UI-EMP-V9-002","high"),
        ("ATOM-003","WP-01","SRC-002.P03","-","Поле `Тип занятости` редактируемо.","covered","TC-UI-EMP-V9-004","medium"),
        ("ATOM-004","WP-01","SRC-002.P04","DICT-001","Поле `Тип занятости` использует справочник `DICT-001`.","covered","TC-UI-EMP-V9-003","high"),
        ("ATOM-005","WP-01","SRC-003.P01","GSR 123","Основной доход не отображается до заполнения `Тип занятости`.","covered","TC-UI-EMP-V9-005","high"),
        ("ATOM-006","WP-01","SRC-003.P02","GSR 123","Основной доход отображается после заполнения `Тип занятости`.","covered","TC-UI-EMP-V9-006","high"),
        ("ATOM-007","WP-01","SRC-003.P03","GSR 123","Основной доход обязателен к заполнению.","covered","TC-UI-EMP-V9-007","high"),
        ("ATOM-008","WP-01","SRC-003.P04","GSR 123","Основной доход редактируем.","covered","TC-UI-EMP-V9-008","medium"),
        ("ATOM-009","WP-01","SRC-003.P05","GSR 124","Основной доход принимает числовые символы.","covered","TC-UI-EMP-V9-009","high"),
        ("ATOM-010","WP-01","SRC-003.P06","GSR 124","Минимальное значение основного дохода `2000`.","covered","TC-UI-EMP-V9-010","high"),
        ("ATOM-011","WP-01","SRC-003.P05; SRC-003.P06","GSR 124","Invalid classes and below-min feedback for main income need exact observable mechanism.","gap","GAP-005","high"),
        ("ATOM-012","WP-02","SRC-010.P01","-","Блок дополнительного дохода отсутствует до действия добавления.","covered","TC-UI-EMP-V9-011","medium"),
        ("ATOM-013","WP-02","SRC-020.P01","GSR 146","Действие добавления отображает блок дополнительного дохода.","covered","TC-UI-EMP-V9-012","high"),
        ("ATOM-014","WP-02","SRC-020.P02","GSR 147","Созданный дополнительный доход можно удалить через `Корзина`.","covered","TC-UI-EMP-V9-013","high"),
        ("ATOM-015","WP-02","SRC-011.P01","-","Тип дохода обязателен после создания блока.","covered","TC-UI-EMP-V9-014","high"),
        ("ATOM-016","WP-02","SRC-011.P02","DICT-004","Тип дохода использует справочник `DICT-004`.","covered","TC-UI-EMP-V9-015","high"),
        ("ATOM-017","WP-02","SRC-011.P03","-","`Пенсия` и `Аренда` могут быть добавлены только один раз; точный механизм не определен.","gap","GAP-002","high"),
        ("ATOM-018","WP-02","SRC-012.P01","-","Сумма дополнительного дохода обязательна после создания блока.","covered","TC-UI-EMP-V9-014","high"),
        ("ATOM-019","WP-02","SRC-012.P02","GSR 135","Сумма дополнительного дохода принимает числовые символы.","covered","TC-UI-EMP-V9-016","high"),
        ("ATOM-020","WP-02","SRC-012.P02","GSR 135","Invalid numeric classes for additional income need exact observable mechanism.","gap","GAP-006","high"),
        ("ATOM-021","WP-03","SRC-014.P01","GSR 136","`Клиент добросовестный` по умолчанию `Нет`.","covered","TC-UI-EMP-V9-017","medium"),
        ("ATOM-022","WP-03","SRC-015.P01","GSR 137","`Визуальная информация` по умолчанию `Нет`.","covered","TC-UI-EMP-V9-017","medium"),
        ("ATOM-023","WP-03","SRC-015.P02","GSR 138","`Визуальная информация = Да` отображает параметры визуальной оценки.","covered","TC-UI-EMP-V9-018","high"),
        ("ATOM-024","WP-03","SRC-016.P01","-","Параметры визуальной оценки отображаются при `Визуальная информация = Да`.","covered","TC-UI-EMP-V9-018","high"),
        ("ATOM-025","WP-03","SRC-016.P02","GSR 139; DICT-005","По каждому значению `DICT-005` доступен чек-бокс.","covered","TC-UI-EMP-V9-019","high"),
        ("ATOM-026","WP-03","SRC-016.P03","GSR 140","Должно быть выбрано хотя бы одно значение параметров визуальной оценки.","covered","TC-UI-EMP-V9-020","high"),
        ("ATOM-027","WP-03","SRC-016.P04","GSR 139; GSR 140","Один выбранный параметр удовлетворяет обязательности.","covered","TC-UI-EMP-V9-021","high"),
        ("ATOM-028","WP-03","SRC-016.P05","GSR 138","Список поддерживает множественный выбор.","covered","TC-UI-EMP-V9-022","high"),
        ("ATOM-029","WP-03","SRC-016.P06","GSR 139; GSR 140","Выбор можно снять; без выбора обязательность снова нарушена.","covered","TC-UI-EMP-V9-023","high"),
        ("ATOM-030","WP-04","SRC-018.P01","GSR 142","`Следующий шаг` подсвечивает пустые обязательные поля красным.","covered","TC-UI-EMP-V9-002; TC-UI-EMP-V9-007; TC-UI-EMP-V9-014; TC-UI-EMP-V9-020; TC-UI-EMP-V9-023","high"),
        ("ATOM-031","WP-04","SRC-018.P02","GSR 143","При заполненных обязательных полях открывается `Анкета клиента` и формируется печатная форма.","covered","TC-UI-EMP-V9-024","high"),
        ("ATOM-032","WP-04","SRC-019.P01","GSR 144","`Добавить работу по совместительству` отображает блок совместительства.","covered","TC-UI-EMP-V9-025","high"),
        ("ATOM-033","WP-04","SRC-019.P02","GSR 145","Работу по совместительству можно удалить через `Корзина`.","covered","TC-UI-EMP-V9-026","high"),
        ("ATOM-034","WP-04","SRC-021.P01","GSR 148","`Назад` с несохраненными данными показывает подтверждение `Да`/`Нет`.","covered","TC-UI-EMP-V9-027","high"),
        ("ATOM-035","WP-04","SRC-021.P02","GSR 148","Ветка `Да` сохраняет данные и открывает `Основная информация`.","covered","TC-UI-EMP-V9-028","high"),
        ("ATOM-036","WP-04","SRC-021.P03","GSR 148","Ветка `Нет` не сохраняет данные и открывает `Основная информация`.","covered","TC-UI-EMP-V9-029","high"),
        ("ATOM-037","WP-04","SRC-018.P03","GSR 142","SPR/anti-fraud effects after return from `Выбор решения` need observable artifact.","gap","GAP-003","high"),
        ("ATOM-038","WP-05","SRC-022.P01","-","CDI message trigger/setup remains unresolved and out of v9 executable scope.","gap","GAP-004","medium"),
    ]
    ledger_body = "| atom_id | package_id | source_property_id | req_id | atomic_statement | coverage_status | covered_by_tc | gap_id | priority |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    ledger_lines = []
    for row in atoms:
        atom_id, pkg, prop, req, stmt, status, link, priority = row
        covered_by_tc = link if status == "covered" else "-"
        gap_id = link if status == "gap" else "-"
        out = (atom_id, pkg, prop, req, stmt, status, covered_by_tc, gap_id, priority)
        ledger_lines.append("| " + " | ".join(f"`{x}`" if i in [0,1,2,3,5,6,7,8] and x != "-" else x for i, x in enumerate(out)) + " |")
    ledger_body += "\n".join(ledger_lines)
    manifest("atomic-requirements-ledger", TD / "atomic-requirements-ledger.md", "Atomic Requirements Ledger", ledger_body)

    plan_rows = []
    for idx, tc in enumerate(TC_ROWS, start=1):
        tc_id, pkg, typ, priority, trace, title, *_ = tc
        atom_refs = "; ".join([x.strip("` ") for x in trace.split(";") if "ATOM-" in x])
        check_type = "negative" if typ == "Negative" else ("boundary" if "миним" in title.lower() else "positive")
        title_l = title.lower()
        if "подсвеч" in title_l or "пуст" in title_l:
            dimension = "expected-result"
        elif "dict-" in trace.lower() or "список" in title_l or "параметр" in title_l:
            dimension = "table-list"
        elif "доход" in title_l and ("принима" in title_l or "миним" in title_l or "заменить" in title_l):
            dimension = "numeric"
        elif "назад" in title_l and ("сохраняет" in title_l or "не сохраняет" in title_l):
            dimension = "persistence"
        elif "следующий шаг" in title_l or "открывает" in title_l:
            dimension = "scenario-use-case"
        elif "не отображается" in title_l or "отображается" in title_l:
            dimension = "conditional-visibility"
        else:
            dimension = "other"
        plan_rows.append((f"PD-{idx:03d}", pkg, dimension, trace.replace("`",""), atom_refs or "-", title, check_type, title, "see TC data", "see TC expected result", "FT/PDF/support dictionary", tc_id, "covered"))
    for gap_id, pkg, source, atoms_ref, text in [
        ("GAP-001","WP-01","GSR 126; GSR 128; GSR 141","ATOM-039","DaData exact trigger and non-UI SPR contract artifact remain unresolved."),
        ("GAP-002","WP-02","SRC-011","ATOM-017","Duplicate income exact prevention mechanism remains unresolved."),
        ("GAP-003","WP-04","GSR 142","ATOM-037","SPR/anti-fraud observable artifact remains unresolved."),
        ("GAP-004","WP-05","SRC-022..SRC-024","ATOM-038","CDI deterministic setup remains unresolved and out of v9 executable scope."),
        ("GAP-005","WP-01","GSR 124; SRC-003","ATOM-011","Main income invalid classes need source-backed observable feedback mechanism."),
        ("GAP-006","WP-02","GSR 135; SRC-012","ATOM-020","Additional income invalid classes need source-backed observable feedback mechanism."),
        ("GAP-007","WP-04","GSR 143","ATOM-031","Print-form content mapping is outside selected v9 source rows."),
    ]:
        gap_dimension = "integration" if gap_id in {"GAP-001", "GAP-003", "GAP-004"} else ("numeric" if gap_id in {"GAP-005", "GAP-006"} else "other")
        plan_rows.append((f"PD-G-{gap_id[-3:]}", pkg, gap_dimension, source, atoms_ref, text, "gap", "unresolved source mechanism", "n/a", text, gap_id, gap_id, "gap"))
    plan_body = "| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    plan_body += "\n".join("| " + " | ".join(f"`{x}`" if i in [0,1,6,11,12] and x != "-" else x for i, x in enumerate(row)) + " |" for row in plan_rows)
    manifest("package-test-design-plan", TD / "package-test-design-plan.md", "Package Test Design Plan", plan_body)

    app_rows = [
        ("conditional-visibility","yes","SRC-002; SRC-003; SRC-010; SRC-015; SRC-016","Conditional and always-visible fields/actions are in selected rows.","ATOM-001; ATOM-005; ATOM-006; ATOM-012; ATOM-023; ATOM-024","TC-UI-EMP-V9-001; TC-UI-EMP-V9-005; TC-UI-EMP-V9-006; TC-UI-EMP-V9-011; TC-UI-EMP-V9-018","-"),
        ("expected-result","yes","SRC-002; SRC-003; SRC-011; SRC-012; SRC-016; SRC-018","Required fields and red highlight action are source-backed.","ATOM-002; ATOM-007; ATOM-015; ATOM-018; ATOM-026; ATOM-030","TC-UI-EMP-V9-002; TC-UI-EMP-V9-007; TC-UI-EMP-V9-014; TC-UI-EMP-V9-020; TC-UI-EMP-V9-023","-"),
        ("other","yes","SRC-002; SRC-003; SRC-016","Editable fields have concrete old/new values or checkbox state changes.","ATOM-003; ATOM-008; ATOM-029","TC-UI-EMP-V9-004; TC-UI-EMP-V9-008; TC-UI-EMP-V9-023","-"),
        ("table-list","yes","DICT-001; DICT-004; DICT-005","Closed support dictionaries are used.","ATOM-004; ATOM-016; ATOM-025","TC-UI-EMP-V9-003; TC-UI-EMP-V9-015; TC-UI-EMP-V9-019","-"),
        ("numeric","yes","GSR 124; GSR 135","Valid/min classes covered; invalid feedback mechanism is unresolved.","ATOM-009; ATOM-010; ATOM-011; ATOM-019; ATOM-020","TC-UI-EMP-V9-009; TC-UI-EMP-V9-010; TC-UI-EMP-V9-016","GAP-005; GAP-006"),
        ("scenario-use-case","yes","SRC-010; SRC-019; SRC-020; GSR 144; GSR 145; GSR 146; GSR 147","Action-created blocks and trash deletion are visible UI scenarios.","ATOM-012; ATOM-013; ATOM-014; ATOM-032; ATOM-033","TC-UI-EMP-V9-011; TC-UI-EMP-V9-012; TC-UI-EMP-V9-013; TC-UI-EMP-V9-025; TC-UI-EMP-V9-026","GAP-002"),
        ("table-list","yes","SRC-016; DICT-005","Visual assessment parameters are a checkbox list with multiple selection.","ATOM-025; ATOM-026; ATOM-027; ATOM-028; ATOM-029","TC-UI-EMP-V9-019; TC-UI-EMP-V9-020; TC-UI-EMP-V9-021; TC-UI-EMP-V9-022; TC-UI-EMP-V9-023","-"),
        ("persistence","yes","SRC-018; SRC-021; GSR 143; GSR 148","Next and Back have visible transitions and save/discard branch outcomes.","ATOM-031; ATOM-034; ATOM-035; ATOM-036","TC-UI-EMP-V9-024; TC-UI-EMP-V9-027; TC-UI-EMP-V9-028; TC-UI-EMP-V9-029","GAP-003"),
        ("integration","unclear","GSR 141; GSR 142; CDI PDF-only context","Exact backend/DaData/CDI artifacts are not in v9 executable source boundary.","ATOM-037; ATOM-038","-","GAP-001; GAP-003; GAP-004"),
    ]
    app_body = "| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |\n| --- | --- | --- | --- | --- | --- | --- |\n"
    app_body += "\n".join("| " + " | ".join(f"`{x}`" if i in [1,6] and x != "-" else x for i, x in enumerate(row)) + " |" for row in app_rows)
    manifest("test-design-applicability-matrix", TD / "test-design-applicability-matrix.md", "Test-design Applicability Matrix", app_body)

    metrics_body = """
| dimension | design_method | applicable | source_ref | obligations_total | covered_by_tc | gap_or_unclear | coverage_unit | evidence_artifact | residual_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `visibility / availability` | `field-property` | `yes` | `SRC-002; SRC-003; SRC-010; SRC-015; SRC-016` | `6` | `6` | `0` | `atom` | `atomic-requirements-ledger.md` | `-` |
| `requiredness` | `negative transition` | `yes` | `SRC-002; SRC-003; SRC-011; SRC-012; SRC-016; SRC-018` | `6` | `6` | `0` | `atom` | `package-test-design-plan.md` | `-` |
| `dictionary/list composition` | `closed-set` | `yes` | `DICT-001; DICT-004; DICT-005` | `3` | `3` | `0` | `dictionary` | `dictionary-inventory.md` | `-` |
| `numeric` | `equivalence-boundary` | `yes` | `GSR 124; GSR 135` | `14` | `3` | `11` | `class` | `coverage-obligation-table.md` | `GAP-005; GAP-006` |
| `repeatable blocks` | `lifecycle/action-flow` | `yes` | `GSR 144; GSR 145; GSR 146; GSR 147` | `6` | `5` | `1` | `branch` | `coverage-obligation-table.md` | `GAP-002` |
| `checkbox-list` | `checkbox-list` | `yes` | `GSR 138; GSR 139; GSR 140; DICT-005` | `5` | `5` | `0` | `class` | `coverage-obligation-table.md` | `-` |
| `state transition / navigation` | `branch` | `yes` | `GSR 143; GSR 148` | `4` | `4` | `0` | `branch` | `package-test-design-plan.md` | `-` |
| `integration/API/internal effects` | `gap gate` | `unclear` | `GSR 141; GSR 142; SRC-022..SRC-024` | `3` | `0` | `3` | `gap` | `coverage-gaps.md` | `GAP-001; GAP-003; GAP-004` |
"""
    manifest("coverage-metrics", TD / "coverage-metrics.md", "Test-design Coverage Metrics", metrics_body)

    fixture_body = """
| fixture_id | purpose | fixture_data | source_ref | used_by | limitations |
| --- | --- | --- | --- | --- | --- |
| `FIX-EMP-V9-BASE-PENSIONER` | Валидный baseline для `Следующий шаг` без employer/address fixture. | `Тип занятости = Пенсионер (не работает)`; основной доход `2000`; `Должность = Пенсионер`; дополнительные блоки не созданы; `Клиент добросовестный = Нет`; `Визуальная информация = Нет`. | `SRC-002`; `SRC-003`; out-of-v9 row `SRC-007` only as fixture context; `SRC-014`; `SRC-015`; `SRC-018`. | `TC-UI-EMP-V9-024` and negative requiredness isolation. | Does not assert employer/address/position behavior as v9 coverage. |
| `FIX-EMP-V9-BACK-OLD-NEW` | Проверка branch `Назад` with observable save/discard. | Old main income `3000`; unsaved new main income `3500`; reopen employment section after Back branch. | `SRC-021`; `GSR 148`. | `TC-UI-EMP-V9-027`; `TC-UI-EMP-V9-028`; `TC-UI-EMP-V9-029`. | Requires UI path to reopen employment section from card. |
"""
    manifest("fixture-catalog", TD / "fixture-catalog.md", "Fixture Catalog", fixture_body)

    risk_body = """
| atom_id | coverage_dimension | impact | likelihood | risk_score | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | residual_risk_decision | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-010` | `numeric` | `4` | `4` | `16` | `high` | `money; business validation` | `GSR 124` | `High` | `TC-UI-EMP-V9-010` | `GAP-005` | `accepted-with-gap` | Минимум покрыт executable TC; invalid feedback remains explicit gap. |
| `ATOM-017` | `repeatable blocks` | `4` | `3` | `12` | `high` | `duplicate income; business validation` | `SRC-011` | `High` | `-` | `GAP-002` | `accepted-with-gap` | Invariant source-backed, exact mechanism unresolved. |
| `ATOM-026` | `checkbox-list` | `4` | `3` | `12` | `high` | `visual assessment requiredness` | `GSR 140` | `High` | `TC-UI-EMP-V9-020` | `-` | `none` | Missing required visual assessment can block progression. |
| `ATOM-031` | `state transition / navigation` | `4` | `3` | `12` | `high` | `section transition; generated form` | `GSR 143` | `High` | `TC-UI-EMP-V9-024` | `GAP-007` | `accepted-with-gap` | UI generation/section open covered; content mapping out of selected rows. |
| `ATOM-037` | `integration/API/internal effects` | `5` | `2` | `10` | `high` | `SPR; anti-fraud; external checks` | `GSR 142` | `High` | `-` | `GAP-003` | `accepted-with-gap` | Hidden effects need observable artifact. |
"""
    manifest("risk-priority-map", TD / "risk-priority-map.md", "Risk / Priority Map", risk_body)

    work_pkg_body = """
| package_id | focus | ledger_gate | design_plan_gate | tc_gate | atoms | covered | gap | unclear | TC count | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | Employment type and main income | `pass` | `pass` | `pass-with-gaps` | `11` | `10` | `1` | `0` | `10` | `ready-for-review` |
| `WP-02` | Additional income block | `pass` | `pass` | `pass-with-gaps` | `9` | `7` | `2` | `0` | `6` | `ready-for-review` |
| `WP-03` | Visual assessment | `pass` | `pass` | `pass` | `9` | `9` | `0` | `0` | `7` | `ready-for-review` |
| `WP-04` | Section actions | `pass` | `pass` | `pass-with-gaps` | `8` | `7` | `1` | `0` | `6` | `ready-for-review` |
| `WP-05` | CDI residual context | `pass` | `pass` | `not-executable-v9` | `1` | `0` | `1` | `0` | `0` | `residual-gap-only` |
"""
    manifest("internal-work-package-coverage", TD / "internal-work-package-coverage.md", "Internal Work Package Coverage", work_pkg_body)

    gaps_body = """
| gap_id | source_ref | related_atoms | gap_type | description | impact | coverage_impact | temporary_handling | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GAP-001` | `GSR 126; GSR 128; GSR 141; SRC-004; SRC-005; SRC-017` | `-` | `integration` | DaData lookup trigger, exact dropdown/no-result behavior and observable non-UI SPR contract artifact are not defined. | `non-blocking` | `partial` | Do not assert backend/SPR contract effects; employer/address rows may be fixture context only. | `open` |
| `GAP-002` | `SRC-011; DICT-004` | `ATOM-017` | `missing-rule` | `Пенсия` and `Аренда` are one-time income types, but source does not define exact UI prevention mechanism. | `non-blocking` | `design-constraint-on-covered-atom` | Keep invariant visible; do not create executable TC for exact feedback/control state. | `open` |
| `GAP-003` | `GSR 142; SRC-018` | `ATOM-037` | `cross-ft-dependency` | Return from status `Выбор решения`, SPR re-call and repeated anti-fraud/external checks have no approved observable artifact/setup in v9 scope. | `non-blocking` | `partial` | Cover only UI validation/navigation; hidden effects remain gap. | `open` |
| `GAP-004` | `SRC-022; SRC-023; SRC-024` | `ATOM-038` | `missing-constraint` | CDI message text/button behavior exists in PDF, but deterministic trigger/test data is not defined; v9 excludes executable CDI rows. | `non-blocking` | `partial` | Preserve as residual context; no executable CDI TC in v9. | `open` |
| `GAP-005` | `GSR 124; SRC-003` | `ATOM-011` | `observable-oracle` | Main income invalid classes (`letters`, `spaces`, `special chars`, decimal separator, sign, below `2000`) lack exact observable feedback mechanism. | `non-blocking` | `class-level-gap` | Positive/min classes covered; invalid mechanism not asserted. | `open` |
| `GAP-006` | `GSR 135; SRC-012` | `ATOM-020` | `observable-oracle` | Additional income invalid numeric classes lack exact observable feedback mechanism. | `non-blocking` | `class-level-gap` | Positive numeric class covered; invalid mechanism not asserted. | `open` |
| `GAP-007` | `GSR 143; SRC-018` | `ATOM-031` | `content-mapping` | Print form is generated/opened in `Анкета клиента`, but selected v9 rows do not define field-to-form content mapping. | `non-blocking` | `partial` | Cover UI-visible generation/section open only. | `open` |
"""
    manifest("coverage-gaps", TD / "coverage-gaps.md", "Coverage Gaps", gaps_body)

    review_body = """
| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- | --- |
| `decision-table-classification` | `pass` | `info` | `all` | Each `source_property_id` in `test-design-decision-table.md` has one decision. | - | `no` |
| `ledger-plan-alignment` | `pass` | `info` | `all` | `atomic-requirements-ledger.md` atoms map to `package-test-design-plan.md` TC/gap rows. | - | `no` |
| `coverage-class-completeness` | `pass` | `info` | `all` | Numeric, action-created block, repeatable block and checkbox-list classes are in `coverage-obligation-table.md`; unresolved classes link to `GAP-*`. | - | `no` |
| `coverage-metrics-completeness` | `pass` | `info` | `all` | `coverage-metrics.md` counts each applicable dimension. | - | `no` |
| `fixture-specificity` | `pass` | `info` | `all` | `fixture-catalog.md` defines valid baseline and Back branch old/new values. | - | `no` |
| `risk-model-completeness` | `pass` | `info` | `all` | `risk-priority-map.md` includes high-risk numeric, duplicate, checkbox, navigation and integration atoms. | - | `no` |
| `numeric-length-boundaries` | `pass` | `info` | `WP-01; WP-02` | Valid/min numeric classes are executable; invalid feedback classes use `GAP-005`/`GAP-006`. | - | `no` |
| `unsupported-ui-mechanism` | `pass` | `info` | `all` | No TC asserts filtering, disabled state, exact error text or auto-clear for numeric/duplicate gaps. | - | `no` |
| `mask-format-coverage` | `pass` | `info` | `all` | V9 selected rows contain no mask/default-mask source property; numeric formatting is handled through numeric obligations and gaps. | - | `no` |
| `dictionary-closed-set` | `pass` | `info` | `WP-01; WP-02; WP-03` | TC dictionary checks say all and only active `DICT-*` values; traceability includes used `DICT-*`. | - | `no` |
| `conditional-branches` | `pass` | `info` | `all` | Employment type dependency, visual info dependency and Back `Да`/`Нет` branches have distinct oracles/gaps. | - | `no` |
| `negative-fixture-isolation` | `pass` | `info` | `all` | Negative transition TCs specify other required fields as filled or use a fixture row. | - | `no` |
| `applicability-linked-tc-semantics` | `pass` | `info` | `all` | Applicability matrix links match actual TC dimensions. | - | `no` |
| `gap-specificity` | `pass` | `info` | `all` | `coverage-gaps.md` names exact missing mechanism/setup/content mapping. | - | `no` |
| `gap-admissibility` | `pass` | `info` | `all` | Visible UI behavior is covered; only exact mechanism/backend/setup/content mapping remains gap. | - | `no` |
| `internal-observability` | `pass` | `info` | `WP-04; WP-05` | SPR/anti-fraud/CDI hidden effects are not marked covered. | - | `no` |
| `metadata-only-exclusion` | `pass` | `info` | `all` | No value-type-only row creates a pseudo-TC. | - | `no` |
| `tc-mapping-atomicity` | `pass` | `info` | `all` | Each executable plan row maps to one TC except deliberate requiredness trigger reuse of `GSR 142`. | - | `no` |
| `ready-for-tc-writing` | `pass` | `info` | `all` | No blocking design review rows remain. | - | `no` |
"""
    manifest("test-design-review", TD / "test-design-review.md", "Test Design Review", review_body)

    gate_items = [
        ("artifact-write-strategy","pass","`artifact-write-strategy.md` declares manifest helper before artifact write.","all","-","no"),
        ("mockup-visual-inventory","pass","`mockup-visual-inventory.md` read; mockup only used for interaction hints.","all","-","no"),
        ("source-row-inventory","pass","Selected v9 rows plus residual gap rows preserved in writer-side inventory.","all","-","no"),
        ("source-normalization-atomic","pass","Normalization rows split visibility, requiredness, editability, dictionary, numeric, action and branch properties.","all","-","no"),
        ("dictionary-inventory","pass","`DICT-001`, `DICT-004`, `DICT-005` copied and linked to downstream artifacts.","WP-01; WP-02; WP-03","-","no"),
        ("test-design-decision-table","pass","Every normalized property has one TDDT decision.","all","-","no"),
        ("coverage-obligation-table","pass","Numeric, action-created, repeatable, checkbox and print-form classes are split with TC or gap links.","all","-","no"),
        ("coverage-metrics","pass","Metrics exist for all applicable dimensions.","all","-","no"),
        ("fixture-catalog","pass","Reusable valid baseline and Back branch fixture are explicit.","all","-","no"),
        ("risk-priority-map","pass","High-risk atoms have priority or residual gap decision.","all","-","no"),
        ("test-design-review","pass","`test-design-review.md` has no blocking failed rows.","all","-","no"),
        ("gap-admissibility","pass","Gaps do not hide source-backed visible UI behavior.","all","-","no"),
        ("ledger-atomicity","pass","Atoms do not combine independent properties except traceable requiredness trigger reuse.","all","-","no"),
        ("gsr-range-compression","pass","No broad `GSR N-M` atom used as covered behavior.","all","-","no"),
        ("design-plan-atomicity","pass","Plan rows have one check type/input class/oracle.","all","-","no"),
        ("scenario-does-not-replace-atomic","pass","Scenario/action TCs do not replace dictionary/numeric/requiredness atomic checks.","all","-","no"),
        ("tc-atomicity","pass","Each TC has one primary expected result.","all","-","no"),
        ("test-data-specificity","pass","Boundary/editability/branch TCs use concrete old/new and input values.","all","-","no"),
        ("internal-observability","pass","Backend/API/CDI effects remain gaps without executable hidden assertions.","all","-","no"),
        ("action-observability","pass","Action TCs name concrete UI state, navigation, confirmation or displayed value after reopen.","all","-","no"),
        ("semantic-req-id-parity","pass","PDF-only GSR ids are tied to the same selected rows/properties as source parity.","all","-","no"),
        ("tc-regression-smells","pass","No duplicate source token fields, missing `DICT-*` traceability, source-rule oracle, generic editability, unresolved-gap TC, or generic cleanup postcondition found in drafted TC set.","all","-","no"),
        ("package-ready","pass","All executable v9 packages are ready for structure preflight; residual gaps are explicit.","all","-","no"),
    ]
    gate_body = "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |\n| --- | --- | --- | --- | --- | --- |\n"
    gate_body += "\n".join("| " + " | ".join(f"`{x}`" if i in [0,1,5] else x for i, x in enumerate(row)) + " |" for row in gate_items)
    manifest("writer-quality-gate", TD / "writer-quality-gate.md", "Writer Quality Gate", gate_body)

    self_body = """
| check_item | status | evidence | follow_up |
| --- | --- | --- | --- |
| source parity checked | `yes` | `source-parity-check.md` read; v9 selected rows preserve required GSR ids. | Reviewer should verify row/GSR property mapping. |
| mandatory requirement IDs preserved | `yes` | `GSR 123; GSR 124; GSR 135; GSR 136; GSR 137; GSR 138; GSR 139; GSR 140; GSR 142; GSR 143; GSR 144; GSR 145; GSR 146; GSR 147; GSR 148` appear in ledger/TC/gap artifacts where selected. | None. |
| uncovered atoms | `accepted residual gaps` | `ATOM-011`, `ATOM-017`, `ATOM-020`, `ATOM-037`, `ATOM-038` link to `GAP-*`. | Do not treat as covered in review. |
| possible merged checks | `pass` | No TC combines positive and invalid classes; requiredness TCs use one red-highlight oracle. | None. |
| possible over-splitting | `pass` | Split follows mandatory classes; dictionary closed-set values are combined only as one list-composition check per dictionary. | None. |
| test-case grouping and numbering | `pass` | `TC-UI-EMP-V9-001` through `TC-UI-EMP-V9-029` are continuous. | None. |
| internal work package coverage | `pass` | `internal-work-package-coverage.md` summarizes WP gates. | None. |
| merged checks across packages | `pass` | No TC crosses packages except `GSR 142` requiredness trigger used as action oracle. | None. |
| assumptions | `pass-with-risk` | Valid fixture uses out-of-v9 `Должность` only as setup context, not coverage. | Reviewer should check fixture acceptability. |
| unclear items | `pass-with-gaps` | `GAP-001`..`GAP-007` remain open and non-blocking for structure preflight. | Semantic reviewer should verify gap admissibility. |
| high-risk atoms priority | `pass` | High-risk executable TCs have `Приоритет = High`; high-risk hidden effects remain gaps. | None. |
"""
    manifest("writer-self-check", TD / "writer-self-check.md", "Writer Self-Check", self_body)

    canon_preamble = """# Тест-кейсы: 2.1.1.1.1.2 Сведения о занятости — canary v9 agent-gate regression"""
    canon_sections = [
        (2, "Metadata", """
| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `ui-employment-canary-v9-agent-gate-regression` |
| section_id | `2.1.1.1.1.2` |
| writer_mode | `fresh-eval-run` |
| canonical_test_cases | `test-cases/2-1-1-1-1-2-ui-employment-canary-v9-agent-gate-regression.md` |
| test_design_dir | `work/test-design/ui-employment-canary-v9-agent-gate-regression/` |
"""),
        (2, "Coverage Boundary", """
Набор покрывает только выбранные в active prompt строки: `SRC-002`, `SRC-003`, `SRC-010`, `SRC-011`, `SRC-012`, `SRC-014`, `SRC-015`, `SRC-016`, `SRC-018`, `SRC-019`, `SRC-020`, `SRC-021`, связанные `GSR 123`, `GSR 124`, `GSR 135`, `GSR 136`, `GSR 137`, `GSR 138`, `GSR 139`, `GSR 140`, `GSR 142`, `GSR 143`, `GSR 144`, `GSR 145`, `GSR 146`, `GSR 147`, `GSR 148` и словари `DICT-001`, `DICT-004`, `DICT-005`.

Не покрываются как executable TC: employer/address/position/work-experience/work-phone requirements beyond fixture context, CDI rows `SRC-022`-`SRC-024`, backend/API/RabbitMQ/model effects, exact DaData behavior, mockup-only sample values and exact validation text.
"""),
        (2, "Canonical Artifact Links", """
| artifact | path |
| --- | --- |
| artifact write strategy | `work/test-design/ui-employment-canary-v9-agent-gate-regression/artifact-write-strategy.md` |
| source row inventory | `work/test-design/ui-employment-canary-v9-agent-gate-regression/source-row-inventory.md` |
| source table normalization | `work/test-design/ui-employment-canary-v9-agent-gate-regression/source-table-normalization.md` |
| dictionary inventory | `work/test-design/ui-employment-canary-v9-agent-gate-regression/dictionary-inventory.md` |
| test design decision table | `work/test-design/ui-employment-canary-v9-agent-gate-regression/test-design-decision-table.md` |
| coverage obligation table | `work/test-design/ui-employment-canary-v9-agent-gate-regression/coverage-obligation-table.md` |
| atomic requirements ledger | `work/test-design/ui-employment-canary-v9-agent-gate-regression/atomic-requirements-ledger.md` |
| package test design plan | `work/test-design/ui-employment-canary-v9-agent-gate-regression/package-test-design-plan.md` |
| coverage gaps | `work/test-design/ui-employment-canary-v9-agent-gate-regression/coverage-gaps.md` |
| writer quality gate | `work/test-design/ui-employment-canary-v9-agent-gate-regression/writer-quality-gate.md` |
| writer self-check | `work/test-design/ui-employment-canary-v9-agent-gate-regression/writer-self-check.md` |
"""),
        (2, "Dictionary Inventory", dict_body),
        (2, "Residual Coverage Gaps", """
`GAP-001`-`GAP-004` remain accepted non-blocking pre-writer residual gaps. This writer pass also records `GAP-005` and `GAP-006` for exact observable feedback of invalid numeric classes and `GAP-007` for print-form content mapping outside the selected v9 rows. These gaps are not executable test cases and are not treated as covered behavior.
"""),
        (2, "Test Cases", tc_markdown()),
    ]
    manifest_with_preamble("canonical-test-cases", CANONICAL, canon_preamble, canon_sections)

    session_log = """
# Writer Session Log Writer R1

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `fresh-eval-run / writer.session_initial_draft` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `ui-employment-canary-v9-agent-gate-regression` |
| started_from | `work/review-cycles/ui-employment-canary-v9-agent-gate-regression/cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command; budget status `pass (129.4 / 200.0 KiB)`.
- Selected required files: `AGENTS.md`; `skills/README.md`; `references/agent/session-based-review-cycle-format.md`; `references/agent/codex-sdk-orchestration-format.md`; `skills/ft-test-case-writer/SKILL.md`; `references/agent/writer-runtime-workflow.md`; `references/agent/writer-runtime-contract.md`; `references/qa/test-case-runtime-format.md`; `references/qa/coverage-runtime-checklist.md`; `references/qa/traceability-rules.md`; `references/agent/writer-process-workflow.md`; `references/agent/workflow-state-format.md`; `references/agent/session-log-format.md`; `references/agent/agent-decision-log-format.md`; `references/agent/writer-handoff-format.md`.
- `AGENT-NOTES.md` - package-specific abbreviations and DaData boundary.
- `work/stage-handoffs/00-source-selection/source-selection.md` - selected main DOCX/PDF/support/mockups.
- `work/stage-handoffs/01-ui-employment/scope-contract.md` - base UI employment scope and source rules.
- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md` - residual gaps `GAP-001`..`GAP-004`.
- `work/stage-handoffs/01-ui-employment/source-parity-check.md` - mandatory PDF-only GSR mapping.
- `work/stage-handoffs/01-ui-employment/source-row-inventory.md` - source row IDs and in-scope rows.
- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md` - interaction hints only.
- `work/stage-handoffs/01-ui-employment/scope-clarification-requests.md` - unanswered gap clarification rows.
- `work/review-cycles/ui-employment-canary-v2-test-design-upgrade/outputs/scope-gap-review-findings.md` - evidence that `GAP-001`..`GAP-004` are accepted non-blocking residual gaps.
- `work/test-design/ui-employment/dictionary-inventory.md` - source dictionary values for `DICT-001`, `DICT-004`, `DICT-005`.
- Main DOCX/PDF extracted directly for selected rows and GSR placement.

## Inputs Not Used

- Existing canary v1-v8 canonical files, ledgers, matrices, writer/reviewer outputs and helper scripts - excluded as requirement sources/templates by active prompt.
- `SRC-022`-`SRC-024` CDI rows - preserved through `GAP-004`, but out of v9 executable scope.
- Employer/address/position/work-experience/work-phone rows - not coverage sources, except `Должность` as fixture context where needed.

## Key Decisions

- Built v9 as a medium selected-row draft, not a full `ui-employment` rewrite.
- Split source properties before atoms and kept unresolved mechanisms as gaps instead of executable TC.
- Used `DICT-*` in every TC traceability row that uses dictionary data.
- Did not assert exact numeric invalid feedback, duplicate prevention UI mechanism, DaData internals, SPR/anti-fraud effects, CDI setup or print-form content mapping.

## Risks And Fallbacks

- Broad `rg` command surfaced old canary snippets; they were discarded and logged as contamination risk.
- Initial DOCX path with Cyrillic filename was mangled by shell path embedding; source was re-read by discovering the DOCX path from filesystem and setting UTF-8 output.

## Validation

- `python scripts\\validate_agent_artifacts.py --root fts\\ft-2-OF_16 --json` - run after artifact write; result recorded in final response and cycle artifacts.

## Contamination Check

- Old canary outputs were not used as requirement sources or templates after accidental broad search output.
- Source-backed decisions use active prompt, handoff artifacts, direct DOCX/PDF extraction and dictionary inventory only.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/test-design/ui-employment-canary-v9-agent-gate-regression/*.md` | `large generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
| `test-cases/2-1-1-1-1-2-ui-employment-canary-v9-agent-gate-regression.md` | `large generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest canonical-test-cases.manifest.json` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | Budget pass | resolver output |
| 2 | Read required instructions | Required files loaded | session log inputs |
| 3 | Read package/handoff inputs | Scope narrowed to v9 selected rows | handoff artifacts |
| 4 | Extracted DOCX/PDF selected rows | Field/action rules and GSR placement confirmed | direct DOCX/PDF extraction |
| 5 | Wrote split artifacts and canonical file | Manifest helper path used | `artifact-sections/manifests/` |
| 6 | Prepared reviewer prompt and cycle state | Next stage is structure preflight | `prompt.structure-preflight-r1.md`; `cycle-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | `pass` | `writer-quality-gate.md` | Structure preflight should parse canonical schema. |
| Self-check near misses | `pass-with-gaps` | `writer-self-check.md`; `coverage-gaps.md` | Semantic reviewer should check gap admissibility. |
| Contamination guard | `pass-with-disclosure` | old canary snippets discarded after broad search | Reviewer should not treat old snippets as evidence. |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Cyrillic source path mangled in shell command | Embedded non-ASCII DOCX path in Python here-stdin | Discovered DOCX/PDF paths by `Path(...).glob()` and set `PYTHONIOENCODING=utf-8` | `n/a` | `n/a` | `none; distorted path output not used as source evidence` | None. |
| `TF-002` | Broad search returned old canary snippets | `rg` over `fts/ft-2-OF_16` without excluding old canaries | Discarded old snippets and used direct DOCX/PDF/handoff/dictionary extraction | `n/a` | `n/a` | `contamination risk mitigated by exclusion` | Reviewer should verify no old canary wording drove requirements. |

## Handoff Notes For Next Session

- Structure preflight should focus on canonical schema, table parseability, `DICT-*` traceability, and absence of duplicated optional source fields.
- Semantic review should verify whether `GAP-005`/`GAP-006` are acceptable or whether support widget rules provide a deterministic invalid numeric oracle.
"""
    manifest_with_preamble("writer-session-log-writer-r1", OUTPUTS / "writer-session-log.writer-r1.md", "", [(1, "Writer Session Log Writer R1", session_log.split("# Writer Session Log Writer R1",1)[1].strip())])

    decision_log = """
| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `ui-employment-canary-v9-agent-gate-regression` |
| stage | `ft-test-case-writer` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | active prompt | Cover only v9 selected rows, not full employment section. | Prompt explicitly excludes full re-run and old canary sources. | canonical TC; source inventory | high | applied |
| `DEC-002` | 2 | `source-boundary` | accidental broad `rg` output | Discard old canary snippets as requirement evidence. | Active prompt allows old canaries only as regression comparison material. | session log contamination check | high | applied |
| `DEC-003` | 3 | `coverage` | `GSR 124`; `GSR 135` | Cover valid/min numeric classes and route invalid feedback classes to `GAP-005`/`GAP-006`. | Source says numeric/min rules but not exact UI feedback mechanism. | coverage gaps; obligation table | medium | applied |
| `DEC-004` | 4 | `gap` | `SRC-011`; `GAP-002` | Keep duplicate-income invariant as gap, no executable mechanism TC. | Exact prevention UI is explicitly unresolved. | coverage gaps; ledger | medium | applied |
| `DEC-005` | 5 | `test-design` | `DICT-001`; `DICT-004`; `DICT-005` | Dictionary TCs verify all and only active values and include `DICT-*` in traceability. | Runtime format requires traceability for dictionary use. | canonical TC; dictionary inventory | high | applied |
| `DEC-006` | 6 | `test-design` | `GSR 148` | Split Back `Да` and `Нет` branches into distinct save/no-save observable TCs. | Same navigation target has distinct source-backed data outcome. | TC-UI-EMP-V9-028; TC-UI-EMP-V9-029 | high | applied |
| `DEC-007` | 7 | `routing` | writer gate pass | Route to `structure-preflight-r1` with `writer-draft-ready`. | Writer artifacts and canonical file are ready for structure review. | cycle-state.yaml; next prompt | medium | applied |
"""
    manifest("agent-decision-log-writer-r1", OUTPUTS / "agent-decision-log.writer-r1.md", "Agent Decision Log", decision_log)

    prompt_body = """
## Stage Goal

Run `ft-test-case-reviewer` in `structure_preflight` mode for the v9 writer draft. This is a parseability and canonical-schema preflight only. Do not perform semantic redesign or edit the canonical test-case file.

## Cycle Context

- `cycle_id`: `ft-2-OF_16-ui-employment-canary-v9-agent-gate-regression`
- `scope_slug`: `ui-employment-canary-v9-agent-gate-regression`
- `current_stage`: `structure-preflight-r1`
- `semantic_round`: `1`
- canonical test cases: `test-cases/2-1-1-1-1-2-ui-employment-canary-v9-agent-gate-regression.md`
- test-design dir: `work/test-design/ui-employment-canary-v9-agent-gate-regression/`
- cycle state: `work/review-cycles/ui-employment-canary-v9-agent-gate-regression/cycle-state.yaml`

## Instruction Loading

Before review decisions, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file from resolver output. Record resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.

## Required Inputs

- `AGENT-NOTES.md`
- `work/stage-handoffs/00-source-selection/source-selection.md`
- `work/stage-handoffs/01-ui-employment/scope-contract.md`
- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md`
- `work/stage-handoffs/01-ui-employment/source-parity-check.md`
- `work/stage-handoffs/01-ui-employment/source-row-inventory.md`
- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md`
- `work/stage-handoffs/01-ui-employment/scope-clarification-requests.md`
- `work/test-design/ui-employment-canary-v9-agent-gate-regression/`
- `work/review-cycles/ui-employment-canary-v9-agent-gate-regression/outputs/writer-session-log.writer-r1.md`
- `work/review-cycles/ui-employment-canary-v9-agent-gate-regression/outputs/agent-decision-log.writer-r1.md`
- canonical test-case file listed above

## Structure Preflight Checks

- canonical `TC-*` sections are parseable and consistently use one schema;
- required runtime fields exist: `Название`, `Тип`, `Приоритет`, `Трассировка`, `Предусловия`, `Тестовые данные`, `Шаги`, `Итоговый ожидаемый результат`, `Постусловия`;
- `TC-*` numbering is continuous and stable;
- no optional source fields duplicate the same source token set as `Трассировка`;
- every TC using `DICT-*` includes that `DICT-*` in `Трассировка`;
- split artifacts use canonical table columns and are readable;
- action-created block TCs have cleanup postconditions;
- no unresolved `GAP-*` is represented as executable `TC-*`;
- no current-scope validator warning/error blocks structure review.

## Expected Outputs

Write reviewer outputs under `work/review-cycles/ui-employment-canary-v9-agent-gate-regression/outputs/`:

- `structure-preflight-r1-findings.md`
- `reviewer-session-log.structure-preflight-r1.md`
- `agent-decision-log.structure-preflight-r1.md`
- if blocked: `prompts/prompt.writer-structure-r1.md`
- if passed: `prompts/prompt.semantic-review-r1.md`

Update `cycle-state.yaml` before ending according to `session-based-review-cycle-format.md`.
"""
    manifest("prompt-structure-preflight-r1", PROMPTS / "prompt.structure-preflight-r1.md", "Handoff Prompt", prompt_body)

    index = "\n".join(str(p) for p in sorted(MANIFESTS.glob("*.manifest.json")))
    write(MANIFESTS / "manifest-list.txt", index)


if __name__ == "__main__":
    main()
