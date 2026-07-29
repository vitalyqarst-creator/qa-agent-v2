# UI evidence report: 20260729 stand checks

## Metadata

- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `date`: 2026-07-29
- `page_title`: `Заявки в Системе - AFB`
- `visible_user`: `Виталий Жидков`
- `role`: not visible in UI evidence
- `build/version`: not visible in UI evidence
- `application`: new unsaved card, header `Новая заявка (Заёмщик)`
- `application_id / number / status`: not assigned/visible before save

Only the test stand UI was used. No API secrets, auth/session/storage files, source DOCX/XHTML/PDF/support/mockups/canonical files, or baseline test-cases were edited.

## Status summary

| Area | Gap / check | Status |
| --- | --- | --- |
| P0 `4.3-personal-data` | `GAP-PERSON-REQUIREDNESS-TRIGGER-001` empty previous-FIO fields | `confirmed` |
| P0 `4.3-personal-data` | `GAP-PERSON-REQUIREDNESS-TRIGGER-001` positive branches with direct typed values | `blocked-observability` |
| P0 `4.3-personal-data` | `GAP-PERSON-ABS-ID-FIXTURE-001` | `blocked-observability` |
| P0 `4.3-personal-data` | DaData/FIO calibration via direct UI typing | `blocked-observability` |
| P1 `4.3-card-shell-header-and-calculator` | header/widget `Краткая информация с калькулятора` | `confirmed` |
| P1 `4.3-card-shell-header-and-calculator` | open `Кредитный калькулятор` from card | `blocked-observability` |
| P1 `4.2-menu-actions-and-responsible-manager` | `Ответственный КМ` fixture | `blocked-observability` |
| P2 `4.3-client-addresses` | registration address manual mode, empty required and invalid value behavior | `confirmed` |
| P2 `4.3-client-addresses` | actual address manual mode | `blocked-observability` |
| P2 `4.3-previous-passports` | visible fields after condition and issue date validation | `confirmed` |
| P2 `4.3-previous-passports` | trash/delete semantics | `blocked-observability` |

## P0: Personal Data

### GAP-PERSON-REQUIREDNESS-TRIGGER-001

Steps:

1. Opened a new application card.
2. Enabled `Клиент менял ФИО`.
3. Left `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество` empty.
4. Used blur/focus-out and then clicked `ДАЛЕЕ`.

Observed empty-state UI:

- `Клиент менял ФИО` checkbox was enabled.
- All three previous-FIO fields became visible.
- Each previous-FIO field had DOM `required=true`.
- Each field had state `empty required invalid`.
- Exact message for each field: `Выберите значение`.
- After `ДАЛЕЕ`, URL stayed on `/application/card/create`.

Evidence:

- `evidence/screenshots/p0-person-requiredness-empty-after-blur.png`
- `evidence/screenshots/p0-person-requiredness-empty-after-next.png`

Positive branch attempt:

- Direct keyboard typing into `Предыдущая фамилия`, `Предыдущее имя`, or `Предыдущее отчество` did not produce a confirmed selected value.
- The fields are DaData/select-style fields; typed values without a selected dropdown option were cleared and the group remained invalid with `Выберите значение`.
- Status for positive branches: `blocked-observability`.

Evidence:

- `evidence/screenshots/p0-person-requiredness-only_last_name-after-next.png`
- `evidence/screenshots/p0-person-requiredness-only_first_name-after-next.png`
- `evidence/screenshots/p0-person-requiredness-only_middle_name-after-next.png`

### GAP-PERSON-ABS-ID-FIXTURE-001

Observed:

- `ID Клиента` is visible in the new card.
- Before save, value was empty.
- Field state: `empty readonly label-align-top text-align-left`.
- No `Сохранить` button was visible in the current card UI; only `ДАЛЕЕ` was visible.
- The card had many unrelated required fields empty/invalid, so a safe save path was not available in this run.
- No backend/ABS/test-data source for expected ABS client ID was available.

Status: `blocked-observability`.

### DaData/FIO calibration

Attempted through UI only, no API:

- `Иванова Анна Сергеевна` typed into current `Фамилия`.
- `Иванов Иван Сергеевич` typed into current `Фамилия`.
- `Петрова Мария Сергеевна` typed into `Предыдущая фамилия`.
- `Петров Петр Сергеевич` typed into `Предыдущая фамилия`.

Observed:

- No visible `li.ui-menu-item` dropdown options were captured for these full-string inputs.
- Values did not remain selected after blur.
- `Пол` remained unselected: both `Мужской` and `Женский` checked state `false`.
- Because no DaData suggestion was observed/selected, this does not confirm gender auto-fill or previous-FIO fill behavior.

Status: `blocked-observability`.

Evidence:

- `evidence/screenshots/p0-dadata-current-female-dropdown.png`
- `evidence/screenshots/p0-dadata-current-female-after-select.png`
- `evidence/screenshots/p0-dadata-current-male-dropdown.png`
- `evidence/screenshots/p0-dadata-current-male-after-select.png`
- `evidence/screenshots/p0-dadata-prev-female-dropdown.png`
- `evidence/screenshots/p0-dadata-prev-female-after-select.png`
- `evidence/screenshots/p0-dadata-prev-male-dropdown.png`
- `evidence/screenshots/p0-dadata-prev-male-after-select.png`

## P1: Card Shell Header and Calculator

### Header calculator widget

Steps:

1. Opened a new application card.
2. Read the top card widget/header.

Observed widget labels and values:

- `Сумма кредита, Р`: `1000000`
- `VIN`: `XTA2100400Y123456`
- `Ставка, %`: `12.5`
- `Платёж в месяц, Р`: `8870`
- `Срок мес.`: `60`

Status: `confirmed`.

Evidence:

- `evidence/screenshots/p1-card-shell-header-calculator-widget.png`

### Credit calculator opening

Observed:

- No visible button/control matching `Кредитный калькулятор` or `КАЛЬКУЛЯТОР` was found inside the application card.
- The list page has a `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` action, but list-page screenshot was not saved because it exposes application rows.

Status: `blocked-observability`.

## P1: Responsible Manager

Observed:

- No source-approved fixture for expected `Ответственный КМ` binding was available.
- List page displayed application rows and responsible manager values, but this is not enough to close the fixture gap without expected source binding.
- No safe permission was provided to change responsible manager assignment.

Status: `blocked-observability`.

## P2: Client Addresses

### Registration address manual mode

Steps:

1. Opened `Адрес регистрации`.
2. Clicked `Ввести вручную`.
3. Clicked `ДАЛЕЕ` with minimal fields empty.
4. Entered invalid values for selected format fields.

Observed empty required behavior after `ДАЛЕЕ`:

| Field | Required | State | Exact message |
| --- | --- | --- | --- |
| `Регион` | true | `empty required invalid` | `Выберите значение` |
| `Населенный пункт` | true | `empty required invalid` | `Обязательно к заполнению` |
| `Город` | true | `empty required invalid` | `Обязательно к заполнению` |
| `Дом` | true | `empty required invalid` | `Обязательно к заполнению` |
| `Квартира` | true | `empty required invalid` | `Обязательно к заполнению` |
| `Почтовый индекс` | false | empty, no invalid state | none |
| `Корпус` | false | empty, no invalid state | none |

Observed format behavior:

| Field | Input | Displayed value after blur | State | Exact message |
| --- | --- | --- | --- | --- |
| `Почтовый индекс` | `12345A` | empty | no invalid state | none |
| `Почтовый индекс` | `1234567` | `123456` | no invalid state | none |
| `Корпус` | `12A` | `12A` | `invalid` | `Введено некорректное значение` |
| `Квартира` | `45A` | `45A` | `invalid` | `Введено некорректное значение` |

Status: `confirmed`.

Evidence:

- `evidence/screenshots/p2-address-registration-manual-enabled.png`
- `evidence/screenshots/p2-address-registration-manual-empty-after-next.png`
- `evidence/screenshots/p2-address-registration-manual-invalid-values.png`

### Actual address manual mode

Not completed in this run. The current card already had multiple invalid/manual states, so using it for `same-address = Нет` would mix contexts.

Status: `blocked-observability`.

## P2: Previous Passports

Steps:

1. Located `Клиент менял паспорт` condition by visible text.
2. Enabled the condition through UI.
3. Captured visible passport-related fields and buttons.
4. Entered future date `01.01.2099` into previous passport `Дата выдачи`.

Observed visible previous-passport fields after condition:

- `Серия`, required.
- `Номер`, required.
- `Дата выдачи`, required.
- `ДОБАВИТЬ ПАСПОРТ` button visible.

Not observed in the previous-passport row:

- `Код подразделения`.
- `Кем выдан`.
- Manual input toggle for department.

Observed date validation:

- Input: `01.01.2099`.
- Trigger: blur, then `ДАЛЕЕ`.
- Displayed value remained `01.01.2099`.
- State: `required invalid`.
- Exact message: `Дата не может быть больше 29.07.2026.`

Trash/delete:

- A `DELETE` button was visible elsewhere but disabled.
- No enabled trash/delete control for the previous-passport row was confirmed in this run.

Status:

- Visible fields and date validation: `confirmed`.
- Trash/delete semantics: `blocked-observability`.

Evidence:

- `evidence/screenshots/p2-prev-passports-before-toggle.png`
- `evidence/screenshots/p2-prev-passports-after-toggle.png`
- `evidence/screenshots/p2-prev-passport-issue-date-future-after-blur.png`
