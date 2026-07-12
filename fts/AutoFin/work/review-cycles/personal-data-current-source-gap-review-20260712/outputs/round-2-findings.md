# Round 2 Findings

## Human Summary
Семантическое покрытие в целом заявлено на 42/42 атома и 47 TC, с принятыми рисками GAP-001..GAP-003. Прогресс блокируют не новые продуктовые gaps, а несогласованная трассировка: ATOM-025 расходится между ledger/design plan и draft TC, а decision table содержит устаревшие TC-маппинги после перенумерации/вставки TC-ACPD-047.

## Coverage Summary
- `executable_tc_count`: 47
- `atoms_total`: 42
- `atoms_covered`: 42
- `gaps`: ['GAP-001', 'GAP-002', 'GAP-003']

## Findings
### SEM-001

- review_mode: `traceability`
- severity: `error`
- category: `coverage`
- test_case_id: `TC-ACPD-026; TC-ACPD-027; TC-ACPD-028`
- coverage_gap: ``
- traceability_ref: `ATOM-025`
- problem: Ledger and design plan state that ATOM-025 is covered by the negative date-boundary cases, but the writer draft traces TC-ACPD-026 to ATOM-022, TC-ACPD-027 to ATOM-023, and TC-ACPD-028 to ATOM-024 without ATOM-025.
- evidence: atomic-requirements-ledger.md maps ATOM-025 to TC-ACPD-014; TC-ACPD-015; TC-ACPD-026; TC-ACPD-027; TC-ACPD-028. package-test-design-plan.md PLAN-025 has the same intent. writer-r2-draft.md traces ATOM-025 only in TC-ACPD-014 and TC-ACPD-015, while TC-ACPD-026..028 omit it.
- required_change: Align draft traceability and test-design artifacts: add ATOM-025 to TC-ACPD-026..028 if those cases validate D-relative boundary calculation, or reduce ledger/design coverage if that was not intended.
- source_reference: `SRC-007; BSR 61-63; ATOM-025`
- status: `open`

### SEM-002

- review_mode: `test-design`
- severity: `error`
- category: `traceability-artifact-consistency`
- test_case_id: ``
- coverage_gap: ``
- traceability_ref: `ATOM-022..ATOM-030; ATOM-033; ATOM-034; ATOM-038; ATOM-039`
- problem: test-design-decision-table.md contains stale/off-by-one planned_tc_or_gap mappings that conflict with package-test-design-plan.md, atomic-requirements-ledger.md, and the writer draft.
- evidence: Examples: DD-022 maps ATOM-022 to TC-ACPD-025, but the ledger/plan/draft map the invalid D-18 boundary to TC-ACPD-026; DD-026 maps ATOM-026 to TC-ACPD-028, but draft TC-ACPD-029 traces ATOM-026; DD-028 maps ATOM-028 to TC-ACPD-030; TC-ACPD-031, but draft coverage is TC-ACPD-031; TC-ACPD-032.
- required_change: Regenerate or correct the affected decision table rows so planned_tc_or_gap matches the writer draft and ledger before moving to format review.
- source_reference: `test-design-decision-table.md DD-022..DD-030, DD-033..DD-034, DD-038..DD-039`
- status: `open`
