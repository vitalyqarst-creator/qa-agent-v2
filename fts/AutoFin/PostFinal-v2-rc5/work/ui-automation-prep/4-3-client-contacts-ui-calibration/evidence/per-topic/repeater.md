# Phone repeater UI evidence

## Scope

- Area: `Контакты клиента`
- Action: `Добавить телефон`
- Date: 2026-07-29

## Observed behavior

| Scenario | Exact action/data | Trigger | Observed UI result | UI status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Initial repeater state | No additional phone row | Open fresh application card | Only main row is visible: `Мобильный телефон *`, `E-mail`, and action `Добавить телефон`. | `confirmed` | `evidence/screenshots/contacts-initial.png` |
| Add phone via ref click | Click ref for `Добавить телефон` | Playwright ref click | No new row appeared. This looked like locator/action targeting issue rather than a stable UI result. | `blocked-observability` | `evidence/screenshots/repeater-after-add-phone.png` |
| Add phone via visible button DOM click | `.button.ui-button.additional` with text `ДОБАВИТЬ ТЕЛЕФОН` | button click | A new row appeared with `Тип телефона *`, `Номер телефона *`, and delete action `-`. | `confirmed` | `evidence/screenshots/repeater-after-add-phone-dom-click.png` |
| Delete added phone row | Click `-` in added row | button click | Added row disappeared; only main `Мобильный телефон` and `E-mail` remained. | `confirmed` | `evidence/screenshots/repeater-after-delete-phone.png` |

## Automation notes

- The stable action label is `Добавить телефон`.
- Use a selector scoped to the visible `.button.ui-button.additional` with text `ДОБАВИТЬ ТЕЛЕФОН`.
- Added row delete action is visible as `-`.

