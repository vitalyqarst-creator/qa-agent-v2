# Coverage Metrics

## Summary Table

| dimension | technique | applicable | source_refs | obligations_total | covered | gaps_or_unclear | coverage_strength | supporting_artifact | residual_note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filters | atomic-reset | yes | BSR 32; SRC-001 | 1 | 1 | 0 | atom-level | coverage-obligation-table.md | No concrete filter field/default asserted. |
| sorting | atomic-reset | yes | BSR 32; SRC-001 | 1 | 1 | 0 | atom-level | coverage-obligation-table.md | No exact default sort asserted. |
| pagination | atomic-reset | yes | BSR 32; SRC-001 | 1 | 1 | 0 | atom-level | coverage-obligation-table.md | Requires multi-page fixture; no page size/count asserted. |
| row-selection | atomic-reset | yes | BSR 32; SRC-001 | 1 | 1 | 0 | atom-level | coverage-obligation-table.md | No backend/persistence state asserted. |

## Technique Detail Tables

| technique | covered_items | omitted_items | residual_risk |
| --- | --- | --- | --- |
| atomic-reset | ATOM-001; ATOM-002; ATOM-003; ATOM-004 | none_required:all_source_dimensions_covered | Low residual risk: exact default values remain intentionally unasserted because source does not define them. |

## Rules

- Metrics count only source-backed dimensions from `BSR 32`.
- Out-of-scope `BSR 31`, `BSR 33+`, concrete defaults and API effects are not counted as obligations.
