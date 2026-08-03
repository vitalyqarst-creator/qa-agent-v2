# Source assertion review receipt v6 rule card

Компактный output-контракт независимого source reviewer-а. JSON Schema задаёт
shape; эти relational invariants обязательны одновременно и проверяются
каноническим post-validator-ом один раз после model call.

## Полный набор и агрегаты

- `version = 6`; `manifest_digest` равен exact digest входного manifest-а.
- `assertion_reviews` содержит каждый manifest `assertion_id` ровно один раз:
  missing, unknown и duplicate id запрещены.
- Каждый `dimension_verdicts` содержит ровно 13 keys из semantic rule card;
  каждое значение — `verified | incorrect`.
- Per-assertion `verdict = incorrect`, если хотя бы одна dimension incorrect;
  иначе ровно `verified`.
- `decision = accepted` тогда и только тогда, когда все assertion verdicts,
  `source_inventory_review.verdict` и `scope_boundary_review.verdict` равны
  `verified`. При любом incorrect решение ровно `changes-required`.
- Для любого verified assertion/inventory/boundary review
  `required_change` равен literal `none_required`. Для incorrect он не равен
  `none_required` и содержит конкретное содержательное исправление. `note` всегда
  содержательная (используй минимум 20 символов, а не checkbox/placeholder).

## Approved classifications

- `approved_polarity`, `approved_semantic_disposition`,
  `approved_execution_readiness`, `approved_risk` всегда содержат допустимое
  значение соответствующего closed enum.
- Если classification dimension (`polarity`, `semantic-disposition`,
  `execution-readiness`, `risk`) равна `verified`, её `approved_*` обязано быть
  точно равно manifest value.
- Если такая dimension равна `incorrect`, её `approved_*` обязано отличаться от
  manifest value и задавать предлагаемое корректное значение. Нельзя пометить
  classification incorrect и эхом вернуть старое значение.
- Approved pair остаётся внутренне согласованной: `not-applicable` disposition
  требует `not-applicable` readiness; `ambiguous` требует
  `dependency-blocked`; `testable` допускает `ready | dependency-blocked`.

## Source inventory

- `extraction_spec_digest`, `baseline_digest`, `candidate_count` равны exact
  manifest values.
- `mapped_source_row_count` равен exact числу manifest rows с non-null
  `candidate_id` и одновременно равен `candidate_count` singular baseline.
- Verified/incorrect, `required_change` и `note` следуют общим aggregate и
  `none_required` правилам выше.

## Exact scope boundary accounting

- `checked_context_classes` duplicate-free и содержит ровно:
  `document-global-constraints`, `ancestor-and-section-preamble`,
  `cross-referenced-constraints`.
- `reviewed_manifest_contexts` перечисляет каждую manifest row этих classes
  ровно один раз как exact `{context_class, source_row_id}`. Учитываются также
  `scope_disposition = no` и all-N/A rows; exclusion никогда не заменяет row.
- Каждый `excluded_contexts` относится только к source-bound context вне всех
  manifest rows. `source_path` зарегистрирован в `manifest.sources`,
  `source_sha256` равен manifest SHA, literal text реально присутствует в этом
  UTF-8 source, а `source_locator` равен каноническому
  `<path>#text-sha256=<sha256(normalized exact_source_text)>`.
- Duplicate exclusion запрещён. Один `(source_path, canonical locator)` нельзя
  использовать для разных context classes.
- Для каждой из трёх checked classes есть evidence: все её manifest rows в
  `reviewed_manifest_contexts`; если rows нет — минимум один реальный
  source-bound exclusion этой class. Пустая аттестация недопустима.
- Boundary `verdict`, `required_change` и `note` следуют общим aggregate и
  `none_required` правилам.

Если schema-valid draft нарушает хотя бы один пункт, не пытайся угадывать обход
validator-а: исправь JSON до отправки. Reviewer не изменяет manifest и не
запускает validator самостоятельно.
