# Independent Wide Canary V3 Evaluation Report

## Run Contract

| item | value |
| --- | --- |
| branch | `audit/stabilize-testcase-agent-atomicity-coverage-fixes` |
| original_failure_fixture_modified | `no` |
| generated_tc_artifact | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary-v3.md` |
| work_dir | `fts/AutoFin/work/canary-runs/independent-wide-canary-v3/` |
| source_basis | `FT4AutoFinFinal.xhtml`, `FT4AutoFinFinal.docx`, package `AGENT-NOTES.md` |
| old_independent_wide_canary_role | diagnostic failure fixture only |

## Counts

| metric | count |
| --- | ---: |
| total_tc | 28 |
| positive_tc | 16 |
| negative_tc_exact_oracle | 1 |
| candidate_negative_tc | 11 |

## Candidate-Negative Coverage

| restriction | requirement | candidate_tc | representative_invalid_value |
| --- | --- | --- | --- |
| Registration postal index: only six numeric chars | `BSR 124` | `TC-AF43-AW3-005` | `66000A` |
| Residence postal index: only six numeric chars | `BSR 161` | `TC-AF43-AW3-010` | `66001` |
| Client mobile phone: only ten numeric chars | `BSR 163` | `TC-AF43-AW3-012` | `92345A7890` |
| E-mail must contain `@` | `BSR 166` | `TC-AF43-AW3-014` | `ivanov.example.ru` |
| E-mail allows only one address | `BSR 166` | `TC-AF43-AW3-015` | `ivanov@example.ru; petrov@example.ru` |
| Work phone: only ten numeric chars | `BSR 169` | `TC-AF43-AW3-017` | `93456789012` |
| Contact surname: text symbols and hyphen only | `BSR 174` | `TC-AF43-AW3-021` | `Иванов1` |
| Contact first name: text symbols and hyphen only | `BSR 176` | `TC-AF43-AW3-022` | `Ан@на` |
| Contact patronymic: text symbols and hyphen only | `BSR 178` | `TC-AF43-AW3-023` | `Сергеевна2` |
| Contact phone: only ten numeric chars | `BSR 182` | `TC-AF43-AW3-026` | `94567A9012` |
| Contact birth date cannot be greater than current date | `BSR 185` | `TC-AF43-AW3-028` | `D + 1 calendar day`; example `10.07.2026` when `D = 09.07.2026` |

## Date Boundary Follow-up

| item | result |
| --- | --- |
| defect found | `TC-AF43-AW3-028` used static future date `10.07.2026`; after that calendar date it would no longer be future. `TC-AF43-AW3-027` claimed current-date boundary coverage while using stable past date `10.01.1985`. |
| TC-AF43-AW3-027 | Now checks positive boundary `D`, where `D` is the current application date at test execution, with `DD.MM.YYYY` format and example. |
| TC-AF43-AW3-028 | Now checks candidate-negative boundary `D + 1 calendar day`, keeps `ui-calibration-required` / `candidate-ui-calibration`, and asks UI calibration to record rejection mechanism plus current-date source. |
| BA question | Added `BAQ-DATE-CURRENT-SOURCE` for `BSR 185`, `TC-AF43-AW3-027`, `TC-AF43-AW3-028`. |

## Residual Gaps

| gap_id | why_allowed |
| --- | --- |
| `GAP-AW3-001` | Internal/model `kladr` verification is not observable in selected UI scope without API/DB/log evidence. |
| `GAP-AW3-002` | Default-hidden phone widget labels and exact initial UI state require UI evidence; add/delete behavior is covered. |
| `GAP-AW3-003` | Source lists relation values but does not explicitly assert closed-set exclusivity. |
| GAP-AW3-004 | Parent BA question for exact UI rejection mechanism; all visible invalid input classes have candidate-negative TC coverage. |

## Atomicity And Representative Coverage

| item | result |
| --- | --- |
| v2 diagnostic role | V2 remains unchanged and fails strict atomicity coverage because multiple TC reference more than two independent source-backed obligations without scenario rationale. |
| v3 atomicity fix | V3 adds `Scenario rationale` only where one visible source-backed workflow justifies grouping; independent invalid classes stay in separate candidate-negative TC. |
| FIO representative strategy | `TC-AF43-AW3-020` and `coverage-matrix.md` state selected combinations, omitted combinations and residual risk for the shared surname/first-name/patronymic restriction. |
| positive allowed-class coverage | Positive allowed-class TC are retained, including `TC-AF43-AW3-020` for FIO and positive phone/postal/email/date cases. |
| candidate-negative coverage | Visible source-backed input restrictions still have candidate-negative TC with concrete invalid values and UI calibration markers. |

## Validator Evidence

| command | result |
| --- | --- |
| `python -m py_compile scripts\validate_agent_artifacts.py` | pass |
| `python -m pytest tests\test_agent_artifact_validator.py -k "source_backed_input_restriction_gap_only or gap_only_visible_input_restriction or representative_strategy or overmerged_source_backed or partial_similar_field_coverage"` | pass; 11 passed |
| `python scripts\validate_agent_artifacts.py --root fts\AutoFin\test-cases\4.3-application-card-client-addresses-contacts-independent-wide-canary-v2.md --json --atomicity-coverage-policy strict-canary --fail-on error` | expected fail; 2 errors: `test-case-excessive-atom-fan-in`, `test-case-overmerged-atoms-without-rationale` |
| `python scripts\validate_agent_artifacts.py --root fts\AutoFin\test-cases\4.3-application-card-client-addresses-contacts-independent-wide-canary-v3.md --json --input-restriction-gap-policy strict-canary --rolling-date-boundary-policy strict-canary --atomicity-coverage-policy strict-canary --fail-on error` | pass; 0 errors |
| `python scripts\validate_agent_artifacts.py --root fts\AutoFin\work\canary-runs\independent-wide-canary-v3 --json --input-restriction-gap-policy strict-canary --rolling-date-boundary-policy strict-canary --atomicity-coverage-policy strict-canary --fail-on error` | pass; 0 errors |
| `python scripts\run_tests.py --suite architecture` | pass; 0 findings |
| `python scripts\run_tests.py --suite agent-layer-fast` | pass; 215 tests, 1 skipped |
| `python scripts\run_tests.py --suite artifact-validator-sharded` | pass; 329 tests across 7 shards |
| `git diff --check` | pass |

## Severity Behavior

| profile / policy | `source-backed-input-restriction-gap-only` severity | sign-off impact |
| --- | --- | --- |
| `compatible` | `warning` | diagnostic only |
| `diagnostic` | `warning` | diagnostic only |
| `strict-canary` | `error` | fails `--fail-on error` |
| `writer-final` | `error` | fails `--fail-on error` |
| `production` | `error` | fails `--fail-on error` |

## Atomicity / Representative Severity

| profile / policy | findings | severity | sign-off impact |
| --- | --- | --- | --- |
| `compatible` | `test-case-overmerged-atoms-without-rationale`, `test-case-excessive-atom-fan-in`, `missing-representative-strategy`, `representative-strategy-without-omitted-combinations`, `representative-strategy-without-residual-risk` | `warning` | diagnostic only |
| `diagnostic` | same | `warning` | diagnostic only |
| `strict-canary` | same | `error` | fails `--fail-on error` |
| `writer-final` | same | `error` | fails `--fail-on error` |
| `production` | same | `error` | fails `--fail-on error` |

## Rolling Date Boundary Severity

| profile / policy | `rolling-date-boundary-static-test-data` severity | sign-off impact |
| --- | --- | --- |
| `compatible` | `warning` | diagnostic only |
| `diagnostic` | `warning` | diagnostic only |
| `strict-canary` | `error` | fails `--fail-on error` |
| `writer-final` | `error` | fails `--fail-on error` |
| `production` | `error` | fails `--fail-on error` |
