# Формат `negative-oracle-inventory.md`

`negative-oracle-inventory.md` фиксирует на scope stage ограничения ввода и классы недопустимых значений, которые должны стать executable TC, candidate TC или явным gap/clarification.

Артефакт создается рядом со `scope-contract.md`, если подтвержденный scope содержит ограничения формата, длины, даты, e-mail, числового ввода, допустимых символов или allowed values.

## Назначение

- выявить negative obligations до writer stage;
- отделить executable negative cases от calibration candidates и pure gaps;
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
| `negative_class` | Один класс недопустимого значения: `letters`, `spaces`, `special-chars`, `decimal-separator`, `sign`, `too-short`, `too-long`, `second-email`, `future-date`, `not-in-list`, etc. Legacy alias: `invalid_class`. |
| `source_statement` | Краткая source-backed формулировка ограничения. |
| `representative_invalid_value` | Конкретное значение, если оно выводится безопасно; иначе `not_derived`. |
| `observable_oracle_found` | `yes`, `no`, `partial`. |
| `oracle_source` | Источник oracle: `FT`, `support`, `mockup`, `common-validation-standard`, `not_found`. |
| `oracle_status` | `source-backed`, `common-standard-backed`, `analyst-confirmed`, `ui-calibration-required`, `observed-ui-backed`, `not-testable-gap`. |
| `decision` | `executable_tc`, `candidate_tc_required`, `gap_required`, `clarification_required`, `not_applicable`. |
| `planned_tc_or_gap` | Planned `TC-*`, `candidate:<scope_obligation_id>`, `GAP-*`, `clarification:<id>` or `not_applicable:<reason>`. |
| `gap_id` | `GAP-*` если есть parent gap/clarification; иначе `none_required:covered`. |
| `analyst_question` | Вопрос аналитику или `none_required`. |
| `handoff_rule` | Что writer обязан сделать: создать TC, создать/сохранить GAP, не домысливать oracle. |
| `calibration_notes` | Что нужно зафиксировать при UI calibration или `not_applicable`. |

## Правила

- Одна строка = один invalid class. Не объединяй `letters/spaces/special chars` в одну строку.
- Если source задает restriction, но exact UI oracle неизвестен, `decision = candidate_tc_required`, `oracle_status = ui-calibration-required`; writer обязан создать candidate TC по `negative-ui-calibration-policy.md`.
- `gap_required` используй только когда нельзя сформировать даже candidate TC или отсутствует проверяемая obligation/input class.
- Parent `GAP-*` про общий неизвестный validation oracle допустим, но child obligations должны оставаться отдельными строками со stable `scope_obligation_id`.
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

| scope_obligation_id | source_ref | field_or_block | restriction_type | negative_class | source_statement | representative_invalid_value | observable_oracle_found | oracle_source | oracle_status | decision | planned_tc_or_gap | gap_id | analyst_question | handoff_rule | calibration_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SO-NEG-001` | `Table 4 row 71; BSR 185` | `Дата рождения` | `date-validity-window` | `future-date` | `Дата не должна быть больше текущей даты` | `tomorrow` | `no` | `not_found` | `ui-calibration-required` | `candidate_tc_required` | `candidate:SO-NEG-001` | `GAP-006` | `Как UI отклоняет будущую дату?` | `Create candidate TC; do not invent exact UI reaction.` | `Record validation trigger, UI reaction, message if any, transition/save effect.` |

## Summary

- total_negative_obligations: `1`
- executable_tc: `0`
- candidate_tc_required: `1`
- gap_required: `0`
- clarification_required: `0`

## Writer Handoff Rules

- Writer must carry every `scope_obligation_id` into Source Table Normalization / Coverage Obligation Table until mapped to `ATOM-*` or `GAP-*`.
- Writer must create candidate TC for `candidate_tc_required` rows and mark `Статус oracle: ui-calibration-required`.
- Writer must not create executable negative TC for `gap_required` rows without new source evidence.
```
