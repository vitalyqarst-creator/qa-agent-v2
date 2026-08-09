# Practical Stage Summary Template

Use this template verbatim for `practical-stage-summary.md` in practical route
v0.8.3. The file is a user-facing handoff and a machine-checkable gate.

## Summary

| field | value |
| --- | --- |
| route_profile | `practical route v0.8.3` |
| summary_stage | `<short-stage-id>` |
| code_root | `<absolute path>` |
| execution_working_directory | `<absolute path; must equal code_root>` |
| ft_package_root | `<absolute path>` |
| artifact_write_root | `<absolute path>` |
| root_split_allowed | `yes / no` |
| root_split_authority | `<user/controller approval or not-applicable>` |
| next_stage_transition | `matrix-review allowed / matrix-review conditional / matrix-review blocked / writer allowed / writer conditional / writer blocked / tc-review allowed / tc-review conditional / tc-review blocked / not-applicable` |
| next_safe_step | `<one Russian sentence>` |
| review_launch_preflight_status | `not-run / allowed / blocked / not-applicable` |
| review_launch_preflight_receipt | `<FT-relative review-launch-preflight-rN.json or not-applicable>` |
| per_scope_next_stage_transitions | `yes / not-applicable` |
| production_tc_clean | `yes / no / mixed / not-applicable` |
| git_persistence | `tracked / ignored-by-git / mixed / not-applicable` |
| validator_primary_command | `python scripts/validate_agent_artifacts.py --root <FT package root> --json / not-run` |
| validator_primary_root | `<absolute FT package root or not-applicable>` |
| validator_supplementary_command | `<repo-root validator command or not-run>` |
| validator_findings_breakdown | `tc_quality=<n>; process_artifact=<n>; validator_path_resolution=<n>; unrelated_repo=<n>` |
| validator_errors_count | `<integer>` |
| validator_scope_errors_count | `<integer for active_scope_ids, or not-applicable>` |
| validator_scope_errors_evidence | `<finding ids or not-applicable>` |
| validator_external_errors_count | `<integer for other scopes, or not-applicable>` |
| validator_external_errors_evidence | `<finding ids or not-applicable>` |
| validator_errors_classification | `none / next-stage-blocker / pre-existing-unrelated / validator-false-positive / mixed / not-applicable` |
| validator_errors_evidence | `<finding ids or not-applicable>` |
| validator_warnings_count | `<integer>` |
| validator_warnings_classification | `none / blocking-for-scope / expected-pre-writer / nonblocking-info / mixed / not-applicable` |
| validator_warnings_evidence | `<finding ids or not-applicable>` |
| validator_info_count | `<integer>` |
| validator_info_evidence | `<finding ids or not-applicable>` |
| source_row_counts | `<scope-id>=<count> через `;`, например `05=27`; для scope-analysis обязателен exact count из source-row-inventory.md>` |
| source_restore_provenance | `<source path/checkpoint or not-applicable>` |
| source_restore_sha256 | `<SHA-256 or not-applicable>` |
| active_scope_ids | `<обязательный allowlist: один id или список через запятую, например 02, 05>` |

## TC Review Snapshot

Заполняй этот раздел только после `tc_review`. Он фиксирует именно текущий review
и не заменяет полные `review-findings.md` / `review-independence.md`.

| scope | verdict | blocking_finding_count | reviewer_task_or_session | reviewer_execution_surface |
| --- | --- | --- | --- | --- |
| `<scope-slug>` | `tc-accepted / tc-changes-required` | `<integer>` | `<separate Codex session id>` | `codex-thread` |

## Scope transitions

| scope | verdict | next_stage_transition | source_contradiction | tc_with_status_decision | reason |
| --- | --- | --- | --- | --- | --- |
| `<scope-slug>` | `matrix-not-created / matrix-accepted / matrix-changes-required / round-cap-reached / blocked` | `<enum from Summary>` | `yes / no / not-applicable` | `write-with-statuses / block-source-contradiction / not-applicable` | `<Russian reason>` |

## Current stage actions

- `<Only actions performed in the current stage/turn. Do not repeat older history here.>`

## Prior state context

- `<Older facts that explain the current state, for example previous review verdicts or already completed revisions.>`

## Rules

- Enum fields must contain only the enum value, not explanatory prose.
- Before a matrix exists, use `matrix-not-created`; it is not a reviewer verdict.
  It routes only to matrix writing through `writer allowed`, `writer conditional`
  or `writer blocked`, and `tc_with_status_decision = not-applicable`.
- For `matrix-changes-required`, `matrix-accepted` and `matrix-not-created`,
  `tc_with_status_decision = not-applicable`: the status-based decision is made
  only after the review cap. For `round-cap-reached`,
  `source_contradiction = no` requires `write-with-statuses`; `yes` requires
  `block-source-contradiction`. Put case statuses and explanation only in
  `reason`, never in the enum cell.
- Before creating any separate reviewer task, run
  `python scripts/practical_review_preflight.py` with this summary, the selected
  scope id, the review mode and `--check-only`. Use it to validate the final
  controller state before materializing evidence. Only when this check returns
  `allowed: true`, run the same command once with `--output` to store
  `review-launch-preflight.json` next to the practical scope artifacts. Do not
  edit controller-owned artifacts after that output is written. The reviewer
  repeats the same command with `--verify-receipt <review-launch-preflight.json>`
  before reviewing.
- The controller may pre-link only the exact active-round receipt path in
  `latest_artifacts.review_launch_preflight` before materialization. This is a
  planned artifact, not a stale link; any other missing `latest_artifacts` link
  remains a validator warning.
- Immediately record a preflight result in controller state. For an allowed TC
  review, link its receipt as `latest_artifacts.review_launch_preflight`, set
  `review_launch_preflight_round_<N>: allowed`,
  `tc_review_gate_status: preflight-allowed-round-<N>` and
  `final_independent_tc_review_status: ready-to-launch-round-<N>`. Set the
  summary fields `review_launch_preflight_status` and
  `review_launch_preflight_receipt` to the same receipt, and change
  `next_safe_step` to reviewer dispatch. Do this before reporting the preflight
  result or creating the separate reviewer task.
- If the preflight result is `allowed: false` with `status: blocked`, it is a
  controller gate result. Keep only the preflight receipt, this summary and the
  workflow-state update; do not create reviewer findings, reviewer logs or a
  reviewer-independence receipt. For a failed Writer Quality Gate use
  `stage_status: blocked-quality-gate` and route back to the writer; reserve
  `blocked-input` for missing or contradictory external inputs.
- Explanations belong in `next_safe_step`, scope `reason` or a short notes section.
- Keep `Current stage actions` and `Prior state context` separate. A summary that
  mixes old route history into current-stage actions is not a clear handoff.
- In the current validator evidence and current-stage actions, refer only to the
  active review-launch round. Put references to superseded rounds in `Prior state
  context`; do not correct this wording after a receipt is materialized because
  the receipt hash-binds the summary.
- For every named `summary_stage`, both sections are mandatory. In a
  `contract-only-status-repair`, `Current stage actions` may describe only the
  repair; the preceding writer revision belongs in `Prior state context`.
- After every repair, run:
  `python scripts/refresh_practical_stage_summary.py --root . --summary <path> --scope-id <two-digit scope id> --print-fields`
  and update validator counts/evidence, including info fields, plus `git_persistence`
  from the output.
- Before controller aliases, `workflow-state.yaml` or this summary are updated
  after an independent review, run
  `python scripts/practical_review_finalization_guard.py` with the original
  launch receipt, review artifact and independence artifact. A blocked guard is
  a controller-state integrity failure, not a reason to revise test cases.
- `execution_working_directory` must equal `code_root`. If the current Codex task
  is attached to another worktree, hand it off or recreate it in `code_root`
  before the stage; changing into an external repository mid-stage is invalid.
- The `Code Version Gate` must record the exact current `code_root` commit. Refresh
  this summary after any contract-only repair before the next handoff.
- For FT-package practical stages, primary validation is:
  `python scripts/validate_agent_artifacts.py --root <FT package root> --json`.
  Repo-root validation is supplementary. Keep primary package-root findings
  separate from repo-root-only findings.
- A package-wide validator result is audit evidence, not by itself the decision
  to launch a reviewer for one scope. The launch decision comes only from
  `practical_review_preflight.py` for the declared `active_scope_ids`: its
  `scope_relevant` and `package_global` errors block; `external` errors are
  recorded but do not block that scope.
- Classify validator warning/error findings in `validator_findings_breakdown` as:
  `tc_quality`, `process_artifact`, `validator_path_resolution` or
  `unrelated_repo`.
- Если `validator_errors_classification = pre-existing-unrelated` или `mixed`, обязательно заполни `validator_scope_errors_*` и `validator_external_errors_*`: их количества должны в сумме давать `validator_errors_count`, а evidence для ненулевой части содержит каждый `finding id` и путь. Нельзя объявить ошибку «внешней» только текстом без проверяемого идентификатора и пути.
- `validator_errors_count`, `validator_warnings_count` and
  `validator_info_count` are the canonical counts. Do not repeat them as
  unprefixed `errors_count`, `warnings_count` or `info_count`; if a secondary
  report table keeps such fields for a consumer, every duplicate must exactly
  match the canonical fields and the same validator run.
- If `git_persistence = ignored-by-git`, the stage/final response must explicitly
  say that changed FT/package artifacts are local, ordinary commit/push will not
  include them, and persistence requires `git add -f <paths>` or an export/bundle.
- An accepted review with `git_persistence = ignored-by-git` or `mixed` is
  `accepted-local-publication-pending`, not `released-*`. The only next action
  is explicit persistence of the accepted artifacts; do not reopen writer/reviewer
  work merely because the package is ignored.
- Link this file from affected `workflow-state.yaml` files or from a
  package-level state/index inside the actual `ft_package_root`.
- После `tc_review` generic aliases `review_independence`, `session_log`,
  `decision_log` и `review_findings` в каждом `workflow-state.yaml` должны
  ссылаться на те же текущие артефакты, что и dedicated `tc_review_*` aliases.
- Для multi-scope stage `active_scope_ids` — allowlist текущего этапа. Не
  изменяй artifacts scope вне этого перечня ради общего package-level validator;
  классифицируй такие findings как внешние для текущего этапа.
- `active_scope_ids` обязателен и содержит только номера handoff-папок текущего
  этапа. `all`, диапазоны и неявные описания не допускаются.
- `next_safe_step`, `reason` в таблице переходов, а также текст в разделах
  `Current stage actions` и `Prior state context` пиши по-русски. Английскими
  могут остаться только канонические enum-значения, идентификаторы, пути и
  технические литералы в code span.
