# UI validation report: 4.3 client contacts

## Metadata

- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `scope`: `4.3-client-contacts`
- `scope_slug`: `4-3-client-contacts-ui-calibration`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `date`: 2026-07-29
- `browser`: Playwright Chromium profiles `client-contacts`, `phone-negative-recheck`

Only UI facts were checked. Baseline `test-cases/*.md`, DOCX/XHTML/PDF, support/mockups, and agent code/instructions were not edited.

## Validation matrix

| Area | Field | Scenario | Exact test data | Trigger | Observed UI result | UI status | Automation recommendation |
|---|---|---|---|---|---|---|---|
| Phone | `Мобильный телефон` | Initial empty required state | empty | Open fresh application card | Field has `*`, DOM `required=true`, state `empty required ... invalid`; no standalone message in contacts section. | `confirmed` | Assert required marker/state; screenshot `contacts-initial.png`. |
| Phone | `Мобильный телефон` | Valid phone | `9991234567` | `fill`, `Tab` blur | Displayed as `+7 (999) 912–34–56`; state `valid`; value did not clear. | `confirmed` | Assert actual mask observed for this input, or verify with manual keyboard if automation needs literal digit mapping. |
| Phone | `Мобильный телефон` | Short phone | `999123456` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Clear step produced empty field with state `invalid required empty`; after input UI displayed `+7 (999) 912–34–56`, state `valid`, no visible message. | `confirmed` | Do not assert rejection for this value; assert mask normalization/accepted valid state if this scenario is automated. |
| Phone | `Мобильный телефон` | Long phone | `99912345678` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Clear step produced empty field with state `invalid required empty`; after input UI displayed `+7 (999) 912–34–56`, state `valid`, no visible message; extra digit was ignored by mask. | `confirmed` | Do not assert rejection for this value; assert accepted masked value and valid state. |
| Phone | `Мобильный телефон` | Alpha phone | `99912A4567` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Clear step produced empty field with state `invalid required empty`; after input UI displayed `+7 (999) 912–45–67`, state `valid`, no visible message; alpha character was ignored by mask. | `confirmed` | Do not assert error text; assert that non-digit input is filtered by the mask. |
| Phone | `Мобильный телефон` | Space phone | `99912 4567` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Clear step produced empty field with state `invalid required empty`; after input UI displayed `+7 (999) 912–45–67`, state `valid`, no visible message; space was ignored by mask. | `confirmed` | Do not assert error text; assert that spaces are filtered by the mask. |
| Phone | `Мобильный телефон` | Repeating digits | `9999999999` | `fill`, `Tab` blur | Displayed as `+7 (999) 999–99–99`; state `valid`; no message. | `confirmed` | Repeating digits are not rejected by observed UI. |
| E-mail | `E-mail` | Field presence/required | empty | Open contacts block | Field visible, no `*`, DOM `required=false`. | `confirmed` | Treat e-mail as optional. |
| E-mail | `E-mail` | Valid e-mail | `one@example.ru` | `fill`, `Tab` blur | Value remained; no invalid state/message. | `confirmed` | Positive e-mail fixture can use `one@example.ru`. |
| E-mail | `E-mail` | Invalid no `@` | `testexample.ru` | `fill`, `Tab` blur | Value cleared to empty; no visible message. | `confirmed` | Assert clear-on-blur, not error text. |
| E-mail | `E-mail` | Invalid incomplete domain | `test@` | `fill`, `Tab` blur | Value cleared to empty; no visible message. | `confirmed` | Assert clear-on-blur. |
| E-mail | `E-mail` | Invalid double `@` | `test@@example.ru` | `fill`, `Tab` blur | Value cleared to empty; no visible message. | `confirmed` | Assert clear-on-blur. |
| E-mail | `E-mail` | Invalid space | `test example@example.ru` | `fill`, `Tab` blur | Value cleared to empty; no visible message. | `confirmed` | Assert clear-on-blur. |
| E-mail | `E-mail` | Two e-mails semicolon | `one@example.ru; two@example.ru` | `fill`, `Tab` blur | Value cleared to empty; multiple e-mails not accepted. | `confirmed` | Do not use semicolon-separated e-mails in one field. |
| E-mail | `E-mail` | Two e-mails comma | `one@example.ru, two@example.ru` | `fill`, `Tab` blur | Value cleared to empty; multiple e-mails not accepted. | `confirmed` | Do not use comma-separated e-mails in one field. |
| Phone type | `Тип телефона` | Field presence before add | empty | Open contacts block | `Тип телефона` is not visible in initial/main row. | `confirmed` | Add phone row before checking phone type. |
| Phone type | `Тип телефона` | Field appears after add | click `Добавить телефон` | button click | Added row contains `Тип телефона *` and `Номер телефона *`. | `confirmed` | Use added row for phone type scenarios. |
| Phone type | `Тип телефона` | Dropdown values | focus `Тип телефона` | click/focus | Values visible: `Мобильный`, `Рабочий`, `Домашний`. | `confirmed` | Assert option presence; do not assert order unless required. |
| Phone type | `Тип телефона` | Select valid value | `Мобильный` | dropdown item selection, `Tab` blur | Value remained `Мобильный`; state `valid`. | `confirmed` | Use scoped dropdown-item selector to avoid text collision. |
| Repeater | `Добавить телефон` | Initial state | none | Open contacts block | Action label `Добавить телефон` visible; no added phone row. | `confirmed` | Initial assertion can use section screenshot. |
| Repeater | `Добавить телефон` | Add row with ref click | none | Playwright ref click | No row appeared; likely automation targeting issue. | `blocked-observability` | Use scoped visible button selector rather than stale/ref text locator. |
| Repeater | `Добавить телефон` | Add row with visible button DOM click | none | button click | Row appeared with `Тип телефона *`, `Номер телефона *`, delete `-`. | `confirmed` | Use `.button.ui-button.additional` scoped by text `ДОБАВИТЬ ТЕЛЕФОН`. |
| Repeater | `-` | Delete added phone row | none | button click | Added row disappeared; main row remained. | `confirmed` | Assert absence of added row fields after click. |

## Summary

- Confirmed scenarios: 22
- Blocked-observability scenarios: 1

## Key facts for automation-ready tests

1. Main contacts row has `Мобильный телефон *` and optional `E-mail`.
2. `Тип телефона` exists only in an added phone row.
3. Added phone row fields: `Тип телефона *`, `Номер телефона *`, delete action `-`.
4. `Тип телефона` dropdown values: `Мобильный`, `Рабочий`, `Домашний`.
5. E-mail invalid/multiple values clear on blur without visible message.
6. Main phone mask can be reset reliably with `Ctrl+A`, `Backspace`, `Delete`, and `Tab`; after verified clear state, values `999123456`, `99912345678`, `99912A4567`, and `99912 4567` were accepted as valid masked values with no visible error message.

## Blur clearing clarification

- The expected rule "short phone clears on blur, valid phone remains on blur" was checked explicitly and was not confirmed for the short phone case.
- For `999123456`, after verified pre-clear and blur, the field did not clear; UI displayed `+7 (999) 912–34–56` and the field state became `valid`.
- For valid input `9991234567`, after blur the value also remained in the field as `+7 (999) 912–34–56`, state `valid`.
- Automation-ready tests should not assert clear-on-blur for short phone input unless the product behavior changes or another validation trigger is identified.
