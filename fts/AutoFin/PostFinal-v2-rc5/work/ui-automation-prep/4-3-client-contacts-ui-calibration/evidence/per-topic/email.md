# E-mail UI evidence

## Scope

- Area: `Контакты клиента`
- Field: `E-mail`
- Date: 2026-07-29

## Observed field

- Main contact row contains field `E-mail`.
- `E-mail` has no required marker `*`.
- DOM `required=false`.
- One valid e-mail is accepted; invalid values and multiple e-mails in one field clear after blur without a visible message.

## E-mail scenarios

| Scenario | Exact test data | Trigger | Observed UI result | UI status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Valid e-mail | `one@example.ru` | `fill`, `Tab` blur | Value remained `one@example.ru`; field did not become invalid; no message. | `confirmed` | `evidence/screenshots/email-valid-one-example-ru.png` |
| Invalid e-mail without `@` | `testexample.ru` | `fill`, `Tab` blur | Value cleared to empty; field state `empty`; no visible message; field remains optional. | `confirmed` | `evidence/screenshots/email-invalid-no-at.png` |
| Invalid e-mail incomplete domain | `test@` | `fill`, `Tab` blur | Value cleared to empty; no visible message; field remains optional. | `confirmed` | `evidence/screenshots/email-invalid-test-at.png` |
| Invalid e-mail double `@` | `test@@example.ru` | `fill`, `Tab` blur | Value cleared to empty; no visible message; field remains optional. | `confirmed` | `evidence/screenshots/email-invalid-double-at.png` |
| Invalid e-mail with space | `test example@example.ru` | `fill`, `Tab` blur | Value cleared to empty; no visible message; field remains optional. | `confirmed` | `evidence/screenshots/email-invalid-space.png` |
| Two e-mails with semicolon | `one@example.ru; two@example.ru` | `fill`, `Tab` blur | Value cleared to empty; semicolon-separated multiple e-mails are not accepted in this field. | `confirmed` | `evidence/screenshots/email-two-semicolon.png` |
| Two e-mails with comma | `one@example.ru, two@example.ru` | `fill`, `Tab` blur | Value cleared to empty; comma-separated multiple e-mails are not accepted in this field. | `confirmed` | `evidence/screenshots/email-two-comma.png` |

## Automation notes

- Use one e-mail per field.
- Do not expect visible validation text for invalid e-mail inputs; assert clear-on-blur behavior instead.

