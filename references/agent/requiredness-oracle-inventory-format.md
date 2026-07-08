# Формат `requiredness-oracle-inventory.md`

`requiredness-oracle-inventory.md` фиксирует обязательность полей на scope stage и проверяет, есть ли source-backed oracle для пустого значения или видимого маркера обязательности.

Артефакт создается рядом со `scope-contract.md`, если подтвержденный scope содержит колонку/признак обязательности (`О`, `required`, `mandatory`, `обязательное поле`) или правила, из которых выводится обязательность.

## Назначение

- не считать заполнение поля покрытием обязательности;
- заранее отделить видимый marker-oracle от empty-value validation oracle;
- создать `GAP-*` или clarification request, если ФТ задает обязательность, но не задает механизм проверки пустого значения;
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
| `requiredness_source` | Колонка/фраза/правило, задающее обязательность. |
| `required_when` | `always`, `condition=true`, `condition=false`, конкретная ветка или `unclear`. |
| `marker_oracle_found` | `yes`, `no`, `not_applicable`. |
| `empty_value_oracle_found` | `yes`, `no`, `partial`. |
| `oracle_source` | `FT`, `support`, `mockup`, `common-validation-standard`, `not_found`. |
| `decision` | `executable_marker`, `executable_empty_value`, `gap_required`, `clarification_required`, `not_applicable`. |
| `gap_id` | `GAP-*` если oracle отсутствует; иначе `none_required:covered`. |
| `analyst_question` | Вопрос аналитику или `none_required`. |
| `handoff_rule` | Что writer обязан сделать. |

## Правила

- Одна строка = одна requiredness obligation для одного поля/ветки.
- Если обязательность покрывается только заполненным valid value, это не `executable_empty_value`; нужен visible marker, exact validation message, blocked transition, saved-state oracle или другой наблюдаемый результат.
- Если `empty_value_oracle_found = no`, создавай/link `GAP-*` или clarification request.
- Условная обязательность должна иметь отдельные строки для веток `condition=true` и `condition=false`, если обе ветки влияют на expected result.

## Минимальный шаблон

```md
## Контекст

- `scope_slug`: `...`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Requiredness Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | requiredness_source | required_when | marker_oracle_found | empty_value_oracle_found | oracle_source | decision | gap_id | analyst_question | handoff_rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-REQ-001` | `Table 4 row 66; column О` | `Фамилия` | `О = yes` | `after add contact-person` | `no` | `no` | `not_found` | `gap_required` | `GAP-007` | `Как UI проверяет пустую Фамилию?` | `Do not cover requiredness through valid filled value only.` |

## Summary

- total_requiredness_obligations: `1`
- executable_marker: `0`
- executable_empty_value: `0`
- gap_required: `1`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must carry every `scope_obligation_id` into Source Table Normalization / Coverage Obligation Table until mapped to `ATOM-*` or `GAP-*`.
- Writer must not mark requiredness covered by a positive value-entry TC unless a marker or empty-value oracle is source-backed.
```
