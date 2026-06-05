# Writer Handoff Format

Runtime handoff reference for `ft-test-case-writer`. It gives the minimum writer-to-reviewer transition contract. Full process details stay in `workflow-state-format.md`, `session-log-format.md`, `agent-decision-log-format.md` and `next-step-prompt-format.md`.

## Required Writer Handoff

When writer is ready for review, it must provide:

- canonical test-case file path;
- split test-design directory path, if created;
- `workflow-state.yaml` with `current_stage: ft-test-case-writer`;
- `stage_status: ready-for-review`;
- `next_skill: ft-test-case-reviewer`;
- `required_inputs` for reviewer;
- `latest_artifacts.canonical_test_cases`;
- `latest_artifacts.session_log` or `latest_artifacts.writer_session_log`;
- `latest_artifacts.decision_log`;
- `prompt.writer-to-reviewer.round-N.md`.

If any required input is missing, use `stage_status: blocked-input`.

## Reviewer Prompt Minimum

The active prompt must name:

- FT package;
- confirmed scope;
- canonical test-case file;
- source/scope artifacts reviewer must read;
- review mode, default `full`;
- known `GAP-*`, accepted risks and blocking constraints;
- expected output artifacts.

If `latest_artifacts.active_transition_prompt` is set, it must point to the actual active writer-to-reviewer prompt.

## Do Not

- Do not leave stale same-direction prompt aliases beside a newer active prompt.
- Do not route to reviewer with unresolved blocking writer gate failure.
- Do not use `stage_status: not-signed-off`; this is not a process status.
