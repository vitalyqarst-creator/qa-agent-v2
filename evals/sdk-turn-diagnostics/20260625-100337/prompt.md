Standalone SDK diagnostic safety contract.
diagnostic_output_dir: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\evals\sdk-turn-diagnostics\20260625-100337
- Do not edit cycle-state.yaml, runner.lock.yaml, codex-session-map.yaml, snapshots, or files under fts/.
- If the embedded prompt asks for reviewer artifacts, write diagnostic copies only under diagnostic_output_dir/reviewer-artifacts/.
- If the embedded prompt asks for a state transition, report the intended transition in response.md only.
- This diagnostic turn must not mutate the review cycle.

# Bounded semantic traceability and test-design review

This is a bounded read-only reviewer turn.
Do not edit files. Do not update cycle-state.yaml. Do not create reviewer artifacts.
Do not recursively read directories. Do not scan unrelated files. Read only the exact files listed below.

## Stage
- stage: semantic-review-r1
- scenario: reviewer.semantic_traceability_test_design
- cycle_id: client-documents-upload-and-actuality-2026-06-25
- scope_slug: client-documents-upload-and-actuality

## Allowed Files
- fts/ft-2-OF_17/test-cases/section-31-client-documents-upload-and-actuality.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/package-test-design-plan.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/atomic-requirements-ledger.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/coverage-map.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/test-design-decision-table.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/test-design-applicability-matrix.md
- fts/ft-2-OF_17/work/test-design/section-31-client-documents-upload-and-actuality/fixture-catalog.md

## Open Questions
- GAP-001: exact UI notification text after sending SMS for online document signing is not confirmed; cover only observable UI notification/modal, not SMS/backend delivery.
- GAP-002: exact invalid format and oversize file error messages are not confirmed; use conservative rejection/error indication only.
- GAP-003: PDF pages and possible PDF-only GSR IDs are not confirmed; use DOCX/SRC anchors only.

## Accepted Risks
- source-quality-oversized-blocks: active DOCX has large unrelated source blocks; selected scope rows are split into SRC-001..SRC-015 and used defensively.

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
