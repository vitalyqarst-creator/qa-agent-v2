Standalone SDK diagnostic safety contract.
diagnostic_output_dir: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\evals\sdk-turn-diagnostics\semantic-runner-composed-dry-run
- Do not edit cycle-state.yaml, runner.lock.yaml, codex-session-map.yaml, snapshots, or files under fts/.
- If the embedded prompt asks for reviewer artifacts, write diagnostic copies only under diagnostic_output_dir/reviewer-artifacts/.
- If the embedded prompt asks for a state transition, report the intended transition in response.md only.
- This diagnostic turn must not mutate the review cycle.

Session-based structure-preflight stage.
cycle_id: client-documents-upload-and-actuality-2026-06-25
stage: structure-preflight-r1
role: reviewer
instruction_scenario: reviewer.structure_preflight
cycle_state: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17\work\review-cycles\client-documents-upload-and-actuality\cycle-state.yaml
ft_root: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17
active_prompt_path: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\fts\ft-2-OF_17\work\review-cycles\client-documents-upload-and-actuality\prompts\prompt.semantic-review-r1.md

Slim runtime contract:
- The runner already resolved the instruction context for reviewer.structure_preflight.
- Resolved context budget: pass (176.2 / 210.0 KiB).
- Do not rerun the instruction resolver and do not read the selected instruction files in this SDK turn.
- Use the bounded checks and output paths below as the runtime contract for this preflight.
- Do not recursively read directories and do not read validator-report*.json.
- Do not perform semantic coverage review.
- If structure evidence is missing or too broad to inspect safely, block with a structure finding instead of broadening the search.

Exact review inputs:
- test-cases/section-31-client-documents-upload-and-actuality.md
- work/review-cycles/client-documents-upload-and-actuality/outputs/writer-r1-response.md
- work/review-cycles/client-documents-upload-and-actuality/outputs/writer-session-log.writer-r1.md
- work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.writer-r1.md
- work/review-cycles/client-documents-upload-and-actuality/outputs/scoped-validator-profile.writer-r1.json
- work/review-cycles/client-documents-upload-and-actuality/prompts/prompt.writer-structure-r1.md
- work/review-cycles/client-documents-upload-and-actuality/prompts/prompt.semantic-review-r1.md
- work/test-design/section-31-client-documents-upload-and-actuality/writer-quality-gate.md
- work/test-design/section-31-client-documents-upload-and-actuality/test-design-review.md
- work/test-design/section-31-client-documents-upload-and-actuality/package-test-design-plan.md

Structure checks:
- Markdown parseability and duplicate wrapper headings.
- Canonical TC runtime fields/sections and continuous TC numbering.
- Required split artifact shape only for the bounded test-design files above.
- Current writer-stage scoped validator evidence from scoped-validator-profile.*.json.

Required outputs:
- work/review-cycles/client-documents-upload-and-actuality/outputs/structure-preflight-r1-findings.md
- work/review-cycles/client-documents-upload-and-actuality/outputs/reviewer-session-log.structure-preflight-r1.md
- work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.structure-preflight-r1.md

State transition:
- If structure passes, update cycle-state.yaml to stage_status: semantic-review-ready and keep semantic_round unchanged.
- If structure blocks, update cycle-state.yaml to stage_status: structure-preflight-blocked and create a writer-structure remediation prompt.
- Keep cycle-state.yaml in runner simple-YAML form with top-level scalar fields plus top-level string lists only.
- Do not edit codex-session-map.yaml; it is owned by the SDK runner.