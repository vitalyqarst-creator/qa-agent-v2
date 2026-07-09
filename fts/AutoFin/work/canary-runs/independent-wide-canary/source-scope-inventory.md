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
| previous_canary_artifacts_used | `no` |

## Encoding / Extraction Notes

| issue | impact | handling |
| --- | --- | --- |
| Python stdout in this PowerShell session displays Cyrillic as mojibake. | Console output was not used as human-readable source evidence. | Stable extraction was anchored by `BSR` IDs and direct source snippets from XHTML/PowerShell; work artifacts use normalized Russian text created from the FT content. |
| XHTML contains large embedded images. | Raw `rg` around table 7 can include huge image payloads. | Table rows were extracted by HTML table structure and BSR ranges, not by copying raw surrounding XHTML. |

## Selected Scope

| package_id | source_row_id | source artifact | source location | requirement codes | requirement summary | included reason |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | `SRC-AW-001` | `FT4AutoFinFinal.xhtml` | Table 7 row 33 | `BSR 115`-`BSR 120` | Поле «Адрес регистрации»: видимость, DaData, подсказки по не найденному адресу/квартире, разложение и ручная сборка адреса. | Core address-registration behavior in requested 4.3 address scope. |
| `WP-01` | `SRC-AW-002` | `FT4AutoFinFinal.xhtml` | Table 7 row 34 | `BSR 121`-`BSR 122` | Признак «Ручной ввод» для адреса регистрации: видимость и default `Нет`. | Controls manual address branch. |
| `WP-01` | `SRC-AW-003` | `FT4AutoFinFinal.xhtml` | Table 7 row 35 | `BSR 123`-`BSR 124` | Почтовый индекс адреса регистрации: visibility under manual input and 6 numeric chars. | Manual address component and numeric-format obligation. |
| `WP-01` | `SRC-AW-004` | `FT4AutoFinFinal.xhtml` | Table 7 rows 36-42 | `BSR 125`-`BSR 132` | Region, district, settlement, city, street, house, corpus fields for registration address. | Manual address components used by `BSR 120`. |
| `WP-01` | `SRC-AW-005` | `FT4AutoFinFinal.xhtml` | Table 7 rows 43-44 | `BSR 133`-`BSR 137` | Apartment/private-house branch for registration address and apartment warning. | High-risk requiredness branch with source-backed message. |
| `WP-02` | `SRC-AW-006` | `FT4AutoFinFinal.xhtml` | Table 7 row 45 | `BSR 138`-`BSR 139` | Checkbox «Адрес фактического места жительства совпадает с адресом регистрации»: always visible, default `Да`. | Controls residence-address visibility. |
| `WP-02` | `SRC-AW-007` | `FT4AutoFinFinal.xhtml` | Table 7 row 46 | `BSR 140`-`BSR 145` | Field «Адрес фактического места жительства»: conditional visibility, DaData, hints, decomposition, manual composition. | Core residence-address behavior in requested scope. |
| `WP-02` | `SRC-AW-008` | `FT4AutoFinFinal.xhtml` | Table 7 row 47 | `BSR 146`-`BSR 147` | Private-house checkbox for residence address: conditional visibility and default `Нет`. | Requiredness branch for apartment in residence address. |
| `WP-02` | `SRC-AW-009` | `FT4AutoFinFinal.xhtml` | Table 7 row 48 | `BSR 148`-`BSR 149` | Manual-input checkbox for residence address: conditional visibility and default `Нет`. | Controls residence manual branch. |
| `WP-02` | `SRC-AW-010` | `FT4AutoFinFinal.xhtml` | Table 7 rows 49-57 | `BSR 150`-`BSR 161` | Residence address manual fields and postal index. | Manual residence address components. |
| `WP-03` | `SRC-AW-011` | `FT4AutoFinFinal.xhtml` | Table 7 row 59 | `BSR 162`-`BSR 164` | Client mobile phone: always visible, 10 digits, default `+7 (9xx) xxx-xx-xx` mask. | Core contact channel. |
| `WP-03` | `SRC-AW-012` | `FT4AutoFinFinal.xhtml` | Table 7 row 60 | `BSR 165`-`BSR 166` | E-mail: always visible, contains `@`, only one e-mail address. | Core contact channel and format rule. |
| `WP-03` | `SRC-AW-013` | `FT4AutoFinFinal.xhtml` | Table 7 rows 61-64 | `BSR 167`-`BSR 172` | Home/work phone conditional display and add/remove buttons. | Repeatable/optional contact fields. |
| `WP-04` | `SRC-AW-014` | `FT4AutoFinFinal.xhtml` | Table 7 rows 66-68 | `BSR 173`-`BSR 178` | Contact-person surname/name/patronymic visible after add and allow text plus hyphen. | Previous narrow area plus wider related block. |
| `WP-04` | `SRC-AW-015` | `FT4AutoFinFinal.xhtml` | Table 7 row 69 | `BSR 179`-`BSR 180` | Relation to applicant list and `Иное` branch. | Closed visible value list and dependency. |
| `WP-04` | `SRC-AW-016` | `FT4AutoFinFinal.xhtml` | Table 7 rows 70-71 | `BSR 181`-`BSR 185` | Contact-person phone and birth date visibility/format/date limit. | Contact-person details. |
| `WP-04` | `SRC-AW-017` | `FT4AutoFinFinal.xhtml` | Table 7 rows 72-73 | `BSR 186`-`BSR 189` | Add contact-person row and delete row. | Repeatable block action behavior. |

## Explicitly Out Of Scope

| source area | reason |
| --- | --- |
| Table 7 rows before `BSR 115` | Personal data/passport fields are a separate subarea of section 4.3. |
| Employment/income blocks after contact-person scope | Separate domain, larger than target canary size. |
| Documents, participant windows, visual assessment, consent/check blocks | Separate 4.3 subareas already outside addresses/contacts. |
| Table 5 actions and section 4.2 list actions | Navigation/actions context only; not address/contact field behavior. |
| Previous generated test-case files and canary reports | Explicitly forbidden as source or template for this independent run. |

## Dictionary Inventory

| dict_id | source_ref | values | closed_set_decision | used_by_tc |
| --- | --- | --- | --- | --- |
| `DICT-AW-REL-001` | Table 7 row 69, `BSR 179` | `супруг/супруга`; `отец/мать`; `сестра/брат`; `теща/свекровь/тесть/свекр`; `сын/дочь`; `друг/знакомый/коллега`; `иное` | `source-list`; absence of extra values not asserted because source does not explicitly say "only" | `TC-AF43-AW-034`; `TC-AF43-AW-035` |

