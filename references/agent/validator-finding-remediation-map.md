# Validator Finding Remediation Map

Default validator remediation is finding-targeted. Read the validator finding id, edit only affected TC/artifact rows, rerun the same validator command, and do not rewrite unaffected TC.

| finding_id | compact action | deep reference / optional scenario |
|---|---|---|
| `source-backed-input-restriction-gap-only` | Add candidate-negative TC with a concrete invalid value and `ui-calibration-required`, or prove the restriction is non-UI/internal. | `references/agent/negative-ui-calibration-policy.md` |
| `test-case-ui-calibration-candidate-missing-concrete-invalid-value` | Add a concrete representative invalid value to candidate UI calibration TC. | `references/agent/negative-ui-calibration-policy.md` |
| `rolling-date-boundary-static-test-data` | Replace fixed date-only test data with `D` / `D + 1 calendar day` formula; fixed dates may remain examples only. | `references/qa/coverage-input-boundaries.md` |
| `rolling-date-boundary-unformalized-relative-value` | Define `D`, state the output format, include an example value, and assert the calculated value instead of a raw relative placeholder. | `references/qa/coverage-input-boundaries.md` |
| `test-case-overmerged-atoms-without-rationale` | Split independent obligations or add source-backed scenario rationale and keep atomic checks elsewhere. | `references/qa/test-design-review-rubric.md` |
| `test-case-excessive-atom-fan-in` | Split high fan-in TC or document why one user workflow is the intended scenario container. | `references/qa/test-design-review-rubric.md` |
| `scenario-rationale-noncanonical-field` | Rename the field to `**Сценарное обоснование:**`; do not change TC split unless another finding requires it. | `references/qa/test-design-review-rubric.md` |
| `scenario-rationale-domain-mismatch` | Replace copied/unrelated rationale with a field/block-specific source-backed grouping reason. | `references/qa/test-design-review-rubric.md` |
| `scenario-rationale-too-generic` | Add concrete target, source rows/codes and statement that independent checks remain covered elsewhere. | `references/qa/test-design-review-rubric.md` |
| `scenario-rationale-stimulus-mismatch` | Rewrite title/rationale to match the exercised stimulus, or split visibility/default-state and input/selection checks. | `references/agent/runtime-quality-rule-cards.md` |
| `missing-representative-strategy` | Document representative/pairwise strategy, selected combinations, omitted combinations and residual risk. | `references/agent/coverage-obligation-table-format.md` |
| `representative-strategy-without-omitted-combinations` | Add omitted/excluded field-class combinations, or add the missing TC/GAP rows. | `references/agent/coverage-obligation-table-format.md` |
| `representative-strategy-without-residual-risk` | Add explicit residual risk, or replace the representative shortcut with full TC/GAP coverage. | `references/agent/coverage-obligation-table-format.md` |
| `tc-type-expected-result-mismatch` | Change TC type to Negative / Validation Negative or split/add a positive pair. | `references/qa/test-design-review-rubric.md` |
| `trace-not-exercised-by-steps` | Remove unexercised trace or split/add a TC that actually exercises that source behavior. | `references/qa/test-design-review-rubric.md` |
| `multiple-independent-assertions-in-one-tc` | Split independent dictionary, branch, action or persistence assertions into separate TC. | `references/qa/test-design-review-rubric.md` |
| `representative-strategy-data-mismatch` | Align representative strategy with concrete test data or change data to match the stated class. | `references/agent/coverage-obligation-table-format.md` |
| `production-artifact-internal-language-leak` | Replace internal English strategy labels with Russian production labels or move details to work artifacts. | `references/qa/test-case-format.md` |
| `candidate-negative-validation-trigger-missing` | Add a neutral completion/focus/validation/save trigger or a BA question about trigger selection. | `references/agent/negative-ui-calibration-policy.md` |
| `candidate-negative-trigger-too-specific` | Replace blur/focus-only trigger wording with focus loss or another available validation action; record exact trigger during UI calibration. | `references/agent/negative-ui-calibration-policy.md` |
| `sampled-field-group-without-group-strategy` | Add explicit sampled-field group strategy for the affected field family. | `references/agent/coverage-obligation-table-format.md` |
| `coverage-matrix-tc-domain-mismatch` | Move mismatched TC ids to the correct representative group or fix the group label/source rows. | `references/agent/coverage-obligation-table-format.md` |
| `persist-coverage-missing-for-crud-scope` | Add save/persist smoke coverage plan or explicit out-of-scope rationale. | `references/qa/test-design-review-rubric.md` |
| `field-level-canary-without-persistence-scope-note` | Add explicit field-level/risk-based scope and persistence follow-up/out-of-scope note to the canary evaluation report. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-tc-without-save-action` | Add a source-backed save action, or mark the save step as requiring BA/UI confirmation if the exact action is unknown. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-tc-without-reopen-verification` | Close/leave/reload, reopen the same card, and verify the saved value after reopen. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-tc-closes-without-saving` | Save and verify persisted data before cleanup; do not use close-without-saving as a persistence TC exit path. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-tc-unsourced-save-action` | Cite the save action source or replace the concrete save control with a confirmation-required save step. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-smoke-without-cleanup-strategy` | Add cleanup/isolation postconditions so saved smoke data does not silently remain in the application. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-trace-not-exercised` | Remove the unexercised BSR from primary trace, move it to supporting/setup notes, or add a TC that directly exercises it. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-precondition-passive-state` | Rewrite preconditions as action-oriented setup steps that open/navigate/create/verify the required state. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-delete-tc-not-self-contained` | Create and save the entity in setup, reopen and verify it exists, then delete/save/reopen; or cite a defined fixture. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-grouped-smoke-without-residual-risk` | Add explicit grouped-smoke rationale and residual risk, or split the grouped check into atomic persistence TC. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-candidate-without-calibration-questions` | Link candidate persistence TC to BA/UI calibration question IDs or add the persistence save-flow calibration package. | `references/agent/runtime-quality-rule-cards.md` |
| `executable-persistence-with-unconfirmed-save-flow` | Restore `candidate-persistence-calibration` or add source-backed/BA-confirmed save action, save success oracle, exit/reopen flow and cleanup evidence. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-save-placeholder-in-executable-tc` | Replace placeholder save wording with the confirmed exact action or restore candidate calibration status. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-calibration-package-missing` | Add the four files under `work/calibration/persistence-save-flow/`: questions, conversion plan, checklist and evaluation report. | `references/agent/runtime-quality-rule-cards.md` |
| `persistence-terminology-source-mismatch` | Normalize relation-field wording to the source-backed term or add an explicit terminology mapping. | `references/agent/runtime-quality-rule-cards.md` |
| `source-backed-ui-term-inconsistency` | Normalize to the source-backed UI block term for the active section or document a source/appended-term naming decision. | `references/agent/runtime-quality-rule-cards.md` |
| `generated-artifact-used-as-source-of-truth` | Treat old generated artifacts only as diagnostic fixtures; cite source rows/BSR/FT artifacts for decisions. | `references/agent/source-row-inventory-format.md` |
| `production-setup-profile-reference` | Replace production setup profile/stand/environment leakage with inline action-oriented preconditions. | `references/qa/test-case-format.md` |
| `test-case-generic-test-data-reference-smell` | Put concrete literal, fixture value or formula in test data and reference it in the step. | `references/qa/test-case-format.md` |
| `test-case-generic-test-data-oracle-smell` | Name the checked concrete value and observable result directly in expected result. | `references/qa/test-case-format.md` |
| `test-case-title-process-marker-smell` | Move process status from title to TC body metadata/status fields. | `references/agent/style-remediation-checklist.md` |
| `production-markdown-heading-not-at-line-start` | Move the `## TC-*` heading to the start of its own line; preserve TC content. | `references/qa/test-case-format.md` |
| `production-metadata-field-not-at-line-start` | Move the runtime metadata field to the start of its own line; preserve field text. | `references/qa/test-case-format.md` |

If a finding id is not listed, use the compact rule cards first. Load `writer.remediation.validator_failure.deep_debug` only when the compact map does not give enough information to make a bounded patch.
