# UI validation report: 4.3 client contacts repeater phone

## Metadata

- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `scope`: `4.3-client-contacts`
- `block`: `Контакты клиента`
- `row_scope`: added phone row after `Добавить телефон`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `date`: 2026-07-29
- `browser`: Playwright Chromium profile `phone-negative-recheck`

Only added phone row UI facts were checked. Baseline `test-cases/*.md`, source DOCX/XHTML/PDF, support/mockups, `.env`, credentials, cookies, auth/session/storage files were not edited.

## Summary

- Confirmed: `GAP-CONTACT-PHONE-TYPE-OPTIONALNESS-UI-001`, `GAP-CONTACT-PHONE-NUMBER-OPTIONALNESS-UI-001`, `GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001`
- Blocked-observability: none
- Mismatch-ft-ui: none

## Validation matrix

| Gap ID | Field | Scenario | Exact test data | Trigger | Observed UI result | UI status | Automation recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GAP-CONTACT-PHONE-TYPE-OPTIONALNESS-UI-001` | `Тип телефона` in added phone row | Phone number filled, phone type empty | `Номер телефона` = `9991234567`; `Тип телефона` empty | Clear fields, type phone number, `Tab` blur; then click `ДАЛЕЕ` | `Тип телефона` has required marker/DOM `required=true`; field state `empty required invalid`; exact message `Выберите значение`. `Номер телефона` displays `+7 (999) 123–45–67`, state `valid`. After `ДАЛЕЕ`, URL stayed on `/application/card/create`. | `confirmed` | Treat `Тип телефона` as mandatory when added phone row exists. Assert message `Выберите значение` after blur/validation trigger. |
| `GAP-CONTACT-PHONE-NUMBER-OPTIONALNESS-UI-001` | `Номер телефона` in added phone row | Phone type selected, phone number empty | `Тип телефона` = `Мобильный`; `Номер телефона` empty | Select dropdown value, clear phone number, `Tab` blur; then click `ДАЛЕЕ` | `Номер телефона` has required marker/DOM `required=true`; field state `invalid required empty`; exact message `Обязательно к заполнению`. `Тип телефона` remains `Мобильный`, state `valid`. After `ДАЛЕЕ`, URL stayed on `/application/card/create`. | `confirmed` | Treat `Номер телефона` as mandatory when added phone row exists. Assert message `Обязательно к заполнению`. |
| `GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001` | `Номер телефона` in added phone row | Repeating digits | `9999999999` | Pre-clear number field, `keyboard.type`, `Tab` blur | Displayed value `+7 (999) 999–99–99`; state `valid`; no message. | `confirmed` | Repeating digits are accepted by added-row phone mask. |
| `GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001` | `Номер телефона` in added phone row | Short number | `999123456` | Pre-clear number field, `keyboard.type`, `Tab` blur | Displayed value is empty; state `invalid required empty`; exact message `Обязательно к заполнению`. | `confirmed` | Added-row phone differs from main phone: short value clears/rejects on blur. |
| `GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001` | `Номер телефона` in added phone row | Long number | `99912345678` | Pre-clear number field, `keyboard.type`, `Tab` blur | Displayed value `+7 (999) 123–45–67`; state `valid`; no message; extra symbol is ignored/truncated by mask. | `confirmed` | Assert accepted masked value and ignored extra digit. |
| `GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001` | `Номер телефона` in added phone row | Alpha in number | `99912A4567` | Pre-clear number field, `keyboard.type`, `Tab` blur | Displayed value is empty; state `invalid required empty`; exact message `Обязательно к заполнению`. Letter-containing value is not converted to valid number. | `confirmed` | Assert clear/reject on blur for alpha-containing input. |
| `GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001` | `Номер телефона` in added phone row | Space in number | `99912 4567` | Pre-clear number field, `keyboard.type`, `Tab` blur | Displayed value is empty; state `invalid required empty`; exact message `Обязательно к заполнению`. Space-containing value is not converted to valid number. | `confirmed` | Assert clear/reject on blur for space-containing input. |

## Notes

- Added phone row appears after clicking `ДОБАВИТЬ ТЕЛЕФОН` and contains `Тип телефона *` and `Номер телефона *`.
- `Тип телефона` dropdown values observed during this run: `Мобильный`, `Рабочий`, `Домашний`.
- `ДАЛЕЕ` validation kept the user on the same `/application/card/create` URL. The card also contained other unrelated required fields, so route blocking is recorded as observed global no-transition plus confirmed row-level invalid state/message, not as an isolated proof that this row alone blocks navigation.
- Added-row `Номер телефона` behavior is not identical to the main `Мобильный телефон` field previously checked: short, alpha, and space-containing values clear/reject in the added row.
