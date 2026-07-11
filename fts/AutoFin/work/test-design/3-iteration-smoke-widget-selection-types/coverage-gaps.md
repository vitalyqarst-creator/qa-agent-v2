# Coverage Gaps

| gap_id | source_ref | affected_atom | gap_statement | severity | blocking_ready_for_review | downstream_handling |
| --- | --- | --- | --- | --- | --- | --- |
| `GAP-001` | `SRC-003` | `ATOM-006` | The selected sources state that absent widget values are interpreted as `NULL`, but the confirmed scope excludes persistence, database, API and async artifacts that could observe internal null semantics. | `non-blocking` | `no` | Preserve for reviewer and future scope expansion; do not assert internal `NULL` in UI-only TC. |
| `GAP-002` | `SRC-001`; `SRC-002` | `ATOM-001`; `ATOM-003` | The selected scope does not identify concrete dictionaries or provide an independent complete inventory for source-origin assertions. | `non-blocking` | `no` | Preserve dictionary provenance as a gap; cardinality remains executable with two distinct fixture values. |
