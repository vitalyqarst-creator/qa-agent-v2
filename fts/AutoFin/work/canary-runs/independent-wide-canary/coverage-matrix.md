# Coverage Matrix

## Summary

| metric | count |
| --- | ---: |
| selected source rows | 17 normalized rows from 39 XHTML table rows |
| selected requirement codes | 75 (`BSR 115`-`BSR 189`) |
| executable test cases | 38 |
| coverage gaps | 9 |

## Requirement To Test Case Matrix

| source_row_id | requirement_codes | requirement summary | covered_by_tc | gap_or_question |
| --- | --- | --- | --- | --- |
| `SRC-AW-001` | `BSR 115` | Registration address is always visible. | `TC-AF43-AW-001` | `none_required:covered` |
| `SRC-AW-001` | `BSR 116` | Registration address has DaData integration. | `TC-AF43-AW-002` | `none_required:covered_by_selection_flow` |
| `SRC-AW-001` | `BSR 117` | Region and house are required; missing apartment requires warning unless private-house mark is set. | `TC-AF43-AW-004`; `TC-AF43-AW-010` | `none_required:covered` |
| `SRC-AW-001` | `BSR 118` | Address not found in DaData shows `Некорректно указан адрес`. | `TC-AF43-AW-003` | `none_required:covered` |
| `SRC-AW-001` | `BSR 119` | Found address decomposes into manual-input fields. | `TC-AF43-AW-002` | `GAP-AW-001` for model `kladr` observability from related `BSR 325` outside selected rows |
| `SRC-AW-001` | `BSR 120` | Manual components compose registration address. | `TC-AF43-AW-005` | `none_required:covered` |
| `SRC-AW-002` | `BSR 121`; `BSR 122` | Registration manual-input checkbox is visible, default `Нет`. | `TC-AF43-AW-006` | `none_required:covered` |
| `SRC-AW-003` | `BSR 123`; `BSR 124` | Registration postal index visible under manual input; only 6 numeric chars. | `TC-AF43-AW-007` | `GAP-AW-002` for invalid length/non-numeric enforcement oracle |
| `SRC-AW-004` | `BSR 125`-`BSR 132` | Registration manual component fields visible under manual input. | `TC-AF43-AW-008`; `TC-AF43-AW-009` | `none_required:covered` |
| `SRC-AW-005` | `BSR 133`-`BSR 137` | Apartment/private-house branch for registration address. | `TC-AF43-AW-010` | `none_required:covered` |
| `SRC-AW-006` | `BSR 138`; `BSR 139` | Residence-address coincidence checkbox is visible, default `Да`. | `TC-AF43-AW-011` | `none_required:covered` |
| `SRC-AW-007` | `BSR 140` | Residence address visible when coincidence checkbox is `Нет`. | `TC-AF43-AW-012` | `none_required:covered` |
| `SRC-AW-007` | `BSR 141`; `BSR 144` | Residence address has DaData integration and decomposes found address. | `TC-AF43-AW-013` | `none_required:covered_by_selection_flow` |
| `SRC-AW-007` | `BSR 142` | Residence address requires apartment/private-house warning. | `TC-AF43-AW-015` | `none_required:covered` |
| `SRC-AW-007` | `BSR 143` | Residence address not found in DaData shows `Некорректно указан адрес`. | `TC-AF43-AW-014` | `none_required:covered` |
| `SRC-AW-007` | `BSR 145` | Manual components compose residence address. | `TC-AF43-AW-016` | `none_required:covered` |
| `SRC-AW-008` | `BSR 146`; `BSR 147` | Residence private-house checkbox visible under conditions, default `Нет`. | `TC-AF43-AW-017` | `none_required:covered` |
| `SRC-AW-009` | `BSR 148`; `BSR 149` | Residence manual-input checkbox visible under conditions, default `Нет`. | `TC-AF43-AW-018` | `none_required:covered` |
| `SRC-AW-010` | `BSR 150`-`BSR 159` | Residence manual component fields visible under manual input. | `TC-AF43-AW-019`; `TC-AF43-AW-020` | `none_required:covered` |
| `SRC-AW-010` | `BSR 160`; `BSR 161` | Residence postal index visible under manual input; only 6 numeric chars. | `TC-AF43-AW-021` | `GAP-AW-003` for invalid length/non-numeric enforcement oracle |
| `SRC-AW-011` | `BSR 162` | Client mobile phone always visible. | `TC-AF43-AW-022` | `none_required:covered` |
| `SRC-AW-011` | `BSR 163`; `BSR 164` | Client mobile phone is 10 digits with default `+7 (9xx) xxx-xx-xx` mask. | `TC-AF43-AW-023` | `GAP-AW-004` for invalid phone enforcement oracle |
| `SRC-AW-012` | `BSR 165` | E-mail always visible. | `TC-AF43-AW-024` | `none_required:covered` |
| `SRC-AW-012` | `BSR 166` | E-mail contains `@`, only one e-mail address. | `TC-AF43-AW-025` | `GAP-AW-005` for no-`@` and multiple-email enforcement oracle |
| `SRC-AW-013` | `BSR 167`; `BSR 171` | Home phone hidden by default and appears after add action. | `TC-AF43-AW-026` | `GAP-AW-006` for exact default hidden check not independently executable without UI evidence |
| `SRC-AW-013` | `BSR 168`; `BSR 172` | Work phone hidden by default, appears after add action, can be removed. | `TC-AF43-AW-027`; `TC-AF43-AW-029` | `GAP-AW-006` for exact default hidden check not independently executable without UI evidence |
| `SRC-AW-013` | `BSR 169`; `BSR 170` | Work phone is 10 digits with default mask. | `TC-AF43-AW-028` | `GAP-AW-004` for invalid phone enforcement oracle |
| `SRC-AW-014` | `BSR 173`; `BSR 174` | Contact surname visible after add and allows text plus hyphen. | `TC-AF43-AW-031` | `GAP-AW-007` for invalid character enforcement oracle |
| `SRC-AW-014` | `BSR 175`; `BSR 176` | Contact first name visible after add and allows text plus hyphen. | `TC-AF43-AW-032` | `GAP-AW-007` for invalid character enforcement oracle |
| `SRC-AW-014` | `BSR 177`; `BSR 178` | Contact patronymic visible after add and allows text plus hyphen. | `TC-AF43-AW-033` | `GAP-AW-007` for invalid character enforcement oracle |
| `SRC-AW-015` | `BSR 179` | Relation list visible after add and contains source values. | `TC-AF43-AW-034` | `GAP-AW-008` for closed-list certainty |
| `SRC-AW-015` | `BSR 180` | Choosing `Иное` shows additional text field. | `TC-AF43-AW-035` | `none_required:covered` |
| `SRC-AW-016` | `BSR 181`; `BSR 182`; `BSR 183` | Contact phone visible after add, 10 digits, default mask. | `TC-AF43-AW-036` | `GAP-AW-004` for invalid phone enforcement oracle |
| `SRC-AW-016` | `BSR 184` | Contact birth date visible after add. | `TC-AF43-AW-037` | `none_required:covered` |
| `SRC-AW-016` | `BSR 185` | Contact birth date cannot be greater than current date. | `not_covered:GAP-AW-009` | `GAP-AW-009` |
| `SRC-AW-017` | `BSR 186`; `BSR 187` | Add contact-person action adds full row. | `TC-AF43-AW-030` | `none_required:covered` |
| `SRC-AW-017` | `BSR 188`; `BSR 189` | Delete widget visible for repeatable block and deletes row. | `TC-AF43-AW-038` | `none_required:covered` |

## Distribution By Type

| type | count |
| --- | ---: |
| Positive | 34 |
| Negative | 4 |

## Distribution By Package

| package_id | tc_count |
| --- | ---: |
| `WP-01` | 10 |
| `WP-02` | 11 |
| `WP-03` | 8 |
| `WP-04` | 9 |

