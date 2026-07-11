# prepared-own-output-evidence-access: own attempt output must not be treated as historical evidence

## Metadata

- `candidate_id`: `prepared-own-output-evidence-access-20260711`
- `created_at`: `2026-07-11`
- `source_signal`: live prepared widget-selection canary v10
- `affected_skill`: `ft-test-case-iteration`
- `failure_class`: `prepared-own-output-evidence-access`
- `status`: `candidate`

## Failure Signal

- `bad_artifact`: `fts/AutoFin/work/review-cycles/codex-exec-prepared-widget-selection-live-v10-20260711/attempts/writer-r1/attempt-001/runner-output/evidence-access-report.json`
- `bad_output_excerpt`: `forbidden-evidence-root-access` for `fts/AutoFin/work/review-cycles`
- `why_it_is_wrong`: the command read only the current writer attempt's `stage-output/draft.md`, which is a declared stage-owned output rather than requirement evidence.
- `source_or_rule_ref`: `references/agent/prepared-stage-package-format.md` requires outputs inside attempt root and forbids old cycle artifacts as evidence.

## Evidence Bundle

- `ft_package_or_fixture`: `fts/AutoFin`
- `review_findings`: reviewer was not started
- `traceability_refs`: `OBL-001..OBL-006`
- `test_case_refs`: unsigned `TC-AF-WS-001..003`
- `validator_output`: prepared evidence-access report above

## Pattern / Recurrence

- `seen_in`: one blocking live canary with a deterministic implementation cause
- `same_failure_shape`: any prepared stage command that self-checks its output under `work/review-cycles/**`
- `not_noise_because`: the validator uses unconditional normalized substring matching for every forbidden root.

## Eval Target

- `input_fixture`: command reading current `attempts/writer-r1/attempt-001/stage-output/draft.md`, plus commands reading a sibling cycle and production test cases.
- `expected_detection_or_output`: own-output command passes; sibling-cycle and production reads remain `forbidden-evidence-root-access`.
- `pass_criteria`: scoped allowlist cannot escape the exact current attempt output root and existing forbidden-root tests remain green.
- `fail_criteria`: whole `work/review-cycles` becomes allowed, path traversal passes, or own-output remains blocked.

## Bounded Improvement Task

- `writable_surfaces`: `test_case_agent/review_cycle/evidence_access.py`, `scripts/codex_exec_review_cycle_runner.py`, focused tests and relevant reference wording if the API changes.
- `read_only_context`: the v10 cycle, prepared package and live report.
- `out_of_scope`: production promotion, domain test-case changes, relaxing full-source or historical-cycle isolation.

## Validation Gates

- `targeted_eval`: focused evidence-access and exec-runner tests.
- `regression_suite`: canonical repository test runner plus architecture and artifact validation.
- `manual_review_needed`: verify path normalization on Windows and POSIX separators.

## Routing Decision

- `decision`: accepted as next bounded fix candidate
- `reason`: the defect blocks reviewer handoff despite a valid writer artifact and has an exact regression oracle.
- `next_action`: implement scoped current-attempt read allowance, then rerun fast and standard promotion-off arms in new cycle directories.
