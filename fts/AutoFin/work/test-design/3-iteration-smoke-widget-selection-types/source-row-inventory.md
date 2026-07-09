# Source Row Inventory

| source_row_id | source_anchor | source_text | writer_scope_decision | linked_atoms | linked_tc_or_gap |
| --- | --- | --- | --- | --- | --- |
| `SRC-001` | `source/FT4AutoFinFinal.xhtml`, section `3`, row `Список`; DOCX parity confirmed by handoff | `Значения из справочника. Возможен выбор только одного значения` | `candidate_tc_required` | `ATOM-001`; `ATOM-002` | `TC-WIDGET-SELECTION-TYPES-001` |
| `SRC-002` | `source/FT4AutoFinFinal.xhtml`, section `3`, row `Список с множественным выбором`; DOCX parity confirmed by handoff | `Значения из справочника. Возможен выбор нескольких значения` | `candidate_tc_required` | `ATOM-003`; `ATOM-004` | `TC-WIDGET-SELECTION-TYPES-002` |
| `SRC-003` | `source/FT4AutoFinFinal.xhtml`, section `3`, paragraph after data type table; DOCX parity confirmed by handoff | `По умолчанию значения в виджетах отсутствуют и интерпретируются как NULL` | `split_observable_and_gap` | `ATOM-005`; `ATOM-006` | `TC-WIDGET-SELECTION-TYPES-003`; `GAP-001` |

## Writer Notes

- `source-excerpt.writer-r1.md` was generated as diagnostic source evidence for XHTML rows.
- The DOCX confirmation is taken from `source-row-inventory.md` and `source-parity-check.md` in the stage handoff; the stage-local helper could not extract these DOCX rows directly.
