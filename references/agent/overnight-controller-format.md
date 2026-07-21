# Overnight Controller Contract

This reference defines the durable queue used for long local production and
verification runs. It is an execution controller, not a source of FT semantics.

## Entrypoint and state

Use:

```powershell
python scripts/run_overnight_controller.py <init|run|retry|status|summary> ...
```

The controller owns one immutable run directory:

```text
fts/<ft-slug>/work/overnight-runs/<run-id>/
  overnight-state.yaml
  attempts/<job-id>/<attempt-id>/
  overnight-summary.md
```

`overnight-state.yaml` is atomically replaced after every transition and is the
only queue-status source. Its JSON serialization is valid YAML 1.2. It records
the goal, queue, current/completed/deferred/blocked work, timestamps, exact
continuation commands, artifact/log links and the last confirmed safe state.

Allowed job states are `pending`, `running`, `completed`,
`deferred-transient`, `blocked-scope` and `failed-infrastructure`. The run must
continue while any dependency-satisfied `pending` or retriable
`deferred-transient` job exists. A scope blocker never becomes a global blocker.

## Failure policy

- Network/backend/model-capacity failures are `deferred-transient`; local work
  continues and retry creates a new attempt. Exhausting the automatic attempt
  budget preserves `deferred-transient` with `retry_exhausted: true` and an
  explicit requeue command; it must not be relabelled as an infrastructure defect.
- A requirement ambiguity or scope-local input blocker is `blocked-scope`; its
  evidence and continuation command remain in state while other jobs run.
- A validator/gate failure must be classified as product-artifact or
  infrastructure failure before bounded repair.
- A runner defect terminates that benchmark attempt. Repair happens as a
  separate job and the benchmark restarts as a new clean job/attempt.
- Round cap preserves the candidate and routes to another job without weakening
  reviewer gates.
- Only corrupted mandatory DOCX/XHTML inputs or a repository-wide integrity
  defect may set `global_blocker`.

Every attempt directory is immutable and contains `command.json`, stdout,
stderr and `result.json`. Interrupted `running` jobs recover as transient and a
retry always receives a new attempt ID; an old attempt is never resumed.

## Integrity and completion

Optional `source_guard` entries bind paths to SHA-256. A mismatch is checked
before each command and fails closed without launching the job. A per-run lock
prevents concurrent controllers from mutating the same state.

Jobs may define a positive `timeout_seconds` and a `timeout_classification`.
The watchdog terminates only that attempt's child process tree, records the
termination evidence, and applies the declared classification. Live backend
jobs should normally classify watchdog expiry as `transient`; benchmark retries
must still use fresh handoff, cycle, observation and result paths.

The generated summary must distinguish completed work, transient deferrals,
scope blockers and infrastructure failures, and must include exact continuation
commands. Controller completion does not imply reviewer sign-off; downstream
production artifacts retain their own gates and lifecycle state.
