# Runtime Quality Rule Cards

| rule_id | trigger | required action | validator gate |
|---|---|---|---|
| R-CANDIDATE-NEG | visible source-backed input restriction, missing UI rejection oracle | write candidate-negative TC with concrete invalid value; BA gap may accompany, not replace | `source-backed-input-restriction-gap-only`, `test-case-ui-calibration-candidate-missing-concrete-invalid-value` |
| R-ROLLING-DATE | current/future/not-later-than-current/relative date | use `D`; fixed date only as example; define `D`, format and example for relative values | `rolling-date-boundary-static-test-data`, `rolling-date-boundary-unformalized-relative-value` |
| R-ATOMICITY | TC traces >2 independent `ATOM`/`BSR`/`GSR`/`REQ` obligations | split, or justify one source-backed workflow via `Сценарное обоснование` with atomic coverage elsewhere | `test-case-overmerged-atoms-without-rationale`, `test-case-excessive-atom-fan-in` |
| R-SCENARIO-RATIONALE | grouped/source-backed TC | canonical `**Сценарное обоснование:**`; name target/source rows; match exercised stimulus | `scenario-rationale-noncanonical-field`, `scenario-rationale-domain-mismatch`, `scenario-rationale-too-generic`, `scenario-rationale-stimulus-mismatch` |
| R-REPRESENTATIVE | sampled similar fields/classes | document strategy, selected/omitted combinations and residual risk | `missing-representative-strategy`, `representative-strategy-without-omitted-combinations`, `representative-strategy-without-residual-risk` |
| R-TC-TYPE | type conflicts with expected result | Positive only for acceptance; validation/error oracle => Negative / Validation Negative | `tc-type-expected-result-mismatch` |
| R-TRACE-EXERCISED | trace names source fields/actions | traced behavior is exercised or explicitly supporting | `trace-not-exercised-by-steps` |
| R-ONE-ASSERTION | TC proves independent assertions | split dictionary/branch/action/persistence checks unless rationale applies | `multiple-independent-assertions-in-one-tc` |
| R-REP-DATA | strategy states selected classes | strategy and coverage matrix match concrete values/domains/classes | `representative-strategy-data-mismatch`, `sampled-field-group-without-group-strategy`, `coverage-matrix-tc-domain-mismatch` |
| R-NEG-TRIGGER | candidate-negative invalid input | include neutral completion/focus/validation/save trigger or trigger BA question | `candidate-negative-validation-trigger-missing`, `candidate-negative-trigger-too-specific` |
| R-PERSISTENCE-COVERAGE | editable CRUD/card scope | save/reopen smoke or rationale; save, reopen, verify; exercised trace; reproducible setup; grouped residual risk | `persist-coverage-missing-for-crud-scope`, `field-level-canary-without-persistence-scope-note`, `persistence-tc-without-save-action`, `persistence-tc-without-reopen-verification`, `persistence-tc-closes-without-saving`, `persistence-tc-unsourced-save-action`, `persistence-smoke-without-cleanup-strategy`, `persistence-trace-not-exercised`, `persistence-precondition-passive-state`, `persistence-delete-tc-not-self-contained`, `persistence-grouped-smoke-without-residual-risk` |
| R-SOURCE-UI-TERMS | section UI block names | use source-backed term or document naming decision | `source-backed-ui-term-inconsistency` |
| R-SOURCE-BASIS | old/generated canary used in v3 decisions | diagnostic fixture only; cite FT rows/BSR | `generated-artifact-used-as-source-of-truth` |
| R-INLINE-PRECONDITIONS | production TC | inline action-oriented preconditions; no setup profile/stand/env leakage | `production-setup-profile-reference`, precondition smells |
| R-CONCRETE-DATA | executable TC | concrete data or formula | `test-case-generic-test-data-reference-smell`, `test-case-generic-test-data-oracle-smell` |
| R-TITLE-METADATA | candidate/calibration/process status | keep process markers out of `Title`; put status in body metadata | `test-case-title-process-marker-smell` |
| R-PRODUCTION-MARKDOWN | production TC markdown | `## TC-*` and metadata fields start their own lines | `production-markdown-heading-not-at-line-start`, `production-metadata-field-not-at-line-start` |
