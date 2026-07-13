# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/44-personal-data-v7-targeted-oracle-repair/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V7 terminal `blocked-invalid-output`; stop gate forbids retry/resume | Create immutable H45/V8 rather than reuse V7 | Contract and evidence transport must change before another reviewer session | H45 workflow | high | applied |
| `DEC-002` | 2 | `validation` | Generic schema allowed all verdicts, parser rejected `OBL-025 -> invented-coverage` after live | Bind generic schema verdicts to coverage-status groups and keep parser defense | Text instruction alone did not prevent an invalid structured response | runner/tests | high | applied |
| `DEC-003` | 3 | `source-boundary` | Compact projection ended before DICT blocks although V7 package contained `DICT-001` | Add explicit structured dictionary evidence projection; do not treat V7 `F-002` as a draft defect | Reviewer must receive exact active values already extracted from canonical inventory | runner/tests/V8 package | high | applied |
| `DEC-004` | 4 | `artifact-write` | Byte-preserving splice retained V6 metadata inside V7 draft | Add runner-owned metadata migration and separate semantic-preservation proof | Cycle metadata is not test semantics, but mixed package ids must block review | runner/tests | high | applied |
| `DEC-005` | 5 | `source-boundary` | Invalid reviewer diagnostics `F-001..F-005` require independent verification | Repair only 13 TC confirmed by V7 draft plus V8 source obligations; exclude `F-002` | Invalid reviewer output is not a requirements source | source-backed verification/findings | high | applied |
| `DEC-006` | 6 | `budget` | First V8 compile exceeded evidence budget by 2103 bytes | Compact duplicate design prose without raising the 49152-byte limit | Field/action/precondition/oracle semantics remain explicit; compiled evidence is 49104 bytes | V8 compiler inputs/package | high | applied |
| `DEC-007` | 7 | `live-gate` | Validate-only and exec dry-run pass; live still mutates immutable cycle evidence | Require checkpoint/push and separate authorization before exactly one dispatcher | Prevents mixing code/package mutation with live evidence | pre-live stop gate | high | applied |
