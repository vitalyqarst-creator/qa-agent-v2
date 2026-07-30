# Automation-ready: 4-3-personal-data

> Источник baseline: `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-personal-data.md`.
> UI evidence: `origin/codex/postfinal-v2-rc5-three-files-ui-pass`, commit `2ed11a295467d6beba1809f8395a340c3921b87c`.
> Automation-ready версия не заменяет FT-first baseline и отражает executable UI flow по результатам UI pass 2026-07-30 и последующих owner clarifications.

## Общие предусловия для автоматизации

1. Открыть тестовый стенд AutoFin.
2. После входа выбрать строку `cff` на launch screen и нажать `ЗАПУСТИТЬ`.
3. В списке заявок нажать `СОЗДАТЬ ЗАЯВКУ`.
4. Убедиться, что открыта карточка `Заявка`.

## Общие automation notes

- Базовое предусловие каждого кейса: открыта карточка `Заявка`; автоматизатор сам выбирает стратегию создания/очистки заявки.
- Baseline test-cases в `test-cases/` не изменяются.
- Если в кейсе указана DaData-подсказка, automation вводит значение медленно, ждёт `li.ui-menu-item`, выбирает exact option и только затем делает blur/assert.
- Для masked inputs использовать keyboard/type, затем blur. Не использовать raw value injection, если нужно проверить работу маски.
- UI evidence paths указывают на артефакты из evidence branch; в этой ветке automation-ready файлы ссылаются на них как на опубликованный источник UI pass.

# Тест-кейсы: Карточка «Заявка» / Блок «Персональные данные»

> Статус: канонический baseline.
> Основание: source gate `v52`, source assertion review `v32`, prepared package `WP-01-r19`.
> UI evidence используется только как подтверждение наблюдаемых состояний полей; расхождения по BSR 54/BSR 63 зафиксированы как дефекты реализации и не меняют ожидаемые результаты, выведенные из ФТ.

## Общие примечания

- Проверки DaData по ФИО используют подготовленные selected-suggestion фикстуры; точный состав, порядок, количество подсказок, debounce, текст no-match и поведение фокуса не проверяются в этом baseline.
- Интеграция с АБС пока не реализована; `TC-PERSON-009` оставлен как `blocked-not-implemented / skip` до реализации интеграции и oracle в списке заявок.
- Для проверок предыдущего ФИО после `Клиент менял ФИО` = `Да` переход всей карточки не утверждается, потому что его могут блокировать другие обязательные поля.

## TC-PERSON-001

**№:** 1
**Название:** Состав списка «Пол»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-012; ATOM-PERSON-012; ASSERT-PERSON-012; BSR 58

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Полный перечень: `Мужской`, `Женский`.

### Шаги

1. Открыть список `Пол`.
2. Сверить отображаемые значения с полным перечнем из тестовых данных.
3. Проверить отсутствие дополнительных значений.

### Итоговый ожидаемый результат

Список содержит только значения `Мужской` и `Женский`.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-002

**№:** 2
**Название:** Заполнение поля «Пол» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-013; ATOM-PERSON-013; ASSERT-PERSON-013; BSR 59

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-GENDER-FEMALE-001`.
- Запрос: `Иванова`.
- Подсказка: `Иванова Анна Сергеевна`.
- Компонент `gender`: `Женский`.
- Компонент `name`: `Анна`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Иванова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-GENDER-MALE-001`.
- Запрос: `Иванов`.
- Подсказка: `Иванов Иван Сергеевич`.
- Компонент `gender`: `Мужской`.
- Компонент `name`: `Иван`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Иванов`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. Ввести запрос `Иванова` в поле ФИО и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванова Анна Сергеевна`.
2. Проверить значение поля `Пол`.
3. Начать изолированный прогон с исходными предусловиями.
4. Ввести запрос `Иванов` в поле ФИО и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванов Иван Сергеевич`.
5. Проверить значение поля `Пол`.

### Итоговый ожидаемый результат

После выбора `Иванова Анна Сергеевна` поле `Пол` содержит `Женский`; после выбора `Иванов Иван Сергеевич` поле `Пол` содержит `Мужской`.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-003

**№:** 3
**Название:** Значение по умолчанию переключателя «Клиент менял ФИО»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-019; ATOM-PERSON-019; ASSERT-PERSON-019; BSR 65

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Ожидаемое значение: `Нет`.

### Шаги

1. Не взаимодействуя с переключателем `Клиент менял ФИО`, проверить его первоначальное значение.

### Итоговый ожидаемый результат

Для переключателя `Клиент менял ФИО` выбрано значение `Нет`.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-004

**№:** 4
**Название:** Отображение переключателя «Клиент менял ФИО»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-018; ATOM-PERSON-018; ASSERT-PERSON-018; BSR 64

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Найти переключатель `Клиент менял ФИО`.

### Итоговый ожидаемый результат

Переключатель `Клиент менял ФИО` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-005

**№:** 5
**Название:** Заполнение поля «Имя» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-006; ATOM-PERSON-006; ASSERT-PERSON-006; BSR 52

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-CURRENT-FEMALE-001`.
- Запрос: `Иванова`.
- Подсказка: `Иванова Анна Сергеевна`.
- Компонент `gender`: `Женский`.
- Компонент `name`: `Анна`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Иванова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-CURRENT-MALE-001`.
- Запрос: `Иванов`.
- Подсказка: `Иванов Иван Сергеевич`.
- Компонент `gender`: `Мужской`.
- Компонент `name`: `Иван`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Иванов`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. В поле `Имя` ввести запрос `Иванова` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванова Анна Сергеевна`.
2. Проверить значение поля `Имя`.
3. Начать изолированный прогон с исходными предусловиями.
4. В поле `Имя` ввести запрос `Иванов` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванов Иван Сергеевич`.
5. Проверить значение поля `Имя`.

### Итоговый ожидаемый результат

После выбора `Иванова Анна Сергеевна` поле `Имя` содержит `Анна`; после выбора `Иванов Иван Сергеевич` — `Иван`. Количество, порядок и полный состав подсказок не проверяются.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-006

**№:** 6
**Название:** Недопустимые классы символов в поле «Имя»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-005; ATOM-PERSON-005; ASSERT-PERSON-005; BSR 51

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое значение: `Иванов Петров`.
- Недопустимое значение: `Иванов1`.
- Недопустимое значение: `Иванов@`.

### Шаги

1. Ввести `Иванов Петров` в поле `Имя`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
2. Очистить поле `Имя`.
3. Ввести `Иванов1` в поле `Имя`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
4. Очистить поле `Имя`.
5. Ввести `Иванов@` в поле `Имя`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Для каждого значения при вводе поле `Имя` содержит введённый текст, находится в состоянии `invalid` и показывает сообщение `Введено некорректное значение`. После потери фокуса поле пустое, сообщение отсутствует; после нажатия `ДАЛЕЕ` поле остаётся пустым.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-007

**№:** 7
**Название:** Допустимые классы символов в поле «Имя»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-005; ATOM-PERSON-005; ASSERT-PERSON-005; BSR 51

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Допустимое значение: `Анна`.
- Допустимое значение: `Анна-Мария`.
- Допустимое значение: `Anna-Maria`.

### Шаги

1. Медленно ввести проверяемое значение в целевое поле.
2. Если UI показывает dropdown `li.ui-menu-item`, выбрать exact matching option.
3. Убрать фокус с поля.
4. Проверить отображаемое значение и состояние поля.
5. Очистить поле перед следующим значением.

### Итоговый ожидаемый результат

Выбранное из dropdown или retained после blur значение отображается в целевом поле и не находится в invalid state. Automation не утверждает стабильную валидность simple fill+blur без выбранной подсказки DaData.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для positive FIO automation не утверждать stable valid state после simple fill+blur; если появляется dropdown, выбирать exact option и проверять retained value after blur.

## TC-PERSON-008

**№:** 8
**Название:** Отображение поля «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-004; ATOM-PERSON-004; ASSERT-PERSON-004; BSR 50

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Найти поле `Имя`.

### Итоговый ожидаемый результат

Поле `Имя` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-009

**№:** 9
**Название:** Автоматическое заполнение поля «ID клиента» после сохранения заявки
**Тип:** интеграционный / skipped until ABS implementation
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-011; ATOM-PERSON-011; ASSERT-PERSON-011; BSR 57; SO-CAL-E12B69C290053EA0
**Статус oracle:** blocked-not-implemented

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Интеграция с АБС пока не реализована.
- До реализации АБС кейс не исполняется в автоматизации.
- После реализации АБС ожидаемый oracle: после сохранения карточки заявки с заполненными обязательными полями перейти к списку заявок и проверить, что у созданной заявки в столбце `ID клиента` заполнено значение.

### Шаги

1. До реализации АБС пометить автотест как skipped.
2. После реализации АБС заполнить обязательные поля карточки заявки валидными значениями.
3. Сохранить карточку заявки согласованным безопасным способом.
4. Перейти к списку заявок.
5. Найти созданную заявку.
6. Проверить значение в столбце `ID клиента`.

### Итоговый ожидаемый результат

До реализации АБС автотест пропущен со статусом `blocked-not-implemented`. После реализации АБС в списке заявок у созданной заявки в столбце `ID клиента` отображается заполненное значение согласованного формата.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** blocked-observability
**Automation Execution Status:** blocked-not-implemented / skip
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** АБС не реализована. Автотест должен быть skipped до появления safe save path, формата `ID клиента` и oracle в списке заявок.

## TC-PERSON-010

**№:** 10
**Название:** Отображение поля «ID клиента»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-010; ATOM-PERSON-010; ASSERT-PERSON-010; BSR 56

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Найти поле `ID клиента`.

### Итоговый ожидаемый результат

Поле `ID клиента` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-011

**№:** 11
**Название:** Заполнение поля «Предыдущее отчество» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-031; ATOM-PERSON-031; ASSERT-PERSON-031; BSR 77

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-PREVIOUS-FEMALE-001`.
- Запрос: `Петрова`.
- Подсказка: `Петрова Мария Сергеевна`.
- Компонент `name`: `Мария`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Петрова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-PREVIOUS-MALE-001`.
- Запрос: `Петров`.
- Подсказка: `Петров Петр Сергеевич`.
- Компонент `name`: `Петр`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Петров`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. В поле `Предыдущее отчество` ввести запрос `Петрова` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Петрова Мария Сергеевна`.
2. Проверить значение поля `Предыдущее отчество`.
3. Начать изолированный прогон с исходными предусловиями.
4. В поле `Предыдущее отчество` ввести запрос `Петров` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Петров Петр Сергеевич`.
5. Проверить значение поля `Предыдущее отчество`.

### Итоговый ожидаемый результат

После выбора `Петрова Мария Сергеевна` поле `Предыдущее отчество` содержит `Сергеевна`; после выбора `Петров Петр Сергеевич` — `Сергеевич`. Количество, порядок и полный состав подсказок не проверяются.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-012

**№:** 12
**Название:** Недопустимые классы символов в поле «Предыдущее отчество»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-029; ATOM-PERSON-029; ASSERT-PERSON-029; BSR 75

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Недопустимое значение: `Петрова Сидорова`.
- Недопустимое значение: `Петрова1`.
- Недопустимое значение: `Петрова@`.

### Шаги

1. Ввести `Петрова Сидорова` в поле `Предыдущее отчество`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
2. Очистить поле `Предыдущее отчество`.
3. Ввести `Петрова1` в поле `Предыдущее отчество`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
4. Очистить поле `Предыдущее отчество`.
5. Ввести `Петрова@` в поле `Предыдущее отчество`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Для каждого значения при вводе поле `Предыдущее отчество` содержит введённый текст, находится в состоянии `invalid` и показывает сообщение `Введено некорректное значение`. После потери фокуса поле пустое, сообщение отсутствует; после нажатия `ДАЛЕЕ` поле остаётся пустым.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-013

**№:** 13
**Название:** Допустимые классы символов в поле «Предыдущее отчество»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-029; ATOM-PERSON-029; ASSERT-PERSON-029; BSR 75

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Допустимое значение: `Мария`.
- Допустимое значение: `Мария-Сергеевна`.
- Допустимое значение: `Maria-Sergeevna`.

### Шаги

1. Медленно ввести проверяемое значение в целевое поле.
2. Если UI показывает dropdown `li.ui-menu-item`, выбрать exact matching option.
3. Убрать фокус с поля.
4. Проверить отображаемое значение и состояние поля.
5. Очистить поле перед следующим значением.

### Итоговый ожидаемый результат

Выбранное из dropdown или retained после blur значение отображается в целевом поле и не находится в invalid state. Automation не утверждает стабильную валидность simple fill+blur без выбранной подсказки DaData.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для positive FIO automation не утверждать stable valid state после simple fill+blur; если появляется dropdown, выбирать exact option и проверять retained value after blur.

## TC-PERSON-014

**№:** 14
**Название:** Участие поля «Предыдущее отчество» в обязательности группы предыдущего ФИО
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-030; ATOM-PERSON-030; ASSERT-PERSON-030; BSR 76

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Предыдущее отчество: оставить пустым.

### Шаги

1. Оставить все поля предыдущего ФИО пустыми.
2. Нажать `ДАЛЕЕ` и проверить поле `Предыдущее отчество` и состояние карточки.
3. Начать изолированный прогон с исходными предусловиями.
4. Ввести `Сергеевна` в поле `Предыдущее отчество`.
5. Нажать `ДАЛЕЕ` и проверить отсутствие сообщения у поля `Предыдущее отчество`.

### Итоговый ожидаемый результат

Когда все поля предыдущего ФИО пусты, у поля `Предыдущее отчество` отображается сообщение `Выберите значение`, а карточка остаётся открытой. После ввода `Сергеевна` это сообщение у поля отсутствует; переход всей карточки не проверяется, поскольку его могут блокировать другие обязательные поля.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-015

**№:** 15
**Название:** Отображение поля «Предыдущее отчество» при изменении ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-028; ATOM-PERSON-028; ASSERT-PERSON-028; BSR 74

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Установить переключатель `Клиент менял ФИО` в значение `Да`.
2. Найти поле `Предыдущее отчество`.

### Итоговый ожидаемый результат

После выбора значения `Да` поле `Предыдущее отчество` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-016

**№:** 16
**Название:** Заполнение поля «Предыдущее имя» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-027; ATOM-PERSON-027; ASSERT-PERSON-027; BSR 73

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-PREVIOUS-FEMALE-001`.
- Запрос: `Петрова`.
- Подсказка: `Петрова Мария Сергеевна`.
- Компонент `name`: `Мария`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Петрова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-PREVIOUS-MALE-001`.
- Запрос: `Петров`.
- Подсказка: `Петров Петр Сергеевич`.
- Компонент `name`: `Петр`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Петров`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. В поле `Предыдущее имя` ввести запрос `Петрова` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Петрова Мария Сергеевна`.
2. Проверить значение поля `Предыдущее имя`.
3. Начать изолированный прогон с исходными предусловиями.
4. В поле `Предыдущее имя` ввести запрос `Петров` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Петров Петр Сергеевич`.
5. Проверить значение поля `Предыдущее имя`.

### Итоговый ожидаемый результат

После выбора `Петрова Мария Сергеевна` поле `Предыдущее имя` содержит `Мария`; после выбора `Петров Петр Сергеевич` — `Петр`. Количество, порядок и полный состав подсказок не проверяются.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-017

**№:** 17
**Название:** Недопустимые классы символов в поле «Предыдущее имя»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-025; ATOM-PERSON-025; ASSERT-PERSON-025; BSR 71

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Недопустимое значение: `Петрова Сидорова`.
- Недопустимое значение: `Петрова1`.
- Недопустимое значение: `Петрова@`.

### Шаги

1. Ввести `Петрова Сидорова` в поле `Предыдущее имя`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
2. Очистить поле `Предыдущее имя`.
3. Ввести `Петрова1` в поле `Предыдущее имя`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
4. Очистить поле `Предыдущее имя`.
5. Ввести `Петрова@` в поле `Предыдущее имя`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Для каждого значения при вводе поле `Предыдущее имя` содержит введённый текст, находится в состоянии `invalid` и показывает сообщение `Введено некорректное значение`. После потери фокуса поле пустое, сообщение отсутствует; после нажатия `ДАЛЕЕ` поле остаётся пустым.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-018

**№:** 18
**Название:** Допустимые классы символов в поле «Предыдущее имя»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-025; ATOM-PERSON-025; ASSERT-PERSON-025; BSR 71

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Допустимое значение: `Мария`.
- Допустимое значение: `Мария-Сергеевна`.
- Допустимое значение: `Maria-Sergeevna`.

### Шаги

1. Медленно ввести проверяемое значение в целевое поле.
2. Если UI показывает dropdown `li.ui-menu-item`, выбрать exact matching option.
3. Убрать фокус с поля.
4. Проверить отображаемое значение и состояние поля.
5. Очистить поле перед следующим значением.

### Итоговый ожидаемый результат

Выбранное из dropdown или retained после blur значение отображается в целевом поле и не находится в invalid state. Automation не утверждает стабильную валидность simple fill+blur без выбранной подсказки DaData.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для positive FIO automation не утверждать stable valid state после simple fill+blur; если появляется dropdown, выбирать exact option и проверять retained value after blur.

## TC-PERSON-019

**№:** 19
**Название:** Участие поля «Предыдущее имя» в обязательности группы предыдущего ФИО
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-026; ATOM-PERSON-026; ASSERT-PERSON-026; BSR 72

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Предыдущее имя: оставить пустым.

### Шаги

1. Оставить все поля предыдущего ФИО пустыми.
2. Нажать `ДАЛЕЕ` и проверить поле `Предыдущее имя` и состояние карточки.
3. Начать изолированный прогон с исходными предусловиями.
4. Ввести `Петр` в поле `Предыдущее имя`.
5. Нажать `ДАЛЕЕ` и проверить отсутствие сообщения у поля `Предыдущее имя`.

### Итоговый ожидаемый результат

Когда все поля предыдущего ФИО пусты, у поля `Предыдущее имя` отображается сообщение `Выберите значение`, а карточка остаётся открытой. После ввода `Петр` это сообщение у поля отсутствует; переход всей карточки не проверяется, поскольку его могут блокировать другие обязательные поля.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-020

**№:** 20
**Название:** Отображение поля «Предыдущее имя» при изменении ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-024; ATOM-PERSON-024; ASSERT-PERSON-024; BSR 70

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Установить переключатель `Клиент менял ФИО` в значение `Да`.
2. Найти поле `Предыдущее имя`.

### Итоговый ожидаемый результат

После выбора значения `Да` поле `Предыдущее имя` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-021

**№:** 21
**Название:** Заполнение поля «Фамилия» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-003; ATOM-PERSON-003; ASSERT-PERSON-003; BSR 49

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-CURRENT-FEMALE-001`.
- Запрос: `Иванова`.
- Подсказка: `Иванова Анна Сергеевна`.
- Компонент `gender`: `Женский`.
- Компонент `name`: `Анна`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Иванова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-CURRENT-MALE-001`.
- Запрос: `Иванов`.
- Подсказка: `Иванов Иван Сергеевич`.
- Компонент `gender`: `Мужской`.
- Компонент `name`: `Иван`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Иванов`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. В поле `Фамилия` ввести запрос `Иванова` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванова Анна Сергеевна`.
2. Проверить значение поля `Фамилия`.
3. Начать изолированный прогон с исходными предусловиями.
4. В поле `Фамилия` ввести запрос `Иванов` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванов Иван Сергеевич`.
5. Проверить значение поля `Фамилия`.

### Итоговый ожидаемый результат

После выбора `Иванова Анна Сергеевна` поле `Фамилия` содержит `Иванова`; после выбора `Иванов Иван Сергеевич` — `Иванов`. Количество, порядок и полный состав подсказок не проверяются.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-022

**№:** 22
**Название:** Недопустимые классы символов в поле «Фамилия»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-002; ATOM-PERSON-002; ASSERT-PERSON-002; BSR 48

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое значение: `Иванов Петров`.
- Недопустимое значение: `Иванов1`.
- Недопустимое значение: `Иванов@`.

### Шаги

1. Ввести `Иванов Петров` в поле `Фамилия`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
2. Очистить поле `Фамилия`.
3. Ввести `Иванов1` в поле `Фамилия`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
4. Очистить поле `Фамилия`.
5. Ввести `Иванов@` в поле `Фамилия`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Для каждого значения при вводе поле `Фамилия` содержит введённый текст, находится в состоянии `invalid` и показывает сообщение `Введено некорректное значение`. После потери фокуса поле пустое, сообщение отсутствует; после нажатия `ДАЛЕЕ` поле остаётся пустым.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-023

**№:** 23
**Название:** Допустимые классы символов в поле «Фамилия»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-002; ATOM-PERSON-002; ASSERT-PERSON-002; BSR 48

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Допустимое значение: `Анна`.
- Допустимое значение: `Анна-Мария`.
- Допустимое значение: `Anna-Maria`.

### Шаги

1. Медленно ввести проверяемое значение в целевое поле.
2. Если UI показывает dropdown `li.ui-menu-item`, выбрать exact matching option.
3. Убрать фокус с поля.
4. Проверить отображаемое значение и состояние поля.
5. Очистить поле перед следующим значением.

### Итоговый ожидаемый результат

Выбранное из dropdown или retained после blur значение отображается в целевом поле и не находится в invalid state. Automation не утверждает стабильную валидность simple fill+blur без выбранной подсказки DaData.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для positive FIO automation не утверждать stable valid state после simple fill+blur; если появляется dropdown, выбирать exact option и проверять retained value after blur.

## TC-PERSON-024

**№:** 24
**Название:** Отображение поля «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-001; ATOM-PERSON-001; ASSERT-PERSON-001; BSR 47

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Найти поле `Фамилия`.

### Итоговый ожидаемый результат

Поле `Фамилия` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-025

**№:** 25
**Название:** Заполнение поля «Отчество» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-009; ATOM-PERSON-009; ASSERT-PERSON-009; BSR 55

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-CURRENT-FEMALE-001`.
- Запрос: `Иванова`.
- Подсказка: `Иванова Анна Сергеевна`.
- Компонент `gender`: `Женский`.
- Компонент `name`: `Анна`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Иванова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-CURRENT-MALE-001`.
- Запрос: `Иванов`.
- Подсказка: `Иванов Иван Сергеевич`.
- Компонент `gender`: `Мужской`.
- Компонент `name`: `Иван`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Иванов`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. В поле `Отчество` ввести запрос `Иванова` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванова Анна Сергеевна`.
2. Проверить значение поля `Отчество`.
3. Начать изолированный прогон с исходными предусловиями.
4. В поле `Отчество` ввести запрос `Иванов` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Иванов Иван Сергеевич`.
5. Проверить значение поля `Отчество`.

### Итоговый ожидаемый результат

После выбора `Иванова Анна Сергеевна` поле `Отчество` содержит `Сергеевна`; после выбора `Иванов Иван Сергеевич` — `Сергеевич`. Количество, порядок и полный состав подсказок не проверяются.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-026

**№:** 26
**Название:** Недопустимые классы символов в поле «Отчество»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-008; ATOM-PERSON-008; ASSERT-PERSON-008; BSR 54

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое значение: `Иванов Петров`.
- Недопустимое значение: `Иванов1`.
- Недопустимое значение: `Иванов@`.

### Шаги

1. Ввести `Иванов Петров` в поле `Отчество`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
2. Очистить поле `Отчество`.
3. Ввести `Иванов1` в поле `Отчество`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
4. Очистить поле `Отчество`.
5. Ввести `Иванов@` в поле `Отчество`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Для каждого значения при вводе поле `Отчество` содержит введённый текст, находится в состоянии `invalid` и показывает сообщение `Введено некорректное значение`. После потери фокуса поле пустое, сообщение отсутствует; после нажатия `ДАЛЕЕ` поле остаётся пустым.

Примечание: UI evidence от 30.07.2026 показывал сохранение сообщения для текущего `Отчество` после blur/`ДАЛЕЕ`; по пользовательскому уточнению это дефект реализации, а ожидаемое поведение должно быть аналогично полям `Фамилия` и `Имя`.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-027

**№:** 27
**Название:** Допустимые классы символов в поле «Отчество»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-008; ATOM-PERSON-008; ASSERT-PERSON-008; BSR 54

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Допустимое значение: `Анна`.
- Допустимое значение: `Анна-Мария`.
- Допустимое значение: `Anna-Maria`.

### Шаги

1. Медленно ввести проверяемое значение в целевое поле.
2. Если UI показывает dropdown `li.ui-menu-item`, выбрать exact matching option.
3. Убрать фокус с поля.
4. Проверить отображаемое значение и состояние поля.
5. Очистить поле перед следующим значением.

### Итоговый ожидаемый результат

Выбранное из dropdown или retained после blur значение отображается в целевом поле и не находится в invalid state. Automation не утверждает стабильную валидность simple fill+blur без выбранной подсказки DaData.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для positive FIO automation не утверждать stable valid state после simple fill+blur; если появляется dropdown, выбирать exact option и проверять retained value after blur.

## TC-PERSON-028

**№:** 28
**Название:** Отображение поля «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-007; ATOM-PERSON-007; ASSERT-PERSON-007; BSR 53

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Найти поле `Отчество`.

### Итоговый ожидаемый результат

Поле `Отчество` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-029

**№:** 29
**Название:** Дата рождения на один день раньше 100-летней границы
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-017; ATOM-PERSON-017; ASSERT-PERSON-017; BSR 63

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое граничное условие: `<текущая дата> - 100 лет - 1 день`.

### Шаги

1. Зафиксировать текущую дату выполнения проверки.
2. Рассчитать дату по условию `<текущая дата> - 100 лет - 1 день`.
3. Ввести рассчитанную дату в поле `Дата рождения`.
4. Нажать `ДАЛЕЕ` и проверить значение и состояние поля.

### Итоговый ожидаемый результат

Рассчитанная дата остается в поле `Дата рождения`, поле находится в состоянии `invalid`. Точный текст сообщения под полем не проверяется.

Примечание: Если на стенде 30.07.2026 значение `29.07.1926` принимается как `valid`, это дефект реализации, а не корректировка ожидаемого результата.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** mismatch-ft-ui
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DOB boundary оставлен по owner clarification: 18 лет включительно, дата рождения должна быть строго позднее 100-летней границы.

**FT/UI Divergence:** На стенде 30.07.2026 UI принял значения на/старше 100-летней границы как valid и отклонил exact 18th birthday; это дефект реализации, не изменение expected result.

## TC-PERSON-030

**№:** 30
**Название:** Дата рождения на один день позже 18-летней границы
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-015; ATOM-PERSON-015; ASSERT-PERSON-015; BSR 61

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое граничное условие: `<текущая дата> - 18 лет + 1 день`.

### Шаги

1. Зафиксировать текущую дату выполнения проверки.
2. Рассчитать дату по условию `<текущая дата> - 18 лет + 1 день`.
3. Ввести рассчитанную дату в поле `Дата рождения`.
4. Нажать `ДАЛЕЕ` и проверить значение, состояние поля и наличие сообщения.

### Итоговый ожидаемый результат

Рассчитанная дата остаётся в поле `Дата рождения`, поле находится в состоянии `invalid`, сообщение под полем отсутствует.

Примечание: Если стенд принимает значение младше 18 лет как валидное, это дефект реализации; тест-кейс остается корректным относительно BSR 61.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-031

**№:** 31
**Название:** Дата рождения ровно на 100-летней границе
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-017; ATOM-PERSON-017; ASSERT-PERSON-017; BSR 63

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое граничное условие: `<текущая дата> - 100 лет`.

### Шаги

1. Зафиксировать текущую дату выполнения проверки.
2. Рассчитать дату по условию `<текущая дата> - 100 лет`.
3. Ввести рассчитанную дату в поле `Дата рождения`.
4. Убрать фокус с поля и проверить отображаемое значение.

### Итоговый ожидаемый результат

Рассчитанная дата остаётся в поле `Дата рождения`, поле находится в состоянии `invalid`. Точный текст сообщения под полем не проверяется.

Примечание: по owner clarification минимально допустимая дата рождения должна быть строго позднее 100-летней границы; на стенде 30.07.2026 значение `30.07.1926` должно отклоняться.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** mismatch-ft-ui
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DOB boundary оставлен по owner clarification: 18 лет включительно, дата рождения должна быть строго позднее 100-летней границы.

**FT/UI Divergence:** На стенде 30.07.2026 UI принял значения на/старше 100-летней границы как valid и отклонил exact 18th birthday; это дефект реализации, не изменение expected result.

## TC-PERSON-032

**№:** 32
**Название:** Дата рождения на 18-летней границе
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-015; ATOM-PERSON-015; ASSERT-PERSON-015; BSR 61

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Допустимое граничное условие: `<текущая дата> - 18 лет`.

### Шаги

1. Зафиксировать текущую дату выполнения проверки.
2. Рассчитать дату по условию `<текущая дата> - 18 лет`.
3. Ввести рассчитанную дату в поле `Дата рождения`.
4. Убрать фокус с поля и проверить отображаемое значение.

### Итоговый ожидаемый результат

Поле `Дата рождения` отображает рассчитанную граничную дату и не находится в invalid state.

Примечание: по owner clarification минимальный возраст 18 лет включительно; на стенде 30.07.2026 значение `30.07.2008` должно приниматься как valid.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** mismatch-ft-ui
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DOB boundary оставлен по owner clarification: 18 лет включительно, дата рождения должна быть строго позднее 100-летней границы.

**FT/UI Divergence:** На стенде 30.07.2026 UI принял значения на/старше 100-летней границы как valid и отклонил exact 18th birthday; это дефект реализации, не изменение expected result.

## TC-PERSON-033

**№:** 33
**Название:** Будущая дата в поле «Дата рождения»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-016; ATOM-PERSON-016; ASSERT-PERSON-016; BSR 62

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Недопустимое значение больше текущей даты: `текущая дата + 1 день`.

### Шаги

1. Зафиксировать текущую дату выполнения проверки и рассчитать `текущая дата + 1 день`.
2. Ввести рассчитанное значение `текущая дата + 1 день` в поле `Дата рождения`.
3. Нажать `ДАЛЕЕ`.
4. Проверить значение, состояние поля и наличие сообщения.
5. Очистить поле `Дата рождения`.

### Итоговый ожидаемый результат

Будущая дата остаётся в поле `Дата рождения`, поле находится в состоянии `required invalid`, сообщение под полем отсутствует. Значение одновременно нарушает ограничение минимального возраста, поэтому эта проверка не изолирует причины невалидности.

Примечание: Значение `текущая дата + 1 день` одновременно нарушает ограничение BSR 61, поэтому тест фиксирует состояние поля и не изолирует причину невалидности только как BSR 62.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-034

**№:** 34
**Название:** Отображение дат, не превышающих текущую дату, в поле «Дата рождения»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-016; ATOM-PERSON-016; ASSERT-PERSON-016; BSR 62

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

- Допустимое граничное значение: `текущая дата - 1 день`.
- Допустимое граничное значение: `текущая дата`.

### Шаги

1. Зафиксировать текущую дату выполнения проверки и рассчитать `текущая дата - 1 день`.
2. Ввести рассчитанное значение `текущая дата - 1 день` в поле `Дата рождения` и проверить отображаемое значение.
3. Очистить поле `Дата рождения`.
4. Ввести рассчитанное значение `текущая дата` в поле `Дата рождения` и проверить отображаемое значение.

### Итоговый ожидаемый результат

Поле `Дата рождения` отображает введенные значения, которые не превышают текущую дату. Тест не утверждает общую валидность этих дат по возрастным ограничениям BSR 61/BSR 63.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-035

**№:** 35
**Название:** Отображение поля «Дата рождения»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-014; ATOM-PERSON-014; ASSERT-PERSON-014; BSR 60

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Найти поле `Дата рождения`.

### Итоговый ожидаемый результат

Поле `Дата рождения` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-036

**№:** 36
**Название:** Заполнение поля «Предыдущая фамилия» по выбранной подсказке DaData
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-023; ATOM-PERSON-023; ASSERT-PERSON-023; BSR 69

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-PREVIOUS-FEMALE-001`.
- Запрос: `Петрова`.
- Подсказка: `Петрова Мария Сергеевна`.
- Компонент `name`: `Мария`.
- Компонент `patronymic`: `Сергеевна`.
- Компонент `surname`: `Петрова`.
- Результат фикстуры: `prepared-suggestion-selected`.
- Фикстура DaData: `FX-DADATA-FIO-SUGGESTION-PREVIOUS-MALE-001`.
- Запрос: `Петров`.
- Подсказка: `Петров Петр Сергеевич`.
- Компонент `name`: `Петр`.
- Компонент `patronymic`: `Сергеевич`.
- Компонент `surname`: `Петров`.
- Результат фикстуры: `prepared-suggestion-selected`.

### Шаги

1. В поле `Предыдущая фамилия` ввести запрос `Петрова` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Петрова Мария Сергеевна`.
2. Проверить значение поля `Предыдущая фамилия`.
3. Начать изолированный прогон с исходными предусловиями.
4. В поле `Предыдущая фамилия` ввести запрос `Петров` и дождаться dropdown `li.ui-menu-item` и выбрать подсказку DaData `Петров Петр Сергеевич`.
5. Проверить значение поля `Предыдущая фамилия`.

### Итоговый ожидаемый результат

После выбора `Петрова Мария Сергеевна` поле `Предыдущая фамилия` содержит `Петрова`; после выбора `Петров Петр Сергеевич` — `Петров`. Количество, порядок и полный состав подсказок не проверяются.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** DaData/FIO positive flow: медленно вводить значение, дождаться `li.ui-menu-item`, выбрать exact option, затем blur. Simple fill+blur не использовать как positive oracle.

## TC-PERSON-037

**№:** 37
**Название:** Недопустимые классы символов в поле «Предыдущая фамилия»
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-021; ATOM-PERSON-021; ASSERT-PERSON-021; BSR 67

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Недопустимое значение: `Петрова Сидорова`.
- Недопустимое значение: `Петрова1`.
- Недопустимое значение: `Петрова@`.

### Шаги

1. Ввести `Петрова Сидорова` в поле `Предыдущая фамилия`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
2. Очистить поле `Предыдущая фамилия`.
3. Ввести `Петрова1` в поле `Предыдущая фамилия`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.
4. Очистить поле `Предыдущая фамилия`.
5. Ввести `Петрова@` в поле `Предыдущая фамилия`; проверить состояние при вводе, убрать фокус и нажать `ДАЛЕЕ`.

### Итоговый ожидаемый результат

Для каждого значения при вводе поле `Предыдущая фамилия` содержит введённый текст, находится в состоянии `invalid` и показывает сообщение `Введено некорректное значение`. После потери фокуса поле пустое, сообщение отсутствует; после нажатия `ДАЛЕЕ` поле остаётся пустым.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-038

**№:** 38
**Название:** Допустимые классы символов в поле «Предыдущая фамилия»
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-021; ATOM-PERSON-021; ASSERT-PERSON-021; BSR 67

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Допустимое значение: `Мария`.
- Допустимое значение: `Мария-Сергеевна`.
- Допустимое значение: `Maria-Sergeevna`.

### Шаги

1. Медленно ввести проверяемое значение в целевое поле.
2. Если UI показывает dropdown `li.ui-menu-item`, выбрать exact matching option.
3. Убрать фокус с поля.
4. Проверить отображаемое значение и состояние поля.
5. Очистить поле перед следующим значением.

### Итоговый ожидаемый результат

Выбранное из dropdown или retained после blur значение отображается в целевом поле и не находится в invalid state. Automation не утверждает стабильную валидность simple fill+blur без выбранной подсказки DaData.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для positive FIO automation не утверждать stable valid state после simple fill+blur; если появляется dropdown, выбирать exact option и проверять retained value after blur.

## TC-PERSON-039

**№:** 39
**Название:** Участие поля «Предыдущая фамилия» в обязательности группы предыдущего ФИО
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-022; ATOM-PERSON-022; ASSERT-PERSON-022; BSR 68

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.
3. Установить переключатель `Клиент менял ФИО` в значение `Да`.

### Тестовые данные

- Предыдущая фамилия: оставить пустым.

### Шаги

1. Оставить все поля предыдущего ФИО пустыми.
2. Нажать `ДАЛЕЕ` и проверить поле `Предыдущая фамилия` и состояние карточки.
3. Начать изолированный прогон с исходными предусловиями.
4. Ввести `Петрова` в поле `Предыдущая фамилия`.
5. Нажать `ДАЛЕЕ` и проверить отсутствие сообщения у поля `Предыдущая фамилия`.

### Итоговый ожидаемый результат

Когда все поля предыдущего ФИО пусты, у поля `Предыдущая фамилия` отображается сообщение `Выберите значение`, а карточка остаётся открытой. После ввода `Петрова` это сообщение у поля отсутствует; переход всей карточки не проверяется, поскольку его могут блокировать другие обязательные поля.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-PERSON-040

**№:** 40
**Название:** Отображение поля «Предыдущая фамилия» при изменении ФИО
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-01-r19
**Трассировка:** OBL-PERSON-020; ATOM-PERSON-020; ASSERT-PERSON-020; BSR 66

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Персональные данные`.

### Тестовые данные

Не требуются.

### Шаги

1. Установить переключатель `Клиент менял ФИО` в значение `Да`.
2. Найти поле `Предыдущая фамилия`.

### Итоговый ожидаемый результат

После выбора значения `Да` поле `Предыдущая фамилия` отображается.

### Постусловия

- Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.
