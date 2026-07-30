# Automation-ready: 4-3-client-contacts

> Источник baseline: `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-client-contacts.md`.
> UI evidence: `origin/codex/postfinal-v2-rc5-client-contacts-documents-ui-pass`, commit `acba6a3424e73010d5c3b7977e9169cc066b5fd6`.
> Automation-ready версия не заменяет FT-first baseline и отражает executable UI flow по результатам UI pass 2026-07-30.

## Suite Metadata

- **test_case_count:** 25
- **confirmed:** 23
- **mismatch-ft-ui:** 2
- **blocked-observability:** 0
- **status_adjustment:** `TC-CONTACT-008`, `TC-CONTACT-009`, `TC-CONTACT-016` переклассифицированы в `confirmed`, потому что фактическое UI-поведение совпадает с текущим baseline и более ранней UI-калибровкой.

## Общие предусловия для автоматизации

1. Открыть тестовый стенд AutoFin.
2. После входа выбрать строку `cff` на launch screen и нажать `ЗАПУСТИТЬ`.
3. В списке заявок нажать `СОЗДАТЬ ЗАЯВКУ`.
4. Убедиться, что открыта карточка `Заявка`.

## Общие automation notes

- Baseline test-cases в `test-cases/` не изменяются.
- Базовое предусловие каждого кейса: открыта карточка `Заявка`; автоматизатор сам выбирает стратегию создания/очистки заявки.
- Для masked phone inputs использовать keyboard/type и blur; не использовать raw value injection, если проверяется работа маски.
- Для добавленной строки телефона selector должен быть scoped to row/repeater; не смешивать основной `Мобильный телефон` с `Номер телефона` в повторителе.

# Тест-кейсы: Карточка «Заявка» / Блок «Контакты клиента»

## TC-CONTACT-001

**№:** 1
**Название:** Поле `Номер телефона` до добавления строки телефона не отображается
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-017; ATOM-CONTACT-017; ASSERT-CONTACT-017; BSR 168

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Не нажимая кнопку `Добавить телефон`, проверить наличие поля `Номер телефона`.

### Итоговый ожидаемый результат

Поле `Номер телефона` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-01-initial-final.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-002

**№:** 2
**Название:** Шаблон поля `Номер телефона` в добавленной строке
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-022; ATOM-CONTACT-022; ASSERT-CONTACT-022; BSR 170; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

Не требуются.

### Шаги

1. Не переводя фокус на поле `Номер телефона` и не взаимодействуя с ним, проверить его первоначальное отображение.

### Итоговый ожидаемый результат

В поле `Номер телефона` отображается шаблон с кодом страны `+7 (9xx) xxx-xx-xx`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** mismatch-ft-ui
**Automation Execution Status:** implementation-defect / expected-fail
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-02-after-add-phone-row.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Автоматизировать как known failing: на стенде initial template в добавленной строке не отображается до ввода/фокуса.

**FT/UI Divergence:** Baseline ожидает initial template `+7 (9xx) xxx-xx-xx` в добавленной строке `Номер телефона`; UI pass 2026-07-30 показал пустое `required/invalid` поле без шаблона до ввода/фокуса.

## TC-CONTACT-003

**№:** 3
**Название:** Отображение поля `Номер телефона` после добавления строки телефона
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-018; ATOM-CONTACT-018; ASSERT-CONTACT-018; BSR 168; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить телефон`.

### Итоговый ожидаемый результат

Появляется строка повторителя с полем `Номер телефона *`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-02-after-add-phone-row.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-004

**№:** 4
**Название:** Редактирование поля `Номер телефона`
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-020; ATOM-CONTACT-020; ASSERT-CONTACT-020; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Значение номера телефона: `9999999999`.

### Шаги

1. Ввести `9999999999` в поле `Номер телефона`.
2. Снять фокус с поля `Номер телефона`.

### Итоговый ожидаемый результат

В поле `Номер телефона` отображается `+7 (999) 999–99–99`; поле находится в состоянии `valid`, сообщение не отображается.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-row-phone-final-9999999999.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-006-OBS

**№:** 5
**Название:** Обработка значений со специальными символами в поле `Номер телефона`
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-021; ATOM-CONTACT-021; ASSERT-CONTACT-021; BSR 169; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** fully-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Проверяемые значения: `99912@4567`, `99912.4567`, `99912-4567`.

### Шаги

1. Очистить поле `Номер телефона`, ввести `99912@4567` и снять фокус с поля.
2. Проверить, что значение поля очищено и поле находится в состоянии `invalid/required/empty`.
3. Очистить поле `Номер телефона`, ввести `99912.4567` и снять фокус с поля.
4. Проверить, что значение поля очищено и поле находится в состоянии `invalid/required/empty`.
5. Очистить поле `Номер телефона`, ввести `99912-4567` и снять фокус с поля.
6. Проверить, что значение поля очищено и поле находится в состоянии `invalid/required/empty`.

### Итоговый ожидаемый результат

Для `99912@4567`, `99912.4567` и `99912-4567` поле `Номер телефона` в добавленной строке очищается после потери фокуса; валидная телефонная маска не остается; поле находится в состоянии `invalid/required/empty`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-row-phone-final-99912_4567.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Calibration resolved: для спецсимволов в добавленной строке проверять clear-on-blur и `invalid/required/empty`, без ожидания валидной маски.

## TC-CONTACT-006-NEG

**№:** 6
**Название:** Обработка недопустимых значений в поле `Номер телефона`
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-021; ATOM-CONTACT-021; ASSERT-CONTACT-021; BSR 169; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Проверяемые значения: `999123456`, `99912A4567`, `99912 4567`.

### Шаги

1. Очистить поле `Номер телефона`, ввести `999123456` и снять фокус с поля.
2. Проверить, что поле очищено и отображается сообщение `Обязательно к заполнению`.
3. Очистить поле `Номер телефона`, ввести `99912A4567` и снять фокус с поля.
4. Проверить, что поле очищено и отображается сообщение `Обязательно к заполнению`.
5. Очистить поле `Номер телефона`, ввести `99912 4567` и снять фокус с поля.
6. Проверить, что поле очищено и отображается сообщение `Обязательно к заполнению`.

### Итоговый ожидаемый результат

Для `999123456`, `99912A4567` и `99912 4567` поле очищается и отображается сообщение `Обязательно к заполнению`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-row-phone-final-999123456.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-006

**№:** 7
**Название:** Обработка допустимых числовых значений в поле `Номер телефона`
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-021; ATOM-CONTACT-021; ASSERT-CONTACT-021; BSR 169; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Проверяемые значения: `99912345678`, `9999999999`.

### Шаги

1. Очистить поле `Номер телефона`, ввести `99912345678` и снять фокус с поля.
2. Проверить, что отображается `+7 (999) 123–45–67`, поле находится в состоянии `valid`, а сообщение отсутствует.
3. Очистить поле `Номер телефона`, ввести `9999999999` и снять фокус с поля.
4. Проверить, что отображается `+7 (999) 999–99–99`, поле находится в состоянии `valid`, а сообщение отсутствует.

### Итоговый ожидаемый результат

Для `99912345678` отображается `+7 (999) 123–45–67`: лишний символ отброшен, поле находится в состоянии `valid`, сообщение отсутствует. Для `9999999999` отображается `+7 (999) 999–99–99`, поле находится в состоянии `valid`, сообщение отсутствует.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-row-phone-final-99912345678.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-005

**№:** 8
**Название:** Обязательность поля `Номер телефона` при выбранном типе телефона
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-026; ATOM-CONTACT-026; ASSERT-CONTACT-026; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Тип телефона: `Мобильный`.
- Номер телефона: оставить пустым.

### Шаги

1. Открыть раскрывающийся список `Тип телефона`.
2. Выбрать значение `Мобильный`.
3. Оставить поле `Номер телефона` пустым.
4. Перевести фокус с поля `Номер телефона` на поле `Тип телефона`.

### Итоговый ожидаемый результат

У поля `Номер телефона` установлен признак обязательности `required=true`; поле находится в состоянии `invalid required empty`, отображается сообщение `Обязательно к заполнению`. В поле `Тип телефона` остаётся значение `Мобильный`, поле находится в состоянии `valid`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-04-phone-type-selected.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-007

**№:** 9
**Название:** Редактирование поля `E-mail`
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-009; ATOM-CONTACT-009; ASSERT-CONTACT-009

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

- Значение E-mail: `one@example.ru`.

### Шаги

1. Ввести `one@example.ru` в поле `E-mail`.
2. Снять фокус с поля `E-mail`.

### Итоговый ожидаемый результат

В поле `E-mail` отображается `one@example.ru`; значение не очищается, сообщение не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-email-final-test_example_ru.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-008

**№:** 10
**Название:** Проверка E-mail без символа `@`
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-010; ATOM-CONTACT-010; ASSERT-CONTACT-010; BSR 166

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

- Значение E-mail без символа `@`: `testexample.ru`.

### Шаги

1. Очистить поле `E-mail`.
2. Ввести `testexample.ru` в поле `E-mail`.
3. Снять фокус с поля `E-mail`.

### Итоговый ожидаемый результат

Значение поля `E-mail` очищается; отдельное сообщение не отображается, признак обязательности у поля отсутствует.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-email-final-testexample_ru.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Фактическое UI-поведение совпадает с baseline: invalid e-mail без `@` очищается на blur без отдельного сообщения.

## TC-CONTACT-009

**№:** 11
**Название:** Запрет нескольких адресов в поле `E-mail`
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-011; ATOM-CONTACT-011; ASSERT-CONTACT-011; BSR 166

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

- Несколько адресов с разделителем `;`: `one@example.ru; two@example.ru`.
- Несколько адресов с разделителем `,`: `one@example.ru, two@example.ru`.

### Шаги

1. Очистить поле `E-mail`, ввести `one@example.ru; two@example.ru` и снять фокус с поля.
2. Проверить значение поля `E-mail`.
3. Очистить поле `E-mail`, ввести `one@example.ru, two@example.ru` и снять фокус с поля.
4. Проверить значение поля `E-mail`.

### Итоговый ожидаемый результат

После каждого ввода значение поля `E-mail` очищается; несколько адресов в одном поле не принимаются.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-email-final-first_example_ru_second_example_ru.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Фактическое UI-поведение совпадает с baseline: несколько e-mail в одном поле очищаются на blur.

## TC-CONTACT-010

**№:** 12
**Название:** Поле `E-mail` не является обязательным
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-008; ATOM-CONTACT-008; ASSERT-CONTACT-008

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

- E-mail: оставить пустым.

### Шаги

1. Оставить поле `E-mail` пустым.
2. Проверить наличие у поля признака обязательности.

### Итоговый ожидаемый результат

Поле `E-mail` не имеет признака обязательности.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-email-final-empty.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-011

**№:** 13
**Название:** Отображение поля `E-mail` до и после добавления строки телефона
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-007; ATOM-CONTACT-007; ASSERT-CONTACT-007; BSR 165; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля `E-mail` в блоке `Контакты клиента`.
2. Нажать кнопку `Добавить телефон`.
3. Повторно проверить отображение поля `E-mail`.

### Итоговый ожидаемый результат

Поле `E-mail` отображается как до, так и после добавления строки телефона.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-02-after-add-phone-row.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-012

**№:** 14
**Название:** Шаблон поля `Мобильный телефон` при первоначальном отображении
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-006; ATOM-CONTACT-006; ASSERT-CONTACT-006; BSR 164

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Не переводя фокус на поле `Мобильный телефон` и не взаимодействуя с ним, проверить его первоначальное отображение.

### Итоговый ожидаемый результат

В поле `Мобильный телефон` отображается шаблон с кодом страны `+7 (9xx) xxx-xx-xx`.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** mismatch-ft-ui
**Automation Execution Status:** implementation-defect / expected-fail
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-01-initial-final.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Автоматизировать как known failing: на стенде initial template основного `Мобильный телефон` не отображается до ввода/фокуса.

**FT/UI Divergence:** Baseline ожидает initial template `+7 (9xx) xxx-xx-xx` в основном поле `Мобильный телефон`; UI pass 2026-07-30 показал пустое `required/invalid` поле без шаблона до ввода/фокуса.

## TC-CONTACT-013

**№:** 15
**Название:** Редактирование поля `Мобильный телефон`
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-004; ATOM-CONTACT-004; ASSERT-CONTACT-004

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

- Значение мобильного телефона: `9991234567`.

### Шаги

1. Очистить поле `Мобильный телефон`.
2. Ввести `9991234567` в поле `Мобильный телефон`.
3. Снять фокус с поля `Мобильный телефон`.

### Итоговый ожидаемый результат

В поле `Мобильный телефон` отображается `+7 (999) 912–34–56`; поле находится в состоянии `valid`, сообщение не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-mobile-final-9991234567.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-014-OBS

**№:** 16
**Название:** Обработка значений со специальными символами в поле `Мобильный телефон`
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-005; ATOM-CONTACT-005; ASSERT-CONTACT-005; BSR 163
**Статус oracle:** observed-ui-backed
**Статус тест-кейса:** fully-ready

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Перевести фокус на поле `Мобильный телефон`.

### Тестовые данные

- Проверяемые значения: `99912@4567`, `99912.4567`, `99912-4567`.

### Шаги

1. Очистить поле `Мобильный телефон`, ввести `99912@4567` и снять фокус с поля.
2. Проверить, что отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, сообщение не отображается.
3. Очистить поле `Мобильный телефон`, ввести `99912.4567` и снять фокус с поля.
4. Проверить, что отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, сообщение не отображается.
5. Очистить поле `Мобильный телефон`, ввести `99912-4567` и снять фокус с поля.
6. Проверить, что отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, сообщение не отображается.

### Итоговый ожидаемый результат

Для `99912@4567`, `99912.4567` и `99912-4567` недопустимый символ фильтруется/игнорируется маской; в поле `Мобильный телефон` отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, сообщение не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-mobile-special-1.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Calibration resolved: для основного `Мобильный телефон` спецсимвол фильтруется/игнорируется, результат остается valid.

## TC-CONTACT-014

**№:** 17
**Название:** Нормализация допустимых значений в поле `Мобильный телефон`
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-005; ATOM-CONTACT-005; ASSERT-CONTACT-005; BSR 163

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Перевести фокус на поле `Мобильный телефон`.

### Тестовые данные

- Проверяемые значения: `999123456`, `99912345678`, `99912A4567`, `99912 4567`.

### Шаги

1. Очистить поле `Мобильный телефон`, ввести `999123456` и снять фокус с поля.
2. Проверить, что отображается `+7 (999) 912–34–56`, поле находится в состоянии `valid`, а сообщение отсутствует.
3. Очистить поле `Мобильный телефон`, ввести `99912345678` и снять фокус с поля.
4. Проверить, что отображается `+7 (999) 912–34–56`, поле находится в состоянии `valid`, а сообщение отсутствует.
5. Очистить поле `Мобильный телефон`, ввести `99912A4567` и снять фокус с поля.
6. Проверить, что отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, а сообщение отсутствует.
7. Очистить поле `Мобильный телефон`, ввести `99912 4567` и снять фокус с поля.
8. Проверить, что отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, а сообщение отсутствует.

### Итоговый ожидаемый результат

Для `999123456` отображается `+7 (999) 912–34–56`, поле находится в состоянии `valid`, сообщение отсутствует. Для `99912345678` лишний символ игнорируется, отображается `+7 (999) 912–34–56`, поле находится в состоянии `valid`, сообщение отсутствует. Для `99912A4567` и `99912 4567` недопустимый символ фильтруется, отображается `+7 (999) 912–45–67`, поле находится в состоянии `valid`, сообщение отсутствует.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-mobile-final-99912345678.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-015

**№:** 18
**Название:** Обязательность поля `Мобильный телефон`
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-003; ATOM-CONTACT-003; ASSERT-CONTACT-003

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

- Мобильный телефон: оставить пустым.

### Шаги

1. Оставить поле `Мобильный телефон` пустым.
2. Проверить признак обязательности и состояние поля `Мобильный телефон`.

### Итоговый ожидаемый результат

У поля `Мобильный телефон` отображается признак обязательности `*`; пустое поле находится в состоянии `required/invalid`, отдельное сообщение не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-01-initial-final.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-016

**№:** 19
**Название:** Отображение поля `Мобильный телефон` до и после добавления строки телефона
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-002; ATOM-CONTACT-002; ASSERT-CONTACT-002; BSR 162; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Проверить отображение поля `Мобильный телефон` в блоке `Контакты клиента`.
2. Нажать кнопку `Добавить телефон`.
3. Повторно проверить отображение поля `Мобильный телефон`.

### Итоговый ожидаемый результат

Поле `Мобильный телефон` отображается как до, так и после добавления строки телефона.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-01-initial-final.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Фактическое UI-поведение совпадает с baseline: основной `Мобильный телефон` отображается до и после добавления дополнительной строки.

## TC-CONTACT-017

**№:** 20
**Название:** Поле `Тип телефона` до добавления строки телефона не отображается
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-012; ATOM-CONTACT-012; ASSERT-CONTACT-012; BSR 167

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Не нажимая кнопку `Добавить телефон`, проверить наличие поля `Тип телефона`.

### Итоговый ожидаемый результат

Поле `Тип телефона` не отображается.

### Постусловия

Не требуются.

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-01-initial-final.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-018

**№:** 21
**Название:** Состав раскрывающегося списка `Тип телефона`
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-016; ATOM-CONTACT-016; ASSERT-CONTACT-016; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Полный перечень: `Мобильный`, `Домашний`, `Рабочий`.

### Шаги

1. Открыть раскрывающийся список `Тип телефона`.
2. Сверить отображаемые пункты с полным перечнем из тестовых данных.
3. Проверить отсутствие дополнительных пунктов.

### Итоговый ожидаемый результат

Список полностью совпадает с перечнем `Мобильный`, `Домашний`, `Рабочий`; дополнительные значения отсутствуют.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-03-phone-type-dropdown.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Dropdown option locator должен быть scoped to `li.ui-menu-item`, потому что generic text `Мобильный` конфликтует с label `Мобильный телефон`.

## TC-CONTACT-019

**№:** 22
**Название:** Отображение полей `Тип телефона` и `Номер телефона` после добавления строки
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-023; ATOM-CONTACT-023; ASSERT-CONTACT-023; BSR 171; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.

### Тестовые данные

Не требуются.

### Шаги

1. Нажать кнопку `Добавить телефон`.

### Итоговый ожидаемый результат

Появляется строка повторителя с полями `Тип телефона *` и `Номер телефона`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-02-after-add-phone-row.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-020

**№:** 23
**Название:** Удаление строки телефона кнопкой `Корзина`
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172; OBL-CONTACT-023; ATOM-CONTACT-023; ASSERT-CONTACT-023; BSR 171

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.
4. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Первая тестовая строка: первая по порядку.
- Вторая тестовая строка: вторая по порядку.

### Шаги

1. Нажать кнопку `Корзина` в первой тестовой строке.

### Итоговый ожидаемый результат

Первая строка повторителя с полями `Тип телефона` и `Номер телефона` удаляется; вторая строка остаётся на странице.

### Постусловия

- Нажать кнопку `Корзина` для оставшейся второй тестовой строки.
- Проверить, что оставшаяся вторая тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-06-after-delete-phone-row.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Удаление выполнять кликом по delete/trash control добавленной строки; confirmation dialog в UI pass не появлялся.

## TC-CONTACT-021

**№:** 24
**Название:** Выбор значения в поле `Тип телефона`
**Тип:** позитивный
**Приоритет:** средний
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-015; ATOM-CONTACT-015; ASSERT-CONTACT-015; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Значение типа телефона: `Мобильный`.

### Шаги

1. Открыть раскрывающийся список `Тип телефона`.
2. Выбрать пункт `Мобильный`.
3. Перевести фокус на поле `Номер телефона`.

### Итоговый ожидаемый результат

В поле `Тип телефона` отображается `Мобильный`; поле находится в состоянии `valid`, выбранное значение остаётся видимым после перехода к полю `Номер телефона`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-04-phone-type-selected.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Кейс включен в automation-ready на основании полного UI pass 2026-07-30; стартовое состояние: открыта карточка `Заявка`.

## TC-CONTACT-022

**№:** 25
**Название:** Обязательность поля `Тип телефона` при заполненном номере
**Тип:** негативный
**Приоритет:** высокий
**package_id:** WP-ALL-v4
**Трассировка:** OBL-CONTACT-025; ATOM-CONTACT-025; ASSERT-CONTACT-025; OBL-CONTACT-013; ATOM-CONTACT-013; ASSERT-CONTACT-013; BSR 167; OBL-CONTACT-024; ATOM-CONTACT-024; ASSERT-CONTACT-024; BSR 172

### Предусловия

1. Открыть карточку `Заявка`.
2. Перейти к блоку `Контакты клиента`.
3. Нажать кнопку `Добавить телефон`.

### Тестовые данные

- Номер телефона: `9991234567`.
- Тип телефона: оставить пустым.

### Шаги

1. Ввести `9991234567` в поле `Номер телефона`.
2. Снять фокус с поля `Номер телефона`.
3. Оставить поле `Тип телефона` пустым.
4. Нажать кнопку `ДАЛЕЕ` или выполнить другой общий trigger валидации карточки.
5. Проверить состояние поля `Тип телефона` и отображаемое значение поля `Номер телефона`.

### Итоговый ожидаемый результат

У поля `Тип телефона` установлен признак обязательности `required=true`; поле находится в состоянии `empty required invalid`, отображается сообщение `Выберите значение`. В поле `Номер телефона` отображается `+7 (999) 123–45–67`, поле находится в состоянии `valid`.

### Постусловия

- Нажать кнопку `Корзина` для добавленной строки телефона.
- Проверить, что добавленная тестовая строка удалена

### UI Automation Prep

**UI Verification Status:** confirmed
**Automation Execution Status:** ready
**UI Evidence:**
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/client-contacts-documents-full-ui-pass-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-documents-full-ui-pass/evidence/screenshots/contacts-05-type-empty-number-filled.png`
- evidence commit: `acba6a3424e73010d5c3b7977e9169cc066b5fd6`

**Automation Notes:** Для exact message `Выберите значение` использовать общий validation trigger (`ДАЛЕЕ`); на одном blur подтвержден required/invalid state, но текст может не появиться.
