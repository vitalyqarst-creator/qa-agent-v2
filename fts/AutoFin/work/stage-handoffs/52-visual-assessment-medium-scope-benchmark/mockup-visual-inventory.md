# Mockup Visual Inventory

## Validator Contract Terms

| contract_terms | value | evidence |
| --- | --- | --- |
| `visible_blocks` | recorded | `Visual Inventory` |
| `visible_fields` | recorded | `Visual Inventory` |
| `visible_actions` | recorded | `Visual Inventory` |
| `interaction_hints` | recorded | `Interaction Hints` |
| `mockup_only_items` | recorded | `Mockup-Only Items` |
| `ft_conflicts` | recorded | `FT Conflicts` |
| `used_for_steps` | recorded | `Usage Decision` |
| `not_used_as_requirement_source` | `yes` | `Usage Decision` |

## Metadata

| item | value | evidence |
| --- | --- | --- |
| mockup_path | `fts/AutoFin/mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | SHA-256 `e3a20500405da5dc23fac1df2e8ee2ec77876723832cde8b688facb32de93622` |
| opened | `yes` | Codex `view_image`, original detail, 2026-07-13 |
| method | `visual-inspection` | full-height application questionnaire mockup |
| screen_name | `Анкета клиента. Максимальное состояние` | mockup caption |
| source_priority | `FT-over-mockup` | `AGENTS.md`; scope contract |

## Visual Inventory

| item_type | label_from_mockup | canonical_ft_name | visible_state | notes |
| --- | --- | --- | --- | --- |
| `visible_blocks` | `Визуальная оценка клиента` | block `Визуальная информация` / parameters | `visible` | Located near bottom after consent/checks. |
| `visible_fields` | toggle near visual assessment heading | `Визуальная информация` | `visible/editable` | Exact default/rules come from BSR 311-313. |
| `visible_fields` | grouped criteria checkboxes | `Параметры визуальной оценки` | `visible/editable` | Confirms checkbox interaction only. |
| `visible_fields` | `Комментарий` lines | standalone Appendix 1 comments | `visible/editable` | Consistent with saved analyst answer. |
| `visible_actions` | checkbox values including `Другое` | Appendix 1 criteria | `visible` | Requiredness comes from BSR 317, not mockup. |

## Interaction Hints

| element | interaction_hint | source | used_for_steps | limitation |
| --- | --- | --- | --- | --- |
| `Визуальная информация` | switch/toggle between `Нет` and `Да` | mockup + FT | `yes` | dependency oracle is FT-backed. |
| ordinary criterion | select checkbox | mockup + BSR 315 | `yes` | list values come from Appendix 1. |
| `Другое` | select checkbox, then enter text in revealed field | BSR 317 | `yes` | exact validation reaction is not shown. |
| standalone `Комментарий` | enter text in separate line/input | analyst answer + mockup | `yes` | do not merge with `Другое`. |

## Mockup-Only Items

| item | mockup_observation | ft_reference | handling |
| --- | --- | --- | --- |
| surrounding questionnaire layout | many unrelated blocks and example data | out of current scope | `ignore-out-of-scope` |
| colors/spacing/control styling | visible presentation details | not specified as behavior | `ignore-out-of-scope` |

## FT Conflicts

| item | ft_statement | mockup_observation | decision |
| --- | --- | --- | --- |
| none confirmed | FT defines rules; analyst answer defines standalone comments | visual layout is compatible | `FT wins` |

## Usage Decision

| item | value | evidence |
| --- | --- | --- |
| used_for_steps | `yes` | toggle/check/type interaction hints |
| not_used_as_requirement_source | `yes` | FT/analyst answer define behavior and oracle status |
| open_questions | `none` | no mockup conflict found |
