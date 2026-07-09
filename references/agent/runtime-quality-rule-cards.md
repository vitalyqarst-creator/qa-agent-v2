# Runtime Quality Rule Cards

Compact runtime index only. Detailed examples stay in validator tests, evals and deep references.

| rule_id | trigger | required action | validator gate |
|---|---|---|---|
| R-CANDIDATE-NEG | visible source-backed input restriction + missing UI rejection oracle | write candidate-negative TC with concrete invalid value; BA question may accompany but not replace TC | `source-backed-input-restriction-gap-only`, `test-case-ui-calibration-candidate-missing-concrete-invalid-value` |
| R-ROLLING-DATE | current date, future date, not later than current date | use `D` current app date and `D + 1 calendar day`; fixed date only as example | `rolling-date-boundary-static-test-data` |
| R-ATOMICITY | TC references more than two independent source-backed obligations (`ATOM`/`BSR`/`GSR`/`REQ`) | split, or add explicit `Сценарное обоснование` only when one user workflow is source-backed and atomic coverage remains traceable elsewhere | `test-case-overmerged-atoms-without-rationale`, `test-case-excessive-atom-fan-in` |
| R-SCENARIO-RATIONALE | grouped/source-backed TC has scenario rationale | use canonical `**Сценарное обоснование:**`; rationale must name the tested field/block/source rows and must not be copied from another domain | `scenario-rationale-noncanonical-field`, `scenario-rationale-domain-mismatch`, `scenario-rationale-too-generic` |
| R-REPRESENTATIVE | similar fields/classes share restriction and only some combinations are tested | document representative/pairwise strategy, selected combinations, omitted combinations and residual risk | `missing-representative-strategy`, `representative-strategy-without-omitted-combinations`, `representative-strategy-without-residual-risk` |
| R-SOURCE-BASIS | old/generated canary artifact is used during v3 decisions | use it only as diagnostic failure fixture; cite FT source rows/BSR for decisions | `generated-artifact-used-as-source-of-truth` |
| R-INLINE-PRECONDITIONS | production TC under `fts/**/test-cases/*.md` | full inline action-oriented preconditions; no setup profile, stand, environment or package leakage | `production-setup-profile-reference`, precondition smells |
| R-CONCRETE-DATA | every executable TC | concrete test data or explicit calculation formula | `test-case-generic-test-data-reference-smell`, `test-case-generic-test-data-oracle-smell` |
| R-TITLE-METADATA | candidate, calibration or process status exists | keep process markers out of `Title`; put candidate status in TC body metadata | `test-case-title-process-marker-smell` |
| R-PRODUCTION-MARKDOWN | production TC under `fts/**/test-cases/*.md` | keep every `## TC-*` heading and runtime metadata field at line start | `production-markdown-heading-not-at-line-start`, `production-metadata-field-not-at-line-start` |

Runtime rule cards do not replace semantic review. They only keep high-risk gates visible when a scenario intentionally avoids deep references.
