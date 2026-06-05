# Codex SDK Orchestration Format

This reference defines how local Codex SDK sessions are used by the session-based review cycle.

The SDK layer is an orchestrator, not a domain-rule source. The SDK runner is not a domain-rule source and must not decide whether reviewer findings are correct. Domain behavior remains in `AGENTS.md`, `skills/` and canonical references.

## Responsibilities

The SDK runner:

- reads `cycle-state.yaml`;
- verifies the transition gate before starting a session;
- acquires a per-cycle runner lock before starting a mutating SDK session;
- writes a heartbeat while a session is running, including current stage and `thread_id` when available;
- starts a new Codex thread for each writer or reviewer stage;
- passes the active transition prompt and required artifact paths;
- records the Codex `thread_id`;
- creates before/after snapshots;
- writes an append-only runner event log for lock/session lifecycle diagnostics;
- writes a stage completion manifest for every completed SDK turn;
- updates cycle metadata after the stage completes.
- can run the full chain until a terminal or non-runnable status by repeatedly reloading `cycle-state.yaml` after each completed session.

The SDK runner must not:

- let writer start reviewer directly;
- let reviewer edit test cases;
- let writer or reviewer sessions edit `codex-session-map.yaml`;
- bypass skill routing or instruction-loading scenarios;
- decide whether reviewer findings are correct;
- create semantic review decisions itself;
- route `round-cap-reached` to UI automation prep.

The SDK runner must not let writer start reviewer directly; every role handoff goes through `cycle-state.yaml` and a new SDK-started session.

## Session Map

Runtime session metadata lives in:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/codex-session-map.yaml
```

Recommended structure:

```yaml
version: 1
ft_slug: <ft-slug>
scope_slug: <scope-slug>
sessions:
  - stage: writer-r1
    skill: ft-test-case-writer
    scenario: writer.session_initial_draft
    thread_id: <codex-thread-id>
    sandbox: workspace_write
    prompt: work/review-cycles/<scope-slug>/prompts/prompt.writer-r1.md
    input_snapshot: work/review-cycles/<scope-slug>/versions/r0-baseline
    output_snapshot: work/review-cycles/<scope-slug>/versions/r1-writer-draft
    started_at: <iso-8601>
    finished_at: <iso-8601>
    status: completed | failed | blocked
```

## Sandbox Policy

Default sandbox by stage:

- `structure-preflight-*`: `workspace_write`, because the reviewer session must write findings, logs, transition prompts and the updated `cycle-state.yaml`.
- `semantic-review-*`: `workspace_write`.
- `format-review-*`: `workspace_write`.
- `writer-*`: `workspace_write`.
- `snapshot` and `validate`: local file write/read only.

`full_access` is not a default for this process.

## Prompt Contract

The active prompt must include:

- selected skill and mode;
- instruction-loading scenario id;
- the exact resolver command `python scripts/resolve_instruction_context.py --scenario <scenario> --budget-report --fail-on-budget`;
- selected required instruction files from the resolver output;
- a requirement that the stage reads those selected files before domain decisions;
- a requirement that the session log records the resolver command, budget status and selected files under inputs read;
- FT package and scope;
- canonical test-case path;
- required source/scope/test-design artifacts;
- current semantic round;
- expected output artifacts;
- verification gates for the session.

The runner should fail before session start if `active_transition_prompt` is missing or if the instruction context resolver fails for the selected scenario. A writer or reviewer stage that cannot prove it loaded the selected instruction context must not sign off or route the cycle forward as semantically complete.

## Runner Commands

The canonical runner entrypoint is:

```powershell
python scripts/codex_review_cycle_runner.py validate --state <cycle-state.yaml>
python scripts/codex_review_cycle_runner.py snapshot --state <cycle-state.yaml> --snapshot-id <id>
python scripts/codex_review_cycle_runner.py doctor --state <cycle-state.yaml>
python scripts/codex_review_cycle_runner.py start --state <cycle-state.yaml> --dry-run
python scripts/codex_review_cycle_runner.py continue --state <cycle-state.yaml> --dry-run
python scripts/codex_review_cycle_runner.py start --state <cycle-state.yaml>
python scripts/codex_review_cycle_runner.py run-until-terminal --state <cycle-state.yaml>
python scripts/codex_review_cycle_runner.py resume --state <cycle-state.yaml> --dry-run
python scripts/codex_review_cycle_runner.py resume --state <cycle-state.yaml>
```

`--dry-run` must verify transition inputs and write no Codex session. It may report the next stage, prompt, sandbox and scenario.

`doctor` is read-only diagnostics. It reports `cycle-state.yaml` validity, next transition summary, lock age/PID status, last runner event and completion manifests. It must not call the instruction resolver, because it is also used when transition inputs are broken.

Without `--dry-run`, `start` / `continue` starts a new Codex thread, runs the active prompt, writes `codex-session-map.yaml`, saves the final response under `outputs/`, and creates before/after snapshots. The runner still must not update semantic verdicts by itself.

`run-until-terminal` starts the next Codex thread, waits for it to finish, reloads `cycle-state.yaml`, validates the next transition, and repeats until `signed-off`, `round-cap-reached`, `blocked-input` or another non-runnable status is reached. It must stop with an error if a completed session does not advance `current_stage`, `stage_status`, `semantic_round` or `active_transition_prompt`, because continuing would risk repeating the same stage. Use `--max-sessions` as a loop safety limit; the default is 12.

`resume` is a safe wrapper for continuing a chain after diagnostics. `resume --dry-run` prints the same diagnostic payload as `doctor`. A stale lock may be recovered by `resume --recover-stale-lock` only when the lock heartbeat is stale and the recorded PID is confirmed dead. If the PID is alive or cannot be checked, the runner must refuse recovery.

If the SDK returns `turn_status = interrupted` after the stage has already written artifacts and advanced a valid `cycle-state.yaml`, the runner may record the session as `status: completed-with-progress` and continue the chain. This is not a semantic decision by the runner: the only accepted evidence is a changed progress marker plus a valid next state. If the state did not advance, if the next state does not validate, or if the raw turn status is a real failure rather than `interrupted`, the runner must stop.

`run-until-terminal --dry-run` validates only the first runnable stage. It must not pretend to know the full future chain, because later routing depends on the stage-owned updates to `cycle-state.yaml`.

## Runner Lock And Heartbeat

Mutating commands (`start`, `continue`, `run-until-terminal`) must create:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/runner.lock.yaml
```

The lock contains at least `pid`, `command`, `state`, `started_at_epoch`, `last_heartbeat_epoch`, current `stage`, `scenario`, `thread_id` and `status`.

While blocked inside the Codex SDK, the runner must keep updating `last_heartbeat_epoch`. A second runner on the same state must fail fast when the lock heartbeat is fresh. If the heartbeat is stale, recovery is explicit: pass `--recover-stale-lock` after confirming no old runner is still active. Recovery archives the stale lock as `runner.lock.recovered-<epoch>.yaml` and appends an `aborted` record to `codex-session-map.yaml` when the stale lock recorded a stage or thread id.

Lock diagnostics must include the recorded PID and whether that PID is alive, dead or unknown. Stale-lock recovery must not proceed when the recorded PID is alive or cannot be checked.

Do not solve timeout ambiguity by launching a second runner in parallel. Increase the external shell timeout, inspect `runner.lock.yaml`, or recover a stale lock deliberately.

## Runner Event Log

The runner writes append-only lifecycle events to:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/runner-events.ndjson
```

Each line is one JSON object with at least `ts_epoch` and `event`. Expected event types include `lock_acquired`, `lock_blocked`, `lock_recovered`, `lock_released`, `session_preparing`, `input_snapshot_created`, `thread_started`, `turn_started`, `turn_finished`, `turn_exception` and `stage_completed`.

The event log is diagnostic evidence only. It must not replace `cycle-state.yaml`, `codex-session-map.yaml`, reviewer findings or completion manifests.

## Stage Completion Manifest

For every stage that reaches post-turn classification, the runner writes:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/<stage>-completion.yaml
```

The manifest records stage, role, scenario, thread/turn ids, raw `turn_status`, classified `session_status`, before/after progress markers, state advancement, final response path, input/output snapshot paths and timing. The after-snapshot must include this manifest and the runner event log.

## Completion Evidence

A completed stage requires:

- session record in `codex-session-map.yaml`;
- `status: started` session record written before blocking on the SDK run, so interrupted runner processes still leave the `thread_id`;
- append-only entries in `runner-events.ndjson`;
- `<stage>-completion.yaml` in `outputs/`;
- for `turn_status: interrupted`, `status: completed-with-progress` is allowed only when `cycle-state.yaml` advanced and validates;
- no active `runner.lock.yaml` remains after normal completion;
- output snapshot with `snapshot-manifest.yaml`;
- expected stage artifacts present;
- updated `cycle-state.yaml`;
- validation command output showing no gate violation for the next transition.
