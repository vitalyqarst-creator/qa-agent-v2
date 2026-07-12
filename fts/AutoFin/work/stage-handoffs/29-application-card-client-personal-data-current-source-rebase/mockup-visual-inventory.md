# Mockup Visual Inventory

## Metadata

| item | value | evidence |
| --- | --- | --- |
| mockup_path | `mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg`; `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | local files opened visually |
| opened | `yes` | Codex image viewer, 2026-07-12 |
| method | `visual-inspection` | original-resolution inspection |
| screen_name | `Анкета клиента: минимальное/максимальное состояние` | captions |
| source_priority | `FT-over-mockup` | project policy |

## Visual Inventory

| item_type | label_from_mockup | canonical_ft_name | visible_state | notes |
| --- | --- | --- | --- | --- |
| visible_blocks | `Персональные данные` | same | `visible` | top client block |
| visible_fields | `Фамилия`; `Имя`; `Отчество`; `ID клиента`; `Дата рождения`; `Пол` | same | `visible` | ID visually readonly; business properties come from FT |
| visible_fields | `Предыдущая фамилия`; `Предыдущее имя`; `Предыдущее отчество` | same | `conditional` | visible in maximum state when changed-FIO toggle is on |
| visible_actions | `Клиент менял ФИО` | same | `toggle` | interaction hint only |

## Interaction Hints

- `interaction_hints`: recorded below.

| element | interaction_hint | source | used_for_steps | limitation |
| --- | --- | --- | --- | --- |
| text/date fields | type/select date | mockup | yes | no validation oracle |
| `Пол` | select radio option | mockup | yes | values confirmed by support dictionary |
| changed-FIO | toggle between `Нет/Да` | mockup | yes | visibility rules come from FT |

## Mockup-Only Items

- `mockup_only_items`: recorded below.

| item | mockup_observation | ft_reference | handling |
| --- | --- | --- | --- |
| Sample personal values | mockup contains example names/dates | not a fixed FT dataset | ignore as test data |
| Element placement/order | visual layout shown | not a business rule | alias/layout hint only |

## FT Conflicts

- `ft_conflicts`: recorded below.

| item | ft_statement | mockup_observation | decision |
| --- | --- | --- | --- |
| none | no material conflict identified | - | FT wins if later conflict appears |

## Usage Decision

| item | value | evidence |
| --- | --- | --- |
| used_for_steps | `yes` | field/toggle mechanics |
| not_used_as_requirement_source | `yes` | FT/support define behavior |
| open_questions | `GAP-001`; `GAP-002` | validation/requiredness oracle absent from mockup |
