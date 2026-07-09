# Source Row Inventory

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Source: `source/FT4AutoFinFinal.xhtml`
- Extraction method: BeautifulSoup table extraction from XHTML
- Table anchor: action table under section `4.2. Меню «Заявки в системе»`

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `WP-BSR32` | `button «Очистить» / Очистить контекст поиска / Нажатие` | `FT4AutoFinFinal.xhtml`, section `4.2`, table index 5 row `«Очистить»`; PDF page 8 | `BSR 32` | `yes` | `ATOM-001; ATOM-002; ATOM-003; ATOM-004` |

## Extraction Notes

- XHTML is used as mandatory machine-readable source for the action table row.
- PDF page 8 confirms the same `BSR 32` row.
- No dictionary values are introduced by this scope.
- `SRC-001` contains four reset properties; writer-side Source Row Completeness Matrix must keep each property linked to `BSR 32`.
