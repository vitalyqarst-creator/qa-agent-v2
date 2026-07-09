# Atomicity Failure Analysis

## Source Artifact

| item | value |
| --- | --- |
| failure_fixture | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary-v2.md` |
| v3_artifact | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-independent-wide-canary-v3.md` |
| original_failure_fixture_modified | `no` |
| validator_policy | `--atomicity-coverage-policy strict-canary` |

## Source Cross-check Evidence

| decision area | source rows / BSR | source artifacts used | result |
| --- | --- | --- | --- |
| Address composition grouping | Table 7 rows 33-44, `BSR 115`-`BSR 137` | `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.docx` | Address fields have independent BSR, but composed manual-address entry is one visible workflow; grouped TC require scenario rationale. |
| Residence address grouping | Table 7 rows 45-57, `BSR 138`-`BSR 161` | `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.docx` | Same-as-registration branch and manual residence entry are separate source rows; grouped TC require scenario rationale and separate invalid-class TC. |
| Contact-person block reveal | Table 7 rows 66-73, `BSR 173`-`BSR 189` | `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.docx` | Adding a contact person reveals a composed subform; grouped reveal TC is acceptable only with scenario rationale. |
| Contact-person FIO restriction | Table 7 rows 66-68, `BSR 174`, `BSR 176`, `BSR 178` | `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.docx` | The fields share the same text/hyphen source restriction; partial field x invalid-class coverage needs explicit representative/pairwise strategy. |
| Contact phone and birth date | Table 7 rows 70-71, `BSR 181`-`BSR 185` | `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.docx` | Phone format and date boundary are independent obligations; invalid phone and future date stay as separate candidate-negative TC. |

## V2 Findings Preserved

| v2_tc | source_ref_count | v3_resolution |
| --- | ---: | --- |
| `TC-AF43-AW2-001` | 3 | Сценарное обоснование added in `TC-AF43-AW3-001`; individual input restrictions remain separate. |
| `TC-AF43-AW2-003` | 3 | Сценарное обоснование added in `TC-AF43-AW3-003`. |
| `TC-AF43-AW2-004` | 3 | Сценарное обоснование added in `TC-AF43-AW3-004`; invalid postal index remains `TC-AF43-AW3-005`. |
| `TC-AF43-AW2-006` | 6 | Сценарное обоснование added in `TC-AF43-AW3-006`; high fan-in is documented as one visible address-entry workflow. |
| `TC-AF43-AW2-008` | 3 | Сценарное обоснование added in `TC-AF43-AW3-008`. |
| `TC-AF43-AW2-009` | 3 | Сценарное обоснование added in `TC-AF43-AW3-009`; email invalid classes remain separate. |
| `TC-AF43-AW2-011` | 3 | Сценарное обоснование added in `TC-AF43-AW3-011`; FIO invalid classes remain separate. |
| `TC-AF43-AW2-016` | 3 | Сценарное обоснование added in `TC-AF43-AW3-016`; birth-date future boundary remains separate. |
| `TC-AF43-AW2-018` | 3 | Сценарное обоснование added in `TC-AF43-AW3-018`. |
| `TC-AF43-AW2-019` | 7 | Сценарное обоснование added in `TC-AF43-AW3-019`; field-level checks stay traceable in `TC-AF43-AW3-020`-`TC-AF43-AW3-028`. |
| `TC-AF43-AW2-020` | 3 | Сценарное обоснование plus representative/pairwise strategy, omitted combinations and residual risk added in `TC-AF43-AW3-020`. |
| `TC-AF43-AW2-025` | 3 | Сценарное обоснование added in `TC-AF43-AW3-025`; invalid phone value remains `TC-AF43-AW3-026`. |

## Representative Strategy

V2 had candidate-negative checks for source-backed input restrictions, but the FIO field family was only implicitly sampled. V3 keeps the candidate-negative TC and adds an explicit representative/pairwise decision:

- selected combinations: surname digit, first-name non-hyphen special symbol, patronymic digit;
- omitted combinations: surname non-hyphen special symbol, first-name digit, patronymic non-hyphen special symbol;
- residual risk: field-specific frontend validators may diverge despite shared source wording, so UI execution must escalate divergent behavior.

This keeps v2 as the failure fixture and makes v3 an independent corrected artifact rather than a silent overwrite.

## Scenario Rationale Quality Remediation

The v3 follow-up found rationale-copy defects in the corrected production artifact. The affected TC bodies and coverage decisions stayed valid, but the rationale text could mislead reviewer sign-off because it referenced unrelated domains.

| tc_id | checked target | invalid rationale domain | remediation |
| --- | --- | --- | --- |
| `TC-AF43-AW3-009` | residence postal index | phone/email contact details | Rewritten to BSR 148, BSR 160/161 and sibling invalid index `TC-AF43-AW3-010`. |
| `TC-AF43-AW3-011` | client mobile phone | contact-person surname/first-name/patronymic | Rewritten to BSR 162-164 and sibling invalid phone `TC-AF43-AW3-012`. |
| `TC-AF43-AW3-016` | work phone | birth-date/current-date boundary | Rewritten to BSR 168-170 and sibling invalid work phone `TC-AF43-AW3-017`. |
| `TC-AF43-AW3-018` | home/work phone delete lifecycle | citizenship/relation fields | Rewritten to phone add/display/delete lifecycle from source rows 61 and 64. |
| `TC-AF43-AW3-025` | contact-person phone | passport series/number | Rewritten to BSR 181-183 and sibling invalid contact phone `TC-AF43-AW3-026`. |

All scenario rationale fields now use canonical `**Сценарное обоснование:**`. No test cases were added, removed, split or merged in this remediation pass.
