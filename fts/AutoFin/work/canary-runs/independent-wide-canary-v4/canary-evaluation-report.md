# Independent Wide Canary v4 Evaluation Report

## Purpose

This v4 run preserves the original v3 artifact as a diagnostic failure fixture and creates a corrected field-level / risk-based canary artifact for section 4.3 client addresses and contacts. It is not a full production regression suite for every persistence, integration and cartesian field-combination obligation in section 4.3.

## Human Review Findings Captured

| Finding id | v4 remediation |
|---|---|
| `tc-type-expected-result-mismatch` | TC-AF43-AW4-003 is negative; positive address representatives moved to TC-AF43-AW4-029. |
| `trace-not-exercised-by-steps` | TC-AF43-AW4-018 traces only home-phone deletion; work-phone deletion added as TC-AF43-AW4-030. |
| `multiple-independent-assertions-in-one-tc` | TC-AF43-AW4-024 checks relation dictionary values only; `Иное` branch moved to TC-AF43-AW4-031. |
| `representative-strategy-data-mismatch` | TC-AF43-AW4-020 no longer exposes internal strategy bullets whose examples conflict with test data. |
| `production-artifact-internal-language-leak` | Representative strategy is kept in `coverage-matrix.md`, not in production TC text. |
| `candidate-negative-validation-trigger-missing` | Candidate UI-calibration negative TC include a neutral trigger step: finish input through focus change or another available validation action; exact trigger remains UI-calibration-required. |
| `sampled-field-group-without-group-strategy` | Coverage matrix now includes verified group strategy rows for postal indexes, phones, e-mail restrictions, contact-person FIO, birth-date boundary and address composition. |
| `persist-coverage-missing-for-crud-scope` | Save/persistence is explicitly tracked as a separate smoke plan instead of being implied by field-level TC. |

## Design Polish Repair Pass

| Item | Result |
|---|---|
| Header metadata | Fixed diagnostic materials label from `v2` to `v4`. |
| `TC-AF43-AW4-001` | Rationale now matches the DaData selection scenario: input, suggestion selection and displayed selected registration address. |
| `TC-AF43-AW4-008` | Title and rationale now describe one scenario: residence address field appears when it differs from registration address and accepts selected DaData address. |
| `TC-AF43-AW4-020` | Rationale now matches data: surname and first name contain letters plus hyphen, patronymic contains letters. |
| Candidate-negative trigger wording | Updated to avoid assuming blur-only validation; confirmation now records both UI mechanism and trigger. |
| Coverage matrix | Representative groups were checked and fixed so postal, phone, e-mail, FIO, date and address groups reference matching TC/BSR domains. |

## TC Counts

| Metric | Count |
|---|---:|
| Total TC | 31 |
| Positive TC | 18 |
| Negative TC | 2 |
| Candidate-negative TC | 11 |

## Candidate-Negative Coverage

Candidate-negative TC now cover source-backed visible input restrictions for postal indexes, invalid e-mail format, phone value classes, contact-person FIO digit/special-symbol restrictions, contact-person phone value classes and future birth-date boundary. Each candidate-negative TC has a concrete invalid representative value, UI calibration status, confirmation requirement and neutral trigger wording that does not assume a blur-only validation mechanism.

## Remaining Gaps

`GAP-AW4-001` remains for address source ambiguity, `GAP-AW4-002` for exact phone UI rejection mechanics, `GAP-AW4-003` for closed-set relation ambiguity and `GAP-AW4-004` for exact UI rejection mechanics for contact-person FIO. These gaps are allowed because they do not replace visible source-backed negative coverage; they record oracle calibration or source ambiguity.

## Save / Persistence Coverage Plan

The v4 artifact is a field-level / risk-based canary, not a full persistence suite. Save/persistence coverage is out of scope for this v4 artifact and must be handled by a separate follow-up smoke suite. That follow-up should save one valid representative edit in the application card, reopen the card and verify persisted values for one address field, one phone field and one contact-person field.

## Validation Summary

Strict validator routing treats v3 human-review defects as test-design findings. The v4 artifact is expected to pass strict canary validation with zero errors; persistence remains a documented follow-up/out-of-scope item unless a later suite claims end-to-end save behavior.
