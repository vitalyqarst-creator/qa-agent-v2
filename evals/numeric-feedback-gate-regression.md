# Numeric Feedback Gate Regression

## Purpose

This regression locks the lesson from `fts/ft-2-OF_16` canary v17:
numeric/input-restriction requirements such as `only digits`, `does not accept
letters`, or `does not accept below-min value` define invalid value classes, but
they do not prove a specific UI enforcement mechanism.

The writer/validator gate must stop the review cycle before reviewer handoff
when TC expected results invent observable feedback such as field clearing,
entered value not displayed, filtered characters, red highlight, error message,
blocked transition, or next section not opening without direct source evidence.

## Regression Cycle

- FT package: `fts/ft-2-OF_16`.
- Cycle: `ui-employment-canary-v17-numeric-feedback-gate-regression`.
- Canonical TC file:
  `fts/ft-2-OF_16/test-cases/2-1-1-1-1-2-ui-employment-canary-v17-numeric-feedback-gate-regression.md`.
- Cycle state:
  `fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v17-numeric-feedback-gate-regression/cycle-state.yaml`.
- Expected terminal state for this regression: `blocked-input`.

## Positive Companion Cycle

The clean companion regression is
`ui-employment-canary-v18-numeric-feedback-clean-regression`.

- Canonical TC file:
  `fts/ft-2-OF_16/test-cases/2-1-1-1-1-2-ui-employment-canary-v18-numeric-feedback-clean-regression.md`.
- Cycle state:
  `fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v18-numeric-feedback-clean-regression/cycle-state.yaml`.
- Expected writer state before reviewer handoff: `writer-draft-ready`.
- Expected runner recommendation: `run-next-stage`.

The companion cycle must demonstrate the corrected behavior:

- negative numeric/input TC do not assert field clearing, filtered characters,
  entered value not displayed, red highlight, message, blocked navigation, or
  any other UI feedback mechanism unless the source explicitly supports it;
- each unsupported invalid input class is represented as a class-specific
  `coverage-obligation-table.md` row mapped to `GAP-*`, not silently omitted and
  not falsely marked `covered`;
- representative invalid-class TC remain single-class, for example one letters
  value per numeric field, rather than bundling letters, spaces, decimal
  separators, signs and special characters under one prose oracle;
- `scoped-validator-profile.writer-r1.json` is runner-compatible and has
  `unresolved_warning_error_count = 0`;
- `runner-events.ndjson` agrees with the scoped profile unresolved count.

## Failure Signal

The v17 draft contains negative numeric TC that assert unsupported UI
mechanisms:

- `TC-EMP-V17-006` expects the below-min income value to clear from the field
  and not be displayed.
- `TC-EMP-V17-007` bundles letters, spaces, decimals, negative sign and special
  characters in one prose negative TC, and expects field clearing / not
  displayed behavior.
- `TC-EMP-V17-011` repeats the bundled invalid-class and unsupported clearing
  oracle pattern for additional income.

These are not valid source-backed oracles unless the source explicitly says the
field clears, filters, hides the entered value, shows a marker/message, or blocks
navigation.

## Must Catch

The validator and runner lifecycle must detect and preserve all of these facts:

- `test-case-unsupported-input-filtering-oracle-smell` is emitted for numeric
  rejection TC that expect field clearing, filtered input, or entered value not
  displayed without direct source evidence.
- `test-case-bundled-negative-input-classes` is emitted when one Negative TC
  checks materially different invalid classes under one prose oracle without a
  value-to-oracle parameter table.
- `writer-quality-gate.md` marks `scoped-validator-findings` as `blocked` when
  the scoped profile has unresolved warning/error findings.
- `package-ready` is not `pass` while `scoped-validator-findings` is blocked.
- `cycle-state.yaml` remains `stage_status: blocked-input` and has no active
  reviewer transition prompt.
- `runner-events.ndjson` and `scoped-validator-profile.writer-r1.json` agree on
  `unresolved_warning_error_count`.

## Pass Criteria

This regression passes when:

- `scripts/validate_agent_artifacts.py --root <v17 canonical file> --json
  --fail-on warning` fails with current-scope warnings for
  `test-case-unsupported-input-filtering-oracle-smell` and
  `test-case-bundled-negative-input-classes`;
- `scripts/codex_review_cycle_runner.py doctor --state <v17 cycle-state.yaml>`
  reports `stage_status: blocked-input`;
- the same `doctor` payload reports
  `events.scoped_validator_profile_consistency.consistent = true`;
- the same `doctor` payload reports `recommendation: no-action-terminal-status`
  after the builder writes a matching profile event;
- targeted tests cover both validator findings and doctor event/profile drift:
  - `tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_unsupported_numeric_filtering_oracle_and_bundled_classes_warn`;
  - `tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_unsupported_numeric_validation_feedback_warns`;
  - `tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_artificial_numeric_property_types_are_rejected_across_design_tables`;
  - `tests.test_codex_review_cycle_runner.CodexReviewCycleRunnerTests.test_doctor_reports_stale_scoped_validator_profile_event`.

The companion v18 pass criteria are:

- full-root validator report for `fts/ft-2-OF_16` has no current-scope findings
  whose path contains
  `ui-employment-canary-v18-numeric-feedback-clean-regression`;
- current-scope validator findings do not include
  `test-case-package-design-plan-merged-numeric-class-row` or
  `test-design-decision-table-merged-numeric-class-decision`;
- `package-test-design-plan.md` and `test-design-decision-table.md` split
  numeric invalid classes into class-level rows/decisions. A row such as
  `letters; decimal-separator; sign; spaces; special-chars` linked to several
  `TC-*` IDs is a regression even if the canonical TC sections themselves are
  split;
- `dependency-matrix.md` is present for the companion cycle when dependency is
  applicable and records controlling values/actions, dependent fields,
  expected branches and TC/GAP links;
- the scoped profile for v18 has `unresolved_warning_error_count = 0`;
- `codex_review_cycle_runner.py doctor --state <v18 cycle-state.yaml>` reports
  `stage_status: writer-draft-ready`,
  `events.scoped_validator_profile_consistency.consistent = true`, and
  `recommendation: run-next-stage`;

## Fail Criteria

This regression fails if any of these happen:

- v17 reaches `writer-draft-ready`, `semantic-review-ready`, or `signed-off`
  while the two scoped validator warnings remain open;
- v18 or its successor reaches `semantic-review-ready` or `signed-off` while
  numeric-format PDP/TDDT rows still merge independent invalid classes such as
  letters, decimal separators, signs, spaces and special characters in one
  executable design row/decision;
- v18 or its successor introduces artificial numeric property types such as
  `numeric-format-invalid`, `numeric-negative` or `non-digit-rejection` in
  Source Table Normalization, TDDT, or Coverage Obligation Table instead of
  preserving the original `numeric-format` source property and expressing
  invalid inputs through class-level obligations;
- the validator accepts field clearing / not-displayed / filtering behavior as a
  deterministic oracle based only on a numeric-only or rejection source rule;
- the writer marks `package-ready = pass` while scoped validator warnings are
  unresolved;
- `runner-events.ndjson` reports a different unresolved count than the scoped
  profile without `doctor` surfacing the drift.

## Non-Goals

- Do not rewrite v17 TC into a clean set as part of this regression. The open
  warnings are the test fixture.
- Do not make every historical canary pass the new validator rules.
- Do not infer a UI validation mechanism from source wording that only defines
  the invalid value class.
- Do not treat the clean companion cycle as a full employment-section coverage
  run; it is a targeted check for corrected numeric feedback and invalid-class
  handling.

## V18 R2 Addendum

The `ui-employment-canary-v18-numeric-feedback-clean-regression` semantic R2
cycle reached `round-cap-reached` with `FINDING-008`: canonical TC sections were
split by numeric invalid class, but `Package Test Design Plan` rows `PD-007` /
`PD-011` and TDDT rows `TDD-008` / `TDD-012` still compressed multiple invalid
classes into one design row/decision.

This is now locked by validator findings:

- `test-case-package-design-plan-merged-numeric-class-row`;
- `test-design-decision-table-merged-numeric-class-decision`.

Targeted tests:

- `tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_numeric_format_plan_and_tddt_reject_merged_invalid_class_rows`;
- `tests.test_agent_artifact_validator.AgentArtifactValidatorTests.test_numeric_format_plan_and_tddt_allow_split_invalid_class_rows`;
- `tests.test_codex_review_cycle_runner.CodexReviewCycleRunnerTests.test_writer_ready_gate_rejects_merged_numeric_class_artifact_warnings`.

## V20 Addendum

The `ui-employment-canary-v20-negative-oracle-recovery-regression` recovery run
shows a second-order writer failure: after `не отображается` / `не принято`
was rejected as unsupported numeric enforcement, the writer replaced it with
another unsupported mechanism: red highlighting plus blocked navigation for
numeric invalid classes.

This must remain a writer-instruction regression, not only a validator
regression. A valid remediation must either cite direct source/UI/support
evidence for the exact feedback mechanism or keep the feedback mechanism as a
narrow `GAP-*` / `unclear` while preserving the invalid class in design
artifacts.

Additional fail criteria:

- writer response marks `test-case-unsupported-input-filtering-oracle-smell` as
  fixed by changing the expected result to red highlight, error message,
  blocked transition, or `Анкета клиента` not opening without new evidence;
- writer-ready handoff proceeds while
  `test-case-unsupported-numeric-validation-feedback-smell` remains in the
  current-scope validator profile;
- `Writer Quality Gate` claims `tc-regression-smells = pass` when numeric
  invalid TC still depend on unsupported UI feedback.

## V24 Addendum

The `ui-employment-canary-v24-agent-fixes` run in `fts/ft-2-OF_17` exposed a
taxonomy regression: the writer avoided some unsupported UI-feedback oracles,
but created artificial source/design property types named
`numeric-format-invalid` for non-digit classes.

The corrected design must keep the source property as `numeric-format` and use
Coverage Obligation Table class rows for invalid inputs:

- `valid-digits`;
- `reject-letters`;
- `reject-spaces`;
- `reject-special-chars`;
- `reject-decimal-separator`;
- `reject-sign`.

Unsupported invalid-class UI reactions must map to source-specific `GAP-*`
rows. They must not become separate source properties such as
`SRC-*.P04 numeric-format-invalid`.

This is now locked by validator findings:

- `source-normalization-artificial-numeric-property-type`;
- `test-design-decision-table-artificial-numeric-property-type`;
- `coverage-obligation-table-artificial-numeric-property-type`.

Canary command used for the regression check:

```powershell
python scripts\validate_agent_artifacts.py --root fts\ft-2-OF_17\test-cases\2-1-1-1-1-2-ui-employment-canary-v24-agent-fixes.md --json --fail-on warning
```

Expected current result for v24: fail. The failure is intentional evidence that
the v24 artifact still contains the artificial taxonomy and should not be used
as a clean companion cycle.

## V25 Addendum

The `ui-employment-canary-v25-numeric-taxonomy-clean` companion in
`fts/ft-2-OF_17` narrows the v24 taxonomy failure without claiming full writer
readiness:

- Source Table Normalization no longer creates separate rows such as
  `SRC-EMP-002.P04 numeric-format-invalid` or
  `SRC-EMP-006.P03 numeric-format-invalid`;
- invalid numeric classes are represented in Coverage Obligation Table rows
  under the original `numeric-format` source properties
  `SRC-EMP-002.P02` and `SRC-EMP-006.P02`;
- TDDT no longer contains `numeric-format-invalid` decisions.

Validation command:

```powershell
python scripts\validate_agent_artifacts.py --root fts\ft-2-OF_17\test-cases\2-1-1-1-1-2-ui-employment-canary-v25-numeric-taxonomy-clean.md --json --fail-on warning
```

Expected current result for v25: fail, but not because of the artificial
numeric taxonomy. Remaining warnings belong to older canary defects such as
coverage-table scope, applicability-matrix vocabulary, TDDT/ledger sync,
artifact-write strategy and writer gates. The regression check passes only for
the specific taxonomy condition when the validator output does not contain:

- `source-normalization-artificial-numeric-property-type`;
- `test-design-decision-table-artificial-numeric-property-type`;
- `coverage-obligation-table-artificial-numeric-property-type`;
- `coverage-obligation-table-missing-required-class` for
  `SRC-EMP-002.P02` or `SRC-EMP-006.P02`.
