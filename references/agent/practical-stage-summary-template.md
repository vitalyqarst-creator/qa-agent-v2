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

## Scope transitions

| scope | verdict | next_stage_transition | source_contradiction | tc_with_status_decision | reason |
| --- | --- | --- | --- | --- | --- |
| `<scope-slug>` | `matrix-accepted / matrix-changes-required / round-cap-reached / blocked` | `<enum from Summary>` | `yes / no / not-applicable` | `write-with-statuses / block-source-contradiction / not-applicable` | `<Russian reason>` |

## Rules

- Enum fields must contain only the enum value, not explanatory prose.
- Explanations belong in `next_safe_step`, scope `reason` or a short notes section.
- After every repair, run:
  `python scripts/refresh_practical_stage_summary.py --root . --summary <path> --print-fields`
  and update validator counts/evidence, including info fields, plus `git_persistence`
  from the output.
- If `git_persistence = ignored-by-git`, the stage/final response must explicitly
  say that changed FT/package artifacts are local, ordinary commit/push will not
  include them, and persistence requires `git add -f <paths>` or an export/bundle.
- Link this file from affected `workflow-state.yaml` files or from a
  package-level state/index inside the actual `ft_package_root`.
