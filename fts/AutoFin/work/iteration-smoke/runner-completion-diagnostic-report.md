# Runner Completion Diagnostic Report

## Scope

- FT package: `AutoFin`
- Scope: `iteration-smoke-widget-selection-types`
- Cycle state: `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`
- Failed stage: `writer-r1`
- Scenario: `writer.session_initial_draft`
- Writer threads:
  - `019f4756-8a46-7c50-99c2-8556e27c63e1`
  - `019f4760-1d88-75a3-8c53-f08df136f6de`

## Expected Writer Stage Terminal Contract

For `writer-r1`, runner-owned completion evidence must include:

- `runner-events.ndjson` entries:
  - `thread_started`
  - `turn_started`
  - `turn_finished`
  - `stage_completed`
- `outputs/writer-r1-completion.yaml`
- a `codex-session-map.yaml` record with `stage: writer-r1`, thread id, raw `turn_status`, classified `session_status`, snapshots and final response path
- `cycle-state.yaml` progress from `scope-ready-for-writer` to `writer-draft-ready`
- next prompt: `prompts/prompt.structure-preflight-r1.md`

The expected completion manifest path is:

```text
fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/outputs/writer-r1-completion.yaml
```

Expected completion event shape is an append-only JSON event similar to:

```json
{
  "event": "stage_completed",
  "stage": "writer-r1",
  "thread_id": "<codex-thread-id>",
  "turn_id": "<codex-turn-id>",
  "session_status": "completed|completed-with-progress|failed",
  "output_snapshot": "after-writer-r1",
  "completion_manifest": "work/review-cycles/iteration-smoke-widget-selection-types/outputs/writer-r1-completion.yaml"
}
```

## Actual Writer Outputs

Produced writer artifacts:

- `outputs/writer-r1-response.md`
- `outputs/writer-session-log.writer-r1.md`
- `outputs/agent-decision-log.writer-r1.md`
- `outputs/source-excerpt.writer-r1.md`
- `outputs/scoped-validator-profile.writer-r1.json`
- `outputs/validator-report.writer-r1.initial.json`
- `outputs/validator-report.writer-r1.after-fix1.json`
- `outputs/validator-report.writer-r1.after-fix2.json`
- `work/test-design/3-iteration-smoke-widget-selection-types/`
- `work/iteration-smoke/writer-draft-from-interrupted-run.md`

Missing terminal runner artifacts:

- `outputs/writer-r1-completion.yaml`
- child payload JSON for either parent PID
- `turn_finished` event
- `stage_completed` event

## Actual Runner Events

The event log contains:

- first attempt: `lock_acquired`, `session_child_started`, `session_preparing`, `input_snapshot_created`, `thread_started`, `turn_started`
- stale-lock recovery
- second attempt: the same sequence through `turn_started`
- final recover-only lock archive/release

It does not contain a completion event for either thread.

## Why State Did Not Advance

The process-supervised runner expected the SDK child to exit and write:

```text
outputs/writer-r1-child-payload-<parent-pid>.json
```

The parent process was interrupted before the SDK child produced the payload and before the parent timeout recovery path ran. On `resume --recover-stale-lock`, the old code archived the stale lock and immediately started another `writer-r1` session because it did not inspect missing completion evidence from the interrupted attempt first.

This caused repeated writer sessions instead of either:

- recovering from complete writer artifacts, or
- writing an explicit blocked state with the missing manifest/event named.

## Writer Response Assessment

The writer response was not obviously malformed:

- it declared `result: writer-draft-ready`
- it listed the canonical test-case path
- it listed test-design artifacts
- it listed `prompt.structure-preflight-r1.md`
- scoped validator profile had `unresolved_warning_error_count = 0`

However, the committed smoke evidence intentionally withheld the production TC from `fts/AutoFin/test-cases/` because no reviewer stage ran. Therefore the original run remains unacceptable as final test-case output. The runner may recover state from artifacts only when the writer response, clean scoped validator profile, next prompt and required writer artifacts are all present.

## Root Cause

Runner resume had no stale-lock completion audit. After recovering a stale lock, it did not check whether the recovered stage was missing its completion manifest before starting the same stage again.

This was a runner/process issue, not a test-case content issue.

## Fix Implemented

The runner now checks recovered stale-lock sessions before launching a new SDK turn:

- if the expected `<stage>-completion.yaml` is missing but writer artifacts are complete enough, it writes a recovered completion manifest with `turn_status: interrupted`, `session_status: completed-with-progress`, advances to the next review stage, and stops;
- if the completion manifest and required writer artifacts are missing or ambiguous, it writes `blocked-runner-completion-missing`, records a completion manifest, updates `cycle-state.yaml` to `blocked-input`, and stops;
- `doctor` now reports the expected completion manifest, terminal events and recoverable writer next state for the next runnable stage;
- `validate` now accepts `blocked-input` when the production TC is intentionally absent.

## Recovery Classification For This Failed Run

The original failed run is partially recoverable as diagnostic evidence, but not recoverable to accepted final output:

- writer response: present
- scoped validator profile: present and clean
- next prompt: present
- production canonical TC: withheld after the failed smoke
- reviewer stage: not started
- final TC: not produced

The correct current state remains `blocked-input` unless the writer stage is rerun or the production draft is deliberately restored for review. Creating a fake final TC would be incorrect.

## Verification

- `python -m pytest tests/test_codex_review_cycle_runner.py -q`: pass, `93 passed`
- `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`: pass, blocked state is valid and no production TC is required
- `python scripts/codex_review_cycle_runner.py doctor --state fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`: pass, no active lock and no completion manifests for the historical blocked run
