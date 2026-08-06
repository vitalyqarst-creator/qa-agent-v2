# Practical Stage Summary Template

Use this template verbatim for `practical-stage-summary.md` in practical route
v0.8.1. The file is a user-facing handoff and a machine-checkable gate.

## Summary

| field | value |
| --- | --- |
| route_profile | `practical route v0.8.1` |
| summary_stage | `<short-stage-id>` |
| code_root | `<absolute path>` |
| ft_package_root | `<absolute path>` |
| artifact_write_root | `<absolute path>` |
| root_split_allowed | `yes / no` |
| root_split_authority | `<user/controller approval or not-applicable>` |
| next_stage_transition | `writer allowed / writer conditional / writer blocked / tc-review allowed / tc-review conditional / tc-review blocked / not-applicable` |
| next_safe_step | `<one Russian sentence>` |
| per_scope_next_stage_transitions | `yes / not-applicable` |
| production_tc_clean | `yes / no / mixed / not-applicable` |
| git_persistence | `tracked / ignored-by-git / mixed / not-applicable` |
| validator_primary_command | `python scripts/validate_agent_artifacts.py --root <FT package root> --json / not-run` |
| validator_primary_root | `<absolute FT package root or not-applicable>` |
| validator_supplementary_command | `<repo-root validator command or not-run>` |
| validator_findings_breakdown | `tc_quality=<n>; process_artifact=<n>; validator_path_resolution=<n>; unrelated_repo=<n>` |
| validator_errors_count | `<integer>` |
| validator_errors_classification | `none / next-stage-blocker / pre-existing-unrelated / validator-false-positive / mixed / not-applicable` |
| validator_errors_evidence | `<finding ids or not-applicable>` |
| validator_warnings_count | `<integer>` |
| validator_warnings_classification | `none / blocking-for-scope / expected-pre-writer / nonblocking-info / mixed / not-applicable` |
| validator_warnings_evidence | `<finding ids or not-applicable>` |
| validator_info_count | `<integer>` |
| validator_info_evidence | `<finding ids or not-applicable>` |
| source_restore_provenance | `<source path/checkpoint or not-applicable>` |
| source_restore_sha256 | `<SHA-256 or not-applicable>` |
| active_scope_ids | `<обязательный allowlist: один id или список через запятую, например 02, 05>` |

## TC Review Snapshot

Заполняй этот раздел только после `tc_review`. Он фиксирует именно текущий review
и не заменяет полные `review-findings.md` / `review-independence.md`.

| scope | verdict | blocking_finding_count | reviewer_task_or_session | reviewer_execution_surface |
| --- | --- | --- | --- | --- |
| `<scope-slug>` | `tc-accepted / tc-changes-required` | `<integer>` | `<Codex task/thread id>` | `codex-task / codex-thread` |

## Scope transitions

| scope | verdict | next_stage_transition | source_contradiction | tc_with_status_decision | reason |
| --- | --- | --- | --- | --- | --- |
| `<scope-slug>` | `matrix-accepted / matrix-changes-required / round-cap-reached / blocked` | `<enum from Summary>` | `yes / no / not-applicable` | `write-with-statuses / block-source-contradiction / not-applicable` | `<Russian reason>` |

## Current stage actions

- `<Only actions performed in the current stage/turn. Do not repeat older history here.>`

## Prior state context

- `<Older facts that explain the current state, for example previous review verdicts or already completed revisions.>`

## Rules

- Enum fields must contain only the enum value, not explanatory prose.
- Explanations belong in `next_safe_step`, scope `reason` or a short notes section.
- Keep `Current stage actions` and `Prior state context` separate. A summary that
  mixes old route history into current-stage actions is not a clear handoff.
- After every repair, run:
  `python scripts/refresh_practical_stage_summary.py --root . --summary <path> --print-fields`
  and update validator counts/evidence, including info fields, plus `git_persistence`
  from the output.
- For FT-package practical stages, primary validation is:
  `python scripts/validate_agent_artifacts.py --root <FT package root> --json`.
  Repo-root validation is supplementary. Keep primary package-root findings
  separate from repo-root-only findings.
- Classify validator warning/error findings in `validator_findings_breakdown` as:
  `tc_quality`, `process_artifact`, `validator_path_resolution` or
  `unrelated_repo`.
- If `git_persistence = ignored-by-git`, the stage/final response must explicitly
  say that changed FT/package artifacts are local, ordinary commit/push will not
  include them, and persistence requires `git add -f <paths>` or an export/bundle.
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
