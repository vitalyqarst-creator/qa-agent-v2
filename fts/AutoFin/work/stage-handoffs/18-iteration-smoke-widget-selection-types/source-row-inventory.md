# Source Row Inventory

## Context

- FT package: `AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- Main source: `source/FT4AutoFinFinal.xhtml`
- Authoritative source: `source/FT4AutoFinFinal.docx`
- Section: `3 Ограничения`
- Table/block: `Ограничения по типам данных`

## Source Row Inventory

| source_row_id | source_anchor | docx_anchor | row_type | source_text | bsr_codes | downstream_decision |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | XHTML table row `Список` | DOCX section `3`, table row `Список` | `data-type-restriction` | `Значения из справочника. Возможен выбор только одного значения` | none | `candidate_tc_required` |
| `SRC-002` | XHTML table row `Список с множественным выбором` | DOCX section `3`, table row `Список с множественным выбором` | `data-type-restriction` | `Значения из справочника. Возможен выбор нескольких значения` | none | `candidate_tc_required` |
| `SRC-003` | XHTML paragraph after data type table | DOCX section `3`, paragraph after data type table | `default-value-rule` | `По умолчанию значения в виджетах отсутствуют и интерпретируются как NULL` | none | `candidate_tc_required` |

## Extraction Notes

- XHTML extraction was performed with `bs4` against `source/FT4AutoFinFinal.xhtml`.
- DOCX extraction was performed with `test_case_agent.resolve_sections()` against `source/FT4AutoFinFinal.docx`.
- PDF page 5 confirms the selected block but is not used as row-level evidence because extracted text is wrapped and partially split.
