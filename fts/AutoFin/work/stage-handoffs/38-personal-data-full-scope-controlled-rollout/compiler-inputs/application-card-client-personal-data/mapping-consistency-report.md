# Mapping Consistency Report

## Result

Prepared inputs are internally consistent and ready for a later compiler invocation. This preparation did not compile a package or start a writer/reviewer cycle.

| check | result | evidence |
| --- | --- | --- |
| Atomic ledger completeness | `pass: 42/42` | `ATOM-001` through `ATOM-042` occur once in `atomic-requirements-ledger.md`. |
| Planned TC inventory | `pass: 47/47` | Exact set is `TC-ACPD-001` through `TC-ACPD-047`; no gaps or extra IDs. |
| Obligation atomicity | `pass: 65/65` | Every `OBL-001` through `OBL-065` links exactly one atom and exactly one TC. |
| Mapping union equality | `pass` | Per-atom TC unions are identical in ledger `covered_by_tc`, obligation `planned_tc_or_gap`, plan `planned_tc_or_gap`, and decision table `planned_tc_or_gap`. |
| Shared plan groups | `pass` | Each shared TC has one plan row whose `linked_atoms` equals the corresponding obligation group; cross-field groups carry `grouping-justification:`. |
| Input fixtures | `pass` | Every plan row that performs input has a concrete `fixture:` or `dictionary:` value in `input_class`. |
| Execution route | `pass: standard-required` | Applicability declares conditional, date/input-boundary, dictionary, integration, and requiredness dimensions. |

## SEM Closure Evidence

| defect | closure |
| --- | --- |
| `SEM-001` | `ATOM-025` maps to `TC-ACPD-014`, `TC-ACPD-015`, `TC-ACPD-026`, `TC-ACPD-027`, `TC-ACPD-028` in all four mapping artifacts. In the obligation table, `OBL-037`, `OBL-038`, and `OBL-039` explicitly attach `ATOM-025` to `TC-ACPD-026`..`TC-ACPD-028`. |
| `SEM-002` | Decision rows `DD-001`..`DD-042` were regenerated from the current ledger. In particular, `ATOM-022 -> TC-ACPD-014, TC-ACPD-026`; `ATOM-023 -> TC-ACPD-027`; `ATOM-024 -> TC-ACPD-015, TC-ACPD-028`; `ATOM-026 -> TC-ACPD-029`; `ATOM-028/033/038 -> TC-ACPD-031, TC-ACPD-032`. No legacy off-by-one mapping remains. |

## Preserved Constraints

- `GAP-001`, `GAP-002`, and `GAP-003` remain open, non-blocking constraints on their testable atoms through `constraint_gap_ids`; no rejection message, requiredness reaction, DaData failure, retry, fallback, or technical attribution was invented.
- `DICT-001` is preserved with the complete active value set: `Мужчина`; `Женщина`.
- Regression draft and findings were used only to identify and close `SEM-001` and `SEM-002`; they were not used as requirement or oracle sources.

## Boundary Check

All writes performed for this task are under `work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/compiler-inputs/application-card-client-personal-data/`. No files under prohibited `work/test-design/**`, `test-cases/**`, review-cycle history, scripts, tests, or handoffs `29`/`37` were modified by this preparation.
