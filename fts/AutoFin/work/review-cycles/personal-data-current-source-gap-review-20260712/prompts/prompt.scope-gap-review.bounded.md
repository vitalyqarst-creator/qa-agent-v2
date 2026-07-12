# Bounded reviewer stage

This is a bounded read-only reviewer turn.
Do not edit files. Do not update cycle-state.yaml. Do not create reviewer artifacts.
Do not recursively read directories. Read only the exact files listed below.

## Stage
- stage: scope-gap-review
- scenario: reviewer.scope_gap_review
- cycle_id: personal-data-current-source-gap-review-20260712
- scope_slug: application-card-client-personal-data

## Allowed Files
- fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/prompts/next.md
- fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/workflow-state.yaml
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/mockup-visual-inventory.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/negative-oracle-inventory.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/requiredness-oracle-inventory.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md
- fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/final-bsr-evidence.json
- fts/AutoFin/AGENT-NOTES.md

## Required Output
Return fenced JSON only. Do not include prose outside the JSON fence.
Use this exact top-level shape:
```json
{
  "findings": [
    {"id": "REV-001", "severity": "warning", "category": "scope-gap", "gap_id": "GAP-001", "problem": "", "evidence": "", "required_change": "", "source_reference": "", "status": "open"}
  ],
  "human_summary": "",
  "recommended_stage_status": "scope-ready-for-writer"
}
```

Allowed recommended_stage_status values: blocked-input, scope-gap-review-passed, scope-ready-for-writer.
Use severity error or warning only for findings that must block progress.
