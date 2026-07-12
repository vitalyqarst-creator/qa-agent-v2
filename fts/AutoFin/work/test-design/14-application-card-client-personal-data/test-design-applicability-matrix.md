# Test-design Applicability Matrix

## Applicability Matrix

| dimension | applicable | source_ref | linked_atoms | linked_tc_or_gap | reason |
| --- | --- | --- | --- | --- | --- |
| `visibility` | `yes` | `SRC-001..SRC-011` | `ATOM-001`; `ATOM-002`; `ATOM-007`; `ATOM-012`; `ATOM-017`; `ATOM-019`; `ATOM-021`; `ATOM-026`; `ATOM-028`; `ATOM-033`; `ATOM-038` | `TC-ACPD-001`; `TC-ACPD-009`; `TC-ACPD-013`; `TC-ACPD-031`; `TC-ACPD-032` | Visibility is source-backed. |
| `requiredness` | `yes` | `SRC-002`; `SRC-003`; `SRC-004`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011` | `ATOM-003`; `ATOM-008`; `ATOM-013`; `ATOM-019`; `ATOM-021`; `ATOM-031`; `ATOM-036`; `ATOM-041` | `TC-ACPD-022`..`TC-ACPD-025`; `TC-ACPD-041`; `TC-ACPD-047` | Requiredness and non-requiredness are source-backed; exact negative requiredness UI oracle requires calibration. |
| `input-format` | `yes` | `SRC-002..SRC-004`; `SRC-009..SRC-011` | `ATOM-005`; `ATOM-010`; `ATOM-015`; `ATOM-030`; `ATOM-035`; `ATOM-040` | `TC-ACPD-003`; `TC-ACPD-005`; `TC-ACPD-007`; `TC-ACPD-016`..`TC-ACPD-021`; `TC-ACPD-034`..`TC-ACPD-045` | Allowed classes and invalid-class candidates are both materialized. |
| `date-time` | `yes` | `SRC-007` | `ATOM-021`..`ATOM-025` | `TC-ACPD-013`..`TC-ACPD-015`; `TC-ACPD-026`..`TC-ACPD-028` | Relative date boundaries use `D`. |
| `dictionary` | `yes` | `SRC-006`; `DICT-001` | `ATOM-019` | `TC-ACPD-011`; `TC-ACPD-012` | Gender values are from support dictionary. |
| `integration` | `yes` | `SRC-005`; `SRC-006`; DaData clauses | `ATOM-006`; `ATOM-011`; `ATOM-016`; `ATOM-018`; `ATOM-020`; `ATOM-032`; `ATOM-037`; `ATOM-042` | `TC-ACPD-004`; `TC-ACPD-006`; `TC-ACPD-008`; `TC-ACPD-010`; `TC-ACPD-012`; `TC-ACPD-037`; `TC-ACPD-042`; `TC-ACPD-046`; `GAP-003` | Only UI-visible success effects are covered; technical attribution/failures remain constrained. |
