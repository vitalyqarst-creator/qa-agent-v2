# Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `positive-acceptance` | `yes` | `BSR 32; SRC-001` | The user action has four source-backed observable reset effects. | `ATOM-001; ATOM-002; ATOM-003; ATOM-004` | `TC-SCCB-001; TC-SCCB-002; TC-SCCB-003; TC-SCCB-004` | `none_required` |
| `state` | `yes` | `BSR 32; SRC-001` | Each test creates and proves a changed UI state before verifying its reset. | `ATOM-001; ATOM-002; ATOM-003; ATOM-004` | `TC-SCCB-001; TC-SCCB-002; TC-SCCB-003; TC-SCCB-004` | `none_required` |
| `default-state` | `yes` | `BSR 32; SRC-001` | Reset is compared with initial state captured in the same test; exact defaults are not asserted. | `ATOM-001; ATOM-002; ATOM-003; ATOM-004` | `TC-SCCB-001; TC-SCCB-002; TC-SCCB-003; TC-SCCB-004` | `none_required` |
| `table-list` | `yes` | `BSR 32; mockup Figure 1` | Sorting, pagination and selection are visible on the result table. | `ATOM-002; ATOM-003; ATOM-004` | `TC-SCCB-002; TC-SCCB-003; TC-SCCB-004` | `none_required` |
| `requiredness` | `no` | `BSR 32` | No mandatory-field rule is present. | `-` | `-` | `-` |
| `numeric` | `no` | `BSR 32` | No numeric input restriction or boundary is present. | `-` | `-` | `-` |
| `dependency` | `no` | `BSR 32` | The four reset dimensions are independent; no conditional field dependency is specified. | `-` | `-` | `-` |
| `persistence` | `no` | `BSR 32` | No save/reopen behavior is present. | `-` | `-` | `-` |
| `integration` | `no` | `BSR 32` | No external-system behavior is present. | `-` | `-` | `-` |
| `security` | `no` | `BSR 32` | No access-control or security rule is present. | `-` | `-` | `-` |

## Routing Decision

- `state = yes` requires the prepared `standard-required` route; compact fast eligibility is forbidden.
