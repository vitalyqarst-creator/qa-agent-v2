# Coverage Matrix

| source_ref | requirement codes | obligation | covered_by | residual_gap |
| --- | --- | --- | --- | --- |
| `SRC-AW3-001` | `BSR 115`-`BSR 120` | Registration address visibility, DaData selection, no-result hint and manual composition. | `TC-AF43-AW3-001`; `TC-AF43-AW3-002`; `TC-AF43-AW3-006` | `GAP-AW3-001` for internal `kladr` verification only |
| `SRC-AW3-003` | `BSR 123`; `BSR 124` | Registration postal index positive six-digit value and invalid non-numeric class. | `TC-AF43-AW3-004`; `TC-AF43-AW3-005` | `GAP-AW3-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW3-005` | `BSR 138`-`BSR 161` | Residence branch, DaData, manual postal index positive and invalid shorter value. | `TC-AF43-AW3-007`; `TC-AF43-AW3-008`; `TC-AF43-AW3-009`; `TC-AF43-AW3-010` | `GAP-AW3-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW3-006` | `BSR 162`-`BSR 164` | Client mobile phone positive ten-digit value and invalid letter class. | `TC-AF43-AW3-011`; `TC-AF43-AW3-012` | `GAP-AW3-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW3-007` | `BSR 165`; `BSR 166` | E-mail positive single address, missing `@`, and multiple-address invalid classes. | `TC-AF43-AW3-013`; `TC-AF43-AW3-014`; `TC-AF43-AW3-015` | `GAP-AW3-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW3-008` | `BSR 167`-`BSR 172` | Home/work phone add/delete, positive ten-digit work phone, invalid overlength work phone. | `TC-AF43-AW3-016`; `TC-AF43-AW3-017`; `TC-AF43-AW3-018` | `GAP-AW3-002`; `GAP-AW3-004` |
| `SRC-AW3-009` | `BSR 173`-`BSR 178` | Contact-person FIO positive text/hyphen and invalid digit/special-symbol classes. | `TC-AF43-AW3-019`; `TC-AF43-AW3-020`; `TC-AF43-AW3-021`; `TC-AF43-AW3-022`; `TC-AF43-AW3-023` | `GAP-AW3-004` keeps UI mechanism question; invalid classes are not gap-only |
| `SRC-AW3-010` | `BSR 179`; `BSR 180` | Relation values and `Иное` branch. | `TC-AF43-AW3-024` | `GAP-AW3-003` for closed-set ambiguity |
| `SRC-AW3-011` | `BSR 181`-`BSR 185` | Contact phone positive/invalid classes and birth-date positive/future-date classes. | `TC-AF43-AW3-025`; `TC-AF43-AW3-026`; `TC-AF43-AW3-027`; `TC-AF43-AW3-028` | `GAP-AW3-004` keeps UI mechanism question; invalid classes are not gap-only |

## Counts

| metric | count |
| --- | ---: |
| total_tc | 28 |
| positive_tc | 16 |
| negative_tc_exact_oracle | 1 |
| candidate_negative_tc | 11 |

## Representative / Pairwise Coverage Decisions

| field family | source restriction | selected combinations | omitted combinations | residual risk | evidence |
| --- | --- | --- | --- | --- | --- |
| Contact-person FIO (`BSR 174`, `BSR 176`, `BSR 178`) | Text symbols and hyphen are allowed; digit and non-hyphen special-symbol classes are invalid representatives. | Positive: surname letters, first name with hyphen, patronymic letters in `TC-AF43-AW3-020`. Negative/candidate: surname digit in `TC-AF43-AW3-021`, first-name non-hyphen special symbol in `TC-AF43-AW3-022`, patronymic digit in `TC-AF43-AW3-023`. | Surname non-hyphen special symbol, first-name digit, patronymic non-hyphen special symbol are not duplicated. | Field-specific frontend validators may differ despite shared source wording; execution must escalate if UI behavior diverges. | `TC-AF43-AW3-020` includes `Representative/pairwise strategy`, `Omitted combinations`, and `Residual risk`. |
| Postal indexes (`BSR 124`, `BSR 161`) | Six numeric characters only. | Registration postal index letter representative in `TC-AF43-AW3-005`; residence postal index shorter length representative in `TC-AF43-AW3-010`. | Full cartesian cross-product of letter/short/long for both postal-index fields is not duplicated in this canary. | Field widgets may enforce length and numeric classes differently; uncovered classes remain reviewer-visible through this matrix. | Both invalid classes have concrete values and candidate UI calibration markers. |
| Phone fields (`BSR 163`, `BSR 169`, `BSR 182`) | Ten numeric characters only. | Client mobile letter representative in `TC-AF43-AW3-012`; work phone overlength representative in `TC-AF43-AW3-017`; contact phone letter representative in `TC-AF43-AW3-026`. | Full digit/letter/short/long cross-product for every phone field is not duplicated. | Different phone widgets may normalize or reject values differently; calibration is required if execution shows divergence. | All selected invalid values are concrete and source-backed. |

## Scenario Rationale Quality Gate

All grouped v3 TC use canonical `**Сценарное обоснование:**`. The rationale must name the checked field/block and source rows; copied rationale from an unrelated domain is not acceptable evidence for grouping.
