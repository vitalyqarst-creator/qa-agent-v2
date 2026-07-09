# Independent Wide Canary v4 Evaluation Report

## Purpose

This v4 run preserves the original v3 artifact as a diagnostic failure fixture and creates a corrected production-style artifact for section 4.3 client addresses and contacts.

## Human Review Findings Captured

| Finding id | v4 remediation |
|---|---|
| `tc-type-expected-result-mismatch` | TC-AF43-AW4-003 is negative; positive address representatives moved to TC-AF43-AW4-029. |
| `trace-not-exercised-by-steps` | TC-AF43-AW4-018 traces only home-phone deletion; work-phone deletion added as TC-AF43-AW4-030. |
| `multiple-independent-assertions-in-one-tc` | TC-AF43-AW4-024 checks relation dictionary values only; `Иное` branch moved to TC-AF43-AW4-031. |
| `representative-strategy-data-mismatch` | TC-AF43-AW4-020 no longer exposes internal strategy bullets whose examples conflict with test data. |
| `production-artifact-internal-language-leak` | Representative strategy is kept in `coverage-matrix.md`, not in production TC text. |
| `candidate-negative-validation-trigger-missing` | Candidate UI-calibration negative TC include a neutral trigger step: finish input and move focus to initiate available UI validation. |
| `sampled-field-group-without-group-strategy` | Coverage matrix now includes group strategy rows for postal indexes, phones, e-mail restrictions and contact-person FIO. |
| `persist-coverage-missing-for-crud-scope` | Save/persistence is explicitly tracked as a separate smoke plan instead of being implied by field-level TC. |

## TC Counts

| Metric | Count |
|---|---:|
| Total TC | 31 |
| Positive TC | 18 |
| Negative TC | 2 |
| Candidate-negative TC | 11 |

## Candidate-Negative Coverage

Candidate-negative TC now cover source-backed visible input restrictions for postal index overlength, invalid e-mail format, phone length, contact-person FIO digit/special-symbol restrictions and contact-person phone overlength. Each candidate-negative TC has a concrete invalid representative value, UI calibration status, confirmation requirement and neutral validation trigger.

## Remaining Gaps

`GAP-AW4-001` remains for address source ambiguity, `GAP-AW4-002` for exact phone UI rejection mechanics, `GAP-AW4-003` for closed-set relation ambiguity and `GAP-AW4-004` for exact UI rejection mechanics for contact-person FIO. These gaps are allowed because they do not replace visible source-backed negative coverage; they record oracle calibration or source ambiguity.

## Save / Persistence Coverage Plan

The v4 artifact is still a section 4.3 field-level canary. Save/persistence is not asserted by invalid-value candidate TC. A follow-up smoke should save one valid representative edit in the application card, reopen the card and verify persisted values for one address field, one phone field and one contact-person field.

## Validation Summary

Strict validator routing treats v3 human-review defects as test-design findings. The v4 artifact is expected to pass strict canary validation with zero errors; any persistence item remains a warning unless the scope claims end-to-end save behavior.
