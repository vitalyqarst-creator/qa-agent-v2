# Source Row Inventory

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Source: `source/FT4AutoFinFinal.xhtml`
- Extraction method: BeautifulSoup table extraction from XHTML
- Table anchor: action table under section `4.2. Меню «Заявки в системе»`

| source_row_id | xhtml_ref | req_id | column_button | column_business_need | column_action | column_description |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `table_index=5`, row `«Очистить»` | `BSR 32` | `«Очистить»` | `Очистить контекст поиска` | `Нажатие` | `Система очищает фильтры, сортировки, постраничность и состояние выделения строк.` |

## Extraction Notes

- XHTML is used as mandatory machine-readable source for the action table row.
- PDF page 8 confirms the same `BSR 32` row.
- No dictionary values are introduced by this scope.
