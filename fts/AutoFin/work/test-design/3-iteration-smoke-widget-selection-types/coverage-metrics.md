# Coverage Metrics

| metric | value | evidence |
| --- | ---: | --- |
| Source rows in scope | 3 | `SRC-001`; `SRC-002`; `SRC-003` |
| Atomic statements | 6 | `atomic-requirements-ledger.md` |
| Atomic statements covered by TC | 5 | `ATOM-001`..`ATOM-005` |
| Atomic statements preserved as gap | 1 | `ATOM-006` -> `GAP-001` |
| Candidate UI-calibration test cases | 3 | `TC-WIDGET-SELECTION-TYPES-001`..`003` |
| Executable non-candidate test cases | 0 | Concrete screen/widget fixture not defined by selected source rows. |
| Blocking coverage gaps | 0 | No gap blocks structural review of the draft. |
| Non-blocking coverage gaps | 1 | `GAP-001` preserves internal `NULL` interpretation risk. |

## Coverage Summary

The writer draft covers all observable obligations from `SRC-001`..`SRC-003` as candidate UI-calibration test cases. The only uncovered atom is the internal `NULL` interpretation from `SRC-003`; it is documented as `GAP-001` because the confirmed scope excludes persistence, database, API and async artifacts.
