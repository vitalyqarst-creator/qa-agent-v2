# prepared-runtime-contract-drift: package version and attempt binding must agree before launch

## Metadata

- `candidate_id`: `prepared-runtime-contract-drift-20260711`
- `created_at`: `2026-07-11`
- `source_signal`: live prepared widget-selection canary v11
- `affected_skill`: `ft-test-case-iteration`
- `failure_class`: `prepared-runtime-contract-drift`
- `status`: `implemented-and-live-verified`

## Failure Signal

- `bad_artifact`: `fts/AutoFin/work/review-cycles/codex-exec-prepared-widget-selection-live-v11-20260711/attempts/writer-r1/attempt-001/stage-output/last-message.txt`
- `bad_output_excerpt`: `route-to-standard-writer` because the package is version 4 while the embedded writer profile requires version 3; the prompt also contains two output paths.
- `why_it_is_wrong`: package v4 is the only current fast-path version, and a package whose stage instructions point to another cycle must be rejected or recompiled before an LLM session starts.
- `source_or_rule_ref`: `references/agent/prepared-stage-package-format.md`; `references/agent/prepared-writer-runtime-profile.md`.

## Evidence Bundle

- `ft_package_or_fixture`: `fts/AutoFin`
- `review_findings`: reviewer was not started
- `traceability_refs`: prepared package `autofin-widget-selection-expanded-v2`
- `test_case_refs`: none; writer correctly did not create a draft
- `validator_output`: v11 `cycle-state.yaml` with `blocked-missing-output`

## Pattern / Recurrence

- `seen_in`: live v10 tolerated the conflict by agent judgment; live v11 correctly blocked it.
- `same_failure_shape`: any prepared package reused in a cycle different from the attempt path embedded in `stage-instructions.md`.
- `not_noise_because`: the runner currently validates hashes/profile but not attempt/output binding, while the writer profile still names legacy package v3.

## Eval Target

- `input_fixture`: v4 eligible package with matching attempt binding, plus packages with stale version and foreign-cycle output/attempt roots.
- `expected_detection_or_output`: matching v4 package launches; stale profile/version or foreign attempt binding blocks during runner preflight without starting a session.
- `pass_criteria`: compiler can build a v4 package directly into the target cycle; runner verifies exact writer attempt and output paths before LLM launch.
- `fail_criteria`: the prompt contains conflicting output paths, mismatches are delegated to the LLM, or package immutability is weakened after build.

## Bounded Improvement Task

- `writable_surfaces`: prepared writer profile, prepared package/exec runner preflight, compiler invocation/tests and directly related references.
- `read_only_context`: v11 cycle and existing compiled widget/common-actions inputs.
- `out_of_scope`: production promotion and domain TC changes.

## Validation Gates

- `targeted_eval`: matching/mismatching attempt-binding tests and prepared writer profile v4 assertion.
- `regression_suite`: canonical full suite.
- `manual_review_needed`: verify a newly compiled target-cycle package before the next promotion-off live launch.

## Routing Decision

- `decision`: accepted as the next bounded fix
- `reason`: the mismatch wastes an LLM session and makes otherwise eligible v4 packages non-deterministic.
- `next_action`: keep the attempt-binding and package-version cases in the permanent regression matrix; no additional bounded fix is open.

## Resolution Evidence

- Package schema is now version `5`; versions `1` through `4` remain readable but are not fast-path eligible.
- Runner preflight requires exact `attempt_root` and `output_path` binding and rejects a reused/foreign package before LLM launch.
- Explicit `OBL-* -> ATOM-*` mapping is machine-readable and checked by writer gate and reviewer contract.
- Checkpoint commits: `d43db29`, `9212141`.
- Live proof: widget-selection v13, v14 and v15 all used newly compiled target-bound packages and reached accepted reviewer outcomes.
- Negative proof: common-actions routing v1 compiled as `standard-required` and was rejected before state/attempt/session creation.
