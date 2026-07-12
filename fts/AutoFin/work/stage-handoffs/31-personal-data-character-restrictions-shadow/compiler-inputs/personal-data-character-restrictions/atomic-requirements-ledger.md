# Atomic Requirements Ledger

Eval-only projection of character restrictions from section 4.3. Each invalid class remains independent. Exact UI rejection mechanics remain constrained by `GAP-001`.

| atom_id | package_id | source_refs | req_id | atomic_statement | coverage_status | covered_by_tc | constraint_gap_ids | priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `WP-01` | `SRC-002`; XHTML row 57; DOCX table 6 row 4 | `BSR 48` | Поле `Фамилия` допускает ввод текстовых символов. | `covered` | `TC-PDCR-001` |  | `High` |
| `ATOM-002` | `WP-01` | `SRC-002`; XHTML row 57; DOCX table 6 row 4 | `BSR 48` | Поле `Фамилия` допускает специальный символ `-` в текстовом значении. | `covered` | `TC-PDCR-002` |  | `High` |
| `ATOM-003` | `WP-01` | `SRC-002`; XHTML row 57; DOCX table 6 row 4 | `BSR 48` | Поле `Фамилия` не допускает цифры. | `covered_with_ui_calibration` | `TC-PDCR-003` | `GAP-001` | `High` |
| `ATOM-004` | `WP-01` | `SRC-002`; XHTML row 57; DOCX table 6 row 4 | `BSR 48` | Поле `Фамилия` не допускает специальные символы, кроме `-`. | `covered_with_ui_calibration` | `TC-PDCR-004` | `GAP-001` | `High` |
| `ATOM-005` | `WP-01` | `SRC-003`; XHTML row 58; DOCX table 6 row 5 | `BSR 51` | Поле `Имя` допускает ввод текстовых символов. | `covered` | `TC-PDCR-005` |  | `High` |
| `ATOM-006` | `WP-01` | `SRC-003`; XHTML row 58; DOCX table 6 row 5 | `BSR 51` | Поле `Имя` допускает специальный символ `-` в текстовом значении. | `covered` | `TC-PDCR-006` |  | `High` |
| `ATOM-007` | `WP-01` | `SRC-003`; XHTML row 58; DOCX table 6 row 5 | `BSR 51` | Поле `Имя` не допускает цифры. | `covered_with_ui_calibration` | `TC-PDCR-007` | `GAP-001` | `High` |
| `ATOM-008` | `WP-01` | `SRC-003`; XHTML row 58; DOCX table 6 row 5 | `BSR 51` | Поле `Имя` не допускает специальные символы, кроме `-`. | `covered_with_ui_calibration` | `TC-PDCR-008` | `GAP-001` | `High` |
| `ATOM-009` | `WP-01` | `SRC-004`; XHTML row 59; DOCX table 6 row 6 | `BSR 54` | Поле `Отчество` допускает ввод текстовых символов. | `covered` | `TC-PDCR-009` |  | `High` |
| `ATOM-010` | `WP-01` | `SRC-004`; XHTML row 59; DOCX table 6 row 6 | `BSR 54` | Поле `Отчество` допускает специальный символ `-` в текстовом значении. | `covered` | `TC-PDCR-010` |  | `High` |
| `ATOM-011` | `WP-01` | `SRC-004`; XHTML row 59; DOCX table 6 row 6 | `BSR 54` | Поле `Отчество` не допускает цифры. | `covered_with_ui_calibration` | `TC-PDCR-011` | `GAP-001` | `High` |
| `ATOM-012` | `WP-01` | `SRC-004`; XHTML row 59; DOCX table 6 row 6 | `BSR 54` | Поле `Отчество` не допускает специальные символы, кроме `-`. | `covered_with_ui_calibration` | `TC-PDCR-012` | `GAP-001` | `High` |
