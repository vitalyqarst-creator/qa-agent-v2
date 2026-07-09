# Test-design Applicability Matrix

| dimension | applicable | source_ref | linked_atoms | planned_tc_or_gap | rationale |
| --- | --- | --- | --- | --- | --- |
| visibility / availability | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | Source describes action effect, not visibility or availability. |
| requiredness | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No required fields are defined by this scope. |
| editability | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | Source does not define field editability. |
| default value | unclear-limited | BSR 32; SRC-001 | ATOM-001; ATOM-002; ATOM-003 | TC-BSR32-001; TC-BSR32-002; TC-BSR32-003 | Exact defaults are not specified; TC compares against observed initial/default state without asserting concrete values. |
| list or dictionary composition | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No dictionary or fixed list values are introduced. |
| positive acceptance | yes | BSR 32; SRC-001 | ATOM-001; ATOM-002; ATOM-003; ATOM-004 | TC-BSR32-001; TC-BSR32-002; TC-BSR32-003; TC-BSR32-004 | User action `Очистить` has source-backed reset effect. |
| negative rejection | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No invalid input or rejection behavior is defined. |
| boundary / length / numeric classes | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No numeric, length or mask constraints are defined. |
| conditional branches and dependencies | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No conditional branch is defined. |
| state transition or navigation | yes | BSR 32; SRC-001 | ATOM-001; ATOM-002; ATOM-003; ATOM-004 | TC-BSR32-001; TC-BSR32-002; TC-BSR32-003; TC-BSR32-004 | Reset changes visible UI state back to initial/default context state. |
| persistence after save/reopen | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No save, reopen or persistence behavior is defined. |
| integration/API/async/internal effects | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No backend/API/internal effect is source-backed. |
| repeated blocks, tables, files or documents | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | Tables are UI containers only; no repeated-block lifecycle is defined. |
| role/status/security/NFR | no | BSR 32; SRC-001 | none_required:not_applicable | none_required:not_applicable | No role/status/security/NFR behavior is defined. |

## Applicability Notes

- The `unclear-limited` default row does not create a gap because the tests do not assert exact default values; they compare against the same session's observed initial/default state.
