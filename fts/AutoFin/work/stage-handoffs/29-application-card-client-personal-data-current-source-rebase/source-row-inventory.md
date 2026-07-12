# Source Row Inventory

Primary extraction: `FT4AutoFinFinal.xhtml`, Table 4, XHTML rows `56–66`; DOCX table `6`, rows `3–13`; PDF pages `16–17`.

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `WP-01` | Блок `Персональные данные` | XHTML tr 56; DOCX table 6 row 3 | `none` | `yes` | `ATOM-001` |
| `SRC-002` | `WP-01` | Фамилия | XHTML tr 57; DOCX table 6 row 4; PDF p.16 | `BSR 47–49` | `yes` | `ATOM-002..ATOM-006; GAP-001; GAP-002` |
| `SRC-003` | `WP-01` | Имя | XHTML tr 58; DOCX table 6 row 5; PDF p.16 | `BSR 50–52` | `yes` | `ATOM-007..ATOM-011; GAP-001; GAP-002` |
| `SRC-004` | `WP-01` | Отчество | XHTML tr 59; DOCX table 6 row 6; PDF p.16 | `BSR 53–55` | `yes` | `ATOM-012..ATOM-016; GAP-001` |
| `SRC-005` | `WP-01` | ID клиента | XHTML tr 60; DOCX table 6 row 7; PDF p.16 | `BSR 56–57` | `yes` | `ATOM-017..ATOM-018; GAP-003` |
| `SRC-006` | `WP-01` | Пол | XHTML tr 61; DOCX table 6 row 8; PDF p.16 | `BSR 58–59` | `yes` | `ATOM-019..ATOM-020; GAP-002; GAP-003` |
| `SRC-007` | `WP-01` | Дата рождения | XHTML tr 62; DOCX table 6 row 9; PDF pp.16–17 | `BSR 60–63` | `yes` | `ATOM-021..ATOM-025; GAP-001; GAP-002` |
| `SRC-008` | `WP-01` | Клиент менял ФИО | XHTML tr 63; DOCX table 6 row 10; PDF p.17 | `BSR 64–65` | `yes` | `ATOM-026..ATOM-027` |
| `SRC-009` | `WP-02` | Предыдущая фамилия | XHTML tr 64; DOCX table 6 row 11; PDF p.17 | `BSR 66–69` | `yes` | `ATOM-028..ATOM-032; GAP-001; GAP-002; GAP-003` |
| `SRC-010` | `WP-02` | Предыдущее имя | XHTML tr 65; DOCX table 6 row 12; PDF p.17 | `BSR 70–73` | `yes` | `ATOM-033..ATOM-037; GAP-001; GAP-002; GAP-003` |
| `SRC-011` | `WP-02` | Предыдущее отчество | XHTML tr 66; DOCX table 6 row 13; PDF p.17 | `BSR 74–77` | `yes` | `ATOM-038..ATOM-042; GAP-001; GAP-002; GAP-003` |

## Inventory Notes

- `SRC-012` recognition button / `BSR 78–83` is the first excluded neighboring row.
- Writer must preserve all 11 rows and decompose every BSR/property through a Source Row Completeness Matrix.
- `ATOM-*` ranges are stable planned mappings for downstream decomposition; writer must materialize each ID or document a source-backed remap.
- Historical mappings `BSR 39–69` are stale for this source version and must not be copied.
