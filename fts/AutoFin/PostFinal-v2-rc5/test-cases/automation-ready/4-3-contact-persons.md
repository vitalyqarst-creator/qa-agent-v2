# Automation-ready: 4-3-contact-persons

> Источник baseline: `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-contact-persons.md`.
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

# Тест-кейсы: 4-3-contact-persons

## Suite Metadata

- **suite_readiness:** ft-first-reviewed-with-calibration-pending
- **test_case_count:** 38
- **execution_ready_count:** 27
- **calibration_candidate_count:** 11
- **review_basis:** immutable attempt 20260724-170052-4-3-contact-persons; reviewer verdict changes-required due UI calibration pending.
- **production_promotion:** not-performed; non_promotable_reason=calibration-pending.


## TC-CP-AD5F4C7217

**Название:** При нажатии на виджет добавления ниже добавляется строка для ввода данных по иному контактному лицу
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-187-ADD-ROW; ATOM-024; ASSERT-024; BSR 187; OBL-BSR-189-DELETE-ROW; ATOM-027; ASSERT-027; BSR 189

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать виджет добавления контактного лица.

### Итоговый ожидаемый результат

Строкой ниже добавляется возможность ввода данных по иному контактному лицу.

### Постусловия

- Для добавленной тестовой строки выполнить действие: Нажать кнопку `Корзина` соответствующей строки.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-069C73C682

**Название:** При нажатии на кнопку `Корзина` соответствующая строка контактного лица удаляется
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-189-DELETE-ROW; ATOM-027; ASSERT-027; BSR 189; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.
3. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Первая тестовая строка: первая по порядку.
- Вторая тестовая строка: вторая по порядку.

### Шаги

1. Для первой тестовой строки выполнить действие: Нажать кнопку `Корзина` соответствующей строки.

### Итоговый ожидаемый результат

Соответствующая строка контактного лица удаляется.

### Постусловия

- Для оставшейся второй тестовой строки выполнить действие: Нажать кнопку `Корзина` соответствующей строки.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Удаление строки выполнять кликом по delete/trash control в строке. Confirmation dialog в UI pass не появлялся; условные шаги подтверждения не добавлять.

## TC-CP-59FA884A01

**Название:** При удалении контактного лица удаляется соответствующая строка со всеми полями блока, включая Ф.И.О., отношение к заявителю, Телефон, Дата рождения и кнопку `Корзина` этой строки
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-189-DELETE-FULL-CONTACT-ROW; ATOM-028; ASSERT-028; BSR 189; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.
3. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Первая тестовая строка: первая по порядку.
- Вторая тестовая строка: вторая по порядку.

### Шаги

1. Для первой тестовой строки выполнить действие: Нажать кнопку `Корзина` для соответствующей строки.

### Итоговый ожидаемый результат

Соответствующая строка со всеми полями блока удаляется: Ф.И.О., отношение к заявителю, Телефон, Дата рождения и кнопка `Корзина` этой строки. Виджет `+ Добавить контактное лицо` остаётся доступным.

### Постусловия

- Для оставшейся второй тестовой строки выполнить действие: Нажать кнопку `Корзина` для соответствующей строки.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Удаление строки выполнять кликом по delete/trash control в строке. Confirmation dialog в UI pass не появлялся; условные шаги подтверждения не добавлять.

## TC-CP-1031D2F0FF

**Название:** Отображение: «Корзина»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-188-BASKET-VISIBLE-WITH-REPEATER; ATOM-026; ASSERT-026; BSR 188; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить наблюдаемое состояние: Кнопка `Корзина` отображается.

### Итоговый ожидаемый результат

Кнопка `Корзина` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-547CF72DA6

**Название:** При добавлении контактного лица добавляется строка со всеми полями блока, включая Ф.И.О., отношение к заявителю, Телефон, Дата рождения, а виджет `+ Добавить контактное лицо` является действием добавления контактного лица
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187; OBL-BSR-189-DELETE-ROW; ATOM-027; ASSERT-027; BSR 189

### Предусловия

1. Открыть карточку `Заявка` и перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать виджет `+ Добавить контактное лицо`.

### Итоговый ожидаемый результат

Ниже добавляется строка со всеми полями блока: Ф.И.О., отношение к заявителю, Телефон, Дата рождения и кнопка `Корзина` для этой строки. Виджет `+ Добавить контактное лицо` остаётся доступным.

### Постусловия

- Для добавленной тестовой строки выполнить действие: Нажать кнопку `Корзина` соответствующей строки.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-3C9ECFD5DC

**Название:** Отображение: «Добавить контактное лицо»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-186-ADD-BUTTON-ALWAYS-VISIBLE; ATOM-023; ASSERT-023; BSR 186; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187; OBL-BSR-189-DELETE-ROW; ATOM-027; ASSERT-027; BSR 189

### Предусловия

1. Открыть карточку `Заявка` и перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка`.
2. Проверить исходное состояние: Кнопка `Добавить контактное лицо` отображается.
3. Нажать виджет `+ Добавить контактное лицо`.
4. Проверить состояние после перехода: Кнопка `Добавить контактное лицо` отображается.

### Итоговый ожидаемый результат

Кнопка `Добавить контактное лицо` отображается.

### Постусловия

- Для добавленной тестовой строки выполнить действие: Нажать кнопку `Корзина` соответствующей строки.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-3D0077E42F

**Название:** Состав списка: «Отношение к заявителю»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-006-RELATION-DICTIONARY; ATOM-014; ASSERT-014; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Полный перечень: `супруг/супруга`, `отец/мать`, `сестра/брат`, `теща/свекровь/тесть/свекр`, `сын/дочь`, `друг/знакомый/коллега`, `иное`.

### Шаги

1. Открыть раскрывающийся список `Отношение к заявителю`.

### Итоговый ожидаемый результат

Список содержит полный перечень значений: `супруг/супруга`, `отец/мать`, `сестра/брат`, `теща/свекровь/тесть/свекр`, `сын/дочь`, `друг/знакомый/коллега`, `иное`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-B78F72E22B

**Название:** Если в поле `Отношение к заявителю` выбрано `Иное`, дополнительно отображается текстовое поле ввода
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-180-OTHER-TEXT-INPUT; ATOM-015; ASSERT-015; BSR 180; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `Иное`.

### Шаги

1. Выбрать `Иное` в раскрывающемся списке.

### Итоговый ожидаемый результат

После выбора `иное` дополнительно отображается поле ввода типа `текст`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** mismatch-ft-ui
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Expected по ФТ сохраняется: после выбора `иное` должно появиться дополнительное текстовое поле.

**FT/UI Divergence:** UI pass 2026-07-30: после выбора `иное` дополнительное поле не появилось; это дефект реализации, не корректировка expected result.

## TC-CP-A84688D4DB

**Название:** Поле `Отношение к заявителю` является редактируемым
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-006-RELATION-EDITABLE; ATOM-038; ASSERT-038; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `Иное`.

### Шаги

1. Ввести или изменить значение поля `Отношение к заявителю`; использовать значение `Иное`.

### Итоговый ожидаемый результат

Поле `Отношение к заявителю` доступно для редактирования.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-6560C2E054

**Название:** Поле `Отношение к заявителю` является обязательным после добавления контактного лица
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-006-RELATION-REQUIRED-AFTER-ADD; ATOM-032; ASSERT-032; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-REQ-004

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Контрольное значение: `пустое значение`.
- Отношение к заявителю: оставить пустым.

### Шаги

1. Оставить поле `Отношение к заявителю` пустым.
2. Ввести `Петров-Бояров` в поле `Фамилия`.
3. Ввести `Иван` в поле `Имя`.
4. Ввести `9991234567` в поле `Телефон`.
5. Указать `30.07.2000` в поле `Дата рождения`.
6. Нажать кнопку `ДАЛЕЕ`.
7. Проверить состояние поля `Отношение к заявителю`.

### Итоговый ожидаемый результат

После запуска проверки обязательности пустое поле `Отношение к заявителю` не принимается как valid; поле находится в required/invalid state. Для полей ФИО при наличии сообщения проверять `Выберите значение`; для остальных полей точный текст сообщения не является обязательным oracle.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-05637FFFE5

**Название:** Отображение: «Отношение к заявителю»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-179-DEFAULT-HIDDEN; ATOM-012; ASSERT-012; BSR 179

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка` без нажатия `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Отношение к заявителю` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-254BA94E1D

**Название:** Отображение: «Отношение к заявителю»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-179-VISIBLE-AFTER-ADD; ATOM-013; ASSERT-013; BSR 179; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Отношение к заявителю` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-43B1FF4F19

**Название:** Значение по умолчанию: «Телефон»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-183-PHONE-DEFAULT-MASK; ATOM-019; ASSERT-019; BSR 183; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Ожидаемое значение: `+7 (___) ___-__-__`.

### Шаги

1. Нажать на «Телефон».
2. После нажатия проверить наблюдаемое состояние: Отображается шаблон `+7 (___) ___-__-__`, курсор расположен внутри скобок.

### Итоговый ожидаемый результат

Отображается шаблон `+7 (___) ___-__-__`, курсор расположен внутри скобок.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-B01529711C

**Название:** Ввод допустимого значения: «Телефон»
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-182-PHONE-10-DIGITS; ATOM-018; ASSERT-018; BSR 182; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-NEG-008; SO-NEG-009; SO-NEG-010; SO-NEG-011

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Допустимое значение: `9991234567`.
- Короткое значение: `999123456`.
- Значение с лишней цифрой: `99912345678`.
- Значение с буквой: `99912A4567`.
- Значение с пробелом: `99912 4567`.

### Шаги

1. Ввести `9991234567` в поле `Телефон`, убрать фокус и проверить отображаемое значение.
2. Очистить поле `Телефон`.
3. Ввести `999123456` в поле `Телефон`, убрать фокус и проверить очистку/invalid state.
4. Очистить поле `Телефон`.
5. Ввести `99912345678` в поле `Телефон`, убрать фокус и проверить отображаемое значение.
6. Очистить поле `Телефон`.
7. Ввести `99912A4567` в поле `Телефон`, убрать фокус и проверить очистку/invalid state.
8. Очистить поле `Телефон`.
9. Ввести `99912 4567` в поле `Телефон`, убрать фокус и проверить очистку/invalid state.

### Итоговый ожидаемый результат

`9991234567` отображается как `+7 (999) 123-45-67` и не находится в invalid state. `99912345678` также отображается как `+7 (999) 123-45-67`, лишняя цифра игнорируется маской. `999123456`, `99912A4567` и `99912 4567` после blur очищаются и приводят поле к required/invalid state.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Phone mask behavior подтверждено UI: extra digit ignored/truncated, short/mixed values clear on blur.

## TC-CP-3921E86CCA

**Название:** Поле `Телефон` является редактируемым
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-007-PHONE-EDITABLE; ATOM-039; ASSERT-039; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `9991234567`.

### Шаги

1. Ввести или изменить значение поля `Телефон`; использовать значение `9991234567`.

### Итоговый ожидаемый результат

Поле `Телефон` доступно для редактирования.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-C76A595256

**Название:** Поле `Телефон` является обязательным после добавления контактного лица
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-007-PHONE-REQUIRED-AFTER-ADD; ATOM-033; ASSERT-033; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-REQ-005

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Контрольное значение: `пустое значение`.
- Телефон: оставить пустым.

### Шаги

1. Оставить поле `Телефон` пустым.
2. Выбрать `супруг/супруга` в поле `Отношение к заявителю`.
3. Ввести `Петров-Бояров` в поле `Фамилия`.
4. Ввести `Иван` в поле `Имя`.
5. Указать `30.07.2000` в поле `Дата рождения`.
6. Нажать кнопку `ДАЛЕЕ`.
7. Проверить состояние поля `Телефон`.

### Итоговый ожидаемый результат

После запуска проверки обязательности пустое поле `Телефон` не принимается как valid; поле находится в required/invalid state. Для полей ФИО при наличии сообщения проверять `Выберите значение`; для остальных полей точный текст сообщения не является обязательным oracle.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-216EC18624

**Название:** Отображение: «Телефон»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-181-DEFAULT-HIDDEN; ATOM-016; ASSERT-016; BSR 181

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка` без нажатия `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Телефон` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-2CBD2F1BE6

**Название:** Отображение: «Телефон»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-181-VISIBLE-AFTER-ADD; ATOM-017; ASSERT-017; BSR 181; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Телефон` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-BF2F522CE8

**Название:** Ввод допустимого значения: «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-176-TEXT-HYPHEN; ATOM-008; ASSERT-008; BSR 176; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-NEG-003; SO-NEG-004

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Допустимое воспроизводимое значение: `Иван`.

### Шаги

1. Ввести `Иван` в поле `Имя`.
2. Убрать фокус с поля `Имя`.
3. Проверить отображаемое значение и состояние поля.

### Итоговый ожидаемый результат

Поле `Имя` отображает значение `Иван` после blur и не находится в invalid state.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для имени контактного лица использовать воспроизводимое значение `Иван`; значение retained after blur.

## TC-CP-FD0866A774

**Название:** Поле `Имя` является редактируемым
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-004-FIRST-NAME-EDITABLE; ATOM-036; ASSERT-036; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `Иван-Петров`.

### Шаги

1. Ввести или изменить значение поля `Имя`; использовать значение `Иван-Петров`.

### Итоговый ожидаемый результат

Поле `Имя` доступно для редактирования.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-116443D9EB

**Название:** Поле `Имя` является обязательным после добавления контактного лица
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-004-FIRST-NAME-REQUIRED-AFTER-ADD; ATOM-030; ASSERT-030; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-REQ-002

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Контрольное значение: `пустое значение`.
- Имя: оставить пустым.

### Шаги

1. Оставить поле `Имя` пустым.
2. Выбрать `супруг/супруга` в поле `Отношение к заявителю`.
3. Ввести `Петров-Бояров` в поле `Фамилия`.
4. Ввести `9991234567` в поле `Телефон`.
5. Указать `30.07.2000` в поле `Дата рождения`.
6. Нажать кнопку `ДАЛЕЕ`.
7. Проверить состояние поля `Имя`.

### Итоговый ожидаемый результат

После запуска проверки обязательности пустое поле `Имя` не принимается как valid; поле находится в required/invalid state. Для полей ФИО при наличии сообщения проверять `Выберите значение`; для остальных полей точный текст сообщения не является обязательным oracle.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-D49350060B

**Название:** Отображение: «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-175-DEFAULT-HIDDEN; ATOM-006; ASSERT-006; BSR 175

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка` без нажатия `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Имя` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-443F3F4189

**Название:** Отображение: «Имя»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-175-VISIBLE-AFTER-ADD; ATOM-007; ASSERT-007; BSR 175; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Имя` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-351CD544DE

**Название:** Ввод допустимого значения: «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-174-TEXT-HYPHEN; ATOM-005; ASSERT-005; BSR 174; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-NEG-001; SO-NEG-002

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Допустимое воспроизводимое значение: `Петров-Бояров`.

### Шаги

1. Ввести `Петров-Бояров` в поле `Фамилия`.
2. Убрать фокус с поля `Фамилия`.
3. Проверить отображаемое значение и состояние поля.

### Итоговый ожидаемый результат

Поле `Фамилия` отображает значение `Петров-Бояров` после blur и не находится в invalid state.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для фамилии контактного лица использовать воспроизводимое значение `Петров-Бояров`; manual input and dropdown selection retained after blur.

## TC-CP-1E7C130DD4

**Название:** Поле `Фамилия` является редактируемым
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-003-FAMILY-EDITABLE; ATOM-035; ASSERT-035; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `Иван-Петров`.

### Шаги

1. Ввести или изменить значение поля `Фамилия`; использовать значение `Иван-Петров`.

### Итоговый ожидаемый результат

Поле `Фамилия` доступно для редактирования.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-C0C583C405

**Название:** Поле `Фамилия` является обязательным после добавления контактного лица
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-003-FAMILY-REQUIRED-AFTER-ADD; ATOM-029; ASSERT-029; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-REQ-001

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Контрольное значение: `пустое значение`.
- Фамилия: оставить пустым.

### Шаги

1. Оставить поле `Фамилия` пустым.
2. Выбрать `супруг/супруга` в поле `Отношение к заявителю`.
3. Ввести `Иван` в поле `Имя`.
4. Ввести `9991234567` в поле `Телефон`.
5. Указать `30.07.2000` в поле `Дата рождения`.
6. Нажать кнопку `ДАЛЕЕ`.
7. Проверить состояние поля `Фамилия`.

### Итоговый ожидаемый результат

После запуска проверки обязательности пустое поле `Фамилия` не принимается как valid; поле находится в required/invalid state. Для полей ФИО при наличии сообщения проверять `Выберите значение`; для остальных полей точный текст сообщения не является обязательным oracle.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-382F750F94

**Название:** Отображение: «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-173-DEFAULT-HIDDEN; ATOM-003; ASSERT-003; BSR 173

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка` без нажатия `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Фамилия` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-2DD9D4E006

**Название:** Отображение: «Фамилия»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-173-VISIBLE-AFTER-ADD; ATOM-004; ASSERT-004; BSR 173; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Фамилия` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-C5BCDBF312

**Название:** Ввод допустимого значения: «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-178-TEXT-HYPHEN; ATOM-011; ASSERT-011; BSR 178; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-NEG-005; SO-NEG-006

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Допустимое воспроизводимое значение: `Иванович`.

### Шаги

1. Ввести `Иванович` в поле `Отчество`.
2. Убрать фокус с поля `Отчество`.
3. Проверить отображаемое значение и состояние поля.

### Итоговый ожидаемый результат

Поле `Отчество` отображает значение `Иванович` после blur и не находится в invalid state.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Для отчества контактного лица использовать воспроизводимое значение `Иванович`; значение retained after blur.

## TC-CP-23A987DEFD

**Название:** Поле `Отчество` является редактируемым
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-005-PATRONYMIC-EDITABLE; ATOM-037; ASSERT-037; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `Иван-Петров`.

### Шаги

1. Ввести или изменить значение поля `Отчество`; использовать значение `Иван-Петров`.

### Итоговый ожидаемый результат

Поле `Отчество` доступно для редактирования.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-FD0683A355

**Название:** Поле `Отчество` не является обязательным
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-005-PATRONYMIC-NOT-REQUIRED; ATOM-031; ASSERT-031; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-REQ-003

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Контрольное значение: `пустое значение`.
- Отчество: оставить пустым.

### Шаги

1. Выбрать `супруг/супруга` в поле `Отношение к заявителю`.
2. Ввести `Петров-Бояров` в поле `Фамилия`.
3. Ввести `Иван` в поле `Имя`.
4. Ввести `9991234567` в поле `Телефон`.
5. Указать `30.07.2000` в поле `Дата рождения`.
6. Оставить поле `Отчество` пустым.
7. Нажать кнопку `ДАЛЕЕ`.
8. Проверить состояние поля `Отчество`.

### Итоговый ожидаемый результат

Поле `Отчество` не имеет required marker; пустое значение не переводит поле в required/invalid state.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-AB0B41DC31

**Название:** Отображение: «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-177-DEFAULT-HIDDEN; ATOM-009; ASSERT-009; BSR 177

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка` без нажатия `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Отчество` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-9CF13C2E86

**Название:** Отображение: «Отчество»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-177-VISIBLE-AFTER-ADD; ATOM-010; ASSERT-010; BSR 177; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Отчество` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-7EC8C7FA5A

**Название:** Дата рождения контактного лица не может быть больше текущей даты
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-185-BIRTHDATE-NOT-FUTURE; ATOM-022; ASSERT-022; BSR 185; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-NEG-013

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Недопустимое значение даты больше текущей даты: `D+1`.

### Шаги

1. Выбрать `супруг/супруга` в поле `Отношение к заявителю`.
2. Ввести `Петров-Бояров` в поле `Фамилия`.
3. Ввести `Иван` в поле `Имя`.
4. Ввести `9991234567` в поле `Телефон`.
5. Указать `31.07.2026` в поле `Дата рождения`.
6. Убрать фокус с поля `Дата рождения`.
7. Проверить состояние поля `Дата рождения`.
8. Очистить поле `Дата рождения`.
9. Указать `30.07.2000` в поле `Дата рождения`.
10. Убрать фокус с поля `Дата рождения`.
11. Проверить состояние поля `Дата рождения`.

### Итоговый ожидаемый результат

Будущая дата `31.07.2026` остаётся отображенной в поле `Дата рождения`, но поле находится в invalid state. Для контрольного валидного значения `30.07.2000` поле не находится в invalid state.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-F374C4FBF7

**Название:** Поле `Дата рождения` является редактируемым
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-008-BIRTHDATE-EDITABLE; ATOM-040; ASSERT-040; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Тестовое значение: `2000-01-01`.

### Шаги

1. Ввести или изменить значение поля `Дата рождения`; использовать значение `2000-01-01`.

### Итоговый ожидаемый результат

Поле `Дата рождения` доступно для редактирования.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-30984FE5C2

**Название:** Поле `Дата рождения` является обязательным после добавления контактного лица
**Тип:** негативный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-SRC-ROW-008-BIRTHDATE-REQUIRED-AFTER-ADD; ATOM-034; ASSERT-034; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** automation-ready
**scope_obligation_id:** SO-REQ-006

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

- Контрольное значение: `пустое значение`.
- Дата рождения: оставить пустым.

### Шаги

1. Оставить поле `Дата рождения` пустым.
2. Выбрать `супруг/супруга` в поле `Отношение к заявителю`.
3. Ввести `Петров-Бояров` в поле `Фамилия`.
4. Ввести `Иван` в поле `Имя`.
5. Ввести `9991234567` в поле `Телефон`.
6. Нажать кнопку `ДАЛЕЕ`.
7. Проверить состояние поля `Дата рождения`.

### Итоговый ожидаемый результат

После запуска проверки обязательности пустое поле `Дата рождения` не принимается как valid; поле находится в required/invalid state. Для полей ФИО при наличии сообщения проверять `Выберите значение`; для остальных полей точный текст сообщения не является обязательным oracle.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-36147078D3

**Название:** Отображение: «Дата рождения»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-184-DEFAULT-HIDDEN; ATOM-020; ASSERT-020; BSR 184

### Предусловия

1. Перейти к блоку `Контактные лица`.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть карточку `Заявка` без нажатия `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Дата рождения` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CP-FEEAF4F60E

**Название:** Отображение: «Дата рождения»
**Тип:** позитивный
**Приоритет:** средний
**package_id:** 4-3-contact-persons
**Трассировка:** OBL-BSR-184-VISIBLE-AFTER-ADD; ATOM-021; ASSERT-021; BSR 184; OBL-BSR-187-ADD-FULL-CONTACT-ROW; ATOM-025; ASSERT-025; BSR 187

### Предусловия

1. Перейти к блоку `Контактные лица`.
2. Нажать виджет `+ Добавить контактное лицо`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить контактное лицо`.

### Итоговый ожидаемый результат

Поле `Дата рождения` отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/three-files-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`
- evidence commit: `2ed11a295467d6beba1809f8395a340c3921b87c`

**Automation Notes:** Кейс включён в automation-ready на основании UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.
