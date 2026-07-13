# action-without-observable-oracle: non-executable prepared test intent

## Metadata

- `candidate_id`: `EVAL-CAND-2026-07-13-ACPD-EXECUTION-ORACLE`
- `created_at`: `2026-07-13`
- `source_signal`: V3 prepared reviewer `FIND-001..004`
- `affected_skill`: `ft-test-case-iteration`, prepared package compiler/quality gates
- `failure_class`: `action-without-observable-oracle`
- `status`: `candidate`

## Failure Signal

- `bad_artifact`: V3 unsigned `TC-ACPD-010`, `012`, `013`, `022`, `023`, `024`, `025`, `041`, `047`
- `bad_output_excerpt`: generic "values needed to save", undefined "attempt/continue scenario", vague valid date, and expected results that restate a source rule or defer the actual UI result
- `why_it_is_wrong`: a manual tester cannot reproduce the fixture, perform a named transition, or compare an observed result with an expected value
- `source_or_rule_ref`: reviewer findings; project quality criterion requiring executable test cases and one observable primary result

## Evidence Bundle

- `ft_package_or_fixture`: `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/prepared-input/application-card-client-personal-data-v3/`
- `review_findings`: `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/attempts/reviewer-r1/attempt-001/runner-output/findings.md`
- `traceability_refs`: `OBL-003`, `010`, `017`, `024`, `026`, `027`, `028`, `029`, `048`, `056`, `064`
- `test_case_refs`: `TC-ACPD-010`, `012`, `013`, `022`, `023`, `024`, `025`, `041`, `047`
- `validator_output`: V3 writer structure/obligation/quality/overlap/seed/evidence gates all pass, demonstrating an enforcement gap

## Pattern / Recurrence

- `seen_in`: four blocking findings and nine cases in one signed-off-blocking cycle
- `same_failure_shape`: the prepared intent lacks one or more of concrete data, concrete action, or observable comparison
- `not_noise_because`: the structured reviewer marks 11 obligations incorrect and gives exact required changes; the failure blocks sign-off

## Eval Target

- `input_fixture`: a minimal prepared package/draft fixture containing the V3-shaped generic fixture, undefined continuation action and source-rule-only expected result, plus a corrected counterpart
- `expected_detection_or_output`: reject the bad fixture with categorized findings and accept the corrected fixture without requiring invented UI text, widgets or integration values
- `pass_criteria`: all three bad shapes are detected; corrected calibration-aware cases pass; `GAP-002/003` remain explicit
- `fail_criteria`: bad fixture passes, corrected fixture is rejected merely for preserving a gap, or enforcement invents an exact UI reaction

## Bounded Improvement Task

- `writable_surfaces`: relevant prepared-package quality check, its focused tests/fixtures, and the smallest necessary compiler/writer instruction surface
- `read_only_context`: AutoFin FT/source/support, handoffs 20/29/38/40, V3 package/draft/findings/state
- `out_of_scope`: changing FT-first baseline, fixing unrelated AutoFin validator debt, broad keyword bans, V3 mutation or another V3 live run

## Validation Gates

- `targeted_eval`: bad V3-shaped fixture fails and corrected fixture passes
- `regression_suite`: `tests.test_codex_exec_review_cycle_runner`, `tests.test_prepared_workflow_compiler`, and scoped agent artifact validation
- `manual_review_needed`: confirm that remediation improves executability without converting `GAP-002/003` into invented behavior

## Routing Decision

- `decision`: accept as bounded candidate for the next iteration
- `reason`: sign-off blocker has concrete evidence, a stable failure shape and objective pass/fail criteria
- `next_action`: implement prevention and input remediation before creating or running immutable V4
