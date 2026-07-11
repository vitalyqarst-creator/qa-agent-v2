# Mockup Visual Inventory

## Validator Contract Terms

| contract_terms | value | evidence |
| --- | --- | --- |
| visible_blocks | recorded | `Visual Inventory` |
| visible_fields | recorded | `Visual Inventory` |
| visible_actions | recorded | `Visual Inventory` |
| interaction_hints | recorded | `Interaction Hints` |
| mockup_only_items | recorded | `Mockup-Only Items` |
| ft_conflicts | recorded | `FT Conflicts` |
| used_for_steps | recorded | `Usage Decision` |
| not_used_as_requirement_source | `yes` | `Usage Decision` |

## Metadata

| item | value | evidence |
| --- | --- | --- |
| mockup_path | `mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg` | opened via local image viewer on `2026-07-11` |
| mockup_path | `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | opened via local image viewer on `2026-07-11` |
| opened | `yes` | visual inspection at original detail |
| method | `visual-inspection` | Codex local image viewer |
| screen_name | Карточка новой заявки | visible title |
| source_priority | `FT-over-mockup` | project policy |

## Visual Inventory

| item_type | label_from_mockup | canonical_ft_name | visible_state | notes |
| --- | --- | --- | --- | --- |
| visible_blocks | top horizontal summary with five values | Краткая информация с калькулятора | visible in both mockups | Shows credit amount, VIN, rate, monthly payment and term positions. Example values are mockup-only. |
| visible_actions | `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` | Кредитный калькулятор | visible at top in both mockups | Button-like control; click outcome comes only from `BSR 46`. |
| visible_fields | five top summary values | parameters from `BSR 44` | visible | Layout hint only; value correctness comes from FT and test fixture. |

## Interaction Hints

| element | interaction_hint | source | used_for_steps | limitation |
| --- | --- | --- | --- | --- |
| top summary widget | click visible summary area | mockup + `BSR 45` | yes | Transition target and behavior come from FT. |
| `КРЕДИТНЫЙ КАЛЬКУЛЯТОР` | click control | mockup + `BSR 46` | yes | Window content and mapping are not inferred from mockup. |

## Mockup-Only Items

| item | mockup_observation | ft_reference | handling |
| --- | --- | --- | --- |
| example values | Numeric credit data and VIN are populated in the top strip. | `BSR 44` defines parameter names, not these concrete examples. | ignore values as requirements |
| exact layout/style | Top strip and white pill button placement. | No layout/style obligation in selected rows. | interaction hint only |

## FT Conflicts

| item | ft_statement | mockup_observation | decision |
| --- | --- | --- | --- |
| none confirmed | `BSR 43–46` | Mockups are compatible with visible summary and calculator button. | FT wins |

## Usage Decision

| item | value | evidence |
| --- | --- | --- |
| used_for_steps | `yes` | locating and clicking summary/button only |
| not_used_as_requirement_source | `yes` | all expected results come from Final FT |
| open_questions | `scope-coverage-gaps.md` | exact prefill mapping remains source gap |
