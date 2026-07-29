# Phone type UI evidence

## Scope

- Area: `Контакты клиента`
- Field: `Тип телефона`
- Date: 2026-07-29

## Observed behavior

- `Тип телефона` is not visible in the initial/main phone row.
- Pressing `Добавить телефон` adds a repeated phone row containing:
  - `Тип телефона *`
  - `Номер телефона *`
  - delete action `-`
- `Тип телефона` is required: DOM `required=true`; empty state is `empty required ... invalid`.
- Dropdown opens on focus/click in `Тип телефона`.

## Dropdown values

Visible values:

- `Мобильный`
- `Рабочий`
- `Домашний`

## Selection scenario

| Scenario | Exact test data | Trigger | Observed UI result | UI status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Open phone type list | focus `Тип телефона` | click/focus | Dropdown opened and showed `Мобильный`, `Рабочий`, `Домашний`. | `confirmed` | `evidence/screenshots/phone-type-options.png` |
| Select phone type | `Мобильный` | exact DOM click on visible dropdown item, then `Tab` blur | Field value became `Мобильный`; field state `valid`; value stayed after transition to `Номер телефона`. | `confirmed` | `evidence/screenshots/phone-type-mobile-selected-dom.png` |
| First strict text click attempt | `Мобильный` | `text=Мобильный`, then `Tab` | Strict locator collided with `Мобильный телефон`; value remained empty and invalid. This is an automation locator issue, not UI failure. | `blocked-observability` | `evidence/screenshots/phone-type-mobile-selected.png` |

## Automation notes

- Use a dropdown-item locator scoped to `li.ui-menu-item` or equivalent, not generic `text=Мобильный`, because `Мобильный телефон` labels collide with the option text.
- Positive scenario can use `Мобильный`.

