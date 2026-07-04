Standalone SDK diagnostic safety contract.
diagnostic_output_dir: C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2\evals\sdk-turn-diagnostics\semantic-active-correct-dry-run
- Do not edit cycle-state.yaml, runner.lock.yaml, codex-session-map.yaml, snapshots, or files under fts/.
- If the embedded prompt asks for reviewer artifacts, write diagnostic copies only under diagnostic_output_dir/reviewer-artifacts/.
- If the embedded prompt asks for a state transition, report the intended transition in response.md only.
- This diagnostic turn must not mutate the review cycle.

# Semantic traceability and test-design review

Structure preflight `structure-preflight-r1` passed deterministically.
Run reviewer.semantic_traceability_test_design against the current scope.
Do not repeat runner-owned structure checks except where they affect semantic coverage.
Write reviewer findings, session log, decision log and update cycle-state.yaml according to the session lifecycle.
