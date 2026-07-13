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
| used_for_steps | `yes` | `Usage Decision` |
| not_used_as_requirement_source | `yes` | `Usage Decision` |

## Metadata

| item | value | evidence |
| --- | --- | --- |
| mockup_path | `fts/AutoFin/mockups/Рисунок 1 Макет раздела меню Заявки в системе.jpg` | SHA-256 `82029a5f393a7ffb8f92d60083ce3e9bfef045dd73963443a01adff66de48f60` |
| opened | `yes` | visual inspection, 2026-07-13 |
| method | `image-viewer` | original-resolution inspection |
| screen_name | `Заявки в Системе` | mockup caption and visible title |
| source_priority | `FT-over-mockup` | project policy |

## Visual Inventory

| item_type | label_from_mockup | canonical_ft_name | visible_state | notes |
| --- | --- | --- | --- | --- |
| `visible_blocks` | `Фильтры`; `Заявки` | search context; result table | `visible` | Filters above results table. |
| `visible_actions` | `ОЧИСТИТЬ`; `НАЙТИ` | `Очистить`; search | `visible` | BSR 32 action label matches semantically. |
| `visible_fields` | client/date/phone/passport/VIN/application/status/office/author filters | filter controls | `visible` | Use any displayed applicable filter; exact field is not a BSR 32 rule. |
| `visible_actions` | sortable table headers; page controls; row information icons | sort/pagination/row context | `visible` | Interaction hints for creating observable pre-state. |

## Interaction Hints

| element | interaction_hint | source | used_for_steps | limitation |
| --- | --- | --- | --- | --- |
| filter | enter/select a value in one visible filter | `mockup` | `yes` | No filter-specific validation asserted. |
| table header | click a sortable column header | `mockup` | `yes` | Exact default sort not inferred. |
| pagination | move from the initial page when another page exists | `mockup` | `yes` | Fixture must contain enough rows. |
| result row | select one displayed row | `mockup` | `yes` | Selection rendering not prescribed. |
| `ОЧИСТИТЬ` | click the button after creating target state | `mockup + FT` | `yes` | Expected reset comes only from BSR 32. |

## Mockup-Only Items

| item | mockup_observation | ft_reference | handling |
| --- | --- | --- | --- |
| exact filter list/layout | multiple named controls and two-column arrangement | outside BSR 32 | `ignore-out-of-scope` |
| credit calculator/create application | header actions | outside BSR 32 | `ignore-out-of-scope` |

## FT Conflicts

| item | ft_statement | mockup_observation | decision |
| --- | --- | --- | --- |
| `none` | BSR 32 button `Очистить` | `ОЧИСТИТЬ` | `match; FT wins for behavior` |

## Usage Decision

| item | value | evidence |
| --- | --- | --- |
| used_for_steps | `yes` | filter, sort, pagination, row selection and click mechanics |
| not_used_as_requirement_source | `yes` | mockup refines interaction only; FT defines reset behavior |
| open_questions | `none` | no mockup/FT conflict inside scope |
