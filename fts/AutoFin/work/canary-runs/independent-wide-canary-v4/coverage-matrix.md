# Coverage Matrix

| source_ref | requirement codes | obligation | covered_by | residual_gap |
| --- | --- | --- | --- | --- |
| `SRC-AW4-001` | `BSR 115`-`BSR 120` | Registration address visibility, DaData selection, no-result hint and manual composition. | `TC-AF43-AW4-001`; `TC-AF43-AW4-002`; `TC-AF43-AW4-006` | `GAP-AW4-001` for internal `kladr` verification only |
| `SRC-AW4-003` | `BSR 123`; `BSR 124` | Registration postal index positive six-digit value and invalid non-numeric class. | `TC-AF43-AW4-004`; `TC-AF43-AW4-005` | `GAP-AW4-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW4-005` | `BSR 138`-`BSR 161` | Residence branch, DaData, manual postal index positive and invalid shorter value. | `TC-AF43-AW4-007`; `TC-AF43-AW4-008`; `TC-AF43-AW4-009`; `TC-AF43-AW4-010` | `GAP-AW4-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW4-006` | `BSR 162`-`BSR 164` | Client mobile phone positive ten-digit value and invalid letter class. | `TC-AF43-AW4-011`; `TC-AF43-AW4-012` | `GAP-AW4-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW4-007` | `BSR 165`; `BSR 166` | E-mail positive single address, missing `@`, and multiple-address invalid classes. | `TC-AF43-AW4-013`; `TC-AF43-AW4-014`; `TC-AF43-AW4-015` | `GAP-AW4-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW4-008` | `BSR 167`-`BSR 172` | Home/work phone add/delete, positive ten-digit work phone, invalid overlength work phone. | `TC-AF43-AW4-016`; `TC-AF43-AW4-017`; `TC-AF43-AW4-018`; `TC-AF43-AW4-030` | `GAP-AW4-002`; `GAP-AW4-004` |
| `SRC-AW4-009` | `BSR 173`-`BSR 178` | Contact-person FIO positive text/hyphen and invalid digit/special-symbol classes. | `TC-AF43-AW4-019`; `TC-AF43-AW4-020`; `TC-AF43-AW4-021`; `TC-AF43-AW4-022`; `TC-AF43-AW4-023` | `GAP-AW4-004` keeps UI mechanism question; invalid classes are not gap-only |
| `SRC-AW4-010` | `BSR 179`; `BSR 180` | Relation values and `Иное` branch. | `TC-AF43-AW4-024`; `TC-AF43-AW4-031` | `GAP-AW4-003` for closed-set ambiguity |
| `SRC-AW4-011` | `BSR 181`-`BSR 185` | Contact phone positive/invalid classes and birth-date positive/future-date classes. | `TC-AF43-AW4-025`; `TC-AF43-AW4-026`; `TC-AF43-AW4-027`; `TC-AF43-AW4-028` | `GAP-AW4-004` keeps UI mechanism question; invalid classes are not gap-only |

## Counts

| metric | count |
| --- | ---: |
| total_tc | 31 |
| positive_tc | 18 |
| negative_tc_exact_oracle | 2 |
| candidate_negative_tc | 11 |

## Representative / Pairwise Coverage Decisions

| field family | source restriction | selected combinations | omitted combinations | residual risk | evidence |
| --- | --- | --- | --- | --- | --- |
| Postal indexes (`BSR 148`, `BSR 149`) | Six-digit positive representative and overlength invalid representative cover visible postal-index restriction. | Positive: `TC-AF43-AW4-008`; candidate-negative: `TC-AF43-AW4-010`. | Shorter malformed postal index is not duplicated. | Exact UI rejection mechanism remains calibration-required for invalid representative. | Candidate-negative TC includes explicit invalid value and neutral validation trigger. |
| Phone fields (`BSR 162`, `BSR 163`, `BSR 169`, `BSR 170`, `BSR 171`, `BSR 172`) | Ten-digit positive representatives are covered for mobile/contact/work phones; invalid length representatives cover visible max-length restrictions. | Positive: `TC-AF43-AW4-011`, `TC-AF43-AW4-012`, `TC-AF43-AW4-016`, `TC-AF43-AW4-017`, `TC-AF43-AW4-027`, `TC-AF43-AW4-030`. Candidate-negative: `TC-AF43-AW4-013`, `TC-AF43-AW4-014`, `TC-AF43-AW4-015`, `TC-AF43-AW4-028`. | Every phone field is not multiplied by every invalid length variant. | Exact UI rejection mechanism remains calibration-required for invalid representatives. | Candidate-negative TC include explicit invalid values and neutral validation trigger. |
| E-mail restrictions (`BSR 160`, `BSR 161`) | Source requires valid e-mail format and invalid format rejection. | Positive valid format in `TC-AF43-AW4-008`; candidate-negative missing-at-sign and double-at representatives in `TC-AF43-AW4-009` and `TC-AF43-AW4-010`. | Other malformed e-mail strings are not duplicated. | Exact UI rejection mechanism remains calibration-required for invalid representatives. | Candidate-negative TC include explicit invalid values and neutral validation trigger. |
| Contact-person FIO (`BSR 174`, `BSR 176`, `BSR 178`) | Text symbols and hyphen are allowed; digit and non-hyphen special-symbol classes are invalid representatives. | Positive: surname letters, first name with hyphen, patronymic letters in `TC-AF43-AW4-020`. Negative/candidate: surname digit in `TC-AF43-AW4-021`, first-name non-hyphen special symbol in `TC-AF43-AW4-022`, patronymic digit in `TC-AF43-AW4-023`. | Surname non-hyphen special symbol, first-name digit, patronymic non-hyphen special symbol are not duplicated. | Field-specific frontend validators may differ despite shared source wording; execution must escalate if UI behavior diverges. | Representative strategy is kept in this work artifact, not in production TC text. |
| Postal indexes (`BSR 124`, `BSR 161`) | Six numeric characters only. | Registration postal index letter representative in `TC-AF43-AW4-005`; residence postal index shorter length representative in `TC-AF43-AW4-010`. | Full cartesian cross-product of letter/short/long for both postal-index fields is not duplicated in this canary. | Field widgets may enforce length and numeric classes differently; uncovered classes remain reviewer-visible through this matrix. | Both invalid classes have concrete values and candidate UI calibration markers. |
| Phone fields (`BSR 163`, `BSR 169`, `BSR 182`) | Ten numeric characters only. | Client mobile letter representative in `TC-AF43-AW4-012`; work phone overlength representative in `TC-AF43-AW4-017`; contact phone letter representative in `TC-AF43-AW4-026`. | Full digit/letter/short/long cross-product for every phone field is not duplicated. | Different phone widgets may normalize or reject values differently; calibration is required if execution shows divergence. | All selected invalid values are concrete and source-backed. |

## Scenario Rationale Quality Gate

All grouped v3 TC use canonical `**Сценарное обоснование:**`. The rationale must name the checked field/block and source rows; copied rationale from an unrelated domain is not acceptable evidence for grouping.

## Save / Persistence Coverage Plan

Current canary is focused on section 4.3 field-level display, input restrictions and add/delete behavior. A separate save smoke must verify that one representative valid edit from the client contacts/address scope survives save and repeated opening of the application card. This is intentionally planned here rather than hidden inside invalid-value candidate TC.
