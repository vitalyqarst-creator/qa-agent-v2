# Test-design Coverage Metrics Format

`coverage-metrics.md` - split artifact в `work/test-design/<scope-slug>/`, который фиксирует измеримое применение test-design техник. Он создается после `Package Test Design Plan` и до `Writer Quality Gate` для каждого `initial_draft`; в revision mode обновляется, если findings меняют coverage classes, dimensions или gaps.

Цель artifact - не дать writer-у заменить технику общим заявлением "покрыто". Метрики не являются источником требований и не заменяют traceability matrix, `Coverage Obligation Table` или `Package Test Design Plan`; они только показывают, какие классы/ветки найдены, чем закрыты и где остался gap.

## Summary Table

| dimension | technique | applicable | source_ref | obligations_found | obligations_covered_by_tc | obligations_gap_or_unclear | coverage_strength | linked_artifact | residual_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `numeric` | `equivalence-boundary` | `yes` | `GSR 124; SRC-003` | `8` | `7` | `1` | `class-level` | `coverage-obligation-table.md` | `GAP-004: max value not defined` |
| `pairwise` | `combinatorial` | `yes` | `section 2.1` | `12 pairs` | `12 pairs` | `0` | `2-way` | `combinatorial-coverage-table.md` | `-` |

## Technique Detail Tables

Для каждой applicable technique добавь короткую detail table или ссылку на canonical split artifact:

- `equivalence/boundary/numeric/length`: список классов из `Coverage Obligation Table`.
- `decision-table`: количество rules/branches, covered rules, gap/unclear rules.
- `dependency/conditional-visibility`: количество controlling branches, transition branches и value reset/preserve gaps.
- `pairwise/combinatorial`: выбранная сила `2-way | 3-way | t-way`, количество факторов/значений, покрытые пары/тройки, high-risk additions.
- `status-lifecycle/state-model`: количество states, events, allowed transitions, forbidden transitions, unclear transitions.
- `table-list/file-upload/print-form-output`: количество source-backed variants/output obligations.
- `risk`: количество high/medium/low atoms и high-risk gaps.

## Rules

- Каждая строка `Test-design applicability matrix` с `applicable = yes` должна иметь строку в `coverage-metrics.md` или ссылку на artifact, где метрика уже посчитана.
- `obligations_found` считается по source-backed obligations и обязательным классам техники; `GAP-*` / `unclear` считается найденным obligation, а не отсутствием obligation.
- Нельзя считать obligation покрытым, если linked `TC-*` не проверяет соответствующую строку `Package Test Design Plan`.
- `coverage_strength = 2-way` не заменяет явно заданные бизнес-ветки decision table; такие ветки считаются separately.
- Если technique применима, но ее strength, classes или coverage count не могут быть посчитаны из-за недостающих данных, укажи `applicable = yes`, `obligations_gap_or_unclear > 0` и linked `GAP-*`.
- Writer не должен ставить `ready-for-review`, если applicable dimension отсутствует в metrics или metrics показывают uncovered obligation без `TC-*`/`GAP-*`.

