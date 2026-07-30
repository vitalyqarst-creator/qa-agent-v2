# Employment UI calibration second-pass observations

Date: 2026-07-30

Scope: `fts/AutoFin/PostFinal-v2-rc5/test-cases/13-4.3-employment-info.md`

## Checked Items

| TC / gap | UI action | Trigger | Actual UI behavior | Outcome |
|---|---|---|---|---|
| `TC-EMP-011` | In a clean new application card, select `Социальный статус = работа по найму`, focus `Наименование организации, ИНН`, manually enter `7707083893`, wait for DaData dropdown, select first option. Then focus and blur `Фактический адрес работы`. | manual keypress, DaData dropdown selection, address focus/blur | DaData dropdown appeared as `ul.ui-autocomplete.ui-front.ui-menu.ui-widget.ui-widget-content.ui-corner-all.vcm-dropdown` with visible `li.ui-menu-item` options. Selected option: `ПАО СБЕРБАНК, 7707083893 7707083893 г Москва, ул Вавилова, д 19`. After selection and blur: `Наименование организации, ИНН` = `ПАО СБЕРБАНК, 7707083893`; `ОПФ` = `ПАО`; `Фактический адрес работы` = `г Москва, ул Вавилова, д 19`. | `confirmed-ui-ready` |
| `TC-EMP-027` | Manually enter `01.01.2020` into `Дата начала работы в компании` and blur. | manual keypress, blur | Field displayed `01.01.2020`; container state `valid`; no validation message. | `confirmed-ui-ready` |
| Date invalid gap | Paste `64.64.6543` into `Дата начала работы в компании` and blur. Then retry with manual keypress. | paste/blur and manual keypress/blur | Paste path: field cleared after blur and became `required invalid`. Manual keypress path: field retained `64.64.6543` after blur and became `required invalid`. No separate error text was observed beyond field invalid state/required labeling. | gap for new negative TC |
| `TC-EMP-033` / `TC-EMP-036` | In a clean new application card, manually enter `01.2020` into `Начало общего трудового стажа` and blur. | manual keypress, blur | Before input the focused mask was `__.____`. After input and blur field displayed `01.2020`; container state `valid`; no validation message. | `confirmed-ui-ready` |
| Period invalid gap | In clean new application cards, test `55.6523` in `Начало общего трудового стажа` by paste and by manual keypress. | paste/blur and manual keypress/blur | Paste path: value became `55.6523__.____` while focused, then cleared after blur and became `required invalid`. Manual keypress path: field retained `55.6523` after blur and became `required invalid`. No separate error text was observed beyond field invalid state/required labeling. | gap for new negative TC |
| `TC-EMP-076` | Focus empty `Рабочий телефон`. | focus, blur | On focus, field displayed mask `+7 (___) ___–__–__`. After blur without digits, field cleared, became `empty required invalid`, and displayed `Обязательно к заполнению`. | `confirmed-ui-ready` |
| `TC-EMP-045` / `TC-EMP-047` | In a clean new application card, manually enter `9234567890` into `Рабочий телефон` and blur. | manual keypress, blur | Field displayed `+7 (923) 456–78–90`; container state `valid`; no validation message. | `confirmed-ui-ready` |
| `TC-EMP-046` short | In a clean new application card, manually enter `923456789` into `Рабочий телефон` and blur. | manual keypress, blur | While focused, value was incomplete: `+7 (923) 456–78–9_`, state `invalid`. After blur, field cleared, became `empty required invalid`, and displayed `Обязательно к заполнению`. | `confirmed-ui-ready` |
| `TC-EMP-046` long | In a clean new application card, manually enter `92345678901` into `Рабочий телефон` and blur. | manual keypress, blur | UI accepted the first 10 digits and ignored the 11th digit. Displayed value after blur: `+7 (923) 456–78–90`; state `valid`; no validation message. | `confirmed-ui-ready` |
| `TC-EMP-046` alpha | In a clean new application card, manually enter `92345A7890` into `Рабочий телефон` and blur. | manual keypress, blur | Letter `A` was not entered. Remaining digits produced incomplete value `+7 (923) 457–89–0_` while focused. After blur, field cleared, became `empty required invalid`, and displayed `Обязательно к заполнению`. | `confirmed-ui-ready` |
| `TC-EMP-048` | In a clean new application card, paste `ФОРМАД-ПЛАСТ ООО 7701` into `Наименование организации, ИНН` and wait for DaData/inactive-organization response. | paste, wait | No DaData option appeared, organization field stayed empty, no message `Организация не является действующей` was observed, and `ДАЛЕЕ` control remained visible/enabled. Fixture did not reproduce on the stand in this pass. | `needs-test-data` / `not-reproducible` |

## Test-case Gap

The source file has positive date/period cases for valid values:

- `TC-EMP-027`: `Дата начала работы в компании` accepts `01.01.2020`.
- `TC-EMP-033` / `TC-EMP-036`: `Начало общего трудового стажа` accepts `01.2020`.

No separate negative test-case was found for invalid day/month values such as `64.64.6543` in `Дата начала работы в компании` or `55.6523` in `Начало общего трудового стажа`.

Recommended new coverage:

- Negative TC for `Дата начала работы в компании`: manual input of an impossible date keeps the invalid value visible after blur and marks the field invalid; paste of the same invalid value clears the field after blur.
- Negative TC for `Начало общего трудового стажа`: manual input of an impossible month/year-like value keeps the invalid value visible after blur and marks the field invalid; paste of the same invalid value clears the field after blur.
