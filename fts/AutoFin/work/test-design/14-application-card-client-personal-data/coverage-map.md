# Coverage Map

| metric | value | evidence |
| --- | --- | --- |
| `atomic_statements` | `42` | `atomic-requirements-ledger.md`; `ATOM-001`..`ATOM-042` |
| `covered` | `42` | `TC-ACPD-001`..`TC-ACPD-047`; covered-with-gap counted as candidate/partial coverage where `GAP-001`..`GAP-003` applies |
| `gap` | `3` | `GAP-001`; `GAP-002`; `GAP-003` |
| `unclear_atoms` | `0` | `ATOM-013` is covered by `TC-ACPD-047`; unresolved oracle risks remain only `GAP-001`..`GAP-003`. |
| `test_cases` | `47` | `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r2-draft.md` |
| `known_limitations` | `3` | DaData/ABS failures; birth-date rule priority; invalid text-input feedback. |
| `requirement_codes` | `31` | `BSR 47`..`BSR 77` from `source-row-inventory.md`; all mapped to `ATOM-*`, `TC-ACPD-*` or accepted residual `GAP-*` anchors. |
