# Формат `requiredness-oracle-inventory.md`

`requiredness-oracle-inventory.md` фиксирует обязательность полей на scope stage и решает, нужна ли executable проверка, candidate TC для UI calibration или pure gap.

Артефакт создается рядом со `scope-contract.md`, если подтвержденный scope содержит колонку/признак обязательности (`О`, `required`, `mandatory`, `обязательное поле`) или правила, из которых выводится обязательность.

## Назначение

- не считать заполнение поля покрытием обязательности;
- заранее отделить видимый marker-oracle от empty-value validation oracle;
- создать candidate TC, если ФТ задает обязательность, но не задает точный UI-механизм проверки пустого значения;
- создать `GAP-*` или clarification request только если нельзя сформировать даже candidate TC;
- передать writer-у stable `scope_obligation_id`.

## Обязательные секции

- `## Контекст`
- `## Requiredness Oracle Inventory`
- `## Summary`
- `## Writer Handoff Rules`

## Таблица

| column | meaning |
| --- | --- |
| `scope_obligation_id` | Stable id вида `SO-REQ-001`. |
| `source_ref` | Раздел, таблица/строка, код требования, поле/условие. |
| `field_or_block` | Поле или блок. |
| `restriction_type` | `requiredness`, `conditional-requiredness`, `required-marker`, `other`. |
| `requiredness_source` | Колонка/фраза/правило, задающее обязательность. |
| `requiredness_class` | `empty-required-field`, `missing-required-block`, `condition-true-empty`, `condition-false-empty`, `marker-only`, etc. |
| `required_when` | `always`, `condition=true`, `condition=false`, конкретная ветка или `unclear`. |
| `marker_oracle_found` | `yes`, `no`, `not_applicable`. |
| `empty_value_oracle_found` | `yes`, `no`, `partial`. |
| `oracle_source` | `FT`, `support`, `mockup`, `common-validation-standard`, `not_found`. |
| `oracle_status` | `source-backed`, `common-standard-backed`, `analyst-confirmed`, `ui-calibration-required`, `observed-ui-backed`, `not-testable-gap`. |
| `decision` | `executable_tc`, `candidate_tc_required`, `gap_required`, `clarification_required`, `not_applicable`. |
| `planned_tc_or_gap` | Planned `TC-*`, `candidate:<scope_obligation_id>`, `GAP-*`, `clarification:<id>` or `not_applicable:<reason>`. |
| `gap_id` | `GAP-*` если есть parent gap/clarification; иначе `none_required:covered`. |
| `analyst_question` | Вопрос аналитику или `none_required`. |
| `handoff_rule` | Что writer обязан сделать. |
| `calibration_notes` | Что нужно зафиксировать при UI calibration или `not_applicable`. |

## Правила

- Одна строка = одна requiredness obligation для одного поля/ветки.
- Если обязательность покрывается только заполненным valid value, это не `executable_empty_value`; нужен visible marker, exact validation message, blocked transition, saved-state oracle или другой наблюдаемый результат.
- Если source задает обязательность, но exact UI oracle неизвестен, `decision = candidate_tc_required`, `oracle_status = ui-calibration-required`; writer обязан создать candidate TC по `negative-ui-calibration-policy.md`.
- `gap_required` используй только когда обязательность/ветка не имеет достаточного source anchor или нельзя сформировать проверяемый empty-value scenario.
- Parent `GAP-*` про общий неизвестный requiredness mechanism допустим, но child obligations должны оставаться отдельными строками со stable `scope_obligation_id`.
- Условная обязательность должна иметь отдельные строки для веток `condition=true` и `condition=false`, если обе ветки влияют на expected result.

## Минимальный шаблон

```md
## Контекст

- `scope_slug`: `...`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | requiredness_source | requiredness_class | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-001` | `Table 4 row 66; column О` | `Фамилия` | `requiredness` | `О = yes` | `empty-required-field` | `after add contact-person` | `no` | `no` | `not_found` | `ui-calibration-required` | `candidate_tc_required` | `candidate:SO-REQ-001` | `GAP-007` | `Как UI проверяет пустую Фамилию?` | `Create candidate TC; do not cover requiredness through valid value only.` | `Record marker/message/highlight/transition/save effect.` |

## Summary

- total_requiredness_obligations: `1`
- executable_tc: `0`
- candidate_tc_required: `1`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must carry every `scope_obligation_id` into Source Table Normalization / Coverage Obligation Table until mapped to `ATOM-*` or `GAP-*`.
- Writer must create candidate TC for `candidate_tc_required` rows and mark `Статус oracle: ui-calibration-required`.
- Writer must not mark requiredness covered by a positive value-entry TC unless a marker or empty-value oracle is source-backed.
```
