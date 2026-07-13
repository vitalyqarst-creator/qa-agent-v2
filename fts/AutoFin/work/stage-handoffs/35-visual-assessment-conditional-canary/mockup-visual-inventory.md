# Mockup Visual Inventory

## Validator Contract Terms

| contract_terms | value | evidence |
| --- | --- | --- |
| visible_blocks | recorded | `Visual Inventory` |
| visible_fields | recorded | `Visual Inventory` |
| visible_actions | recorded | `Interaction Hints` |
| interaction_hints | recorded | `Interaction Hints` |
| mockup_only_items | recorded | `Mockup-Only Items` |
| ft_conflicts | recorded | `FT Conflicts` |
| used_for_steps | `no` | `Usage Decision` |
| not_used_as_requirement_source | `yes` | `Usage Decision` |

## Metadata

| field | value |
| --- | --- |
| canonical inventory reviewed | `work/stage-handoffs/17-visual-assessment-criteria/mockup-visual-inventory.md` |
| mockup_path | `fts/AutoFin/mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` |
| opened | `yes`, подтверждено canonical inventory после visual inspection |
| method | `reuse of canonical visual-inspection inventory; no new image inference` |
| screen_name | `Параметры визуальной оценки` |
| source priority | `FT-over-mockup` |
| used_for_steps | `no` |
| not_used_as_requirement_source | `yes` |

## Decision

- Старый inventory содержит PreFinal-код `BSR 309`; в активном Final source соответствующее правило имеет код `BSR 317`.
- Canary использует точные Final source properties и dictionary fixtures; layout из макета не нужен для шагов.
- Макет не подтверждает validation feedback, persistence или иные дополнительные expected results.

## Visual Inventory

| item_type | label | visible_state | handling |
| --- | --- | --- | --- |
| visible_blocks | анкета клиента / визуальная оценка | visible in maximum-state mockup | support context only |
| visible_fields | `Другое`; `Комментарий` | visible/conditional according to canonical inventory | not used for canary steps |

## Interaction Hints

| element | hint | used_for_steps | limitation |
| --- | --- | --- | --- |
| `Другое` | checkbox-like selection | `no` | Final FT `BSR 317` defines behavior |
| `Комментарий` | text input | `no` | no validation mechanism inferred |

## Mockup-Only Items

| item | observation | handling |
| --- | --- | --- |
| layout/example values | maximum-state layout may show surrounding values | ignored; does not define business rules |

## FT Conflicts

- Визуальный конфликт не установлен.
- Source-version mismatch в коде требования обработан заменой на Final traceability, а не переносом старого кода.

## Usage Decision

| item | value | rationale |
| --- | --- | --- |
| used_for_steps | `no` | Exact state transitions and fixtures are fully source-backed |
| not_used_as_requirement_source | `yes` | DOCX/XHTML/PDF Final source set has priority |
| open_questions | `GAP-COND-001` | Mockup does not close requiredness feedback |
