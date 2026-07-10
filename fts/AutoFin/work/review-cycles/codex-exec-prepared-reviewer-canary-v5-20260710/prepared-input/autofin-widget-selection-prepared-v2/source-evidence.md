# Prepared Source Evidence

- package_id: `autofin-widget-selection-prepared-v2`

## Confirmed scope boundaries

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-contract.md`
- source_sha256: `ad3637a95782f72d4a410d49439ea1a2d74aedc75bd350a12324282554c60022`
- selectors: `## Что Входит В Scope, ## Что Не Входит В Scope, ## Внутренние Рабочие Пакеты`

## Что Входит В Scope

- Row `Список`: values come from a dictionary and only one value can be selected.
- Row `Список с множественным выбором`: values come from a dictionary and several values can be selected.
- Statement after the data type table: default widget values are absent and interpreted as `NULL`.

## Что Не Входит В Scope

- Other data type restrictions from section `3`.
- Screen-specific field visibility, requiredness, role model rules or dictionaries unless already present in selected rows.
- Save-flow, persistence, database storage, API or async behavior.
- Previous canary and generated test-case artifacts.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | UI widget value selection constraints | `SRC-001`, `SRC-002`, `SRC-003` | Single-select list, multi-select list, default empty/NULL widget state | `field-property coverage` | Canonical test cases and writer design artifacts for selected rows | `no` |

## Selected source rows

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-row-inventory.md`
- source_sha256: `766b9ae812bbe0acb59bdc8faa7c6e39e46d4b82abdba710abf7bd4983003b9d`
- selectors: `## Source Row Inventory`

## Source Row Inventory

| source_row_id | source_anchor | docx_anchor | row_type | source_text | bsr_codes | downstream_decision |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | XHTML table row `Список` | DOCX section `3`, table row `Список` | `data-type-restriction` | `Значения из справочника. Возможен выбор только одного значения` | none | `candidate_tc_required` |
| `SRC-002` | XHTML table row `Список с множественным выбором` | DOCX section `3`, table row `Список с множественным выбором` | `data-type-restriction` | `Значения из справочника. Возможен выбор нескольких значения` | none | `candidate_tc_required` |
| `SRC-003` | XHTML paragraph after data type table | DOCX section `3`, paragraph after data type table | `default-value-rule` | `По умолчанию значения в виджетах отсутствуют и интерпретируются как NULL` | none | `candidate_tc_required` |

## Parity decision and limitations

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/source-parity-check.md`
- source_sha256: `65e3c7df70694598c2cca004c09bb008395bbf8f26d43336d1805e2e433cb43d`
- selectors: `## Structure Parity, ## Limitations`

## Structure Parity

| item | DOCX | XHTML | PDF | decision |
| --- | --- | --- | --- | --- |
| Section `3 Ограничения` | found | found | found | `pass` |
| Data type restrictions table | found | found | found on page 5 | `pass` |
| Row `Список` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Row `Список с множественным выбором` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Default widget values paragraph | found | found | found on page 5 | `pass` |

## Limitations

- PDF structural cross-check is sufficient for section/block presence, but row-level extraction is not clean enough to use as primary source.
- No discrepancy between DOCX and XHTML was found for the selected source rows.

## Preserved scope risk

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/scope-coverage-gaps.md`
- source_sha256: `12ad20415578f0363bfcf377c531874edb113c6123312d63dbc599d92980e65c`
- selectors: `RISK-001`

## Non-Blocking Risks To Preserve

| risk_id | source_ref | risk | downstream_handling |
| --- | --- | --- | --- |
| `RISK-001` | `SRC-001`..`SRC-003` | Selected section defines generic widget constraints, not a concrete screen field. | Writer/reviewer must not invent unsupported field names or dictionary values; fixture needs must be explicit. |

## Negative oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/negative-oracle-inventory.md`
- source_sha256: `f199143a0e668f05aad5e3f6b07938e198e753040a7a928bfdeb1ac3bd9ff8f6`
- selectors: `SO-NEG-NA-001`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `none` | Selected rows define positive selection capabilities and default empty state; they do not define invalid input classes. | `not_derived` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-negative-class-in-selected-source` | `none_required:covered` | `none_required` | `Do not create negative TC from this scope unless a later source adds invalid classes.` | `not_applicable` |

## Requiredness oracle boundary

- source_path: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/requiredness-oracle-inventory.md`
- source_sha256: `a35f1c41817890c86c8e1666d3ffb717c3042ef2da20384c855a03f66260a729`
- selectors: `SO-REQ-NA-001`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-NA-001` | `SRC-001`..`SRC-003` | `generic widget constraints` | `other` | `not_present` | `none` | `not_applicable` | `not_applicable` | `no` | `not_found` | `not-testable-gap` | `not_applicable` | `not_applicable:no-requiredness-in-selected-source` | `none_required:covered` | `none_required` | `Do not create requiredness TC from this scope unless a later source adds requiredness.` | `not_applicable` |
