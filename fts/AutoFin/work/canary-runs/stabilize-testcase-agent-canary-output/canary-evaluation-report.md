# Canary Evaluation Report: application-card-client-addresses-contacts

## Run Metadata

- Branch: `audit/stabilize-testcase-agent-canary-output`.
- Base branch: `audit/stabilize-testcase-agent`.
- Base commit at start: `e1490e4 Stabilize test case agent after audit`.
- Scope: `application-card-client-addresses-contacts`.
- Main source: `fts/AutoFin/source/FT4AutoFinFinal.xhtml`.
- Structural cross-check: `fts/AutoFin/source/FT4AutoFinFinal.pdf`.
- Old untracked sample `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md` was not used as generated output and was not staged.

## Generated Artifacts

- `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-canary.md`
- `fts/AutoFin/work/canary-runs/stabilize-testcase-agent-canary-output/outputs/scoped-validator-profile.writer-canary.json`
- `fts/AutoFin/work/canary-runs/stabilize-testcase-agent-canary-output/canary-evaluation-report.md`

## Scope Evidence

| requirement | source row | field | generated TC |
| --- | --- | --- | --- |
| BSR 174 | `SRC-CANARY-174` | `Фамилия` контактного лица | `TC-AFIN-CC-001`; `TC-AFIN-CC-002`; `TC-AFIN-CC-003`; `TC-AFIN-CC-004` |
| BSR 176 | `SRC-CANARY-176` | `Имя` контактного лица | `TC-AFIN-CC-005`; `TC-AFIN-CC-006`; `TC-AFIN-CC-007`; `TC-AFIN-CC-008` |
| BSR 178 | `SRC-CANARY-178` | `Отчество` контактного лица | `TC-AFIN-CC-009`; `TC-AFIN-CC-010`; `TC-AFIN-CC-011`; `TC-AFIN-CC-012` |

## Test Case Counts

| metric | count |
| --- | ---: |
| Total TC | 12 |
| Positive TC | 6 |
| Negative TC | 6 |
| Candidate negative TC | 6 |
| BA questions | 4 |

## Required Restriction Coverage

| field | positive letters | positive letters + hyphen | candidate negative digit | candidate negative non-hyphen special |
| --- | --- | --- | --- | --- |
| `Фамилия` | `Иванов` / `TC-AFIN-CC-001` | `Иванов-Петров` / `TC-AFIN-CC-002` | `Иванов1` / `TC-AFIN-CC-003` | `Иванов@` / `TC-AFIN-CC-004` |
| `Имя` | `Иван` / `TC-AFIN-CC-005` | `Анна-Мария` / `TC-AFIN-CC-006` | `Иван1` / `TC-AFIN-CC-007` | `Иван@` / `TC-AFIN-CC-008` |
| `Отчество` | `Иванович` / `TC-AFIN-CC-009` | `Иванович-Петрович` / `TC-AFIN-CC-010` | `Иванович1` / `TC-AFIN-CC-011` | `Иванович@` / `TC-AFIN-CC-012` |

## Candidate Negative Checks

- Candidate status is kept in body metadata only; titles do not contain `UI calibration`, `candidate`, `oracle`, `requires confirmation`, `требует подтверждения`, or `требуется подтверждение`.
- Each candidate negative TC contains `**Статус oracle:** ui-calibration-required`.
- Each candidate negative TC contains `**Статус тест-кейса:** candidate-ui-calibration`.
- Each candidate negative TC contains `**Требуется подтверждение:** ...`.
- Each candidate negative TC uses a concrete invalid value.
- Expected results do not assert an exact UI rejection mechanism; they require UI calibration for the observed mechanism.

## BA Questions

| id | linked source | question |
| --- | --- | --- |
| BA-CANARY-001 | BSR 174 / BSR 176 / BSR 178 | Какой фактический UI-механизм отклонения должен считаться ожидаемым для цифры в полях ФИО контактного лица? |
| BA-CANARY-002 | BSR 174 / BSR 176 / BSR 178 | Какой фактический UI-механизм отклонения должен считаться ожидаемым для специального символа, отличного от дефиса, в полях ФИО контактного лица? |
| BA-CANARY-003 | BSR 174 / BSR 176 / BSR 178 | Считать ли пробел между частями ФИО текстовым символом или недопустимым символом для этих полей? |
| BA-CANARY-004 | BSR 174 / BSR 176 / BSR 178 | Считать ли латинские буквы, апостроф и букву `ё` допустимыми текстовыми символами для этих полей? |

## Validation Results

| command | result |
| --- | --- |
| `python scripts/validate_agent_artifacts.py --root fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-canary.md --json --test-case-policy strict --fail-on warning` | pass; 0 findings, 0 warnings |
| Canary semantic check for required values, candidate metadata, title markers and BA questions | pass |
| `python -m pytest tests/test_agent_artifact_validator.py -q -k "text_symbol_candidate_invalid_value_is_not_numeric_valid_data or text_symbol_tddt_can_group_required_equivalence_classes or text_symbol_restriction_positive_and_candidate_negative_coverage_passes or generated_test_case_quality_smells_are_reported"` | pass; 3 passed, 298 deselected |
| `python scripts/run_tests.py --suite architecture` | pass; 0 findings |
| `python scripts/run_tests.py --suite agent-layer-fast` | pass; 210 tests, 1 skipped |
| `python scripts/run_tests.py --suite artifact-validator-sharded` | pass; 301 tests across 7 shards |

## Validator Changes

- Fixed a false positive where `VALID_TEST_DATA_VALUE_RE` matched `допустимое значение` inside `Недопустимое значение`.
- Scoped merged numeric-class TDDT warning away from `text-symbol-restriction`, where one source property legitimately maps to the required text-symbol equivalence classes.
- Added targeted regression tests for both cases.

## Remaining Risks

- The exact UI rejection mechanism for invalid symbols is still unknown until UI calibration.
- PDF cross-check found the relevant BSR codes but Poppler emitted font `nameToUnicode` warnings; XHTML remains the primary extraction source.
- This canary is intentionally narrow and proves the BSR 174 / 176 / 178 text-symbol restriction path, not full AutoFin test-case coverage.
