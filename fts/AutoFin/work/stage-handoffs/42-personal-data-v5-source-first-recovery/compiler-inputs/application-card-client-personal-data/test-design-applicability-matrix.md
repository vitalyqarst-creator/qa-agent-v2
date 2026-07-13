# Test-design Applicability Matrix

| dimension | applicable | source_ref | linked_atoms | linked_test_cases | gap_id | reason |
| --- | --- | --- | --- | --- | --- | --- |
| `field-property` | `yes` | `SRC-001..SRC-008` | `ATOM-001`; `ATOM-002`; `ATOM-004`; `ATOM-007`; `ATOM-009`; `ATOM-012`; `ATOM-014`; `ATOM-017`; `ATOM-019`; `ATOM-021`; `ATOM-026`; `ATOM-027` | `TC-ACPD-001`; `TC-ACPD-002`; `TC-ACPD-009`; `TC-ACPD-011`; `TC-ACPD-013`; `TC-ACPD-029`; `TC-ACPD-030`; `TC-ACPD-047` | - | Static visibility, type, editability and default state are source-backed. |
| `requiredness` | `yes` | Table 4 column `О`; `BSR 68, 72, 76` | `ATOM-003`; `ATOM-008`; `ATOM-019`; `ATOM-021`; `ATOM-031`; `ATOM-036`; `ATOM-041` | `TC-ACPD-022`; `TC-ACPD-023`; `TC-ACPD-024`; `TC-ACPD-025`; `TC-ACPD-041` | `GAP-002` | Requiredness applies; exact empty-value UI reaction remains calibration-only. |
| `format` | `yes` | `BSR 48, 51, 54, 67, 71, 75` | `ATOM-005`; `ATOM-010`; `ATOM-015`; `ATOM-030`; `ATOM-035`; `ATOM-040` | `TC-ACPD-003`; `TC-ACPD-005`; `TC-ACPD-007`; `TC-ACPD-016`..`TC-ACPD-021`; `TC-ACPD-034`..`TC-ACPD-045` | `GAP-001` | Valid text and hyphen inputs are source-backed; invalid UI reaction is not. |
| `date-time` | `yes` | `SRC-007`; `BSR 60–63` | `ATOM-021`; `ATOM-022`; `ATOM-023`; `ATOM-024`; `ATOM-025` | `TC-ACPD-013`; `TC-ACPD-014`; `TC-ACPD-015`; `TC-ACPD-025`..`TC-ACPD-028` | `GAP-001`; `GAP-002` | Relative D-boundaries and input/date calibration candidates apply. |
| `dictionary` | `yes` | `SRC-006`; `DICT-001` | `ATOM-019` | `TC-ACPD-011`; `TC-ACPD-024` | `GAP-002` | Active dictionary values are complete and requiredness calibration remains open. |
| `integration` | `yes` | `BSR 49, 52, 55, 57, 59, 69, 73, 77` | `ATOM-006`; `ATOM-011`; `ATOM-016`; `ATOM-018`; `ATOM-020`; `ATOM-032`; `ATOM-037`; `ATOM-042` | `TC-ACPD-004`; `TC-ACPD-006`; `TC-ACPD-008`; `TC-ACPD-010`; `TC-ACPD-012`; `TC-ACPD-037`; `TC-ACPD-042`; `TC-ACPD-046` | `GAP-003` | Only UI-visible success effects are in scope; technical failure paths are constrained. |
| `conditional-visibility` | `yes` | `BSR 66, 70, 74` | `ATOM-028`; `ATOM-033`; `ATOM-038` | `TC-ACPD-031`; `TC-ACPD-032` | - | Both `Да` and `Нет` branches are source-backed. |
| `dependency` | `yes` | `BSR 68, 72, 76` | `ATOM-031`; `ATOM-036`; `ATOM-041` | `TC-ACPD-041` | `GAP-002` | Conditional group requiredness applies with a calibration qualifier. |

Execution route: `standard-required`; applicable conditional, date/input-boundary, dictionary, integration and requiredness dimensions rule out the simple-field profile.
