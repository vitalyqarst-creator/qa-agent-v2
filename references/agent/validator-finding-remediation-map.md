# Validator Finding Remediation Map

Default validator remediation is finding-targeted. Read the validator finding id, edit only affected TC/artifact rows, rerun the same validator command, and do not rewrite unaffected TC.

| finding_id | compact action | deep reference / optional scenario |
|---|---|---|
| `source-backed-input-restriction-gap-only` | Add candidate-negative TC with a concrete invalid value and `ui-calibration-required`, or prove the restriction is non-UI/internal. | `references/agent/negative-ui-calibration-policy.md` |
| `test-case-ui-calibration-candidate-missing-concrete-invalid-value` | Add a concrete representative invalid value to candidate UI calibration TC. | `references/agent/negative-ui-calibration-policy.md` |
| `rolling-date-boundary-static-test-data` | Replace fixed date-only test data with `D` / `D + 1 calendar day` formula; fixed dates may remain examples only. | `references/qa/coverage-input-boundaries.md` |
| `test-case-overmerged-atoms-without-rationale` | Split independent obligations or add source-backed scenario rationale and keep atomic checks elsewhere. | `references/qa/test-design-review-rubric.md` |
| `test-case-excessive-atom-fan-in` | Split high fan-in TC or document why one user workflow is the intended scenario container. | `references/qa/test-design-review-rubric.md` |
| `missing-representative-strategy` | Document representative/pairwise strategy, selected combinations, omitted combinations and residual risk. | `references/agent/coverage-obligation-table-format.md` |
| `representative-strategy-without-omitted-combinations` | Add omitted/excluded field-class combinations, or add the missing TC/GAP rows. | `references/agent/coverage-obligation-table-format.md` |
| `representative-strategy-without-residual-risk` | Add explicit residual risk, or replace the representative shortcut with full TC/GAP coverage. | `references/agent/coverage-obligation-table-format.md` |
| `production-setup-profile-reference` | Replace production setup profile/stand/environment leakage with inline action-oriented preconditions. | `references/qa/test-case-format.md` |
| `test-case-generic-test-data-reference-smell` | Put concrete literal, fixture value or formula in test data and reference it in the step. | `references/qa/test-case-format.md` |
| `test-case-generic-test-data-oracle-smell` | Name the checked concrete value and observable result directly in expected result. | `references/qa/test-case-format.md` |
| `test-case-title-process-marker-smell` | Move process status from title to TC body metadata/status fields. | `references/agent/style-remediation-checklist.md` |

If a finding id is not listed, use the compact rule cards first. Load `writer.remediation.validator_failure.deep_debug` only when the compact map does not give enough information to make a bounded patch.
