Session-based review-cycle stage.
cycle_id: client-documents-upload-and-actuality-2026-06-25
stage: structure-preflight-r1
role: reviewer
instruction_scenario: reviewer.structure_preflight
cycle_state: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17\work\review-cycles\client-documents-upload-and-actuality\cycle-state.yaml
ft_root: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17
canonical_test_cases: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17\test-cases\section-31-client-documents-upload-and-actuality.md

Runner state contract:
- cycle-state.yaml is the source of truth for this automated chain.
- Before ending the session, update cycle-state.yaml to the next lifecycle status, semantic round and active transition prompt according to session-based-review-cycle-format.md.
- Keep cycle-state.yaml in runner simple-YAML form: top-level scalar fields plus top-level string lists only. Do not write nested maps under latest_artifacts, blocking_reasons, blocking_findings, open_questions, accepted_risks or sessions; put rich detail in sidecar artifacts and list their paths.
- If the active prompt below mentions workflow-state.yaml, update it only as compatibility; do not leave cycle-state.yaml stale.
- Use session-based stage_status values from cycle-state.yaml, not legacy workflow-state.yaml status names.
- Writer sessions must not set writer-draft-ready or semantic-review-ready while the current scoped validator profile has any error/warning finding; resolve the findings or route to blocked-input with evidence.
- In session-based writer stages, prefer stage-specific output names such as outputs/writer-session-log.<stage>.md and outputs/agent-decision-log.<stage>.md; legacy writer-session-log.md is tolerated only as compatibility evidence.
- Do not edit codex-session-map.yaml; it is owned by the SDK runner.

Instruction loading contract:
- Before domain work, run: python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
- Read every selected required file listed below before making writer/reviewer decisions.
- If the resolver fails, a selected required file cannot be read, or budget status is not pass, do not sign off; record the blocker in the stage output.
- In the session log, record the resolver command, budget status, and selected files under inputs read.
- Resolved now: 12 files, budget pass (176.2 / 210.0 KiB).
- Selected required files:
  - AGENTS.md (group=global_core)
  - skills/README.md (group=global_core)
  - references/agent/session-based-review-cycle-format.md (group=review_cycle_core)
  - references/agent/codex-sdk-orchestration-format.md (group=review_cycle_core)
  - skills/ft-test-case-reviewer/SKILL.md (group=reviewer_structure_preflight_core)
  - references/agent/reviewer-output-format.md (group=reviewer_structure_preflight_core)
  - references/qa/review-findings-format.md (group=reviewer_structure_preflight_core)
  - references/qa/test-case-runtime-format.md (group=reviewer_structure_preflight_core)
  - references/agent/workflow-state-format.md (group=reviewer_process_artifacts)
  - references/agent/session-log-format.md (group=reviewer_process_artifacts)
  - references/agent/agent-decision-log-format.md (group=reviewer_process_artifacts)
  - references/agent/next-step-prompt-format.md (group=reviewer_process_artifacts)

Use the prompt below as the active transition prompt. Do not rely on prior chat history.

# Prompt: Structure Preflight R1

Run `reviewer.structure_preflight` for `ft-2-OF_17` / `client-documents-upload-and-actuality`.

## Instruction Loading

Before review, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file before review decisions. If resolver fails or budget is not pass, do not advance the cycle.

## Inputs

- Canonical test cases: `test-cases/section-31-client-documents-upload-and-actuality.md`
- Test-design dir: `work/test-design/section-31-client-documents-upload-and-actuality/`
- Writer response: `work/review-cycles/client-documents-upload-and-actuality/outputs/writer-r1-response.md`
- Writer session log: `work/review-cycles/client-documents-upload-and-actuality/outputs/writer-session-log.writer-r1.md`
- Writer decision log: `work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.writer-r1.md`
- Scoped validator profile: `work/review-cycles/client-documents-upload-and-actuality/outputs/scoped-validator-profile.writer-r1.json`
- Scope contract: `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-contract.md`
- Source row inventory: `work/stage-handoffs/08-client-documents-upload-and-actuality/source-row-inventory.md`
- Coverage gaps: `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-coverage-gaps.md`

## Review Mode

Use `structure_preflight` only: parseability, canonical TC runtime fields, continuous numbering, required split artifact headings/table columns, no duplicate wrapper headings, and current writer-stage scoped validator evidence.

Do not perform semantic coverage review in this stage.

## Expected Output

- `work/review-cycles/client-documents-upload-and-actuality/outputs/structure-preflight-r1-findings.md`
- `work/review-cycles/client-documents-upload-and-actuality/outputs/reviewer-session-log.structure-preflight-r1.md`
- `work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.structure-preflight-r1.md`
- Updated `cycle-state.yaml` to `semantic-review-ready` if structure passes, or `structure-preflight-blocked` with a writer remediation prompt if blocked.
