# Atomicity Failure Analysis

## Source Artifact

| item | value |
| --- | --- |
| failure_fixture | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary-v2.md` |
| v3_artifact | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary-v3.md` |
| original_failure_fixture_modified | `no` |
| validator_policy | `--atomicity-coverage-policy strict-canary` |

## V2 Findings Preserved

| v2_tc | source_ref_count | v3_resolution |
| --- | ---: | --- |
| `TC-AF43-AW2-001` | 3 | Scenario rationale added in `TC-AF43-AW3-001`; individual input restrictions remain separate. |
| `TC-AF43-AW2-003` | 3 | Scenario rationale added in `TC-AF43-AW3-003`. |
| `TC-AF43-AW2-004` | 3 | Scenario rationale added in `TC-AF43-AW3-004`; invalid postal index remains `TC-AF43-AW3-005`. |
| `TC-AF43-AW2-006` | 6 | Scenario rationale added in `TC-AF43-AW3-006`; high fan-in is documented as one visible address-entry workflow. |
| `TC-AF43-AW2-008` | 3 | Scenario rationale added in `TC-AF43-AW3-008`. |
| `TC-AF43-AW2-009` | 3 | Scenario rationale added in `TC-AF43-AW3-009`; email invalid classes remain separate. |
| `TC-AF43-AW2-011` | 3 | Scenario rationale added in `TC-AF43-AW3-011`; FIO invalid classes remain separate. |
| `TC-AF43-AW2-016` | 3 | Scenario rationale added in `TC-AF43-AW3-016`; birth-date future boundary remains separate. |
| `TC-AF43-AW2-018` | 3 | Scenario rationale added in `TC-AF43-AW3-018`. |
| `TC-AF43-AW2-019` | 7 | Scenario rationale added in `TC-AF43-AW3-019`; field-level checks stay traceable in `TC-AF43-AW3-020`-`TC-AF43-AW3-028`. |
| `TC-AF43-AW2-020` | 3 | Scenario rationale plus representative/pairwise strategy, omitted combinations and residual risk added in `TC-AF43-AW3-020`. |
| `TC-AF43-AW2-025` | 3 | Scenario rationale added in `TC-AF43-AW3-025`; invalid phone value remains `TC-AF43-AW3-026`. |

## Representative Strategy

V2 had candidate-negative checks for source-backed input restrictions, but the FIO field family was only implicitly sampled. V3 keeps the candidate-negative TC and adds an explicit representative/pairwise decision:

- selected combinations: surname digit, first-name non-hyphen special symbol, patronymic digit;
- omitted combinations: surname non-hyphen special symbol, first-name digit, patronymic non-hyphen special symbol;
- residual risk: field-specific frontend validators may diverge despite shared source wording, so UI execution must escalate divergent behavior.

This keeps v2 as the failure fixture and makes v3 an independent corrected artifact rather than a silent overwrite.
