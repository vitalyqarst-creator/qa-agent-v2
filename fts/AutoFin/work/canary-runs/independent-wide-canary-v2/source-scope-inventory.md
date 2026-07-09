# Source And Scope Inventory

## Source Selection

| item | value |
| --- | --- |
| ft_slug | `AutoFin` |
| main_ft_docx | `fts/AutoFin/source/FT4AutoFinFinal.docx` |
| main_ft_xhtml | `fts/AutoFin/source/FT4AutoFinFinal.xhtml` |
| xhtml_available | `yes` |
| pdf_cross_check | `fts/AutoFin/source/FT4AutoFinFinal.pdf` |
| package_notes | `fts/AutoFin/AGENT-NOTES.md` |
| support_used | `none` |
| mockups_used_as_requirement_source | `no` |
| previous_test_cases_used | `no` |
| original_independent_wide_canary_used_as_success_template | `no` |

## Selected Scope

| package_id | source_row_id | source artifact | source location | requirement codes | requirement summary | mapped_tc_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | `SRC-AW2-001` | `FT4AutoFinFinal.xhtml` | Table 7 row 33 | `BSR 115`-`BSR 120` | Registration address: always visible, DaData integration, no-result hint, decomposition and manual composition. | `TC-AF43-AW2-001`; `TC-AF43-AW2-002`; `TC-AF43-AW2-006`; `GAP-AW2-001` |
| `WP-01` | `SRC-AW2-002` | `FT4AutoFinFinal.xhtml` | Table 7 row 34 | `BSR 121`-`BSR 122` | Registration manual-input switch visibility and default `Нет`. | `TC-AF43-AW2-004`; `TC-AF43-AW2-006` |
| `WP-01` | `SRC-AW2-003` | `FT4AutoFinFinal.xhtml` | Table 7 row 35 | `BSR 123`-`BSR 124` | Registration postal index visible in manual mode and restricted to six numeric chars. | `TC-AF43-AW2-004`; `TC-AF43-AW2-005`; `GAP-AW2-004` |
| `WP-01` | `SRC-AW2-004` | `FT4AutoFinFinal.xhtml` | Table 7 rows 36-44 | `BSR 125`-`BSR 137` | Registration manual components and apartment/private-house branch. | `TC-AF43-AW2-003`; `TC-AF43-AW2-006` |
| `WP-02` | `SRC-AW2-005` | `FT4AutoFinFinal.xhtml` | Table 7 rows 45-57 | `BSR 138`-`BSR 161` | Residence-address same-as-registration branch, DaData, manual branch and postal index. | `TC-AF43-AW2-007`; `TC-AF43-AW2-008`; `TC-AF43-AW2-009`; `TC-AF43-AW2-010`; `GAP-AW2-004` |
| `WP-03` | `SRC-AW2-006` | `FT4AutoFinFinal.xhtml` | Table 7 row 59 | `BSR 162`-`BSR 164` | Client mobile phone: visible, ten digits, default `+7` mask. | `TC-AF43-AW2-011`; `TC-AF43-AW2-012`; `GAP-AW2-004` |
| `WP-03` | `SRC-AW2-007` | `FT4AutoFinFinal.xhtml` | Table 7 row 60 | `BSR 165`-`BSR 166` | E-mail visible, contains `@`, only one address. | `TC-AF43-AW2-013`; `TC-AF43-AW2-014`; `TC-AF43-AW2-015`; `GAP-AW2-004` |
| `WP-03` | `SRC-AW2-008` | `FT4AutoFinFinal.xhtml` | Table 7 rows 61-64 | `BSR 167`-`BSR 172` | Home/work phone add, display, format and delete behavior. | `TC-AF43-AW2-016`; `TC-AF43-AW2-017`; `TC-AF43-AW2-018`; `GAP-AW2-002`; `GAP-AW2-004` |
| `WP-04` | `SRC-AW2-009` | `FT4AutoFinFinal.xhtml` | Table 7 rows 66-68 | `BSR 173`-`BSR 178` | Contact-person surname/name/patronymic visible after add and allow text plus hyphen. | `TC-AF43-AW2-019`; `TC-AF43-AW2-020`; `TC-AF43-AW2-021`; `TC-AF43-AW2-022`; `TC-AF43-AW2-023`; `GAP-AW2-004` |
| `WP-04` | `SRC-AW2-010` | `FT4AutoFinFinal.xhtml` | Table 7 row 69 | `BSR 179`-`BSR 180` | Relation list and `Иное` branch. | `TC-AF43-AW2-024`; `GAP-AW2-003` |
| `WP-04` | `SRC-AW2-011` | `FT4AutoFinFinal.xhtml` | Table 7 rows 70-71 | `BSR 181`-`BSR 185` | Contact-person phone and birth date visibility/format/date limit. | `TC-AF43-AW2-025`; `TC-AF43-AW2-026`; `TC-AF43-AW2-027`; `TC-AF43-AW2-028`; `GAP-AW2-004` |
| `WP-04` | `SRC-AW2-012` | `FT4AutoFinFinal.xhtml` | Table 7 rows 72-73 | `BSR 186`-`BSR 189` | Add and delete contact-person row. | `TC-AF43-AW2-019` |

## Dictionary Inventory

| dict_id | source_ref | values | closed_set_decision | used_by_tc |
| --- | --- | --- | --- | --- |
| `DICT-AW2-REL-001` | Table 7 row 69, `BSR 179` | `супруг/супруга`; `отец/мать`; `сестра/брат`; `теща/свекровь/тесть/свекр`; `сын/дочь`; `друг/знакомый/коллега`; `иное` | `source-list`; absence of extra values is not asserted because source does not explicitly say "only" | `TC-AF43-AW2-024`; `GAP-AW2-003` |
