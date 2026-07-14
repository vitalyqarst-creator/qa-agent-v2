# prepared-writer dictionary duplication

## Metadata

- `candidate_id`: `CAND-2026-07-14-PREPARED-WRITER-DICTIONARY-DUPLICATION`
- `created_at`: `2026-07-14`
- `source_signal`: `H52 V3 raw writer output and runner projection`
- `affected_skill`: `ft-test-case-iteration; ft-test-case-writer`
- `failure_class`: `writer-owned-exhaustive-dictionary-values`
- `status`: `implemented-offline`

## Failure Signal

V3 writer перечислил полный `DICT-001` в `TC-VAMB-005`, после чего runner добавил source-backed projection. Reviewer-visible TC сохранил оба списка; raw writer output и latency выросли без улучшения покрытия.

## Expected Detection Or Output

- Writer-only context не переносит полный leaf payload exhaustive dictionary.
- Structured obligation transport явно объявляет runner-owned materializations.
- Writer оставляет symbolic `DICT-*` check; два и более exact labels в exhaustive TC блокируются до reviewer.
- Runner добавляет полный набор ровно один раз, после чего exact completeness gate проходит.

## Verification

- Focused unit/runner/context tests pass.
- Full agent-layer and V4 live evidence pending.
- Production baseline must remain unchanged.
