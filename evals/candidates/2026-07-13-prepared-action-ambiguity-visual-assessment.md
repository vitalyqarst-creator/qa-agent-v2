# prepared-action-ambiguity: writer action is not reproducibly executable

## Metadata

- `candidate_id`: `CAND-2026-07-13-PREPARED-ACTION-AMBIGUITY`
- `created_at`: `2026-07-13`
- `source_signal`: `H52 V2 reviewer F-001/F-002`
- `affected_skill`: `ft-test-case-iteration; ft-test-case-writer`
- `failure_class`: `ambiguous-execution-action; ambiguous-dictionary-value-path`
- `status`: `verified-live`

## Failure Signal

- V2 `TC-VAMB-004` used alternative verbs `установить или сохранить`.
- V2 `TC-VAMB-012` selected a label present in DICT-101 and DICT-102 without a child group locator.
- Deterministic gates passed both defects; semantic reviewer rejected OBL-005 and OBL-013.

## Expected Detection Or Output

- Compiler rejects a dictionary child id named in `test_data` but omitted from `planned_check`.
- Runner rejects alternative user-action verbs and duplicated labels without a group id/name, except explicit `в любой группе` policy.
- Corrected output contains one exact action and one unambiguous dictionary path.

## Verification

- Negative compiler and runner regressions pass.
- Full agent-layer suite: 462 passed, 1 skipped.
- V3 deterministic quality bundle includes action/path unambiguity checks and has 0 findings.
- V3 semantic reviewer accepted OBL-005 and OBL-013 and all 13 obligations.
- Production baseline remained unchanged; V3 target was not promoted.
