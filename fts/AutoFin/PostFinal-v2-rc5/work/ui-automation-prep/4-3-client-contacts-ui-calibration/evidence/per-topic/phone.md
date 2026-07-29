# Phone UI evidence

## Scope

- Area: `Контакты клиента`
- Field: `Мобильный телефон`
- Date: 2026-07-29
- Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- Browser profiles: Playwright Chromium `client-contacts`, `phone-negative-recheck`

## Observed fields

- Main contact row contains `Мобильный телефон *` and `E-mail`.
- Main `Мобильный телефон` is required: DOM `required=true`; initial field container state was `empty required ... invalid`.
- No `Тип телефона` field is visible in the main row before pressing `Добавить телефон`.

## Phone scenarios

| Scenario | Exact test data | Trigger | Observed UI result | UI status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Initial empty phone | empty | Open fresh application card / initial validation | Field is empty, required marker `*` is visible, field state is `empty required ... invalid`. No standalone message was visible inside contacts section. | `confirmed` | `evidence/screenshots/contacts-initial.png` |
| Valid phone | `9991234567` | `fill` into empty main phone field, then `Tab` blur | Displayed mask became `+7 (999) 912–34–56`; field state `valid`; value did not clear after blur. | `confirmed` | `evidence/screenshots/phone-valid-9991234567.png` |
| Short phone | `999123456` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Before input, field was confirmed empty with container state `invalid required empty`. After input, displayed value became `+7 (999) 912–34–56`; field state `valid`; no visible message. | `confirmed` | `evidence/screenshots/phone-negative-recheck-short-999123456.png` |
| Long phone | `99912345678` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Before input, field was confirmed empty with container state `invalid required empty`. After input, displayed value became `+7 (999) 912–34–56`; field state `valid`; no visible message; extra digit was ignored by mask. | `confirmed` | `evidence/screenshots/phone-negative-recheck-long-99912345678.png` |
| Alpha phone | `99912A4567` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Before input, field was confirmed empty with container state `invalid required empty`. After input, displayed value became `+7 (999) 912–45–67`; field state `valid`; no visible message; alpha character was ignored by mask. | `confirmed` | `evidence/screenshots/phone-negative-recheck-alpha-99912A4567.png` |
| Space phone | `99912 4567` | `Ctrl+A`, `Backspace`, `Delete`, `Tab` clear verification; then `keyboard.type`, `Tab` blur | Before input, field was confirmed empty with container state `invalid required empty`. After input, displayed value became `+7 (999) 912–45–67`; field state `valid`; no visible message; space was ignored by mask. | `confirmed` | `evidence/screenshots/phone-negative-recheck-space-99912-4567.png` |
| Repeating digits | `9999999999` | `fill`, `Tab` blur | Displayed as `+7 (999) 999–99–99`, field state `valid`, no message. | `confirmed` | `evidence/screenshots/phone-repeat-9999999999.png` |

## Automation notes

- The main phone field is masked and required.
- `fill` on this masked field produced a non-obvious mask result for `9991234567`: `+7 (999) 912–34–56`.
- The field can be reset between attempts with `Ctrl+A`, `Backspace`, `Delete`, and `Tab`; the clear step was confirmed by empty value and `invalid required empty` container state before each rechecked input.
- Short, long, alpha, and space-containing inputs were not rejected by observed UI. The mask normalized/filtered the input and left the field in `valid` state without a visible message.

## Blur clearing clarification

- Explicit check performed: compare blur behavior for short `999123456` and valid `9991234567`.
- Short `999123456` did not clear on blur after a verified empty pre-state. UI displayed `+7 (999) 912–34–56`, state `valid`, no visible message.
- Valid `9991234567` remained in the field after blur as `+7 (999) 912–34–56`, state `valid`.
- Therefore, the UI evidence does not support a test expectation that short phone input clears on blur.
