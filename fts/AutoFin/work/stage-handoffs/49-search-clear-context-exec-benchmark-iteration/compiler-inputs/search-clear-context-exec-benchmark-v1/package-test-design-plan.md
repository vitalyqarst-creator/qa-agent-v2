# Package Test Design Plan

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PD-001` | `WP-01` | `state` | `BSR 32; SRC-001.P01` | `ATOM-001` | Capture initial filter state, choose one visible filter value, then click `Очистить`. | `action-flow` | `filter-reset` | `changed-filter-state: one visible filter differs from captured initial state` | Filter state equals the captured initial state. | `BSR 32` | `TC-SCCB-001` | `covered` |
| `PD-002` | `WP-01` | `state` | `BSR 32; SRC-001.P02` | `ATOM-002` | Capture initial sort state, click one sortable header until state changes, then click `Очистить`. | `action-flow` | `sorting-reset` | `changed-sort-state: visible sort indicator differs from captured initial state` | Sort state equals the captured initial state. | `BSR 32` | `TC-SCCB-002` | `covered` |
| `PD-003` | `WP-01` | `state` | `BSR 32; SRC-001.P03` | `ATOM-003` | Capture initial page, navigate to `page 2`, then click `Очистить`. | `action-flow` | `pagination-reset` | `noninitial-page: page 2` | Pagination state equals the captured initial state. | `BSR 32` | `TC-SCCB-003` | `covered` |
| `PD-004` | `WP-01` | `state` | `BSR 32; SRC-001.P04` | `ATOM-004` | Capture initial row-selection state, select the `first displayed row`, then click `Очистить`. | `action-flow` | `row-selection-reset` | `selected-row: first displayed row` | Row-selection state equals the captured initial state. | `BSR 32` | `TC-SCCB-004` | `covered` |

## Fixture Contracts

- `FIX-SCCB-001`: environment has at least one available visible filter value that changes filter state.
- `FIX-SCCB-002`: results table contains at least one sortable header and one displayed row.
- `FIX-SCCB-003`: result set has at least two pages; otherwise `TC-SCCB-003` is not executable on that environment and must be reported as fixture-blocked, not reinterpreted.

## Plan Notes

- Each planned test changes and verifies one reset dimension only.
- Initial state is captured in the same session; no exact product default is invented.
