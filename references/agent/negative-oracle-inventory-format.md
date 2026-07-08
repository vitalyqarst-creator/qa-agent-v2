# Формат `negative-oracle-inventory.md`

`negative-oracle-inventory.md` фиксирует на scope stage ограничения ввода и классы недопустимых значений, которые могут стать негативными тестами только при наличии наблюдаемого oracle.

Артефакт создается рядом со `scope-contract.md`, если подтвержденный scope содержит ограничения формата, длины, даты, e-mail, числового ввода, допустимых символов или allowed values.

## Назначение

- выявить blocked negative obligations до writer stage;
- отделить проверяемые negative cases от требований без UI/API oracle;
- передать writer-у stable `scope_obligation_id`, чтобы downstream `ATOM-*`, `GAP-*` и Coverage Obligation Table не теряли связь со scope-analysis;
- сформировать вопросы аналитику до написания synthetic TC.

## Обязательные секции

- `## Контекст`
- `## Negative Oracle Inventory`
- `## Summary`
- `## Writer Handoff Rules`

## Таблица

| column | meaning |
| --- | --- |
| `scope_obligation_id` | Stable id вида `SO-NEG-001`; сохраняется в writer artifacts до маппинга в `ATOM-*` / `GAP-*`. |
| `source_ref` | Раздел, таблица/строка, код требования, поле/условие. |
| `field_or_block` | Поле, действие или блок, к которому относится ограничение. |
| `restriction_type` | `numeric-format`, `length`, `text-symbols`, `email-format`, `date-validity-window`, `allowed-values`, `format-mask`, `other`. |
| `invalid_class` | Один класс недопустимого значения: `letters`, `spaces`, `special-chars`, `decimal-separator`, `sign`, `too-short`, `too-long`, `second-email`, `future-date`, `not-in-list`, etc. |
| `source_statement` | Краткая source-backed формулировка ограничения. |
| `representative_invalid_value` | Конкретное значение, если оно выводится безопасно; иначе `not_derived`. |
| `observable_oracle_found` | `yes`, `no`, `partial`. |
| `oracle_source` | Источник oracle: `FT`, `support`, `mockup`, `common-validation-standard`, `not_found`. |
| `decision` | `executable_candidate`, `gap_required`, `clarification_required`, `not_applicable`. |
| `gap_id` | `GAP-*` если `decision != executable_candidate`; иначе `none_required:covered`. |
| `analyst_question` | Вопрос аналитику или `none_required`. |
| `handoff_rule` | Что writer обязан сделать: создать TC, создать/сохранить GAP, не домысливать oracle. |

## Правила

- Одна строка = один invalid class. Не объединяй `letters/spaces/special chars` в одну строку.
- Если `observable_oracle_found = no`, `decision` должен быть `gap_required` или `clarification_required`, а `gap_id` должен ссылаться на `scope-coverage-gaps.md`.
- `representative_invalid_value` не заменяет oracle. Значение `12A00` полезно только если известно, как система должна реагировать.
- Макет не задает validation oracle, если он не подтвержден ФТ/support/common standard.
- Если общий validation standard найден, укажи его в `oracle_source` и передай writer-у как разрешенный источник.

## Минимальный шаблон

```md
## Контекст

- `scope_slug`: `...`
- `scope_contract`: `scope-contract.md`
- `scope_coverage_gaps`: `scope-coverage-gaps.md`

## Negative Oracle Inventory

| scope_obligation_id | source_ref | field_or_block | restriction_type | invalid_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | decision | gap_id | analyst_question | handoff_rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-001` | `Table 4 row 71; BSR 185` | `Дата рождения` | `date-validity-window` | `future-date` | `Дата не должна быть больше текущей даты` | `tomorrow` | `no` | `not_found` | `gap_required` | `GAP-006` | `Как UI отклоняет будущую дату?` | `Do not create executable TC until oracle is source-backed.` |

## Summary

- total_negative_obligations: `1`
- executable_candidates: `0`
- gap_required: `1`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must carry every `scope_obligation_id` into Source Table Normalization / Coverage Obligation Table until mapped to `ATOM-*` or `GAP-*`.
- Writer must not create executable negative TC for `gap_required` rows without new source evidence.
```
