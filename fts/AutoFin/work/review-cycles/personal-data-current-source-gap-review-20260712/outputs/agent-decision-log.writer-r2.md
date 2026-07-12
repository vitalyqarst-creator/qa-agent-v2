# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-writer` |
| started_from | `work/review-cycles/personal-data-current-source-gap-review-20260712/cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `test-design` | `SEM-001`; `ATOM-013` | Add `TC-ACPD-047` instead of attaching `ATOM-013` to display/editability TC. | Non-requiredness is independently checkable and visibility-only coverage did not prove empty optional value acceptance. | `writer-r2-draft.md`; `traceability-matrix.md`; `atomic-requirements-ledger.md` | high | applied |
| `DEC-002` | 2 | `traceability` | `SEM-002`; stale ledger IDs | Preserve existing `TC-*` IDs and correct ledger mappings to actual draft numbering. | Renumbering would create unnecessary churn; the defect was artifact drift, not TC semantics. | `atomic-requirements-ledger.md`; `source-table-normalization.md`; `requiredness-oracle-inventory.md` | high | applied |
| `DEC-003` | 3 | `test-design` | `SEM-003`; stale decision table | Update decision-table planned TC references to actual draft IDs. | Reviewer can verify closure only if design decisions point to implemented checks. | `test-design-decision-table.md` | high | applied |
| `DEC-004` | 4 | `coverage` | `SEM-004`; stale coverage map | Regenerate coverage-map summary to current source rows, BSR range, atom count and TC count. | Old `BSR 39`..`BSR 69` coverage summary contradicted current-source rebase. | `coverage-map.md`; `coverage-metrics.md` | high | applied |
| `DEC-005` | 5 | `test-data` | `SEM-005`; stale fixture `used_by` | Update fixture consumers without changing fixture values. | Finding concerns mappings only; values remain source/test-design compatible. | `fixture-catalog.md` | high | applied |
| `DEC-006` | 6 | `routing` | writer gates and validator | Route to `semantic-review-r2`. | Blocking findings have response artifacts and synchronized writer-owned outputs. | `cycle-state.yaml`; `prompt.semantic-review-r2.md` | medium | applied |
