---
name: ft-test-case-iteration
description: Orchestrate the session-based writer/reviewer cycle for an already confirmed FT package and scope. Use the backend dispatcher with verified Codex exec by default; keep SDK as an explicit fallback. Do not perform writer or reviewer work inside the same session.
---

# FT Test Case Iteration

## Lean production orchestration

Для eligible bounded scope следуй `lean-production-workflow.md`: оставайся в одной
пользовательской задаче, автоматически переходи от accepted source receipt к
compile, writer, независимому reviewer и promotion. Не создавай отдельные session
logs, decision logs, saved dispatcher config или schema canary в успешном run.
Измеряй `full_user_wall_ms`, а не только сумму model durations. Один local
deterministic repair допустим внутри общего hard budget; архитектурная отладка и
широкие regression suites не входят в production critical path.

This skill is a thin orchestrator for the session-based writer/reviewer cycle.

Для фактического baseline всего пользовательского turn используй
`full-process-timing-observation.md`. Его observation-only профиль не применяет
target/hard stop или application-level model timeout и не меняет quality gates. Не смешивай
его с time budget профиля `lean-production`: сначала измеряется текущий процесс,
а цели обсуждаются только после получения данных.
Если пользователь указал checked-in benchmark config, запускай observation через
`scripts/start_full_process_observation.py`; не выводи `ft_slug`, FT-каталог или
имя recorder-а из названия документа.

Для явно указанного checked-in config с `schema_version = 2` используй узкий
маршрут `production.checked_in_observation` и один вызов
`scripts/start_full_process_observation.py --execute`. Root-agent не должен
отдельно загружать или запускать `ft-source-locator` и `ft-scope-analyzer`: exact
source registry, совместимость `role/manifest_binding`, hashes, bounded context,
approved clarifications и dependency preflight проверяет executor до первого
model call. После этих gates executor вызывает канонический full-production
wrapper не более одного раза, без retry или fallback. Config schema v1 остаётся
start-only и не подпадает под это исключение.

Use it only when:

- the FT package is already selected;
- a concrete external `scope_slug` is confirmed;
- `scope-contract.md`, `scope-coverage-gaps.md` and the required source handoff artifacts already exist;
- the intended canonical test-case path is known.

Для обычного session/full-loop эти артефакты должны существовать заранее. Единственное
исключение — validated checked-in schema-v2 config: он заранее фиксирует FT,
scope, source-only context template и output targets, а executor создаёт
source/scope handoff fail-closed. Во всех остальных случаях при недостающих
inputs вернись к `ft-source-locator` или `ft-scope-analyzer`.

## Core Rule

Do not run writer and reviewer work inside this same chat/session.

## Conditional incremental-update mode

When the task updates a signed-off suite between two FT versions, select
`mode: incremental-update` and load scenario `iteration.incremental_update`.
Use `scripts/run_incremental_update_iteration.py`; the canonical workflow,
artifact set, byte-identical reuse rule and publication guards are defined in
[incremental-update-iteration.md](../../references/agent/incremental-update-iteration.md).
Do not load that reference for a normal `full_loop`, and do not send the entire
old suite to the writer. Missing XHTML for the new version stops only that
scope as `blocked-input`.

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
   - `source-row-inventory.md` for row-level/table-heavy scopes; compiler v3
     requires its typed path/locator/bounded-text/context/codes registry for all
     rows, including `in_scope = no`;
   - `mockup-visual-inventory.md` for UI scopes with mockups.
   - for every new production/promotion-capable cycle: `source-assertions.json`, accepted `source-assertion-review.json`, and `prepared_compiler_contract_version: 3`.
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
Semantic-design shards containing only authoritative `context`/`excluded` rows
must be materialized deterministically with zero model attempts; any included row
or executable semantic signal keeps the shard on the model route or fails closed.

Before a prepared live writer, require observable-oracle preflight. For a terminal cycle with a complete unsigned draft and only allowlisted deterministic oracle findings, a new immutable cycle may run one hash-bound targeted repair over the named TCs. Treat prior draft/findings only as unsigned repair input; migrate only per-TC `package_id`, prove non-target semantic preservation, run full-set gates, then one fresh reviewer. Never retry/resume the old cycle or treat its draft as requirement evidence.

For compiler contract v3, compile only after the independent source assertion
receipt is accepted. The compiler and runner must verify manifest/source/mockup
freshness, source-row -> assertion -> ATOM -> OBL integrity and coverage accounting
before any model call. Raw-source semantics are reviewed only in that source phase.
The prepared TC reviewer uses the digest-bound accepted typed-assertion projection,
exact compiled OBL semantics and source-first reviewer contract v4: it returns one
compact verdict for every bound obligation plus one review for every routed
cross-cutting dimension. A
source-model or dimension finding cannot enter targeted repair and routes to a
new source/model cycle. A marker without a valid full receipt is not a
source-first package.

Compile with default `output_mode = release`. Use the explicit
`draft-with-blocking-gaps` route only when compiler v3 has an accepted source
receipt, at least one testable obligation and only narrow primary blocking gaps;
all other guards remain fail-closed. An accepted reviewer result for that route
ends `blocked-input`/`blocked-source-gaps` as an unsigned draft: do not create a
promotion seed, canonical test cases or a signed-off snapshot. After
clarification, rematerialize the source model and start a fresh immutable release
cycle; do not resume the blocked draft.

Testable assertions with `execution_readiness = dependency-blocked` stop
`release` with `source-execution-dependency-blocked`. Use explicit
`draft-with-blocking-gaps` only when the purpose is to execute the remaining
ready subset. Package v9 must carry the exact blocked assertion/source-row/
ATOM/OBL/GAP/risk/rationale registry; blocked and ready obligations must not
share a TC or design-plan group. The runner excludes blocked OBLs, runs at most
the ready subset, and after an accepted review ends unsigned
`blocked-input/blocked-execution-dependencies` without promotion seed,
publication or snapshot. If nothing ready remains, stop before writer/reviewer.

When the complete draft is source-correct and the sole blocker is a proven runner transport defect, a new immutable cycle may instead use reviewer rebind: bind the draft hash, migrate only per-TC `package_id`, prove all semantics unchanged, rerun every gate, and start one fresh reviewer with no writer LLM. Do not use it to bypass a real finding or promote automatically. Before either reviewer route, require package-metadata and exact structured `DICT-*` active-values gates.

8. Stop at `signed-off`, `round-cap-reached`, `blocked-input` or any non-runnable status. Do not manually advance semantic verdicts.

## Gates

- Do not start semantic review when structure preflight has blocking findings.
- Do not start final format review before semantic review passes.
- Do not start a third semantic review round. After round 2, unresolved semantic findings mean `round-cap-reached`.
- Do not route `round-cap-reached` or `blocked-input` to `ft-ui-automation-prep`.
- Do not mark `signed-off` unless `cycle-state.yaml`, latest reviewer outputs and snapshots prove semantic closure and final format/regression closure.
- Do not promote compiler v2/legacy packages. Production promotion requires a validated source-first package, strict runtime/quality gates and an accepted hash-bound reviewer receipt; post-hoc execution follows [controlled promotion](../../references/agent/controlled-promotion-format.md). The default one-command path builds the full basis and deterministic signed-off state projections from the runner seed plus real accepted semantic artifacts; it blocks rather than requiring or fabricating manual promotion inputs.
- Treat `PROMO-BLOCKING-SOURCE-GAPS` as a content guard: no accepted receipt,
  alias or copied status may promote an obligation set that still contains a
  blocking gap.
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
- Source-first assertion contract: [../../references/agent/source-assertions-format.md](../../references/agent/source-assertions-format.md)
- Prepared compiler modes: [../../references/agent/prepared-compiler-input-contract.md](../../references/agent/prepared-compiler-input-contract.md)
- Lean production workflow: [../../references/agent/lean-production-workflow.md](../../references/agent/lean-production-workflow.md)
- Full-process timing observation: [../../references/agent/full-process-timing-observation.md](../../references/agent/full-process-timing-observation.md)
- Incremental FT-version update: [../../references/agent/incremental-update-iteration.md](../../references/agent/incremental-update-iteration.md)
- Durable overnight queue: [../../references/agent/overnight-controller-format.md](../../references/agent/overnight-controller-format.md)
- Skill boundaries: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)

## Ограничения

- Do not use this skill for FT package discovery or primary scope selection.
- Do not perform writer or reviewer domain work here when a separate backend session should own the stage.
- Do not solve a stuck runner by launching another runner against the same `cycle-state.yaml`; inspect `runner.lock.yaml` and use the recovery policy in `codex-sdk-orchestration-format.md`.
