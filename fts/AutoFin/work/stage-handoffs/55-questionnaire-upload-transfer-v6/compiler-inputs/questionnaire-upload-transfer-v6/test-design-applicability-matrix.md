# Test-Design Applicability Matrix — Questionnaire Upload Transfer V6

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| file-upload | `yes` | `BSR 209-211` | Picker, Drag and Drop, file name and cardinality. | `ATOM-004..ATOM-011` | `TC-QUT-004..TC-QUT-010` | `none_required:covered` |
| input-boundaries | `yes` | `BSR 210` | Exact max 40 МБ and just-over boundary. | `ATOM-008; ATOM-009` | `TC-QUT-007; TC-QUT-008` | `none_required:covered` |
| negative-oracle | `yes` | `BSR 210` | Exact shared error text is source-backed. | `ATOM-009; ATOM-010` | `TC-QUT-008; TC-QUT-009` | `none_required:covered` |
| equivalence | `yes` | `BSR 210` | Complete fixed format list jpg/png/pdf plus txt invalid class. | `ATOM-007; ATOM-010` | `TC-QUT-006; TC-QUT-009` | `none_required:covered` |
| visibility | `yes` | `BSR 206; BSR 208` | Two independent always-visible properties. | `ATOM-001; ATOM-003` | `TC-QUT-001; TC-QUT-003` | `none_required:covered` |
| persistence | `no` | `BSR 212` | Explicitly outside this internal package. | `none_required` | `none_required` | `none_required:out-of-scope` |
| integration | `no` | `BSR 209 QR branch` | Explicitly outside this internal package. | `none_required` | `none_required` | `none_required:out-of-scope` |
