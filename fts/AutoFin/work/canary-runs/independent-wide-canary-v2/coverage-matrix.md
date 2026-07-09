# Coverage Matrix

| source_ref | requirement codes | obligation | covered_by | residual_gap |
| --- | --- | --- | --- | --- |
| `SRC-AW2-001` | `BSR 115`-`BSR 120` | Registration address visibility, DaData selection, no-result hint and manual composition. | `TC-AF43-AW2-001`; `TC-AF43-AW2-002`; `TC-AF43-AW2-006` | `GAP-AW2-001` for internal `kladr` verification only |
| `SRC-AW2-003` | `BSR 123`; `BSR 124` | Registration postal index positive six-digit value and invalid non-numeric class. | `TC-AF43-AW2-004`; `TC-AF43-AW2-005` | `GAP-AW2-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW2-005` | `BSR 138`-`BSR 161` | Residence branch, DaData, manual postal index positive and invalid shorter value. | `TC-AF43-AW2-007`; `TC-AF43-AW2-008`; `TC-AF43-AW2-009`; `TC-AF43-AW2-010` | `GAP-AW2-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW2-006` | `BSR 162`-`BSR 164` | Client mobile phone positive ten-digit value and invalid letter class. | `TC-AF43-AW2-011`; `TC-AF43-AW2-012` | `GAP-AW2-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW2-007` | `BSR 165`; `BSR 166` | E-mail positive single address, missing `@`, and multiple-address invalid classes. | `TC-AF43-AW2-013`; `TC-AF43-AW2-014`; `TC-AF43-AW2-015` | `GAP-AW2-004` keeps UI mechanism question; invalid class is not gap-only |
| `SRC-AW2-008` | `BSR 167`-`BSR 172` | Home/work phone add/delete, positive ten-digit work phone, invalid overlength work phone. | `TC-AF43-AW2-016`; `TC-AF43-AW2-017`; `TC-AF43-AW2-018` | `GAP-AW2-002`; `GAP-AW2-004` |
| `SRC-AW2-009` | `BSR 173`-`BSR 178` | Contact-person FIO positive text/hyphen and invalid digit/special-symbol classes. | `TC-AF43-AW2-019`; `TC-AF43-AW2-020`; `TC-AF43-AW2-021`; `TC-AF43-AW2-022`; `TC-AF43-AW2-023` | `GAP-AW2-004` keeps UI mechanism question; invalid classes are not gap-only |
| `SRC-AW2-010` | `BSR 179`; `BSR 180` | Relation values and `Иное` branch. | `TC-AF43-AW2-024` | `GAP-AW2-003` for closed-set ambiguity |
| `SRC-AW2-011` | `BSR 181`-`BSR 185` | Contact phone positive/invalid classes and birth-date positive/future-date classes. | `TC-AF43-AW2-025`; `TC-AF43-AW2-026`; `TC-AF43-AW2-027`; `TC-AF43-AW2-028` | `GAP-AW2-004` keeps UI mechanism question; invalid classes are not gap-only |

## Counts

| metric | count |
| --- | ---: |
| total_tc | 28 |
| positive_tc | 16 |
| negative_tc_exact_oracle | 1 |
| candidate_negative_tc | 11 |
