# Round 1 Findings

## Human Summary
Semantic review is not ready for format review. The writer draft mostly covers the intended 42 atoms under the accepted GAP-001..GAP-003 risks, but ATOM-013 is not covered in the draft. Several supporting design artifacts are also stale and contradict the draft numbering/counts, including ledger, decision table, coverage map, and fixture mappings.

## Coverage Summary
- `executable_tc_count`: 46
- `atoms_total`: 42
- `atoms_covered`: 41
- `gaps`: ['GAP-001', 'GAP-002', 'GAP-003', 'ATOM-013']

## Findings
### SEM-001

- review_mode: `traceability`
- severity: `error`
- category: `coverage`
- test_case_id: ``
- coverage_gap: `ATOM-013`
- traceability_ref: `ATOM-013`
- problem: The draft does not cover the atomic statement that field `Отчество` is not required.
- evidence: atomic-requirements-ledger.md defines ATOM-013 as `Поле Отчество не является обязательным`, but writer-structure-r1-draft.md has no TC trace line containing ATOM-013. TC-ACPD-001 only verifies field display, not acceptance of an empty optional patronymic.
- required_change: Add explicit coverage for non-requiredness of `Отчество` or extend an existing suitable TC with trace `ATOM-013` and an observable expected result that leaving `Отчество` empty is accepted where the flow otherwise proceeds.
- source_reference: `SRC-004; column О=Нет`
- status: `open`

### SEM-002

- review_mode: `traceability`
- severity: `error`
- category: `traceability`
- test_case_id: ``
- coverage_gap: ``
- traceability_ref: `atomic-requirements-ledger.md`
- problem: The atomic ledger is stale and maps multiple atoms to wrong or nonexistent TC IDs.
- evidence: Ledger maps ATOM-003 to TC-ACPD-046, ATOM-008 to TC-ACPD-047, ATOM-019 to TC-ACPD-048, ATOM-021 to TC-ACPD-049, and ATOM-031/036/041 to TC-ACPD-050. The draft contains TC-ACPD-001..TC-ACPD-046 only, and TC-ACPD-046 covers ATOM-042 DaData for previous patronymic.
- required_change: Synchronize `atomic-requirements-ledger.md` with the writer draft numbering and actual traceability, including correcting requiredness mappings to TC-ACPD-022..TC-ACPD-025 and TC-ACPD-041.
- source_reference: `atomic-requirements-ledger.md; writer-structure-r1-draft.md`
- status: `open`

### SEM-003

- review_mode: `test-design`
- severity: `error`
- category: `test-design-consistency`
- test_case_id: ``
- coverage_gap: ``
- traceability_ref: `test-design-decision-table.md`
- problem: The decision table uses the same stale TC numbering as the ledger, so design decisions no longer point to the implemented draft checks.
- evidence: DD-003 maps ATOM-003 to TC-ACPD-046 and DD-REQ-001..DD-REQ-005 map requiredness obligations to TC-ACPD-046..TC-ACPD-050, while the draft uses TC-ACPD-022..TC-ACPD-025 and TC-ACPD-041 for those obligations.
- required_change: Update `test-design-decision-table.md` so every `planned_tc_or_gap` points to the actual writer draft TC IDs and remove references to nonexistent TC-ACPD-047..TC-ACPD-050.
- source_reference: `test-design-decision-table.md; writer-structure-r1-draft.md`
- status: `open`

### SEM-004

- review_mode: `traceability`
- severity: `error`
- category: `artifact-consistency`
- test_case_id: ``
- coverage_gap: ``
- traceability_ref: `coverage-map.md`
- problem: The coverage map is from an older scope state and contradicts the current draft and design package.
- evidence: coverage-map.md reports 20 atomic statements, 13 test cases, and requirement codes BSR 39-BSR 69. The current writer draft metadata reports 42 atoms, 46 test cases, and BSR 47-BSR 77 for SRC-001..SRC-011.
- required_change: Regenerate or correct `coverage-map.md` to the current scope: 42 atoms, 46 draft test cases, SRC-001..SRC-011, and BSR 47..BSR 77, with accepted residual gaps GAP-001..GAP-003.
- source_reference: `coverage-map.md; writer-structure-r1-draft.md`
- status: `open`

### SEM-005

- review_mode: `test-design`
- severity: `warning`
- category: `test-data`
- test_case_id: ``
- coverage_gap: ``
- traceability_ref: `fixture-catalog.md`
- problem: Fixture catalog `used_by` mappings are stale and omit current draft TC IDs for date and previous-FIO checks.
- evidence: FIX-ACPD-002 includes invalid `D-100y-1d` but `used_by` stops at TC-ACPD-027, while draft TC-ACPD-028 covers the invalid lower birth-date boundary. FIX-ACPD-003 points to TC-ACPD-032/033/037/042 but the positive previous-FIO and DaData checks in the draft include TC-ACPD-034, TC-ACPD-038, TC-ACPD-043, and TC-ACPD-046.
- required_change: Update fixture `used_by` references to match the current draft TC numbering and include all current consumers of each fixture.
- source_reference: `fixture-catalog.md; writer-structure-r1-draft.md`
- status: `open`
