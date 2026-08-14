# Practical Test Case Route v0.8

This is the default route for ordinary FT test-case writing.

The goal is to produce useful, source-bound manual test cases quickly, without
benchmark, sharding, semantic bridge, immutable runner, source assertion receipt
loops or multi-session repair cycles.

Compared with v0.7, v0.8 keeps the lightweight practical route but makes three
quality controls non-optional:

- when DOCX and PDF are both present, `source-parity-check.md` is created before
  writer handoff, not discovered late by reviewer;
- `test-design-matrix.md` is reviewed as writer output, not trusted as source;
- canonical `TC-*` writing is gated by accepted matrix review, so coverage defects
  are caught before the expensive prose-writing step;
- independent sign-off requires a separate reviewer top-level Codex session by
  default;
- practical-route outputs must fail closed when heavy-route artifacts appear
  without an explicit user-selected route.

Use heavier routes only when the user explicitly asks for them by name, for
example benchmark, sharding, semantic bridge, source-qualified immutable
`ft-agent run`, incremental update, or UI automation preparation.

For a normal request such as "write test cases", the agent must not propose or
start those heavier routes as alternatives. If a prompt is ambiguous, choose
this practical route and record any remaining uncertainty as TC status, BA
question, or UI-calibration candidate.

## Scope-selection boundary

Before an external scope is selected, `ft-scope-analyzer` creates only
`scope-options.md` and a compact `scope-selection-prompts.md`; its status is
`awaiting-user-scope-selection`, not `blocked-input`. Do not create
scope-local artifacts or BA questions until selection, except a contradiction
that prevents decomposition. The prompt contains only the FT package path and
the selected `scope_slug`.

## Macro-stage execution

Default user-facing execution for "write test cases for this scope" is one
macro-stage: continue from the current valid handoff until one of these terminal
conditions occurs:

- canonical test cases are accepted by independent TC review and published as an
  accepted baseline;
- one bounded matrix repair plus one matrix re-review was performed and the
  matrix is still not accepted; apply the practical round-cap policy below:
  write status-marked TC for clear source obligations and block only source
  contradictions or unrepresentable obligations;
- one bounded TC revision was performed, its result was accepted by a final
  independent TC review, and any remaining execution uncertainty is represented
  by explicit `candidate-ui-calibration`, `blocked-observability`,
  `needs-test-data` or `needs-future-clarification` statuses;
- source/support/mockup input is contradictory or missing enough to require a BA
  answer before the obligation can be represented;
- a real tool/runtime failure prevents safe continuation.

Do not stop for user confirmation after internal practical handoffs when the next
prompt is already materialized and no external decision is needed. In particular,
continue automatically across:

- matrix-only writer handoff -> independent matrix review;
- `matrix-changes-required` -> one bounded matrix repair -> one independent
  matrix re-review; if the matrix is still not `matrix-accepted`, apply the
  documented round-cap decision per scope: write status-marked TC only when
  `source_contradiction: no` and `tc_with_status_decision: write-with-statuses`;
  otherwise stop before TC writing for that scope;
- `matrix-accepted` -> canonical TC writing;
- TC writer handoff -> independent TC review;
- `tc-changes-required` -> one bounded TC revision -> one final independent TC
  review; if that review accepts the suite, release the status-marked baseline.
  If it returns `tc-changes-required`, do not start another automatic revision:
  stop and report the remaining findings or external blocker.

If the next stage for a signed-off scope is `ft-ui-automation-prep`, first check
whether the FT package contains package-local UI access inputs:
`work/ui-automation-prep/UI-AGENT-NOTES.md`, runtime URL/entrypoint, login method
and a test account or storage-state. If these inputs are absent, do not create
an empty `automation-ready` file, empty UI evidence, or `ui-run-not-started.log`
just to mark the stage attempted. Record `ui-prep blocked-input` in the current
workflow/summary and continue with the next productive practical-route scope
when one exists. UI-prep without runtime/access input is a known external input
blocker, not a useful stage.

Default review budget per scope is capped at:

- one independent matrix review, plus one matrix re-review only after a bounded
  matrix repair;
- one independent TC review;
- one bounded writer repair/revision only after `tc-changes-required`;
- one final independent TC review after that bounded revision.

Do not start an extra matrix review beyond the single repair re-review, a third
TC review, final-format review, semantic regression or another repair loop unless
a validator contract failure prevents publication or the user explicitly requests
another review round. A reviewer finding is not by itself permission to loop
indefinitely: if the final independent review after the bounded revision still
finds defects, report them rather than applying another automatic repair.

## Неизменность practical-stage

Обычный scope-stage владеет только артефактами выбранного FT package и scope.
Он не меняет `AGENTS.md`, `skills/`, `references/`, `scripts/` или `tests/` и
не выполняет commit/push agent-layer, чтобы снять собственный validator или
dispatch blocker. Даже технически правдоподобный дефект agent-layer не является
разрешением исправлять код «по пути».

Если validator, preflight или dispatch выявил такой дефект, зафиксируй короткую
диагностику в текущем `practical-stage-summary.md`, переведи workflow в
`blocked-input` с причиной `agent-layer`, и останови scope-stage до отдельной,
явно разрешённой архитектурной задачи. Отдельная задача исправляет и проверяет
только agent-layer, публикует его отдельно, а затем новый scope-stage начинается
с чистого worktree и заново фиксирует version gate. Нельзя менять version gate
текущего handoff на commit, созданный этим же scope-stage.

## Root consistency gate

At the start of every practical stage and in every `practical-stage-summary.md`,
record the roots used for code, FT data and artifact writes:

| field | value |
| --- | --- |
| code_root | `<version-gated repository/worktree root>` |
| execution_working_directory | `<actual task working directory; must equal code_root>` |
| ft_package_root | `<FT package root used as input>` |
| artifact_write_root | `<root where this stage writes artifacts>` |
| root_split_allowed | `yes/no` |
| root_split_authority | `<user/controller approval, or not-applicable>` |

Also record the version gate:

| field | value |
| --- | --- |
| code_branch | `<branch name, or detached HEAD>` |
| code_commit | `<exact commit SHA>` |
| version_gate_status | `passed / blocked-input` |

Для `ft-source-locator` также запиши `contract_version` в `code_version_gate`
и `Версия контракта source locator` в `source-selection.md`:
`source-locator-contract-v1`. Если менялась только другая фаза agent-layer,
эта явная версия сохраняет source selection пригодным; для scope/writer/reviewer
такое исключение не применяется.

Detached HEAD is acceptable only when the exact expected commit matches and the
named branch cannot be checked out because it is already occupied by another
worktree. In that case, record the branch occupancy reason and continue only
against the exact expected commit. Detached HEAD without an exact expected commit
match is `blocked-input`.

The task must run in `code_root`. If its current Codex worktree differs, the
controller must hand off or recreate the task in `code_root` before stage
preflight. Switching into an external repository during a stage is not an
approved root arrangement, even when the external checkout has the same branch.
Before it dispatches a separate reviewer, the controller records its actual
`CODEX_THREAD_ID` as `controller_task_or_session` in every active workflow;
missing runtime identity is `blocked-controller-session-provenance`.

## Reviewer launch preflight

Before the controller creates **any** separate Codex reviewer task for either
`matrix_review` or `tc_review`, it must run the deterministic preflight from
the exact version-gated `code_root`:

```text
python scripts/practical_review_preflight.py --repo-root . --ft-package-root <FT package root> --summary <practical-stage-summary.md> --scope-id <two-digit scope id> --review-mode <matrix_review|tc_review> --output <FT package root>/work/practical/<scope-slug>/review-launch-preflight.json
```

Сначала выполни тот же preflight с `--check-only`. Если он вернул
`allowed: true`, сразу зафиксируй в `practical-stage-summary.md`
`review_launch_preflight_status = check-only-allowed`,
`review_launch_preflight_receipt = not-applicable` и короткое
`review_launch_preflight_evidence` с командой и результатом. Не записывай
выполненный check-only как `not-run` и не выдавай его за сохранённый receipt.
Только после этого один раз материализуй launch receipt через `--output`; между
этими двумя командами не меняй controller-owned state. Только JSON-результат с
`allowed: true` разрешает `create_thread`. Preflight
checks the real working directory, Git branch/commit and tracked state against
the summary's Code Version Gate, keeps code/data/artifact roots consistent,
checks requested scope routing, and reruns the package validator. Errors of the
selected scope, its current stage summary, or shared package inputs block the
launch. Findings owned by another scope or its stale practical summary are
recorded as external debt and do not block the selected review. A stale code
version, a changed checkout, a current-scope validator error, or a malformed
summary is `blocked-input`; do not create a reviewer task and do not work around
the failure by switching directories inside the task.

The controller passes the receipt path to the reviewer. Before reading the
matrix or test cases, the separate reviewer reruns the same command with
`--verify-receipt <receipt path>`. If the receipt no longer matches the current
branch, commit, roots, summary digest or scope/mode, it must stop without
creating review artifacts. This is required because another active Codex task
can otherwise switch a shared checkout between controller and reviewer turns.

The launch receipt hash-binds controller-owned workflow state. Before a
controller updates aliases, workflow or summary after review, run
`practical_review_finalization_guard.py`; its full contract is in
[practical-review-finalization-format.md](./practical-review-finalization-format.md).
Before routing that accepted scope to writer, the controller must pass the
post-finalization gate from the same reference; an old verdict never advances a
changed commit, stale current-scope validation, or unreconciled closed `GAP-*`.

The receipt also hash-binds the review subject: `test-design-matrix.md` for
`matrix_review` and canonical test cases for `tc_review`. Do not edit an
accepted matrix before TC writing. Any edit, including identifier repair,
requires a fresh independent matrix review and controller finalization. Once
canonical TCs are created, the only next practical transition is
`ready-for-review` to `ft-test-case-reviewer` in `tc_review` mode; the validator
blocks a writer-to-writer route or a stale practical summary.

### Recovery after matrix invalidation

If the matrix hash no longer matches its accepted controller gate after
canonical TCs have already been written, preserve those TCs and run one fresh
independent `matrix_review` before TC review. This is the only exception to the
normal post-writer TC-review route. The controller must set exactly:

- `matrix_review_status: invalidated`;
- `matrix_revalidation_reason: reviewed-matrix-hash-mismatch`;
- `current_round: 2`;
- `stage_status: ready-for-review`, `next_skill: ft-test-case-reviewer` and
  `review_mode: matrix_review`.

До dispatch matrix reviewer контроллер запускает
`practical_matrix_revalidation_readiness.py`. Если устойчивые prerequisites
сохранённого canonical набора (source-row handoff и split Writer Quality Gate)
не проходят, R2 review не запускается; это отдельный writer-quality blocker, а
не повод повторять review или ослаблять validator.

The validator permits this recovery only while the controller gate proves the
matrix mismatch. Do not rewrite, delete or relabel canonical TCs in this stage.
After the new matrix verdict is accepted and finalized, set
`matrix_review_status: matrix-accepted` and route the preserved canonical suite
to independent `tc_review` through
`practical_matrix_revalidation_transition.py`; the finalization packet must
state `next_controller_transition: tc-review required`. Do not start another
writer pass merely to traverse the route, and do not manually retain a stale
matrix-review prompt or old R1 post-finalization alias.

Create the separate reviewer task with a parking prompt: until it receives the
controller dispatch message, it must not read review inputs or create artifacts.
Immediately after `create_thread` returns the new session ID, the controller
creates `review-dispatch.json` with
`scripts/practical_review_dispatch_receipt.py`. Pass the dispatch receipt path
to the reviewer only after the dispatch command succeeds. The command rechecks
the frozen launch receipt against current controller state. If it is blocked,
do not send the operational reviewer prompt and do not retry dispatch, replace
the receipt or create another reviewer task in the same scope-stage. Record one
`blocked-input` reason and hand the diagnosis to the next explicitly started
controller stage. The reviewer records the dispatch receipt in
`review-independence.md`; it does not manually provide a task ID. This
controller-owned receipt is required by `practical_review_finalization_guard.py`.

After dispatch, the controller keeps the macro-stage open and waits for the
separate reviewer through bounded `wait_threads` calls (at most 60 seconds per
call). When the reviewer completes, the controller runs the finalization guard,
performs its one deterministic state/summary update, and only then reports the
stage result or starts the next permitted transition. It must not return a
terminal stage response while a dispatched reviewer is still active.

When the user requested independent `tc_review`, an active
`prompt.tc-to-reviewer.md`, `tc-review allowed` or a prepared handoff is not a
completed stage. The controller must execute the fresh TC-review preflight,
dispatch a separate top-level reviewer session, wait for the verdict and run
its finalization. If that fresh preflight is blocked, return the blocked result
with its evidence; never replace it with a terminal message that merely offers
the next prompt.

Blocked check-only, launch or dispatch attempts are diagnostics, not durable
handoff artifacts: do not persist a blocked `review-launch-preflight*.json`,
`review-dispatch*.json` or controller snapshot. A successful review attempt has
exactly one active launch receipt and one active dispatch receipt for its
review mode and round; historical accepted receipts remain read-only evidence.

For the first matrix review, create/update the practical summary before launch
and use `next_stage_transition = matrix-review allowed` or
`matrix-review conditional`. Its active scope-transition row must state
`matrix-created-pending-review`; this makes the preflight equally strict for
the matrix gate and the later TC gate.

`ft_package_root` and `artifact_write_root` should normally be inside
`code_root`. If the FT package is outside the version-gated worktree, this is a
split-root run. Split-root is allowed only when the user/controller explicitly
approved that exact arrangement. Otherwise stop as `blocked-input`; do not
silently read requirements from one checkout and write artifacts after checking a
different checkout.

Nested FT packages are valid. For example, `fts/Partners/Partners-v1` is the FT
package root when that directory contains the selected package materials. In such
cases all practical artifacts, `workflow-state.yaml`, handoffs, summaries and
test cases must stay under `fts/Partners/Partners-v1`. Do not create
`fts/Partners/work/stage-handoffs/*` or other parent/domain-level workflow files
as a workaround for package discovery. If a validator or prompt cannot recognize
the nested package root, classify it as an agent-layer/root-detection defect and
fix the rule/tooling; do not mask the problem by adding a fake package index
outside `ft_package_root`.

Before matrix writing, matrix review or canonical TC writing, perform a physical
source package completeness preflight for the declared `ft_package_root`.
`AGENT-NOTES.md`, at least one main `source/*.docx`, mandatory
`source/*.xhtml`, and PDF cross-check `source/*.pdf` must exist in the package.
If any are missing, set `next_stage_transition = writer blocked`, classify the
validator/preflight issue as `next-stage-blocker`, and restore or relink the
source package before continuing. Do not treat this as a reason to create
handoff artifacts above `ft_package_root`.

When split-root is approved, the summary and final report must state it plainly
and must name both roots. The stage must not claim that version gate covers data
artifacts that live outside the version-gated root.

  After every matrix review stage, the acting agent must stop the internal chain
long enough to produce a user-facing `practical-stage-summary.md` and include
the same facts in the final/user-visible report before sending the next prompt.
This is not a permission gate when no external decision is needed; it is a
mandatory transparency gate.

For a single-scope stage, place the summary in
`fts/<ft-slug>/work/practical/<scope-slug>/practical-stage-summary.md`.
For a multi-scope package stage, place the package-level summary in
`fts/<ft-slug>/work/practical-stage-summary.md`.

For a multi-scope practical stage, the scope ids explicitly named by the
controller are the `active_scope_ids` allowlist. Do not modify artifacts of an
outside scope merely to make a package-level validator green: record and
classify that finding as external to the current stage instead.

Create the file from
[practical-stage-summary-template.md](./practical-stage-summary-template.md).
Canonical path: `references/agent/practical-stage-summary-template.md`.
Machine enum fields must contain only enum values; explanatory prose belongs in
`next_safe_step`, scope `reason` or notes. Do not improvise new enum values.

The summary must be linked from `workflow-state.yaml` for every affected scope
through `latest_artifacts.practical_stage_summary` or an equivalent package-level
state/index pointer. A summary that is not linked is not a safe handoff for the
next stage.

The summary must list:

- accepted scopes that may proceed to canonical TC writing;
- blocked / `round-cap-reached` scopes;
- the concrete reason each scope is blocked or capped;
- whether TC can still be written with explicit statuses;
- the next safe step for each scope;
- раздел `Действия текущего этапа`, содержащий только действия текущего этапа;
- раздел `Контекст предыдущих этапов` для более ранней истории, объясняющей
  текущее состояние;
- `next_stage_transition`: exactly one of `matrix-review allowed`,
  `matrix-review conditional`, `matrix-review blocked`, `writer allowed`,
  `writer conditional`, `writer blocked`, `tc-review allowed`,
  `tc-review conditional`, `tc-review blocked`, or `not-applicable`.

If a validator was run, add these fields:

For FT-package practical stages, the canonical validator verdict is the
package-root run:
`python scripts/validate_agent_artifacts.py --root <FT package root> --json`.
Repo-root validation may be run only as supplementary validation. Do not merge
package-root and repo-root counts into one verdict. The stage summary must show
the package-root verdict separately from any repo-root finding; a repo-root-only
path-resolution failure is a `validator_path_resolution` / agent-layer defect,
not proof that the current scope test cases are bad.

| field | value |
| --- | --- |
| validator_primary_command | `python scripts/validate_agent_artifacts.py --root <FT package root> --json` |
| validator_primary_root | `<absolute FT package root>` |
| validator_supplementary_command | `<repo-root validator command or not-run>` |
| validator_findings_breakdown | `tc_quality=<n>; process_artifact=<n>; validator_path_resolution=<n>; unrelated_repo=<n>` |
| validator_raw_errors_count | `<integer: все ошибки package-root validator>` |
| validator_errors_count | `<integer: routing count без practical-stage-summary self-check>` |
| validator_summary_self_check_errors_count | `<integer>` |
| validator_summary_self_check_errors_evidence | `<finding id и путь или not-applicable>` |
| validator_scope_errors_count | `<integer for active_scope_ids, or not-applicable>` |
| validator_scope_errors_evidence | `<finding ids and paths, or not-applicable>` |
| validator_external_errors_count | `<integer for other scopes, or not-applicable>` |
| validator_external_errors_evidence | `<finding ids and paths, or not-applicable>` |
| validator_errors_classification | `none / next-stage-blocker / pre-existing-unrelated / validator-false-positive / mixed` |
| validator_errors_evidence | `<paths/finding ids or not-applicable>` |
| validator_warnings_count | `<integer>` |
| validator_warnings_classification | `none / blocking-for-scope / expected-pre-writer / nonblocking-info / mixed` |
| validator_warnings_evidence | `<paths/finding ids or not-applicable>` |
| validator_info_count | `<integer>` |
| validator_info_evidence | `<paths/finding ids or not-applicable>` |
| per_scope_next_stage_transitions | `yes / not-applicable` |
| production_tc_clean | `yes / no / mixed / not-applicable` |
| git_persistence | `tracked / ignored-by-git / mixed / not-applicable` |
| source_restore_provenance | `<source path/checkpoint used to restore package files, or not-applicable>` |
| source_restore_sha256 | `<SHA-256 bindings for restored files, or not-applicable>` |
| review_launch_preflight_status | `not-run / allowed / blocked / not-applicable` |
| review_launch_preflight_receipt | `<FT-relative review-launch-preflight-rN.json or not-applicable>` |

`validator_raw_errors_count` — это полное число ошибок JSON-вывода primary
validator. `validator_errors_count` — routing count, в который не входят
технические `practical-stage-summary` self-check: иначе summary создавал бы
циклическую проверку самого себя. Полный count обязан равняться
`validator_errors_count + validator_summary_self_check_errors_count`; evidence
исключенного слоя обязательно указывается отдельно.

When `validator_errors_count > 0`, the summary must not say unconditional
`writer allowed` or `tc-review allowed`. It must classify the errors and use a
conditional/blocked transition unless every error is explicitly proven
irrelevant or a validator false positive.

For `pre-existing-unrelated` or `mixed`, the summary also records the exact
partition: counts for active and external scopes, plus every finding id and its
path. The two counts must add up to `validator_errors_count`; an unverified
claim that errors belong to another scope does not authorize the next stage.

When `validator_warnings_count > 0`, classify warnings separately from errors:

- `blocking-for-scope`: blocks only the affected scope(s);
- `expected-pre-writer`: expected because TC artifacts do not exist yet, for
  example oracle-candidate obligations before writer;
- `nonblocking-info`: does not affect the next practical stage;
- `mixed`: more than one category is present.

A package-level conditional state must include per-scope transitions: which
scopes are `writer allowed`, `writer conditional`, `writer blocked`,
`tc-review allowed`, `tc-review conditional`, or `tc-review blocked`, and why.
Do not let a scope-local warning block unrelated accepted scopes. Do not write
package-level `writer allowed` or `tc-review allowed` when warnings are
`blocking-for-scope` or `mixed`.

`tc-review allowed` / `tc-review conditional` require clean production TC files:
`production_tc_clean = yes` for reviewed scopes. Findings
`test-case-split-artifact-duplicated-sections` and
`internal-diagnostic-section-in-production-testcases` are TC-review blockers;
move split-design sections to `work/test-design/<scope>/` before review.

When validator errors mention unresolved source/package artifacts, summary must
distinguish the cause explicitly:

- `physical-source-missing`: the files are absent under `ft_package_root`;
- `workflow-link-stale`: files exist, but `required_inputs` /
  `latest_artifacts` point to stale or wrong paths;
- `validator-root-selection-defect`: files and links are correct, but the
  validator resolved the wrong package root;
- `mixed`: more than one of the above is true.

When reporting validator output, classify every warning/error into one of these
groups before deciding the next-stage transition:

- `tc_quality`: production test-case content is wrong, non-executable,
  non-atomic, mistraced, language-invalid or otherwise not review-ready;
- `process_artifact`: handoff, summary, workflow, matrix, review receipt,
  writer gate or other practical-route artifact is incomplete or stale;
- `validator_path_resolution`: artifacts exist and links are correct, but the
  validator resolved a wrong package/root/path;
- `unrelated_repo`: finding belongs to another scope/package or old artifact and
  does not affect the current stage.

Only `tc_quality` and current-scope `process_artifact` findings may block the
current scope by default. `validator_path_resolution` must be fixed in tooling
or policy; `unrelated_repo` must be reported separately and must not be used as a
reason to loop on the current TC content.

Only `workflow-link-stale` may be repaired by editing links. Physical missing
source files must be restored. Root-selection defects must be fixed in the
agent-layer validator/policy, not by writing new parent-level handoff artifacts.
When files are restored or copied from another checkout, summary must record
`source_restore_provenance` and SHA-256 for the restored package files. Without
that provenance, the next stage cannot audit contamination risk.

After every repair, rerun the validator and refresh
`validator_errors_count`, `validator_warnings_count`, `validator_info_count` and
evidence ids from the latest report. Stale counts or stale finding ids block the
next practical stage.
Use
`python scripts/refresh_practical_stage_summary.py --root . --summary <path> --scope-id <two-digit scope id> --print-fields`
to compute the current validator counts/evidence, including info findings,
`git_persistence` and `source_row_counts` before updating the summary.
When the active transition prompt names a revision `rN` / `round-N`, the same
current revision must be recorded in `workflow-state.yaml.current_round` and in
the routing fields of a single-scope summary (`summary_stage` and
`next_safe_step` when they name a round). Older round numbers belong only in
`Prior state context`.
For a scope-level reviewer launch, use `practical_review_preflight.py` as the
decision gate. The package-wide validator remains mandatory audit evidence, but
only its preflight partition for the declared scope (`scope_relevant` and
`package_global`) can block that scope; errors owned by another scope must be
recorded as external rather than retriggering the current route.
  After any controller-owned `workflow-state.yaml` or summary update, refresh the
  summary's generated validator rows as the final write before handoff:

  ```text
  python scripts/refresh_practical_stage_summary.py --root . --summary <path> --scope-id <two-digit scope id> --write
  ```

  The command reaches a bounded fixed point for validator self-checks. Do not
  report preflight or stage completion with stale counts/evidence.

  After a preflight is written, record its status and receipt before reporting a
verdict. For an allowed TC review, `workflow-state.yaml` must link the receipt
from `latest_artifacts.review_launch_preflight`, mark the active round as
`allowed`, and route to reviewer dispatch; the package summary must expose the
same `review_launch_preflight_status` and receipt. A receipt file alone does
not advance the workflow.
If changed FT/package artifacts are ignored by git, set
`git_persistence = ignored-by-git` or `mixed` and state that ordinary
commit/push will not persist those files. The stage/final response must also
say that persistence requires `git add -f <paths>` or an export/bundle.

An accepted local review is not a published baseline when the reviewed canonical
TC files or the current review receipt are ignored by git. In that situation use
the human-facing state `accepted-local-publication-pending`, keep the next safe
step limited to explicit persistence (`git add -f` or an export/bundle), and do
not claim `released-*` until the declared artifacts are tracked. A later
publication step must not rewrite the accepted TC content merely to make git
accept it.

For ignored accepted artifacts, export with `export_practical_baseline.py`; the
exact contract is in
[practical-review-finalization-format.md](./practical-review-finalization-format.md).

`practical-stage-summary.md` must be linked from workflow-state files inside the
actual FT package root. An "equivalent package-level state/index pointer" is
allowed only inside that same `ft_package_root`; a parent folder such as
`fts/<domain>/work/stage-handoffs` is outside the package and is invalid unless
the user explicitly selected that parent folder as the FT package root.

For `round-cap-reached` after the bounded matrix repair/re-review, use this
practical default:

- if there is no source contradiction and the remaining issue is missing data,
  unknown UI reaction, unknown observability, or a future clarification that does
  not change the source obligation, write the TC baseline with explicit
  `candidate-ui-calibration`, `needs-test-data`, `blocked-observability` or
  `needs-future-clarification` statuses instead of blocking the whole scope;
- if source/support/mockup evidence contradicts itself, or the requirement
  cannot be represented without inventing a business rule, do not write TC for
  that obligation; keep the scope or obligation as `blocked-source` /
  `blocked-input` and state the exact contradictory source references.

The round-cap summary must be machine-checkable per scope: include
`source_contradiction: yes/no` and `tc_with_status_decision:
write-with-statuses / block-source-contradiction`. A generic "controller
decision required" is not a valid default unless the summary also names the
source contradiction or the exact status-based TC route.

After each internal handoff, run the relevant validator gate. If the gate fails
because practical-route infrastructure is inconsistent with this contract, stop
the current scope-stage with a concise `agent-layer` diagnostic. Repair the
smallest rule only in a separate, explicitly authorized agent-layer task; do
not create fake canonical TC files, fake review evidence, heavy-route artifacts
or placeholder outputs just to satisfy a stale validator.

For small scopes (rough guide: no more than 15 source rows and no more than 20
planned TC), use the fast path inside this same route:

- keep `test-design-matrix.md` and both independent reviews;
- skip optional diagnostics, XLSX companions, large ledgers and alias prompts
  unless a validator or reviewer finding proves they are required;
- write only the artifacts required for the next gate and final traceability;
- report timings and blockers in the final summary rather than stopping between
  gates.

## Route

1. `ft-source-locator`
   - Select the FT package.
   - Register the main DOCX, mandatory XHTML, PDF cross-check, support files,
     mockups and package `AGENT-NOTES.md`.
   - Create only the source-selection / scope-options artifacts needed for the
     next step.

2. `ft-scope-analyzer`
   - When resuming after a changed code gate, reread the active skill and this
     route before editing artifacts; record the loaded skill and the verified
     commit in `workflow-state.yaml.instruction_context`.
   - Before narrowing a scope, resolve the canonical source-selection artifact.
     First read `work/stage-handoffs/00-scope-selection/workflow-state.yaml`
     and its `latest_artifacts.source_selection`; then use
     `work/stage-handoffs/00-scope-selection/source-selection.md` as the
     fallback canonical path. If a usable selection resolves, reuse it: do not
     claim that source selection is missing, run `ft-source-locator`, or create
     a replacement selection. If neither path resolves, stop this stage as
     `blocked-input` and create only the transition to `ft-source-locator`.
   - Confirm one or more external scopes by FT section/subsection.
   - For each selected scope, create one compact `scope-brief.md` under
     `fts/<ft-slug>/work/practical/<scope-slug>/`. Все актуальные practical
     artifacts этого scope — brief, matrix, prompts, summary и review receipts —
     остаются в этой одной директории; не создавай параллельный каталог с
     повторным section id.
   - If the main FT has both DOCX and PDF, create `source-parity-check.md`
     before writer handoff and list it in the brief. Missing parity evidence is
     `blocked-input`; do not let writer or reviewer discover it late.
   - If the scope is based on table rows, actions, fields, document mappings or
     status rows, create a compact `source-row-inventory.md` before writer
     handoff. It may be lightweight, but it must name every in-scope row/value
     class the writer must cover or defer.
   - Apply document-global type constraints to every relevant table field before
     creating the inventory: text length, date format/range/calendar/timezone,
     numeric bounds and other explicit shared restrictions. Record each
     independent restriction as a source row and separate `ATOM-*` or
     `SO-NEG-*`; do not collapse it into a generic field row.
   - The brief must contain:
     - scope boundary and source references;
     - relevant FT text / table rows / PDF pages;
     - source parity conclusions and mandatory requirement IDs, when
       `source-parity-check.md` exists;
     - relevant mockups, Figma-index and support references. Before writing the
       brief, close inputs: include every support file whose scope heading,
       requirement code or table row matches the selected scope in the brief,
       `workflow-state.yaml` and downstream prompt. An unavailable optional
       Figma node remains a brief limitation, not a blocker;
     - dictionary values required by the scope;
     - open questions and assumptions;
     - candidate UI-calibration points.
   - `scope-brief.md` uses Russian visible prose and three execution tables; its
     linked source-row inventory path must resolve. In a row/table scope, each
     planned `Источник` names its exact `SRC-*` and the reciprocal `SRC-*` ↔
     `ATOM-*` mapping agrees with `source-row-inventory.md`. Map one `AS.*` / `SO-NEG-*` / `SO-REQ-*`
     to one `ATOM-*` or `GAP-*`, with actor, state, `SETUP-*`, evidence and status;
     `Кандидаты отрицательных проверок` содержит `Связанный ATOM`: один
     `SO-NEG-*` на одно поле/ATOM.
     name every target field of an auto-fill requirement exactly. Generic labels
      such as “basic attributes”, “listed attributes” or “all attributes” are not
      coverage and cannot be accepted. One auto-fill target field is one `ATOM-*`:
      split even when the source gives one common trigger. For one field, split
      auto-fill and manual input into separate `ATOM-*`; they use different
      actions and observability. Likewise, separate independent UI controls (for
      example, `Отмена` and closing a window) even when their expected result is
      the same. A source-backed fixed value list for one field may remain one
      parameterized check only when its trigger and expected result are identical.
     Repeat a `SETUP-*` only for atoms with the same required actor, object and
     initial state. Do not propagate a complete role inventory from a universal
     role check to an administrator-only operation. `ready` needs `FX-*` or source-backed
     `поле=значение` preparation, otherwise use `needs-test-data`.
   - Before writer handoff classify every uncertainty in the brief as exactly
     one of `ba-business-ambiguity`, `ui-calibration`,
     `external-scope-boundary` or `test-data-setup`. Only the first type may
     create a `CLR-*` BA question; do not ask BA to choose an UI screen,
     supply a fixture or describe a future/external FT section.
   - Use one exact `GAP-*` identifier across the brief, linked source-row
     inventory, parity artifact and any `CLR-*`; a renamed local copy is a
     handoff error, not a new gap.
   - A planned check with missing role/object/state/fixture preparation must
     be `needs-test-data` and name the same `SETUP-*` in both execution and
     dependency tables. `candidate-ui-calibration` cannot conceal a missing
     setup: a source anchor or a value such as "existing object" is not
     preparation evidence. A state-changing action by one actor that only
     prepares a later role-matrix check belongs in `SETUP-*`, not in that
     check's executor column. A navigation action with two named destinations becomes separate
     `ATOM-*` checks unless the brief records that the same start state,
     user action and observable result make one parameterized check valid.
   - Enforce atomization before handing the brief to the matrix writer. Split
     different object types or UI levels (for example, a parent partner and a
     requisite inside its card), and split role/state combinations with a
     different action or expected result. Values may remain in one `ATOM-*`
     only when the brief contains a compact Russian section
     `Обоснование параметризации ATOM` proving the same start screen, UI
     level, navigation path, user action, trigger and observable result for
     every value. Do not leave an aggregated `ATOM-*` with an instruction for
     the matrix writer to decide whether it should be split: make that decision
     in the scope-analysis stage. A requirement for every/remaining role needs a
     quantified, parameterized role check plus complete runtime role inventory and
     accounts as `needs-test-data`; this is test-data setup, not a BA question.
     The pre-writer validator requires one `ATOM-*` and one `Основной ожидаемый
     результат` per planned row. An execution row with several named actors is
     rejected unless `Обоснование параметризации ATOM` proves, for that ATOM,
     the same start screen, UI level, navigation path, action, trigger and
     expected result for every actor.
   - For bounded rematerialization, validate `scope-brief.md` directly and
     collect package findings owned by its practical and handoff directories.
     Green means no errors; do not filter only the handoff path or hide parser
     markers in Markdown. Apply one coherent repair patch; a second is only
     for a newly revealed validator finding.
   - Select the rematerialization mode automatically before writing. Use
     `metadata-only` only when the selected source/support inputs, confirmed
     scope boundary, source-row mapping, dictionary values and `GAP-*` set are
     unchanged and the task is limited to code-version, routing, links, summary
       or validator state. It may update only `workflow-state.yaml`, stage
       summary, decision log, active prompt and broken artifact links. When a
       current `source-selection.md` would otherwise retain stale code
       provenance, it may also apply its provenance-only update according to
       `references/agent/source-selection-format.md`; it must preserve the
       original creation record and source-locator session receipt. Otherwise
       use `bounded-content`. The user does not choose this mode in the prompt.
   - Keep temporary inspection scripts, renders, duplicate manifests and
     partial writes outside the final handoff. On a successful scope-analysis
     run, delete only temporary artifacts created by the current run. Files in
     `work/debug/` may remain only when a final artifact explicitly links them
     and states their purpose; never delete pre-existing user artifacts merely
     because they are unlinked.

3. `ft-test-case-writer` — design-matrix-only pass
   - Create or update exactly these required artifacts:
     - `test-design-matrix.md` in the practical scope folder;
     - `writer-self-check.md` or an equivalent compact writer check for the
       matrix;
     - `prompt.matrix-to-reviewer.md` for a separate reviewer top-level Codex session,
       and an updated `practical-stage-summary.md` with
       `next_stage_transition = matrix-review allowed` or
       `matrix-review conditional` before launch.
   - Do not create, update or overwrite canonical test cases under
     `fts/<ft-slug>/test-cases/*.md` in this pass. If such a file already exists
     from an earlier or failed run, do not treat it as current output until the
     matrix review is accepted and the TC-writing pass intentionally refreshes it.
   - Set routing to reviewer with `review_mode = matrix_review`.
   - Markdown `test-design-matrix.md` is the default and required matrix artifact.
     Do not create an XLSX duplicate in `practical_v0_8` unless the user
     explicitly asks for XLSX export.
   - Optional artifacts are allowed only when they directly improve the current
     scope:
     - `dictionary-inventory.md`;
     - `fixture-catalog.md`;
     - `ba-questions.md` or `scope-clarification-requests.md`.
   - Do not create source-assertions, source-assertion review receipts,
     semantic bridge projections, immutable attempts, benchmark configs,
     sharding artifacts, large ledgers, or final-format review artifacts in this
     route.

4. `ft-test-case-reviewer` — matrix review gate
   - Run `matrix_review` over FT/PDF context, `scope-brief.md`,
     `source-row-inventory.md` / dictionary / mockup context when present, and
     `test-design-matrix.md`.
   - Re-derive the coverage plan from FT/PDF/XHTML/support before trusting the
     writer matrix. Check visible field names, button/action labels, table rows,
     mockup figures and disputed source/support notes directly against the
     source package. Re-derive applicable document-global type constraints and
     exact auto-fill target lists rather than trusting a summarized field row.
     A matrix cannot be accepted when reviewer only validates
     matrix formatting or traceability tokens.
   - Do not review canonical test cases in this pass. The expected current TC file
     state is "not created yet" or "old draft ignored".
  - Default behavior: run reviewer in a separate top-level Codex session. The
    controller/writer session must first run the Reviewer launch preflight with
    `--check-only`, then materialize one allowed receipt with `--output`, then
    discover Codex thread tools with
    `tool_search` when they are not already loaded, use `list_projects` and
    `create_thread` to launch the reviewer prompt in a separate top-level Codex session,
    then use `wait_threads`/`read_thread` or the returned thread id to collect
    the reviewer result. A sub-agent spawned inside the writer/controller turn
    does not count as a separate top-level Codex session for independent sign-off. If
    Codex thread tools are genuinely unavailable in the runtime, stop with
    `blocked-reviewer-session-tool-unavailable`; do not perform same-session
    review as the route verdict.
  - A preflight result with `allowed: false` and `status: blocked` is a
    controller outcome, not a reviewer failure. Save only
    `review-launch-preflight.json`, update the affected `workflow-state.yaml`
    and the concise `practical-stage-summary.md`; do not create reviewer task,
    `review-findings.md`, reviewer session log, reviewer decision log or
    reviewer-independence receipt. If the block is a failed Writer Quality Gate,
    set `current_stage: ft-test-case-writer`,
    `stage_status: blocked-quality-gate` and
    `next_skill: ft-test-case-writer`. Use `blocked-input` only for missing or
    contradictory external inputs.
  - When the controller creates a separate reviewer top-level Codex session, set a
    short human-readable title such as `Partners-v1 TC review 9.1+9.3.1`;
    never leave the full reviewer prompt as the task title.
   - The reviewer input must exclude writer transcript, writer private
     reasoning, and process diagnostics that are not needed to judge the suite.
   - A same-session review is allowed only when the user explicitly asks for an
     advisory non-independent review. It must be labeled
     `reviewed-not-independent`; it cannot produce matrix acceptance, TC review
     acceptance, writer-revision authority, independent sign-off or release
     routing. Store advisory matrix review output as
     `advisory-test-design-matrix-review.md`, not as
     `test-design-matrix-review.md`.
   - Produce `test-design-matrix-review.md` and `review-independence.md` in the
     practical scope folder.
   - Markdown matrix review is enough for practical route. Do not require or
     create `round-N-traceability-matrix.xlsx` unless the user explicitly asks
     for XLSX export or an explicit session-based/production-promotion route was
     selected.
   - Produce exactly one matrix verdict:
     `matrix-accepted`, `matrix-changes-required`, or `matrix-rejected`.
   - If verdict is not `matrix-accepted`, route back to writer for matrix repair;
     do not route to canonical TC writing.
   - Also produce or update `practical-stage-summary.md` after the matrix review
     or matrix re-review. The summary must expose accepted scope, blocked /
     capped scope, reasons, whether TC can be written with explicit statuses, and
     the next safe step. It must include the root consistency fields,
     validator-error classification fields when validation was run, and
     `next_stage_transition` and an explicit `active_scope_ids` allowlist. Its
     human-readable narrative (`next_safe_step`, transition reasons and current/prior
     stage notes) must be Russian. It must be linked from affected `workflow-state.yaml`
     artifacts. This summary is required before the controller/user receives the
     next-stage prompt.

5. `ft-test-case-writer` — TC draft after matrix gate
   - Start only when `review-independence.md` shows that the matrix reviewer ran
     in a separate session and either `test-design-matrix-review.md` has verdict
     `matrix-accepted`, or the current practical-stage summary records the
     bounded matrix round-cap decision `source_contradiction: no` and
     `tc_with_status_decision: write-with-statuses` for this exact scope.
   - Create or update canonical test cases in
     `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`.
   - Keep the canonical file in `draft-ready-for-review` or `review-ready`;
     writer must not mark it `released-*`, `signed-off`,
     `independently-signed-off` or equivalent before TC review has accepted the
     suite.
   - The canonical file must remain draft/review-ready before an independent
     reviewer pass accepts it.
   - Exact release invariant: no `released-*`, `signed-off` or equivalent status
     before an independent reviewer pass accepts the canonical cases.
   - Create `prompt.tc-to-reviewer.md` for a separate top-level TC reviewer
     Codex session.

6. `ft-test-case-reviewer` — TC review gate
   - Run practical TC review over FT/PDF context, `scope-brief.md`, accepted
     `test-design-matrix.md`, `test-design-matrix-review.md`, and canonical test
     cases.
   - Default behavior: run reviewer in a separate top-level Codex session. The
     controller/writer session must pass the Reviewer launch preflight before it
     creates the reviewer session with Codex thread
     tools (`tool_search` discovery if needed, then `list_projects` /
     `create_thread`). The reviewer input must exclude writer transcript and
     private reasoning. The controller must give the separate reviewer
     task/thread a concise title, not the full prompt body. If the tool path is
     unavailable, stop as `blocked-reviewer-session-tool-unavailable` and do not
     issue a same-session route verdict.
   - Produce `review-findings.md` only for validator-accepted separate
     Codex-thread TC review and update `review-independence.md` with
     TC-review evidence.
   - If the user explicitly requests advisory non-independent review, or if a
     controller performs auxiliary sub-agent/same-session analysis, store its
     output as `advisory-review-findings.md`. It may inform a later human
     decision, but it must not set `stage_status: ready-for-writer-revision`,
     `next_skill: ft-test-case-writer`, matrix/TC acceptance, sign-off or release
     unless the workflow explicitly records
     `controller_authorized_advisory_revision: yes`.
   - Classify findings as:
     - `blocking` when the test case is materially wrong or misleading;
     - `nonblocking` when the issue is wording, grouping or minor priority;
     - `needs-ui-calibration` when the FT obligation exists but the observable UI
       reaction is unknown;
     - `needs-test-data` when execution needs a fixture that is not in the
       package.

7. Revision
   - The writer performs one revision pass for blocking findings.
   - Route the revised canonical suite to one final independent full-scope TC
     review in a separate top-level Codex session. The reviewer must validate the
     writer's status assertions against canonical metadata before acceptance.
   - Do not enter an unbounded repair loop. If the final review still returns
     `tc-changes-required`, report its findings and stop; do not apply another
     automatic revision.

## Candidate revision after a Writer Quality Gate block

`blocked-quality-gate` is a draft-quality result, not an external-input state.
It may be repaired only when the current macro-stage or controller explicitly
authorizes one bounded writer revision. Before replacing an existing canonical
test-case file, create and verify an immutable `pre_write_baseline` snapshot
under `work/review-cycles/<scope-slug>/versions/<snapshot-id>/` with
`scripts/practical_snapshot_preflight.py`, according to
`test-case-versioning-policy.md`. The command must finish with `status: valid`
before any canonical write. Snapshot only the canonical TC and the split
artifacts that this revision will overwrite; never copy or alter
workflow-state, prompts, session logs, findings or stage summary inside it.
Use `snapshot_role: pre_write_baseline` and the audit reason
`pre_quality_gate_baseline` in its manifest.

After the verified snapshot, the writer updates the one canonical file in `test-cases/`.
That file is the current candidate for the next independent review; do not create
parallel `*-candidate.md`, `*-round-N.md` or other competing files in
`test-cases/`. The workflow must link the snapshot and state that the current
file is a candidate revision through
`latest_artifacts.pre_write_baseline_snapshot`. TC-review preflight verifies
that linked snapshot before a reviewer task may start. A failed Writer Quality Gate alone does not
authorize overwriting an already accepted/released baseline.

## Release statuses

Use these statuses in canonical test cases:

- `ready`
- `candidate-ui-calibration`
- `blocked-observability`
- `needs-test-data`
- `needs-future-clarification`
- `not-automatable-manual-only`

The scope can be released as:

- `released-ft-first`;
- `released-with-calibration-pending`;
- `released-with-blocked-observability`;
- `blocked-source`.

`blocked-source` is allowed only when the source package is missing or
contradictory enough that the requirement itself cannot be represented.

## Test-design matrix

The matrix is mandatory because it is the cheapest way to prove coverage without
large ledgers.

`test-design-matrix.md` is a user-facing artifact. Column headers and
human-readable cell text must be Russian, because the user can inspect this file
to verify whether the planned coverage is acceptable. English is allowed only for
stable metadata values or source literals that are intentionally English.

The matrix is writer output under review, not an accepted source of truth.
Reviewer must re-derive coverage from FT/PDF/XHTML/support/dictionaries/mockups
and then compare that independent view with the matrix. If the matrix is
incomplete or misleading, reviewer returns `matrix-changes-required` or
`matrix-rejected`; canonical test cases must not be independently signed off
until the matrix is accepted.

Minimum columns:

| Источник | Проверяемое утверждение | Объект и место выполнения | Измерение тест-дизайна | Классы покрытия | TC-ID | Статус | Примечания |
| --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- one row represents one source-backed check, one coverage class, or one
  consciously deferred check;
- every executable FT obligation must map to a `TC-*`;
- every unexecutable obligation must map to a `candidate-ui-calibration`,
  `blocked-observability` or `needs-test-data` `TC-*`;
- `Объект и место выполнения` is mandatory: name one concrete tested object and
  the exact screen/card/list/block plus user action where its result is observed;
  if either is absent from the sources, write `не определено: GAP-*` instead of
  inventing a generic usage scenario;
- `Классы покрытия` is mandatory for validation, format, length, mask,
  allowed-symbol, dictionary, requiredness, visibility-condition, dependency,
  file-upload, integration, status/lifecycle and repeatable-block rules;
- choose the exact class group from
  [../qa/coverage-class-catalog.md](../qa/coverage-class-catalog.md); activate a
  group only when the current source contains the matching rule;
- when a source-backed `Создать` / `Добавить` action opens a form for a new
  independent object, child record or row, add the derived
  `R-CREATE-FORM-ISOLATION` row: create A with distinctive user-entered values,
  open creation of B, and verify that B is not prefilled with A values. The
  row may be `not-applicable` only with a reason: no independent creation,
  source-defined copy/inheritance/persistent draft, or no editable value to
  distinguish. Source-defined defaults, context values and autofill are not
  treated as leaked values;
- do not create test cases for glossary/status-table rows when later FT sections
  define the actual screen, action and expected result; assign the matrix row to
  that screen/action scope and use the status row only as supporting context in
  `Источник`;
- a status/lifecycle row may not become a generic TC about an `entity or child
  entity`, `ordinary use`, `removal from use` or `return to use`. Split parent
  and child objects unless the same source-backed screen, action and observable
  result genuinely apply to both; record that narrow common owner in
  `Объект и место выполнения` and `Сценарное обоснование`;
- do not use English technical aliases such as `source_ref`, `atomic_check`,
  `coverage_classes` as the visible headers in this Markdown file. Internal
  tools may normalize the Russian columns to stable keys, but the checked-in
  matrix remains Russian.

Matrix review gate:

- Canonical TC writing is unlocked by verdict `matrix-accepted` from
  `test-design-matrix-review.md`. If the first matrix review returns
  `matrix-changes-required`, the writer may perform exactly one bounded matrix
  repair, record it in `matrix-repair-summary.md`, and perform one independent
  matrix re-review. If that re-review is still not accepted, TC writing is
  allowed only through the explicit practical round-cap decision described above;
  it is never an implicit controller exception.
- `matrix-accepted` means every current-scope source obligation is represented
  as a planned TC, a class-specific deferred TC, or a narrow documented gap, and
  the reviewer has independently checked the plan against FT/PDF/XHTML/support
  rather than relying on writer's matrix alone;
- `matrix-changes-required` means writer can repair the matrix in one bounded
  revision and route the repaired matrix to one independent matrix re-review;
  after that re-review, the per-scope round-cap policy decides between
  `write-with-statuses` and `block-source-contradiction`;
- `matrix-rejected` means the coverage plan is materially unreliable and TC
  review must stop until the matrix is rebuilt.
- Matrix review must block a plan that uses one representative invalid value as
  complete coverage for a source-backed restriction, omits applicable classes
  from `coverage-class-catalog.md`, creates standalone tests from glossary/status
  rows when later FT sections define real actions, leaves `Объект и место
  выполнения` generic or mixes UI levels, or plans TC whose expected
  result has no observable UI/API/document artifact. It must also block an
  applicable independent-create flow without the `R-CREATE-FORM-ISOLATION`
  row, or a row that demands blank source-defined defaults/autofill.

## Bounded TC Revision And Final Review Gate

When the first independent TC review returns `tc-changes-required`, the writer
may make exactly one bounded revision. Before handoff, it must compare every
affected canonical `TC-*` with its concrete runtime inputs:

- `Статус исполнения: ready` is allowed only when the case has no pending
  `Требуется подтверждение`, unverified fixture, missing test data, access or
  observability dependency;
- each affected case and its exact status after the revision must be recorded in
  `work/practical/<scope>/tc-revision-summary.md` under `## Status Assertions`;
- the writer may not set `signed-off`, `released-*` or route directly to
  `ft-ui-automation-prep`.

If a validator discovers only a status, confirmation or summary inconsistency
after that bounded revision and before final review, one contract-only status
repair is allowed. It may update only execution status, `Требуется
подтверждение`, status counters, `## Status Assertions` and the current
practical-stage summary. Record `## Contract-only Repair` with affected TC ids,
evidence and `semantic_change: no`. It must not change coverage, test design,
steps, expected results, traceability, source interpretation or the number of
writer/reviewer rounds.

The next stage is always a final independent full-scope TC review in a separate
top-level Codex session. Its `Review Focus` is a priority list, not a boundary: the
reviewer must inspect the entire current canonical suite against the FT, PDF,
XHTML, support and current statuses. Only that final review can accept the
revised baseline.

## Mandatory coverage class decomposition

The writer must not treat one sample invalid value as complete negative
coverage. For every source-backed restriction, decompose the rule into explicit
classes first, then write or defer each class.

Use the canonical catalog:
[../qa/coverage-class-catalog.md](../qa/coverage-class-catalog.md).

The catalog covers the common source-backed rule groups:

- digits-only and allowed-symbol restrictions;
- text/name-like fields;
- alphanumeric fields;
- masks and patterns;
- exact length and min/max length;
- numeric ranges and amounts;
- dates and date/time;
- requiredness and conditional requiredness;
- dictionaries, closed lists, autocomplete and integrations;
- file upload;
- repeatable blocks and child rows;
- uniqueness and duplicate checks;
- status/lifecycle rules;
- cross-field dependencies and combinations;
- generated documents and mappings.
- independent creation and form isolation.

If the exact UI reaction is unknown, do not drop the class. Keep the class in the
matrix and create a `candidate-ui-calibration` or `blocked-observability` case
with concrete input and a clear `Требуется подтверждение`. Unknown UI mechanism
changes status and expected-result precision; it does not remove the obligation.

Requiredness classes must be split by input mechanism before writing TC. A single
"all required fields are empty" TC is valid only when all listed fields are
reachable by the same setup, have the same user input mechanism, the same trigger
and the same observable oracle. Otherwise use separate TC or a parameter table in
one TC, and ensure every listed field is actually exercised in the steps.

Parameter tables are allowed only when every row keeps the same start screen,
same UI level, same navigation path, user action, trigger, pass/fail oracle and
expected result. If rows cross parent/child entities, different cards, nested
blocks, tables, lists or screens, split them into separate `TC-*`; do not
optimize the case count at the cost of automation-readiness.

Status and lifecycle checks follow the same ownership rule even without a
parameter table: a partner, its requisites, and a parent group are different
objects unless the FT names one common UI surface and one action that applies to
each. Do not hide the difference behind wording such as `партнер или реквизит`.
When the source defines only a status meaning but no observable application
point, preserve the source row as context and create a narrow `GAP-*`; do not
write a fictional availability test.

## Canonical test-case quality gates

Before handing off to reviewer, the writer checks every canonical file:

- Writer Quality Gate uses the current contract version from
  `writer-quality-gate-format.md`. If a later agent version adds a required
  semantic gate, an older draft is `blocked-quality-gate` until writer reruns
  its matrix/TC self-check; it must not append an unsupported `pass` row only to
  migrate the table.

- no service/debug sections such as UI Automation Prep details, benchmark data,
  runner diagnostics, bridge/attempt metadata or internal process logs;
- human-facing runtime text is Russian, except allowed metadata values such as
  `Positive`, `Negative`, `High`, `Medium`, `Low`;
- no phrases such as `source-backed`, `observable source`, `registered-card`,
  `semantic projection`, `exact credit-conveyor screen`, `fixture`, `support`,
  `oracle`, `lifecycle`, `signed-off`, `hash`, `receipt`, `scope`, or other
  agent-process language in runtime test cases; stable IDs such as
  `FX-DADATA-*` may appear only as code-like fixture identifiers in `Трассировка`
  or `Тестовые данные`, while the surrounding prose remains Russian;
- before `review-ready`, writer must run an explicit runtime language/style
  self-check and validator pass; if any agent-process phrase remains in
  `Название`, `Цель`, `Предусловия`, `Тестовые данные`, `Шаги`,
  `Итоговый ожидаемый результат`, `Постусловия`, or
  `Требуется подтверждение`, the draft is blocked at writer gate;
- title describes user-visible behavior, not traceability IDs or internal
  obligations;
- every status/lifecycle TC has one concrete object, one execution location and
  one observable action/result; generic availability/use wording is a writer
  gate failure, not an acceptable placeholder;
- `Предусловия` first open the relevant form/card/screen/section before entering
  a block;
- `Тестовые данные` contain concrete values or a clear `needs-test-data` reason;
- setup/precondition data must respect the source-defined input mechanism of the
  fields used to create it. If a TC creates or prepares an entity through fields
  backed by DaData, BIK, dictionary/autocomplete or another integration, use a
  verified fixture for those fields even when the integration itself is not the
  main test objective; otherwise keep the TC `needs-test-data` with the exact
  missing fixture named;
- steps are executable user actions or checks, not restatements of `BSR-*`,
  `ATOM-*`, `ASSERT-*`, hashes, source rows or abstract obligations;
- expected result is observable in UI/API/document output or explicitly marked
  `blocked-observability`;
- business states/statuses are separated from observable artifacts: keep values
  such as `Подтвержден` / `Скрыт` as setup/business state, but verify the
  displayed indicator, available action, row visibility, API field or generated
  output; do not expect status text unless source/support/UI evidence says it is
  visible;
- one test case has one main expected result;
- positive, negative and boundary coverage is driven by the FT text, dictionaries
  and support notes, not by one-code-one-case mechanics;
- if a dictionary or fixed list is referenced, the writer uses the full relevant
  list from support/source, not a few examples;
- if DaData or another integration is in scope, test cases use a fixed verified
  fixture with exact query/input and exact expected suggestion/result; do not ask
  the tester to call a live service during test execution.
- for an applicable independent creation flow, the plan contains a separate
  form-isolation TC: after creating A with distinctive user-entered values,
  opening creation of B does not prefill B with A values. Source-defined
  defaults, context values, inheritance, clone/import behavior and documented
  draft restoration are excluded or tested by their own source-backed case.
- for each source obligation that names a closed set of fields, values or output
  parts, the matrix and TC enumerate the same set. A `ready` TC may not silently
  omit one member of the source list; its fixture must contain every value that
  the TC asserts.
- do not add an unrelated save action to a file-count, format or field-validation
  TC. If persistence must also be checked, write a separate self-contained TC
  with a single observable persistence result.
- a TC has exactly one `Статус исполнения`; when an unavailable account, role,
  object or data fixture is shared by several checks, every dependent matrix/TC
  line is `needs-test-data`. A BA question is not a substitute for test setup.
- final TC source navigation stays slim: `Трассировка` carries codes/atoms/section,
  while `Источник / цитата требования` carries only a short real quote. Do not
  duplicate the same `ATOM-*`/`SRC-*`/section list again in `Ссылка на ФТ` or
  `Источник требования` unless those fields add nonduplicating navigation.

## Practical-route heavy-artifact guard

In `practical_v0_8`, do not create or route through `source-assertions*`,
`semantic-design*`, `*shard*`, `ft-agent run` configs, `work/iterations/`,
benchmarks/evals or XLSX traceability duplicates unless the user explicitly
selects a named heavy/development route. Stop and repair a mixed handoff.

## Business-analyst questions

Ask BA only about an unresolved product rule, meaning, conflict, trigger or
observable result after checking the package DOCX/XHTML/PDF/support. Do not ask
for a test account, role, object, record or fixture that a tester/automation
engineer can prepare: name the required properties and use `needs-test-data`.
Each question is Russian, self-contained, anchored to source and field/action,
states the exact unknown and expected answer, and names affected TC/statuses.
Reuse prior approved answers. If the source obligation remains representable,
release it with `candidate-ui-calibration`, `blocked-observability` or
`needs-test-data` instead of stopping the scope.

## Reviewer focus

The practical reviewer must block:

- a matrix that has not been independently checked against FT/PDF/XHTML/support;
- a matrix review that does not show source-side checks for coverage, field/button
  labels, table rows, mockup figures and disputed notes that are relevant to the
  scope;
- a suite that claims independent sign-off without separate-session evidence;
- any final verdict called `signed-off` when `independent_signoff_claim_allowed`
  is not `yes`;
- pseudo-test cases that cannot be executed;
- generic fixtures such as “valid entity” without concrete data or a
  `needs-test-data` status;
- a `ready` matrix/TC line that depends on an unavailable account, role, object
  or fixture; every check sharing that prerequisite must be `needs-test-data`;
- merged checks that hide independent positive/negative/boundary behavior;
- one invalid representative that claims to cover several independently
  derivable classes;
- a `candidate-ui-calibration` case that drops a source-backed class instead of
  preserving it with concrete input and a calibration question;
- invented UI messages, validation triggers, buttons, integrations or statuses;
- English agent-process wording in Russian runtime fields;
- missed dictionaries, missing boundary classes, missing equivalence classes and
  missing negative classes when the FT states restrictions;
- generic requiredness cases that list several fields but exercise only a subset
  of them, or merge typed input, dictionary/autocomplete, system-filled,
  autofilled, readonly and repeatable-row fields without a clear decomposition;
- English visible headers or English process wording in `test-design-matrix.md`
  when Russian human-readable wording is expected;
- use of status/glossary rows as standalone tests when later FT sections define
  the actual behavior.
- TC whose expected result verifies only a business/internal state label without
  a concrete observable artifact, or assumes visible status text when source/UI
  evidence only supports an indicator/action/list visibility/API field.

The reviewer should not require heavy process artifacts when the matrix,
scope brief and canonical test cases are sufficient to prove coverage.

## Reviewer independence evidence

Create `review-independence.md` in the practical scope folder.

Minimum fields:

| field | value |
| --- | --- |
| reviewer_dispatch_receipt | `<controller-owned review-dispatch.json>` |
| reviewer_was_separate_session | `yes/no` |
| reviewer_input_excluded_writer_transcript | `yes/no` |
| reviewer_input_excluded_writer_private_reasoning | `yes/no` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `yes/no` |
| review_mode | `matrix_review/tc_review` |
| review_round | `<round number>` |
| review_launch_preflight | `<path to review-launch-preflight.json>` |
| review_launch_preflight_status | `allowed` |

Rules:

- `independent_signoff_claim_allowed = yes` only when
  `reviewer_was_separate_session = yes` and the reviewer did not receive writer
  transcript/private reasoning.
- `reviewer_dispatch_receipt` must point to the controller-owned receipt written
  immediately after `create_thread`. It, rather than reviewer-authored prose,
  holds the durable separate-session ID and execution surface. Do not write
  `reviewer_task_or_session`, `reviewer_execution_surface` or
  `reviewer_thread_url_or_id` in reviewer-owned artifacts.
- `review_mode` and `review_round` must match the current review artifact:
  `test-design-matrix-review.md` for matrix review or `review-findings.md` for
  TC review. A matrix-review independence receipt does not prove a later TC
  review.
- `review_launch_preflight` must point to the controller receipt created before
  `create_thread`; the reviewer must have validated it with `--verify-receipt`
  before it began source or test-case assessment.
- A sub-agent, local helper or same-session pass may be used only as auxiliary
  analysis. It cannot be the final reviewer verdict for matrix acceptance, TC
  review acceptance or independent release. Its findings must be stored in an
  `advisory-*` artifact (`advisory-review-findings.md` for TC review), never in
  release-grade `review-findings.md`.
- If Codex thread tools are not already loaded, discover them with `tool_search`
  and use `list_projects` / `create_thread` as the standard reviewer launch
  path. If the runtime genuinely cannot expose thread tools, stop after writer
  handoff with `blocked-reviewer-session-tool-unavailable` and ask the
  user/controller to launch the reviewer prompt in a new session. If the user
  explicitly chooses a same-session fallback, complete only an advisory practical
  review and label it `reviewed-not-independent`; do not use it for matrix
  acceptance, TC review acceptance, writer revision routing, sign-off or release.

## Production TC visible headings

Production files under `fts/**/test-cases/*.md` are user-facing Russian
artifacts. Use natural Russian sentence casing for visible headings:

- `## Сведения о наборе`, not `## Сведения О Наборе`;
- `## Границы покрытия`, not `## Границы Покрытия`;
- `## Сводка`, not `## Summary` or `## Coverage Summary`.

English remains allowed only for approved metadata enum values such as
`Positive`, `Negative`, `High`, `Medium`, `Low`.
