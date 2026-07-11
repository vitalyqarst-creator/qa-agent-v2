# Source Row Inventory

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `WP-01` | Краткая информация с калькулятора | Final DOCX table 6 row 1; XHTML tr 54; PDF page 16 | `BSR 43`; `BSR 44`; `BSR 45` | `yes` | `ATOM-001`; `ATOM-002`; `ATOM-003`; `GAP-001` |
| `SRC-002` | `WP-01` | Кредитный калькулятор | Final DOCX table 6 row 2; XHTML tr 55; PDF page 16 | `BSR 46` | `yes` | `ATOM-004`; `ATOM-005`; `ATOM-006`; `GAP-001` |

## Inventory Notes

- XHTML is the mandatory row/code extraction source; DOCX supplies authoritative semantics.
- `BSR 35–38` are present in neighboring Final rows but are outside this scope.
- `ATOM-006` remains a gap-only statement for exhaustive prefill mapping.
