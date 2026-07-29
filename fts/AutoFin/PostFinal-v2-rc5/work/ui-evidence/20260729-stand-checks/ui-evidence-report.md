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

## Second UI pass: observability blockers

Date: 2026-07-29. Scope: only previously unclosed observability blockers from this stand package. Each check used a clean new card unless stated otherwise.

### DaData/FIO prefix behavior

Clean current-FIO checks:

| Field | Typed value | Wait | Visible dropdown/options | Selection attempt | Resulting value | Gender state | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Фамилия` | `Иванова` | 2.5s and 5s | none captured | `ArrowDown+Enter` fallback, no clicked option | `Иванова` stayed in field | `Женский` checked, `Мужской` unchecked | `mismatch-ft-ui` for dropdown, `confirmed` for gender derivation |
| `Фамилия` | `Иванов` | 2.5s and 5s | none captured | `ArrowDown+Enter` fallback, no clicked option | `Иванов` stayed in field | `Мужской` checked, `Женский` unchecked | `mismatch-ft-ui` for dropdown, `confirmed` for gender derivation |

Observed DOM for delayed dropdown in retry/polluted state:

- Selector: `ul.ui-autocomplete.ui-front.ui-menu.ui-widget.ui-widget-content.ui-corner-all.vcm-dropdown`.
- Options selector: `ul.ui-autocomplete.ui-menu.vcm-dropdown > li.ui-menu-item`.
- Example visible option texts captured after a delayed retry: `Иванова`, `Ивановас`, `Ивановайте`, `Иванова-Беспощадная`, `Ивановай`, `Иванован`, `Иванована`, `Иванова-Чуронова`, `Иванова-Ылахова`, `Иванова-Аласкирова`.
- This retry state was not used to confirm the positive current-FIO path because the dropdown options were stale/feminine after a previous `Иванова` attempt.

Evidence:

- `evidence/screenshots/second-pass-dadata-clean-female-only-wait2500.png`
- `evidence/screenshots/second-pass-dadata-clean-female-only-wait5000.png`
- `evidence/screenshots/second-pass-dadata-clean-female-only-after-select.png`
- `evidence/screenshots/second-pass-dadata-clean-male-only-wait2500.png`
- `evidence/screenshots/second-pass-dadata-clean-male-only-wait5000.png`
- `evidence/screenshots/second-pass-dadata-clean-male-only-after-select.png`
- `evidence/screenshots/second-pass-dadata-retry-current-male-wait2500.png`
- `evidence/screenshots/second-pass-dadata-retry-current-male-wait5000.png`

### Previous-FIO positive path

Steps:

1. Opened a clean new card.
2. Enabled `Клиент менял ФИО`.
3. Tried previous-FIO DaData fields with typed values: `Иванова`, `Мария`, `Сергеевна`.
4. Waited 2.5s and 5s per field for dropdown.
5. Clicked `ДАЛЕЕ` through visible DOM text after the Playwright exact-text locator did not find the button.

Observed:

- No visible `ul.ui-autocomplete...vcm-dropdown` / `li.ui-menu-item` options were captured for previous surname/name/patronymic in this clean-card path.
- After manual typing, the three previous-FIO fields retained values:
  - `Предыдущая фамилия`: `Иванова`
  - `Предыдущее имя`: `Мария`
  - `Предыдущее отчество`: `Сергеевна`
- Before and after the `ДАЛЕЕ` click, these three fields had no `Выберите значение` messages.
- The whole card did not pass validation because unrelated required fields in passport/address/etc. remained empty.
- Because no dropdown option was selected, this closes only the "typed values remove previous-FIO field messages" observation, not the DaData-selected positive branch.

Status: `blocked-observability` for dropdown-selected positive path; `confirmed` for disappearance of `Выберите значение` on those three previous-FIO fields after values are present.

Evidence:

- `evidence/screenshots/second-pass-prev-fio-positive-enabled.png`
- `evidence/screenshots/second-pass-prev-fio-positive-surname-wait2500.png`
- `evidence/screenshots/second-pass-prev-fio-positive-surname-wait5000.png`
- `evidence/screenshots/second-pass-prev-fio-positive-name-wait2500.png`
- `evidence/screenshots/second-pass-prev-fio-positive-name-wait5000.png`
- `evidence/screenshots/second-pass-prev-fio-positive-patronymic-wait2500.png`
- `evidence/screenshots/second-pass-prev-fio-positive-patronymic-wait5000.png`
- `evidence/screenshots/second-pass-prev-fio-positive-before-dom-next-click.png`
- `evidence/screenshots/second-pass-prev-fio-positive-after-dom-next-click.png`

### ABS ID

Clean-card observation:

- `ID Клиента` value before save: empty.
- Field state: readonly, not disabled; container class includes `empty readonly`.
- Visible card action: `ДАЛЕЕ`.
- No visible `СОХРАНИТЬ` action was available in the card.
- Application header before save: `Новая заявка (Заёмщик)`.
- No application number/id/status was assigned in this state.
- No expected ABS/source oracle was available.

Status: `blocked-observability`. Do not close ABS ID gap without a safe save path and expected-source oracle.

Evidence:

- `evidence/screenshots/second-pass-abs-id-clean-card-observability.png`

### Actual address manual mode

Steps:

1. Opened a clean new card.
2. Clicked `Адрес фактического места жительства совпадает с адресом регистрации` to make actual address separate.
3. Clicked the last visible `Ввести вручную` control, which appeared after actual address separation.
4. Clicked `ДАЛЕЕ`.
5. Tested invalid values separately.

Observed required behavior after `ДАЛЕЕ`:

| Field | State/message |
| --- | --- |
| `Регион` | `empty required invalid`; exact message `Выберите значение` |
| `Населенный пункт` | `empty required`; no inline message captured |
| `Город` | `empty required`; no inline message captured |
| `Дом` | `empty required`; no inline message captured |
| `Квартира` | `empty required`; no inline message captured |
| `Почтовый индекс` | optional empty; no invalid state/message |
| `Корпус` | optional empty; no invalid state/message |

Observed format behavior:

| Field | Input | Displayed value after blur | State/message |
| --- | --- | --- | --- |
| `Почтовый индекс` | `12345A` | empty | no invalid state/message |
| `Почтовый индекс` | `1234567` | `123456` | no invalid state/message |
| `Корпус` | `12A` | `12A` | `invalid`; exact message `Введено некорректное значение` |
| `Квартира` | `45A` | `45A` | `invalid`; exact message `Введено некорректное значение` |

Status: `confirmed`.

Evidence:

- `evidence/screenshots/second-pass-actual-address-after-different-toggle.png`
- `evidence/screenshots/second-pass-actual-address-manual-enabled.png`
- `evidence/screenshots/second-pass-actual-address-required-after-next.png`
- `evidence/screenshots/second-pass-actual-address-postal-alpha.png`
- `evidence/screenshots/second-pass-actual-address-postal-long.png`
- `evidence/screenshots/second-pass-actual-address-building-alpha.png`
- `evidence/screenshots/second-pass-actual-address-flat-alpha.png`

### Previous-passport delete

Steps:

1. Opened a clean new card.
2. Enabled `Клиент менял паспорт`.
3. Clicked `ДОБАВИТЬ ПАСПОРТ`.
4. Filled visible last passport fields where possible: `Номер = 567890`, `Дата выдачи = 01.01.2020`; `Серия` remained not reliably filled/visible in the detected row.
5. Searched visible DOM for delete/trash/remove candidates.
6. Clicked the last visible delete-like candidate only after filtering by visible position.

Observed:

- A second previous-passport field group was partially visible.
- No dedicated enabled trash/delete control for the previous-passport repeater was confirmed.
- Visible delete-like candidates matched the unrelated `Участники` block / large container text, not a passport row action.
- Passport-related field count before and after the delete-like click remained `9`; the passport row was not removed.
- Therefore, exact removal semantics cannot be confirmed.

Status: `blocked-observability`.

Evidence:

- `evidence/screenshots/second-pass-prev-passport-delete-enabled.png`
- `evidence/screenshots/second-pass-prev-passport-delete-after-add-second.png`
- `evidence/screenshots/second-pass-prev-passport-delete-after-fill-second.png`
- `evidence/screenshots/second-pass-prev-passport-delete-after-delete-click.png`
- `evidence/screenshots/second-pass-prev-passport-delete-final-state.png`

### Calculator route

Observed:

- In the application card, no visible control matching `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` / `Кредитный калькулятор` was found.
- On `/applicationlist/`, the top action bar contains `КРЕДИТНЫЙ КАЛЬКУЛЯТОР`.
- This is an observed route difference: calculator is list-level in this UI pass, not card-level.

Status: `mismatch-ft-ui`.

Evidence:

- `evidence/screenshots/second-pass-calculator-card-no-route.png`
- `evidence/screenshots/second-pass-calculator-list-top-cropped.png`
