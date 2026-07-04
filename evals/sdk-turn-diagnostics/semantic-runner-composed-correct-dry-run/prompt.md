Standalone SDK diagnostic safety contract.
diagnostic_output_dir: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\evals\sdk-turn-diagnostics\semantic-runner-composed-correct-dry-run
- Do not edit cycle-state.yaml, runner.lock.yaml, codex-session-map.yaml, snapshots, or files under fts/.
- If the embedded prompt asks for reviewer artifacts, write diagnostic copies only under diagnostic_output_dir/reviewer-artifacts/.
- If the embedded prompt asks for a state transition, report the intended transition in response.md only.
- This diagnostic turn must not mutate the review cycle.

Session-based review-cycle stage.
cycle_id: client-documents-upload-and-actuality-2026-06-25
stage: semantic-review-r1
role: reviewer
instruction_scenario: reviewer.semantic_traceability_test_design
cycle_state: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17\work\review-cycles\client-documents-upload-and-actuality\cycle-state.semantic-diagnostic.yaml
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
- Before domain work, run: python scripts/resolve_instruction_context.py --scenario reviewer.semantic_traceability_test_design --budget-report --fail-on-budget
- Read every selected required file listed below before making writer/reviewer decisions.
- If the resolver fails, a selected required file cannot be read, or budget status is not pass, do not sign off; record the blocker in the stage output.
- In the session log, record the resolver command, budget status, and selected files under inputs read.
- Resolved now: 18 files, budget pass (265.9 / 290.0 KiB).
- Selected required files:
  - AGENTS.md (group=global_core)
  - skills/README.md (group=global_core)
  - references/agent/session-based-review-cycle-format.md (group=review_cycle_core)
  - references/agent/codex-sdk-orchestration-format.md (group=review_cycle_core)
  - skills/ft-test-case-reviewer/SKILL.md (group=reviewer_semantic_core)
  - references/agent/reviewer-output-format.md (group=reviewer_semantic_core)
  - references/agent/package-test-design-plan-format.md (group=reviewer_semantic_core)
  - references/agent/dictionary-inventory-format.md (group=reviewer_semantic_core)
  - references/agent/test-design-defect-taxonomy.md (group=reviewer_semantic_core)
  - references/qa/review-findings-format.md (group=reviewer_semantic_core)
  - references/qa/traceability-matrix-format.md (group=reviewer_semantic_core)
  - references/qa/test-design-review-rubric.md (group=reviewer_semantic_core)
  - references/qa/coverage-runtime-checklist.md (group=reviewer_semantic_core)
  - references/qa/traceability-rules.md (group=reviewer_semantic_core)
  - references/agent/workflow-state-format.md (group=reviewer_process_artifacts)
  - references/agent/session-log-format.md (group=reviewer_process_artifacts)
  - references/agent/agent-decision-log-format.md (group=reviewer_process_artifacts)
  - references/agent/next-step-prompt-format.md (group=reviewer_process_artifacts)



Use the prompt below as the active transition prompt. Do not rely on prior chat history.

# Semantic traceability and test-design review

Structure preflight `structure-preflight-r1` passed deterministically.
Run reviewer.semantic_traceability_test_design against the current scope.
Do not repeat runner-owned structure checks except where they affect semantic coverage.
Write reviewer findings, session log, decision log and update cycle-state.yaml according to the session lifecycle.
