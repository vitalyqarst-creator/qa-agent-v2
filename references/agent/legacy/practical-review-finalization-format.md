# Practical Review Finalization And Export

This conditional reference applies only after an independent practical
`matrix_review` or `tc_review` task has returned. It is controller-facing: a
reviewer creates only review evidence and must not update controller state.

## Controller ownership guard

The launch receipt produced by `practical_review_preflight.py` records SHA-256
hashes and a byte-for-byte controller snapshot for the package summary and each
active `workflow-state.yaml`. Before the controller changes aliases, summary or
workflow state, it must verify the reviewer output:

```text
python scripts/practical_review_finalization_guard.py --repo-root . --ft-package-root <FT package root> --summary <practical-stage-summary.md> --scope-id <two-digit scope id> --review-mode <matrix_review|tc_review> --launch-receipt <review-launch-preflight.json> --dispatch-receipt <review-dispatch.json> --review-artifact <review artifact> --independence-artifact <review-independence.md> --output <review-finalization.json>
```

The guard requires all of the following:

- original launch receipt has `allowed: true` and matches the selected scope/mode;
- current branch **and** exact `HEAD` still equal `code_branch` and
  `code_commit` recorded in that launch receipt; otherwise the verdict is
  stale and the controller must rematerialize and launch a fresh review;
- controller-owned summary and active workflow files have not changed during
  review;
- review artifact has a canonical verdict for the selected mode;
- controller-owned dispatch receipt binds the allowed launch receipt to the
  actual separate Codex session/thread ID and `reviewer_execution_surface`
  equal to `codex-thread`;
- dispatch receipt schema v3 records the running controller's
  `CODEX_THREAD_ID`, which must equal `controller_task_or_session` in every
  active workflow and must differ from the reviewer ID. A reviewer must never
  dispatch a follow-up reviewer; it returns its verdict only to that controller;
- reviewer-owned evidence confirms only its read-only/separate-session facts
  and references the dispatch receipt. It must not invent or manually copy a
  task ID.

Only a packet with `allowed: true` may be followed by the controller's one
deterministic update of `workflow-state.yaml` and `practical-stage-summary.md`.
A blocked packet is a process-integrity failure. If a reviewer changed
controller-owned state, the controller may first inspect and explicitly restore
only that state from the launch snapshot:

```text
python scripts/restore_practical_review_controller_state.py --ft-package-root <FT package root> --summary <practical-stage-summary.md> --scope-id <two-digit scope id> --launch-receipt <review-launch-preflight.json> --restore --output <controller-recovery.json>
```

Then the controller creates a new launch preflight and a new independent review;
it must not silently accept the old reviewer verdict after an ownership
violation. The restore command never touches test cases, sources, matrices or
review findings.

The reviewer prompt must explicitly say that `workflow-state.yaml`,
`practical-stage-summary.md`, launch receipts and controller aliases are
read-only. If a task instruction conflicts with this rule, the reviewer stops
as `blocked-contract` and asks the controller for a corrected task prompt.

## Controller-owned reviewer dispatch receipt

`review-launch-preflight.json` is created before `create_thread` and cannot
know the new task ID. Create the reviewer task with a parking prompt: it does
not read sources or write artifacts until a controller follow-up authorizes
assessment. Immediately after `create_thread` returns its ID, the controller
writes:

```text
python scripts/practical_review_dispatch_receipt.py --launch-receipt <review-launch-preflight.json> --reviewer-session-id <returned separate Codex session id> --reviewer-execution-surface codex-thread --output <review-dispatch.json>
```

The dispatch command reads the controller identity from `CODEX_THREAD_ID` and
rechecks that it matches every selected workflow. Only a successful dispatch
receipt authorizes the controller to send the
operational reviewer prompt. The reviewer receives its path, verifies that it
is bound to the same allowed launch receipt, and records only
`reviewer_dispatch_receipt` in its independence artifact. This keeps task
identity controller-owned and makes an accidental controller/reviewer ID swap
a deterministic finalization failure.

## Post-finalization next-stage gate

After the one controller-owned state/summary update, refresh the summary's
validator evidence and run this gate **before** a matrix-accepted scope is
routed to canonical TC writing (or a TC-accepted scope is routed onward):

```text
python scripts/practical_controller_post_finalization_gate.py --repo-root . --ft-package-root <FT package root> --summary <practical-stage-summary.md> --scope-id <two-digit scope id> --launch-receipt <review-launch-preflight.json> --review-finalization <review-finalization.json> --output <controller-post-finalization.json> --link-output
```

Only `allowed: true` may set `writer allowed`. The packet blocks when a selected
scope/package validator error remains, the version-gated commit changed during
review, or a `GAP-*` marked closed by repair still appears as active debt in
`source-parity-check.md`. In the latter two cases rematerialize from the current
state; do not silently carry the old review verdict forward. Link the packet as
`latest_artifacts.controller_post_finalization_gate`. `--link-output` выполняет
только это controller-owned обновление alias после разрешённого gate; не
заменяй его ручным редактированием workflow-state.

The launch, finalization and post-finalization packets also bind the SHA-256 of
the review subject. If a previously accepted matrix no longer matches that
binding after canonical TCs exist, preserve the TC file and use the exact
matrix-invalidation recovery in `practical-test-case-route-v0.8.md`: one fresh
independent matrix review, then independent TC review. A normal writer route is
not a valid recovery for this condition.

For this recovery, an accepted matrix finalization packet has
`recovery_context: matrix-revalidation-after-canonical-tcs` and
`next_controller_transition: tc-review required`. The controller waits for the
separate reviewer to finish, then finalizes controller-owned state and summary
before reporting the stage as complete.

## Recovery of a preserved canonical suite

Перед запуском отдельного matrix reviewer для R2 контроллер выполняет
read-only preflight сохранённого набора:

```text
python scripts/practical_matrix_revalidation_readiness.py --ft-package-root <FT package root> --scope-id <two-digit scope id>
```

Этот preflight проверяет только устойчивые prerequisites уже созданного
canonical набора: перенос обязательных строк источника в handoff и проходящий
split `writer-quality-gate.md`. Он намеренно не трактует временные ошибки
matrix-revalidation как дефект набора. Если preflight заблокирован, matrix
review не запускается: сначала требуется отдельная разрешённая writer-repair
задача.

После `matrix-accepted` R2 контроллер не редактирует routing вручную. Он
материализует единственный переход к TC-review:

```text
python scripts/practical_matrix_revalidation_transition.py --repo-root . --ft-package-root <FT package root> --summary <practical-stage-summary.md> --scope-id <two-digit scope id> --review-finalization <controller-finalization-r2.json> --output <matrix-revalidation-transition.json> --apply
```

Команда проверяет exact R2 finalization, pinned code version, hash текущей
матрицы и существование `prompt.tc-to-reviewer.md`; затем сохраняет canonical
TC без изменений, переводит workflow в `tc_review`, обновляет summary и
сбрасывает устаревший alias post-finalization gate. Пока новый gate ещё не
создан, validator использует hash-bound `matrix_revalidation_finalization` как
временное controller-owned доказательство принятой матрицы. Следующим действием
обязательно идёт fresh TC-review preflight и отдельная Codex-сессия reviewer.

`tc-review required` is an execution obligation, not a handoff result. The
controller must first pass a fresh TC-review preflight, create and dispatch a
separate top-level reviewer session, wait for its verdict, and finalize it. A
terminal report saying only that a TC-review prompt or handoff was prepared is
invalid. If the fresh preflight is blocked, report that blocked result and its
evidence instead of claiming the requested review was completed.

## Portable accepted baseline

When accepted package artifacts are ignored by Git, ordinary `git commit` does
not preserve them. The controller must either explicitly stage exactly those
files with `git add -f` or create a portable evidence bundle:

```text
python scripts/export_practical_baseline.py --ft-package-root <FT package root> --scope-id <two-digit scope id> --summary <practical-stage-summary.md> --output <destination>.zip
```

The exporter permits only a scope that records accepted independent TC review.
The ZIP contains a SHA-256 manifest plus exactly the canonical TC file, final
findings, independence receipt, active workflow state and practical summary.
It never modifies or stages package artifacts.
