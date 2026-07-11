# Coverage Gaps

| gap_id | status | source_ref | linked_atoms | impact | handling |
| --- | --- | --- | --- | --- | --- |
| `GAP-001` | `open` | `section-14 rows 002-003`; `BSR 38` | `ATOM-003`; `ATOM-005` | `non-blocking` | Do not test calculator screen, calculations, offer selection or exact prefill mapping without external FT `Калькулятор`; window opening remains independently testable via `ATOM-004`. |
