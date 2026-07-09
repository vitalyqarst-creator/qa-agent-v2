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

This section documents field-level / risk-based canary sampling. It is not full cartesian coverage of section 4.3.

| Fields | Shared restriction | Source rows / BSR | Selected strategy | TC ids | Covered classes | Omitted combinations | Residual risk | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Registration and residence postal indexes | Six numeric characters only. | Table 7 rows 35, 57; `BSR 124`, `BSR 161` | Cover one positive six-digit value per address branch plus two invalid representatives across the postal-index field family. | `TC-AF43-AW4-004`; `TC-AF43-AW4-005`; `TC-AF43-AW4-009`; `TC-AF43-AW4-010` | Six digits accepted; letter in registration postal index; shorter value in residence postal index. | Full letter/short/long cross-product for both postal-index fields is not duplicated. | Exact UI rejection trigger/mechanism remains calibration-required for invalid representatives. | Same visible postal-index restriction appears in both address branches; selected representatives keep canary compact while preserving positive and invalid-class coverage. |
| Client, work and contact-person phone fields | Ten numeric characters only; work/home phone add/delete behavior where applicable. | Table 7 rows 59, 62-64, 70; `BSR 163`, `BSR 169`, `BSR 171`, `BSR 172`, `BSR 182` | Cover positive phone display/add/delete representatives and invalid letter/overlength representatives across phone widgets. | `TC-AF43-AW4-011`; `TC-AF43-AW4-012`; `TC-AF43-AW4-016`; `TC-AF43-AW4-017`; `TC-AF43-AW4-018`; `TC-AF43-AW4-025`; `TC-AF43-AW4-026`; `TC-AF43-AW4-030` | Ten digits accepted for client/work/contact phone; letter rejected for client/contact phone; overlength rejected for work phone; home/work delete lifecycle covered. | Every phone field is not multiplied by every invalid length/symbol variant. | Phone widgets may normalize or reject values differently; execution must escalate divergent behavior. | Phone fields share the same visible numeric-length risk but have separate add/delete UI behavior for home/work phones. |
| Client e-mail field | One e-mail address with `@`; multiple addresses are not allowed. | Table 7 row 60; `BSR 165`, `BSR 166` | Cover one valid e-mail and two invalid format representatives. | `TC-AF43-AW4-013`; `TC-AF43-AW4-014`; `TC-AF43-AW4-015` | Single address with `@` accepted; missing `@` rejected; two addresses in one field rejected. | Other malformed e-mail strings are not duplicated. | Exact UI rejection trigger/mechanism remains calibration-required for invalid representatives. | E-mail has its own source row and must not be represented by postal or phone TC. |
| Contact-person FIO fields | Text symbols and hyphen are allowed; digits and non-hyphen special symbols are invalid. | Table 7 rows 66-68; `BSR 174`, `BSR 176`, `BSR 178` | Cover a positive FIO combination with letters and hyphen, plus one invalid representative per selected field/class. | `TC-AF43-AW4-020`; `TC-AF43-AW4-021`; `TC-AF43-AW4-022`; `TC-AF43-AW4-023` | Letters and hyphen accepted in surname/name; letters accepted in patronymic; surname digit rejected; name non-hyphen special symbol rejected; patronymic digit rejected. | Surname non-hyphen special symbol, first-name digit and patronymic non-hyphen special symbol are not duplicated. | Field-specific frontend validators may differ despite shared source wording; execution must escalate if UI behavior diverges. | The FIO field family shares source wording, so selected representatives are explicit and residual risk remains visible in this work artifact. |
| Contact-person birth date | Date must not be greater than the current date. | Table 7 row 71; `BSR 184`, `BSR 185` | Cover current-date positive boundary and D + 1 negative boundary. | `TC-AF43-AW4-027`; `TC-AF43-AW4-028` | Current date accepted; future date rejected. | Other past dates and invalid date formats are not duplicated. | Source of current date remains calibration-required: application/server/business/browser date. | Rolling date risk is isolated with D/D + 1 formulas instead of static calendar values. |
| Address composition and DaData selection | Address fields support DaData selection and manual component composition; internal `kladr` remains non-UI/internal. | Table 7 rows 33, 36-44, 46-48; `BSR 115`-`BSR 120`, `BSR 125`-`BSR 137`, `BSR 140`, `BSR 141`, `BSR 144`, `BSR 148` | Cover registration DaData selection, no-result negative, registration manual composition, address-component positive representative and residence DaData selection. | `TC-AF43-AW4-001`; `TC-AF43-AW4-002`; `TC-AF43-AW4-006`; `TC-AF43-AW4-008`; `TC-AF43-AW4-029` | DaData selection accepted; no-result hint shown; manual components displayed/accepted; residence branch field shown and accepts selected DaData address. | Full component cartesian combinations and internal `kladr` verification are not duplicated in executable TC. | Internal `kladr` and exact DaData backend behavior remain source/implementation ambiguity. | Address behavior is broad; the v4 canary samples visible UI flows and keeps internal decomposition risk in GAP/work artifacts. |

## Scenario Rationale Quality Gate

All grouped v3 TC use canonical `**Сценарное обоснование:**`. The rationale must name the checked field/block and source rows; copied rationale from an unrelated domain is not acceptable evidence for grouping.

## Save / Persistence Coverage Plan

Current canary is focused on section 4.3 field-level display, input restrictions and add/delete behavior. A separate save smoke must verify that one representative valid edit from the client contacts/address scope survives save and repeated opening of the application card. This is intentionally planned here rather than hidden inside invalid-value candidate TC.
