# Test Design Review

| review_item | status | evidence | follow_up |
| --- | --- | --- | --- |
| Source scope limited to selected section 3 rows | `pass` | `source-row-inventory.md`; `scope-contract.md` | Reviewer should reject any screen-specific expansion not tied to fixture calibration. |
| Atomic decomposition | `pass` | `atomic-requirements-ledger.md` contains six atoms from three source rows. | none |
| Candidate fixture handling | `pass` | `fixture-catalog.md`; candidate metadata in all three TCs. | UI calibration must record concrete fields and values before executable conversion. |
| Observable expected results | `pass` | TCs assert visible selected values or visible empty state only. | none |
| Unsupported internal `NULL` oracle avoided | `pass` | `ATOM-006` routed to `GAP-001`. | Reviewer should confirm whether gap is acceptable for this smoke cycle. |
| Negative/rejection coverage | `pass` | selected source rows define no invalid classes. | none |

## Coverage Gaps

| gap_id | source_ref | affected_atom | gap_statement | severity | downstream_handling |
| --- | --- | --- | --- | --- | --- |
| `GAP-001` | `SRC-003` | `ATOM-006` | The selected sources say absent widget values are interpreted as `NULL`, but the confirmed scope excludes persistence, database, API and async artifacts that could observe internal null semantics. | `non-blocking` | Preserve for reviewer and future scope expansion; do not assert internal `NULL` in UI-only TC. |
