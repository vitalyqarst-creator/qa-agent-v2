---
name: ft-test-case-iteration
description: Orchestrate the session-based writer/reviewer cycle for an already confirmed FT package and scope. Use the backend dispatcher with verified Codex exec by default; keep SDK as an explicit fallback. Do not perform writer or reviewer work inside the same session.
---

# FT Test Case Iteration

This skill is a thin orchestrator for the session-based writer/reviewer cycle.

Use it only when:

- the FT package is already selected;
- a concrete external `scope_slug` is confirmed;
- `scope-contract.md`, `scope-coverage-gaps.md` and the required source handoff artifacts already exist;
- the intended canonical test-case path is known.

If these inputs are missing, return to `ft-source-locator` or `ft-scope-analyzer`.

## Core Rule

Do not run writer and reviewer work inside this same chat/session.

`ft-test-case-iteration` prepares and validates the cycle inputs, then uses `scripts/review_cycle_backend_dispatcher.py --backend auto` to select verified Codex exec and start writer and reviewer in separate processes and sessions. The SDK runner is an explicit v1 fallback, never a silent default.

The source of truth for active lifecycle state is:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/cycle-state.yaml
```

New runs must not create or update:

```text
fts/<ft-slug>/work/review-loops/<scope-slug>/
```

That path is legacy-only historical evidence.

## Входы

Required inputs:

- confirmed FT package;
- confirmed `scope_slug`;
- active handoff folder under `work/stage-handoffs/NN-<scope-slug>/`;
- `stage-handoffs/` remains the human handoff layer; active cycle execution state remains in `work/review-cycles/<scope-slug>/cycle-state.yaml`;
- required source/scope artifacts listed in the workflow below.

## Выходы

For a new cycle, ensure these locations exist or are created by the runner:

- canonical test cases: `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`;
- cycle state: `fts/<ft-slug>/work/review-cycles/<scope-slug>/cycle-state.yaml`;
- session map: `fts/<ft-slug>/work/review-cycles/<scope-slug>/codex-session-map.yaml`;
- prompts: `fts/<ft-slug>/work/review-cycles/<scope-slug>/prompts/`;
- session outputs: `fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/`;
- snapshots: `fts/<ft-slug>/work/review-cycles/<scope-slug>/versions/<snapshot-id>/`.

`workflow-state.yaml` in the active handoff folder may point to `cycle-state.yaml` for compatibility, but it must not be used to route the new process back to `work/review-loops/`.

## Workflow

1. Validate that the selected FT package and scope are stable.
2. Read `AGENT-NOTES.md` from the FT package root if it exists.
3. Confirm required scope artifacts:
   - `scope-contract.md`;
   - `scope-coverage-gaps.md`;
   - `source-parity-check.md` when DOCX and PDF are both available;
   - `source-row-inventory.md` for row-level/table-heavy scopes;
   - `mockup-visual-inventory.md` for UI scopes with mockups.
4. If `cycle-state.yaml` does not exist, create it using `session-based-review-cycle-format.md`.
5. Put active transition prompts under `work/review-cycles/<scope-slug>/prompts/`.
6. Run dry-run validation before starting or continuing:

```powershell
.\scripts\run_cycle.ps1 validate --state <cycle-state.yaml>
.\scripts\run_cycle.ps1 start --state <cycle-state.yaml> --dry-run
```

7. Start a fresh immutable cycle through the dispatcher using a reviewed JSON config:

```powershell
.\.venv\Scripts\python.exe scripts\review_cycle_backend_dispatcher.py --backend auto --config <dispatcher-config.json> --selection-output <backend-selection.json>
```

Use `--backend sdk` only for an explicit v1 diagnostic/fallback run. Use `--allow-sdk-fallback` only when the caller has deliberately authorized fallback after a failed exec capability probe.

For `simple-field-property`, keep the default `prepared_fast_writer_mode=structured`: the writer is read-only and the runner materializes its schema-constrained draft. Select `workspace` only as an explicit legacy experiment; never use it as automatic recovery from a failed structured attempt.

For `standard-required`, keep the default `prepared_standard_writer_mode=structured`: the compiler supplies an explicit context profile, writer/reviewer use bounded embedded runtime profiles, and the runner materializes the draft and deterministic gate bundle. Select `assisted` only in a newly compiled immutable cycle when a named OBL/ATOM needs targeted registered-source fallback; never switch modes inside a failed cycle.

For a structured package above the runner's single-session TC limit, require output-capacity preflight and the canonical bounded-shard route. Keep every `planned_test_case_id` group intact, require complete/disjoint TC and obligation membership, use a fresh session for every shard, and allow only runner-owned deterministic merge. Do not send the same full-scope one-shot prompt as a retry. Run one fresh reviewer only after the merged draft passes all full-set deterministic gates.

8. Stop at `signed-off`, `round-cap-reached`, `blocked-input` or any non-runnable status. Do not manually advance semantic verdicts.

## Gates

- Do not start semantic review when structure preflight has blocking findings.
- Do not start final format review before semantic review passes.
- Do not start a third semantic review round. After round 2, unresolved semantic findings mean `round-cap-reached`.
- Do not route `round-cap-reached` or `blocked-input` to `ft-ui-automation-prep`.
- Do not mark `signed-off` unless `cycle-state.yaml`, latest reviewer outputs and snapshots prove semantic closure and final format/regression closure.
- Require traceability closure before `signed-off`: every closed traceability finding is checked by `traceability_ref` / `atom_id`, every writer response preserves `affected_traceability_refs`, and закрытие traceability gaps проверяется по `traceability_ref` / `atom_id`.
- After `signed-off`, route only through the post-iteration вход в `ft-ui-automation-prep`; that stage prepares automation-ready версии without rewriting the FT-first baseline.
- If repeated quality failures meet `quality-feedback-loop.md` triggers, create or update `evals/candidates/YYYY-MM-DD-<failure-class>-<short-scope>.md` instead of hiding the issue in the current cycle.

## Artifact Rules

- Writer sessions may edit canonical test cases and writer test-design artifacts.
- Reviewer sessions may write findings, matrices, summaries, prompts and self-checks, but must not edit canonical test cases.
- The exec runner owns v2 cycle transitions and immutable attempt artifacts. The SDK runner may update v1 `cycle-state.yaml`, `codex-session-map.yaml`, lock/heartbeat files and snapshots only on an explicit fallback route; neither runner may invent review decisions.
- Snapshots follow `references/qa/test-case-versioning-policy.md`.
- Session metadata follows `references/agent/codex-sdk-orchestration-format.md`.

## Canonical References

- Session-based lifecycle: [../../references/agent/session-based-review-cycle-format.md](../../references/agent/session-based-review-cycle-format.md)
- Backend and SDK fallback orchestration: [../../references/agent/codex-sdk-orchestration-format.md](../../references/agent/codex-sdk-orchestration-format.md)
- Test-case versioning: [../../references/qa/test-case-versioning-policy.md](../../references/qa/test-case-versioning-policy.md)
- Workflow state compatibility: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Stage handoff model: [../../references/agent/stage-handoff-model.md](../../references/agent/stage-handoff-model.md)
- Session log format: [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md)
- Agent decision log format: [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md)
- Quality feedback loop: [../../references/agent/quality-feedback-loop.md](../../references/agent/quality-feedback-loop.md)
- Skill boundaries: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)

## Ограничения

- Do not use this skill for FT package discovery or primary scope selection.
- Do not perform writer or reviewer domain work here when a separate backend session should own the stage.
- Do not solve a stuck runner by launching another runner against the same `cycle-state.yaml`; inspect `runner.lock.yaml` and use the recovery policy in `codex-sdk-orchestration-format.md`.
