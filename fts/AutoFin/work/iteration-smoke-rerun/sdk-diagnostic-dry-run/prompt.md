Standalone SDK diagnostic safety contract.
diagnostic_output_dir: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\AutoFin\work\iteration-smoke-rerun\sdk-diagnostic-dry-run
- Do not edit cycle-state.yaml, runner.lock.yaml, codex-session-map.yaml, snapshots, or files under fts/.
- If the embedded prompt asks for reviewer artifacts, write diagnostic copies only under diagnostic_output_dir/reviewer-artifacts/.
- If the embedded prompt asks for a state transition, report the intended transition in response.md only.
- This diagnostic turn must not mutate the review cycle.

Session-based structure-preflight stage.
cycle_id: autofin-iteration-smoke-search-clear-context
stage: structure-preflight-r1
role: reviewer
instruction_scenario: reviewer.structure_preflight
cycle_state: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\AutoFin\work\review-cycles\iteration-smoke-search-clear-context\cycle-state.yaml
ft_root: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\AutoFin
active_prompt_path: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\AutoFin\work\review-cycles\iteration-smoke-search-clear-context\prompts\prompt.structure-preflight-r1.md

Slim runtime contract:
- The runner already resolved the instruction context for reviewer.structure_preflight.
- Resolved context budget: pass (175.8 / 210.0 KiB).
- Do not rerun the instruction resolver and do not read the selected instruction files in this SDK turn.
- Use the bounded checks and output paths below as the runtime contract for this preflight.
- Do not recursively read directories and do not read validator-report*.json.
- Do not perform semantic coverage review.
- If structure evidence is missing or too broad to inspect safely, block with a structure finding instead of broadening the search.

Exact review inputs:
- test-cases/4.2-iteration-smoke-rerun-search-clear-context.md
- work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md
- work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-contract.md
- work/stage-handoffs/19-iteration-smoke-search-clear-context/source-row-inventory.md
- work/stage-handoffs/19-iteration-smoke-search-clear-context/source-parity-check.md
- work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-coverage-gaps.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/source-row-inventory.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/source-row-completeness-matrix.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/source-table-normalization.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/test-design-decision-table.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/coverage-obligation-table.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/atomic-requirements-ledger.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/package-test-design-plan.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/test-design-applicability-matrix.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/coverage-metrics.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/fixture-catalog.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/risk-priority-map.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/coverage-map.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/coverage-gaps.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/test-design-review.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/writer-quality-gate.md
- work/test-design/4.2-iteration-smoke-rerun-search-clear-context/writer-self-check.md
- work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-response.md
- work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-session-log.writer-r1.md
- work/review-cycles/iteration-smoke-search-clear-context/outputs/agent-decision-log.writer-r1.md

Structure checks:
- Markdown parseability and duplicate wrapper headings.
- Canonical TC runtime fields/sections and continuous TC numbering.
- Required split artifact shape only for the bounded test-design files above.
- Current writer-stage scoped validator evidence from scoped-validator-profile.*.json.

Required outputs:
- work/review-cycles/iteration-smoke-search-clear-context/outputs/structure-preflight-r1-findings.md
- work/review-cycles/iteration-smoke-search-clear-context/outputs/reviewer-session-log.structure-preflight-r1.md
- work/review-cycles/iteration-smoke-search-clear-context/outputs/agent-decision-log.structure-preflight-r1.md

State transition:
- If structure passes, update cycle-state.yaml to stage_status: semantic-review-ready and keep semantic_round unchanged.
- If structure blocks, update cycle-state.yaml to stage_status: structure-preflight-blocked and create a writer-structure remediation prompt.
- Keep cycle-state.yaml in runner simple-YAML form with top-level scalar fields plus top-level string lists only.
- Do not edit codex-session-map.yaml; it is owned by the SDK runner.