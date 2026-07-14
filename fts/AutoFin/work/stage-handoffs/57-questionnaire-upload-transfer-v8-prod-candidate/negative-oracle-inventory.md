# Negative Oracle Inventory — Questionnaire Upload Transfer V8 Prod Candidate

## Контекст

- `scope_slug`: `questionnaire-upload-transfer-v8-prod-candidate`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-QUT-001` | `BSR 210; SRC-QUT-002.P07` | `Анкета клиента` | `other` | `oversize-file` | Файл больше 40 МБ не загружается. | валидный PDF размером `50 МБ`; он больше лимита при decimal и binary interpretation | `yes` | `FT` | `source-backed` | `executable_tc` | `TC-QUT-007` | `none_required:covered` | `none_required` | Создать один negative TC; не выдавать fixture за exact boundary convention. | `not_applicable` |
| `SO-NEG-QUT-002` | `BSR 210; SRC-QUT-002.P08` | `Анкета клиента` | `allowed-values` | `unsupported-format` | Допустимы только jpg, png, pdf. | `questionnaire-invalid.txt`, 1 КБ | `yes` | `FT` | `source-backed` | `executable_tc` | `TC-QUT-008` | `none_required:covered` | `none_required` | Создать один negative TC с точным source-backed сообщением. | `not_applicable` |

## Summary

- total_negative_obligations: `2`
- executable_tc: `2`
- candidate_tc_required: `0`
- gap_required: `0`
- clarification_required: `0`
- exact positive boundary: `GAP-QUT-001`, не относится к negative inventory.

## Writer Handoff Rules

- Сохранить `SO-NEG-QUT-001` и `SO-NEG-QUT-002` до маппинга в соответствующие `ATOM-*` / `OBL-*`.
- Использовать точный oracle `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат jpg, png, pdf, размер не более 40 МБ`.
- Не преобразовывать `40 МБ` в байты; `50 МБ` — заведомо oversized fixture, не product boundary.
