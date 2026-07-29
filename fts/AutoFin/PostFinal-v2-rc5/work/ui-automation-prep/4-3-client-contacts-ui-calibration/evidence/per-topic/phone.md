# Phone UI evidence

## Scope

- Area: `Контакты клиента`
- Field: `Мобильный телефон`
- Date: 2026-07-29
- Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- Browser profile: Playwright Chromium `client-contacts`

## Observed fields

- Main contact row contains `Мобильный телефон *` and `E-mail`.
- Main `Мобильный телефон` is required: DOM `required=true`; initial field container state was `empty required ... invalid`.
- No `Тип телефона` field is visible in the main row before pressing `Добавить телефон`.

## Phone scenarios

| Scenario | Exact test data | Trigger | Observed UI result | UI status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Initial empty phone | empty | Open fresh application card / initial validation | Field is empty, required marker `*` is visible, field state is `empty required ... invalid`. No standalone message was visible inside contacts section. | `confirmed` | `evidence/screenshots/contacts-initial.png` |
| Valid phone | `9991234567` | `fill` into empty main phone field, then `Tab` blur | Displayed mask became `+7 (999) 912–34–56`; field state `valid`; value did not clear after blur. | `confirmed` | `evidence/screenshots/phone-valid-9991234567.png` |
| Short phone | `999123456` | `fill`, `Tab` blur | The mask field could not be reliably reset between values in the same card. Observed value remained `+7 (999) 912–34–56`, field state `valid`; this is not a reliable isolated validation of the short value. | `blocked-observability` | `evidence/screenshots/phone-short-999123456.png` |
| Long phone | `99912345678` | `fill`, `Tab` blur | Same observability issue as short phone: field retained/displayed `+7 (999) 912–34–56`, field state `valid`; isolated long-value behavior was not reproducible in the same card. | `blocked-observability` | `evidence/screenshots/phone-long-99912345678.png` |
| Alpha phone | `99912A4567` | `fill`, `Tab` blur | Observed display `+7 (999) 912–45–67`, field state `valid`, no message. Because the mask did not reset cleanly between values, use this as UI evidence but not as a strict isolated negative assertion. | `blocked-observability` | `evidence/screenshots/phone-alpha-99912A4567.png` |
| Space phone | `99912 4567` | `fill`, `Tab` blur | Observed display `+7 (999) 912–45–67`, field state `valid`, no message. Same reset limitation as alpha scenario. | `blocked-observability` | `evidence/screenshots/phone-space-99912-4567.png` |
| Repeating digits | `9999999999` | `fill`, `Tab` blur | Displayed as `+7 (999) 999–99–99`, field state `valid`, no message. | `confirmed` | `evidence/screenshots/phone-repeat-9999999999.png` |

## Automation notes

- The main phone field is masked and required.
- `fill` on this masked field produced a non-obvious mask result for `9991234567`: `+7 (999) 912–34–56`.
- Negative phone scenarios need a reliable clean-card setup per value, or a UI-supported clear/reset action, before they are converted to strict automation-ready assertions.
