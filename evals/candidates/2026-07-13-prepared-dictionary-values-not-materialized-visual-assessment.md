# prepared-dictionary-values-not-materialized: structured dictionary loses executable leaf values

## Metadata

- `candidate_id`: `CAND-2026-07-13-PREPARED-DICT-LEAF-VALUES`
- `created_at`: `2026-07-13`
- `source_signal`: `H52 live reviewer F-001`
- `affected_skill`: `ft-test-case-iteration; ft-test-case-writer`
- `failure_class`: `prepared-dictionary-values-not-materialized`
- `status`: `implemented`

## Failure Signal

- `bad_artifact`: `fts/AutoFin/work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `bad_output_excerpt`: `TC-VAMB-005` lists only eight group names; `TC-VAMB-006` says «обычные значения всех групп DICT-001».
- `why_it_is_wrong`: Both cases claim full dictionary/value-control coverage but omit the concrete leaf values needed for manual execution.
- `source_or_rule_ref`: `BSR 315`; `DICT-001` -> `DICT-101`-`DICT-108`; dictionary inventory policy; reviewer F-001.

## Evidence Bundle

- `ft_package_or_fixture`: `AutoFin / visual-assessment-medium-scope-benchmark-v1`
- `review_findings`: `.../attempts/reviewer-r1/attempt-001/runner-output/findings.md#F-001`
- `traceability_refs`: `OBL-006; OBL-007; ATOM-006; ATOM-007; BSR 315; DICT-001`
- `test_case_refs`: `TC-VAMB-005; TC-VAMB-006`
- `validator_output`: structure, seed, obligation and quality gates all passed, proving a deterministic false-negative.

## Pattern / Recurrence

- `seen_in`: one blocking medium-scope live benchmark.
- `same_failure_shape`: prepared source evidence has complete hierarchical dictionary, generated case collapses leaf values into a symbolic reference.
- `not_noise_because`: reviewer rejected 2/13 obligations and the missing values are mechanically derivable from package data.

## Eval Target

- `input_fixture`: prepared v6 package with parent `DICT-001`, child dictionaries and obligations claiming full composition/control coverage.
- `expected_detection_or_output`: generated draft contains every required active leaf value, or deterministic gate rejects the draft before reviewer.
- `pass_criteria`: no symbolic «all DICT values» substitute remains for a full-composition obligation; gate reports exact missing dictionary ids/values when mutated fixture omits one leaf.
- `fail_criteria`: draft/gate passes while any required active leaf value is absent from the assigned TC set.

## Bounded Improvement Task

- `writable_surfaces`: `scripts/codex_exec_review_cycle_runner.py`; prepared dictionary contract helpers; focused tests under `tests/`.
- `read_only_context`: H52 immutable package, draft, quality gates and reviewer finding.
- `out_of_scope`: FT/source changes, test-case promotion, V1 retry, prompt-wide rewrite, dictionary truncation.

## Validation Gates

- `targeted_eval`: positive full dictionary and negative one-leaf-omitted fixtures.
- `regression_suite`: prepared package/compiler/runner/reviewer tests and agent architecture tests.
- `manual_review_needed`: confirm one-case dictionary grouping remains executable and does not duplicate one TC per value.

## Routing Decision

- `decision`: `accepted-eval-proposal`
- `reason`: clear blocking defect with deterministic expected output; package already contains complete source-backed values.
- `next_action`: exercise the enforced v7 contract in the next authorized medium-scope benchmark; no live rerun was performed in this iteration.

## Implementation Notes

- `implemented_in`: prepared package/compiler dictionary requirements, runner materialization, obligation gate v4 and focused package/compiler/runner/gate tests.
- `gate_behavior`: exhaustive obligations carry exact group/leaf/path values; the runner inserts them into the assigned TC and the deterministic gate reports exact missing or unexpected values.
- `legacy_compatibility`: only stable legacy dictionary obligation classes are mapped; free-form prose is never used to infer exhaustive coverage.
- `calibration_fix`: source-backed UI calibration now has an explicit lifecycle status independent of `GAP-*`.
- `verification`: the H52 package was recompiled diagnostically without a live LLM run; targeted positive and one-leaf-omitted regressions pass.
