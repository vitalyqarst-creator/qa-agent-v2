# Coverage Gaps

| gap_id | status | source_ref | linked_atoms | impact | handling |
| --- | --- | --- | --- | --- | --- |
| `GAP-001` | `open` | `section-14 rows 002-003`; `BSR 45`; `BSR 46` | `ATOM-003`; `ATOM-005`; `ATOM-006` | `non-blocking` | Do not test calculator screen, calculations, offer selection, exhaustive prefilled field set or exact prefill mapping without external FT `Калькулятор`; window opening and observable prefill presence remain independently testable via `ATOM-004` and `ATOM-005`. |
