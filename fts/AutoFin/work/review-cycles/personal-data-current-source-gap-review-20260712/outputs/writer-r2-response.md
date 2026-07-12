# Writer R2 Response

## Human Summary

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| writer_stage | `writer-r2` |
| source_findings | `round-1-findings.md` |
| result | `semantic-review-ready` |

## Traceability Mapping Notes

- Split/merge of `ATOM-*` references was not performed: `ATOM-001`..`ATOM-042` keep the same meanings and IDs.
- Existing `TC-*` IDs were preserved; new `TC-ACPD-047` was added only to cover existing `ATOM-013`.
- `GAP-001`, `GAP-002` and `GAP-003` remain accepted non-blocking calibration/integration risks; no residual gap was converted to covered without source-backed evidence.

## Writer Response

### SEM-001

**Resolution Status:** fixed

**Change Summary:** Added `TC-ACPD-047` for source-backed non-requiredness of `Отчество`; updated draft, traceability matrix, ledger, source normalization, package plan and applicability matrix so `ATOM-013` is covered by this observable positive check instead of visibility-only `TC-ACPD-001`.

**Affected Test Case IDs:**
- `TC-ACPD-047`

**Affected Traceability Refs:**
- `ATOM-013`

### SEM-002

**Resolution Status:** fixed

**Change Summary:** Synchronized `atomic-requirements-ledger.md` with actual draft numbering, including requiredness mappings to `TC-ACPD-022`, `TC-ACPD-023`, `TC-ACPD-024`, `TC-ACPD-025` and `TC-ACPD-041`; removed stale references to nonexistent requiredness cases `TC-ACPD-048`..`TC-ACPD-050`.

**Affected Test Case IDs:**
- `TC-ACPD-022`
- `TC-ACPD-023`
- `TC-ACPD-024`
- `TC-ACPD-025`
- `TC-ACPD-041`

**Affected Traceability Refs:**
- `atomic-requirements-ledger.md`
- `ATOM-003`
- `ATOM-008`
- `ATOM-019`
- `ATOM-021`
- `ATOM-031`
- `ATOM-036`
- `ATOM-041`

### SEM-003

**Resolution Status:** fixed

**Change Summary:** Updated `test-design-decision-table.md` so `planned_tc_or_gap` points to actual draft TC IDs for requiredness, previous-FIO, DaData and invalid-class obligations; removed references to nonexistent `TC-ACPD-048`..`TC-ACPD-050`.

**Affected Test Case IDs:**
- `TC-ACPD-022`
- `TC-ACPD-023`
- `TC-ACPD-024`
- `TC-ACPD-025`
- `TC-ACPD-041`
- `TC-ACPD-047`

**Affected Traceability Refs:**
- `test-design-decision-table.md`

### SEM-004

**Resolution Status:** fixed

**Change Summary:** Corrected `coverage-map.md` to current scope values: 42 atoms, 47 unsigned draft test cases after `TC-ACPD-047`, source rows `SRC-001`..`SRC-011`, requirement IDs `BSR 47`..`BSR 77`, and accepted residual gaps `GAP-001`..`GAP-003`.

**Affected Test Case IDs:**
- `TC-ACPD-001`..`TC-ACPD-047`

**Affected Traceability Refs:**
- `coverage-map.md`

### SEM-005

**Resolution Status:** fixed

**Change Summary:** Updated `fixture-catalog.md`: date-boundary fixture now maps to `TC-ACPD-026`..`TC-ACPD-028`, and previous-FIO fixture maps to current positive/DaData consumers including `TC-ACPD-034`, `TC-ACPD-038`, `TC-ACPD-043` and `TC-ACPD-046`.

**Affected Test Case IDs:**
- `TC-ACPD-014`
- `TC-ACPD-015`
- `TC-ACPD-026`
- `TC-ACPD-027`
- `TC-ACPD-028`
- `TC-ACPD-033`
- `TC-ACPD-034`
- `TC-ACPD-037`
- `TC-ACPD-038`
- `TC-ACPD-042`
- `TC-ACPD-043`
- `TC-ACPD-046`

**Affected Traceability Refs:**
- `fixture-catalog.md`
