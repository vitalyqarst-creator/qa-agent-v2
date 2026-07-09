# Blocked Runner Report

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Cycle state: `work/review-cycles/iteration-smoke-search-clear-context/cycle-state.yaml`
- Terminal status: `blocked-input`
- Last runnable stage attempted: `writer-r1`

## Exact Blocker

The live SDK runner started writer session `019f47a4-5be9-73e2-a70a-088e6c74d1a7`, but the turn timed out after the configured supervised timeout.

Runner completion manifest:

- `turn_status: timeout`
- `session_status: failed`
- `state_before_marker: writer-r1|scope-ready-for-writer||work/review-cycles/iteration-smoke-search-clear-context/prompts/prompt.writer-r1.md`
- `state_after_marker: structure-preflight-r1|blocked-input|1|work/review-cycles/iteration-smoke-search-clear-context/prompts/prompt.structure-preflight-r1.md`
- `final_response: work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-timeout-recovery.md`
- `duration_ms: 967000`

The timeout recovery report states:

- writer response: present;
- next review prompt: present;
- expected stage-appropriate scoped profile: `outputs/scoped-validator-profile.structure-preflight-r1.json`;
- profile exists, but `unresolved_warning_error_count=2`.
- blocking scoped findings: `source-row-inventory-missing`, `writer-quality-gate-missing`.

The original runner incorrectly reported a missing writer-stage profile. The actionable blocker is the existing structure-preflight profile with unresolved scoped findings; recovery must not start reviewer execution until those findings are resolved or the profile is regenerated cleanly.

## Consequence

No reviewer stage started. There are no reviewer findings, no revision, no final reviewer output and no sign-off. The generated test-case file was only an unsigned writer draft and has been moved to `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-draft.md`; it must not be treated as a final production artifact.

## Evidence

| artifact | path |
| --- | --- |
| runner events | `work/review-cycles/iteration-smoke-search-clear-context/runner-events.ndjson` |
| session map | `work/review-cycles/iteration-smoke-search-clear-context/codex-session-map.yaml` |
| completion manifest | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-completion.yaml` |
| unsigned writer draft | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-draft.md` |
| timeout recovery report | `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-timeout-recovery.md` |
| after snapshot | `work/review-cycles/iteration-smoke-search-clear-context/versions/after-writer-r1/snapshot-manifest.yaml` |
