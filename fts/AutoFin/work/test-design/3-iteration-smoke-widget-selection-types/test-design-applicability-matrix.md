# Test Design Applicability Matrix

| dimension | applicable | source_basis | linked_atom_or_gap | planned_coverage |
| --- | --- | --- | --- | --- |
| `visibility / availability` | `no` | `scope-contract.md`: screen-specific visibility is out of scope | `not_applicable:scope-exclusion` | `none_required:scope-excludes-screen-rules` |
| `requiredness` | `no` | selected rows do not define required fields | `not_applicable:no-source-obligation` | `none_required:no-requiredness-rule` |
| `editability` | `no` | selected rows do not define editability | `not_applicable:no-source-obligation` | `none_required:no-editability-rule` |
| `default value` | `yes` | `SRC-003` | `ATOM-005`; `ATOM-006`; `GAP-001` | `TC-WIDGET-SELECTION-TYPES-003` covers visible absence; `GAP-001` preserves internal `NULL` interpretation. |
| `list or dictionary composition` | `yes` | `SRC-001`; `SRC-002` | `ATOM-001`; `ATOM-003` | `TC-WIDGET-SELECTION-TYPES-001`; `TC-WIDGET-SELECTION-TYPES-002` use recorded active dictionary values from fixture widgets. |
| `positive acceptance` | `yes` | `SRC-001`; `SRC-002`; `SRC-003` | `ATOM-002`; `ATOM-004`; `ATOM-005` | Three candidate positive TCs cover observable selection/default behavior. |
| `negative rejection` | `no` | selected rows do not define invalid classes or rejection mechanisms | `not_applicable:no-invalid-class` | `none_required:no-negative-source-rule` |
| `boundary / length / numeric classes` | `no` | selected rows have no numeric, length, mask or date boundaries | `not_applicable:no-boundary-rule` | `none_required:no-boundary-source-rule` |
| `conditional branches and dependencies` | `no` | selected rows have no conditional dependencies | `not_applicable:no-condition` | `none_required:no-conditional-source-rule` |
| `state transition or navigation` | `no` | selected rows do not define navigation or workflow transition | `not_applicable:no-transition` | `none_required:no-transition-source-rule` |
| `persistence after save/reopen` | `no` | `scope-contract.md`: save-flow and persistence are out of scope | `not_applicable:scope-exclusion` | `none_required:scope-excludes-persistence` |
| `integration/API/async/internal effects` | `unclear` | `SRC-003` internal `NULL` phrase has no allowed artifact in scope | `ATOM-006`; `GAP-001` | preserved as residual gap, not converted into UI-only TC. |
| `repeated blocks, tables, files or documents` | `no` | no selected row defines repeatable blocks, files or documents | `not_applicable:no-repeatable-rule` | `none_required:no-repeatable-source-rule` |
| `role/status/security/NFR dimensions` | `no` | no selected row defines role, status, security or NFR behavior | `not_applicable:no-role-status-rule` | `none_required:no-role-status-source-rule` |
