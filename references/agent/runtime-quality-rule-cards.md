# Runtime Quality Rule Cards

Compact runtime index only. Detailed examples stay in validator tests, evals and deep references.

| rule_id | trigger | required action | validator gate |
|---|---|---|---|
| R-CANDIDATE-NEG | visible source-backed input restriction + missing UI rejection oracle | write candidate-negative TC with concrete invalid value; BA question may accompany but not replace TC | `source-backed-input-restriction-gap-only`, `test-case-ui-calibration-candidate-missing-concrete-invalid-value` |
| R-ROLLING-DATE | current date, future date, not later than current date | use `D` current app date and `D + 1 calendar day`; fixed date only as example | `rolling-date-boundary-static-test-data` |
| R-ATOMICITY | TC covers multiple independent obligations | split, or add explicit scenario rationale only when one user workflow is source-backed | `test-case-overmerged-atoms-without-rationale`, `test-case-excessive-atom-fan-in` |
| R-REPRESENTATIVE | similar fields share restriction and only some are tested | document representative/pairwise strategy and residual risk | `missing-representative-strategy` |
| R-INLINE-PRECONDITIONS | production TC under `fts/**/test-cases/*.md` | full inline action-oriented preconditions; no setup profile, stand, environment or package leakage | `production-setup-profile-reference`, precondition smells |
| R-CONCRETE-DATA | every executable TC | concrete test data or explicit calculation formula | `test-case-generic-test-data-reference-smell`, `test-case-generic-test-data-oracle-smell` |
| R-TITLE-METADATA | candidate, calibration or process status exists | keep process markers out of `Title`; put candidate status in TC body metadata | `test-case-title-process-marker-smell` |

Runtime rule cards do not replace semantic review. They only keep high-risk gates visible when a scenario intentionally avoids deep references.
