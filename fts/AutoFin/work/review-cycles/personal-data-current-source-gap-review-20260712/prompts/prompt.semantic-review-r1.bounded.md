# Bounded semantic traceability and test-design review

This is a bounded read-only reviewer turn.
Do not edit files. Do not update cycle-state.yaml. Do not create reviewer artifacts.
Do not recursively read directories. Do not scan unrelated files. Read only the exact files listed below.

## Stage
- stage: semantic-review-r1
- scenario: reviewer.semantic_traceability_test_design
- cycle_id: personal-data-current-source-gap-review-20260712
- scope_slug: application-card-client-personal-data

## Allowed Files
- fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-structure-r1-draft.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/package-test-design-plan.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/atomic-requirements-ledger.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/coverage-map.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/test-design-decision-table.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/test-design-applicability-matrix.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/fixture-catalog.md
- fts/AutoFin/work/test-design/14-application-card-client-personal-data/dictionary-inventory.md

## Open Questions
- GAP-001 exact invalid-value UI oracle remains pending for UI calibration.
- GAP-002 empty requiredness UI oracle remains pending for UI calibration.
- GAP-003 DaData/ABS failure and technical attribution evidence remain pending.

## Accepted Risks
- GAP-001 non-blocking calibration risk accepted for writer draft only; candidate TC preserved.
- GAP-002 non-blocking calibration risk accepted for writer draft only; candidate TC preserved.
- GAP-003 non-blocking integration-evidence risk accepted for writer draft only; success-path visible checks only.

## Required Output
Return fenced JSON only. Do not include prose outside the JSON fence.
Use this exact top-level shape:
```json
{
  "coverage_summary": {
    "executable_tc_count": 0,
    "atoms_total": 0,
    "atoms_covered": 0,
    "gaps": []
  },
  "traceability_matrix_rows": [
    {"atom_id": "ATOM-001", "source_ref": "SRC-001", "coverage_status": "covered", "covered_by_tc": "TC-001", "notes": ""}
  ],
  "findings": [
    {"id": "SEM-001", "review_mode": "traceability", "severity": "warning", "category": "coverage", "test_case_id": "TC-001", "coverage_gap": "", "traceability_ref": "ATOM-001", "problem": "", "evidence": "", "required_change": "", "source_reference": "", "status": "open"}
  ],
  "human_summary": "",
  "recommended_stage_status": "format-review-ready"
}
```

Allowed recommended_stage_status values: semantic-revision-needed, format-review-ready.
Use severity error or warning only for findings that must block progress.
