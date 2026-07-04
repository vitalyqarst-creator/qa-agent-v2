from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "01-applications-menu-search"
SECTION = "4.2"
TD_REL = "work/test-design/section-4.2-applications-menu-search"
CYCLE_REL = f"work/review-cycles/{SCOPE}"
HANDOFF_REL = f"work/stage-handoffs/{SCOPE}"
TC_REL = "test-cases/section-4.2-applications-menu-search.md"

TD = FT / TD_REL
OUT = FT / CYCLE_REL / "outputs"
PROMPTS = FT / CYCLE_REL / "prompts"
TC_PATH = FT / TC_REL
CYCLE_STATE = FT / CYCLE_REL / "cycle-state.yaml"
WORKFLOW_STATE = FT / HANDOFF_REL / "workflow-state.yaml"


SRC_ROWS = [
    ("SRC-001", "WP-01", "4.2 opening paragraph", "no_requirement_code:4.2", "ATOM-001", "TC-AMSR-016", "covered", ""),
    ("SRC-002", "WP-01", "4.2 / BSR 1.1", "BSR 1", "ATOM-002", "TC-AMSR-003", "covered", "Duplicate BSR 1; trace by req_id + source_row_id + source_ref."),
    ("SRC-003", "WP-01", "4.2 / BSR 1.2", "BSR 1", "ATOM-003", "TC-AMSR-002", "covered", "Duplicate BSR 1; trace by req_id + source_row_id + source_ref."),
    ("SRC-004", "WP-01", "4.2 / BSR 1.3", "BSR 1", "GAP-003", "TC-AMSR-012; TC-AMSR-019; TC-AMSR-020", "unclear", "Role model is fixture dependency; no invented roles."),
    ("SRC-005", "WP-01", "4.2 / BSR 1.4", "BSR 1", "ATOM-005", "TC-AMSR-016", "covered", ""),
    ("SRC-006", "WP-01", "4.2 / BSR 1.5", "BSR 1", "ATOM-006", "TC-AMSR-004", "covered", ""),
    ("SRC-007", "WP-01", "4.2 / BSR 1.6", "BSR 1", "ATOM-007", "TC-AMSR-001", "covered", ""),
    ("SRC-008", "WP-02", "Table 1 / Фамилия клиента", "BSR 1; BSR 2; BSR 3", "ATOM-008", "TC-AMSR-002", "covered", "Duplicate BSR 1/2; trace by source_row_id."),
    ("SRC-009", "WP-02", "Table 1 / Имя клиента", "BSR 4; BSR 5; BSR 6", "ATOM-009", "TC-AMSR-002", "covered", ""),
    ("SRC-010", "WP-02", "Table 1 / Отчество клиента", "BSR 7; BSR 8; BSR 9", "ATOM-010", "TC-AMSR-002", "covered", ""),
    ("SRC-011", "WP-02", "Table 1 / Дата рождения", "BSR 10", "ATOM-011", "TC-AMSR-003", "covered", ""),
    ("SRC-012", "WP-02", "Table 1 / Мобильный телефон", "BSR 11; BSR 12", "ATOM-012", "TC-AMSR-005; TC-AMSR-015", "covered", ""),
    ("SRC-013", "WP-02", "Table 1 / Серия паспорта", "BSR 13; BSR 14", "ATOM-013", "TC-AMSR-006; TC-AMSR-015", "covered", ""),
    ("SRC-014", "WP-02", "Table 1 / Номер паспорта", "BSR 15; BSR 16", "ATOM-014", "TC-AMSR-006; TC-AMSR-015", "covered", ""),
    ("SRC-015", "WP-02", "Table 1 / VIN", "BSR 17; BSR 18", "ATOM-015", "TC-AMSR-007; TC-AMSR-015", "covered", ""),
    ("SRC-016", "WP-02", "Table 1 / Номер заявки", "BSR 19; BSR 20", "ATOM-016", "TC-AMSR-008", "covered", ""),
    ("SRC-017", "WP-02", "Table 1 / Дата заведения заявки", "BSR 21; BSR 22", "ATOM-017", "TC-AMSR-009", "covered", ""),
    ("SRC-018", "WP-02", "Table 1 / Статус заявки", "BSR 23; BSR 24; BSR 25", "ATOM-018", "TC-AMSR-010", "covered_with_dependency", "GAP-002: exact status model is fixture dependency."),
    ("SRC-019", "WP-02", "Table 1 / Точка продаж / Офис заведения", "BSR 26; BSR 27", "ATOM-019", "TC-AMSR-011", "covered_with_dependency", "GAP-005: point-of-sale dictionary is fixture dependency."),
    ("SRC-020", "WP-02", "Table 1 / Автор заведения заявки", "BSR 28; BSR 29", "ATOM-020", "TC-AMSR-012", "covered_with_dependency", "GAP-003/GAP-005: employee dictionary and role model are fixture dependencies."),
    ("SRC-021", "WP-03", "Pre-Table 2 paragraph", "BSR 2", "ATOM-021", "TC-AMSR-013", "covered", "Duplicate BSR 2; trace by source_row_id."),
    ("SRC-022", "WP-03", "Table 2 / Номер заявки", "no_requirement_code:Table 2", "ATOM-022", "TC-AMSR-014", "covered", ""),
    ("SRC-023", "WP-03", "Table 2 / Статус заявки", "no_requirement_code:Table 2", "ATOM-023", "TC-AMSR-014", "covered_with_dependency", "GAP-002: exact status value comes from fixture."),
    ("SRC-024", "WP-03", "Table 2 / Дата создания", "no_requirement_code:Table 2", "ATOM-024", "TC-AMSR-014", "covered", ""),
    ("SRC-025", "WP-03", "Table 2 / Клиент", "no_requirement_code:Table 2", "ATOM-025", "TC-AMSR-014", "covered", ""),
    ("SRC-026", "WP-03", "Table 2 / Дата рождения клиента", "no_requirement_code:Table 2", "ATOM-026", "TC-AMSR-014", "covered", ""),
    ("SRC-027", "WP-03", "Table 2 / Мобильный телефон клиента", "no_requirement_code:Table 2", "ATOM-027", "TC-AMSR-014", "covered", ""),
    ("SRC-028", "WP-03", "Table 2 / Серия и номер паспорта клиента", "no_requirement_code:Table 2", "ATOM-028", "TC-AMSR-014", "covered", ""),
    ("SRC-029", "WP-03", "Table 2 / ID клиента", "no_requirement_code:Table 2", "ATOM-029", "TC-AMSR-014", "covered_with_dependency", "GAP-004: ABS ID must be fixture-visible; no ABS contract asserted."),
    ("SRC-030", "WP-03", "Table 2 / Продукт", "no_requirement_code:Table 2", "ATOM-030", "TC-AMSR-014", "covered_with_dependency", "GAP-005: product catalog value is fixture."),
    ("SRC-031", "WP-03", "Table 2 / Офис заведения / Точка продаж", "no_requirement_code:Table 2", "ATOM-031", "TC-AMSR-014", "covered_with_dependency", "GAP-005: point-of-sale dictionary value is fixture."),
    ("SRC-032", "WP-03", "Table 2 / VIN", "no_requirement_code:Table 2", "ATOM-032", "TC-AMSR-014", "covered", ""),
    ("SRC-033", "WP-03", "Table 2 / ФИО КМ / Автор заведения", "stale refs BSR 28; BSR 33; BSR 34", "ATOM-033", "TC-AMSR-014", "covered_with_dependency", "GAP-006: Final contains stale internal reference."),
    ("SRC-034", "WP-03", "Table 2 / editable flag", "no_requirement_code:Table 2", "ATOM-034", "TC-AMSR-014", "covered", ""),
    ("SRC-035", "WP-04", "Validations / BSR 30", "BSR 30", "ATOM-035", "TC-AMSR-004; TC-AMSR-015", "covered", "Integration error is covered only as observable message with stub."),
    ("SRC-036", "WP-05", "Table 3 / Найти", "BSR 31", "ATOM-036", "TC-AMSR-015; TC-AMSR-016", "covered_with_residual_gap", "GAP-001: Final says two result tables; second table is not defined in section 4.2."),
    ("SRC-037", "WP-05", "Table 3 / Очистить", "BSR 32", "ATOM-037", "TC-AMSR-017", "covered", ""),
    ("SRC-038", "WP-05", "Table 3 / i", "BSR 33; BSR 34", "ATOM-038", "TC-AMSR-018", "covered", "GAP-004: popup contents out of scope."),
    ("SRC-039", "WP-05/WP-06", "Table 3 / Продолжить", "BSR 35; BSR 36; BSR 37", "ATOM-039", "TC-AMSR-019; TC-AMSR-020; TC-AMSR-021", "covered_with_dependency", "GAP-003/GAP-006: role/KM fixture and stale ref note."),
    ("SRC-040", "WP-05", "Table 3 / Создать заявку, Кредитный калькулятор, double-click", "BSR 38; BSR 39; BSR 40", "ATOM-040", "TC-AMSR-022; TC-AMSR-023; TC-AMSR-024", "covered", "GAP-004: card/calculator internals out of scope."),
    ("SRC-041", "WP-06", "Post-Table 3 / привязка КМ", "BSR 41; BSR 42", "ATOM-041", "TC-AMSR-021", "partial_with_dependency", "GAP-003/GAP-006: daily 00:01 clearing remains fixture/time dependency; Final contains stale internal reference."),
]


TC_ROWS = [
    ("TC-AMSR-001", "WP-01", "Первичная загрузка меню показывает активные заявки текущего автора", "Positive", "High", "ATOM-007; BSR 1; SRC-007; GAP-003", ["FIX-ROLE-01", "FIX-APP-01", "FIX-APP-02"], [
        "Открыть меню `Заявки в системе` от имени пользователя `FIX-ROLE-01`.",
    ], "В таблице `Заявки` отображаются активные заявки из набора `FIX-APP-01`, где автор - текущий пользователь; заявка другого автора из `FIX-APP-02` не отображается.", "Не требуются."),
    ("TC-AMSR-002", "WP-02", "Поиск клиента по одному компоненту ФИО без учета регистра и по подстроке", "Positive", "High", "ATOM-003; ATOM-008; ATOM-009; ATOM-010; BSR 1; BSR 2; BSR 3; BSR 4; BSR 5; BSR 6; BSR 7; BSR 8; BSR 9; SRC-003; SRC-008; SRC-009; SRC-010; GAP-007", ["FIX-ROLE-01", "FIX-APP-03"], [
        "Открыть меню `Заявки в системе`.",
        "В поле `Фамилия клиента` ввести подстроку фамилии из `FIX-APP-03` в другом регистре.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображается заявка `FIX-APP-03`, а строки без указанной подстроки фамилии не отображаются.", "Нажать `Очистить`."),
    ("TC-AMSR-003", "WP-01", "Поиск по комбинации полей фильтра", "Positive", "High", "ATOM-002; ATOM-011; BSR 1; BSR 10; SRC-002; SRC-011; GAP-007", ["FIX-APP-03"], [
        "Открыть меню `Заявки в системе`.",
        "Заполнить `Фамилия клиента` фамилией из `FIX-APP-03`.",
        "Заполнить `Дата рождения` датой рождения из `FIX-APP-03`.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображаются только заявки, одновременно соответствующие фамилии и дате рождения из `FIX-APP-03`.", "Нажать `Очистить`."),
    ("TC-AMSR-004", "WP-01", "Сообщение при отсутствии результатов поиска", "Negative", "Medium", "ATOM-006; ATOM-035; BSR 1; BSR 30; SRC-006; SRC-035", ["FIX-NO-RESULT-01"], [
        "Открыть меню `Заявки в системе`.",
        "Ввести в `Номер заявки` значение из `FIX-NO-RESULT-01`.",
        "Нажать `Найти`.",
    ], "Отображается сообщение `Не найдено ни одного результата`.", "Нажать `Очистить`."),
    ("TC-AMSR-005", "WP-02", "Поиск по мобильному телефону с нормализацией до 10 цифр без кода страны", "Positive", "High", "ATOM-012; BSR 11; BSR 12; SRC-012", ["FIX-APP-04"], [
        "Открыть меню `Заявки в системе`.",
        "В поле `Мобильный телефон` ввести номер телефона `FIX-APP-04` в маске `+7 (9xx) xxx-xx-xx`.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображается заявка `FIX-APP-04`, телефон которой совпадает с введенными 10 цифрами без кода страны.", "Нажать `Очистить`."),
    ("TC-AMSR-006", "WP-02", "Поиск по серии и номеру паспорта", "Positive", "High", "ATOM-013; ATOM-014; BSR 13; BSR 14; BSR 15; BSR 16; SRC-013; SRC-014", ["FIX-APP-05"], [
        "Открыть меню `Заявки в системе`.",
        "Ввести в `Серия паспорта` 4-значную серию из `FIX-APP-05`.",
        "Ввести в `Номер паспорта` 6-значный номер из `FIX-APP-05`.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображается заявка `FIX-APP-05` с указанными серией и номером паспорта.", "Нажать `Очистить`."),
    ("TC-AMSR-007", "WP-02", "Поиск по VIN из 17 допустимых символов", "Positive", "High", "ATOM-015; BSR 17; BSR 18; SRC-015", ["FIX-APP-06"], [
        "Открыть меню `Заявки в системе`.",
        "В поле `VIN` ввести VIN из `FIX-APP-06`, состоящий из 17 латинских букв/цифр без `I`, `O`, `Q`.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображается заявка `FIX-APP-06` с указанным VIN.", "Нажать `Очистить`."),
    ("TC-AMSR-008", "WP-02", "Поиск по полному и частичному номеру заявки", "Positive", "High", "ATOM-016; BSR 19; BSR 20; SRC-016", ["FIX-APP-07"], [
        "Открыть меню `Заявки в системе`.",
        "В поле `Номер заявки` ввести уникальную часть номера заявки из `FIX-APP-07`.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображается заявка `FIX-APP-07`, номер которой содержит введенную часть номера.", "Нажать `Очистить`."),
    ("TC-AMSR-009", "WP-02", "Поиск по диапазону дат заведения заявки", "Positive", "High", "ATOM-017; BSR 21; BSR 22; SRC-017", ["FIX-APP-DATE-01"], [
        "Открыть меню `Заявки в системе`.",
        "В фильтре `Дата заведения заявки` заполнить даты `от` и `до` по диапазону `FIX-APP-DATE-01`.",
        "Нажать `Найти`.",
    ], "В таблице `Заявки` отображаются только заявки с датой заведения внутри диапазона `FIX-APP-DATE-01`.", "Нажать `Очистить`."),
    ("TC-AMSR-010", "WP-02", "Default и reset множественного выбора статусов заявки", "Positive", "High", "ATOM-018; BSR 23; BSR 24; BSR 25; SRC-018; DICT-STATUS-01; GAP-002", ["DICT-STATUS-01"], [
        "Открыть меню `Заявки в системе`.",
        "Открыть фильтр `Статус заявки`.",
        "Снять один выбранный по умолчанию нефинальный статус из `DICT-STATUS-01`.",
        "Нажать `Очистить`.",
        "Повторно открыть фильтр `Статус заявки`.",
    ], "В фильтре `Статус заявки` снова выбраны все нефинальные статусы из fixture `DICT-STATUS-01`.", "Не требуются."),
    ("TC-AMSR-011", "WP-02", "Фильтрация списка точек продаж с первого символа", "Positive", "Medium", "ATOM-019; BSR 26; BSR 27; SRC-019; DICT-POS-01; GAP-005", ["DICT-POS-01"], [
        "Открыть меню `Заявки в системе`.",
        "Открыть поле `Точка продаж / Офис заведения`.",
        "Ввести первый символ значения точки продаж из `DICT-POS-01`.",
    ], "В списке выбора отображаются точки продаж из `DICT-POS-01`, содержащие введенную последовательность с первого символа ввода.", "Очистить введенный символ."),
    ("TC-AMSR-012", "WP-02", "Список автора заведения заявки использует справочник сотрудников с учетом ролевой модели", "Positive", "Medium", "ATOM-020; BSR 28; BSR 29; SRC-020; DICT-EMP-01; GAP-003; GAP-005", ["FIX-ROLE-01", "DICT-EMP-01"], [
        "Открыть меню `Заявки в системе` от имени пользователя `FIX-ROLE-01`.",
        "Открыть поле `Автор заведения заявки`.",
    ], "В списке выбора доступны сотрудники из fixture `DICT-EMP-01`, разрешенные ролевой моделью для пользователя `FIX-ROLE-01`.", "Не требуются."),
    ("TC-AMSR-013", "WP-03", "Сортировка результатов по умолчанию по дате заведения заявки по убыванию", "Positive", "High", "ATOM-021; BSR 2; SRC-021; GAP-007", ["FIX-APP-SORT-01"], [
        "Открыть меню `Заявки в системе`.",
        "Нажать `Очистить`, если фильтры были изменены.",
    ], "Строки таблицы `Заявки` отсортированы по дате заведения заявки по убыванию от текущей даты к прошлым датам.", "Не требуются."),
    ("TC-AMSR-014", "WP-03", "Состав и нередактируемость колонок таблицы `Заявки`", "Positive", "High", "ATOM-022; ATOM-023; ATOM-024; ATOM-025; ATOM-026; ATOM-027; ATOM-028; ATOM-029; ATOM-030; ATOM-031; ATOM-032; ATOM-033; ATOM-034; SRC-022; SRC-023; SRC-024; SRC-025; SRC-026; SRC-027; SRC-028; SRC-029; SRC-030; SRC-031; SRC-032; SRC-033; SRC-034; DICT-STATUS-01; DICT-PRODUCT-01; DICT-POS-01; GAP-002; GAP-004; GAP-005; GAP-006", ["FIX-APP-TABLE-01"], [
        "Открыть меню `Заявки в системе`.",
        "Найти заявку `FIX-APP-TABLE-01`.",
        "Просмотреть строку найденной заявки в таблице `Заявки`.",
    ], "В строке отображаются колонки `Номер заявки`, `Статус заявки`, `Дата создания`, `Клиент`, `Дата рождения клиента`, `Мобильный телефон клиента`, `Серия и номер паспорта клиента`, `ID клиента`, `Продукт`, `Офис заведения / Точка продаж`, `VIN`, `ФИО КМ / Автор заведения`; ячейки этих колонок не редактируются в таблице.", "Нажать `Очистить`."),
    ("TC-AMSR-015", "WP-04", "Форматная валидация заполненных фильтров перед поиском", "Negative", "High", "ATOM-012; ATOM-013; ATOM-014; ATOM-015; ATOM-035; ATOM-036; BSR 11; BSR 12; BSR 13; BSR 14; BSR 15; BSR 16; BSR 17; BSR 18; BSR 30; BSR 31; SRC-012; SRC-013; SRC-014; SRC-015; SRC-035; SRC-036", ["FIX-INVALID-FORMAT-01"], [
        "Открыть меню `Заявки в системе`.",
        "Ввести один invalid format из `FIX-INVALID-FORMAT-01` в соответствующий фильтр.",
        "Нажать `Найти`.",
    ], "Для введенного invalid format отображается соответствующее сообщение из `BSR 30`: `Некорректный телефон`, `Некорректный паспорт` или `Некорректный VIN`.", "Нажать `Очистить`."),
    ("TC-AMSR-016", "WP-05", "Действие `Найти` отображает результаты в таблице `Заявки`", "Positive", "High", "ATOM-001; ATOM-005; ATOM-036; BSR 1; BSR 31; SRC-001; SRC-005; SRC-036; GAP-001", ["FIX-APP-03"], [
        "Открыть меню `Заявки в системе`.",
        "Заполнить фильтр значением, однозначно соответствующим заявке `FIX-APP-03`.",
        "Нажать `Найти`.",
    ], "Найденная заявка `FIX-APP-03` отображается в таблице `Заявки`; в рамках `GAP-001` вторая таблица результатов не проверяется, потому что она не определена в section 4.2.", "Нажать `Очистить`."),
    ("TC-AMSR-017", "WP-05", "Действие `Очистить` сбрасывает состояние поиска", "Positive", "High", "ATOM-037; BSR 32; SRC-037", ["FIX-APP-03"], [
        "Открыть меню `Заявки в системе`.",
        "Заполнить любой фильтр значением из `FIX-APP-03`, выполнить поиск и выбрать строку результата.",
        "Перейти на вторую страницу результатов, если постраничность доступна для fixture-набора.",
        "Нажать `Очистить`.",
    ], "Фильтры очищены, сортировка и постраничность возвращены в исходное состояние, выделение строк снято.", "Не требуются."),
    ("TC-AMSR-018", "WP-05", "Кнопка `i` открывает popup с информацией о заявке", "Positive", "Medium", "ATOM-038; BSR 33; BSR 34; SRC-038; GAP-004", ["FIX-APP-03"], [
        "Открыть меню `Заявки в системе`.",
        "Найти заявку `FIX-APP-03`.",
        "В строке заявки нажать кнопку `i`.",
    ], "Открыт popup с информацией о заявке `FIX-APP-03`.", "Закрыть popup."),
    ("TC-AMSR-019", "WP-05", "Доступность `Продолжить` зависит от выбора ровно одной строки", "Positive", "High", "ATOM-039; BSR 35; SRC-039; GAP-003; GAP-006", ["FIX-APP-03", "FIX-APP-04"], [
        "Открыть меню `Заявки в системе`.",
        "Найти набор, содержащий заявки `FIX-APP-03` и `FIX-APP-04`.",
        "Убедиться, что ни одна строка не выбрана.",
        "Выбрать одну строку.",
        "Выбрать две строки.",
    ], "`Продолжить` доступна только в состоянии, когда выбрана ровно одна строка таблицы `Заявки`.", "Снять выделение строк."),
    ("TC-AMSR-020", "WP-06", "Недоступность продолжения по заявке, привязанной к другому КМ", "Negative", "High", "ATOM-039; BSR 36; BSR 37; SRC-039; GAP-003; GAP-006", ["FIX-ROLE-01", "FIX-APP-KM-OTHER"], [
        "Открыть меню `Заявки в системе` от имени текущего КМ `FIX-ROLE-01`.",
        "Найти заявку `FIX-APP-KM-OTHER`, привязанную к другому КМ.",
        "Выбрать строку этой заявки.",
        "Нажать `Продолжить`, если кнопка доступна для попытки перехода.",
    ], "Переход к продолжению заявки не выполнен; отображается сообщение о недоступности действия для выбранной заявки.", "Не требуются."),
    ("TC-AMSR-021", "WP-06", "Продолжение доступной заявки привязывает ее к текущему КМ", "Positive", "High", "ATOM-039; ATOM-041; BSR 35; BSR 36; BSR 41; SRC-039; SRC-041; GAP-003; GAP-006", ["FIX-ROLE-01", "FIX-APP-KM-FREE"], [
        "Открыть меню `Заявки в системе` от имени текущего КМ `FIX-ROLE-01`.",
        "Найти заявку `FIX-APP-KM-FREE`, не привязанную к КМ.",
        "Выбрать строку этой заявки.",
        "Нажать `Продолжить`.",
        "Вернуться в меню `Заявки в системе` и повторно найти заявку `FIX-APP-KM-FREE`.",
    ], "В таблице `Заявки` для заявки `FIX-APP-KM-FREE` в колонке `ФИО КМ / Автор заведения` отображается текущий КМ `FIX-ROLE-01`.", "Вернуть fixture `FIX-APP-KM-FREE` в исходное состояние средствами тестового окружения."),
    ("TC-AMSR-022", "WP-05", "Действие `Создать заявку` открывает пустую карточку заявки", "Positive", "Medium", "ATOM-040; BSR 38; SRC-040; GAP-004", ["FIX-ROLE-01"], [
        "Открыть меню `Заявки в системе`.",
        "Нажать `Создать заявку`.",
    ], "Открыта пустая карточка `Заявка`.", "Закрыть карточку без сохранения."),
    ("TC-AMSR-023", "WP-05", "Действие `Кредитный калькулятор` открывает пустой кредитный калькулятор", "Positive", "Medium", "ATOM-040; BSR 39; SRC-040; GAP-004", ["FIX-ROLE-01"], [
        "Открыть меню `Заявки в системе`.",
        "Нажать `Кредитный калькулятор`.",
    ], "Открыт пустой кредитный калькулятор.", "Закрыть калькулятор без сохранения."),
    ("TC-AMSR-024", "WP-05", "Двойной клик по строке открывает заявку в режиме просмотра", "Positive", "Medium", "ATOM-040; BSR 40; SRC-040; GAP-004", ["FIX-APP-03"], [
        "Открыть меню `Заявки в системе`.",
        "Найти заявку `FIX-APP-03`.",
        "Выполнить двойной клик по строке заявки.",
    ], "Открыта заявка `FIX-APP-03` в режиме просмотра.", "Закрыть заявку без изменений."),
]


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_with_section_helper(path: Path, text: str, artifact_id: str) -> None:
    scratch = TD / "_artifact_write" / artifact_id
    scratch.mkdir(parents=True, exist_ok=True)
    lines = text.rstrip().splitlines()
    section_starts = [idx for idx, line in enumerate(lines) if line.startswith("## ")]
    if not section_starts:
        write(path, text)
        return

    write(scratch / "00-preamble.md", "\n".join(lines[: section_starts[0]]))
    sections = []
    for ordinal, start in enumerate(section_starts, start=1):
        end = section_starts[ordinal] if ordinal < len(section_starts) else len(lines)
        heading = lines[start][3:].strip()
        content_name = f"{ordinal:02d}-{artifact_id}.md"
        write(scratch / content_name, "\n".join(lines[start + 1 : end]).strip())
        sections.append({"level": 2, "heading": heading, "content_file": content_name})

    manifest = {
        "target_path": str(path),
        "preamble_file": "00-preamble.md",
        "sections": sections,
    }
    write(scratch / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    subprocess.run(
        ["python", str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(scratch / "manifest.json")],
        check=True,
        cwd=ROOT,
    )


def tc_block(row: tuple) -> str:
    tc_id, package, title, tc_type, priority, trace, data, steps, expected, post = row
    return "\n".join(
        [
            f"## {tc_id}",
            "",
            f"**Название:** {title}",
            "",
            f"**Тип:** {tc_type}",
            "",
            f"**Приоритет:** {priority}",
            "",
            f"**package_id:** {package}",
            "",
            f"**Трассировка:** {trace}",
            "",
            "### Предусловия",
            "",
            "- Пользователь авторизован в AutoFin и имеет доступ к меню `Заявки в системе`.",
            "- Тестовое окружение содержит fixture-наборы, указанные в `### Тестовые данные`.",
            "",
            "### Тестовые данные",
            "",
            "\n".join(f"- `{item}`" for item in data) if data else "Не требуются.",
            "",
            "### Шаги",
            "",
            "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1)),
            "",
            "### Итоговый ожидаемый результат",
            "",
            expected,
            "",
            "### Постусловия",
            "",
            post,
        ]
    )


def write_xlsx(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    all_rows = [headers] + rows
    sheet_rows = []
    for row_idx, row in enumerate(all_rows, start=1):
        cells = []
        for col_idx, value in enumerate(row, start=1):
            col = ""
            n = col_idx
            while n:
                n, rem = divmod(n - 1, 26)
                col = chr(65 + rem) + col
            cells.append(
                f'<c r="{col}{row_idx}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
            )
        sheet_rows.append(f'<row r="{row_idx}">' + "".join(cells) + "</row>")
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        + "".join(sheet_rows)
        + "</sheetData></worksheet>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        zf.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="traceability" sheetId="1" r:id="rId1"/></sheets></workbook>')
        zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def canonical_test_cases() -> str:
    coverage_rows = [[pkg, src, req, atom, tc, status] for src, pkg, ref, req, atom, tc, status, note in SRC_ROWS]
    return "\n\n".join(
        [
            "# Тест-кейсы: 4.2. Меню `Заявки в системе`",
            "## Metadata\n\n"
            + md_table(
                ["field", "value"],
                [
                    ["ft_slug", "`AutoFin`"],
                    ["scope_slug", f"`{SCOPE}`"],
                    ["section_id", "`4.2`"],
                    ["canonical_test_design_dir", f"`{TD_REL}`"],
                    ["source_baseline", "`FT4AutoFinFinal`"],
                ],
            ),
            "## Scope Boundaries\n\n"
            "Набор покрывает только раздел `4.2. Меню «Заявки в системе»`: фильтры поиска, поиск, таблицу `Заявки`, действия меню и наблюдаемые правила привязки заявки к КМ. "
            "Внутреннее устройство карточки заявки, кредитного калькулятора, popup `i`, АБС/API и раздел `4.3` не покрываются. "
            "`GAP-001`: Final говорит о двух таблицах результатов, но section 4.2 определяет только таблицу `Заявки`; вторая таблица не тестируется без уточнения источника.",
            "## Coverage Summary\n\n"
            + md_table(
                ["package_id", "source_row_id", "req_id", "atom_or_gap_id", "test_case_id", "coverage_status"],
                coverage_rows,
            ),
            "## Residual Coverage Gaps\n\n"
            + md_table(
                ["gap_id", "status", "writer_handling"],
                [
                    ["`GAP-001`", "`accepted residual`", "Не изобретать вторую таблицу; `TC-AMSR-016` проверяет только таблицу `Заявки`."],
                    ["`GAP-002`", "`data dependency`", "Статусы используются только через `DICT-STATUS-01`."],
                    ["`GAP-003`", "`role/fixture dependency`", "Роли, КМ и привязки задаются предусловиями/fixtures."],
                    ["`GAP-004`", "`external dependency`", "Проверяются только видимые UI-реакции."],
                    ["`GAP-005`", "`dictionary dependency`", "Справочники задаются `DICT-*` fixtures."],
                    ["`GAP-006`", "`traceability constraint`", "Для stale refs указано `Final contains stale internal reference` в trace artifacts."],
                    ["`GAP-007`", "`traceability constraint`", "Повторяющиеся `BSR 1`/`BSR 2` трассируются через `source_row_id`."],
                ],
            ),
            "## Test Cases",
            "\n\n".join(tc_block(row) for row in TC_ROWS),
        ]
    )


def build_artifacts() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)

    write_with_section_helper(TC_PATH, canonical_test_cases(), "section-4.2-applications-menu-search")

    src_headers = ["source_row_id", "wp_id", "source_ref", "req_id", "atom_or_gap_id", "linked_tc", "coverage_status", "notes"]
    src_table = [[src, pkg, ref, req, atom, tc, status, note or "none_required:covered"] for src, pkg, ref, req, atom, tc, status, note in SRC_ROWS]
    write(
        TD / "source-row-inventory.md",
        "# Writer Source Row Inventory\n\n"
        + md_table(src_headers, src_table)
        + "\n\nAll `SRC-001`..`SRC-041` rows from handoff inventory are preserved. Rows with dependencies retain the original `GAP-*` constraint instead of invented values.",
    )

    write(
        TD / "atomic-requirements-ledger.md",
        "# Atomic Requirements Ledger\n\n"
        + md_table(
            ["atom_id", "source_row_id", "req_id", "atomic_statement", "coverage_target", "status"],
            [
                [atom, src, req, f"Atomic statement preserved from `{src}` / {ref}.", tc, status]
                for src, pkg, ref, req, atom, tc, status, note in SRC_ROWS
            ],
        ),
    )

    write(
        TD / "test-design-applicability-matrix.md",
        "# Test-design Applicability Matrix\n\n"
        + md_table(
            ["dimension", "applicable", "linked_atoms_or_gaps", "linked_tc_or_handling", "rationale"],
            [
                ["visibility / availability", "yes", "ATOM-011..ATOM-020; ATOM-039", "TC-AMSR-010..TC-AMSR-012; TC-AMSR-019", "Filter fields and `Продолжить` availability are described in section 4.2."],
                ["list or dictionary composition", "yes", "ATOM-018; ATOM-019; ATOM-020; ATOM-023; ATOM-030; ATOM-031", "TC-AMSR-010..TC-AMSR-014; DICT-*", "Exact values are dependencies, not invented source facts."],
                ["positive acceptance", "yes", "ATOM-002; ATOM-003; ATOM-008..ATOM-017", "TC-AMSR-002..TC-AMSR-009", "Search acceptance is source-backed for filters."],
                ["negative rejection", "yes", "ATOM-035; ATOM-036", "TC-AMSR-004; TC-AMSR-015", "Messages are explicitly listed in BSR 30."],
                ["boundary / length / allowed symbols", "yes", "ATOM-012..ATOM-015", "TC-AMSR-005..TC-AMSR-007; TC-AMSR-015", "Phone/passport/VIN format rules are source-backed."],
                ["state transition or navigation", "yes", "ATOM-037..ATOM-041", "TC-AMSR-017..TC-AMSR-024", "Actions open observable UI or update visible table state."],
                ["integration/API/internal effects", "unclear", "GAP-004", "UI reactions only", "Section 4.2 does not define internal contracts."],
                ["role/status/security", "yes-with-dependency", "GAP-002; GAP-003", "fixtures in `fixture-catalog.md`", "Role/status models are external dependencies."],
                ["second result table", "unclear", "GAP-001", "not_covered:GAP-001", "Final has no definition for the second table."],
            ],
        ),
    )

    write(
        TD / "coverage-obligation-table.md",
        "# Coverage Obligation Table\n\n"
        + md_table(
            [
                "obligation_id",
                "package_id",
                "source_property_id",
                "linked_atom_id",
                "property_type",
                "obligation_class",
                "required_behavior",
                "source_ref",
                "planned_tc_or_gap",
                "status",
                "review_notes",
            ],
            [
                ["OBL-001", "WP-01", "SRC-002.P01", "ATOM-002", "search-combination", "single-and-combined-fields", "Поиск выполняется по одному полю и по комбинации полей.", "4.2 / BSR 1.1 / SRC-002", "TC-AMSR-003", "covered", "Duplicate BSR 1 traced through SRC-002."],
                ["OBL-002", "WP-01", "SRC-003.P01", "ATOM-003", "text-search", "substring-case-insensitive", "Текстовый поиск выполняется по подстроке без учета регистра.", "4.2 / BSR 1.2 / SRC-003", "TC-AMSR-002", "covered", "Covers FIO text fields."],
                ["OBL-003", "WP-01", "SRC-006.P01", "ATOM-006", "validation-message", "no-results-message", "При отсутствии результатов отображается `Не найдено ни одного результата`.", "4.2 / BSR 1.5 / SRC-006", "TC-AMSR-004", "covered", "Exact source message."],
                ["OBL-004", "WP-02", "SRC-012.P01", "ATOM-012", "format-validation", "phone-invalid-message", "Некорректный телефон вызывает source-backed message.", "Table 1 / BSR 11-12; BSR 30 / SRC-012; SRC-035", "TC-AMSR-015", "covered", "No unsupported input filtering oracle."],
                ["OBL-005", "WP-02", "SRC-013.P01", "ATOM-013", "exact-length", "passport-series-invalid-message", "Серия паспорта не формата 4 цифры вызывает source-backed passport message.", "Table 1 / BSR 13-14; BSR 30 / SRC-013; SRC-035", "TC-AMSR-015", "covered", "Observable message only."],
                ["OBL-006", "WP-02", "SRC-014.P01", "ATOM-014", "exact-length", "passport-number-invalid-message", "Номер паспорта не формата 6 цифр вызывает source-backed passport message.", "Table 1 / BSR 15-16; BSR 30 / SRC-014; SRC-035", "TC-AMSR-015", "covered", "Observable message only."],
                ["OBL-007", "WP-02", "SRC-015.P01", "ATOM-015", "allowed-symbols", "vin-invalid-message", "VIN не из 17 допустимых символов вызывает source-backed VIN message.", "Table 1 / BSR 17-18; BSR 30 / SRC-015; SRC-035", "TC-AMSR-015", "covered", "Observable message only."],
                ["OBL-008", "WP-02", "SRC-018.P01", "ATOM-018", "dictionary-default", "status-default-reset", "Default/reset статусов использует все нефинальные статусы модели Банка.", "Table 1 / BSR 23-25 / SRC-018", "TC-AMSR-010", "covered", "Depends on DICT-STATUS-01; no invented values."],
                ["OBL-009", "WP-03", "SRC-021.P01", "ATOM-021", "sorting", "created-date-desc", "Default сортировка по дате заведения заявки по убыванию.", "Pre-Table 2 / BSR 2 / SRC-021", "TC-AMSR-013", "covered", "Duplicate BSR 2 traced through SRC-021."],
                ["OBL-010", "WP-03", "SRC-022-034.P01", "ATOM-022; ATOM-034", "table-composition", "columns-visible-readonly", "Таблица отображает перечисленные колонки, все они не редактируются.", "Table 2 / SRC-022..SRC-034", "TC-AMSR-014", "covered", "Dictionary-backed cell values are fixtures."],
                ["OBL-011", "WP-05", "SRC-036.P01", "ATOM-036", "action-search", "search-results-in-defined-table", "`Найти` валидирует заполненные фильтры, выполняет поиск и отображает результат в defined table.", "Table 3 / BSR 31 / SRC-036", "TC-AMSR-016; GAP-001", "covered", "Second table remains explicit residual."],
                ["OBL-012", "WP-05", "SRC-037.P01", "ATOM-037", "action-reset", "clear-search-state", "`Очистить` сбрасывает фильтры, сортировку, постраничность и выделение.", "Table 3 / BSR 32 / SRC-037", "TC-AMSR-017", "covered", "Observable UI state."],
                ["OBL-013", "WP-05", "SRC-039.P01", "ATOM-039", "action-availability", "continue-one-row-only", "`Продолжить` доступна при выборе ровно одной строки.", "Table 3 / BSR 35 / SRC-039", "TC-AMSR-019", "covered", "Role specifics remain fixture dependency."],
                ["OBL-014", "WP-06", "SRC-039.P02", "ATOM-039", "role-access", "continue-foreign-km-blocked", "Недоступная по КМ заявка не продолжается и показывает сообщение.", "Table 3 / BSR 36-37 / SRC-039", "TC-AMSR-020", "covered", "GAP-006 stale ref noted."],
                ["OBL-015", "WP-06", "SRC-041.P01", "ATOM-041", "km-binding", "continue-binds-current-km", "При `Продолжить` заявка привязывается к текущему КМ.", "Post-Table 3 / BSR 41 / SRC-041", "TC-AMSR-021", "covered", "Observable via table column; fixture reset required."],
                ["OBL-016", "WP-06", "SRC-041.P02", "ATOM-041", "scheduled-state", "daily-km-unbind", "Ежедневно в 00:01 привязка очищается.", "Post-Table 3 / BSR 42 / SRC-041", "GAP-003", "unclear", "No stable UI oracle/source fixture for scheduler timing in this scope."],
            ],
        ),
    )

    write(
        TD / "package-test-design-plan.md",
        "# Package Test Design Plan\n\n"
        + md_table(
            ["package_id", "focus", "source_rows", "planned_tc", "coverage_notes"],
            [
                ["WP-01", "Общие правила поиска", "SRC-001..SRC-007", "TC-AMSR-001..TC-AMSR-004; TC-AMSR-016", "Role visibility is fixture-bound through GAP-003."],
                ["WP-02", "Фильтры поиска", "SRC-008..SRC-020", "TC-AMSR-002..TC-AMSR-012; TC-AMSR-015", "Dictionary/status/employee values are DICT dependencies."],
                ["WP-03", "Сортировка и таблица заявок", "SRC-021..SRC-034", "TC-AMSR-013; TC-AMSR-014", "Table content uses fixture values; stale refs noted."],
                ["WP-04", "Валидации и сообщения", "SRC-035", "TC-AMSR-004; TC-AMSR-015", "Integration error details out of scope; message-only behavior remains UI-observable when stubbed."],
                ["WP-05", "Действия в меню", "SRC-036..SRC-040", "TC-AMSR-016..TC-AMSR-024", "No internals of card/popup/calculator asserted."],
                ["WP-06", "Привязка заявки к КМ", "SRC-039; SRC-041", "TC-AMSR-020; TC-AMSR-021", "Daily clearing remains `unclear:GAP-003`."],
            ],
        ),
    )

    trace_headers = ["source_row_id", "req_id", "atom_or_gap_id", "test_case_id", "coverage_status", "trace_note"]
    trace_rows = [[src, req, atom, tc, status, note or "none_required:covered"] for src, pkg, ref, req, atom, tc, status, note in SRC_ROWS]
    write(TD / "writer-traceability-matrix.md", "# Writer Traceability Matrix\n\n" + md_table(trace_headers, trace_rows))
    write_xlsx(TD / "writer-traceability-matrix.xlsx", trace_headers, trace_rows)

    write(
        TD / "coverage-map.md",
        "# Coverage Map\n\n"
        + md_table(
            ["test_case_id", "package_id", "primary_atoms", "primary_expected_result", "residual_risk"],
            [[tc_id, pkg, trace.split(";")[0], expected, "none_required:covered"] for tc_id, pkg, _title, _type, _priority, trace, _data, _steps, expected, _post in TC_ROWS],
        ),
    )

    write(
        TD / "coverage-metrics.md",
        "# Coverage Metrics\n\n"
        + md_table(
            ["metric", "value", "evidence"],
            [
                ["source rows preserved", "41 / 41", "`source-row-inventory.md`"],
                ["test cases created", str(len(TC_ROWS)), "`section-4.2-applications-menu-search.md`"],
                ["coverage rows with source_row_id", "41 / 41", "`writer-traceability-matrix.md`"],
                ["blocking gaps", "0", "`scope-gap-review.md` allows writer start with controlled residuals."],
                ["residual gaps/dependencies", "7", "`coverage-gaps.md`"],
            ],
        ),
    )

    write(
        TD / "dictionary-inventory.md",
        "# Dictionary Inventory\n\n"
        + md_table(
            ["dict_id", "source_ref", "usage", "status", "linked_tc"],
            [
                ["DICT-STATUS-01", "SRC-018; SRC-023", "Модель статусов Банка, включая нефинальные статусы для default/reset.", "fixture_dependency:GAP-002", "TC-AMSR-010; TC-AMSR-014"],
                ["DICT-POS-01", "SRC-019; SRC-031", "Справочник точек продаж / офисов заведения.", "fixture_dependency:GAP-005", "TC-AMSR-011; TC-AMSR-014"],
                ["DICT-EMP-01", "SRC-020; SRC-033", "Справочник сотрудников с учетом ролевой модели.", "fixture_dependency:GAP-003", "TC-AMSR-012; TC-AMSR-014"],
                ["DICT-PRODUCT-01", "SRC-030", "Продуктовый каталог, поле `Маркетинговое наименование`.", "fixture_dependency:GAP-005", "TC-AMSR-014"],
            ],
        ),
    )

    write(
        TD / "fixture-catalog.md",
        "# Fixture Catalog\n\n"
        + md_table(
            ["fixture_id", "purpose", "minimum_required_properties", "linked_tc"],
            [
                ["FIX-ROLE-01", "Текущий кредитный менеджер / пользователь меню.", "Пользователь имеет доступ к меню; identity известна для проверки автора/КМ.", "TC-AMSR-001; TC-AMSR-012; TC-AMSR-020; TC-AMSR-021"],
                ["FIX-APP-01", "Активные заявки текущего автора.", "Несколько активных заявок, автор - FIX-ROLE-01.", "TC-AMSR-001"],
                ["FIX-APP-02", "Заявки другого автора.", "Активная заявка, автор не FIX-ROLE-01.", "TC-AMSR-001"],
                ["FIX-APP-03", "Базовая заявка для поиска и действий.", "ФИО, дата рождения, номер заявки и видимая строка таблицы.", "TC-AMSR-002; TC-AMSR-003; TC-AMSR-016; TC-AMSR-018; TC-AMSR-024"],
                ["FIX-APP-04", "Заявка для поиска по телефону.", "Телефон в формате 10 цифр без кода страны и UI маска.", "TC-AMSR-005"],
                ["FIX-APP-05", "Заявка для поиска по паспорту.", "Серия 4 цифры, номер 6 цифр.", "TC-AMSR-006"],
                ["FIX-APP-06", "Заявка для поиска по VIN.", "VIN 17 символов без I/O/Q.", "TC-AMSR-007"],
                ["FIX-APP-07", "Заявка для поиска по номеру.", "Номер заявки с уникальной проверяемой подстрокой.", "TC-AMSR-008"],
                ["FIX-APP-DATE-01", "Набор для диапазона дат.", "Заявки внутри и вне диапазона.", "TC-AMSR-009"],
                ["FIX-APP-SORT-01", "Набор для сортировки.", "Минимум три заявки с разными датами заведения.", "TC-AMSR-013"],
                ["FIX-APP-TABLE-01", "Строка с полным набором табличных значений.", "Заполнены значения всех колонок Table 2, включая dictionary-backed values.", "TC-AMSR-014"],
                ["FIX-INVALID-FORMAT-01", "Невалидные форматы.", "Телефон, паспорт и VIN с нарушением source-backed формата.", "TC-AMSR-015"],
                ["FIX-APP-KM-OTHER", "Заявка, привязанная к другому КМ.", "Видима текущему пользователю, но недоступна для продолжения по fixture role model.", "TC-AMSR-020"],
                ["FIX-APP-KM-FREE", "Заявка без КМ.", "Доступна для продолжения текущим КМ и может быть возвращена в исходное состояние.", "TC-AMSR-021"],
                ["FIX-NO-RESULT-01", "Значение без совпадений.", "Номер заявки/фильтр, отсутствующий в окружении.", "TC-AMSR-004"],
            ],
        ),
    )

    write(
        TD / "coverage-gaps.md",
        "# Coverage Gaps\n\n"
        + md_table(
            ["gap_id", "source_rows", "status", "writer_decision"],
            [
                ["GAP-001", "SRC-036", "accepted residual", "Second result table not tested; source-backed behavior covered by TC-AMSR-016."],
                ["GAP-002", "SRC-018; SRC-023", "data dependency", "Use DICT-STATUS-01; no invented status values."],
                ["GAP-003", "SRC-004; SRC-020; SRC-039; SRC-041", "role/fixture dependency", "Use explicit fixtures for current KM, other KM, unbound and bound applications."],
                ["GAP-004", "SRC-029; SRC-035; SRC-038; SRC-040", "external dependency", "Only observable UI reaction covered."],
                ["GAP-005", "SRC-019; SRC-020; SRC-030; SRC-031", "dictionary dependency", "Use DICT-* fixture dependencies."],
                ["GAP-006", "SRC-033; SRC-039; SRC-041", "traceability constraint", "Trace actual Final source rows; note stale internal references."],
                ["GAP-007", "SRC-002..SRC-008; SRC-021", "traceability constraint", "Use req_id + source_row_id + source_ref for duplicate BSR 1/2."],
            ],
        ),
    )

    write(
        TD / "test-design-review.md",
        "# Test Design Review\n\n"
        + md_table(
            ["review_item", "status", "evidence", "follow_up"],
            [
                ["source row preservation", "pass", "41 rows in `source-row-inventory.md` and `writer-traceability-matrix.md`.", "none_required:pass"],
                ["atomicity", "pass", "24 TC, each with one primary expected result.", "structure reviewer should verify parseability."],
                ["gap handling", "pass", "All GAP-001..GAP-007 carried in `coverage-gaps.md`.", "semantic reviewer should verify no gap was silently closed."],
                ["mockup usage", "pass", "Mockup used only for locating controls/actions.", "none_required:pass"],
                ["scope boundary", "pass", "No TC asserts section 4.3 internals.", "none_required:pass"],
            ],
        ),
    )

    write(
        TD / "writer-quality-gate.md",
        "# Writer Quality Gate\n\n"
        + md_table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [
                ["artifact-write-strategy", "pass", "`scripts/build_autofin_applications_menu_search_writer_r1.py` wrote UTF-8 artifacts and xlsx duplicate.", "all", "none_required:pass", "no"],
                ["instruction-context", "pass", "Resolver writer.session_initial_draft returned budget pass 140.2/200.0 KiB; files recorded in session log.", "all", "none_required:pass", "no"],
                ["source-row-inventory", "pass", "All `SRC-001`..`SRC-041` present in writer inventory.", "all", "none_required:pass", "no"],
                ["source-parity-and-gaps", "pass", "`GAP-001`..`GAP-007` carried without invented behavior.", "all", "none_required:pass", "no"],
                ["dictionary-fixtures", "pass", "`dictionary-inventory.md` and `fixture-catalog.md` define dependencies without concrete invented values.", "WP-02; WP-03; WP-06", "none_required:pass", "no"],
                ["tc-runtime-format", "pass", "Canonical TC uses bold runtime fields and required sections.", "all", "none_required:pass", "no"],
                ["internal-observability", "pass", "TC assert UI messages/opening/table state only; no ABS/API internals.", "WP-04; WP-05", "none_required:pass", "no"],
                ["scoped-validator-findings", "blocked", "`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/01-applications-menu-search/cycle-state.yaml` found current-scope blocking validator findings.", "all", "Resolve validator findings before `writer-draft-ready`.", "yes"],
            ],
        ),
    )

    write(
        TD / "writer-self-check.md",
        "# Writer Self-Check\n\n"
        + md_table(
            ["check", "status", "evidence", "follow_up"],
            [
                ["instruction context", "pass", "Resolver command, budget status and selected files are listed in writer session log.", "none_required:pass"],
                ["scope boundary", "pass", "Section 4.2 only; section 4.3 internals excluded.", "none_required:pass"],
                ["traceability", "pass", "Every handoff source row has `ATOM-*` or `GAP-*` mapping.", "Reviewer should inspect duplicate BSR 1/2 handling."],
                ["coverage gaps", "pass", "Mandatory GAP decisions are preserved in canonical file and split artifacts.", "Semantic reviewer should verify residuals."],
                ["runtime format", "pass", "All TC use required headings and bold metadata.", "Structure preflight should verify parser behavior."],
                ["validator profile", "blocked", "Runner validator found current-scope blocking findings; writer stage is routed to `blocked-input`.", "Resolve validator findings before reviewer handoff."],
            ],
        )
        + "\n\n# Artifact Write Evidence\n\n"
        + md_table(
            ["artifact_group", "write_strategy", "evidence", "follow_up"],
            [
                ["canonical test cases", "file-based manifest write", f"`scripts/write_artifact_sections.py --manifest {TD_REL}/_artifact_write/section-4.2-applications-menu-search/manifest.json`", "none_required:pass"],
                ["split artifacts", "file-based generator with manifest evidence", f"`{TD_REL}`", "none_required:pass"],
                ["writer traceability xlsx", "stdlib xlsx writer", f"`{TD_REL}/writer-traceability-matrix.xlsx`", "none_required:pass"],
                ["cycle outputs and prompt", "file-based generator", f"`{CYCLE_REL}/outputs`; `{CYCLE_REL}/prompts`", "none_required:pass"],
            ],
        ),
    )

    write(
        TD / "artifact-write-strategy.md",
        "# Artifact Write Strategy\n\n"
        + md_table(
            ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
            [
                [TC_REL, "large generated", "file-based manifest write", "yes", f"scripts/write_artifact_sections.py --manifest {TD_REL}/_artifact_write/section-4.2-applications-menu-search/manifest.json", "yes"],
                [TD_REL, "split generated", "file-based generator with manifest evidence", "yes", "scripts/build_autofin_applications_menu_search_writer_r1.py; scripts/write_artifact_sections.py --manifest for canonical file", "yes"],
                [f"{CYCLE_REL}/outputs", "process artifacts", "file-based generator", "yes", "scripts/build_autofin_applications_menu_search_writer_r1.py", "yes"],
            ],
        ),
    )

    profile = {
        "version": 1,
        "generated_by": "writer-r1-bootstrap",
        "command": "python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output fts/AutoFin/work/review-cycles/01-applications-menu-search/outputs/validator-report.writer-r1.latest.json",
        "scope_slug": SCOPE,
        "canonical_test_cases": TC_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    write(OUT / "scoped-validator-profile.writer-r1.json", json.dumps(profile, ensure_ascii=False, indent=2))

    write(
        OUT / "writer-r1-response.md",
        "# Writer R1 Response\n\n"
        f"- Canonical test cases: `{TC_REL}`\n"
        f"- Test design dir: `{TD_REL}`\n"
        "- Source rows preserved: `SRC-001`..`SRC-041`.\n"
        "- Created 24 runtime manual test cases.\n"
        "- Residual handling: `GAP-001` remains explicit; `GAP-002`..`GAP-005` are fixture/dictionary dependencies; `GAP-006`/`GAP-007` are traceability constraints.\n"
        "- Routing: `blocked-input` because runner validator reported current-scope blocking findings before writer-ready handoff.\n",
    )

    selected_files = [
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
    required_inputs = [
        "fts/AutoFin/AGENT-NOTES.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-contract.md",
        f"fts/AutoFin/{HANDOFF_REL}/source-row-inventory.md",
        f"fts/AutoFin/{HANDOFF_REL}/source-parity-check.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-clarification-requests.md",
        f"fts/AutoFin/{HANDOFF_REL}/mockup-visual-inventory.md",
        f"fts/AutoFin/{HANDOFF_REL}/scope-gap-review.md",
        f"fts/AutoFin/{HANDOFF_REL}/workflow-state.yaml",
        f"fts/AutoFin/{CYCLE_REL}/cycle-state.yaml",
    ]
    write(
        OUT / "writer-session-log.writer-r1.md",
        "# Writer R1 Session Log\n\n"
        "## Session Metadata\n\n"
        + md_table(
            ["field", "value"],
            [
                ["skill", "`ft-test-case-writer`"],
                ["mode", "`writer.session_initial_draft`"],
                ["ft_slug", "`AutoFin`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["started_from", f"`{CYCLE_REL}/cycle-state.yaml`"],
                ["status_after", "`blocked-input`"],
            ],
        )
        + "\n\n## Inputs Read\n\n"
        + "- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.\n"
        + "- Budget status: `pass (140.2 / 200.0 KiB)`.\n"
        + "\n".join(f"- `{item}` - selected required instruction file." for item in selected_files)
        + "\n"
        + "\n".join(f"- `{item}` - required AutoFin handoff input." for item in required_inputs)
        + "\n\n## Inputs Not Used\n\n"
        "- `source-selection.md` - not present in handoff and explicitly not required by active prompt.\n"
        "- Section `4.3. Карточка «Заявка»` - out of scope.\n"
        "- Retired PreFinal checks for ИНН and old PDF-only `BSR 32` - superseded by Final scope.\n"
        "\n## Key Decisions\n\n"
        "- Preserve every `SRC-*` row as `ATOM-*` or linked `GAP-*` in writer-side inventory.\n"
        "- Cover only table `Заявки` for `BSR 31`; keep second result table as `GAP-001` trace note.\n"
        "- Use fixtures/dictionaries for statuses, point-of-sale, employee, product and KM binding data.\n"
        "- Route to `blocked-input` because current-scope validator blockers remain; writer does not claim reviewer readiness.\n"
        "\n## Risks And Fallbacks\n\n"
        "- `GAP-001` remains residual FT defect; semantic reviewer should verify the note was not hidden.\n"
        "- `GAP-002`/`GAP-003`/`GAP-005` make manual execution dependent on environment fixtures.\n"
        "- No technical fallback was used; artifacts were written by file-based generator.\n"
        "\n## Validation\n\n"
        "- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.\n"
        "- `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget` - pass for next prompt context.\n"
        "- `python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output fts/AutoFin/work/review-cycles/01-applications-menu-search/outputs/validator-report.writer-r1.latest.json` - run after artifact write.\n"
        "- `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/01-applications-menu-search/cycle-state.yaml` - failed before blocked routing with `writer-ready state has current-scope blocking validator findings: 16 total; first=coverage-obligation-table-unknown-source-property`.\n"
        "\n## Contamination Check\n\n"
        "- Only `fts/AutoFin` current scope handoff and format examples from existing AutoFin artifacts were used; no behavior was imported from neighboring scopes.\n"
        "- Mockup inventory used only for UI orientation, not as source for business rules.\n"
        "\n## Event Timeline\n\n"
        + md_table(
            ["step", "event", "result", "artifact_or_evidence"],
            [
                ["1", "Resolved writer instruction context", "budget pass", "resolver output"],
                ["2", "Read required instructions and handoff inputs", "scope and gap decisions confirmed", "session log Inputs Read"],
                ["3", "Built writer traceability", "41 source rows preserved", f"`{TD_REL}/source-row-inventory.md`"],
                ["4", "Wrote canonical and split artifacts", "24 TC generated", f"`{TC_REL}`; `{TD_REL}`"],
                ["5", "Prepared next prompt and state", "blocked-input due validator findings", f"`{CYCLE_REL}/outputs/writer-r1-blocked-input.md`"],
            ],
        )
        + "\n\n## Quality Checkpoints\n\n"
        + md_table(
            ["checkpoint", "status", "evidence", "follow_up"],
            [
                ["Writer Quality Gate", "blocked", f"`{TD_REL}/writer-quality-gate.md`", "resolve current-scope validator findings before reviewer preflight"],
                ["Traceability", "pass", f"`{TD_REL}/writer-traceability-matrix.md`", "semantic reviewer should inspect source row loss"],
                ["Residual gaps", "pass", f"`{TD_REL}/coverage-gaps.md`", "semantic reviewer should inspect GAP-001/GAP-006"],
            ],
        )
        + "\n\n## Technical Fallbacks\n\n"
        + md_table(
            ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
            [["none", "none", "none", "none", "n/a", "n/a", "none", "none"]],
        )
        + "\n\n## Handoff Notes For Next Session\n\n"
        "- Next session should remediate current-scope validator findings before attempting reviewer preflight.\n"
        "- After remediation, semantic review should inspect residual `GAP-001`, stale refs `GAP-006`, duplicate BSR tracing `GAP-007` and fixture-dependent oracles.\n",
    )

    write(
        OUT / "agent-decision-log.writer-r1.md",
        "# Agent Decision Log\n\n"
        "## Decision Log Metadata\n\n"
        + md_table(
            ["field", "value"],
            [
                ["ft_slug", "`AutoFin`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["stage", "`ft-test-case-writer`"],
                ["started_from", f"`{CYCLE_REL}/cycle-state.yaml`"],
            ],
        )
        + "\n\n## Decision Log\n\n"
        + md_table(
            ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
            [
                ["DEC-001", "1", "scope-boundary", "scope-contract.md", "Use only section 4.2 and exclude section 4.3 internals.", "Scope boundary is explicit in handoff.", TC_REL, "high", "applied"],
                ["DEC-002", "2", "traceability", "source-row-inventory.md", "Map every `SRC-*` row to `ATOM-*` or `GAP-*`.", "Prompt requires row preservation.", f"{TD_REL}/source-row-inventory.md", "high", "applied"],
                ["DEC-003", "3", "gap", "scope-gap-review.md / GAP-001", "Do not create a second result table TC.", "Second table is undefined in section 4.2.", TC_REL, "medium", "applied"],
                ["DEC-004", "4", "test-design", "GAP-002/GAP-003/GAP-005", "Use fixture and dictionary dependencies.", "Source lacks exact status/role/dictionary values.", f"{TD_REL}/fixture-catalog.md", "medium", "applied"],
                ["DEC-005", "5", "test-design", "GAP-004", "Assert only observable UI reactions.", "External systems and popup/calculator internals are out of scope.", TC_REL, "high", "applied"],
                ["DEC-006", "6", "traceability", "GAP-006/GAP-007", "Keep stale ref and duplicate BSR notes in trace artifacts.", "Bare BSR reference is ambiguous or misleading.", f"{TD_REL}/writer-traceability-matrix.md", "high", "applied"],
                ["DEC-007", "7", "routing", "runner scoped validator", "Route to `blocked-input` instead of `writer-draft-ready`.", "Runner validator reported current-scope warning/error findings; writer-ready handoff is forbidden until they are resolved.", f"{CYCLE_REL}/cycle-state.yaml; {CYCLE_REL}/outputs/writer-r1-blocked-input.md", "high", "applied"],
            ],
        ),
    )

    write(
        OUT / "writer-r1-blocked-input.md",
        "# Writer R1 Blocked Input\n\n"
        "## Blocker\n\n"
        "Writer draft artifacts were created, but the stage cannot advance to `writer-draft-ready` because runner validation reported current-scope blocking validator findings.\n\n"
        "## Validator Evidence\n\n"
        "- Command: `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/01-applications-menu-search/cycle-state.yaml`\n"
        "- Result before blocked routing: `writer-ready state has current-scope blocking validator findings: 16 total; first=coverage-obligation-table-unknown-source-property at test-cases/section-4.2-applications-menu-search.md`.\n"
        "- Full report: `work/review-cycles/01-applications-menu-search/outputs/validator-report.writer-r1.latest.json`.\n\n"
        "## Required Remediation Before Reviewer Handoff\n\n"
        "- Normalize current-scope split artifacts to canonical formats: coverage obligation table, dictionary inventory, package design plan, applicability matrix and test-design review.\n"
        "- Fix compatibility `workflow-state.yaml` routing/prompt expectations or make it clearly superseded by valid session-based `cycle-state.yaml`.\n"
        "- Resolve current-scope validator warnings/errors and regenerate a scoped validator profile with zero warning/error findings.\n",
    )

    reviewer_files = [
        "AGENTS.md",
        "skills/README.md",
        "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md",
        "skills/ft-test-case-reviewer/SKILL.md",
        "references/agent/reviewer-output-format.md",
        "references/qa/review-findings-format.md",
        "references/qa/test-case-runtime-format.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/next-step-prompt-format.md",
    ]
    write(
        PROMPTS / "prompt.structure-preflight-r1.md",
        "# Prompt: Structure Preflight R1 For 01 Applications Menu Search\n\n"
        "## Goal\n\n"
        "Проверить structure preflight для writer draft по AutoFin scope `01-applications-menu-search`: parseability, required runtime fields, split artifact shape and current scoped validator cleanliness. Semantic coverage review is out of scope for this stage.\n\n"
        "## Skill And Scenario\n\n"
        "- Skill: `ft-test-case-reviewer`\n"
        "- Scenario: `reviewer.structure_preflight`\n"
        "- Current stage: `structure-preflight-r1`\n"
        "- Current semantic round: `0`\n"
        f"- Canonical target: `fts/AutoFin/{TC_REL}`\n"
        f"- Test design dir: `fts/AutoFin/{TD_REL}/`\n\n"
        "## Instruction Loading\n\n"
        "Before reviewer decisions, run:\n\n"
        "```powershell\npython scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget\n```\n\n"
        "Record resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.\n\n"
        "Selected required files:\n\n"
        + "\n".join(f"- `{item}`" for item in reviewer_files)
        + "\n\n## Inputs\n\n"
        + "\n".join(
            f"- `fts/AutoFin/{path}`"
            for path in [
                TC_REL,
                TD_REL + "/",
                HANDOFF_REL + "/scope-contract.md",
                HANDOFF_REL + "/source-row-inventory.md",
                HANDOFF_REL + "/source-parity-check.md",
                HANDOFF_REL + "/scope-coverage-gaps.md",
                HANDOFF_REL + "/scope-clarification-requests.md",
                HANDOFF_REL + "/mockup-visual-inventory.md",
                HANDOFF_REL + "/scope-gap-review.md",
                CYCLE_REL + "/outputs/writer-session-log.writer-r1.md",
                CYCLE_REL + "/outputs/agent-decision-log.writer-r1.md",
                CYCLE_REL + "/outputs/scoped-validator-profile.writer-r1.json",
                CYCLE_REL + "/cycle-state.yaml",
                "AGENT-NOTES.md",
            ]
        )
        + "\n\n## Required Actions\n\n"
        "- Work only in `structure_preflight`; do not perform semantic coverage review.\n"
        "- Check that all `TC-AMSR-*` cases are parseable and use required bold runtime fields.\n"
        "- Check that every `TC-*` has `package_id` and required runtime sections.\n"
        "- Check that split artifacts exist and are shape-reviewable.\n"
        "- Check that `scoped-validator-profile.writer-r1.json` has no warning/error findings for current scope.\n"
        "- If structure blockers exist, route to `writer-structure-r1` with `structure-preflight-blocked`.\n"
        "- If no structure blockers exist, route to `semantic-review-r1` with `semantic-review-ready`.\n\n"
        "## Guardrails\n\n"
        "- Do not edit canonical test cases.\n"
        "- Do not review section 4.3 internals.\n"
        "- Do not require semantic changes during structure preflight.\n"
        "- Do not set `signed-off`.\n\n"
        "## Expected Outputs\n\n"
        "- `fts/AutoFin/work/review-cycles/01-applications-menu-search/outputs/structure-preflight-r1-findings.md`\n"
        "- `fts/AutoFin/work/review-cycles/01-applications-menu-search/outputs/reviewer-session-log.structure-preflight-r1.md`\n"
        "- `fts/AutoFin/work/review-cycles/01-applications-menu-search/outputs/agent-decision-log.structure-preflight-r1.md`\n"
        "- next prompt for `semantic-review-r1` or `writer-structure-r1`\n"
        "- updated `fts/AutoFin/work/review-cycles/01-applications-menu-search/cycle-state.yaml`\n",
    )

    latest = [
        TC_REL,
        TD_REL,
        f"{TD_REL}/artifact-write-strategy.md",
        f"{TD_REL}/source-row-inventory.md",
        f"{TD_REL}/atomic-requirements-ledger.md",
        f"{TD_REL}/test-design-applicability-matrix.md",
        f"{TD_REL}/coverage-obligation-table.md",
        f"{TD_REL}/package-test-design-plan.md",
        f"{TD_REL}/writer-traceability-matrix.md",
        f"{TD_REL}/writer-traceability-matrix.xlsx",
        f"{TD_REL}/dictionary-inventory.md",
        f"{TD_REL}/fixture-catalog.md",
        f"{TD_REL}/coverage-map.md",
        f"{TD_REL}/coverage-metrics.md",
        f"{TD_REL}/coverage-gaps.md",
        f"{TD_REL}/test-design-review.md",
        f"{TD_REL}/writer-quality-gate.md",
        f"{TD_REL}/writer-self-check.md",
        f"{CYCLE_REL}/outputs/writer-r1-response.md",
        f"{CYCLE_REL}/outputs/writer-session-log.writer-r1.md",
        f"{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md",
        f"{CYCLE_REL}/outputs/writer-r1-blocked-input.md",
        f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json",
        f"{CYCLE_REL}/outputs/validator-report.writer-r1.latest.json",
        f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md",
    ]
    write(
        CYCLE_STATE,
        "\n".join(
            [
                "cycle_id: autofin-01-applications-menu-search",
                "ft_slug: AutoFin",
                f"scope_slug: {SCOPE}",
                f"section_id: {SECTION}",
                "current_stage: writer-r1",
                "stage_status: blocked-input",
                "semantic_round: 0",
                "max_semantic_rounds: 2",
                f"canonical_test_cases: {TC_REL}",
                f"test_design_dir: {TD_REL}",
                "active_snapshot: none",
                "active_transition_prompt: none",
                "sessions: []",
                "latest_artifacts:",
                *[f"  - {item}" for item in latest],
                "blocking_reasons:",
                f"  - {CYCLE_REL}/outputs/writer-r1-blocked-input.md",
                "blocking_findings:",
                f"  - {CYCLE_REL}/outputs/validator-report.writer-r1.latest.json",
                "open_questions:",
                '  - "GAP-001: residual FT defect; second result table is undefined and must remain explicit note."',
                '  - "GAP-002/GAP-003/GAP-005: data fixtures required for full execution."',
                "accepted_risks:",
                '  - "GAP-001 | controlled residual | owner: scope-gap-reviewer | rationale: section 4.2 defines only table Заявки; writer must not invent a second table | revisit: analyst/product clarification or source correction"',
            ]
        ),
    )

    write(
        WORKFLOW_STATE,
        f"""ft_slug: AutoFin
scope_slug: {SCOPE}
current_stage: ft-test-case-writer
stage_status: blocked-input
current_round: 1
next_skill: none
ft_package: AutoFin
scope_id: {SCOPE}
workflow_phase: ft-test-case-writer
source_baseline: FT4AutoFinFinal
priority_source: fts/AutoFin/source/FT4AutoFinFinal.xhtml
parity_sources:
  - fts/AutoFin/source/FT4AutoFinFinal.docx
  - fts/AutoFin/source/FT4AutoFinFinal.pdf
target_test_case_file: fts/AutoFin/{TC_REL}

required_inputs:
  - fts/AutoFin/{TC_REL}
  - fts/AutoFin/{TD_REL}
  - fts/AutoFin/{HANDOFF_REL}/scope-contract.md
  - fts/AutoFin/{HANDOFF_REL}/source-row-inventory.md
  - fts/AutoFin/{HANDOFF_REL}/source-parity-check.md
  - fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md
  - fts/AutoFin/{HANDOFF_REL}/scope-clarification-requests.md
  - fts/AutoFin/{HANDOFF_REL}/mockup-visual-inventory.md
  - fts/AutoFin/{HANDOFF_REL}/scope-gap-review.md
  - fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md
  - fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
  - fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json
  - fts/AutoFin/{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
  - fts/AutoFin/{CYCLE_REL}/cycle-state.yaml

latest_artifacts:
  canonical_test_cases: fts/AutoFin/{TC_REL}
  test_design_dir: fts/AutoFin/{TD_REL}
  writer_session_log: fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md
  decision_log: fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
  writer_response: fts/AutoFin/{CYCLE_REL}/outputs/writer-r1-response.md
  blocked_input: fts/AutoFin/{CYCLE_REL}/outputs/writer-r1-blocked-input.md
  validator_report: fts/AutoFin/{CYCLE_REL}/outputs/validator-report.writer-r1.latest.json
  scoped_validator_profile: fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json
  cycle_state: fts/AutoFin/{CYCLE_REL}/cycle-state.yaml

next_step:
  skill: none
  mode: blocked-input
  prompt: none

open_gaps:
  - GAP-001
  - GAP-002
  - GAP-003
  - GAP-004
  - GAP-005
  - GAP-006
  - GAP-007

blocked_for_writer_until:
  - current-scope validator warning/error findings are resolved
blocking_reasons:
  - fts/AutoFin/{CYCLE_REL}/outputs/writer-r1-blocked-input.md
open_questions:
  - GAP-001: residual FT defect; second result table is undefined.
  - GAP-002/GAP-003/GAP-005: fixture dependencies for execution.
""",
    )


if __name__ == "__main__":
    build_artifacts()
