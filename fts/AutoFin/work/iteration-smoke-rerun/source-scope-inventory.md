# Source / Scope Inventory

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Section: `4.2. Меню «Заявки в системе»`
- Handoff directory: `work/stage-handoffs/19-iteration-smoke-search-clear-context`
- Review-cycle directory: `work/review-cycles/iteration-smoke-search-clear-context`
- Intended canonical artifact after sign-off: `test-cases/4.2-iteration-smoke-rerun-search-clear-context.md`

## Sources Used

| source | role | status |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | source of truth | selected |
| `source/FT4AutoFinFinal.xhtml` | mandatory machine-readable extraction source | selected |
| `source/FT4AutoFinFinal.pdf` | structural/visual cross-check | selected |
| prior generated `test-cases/**` | source/template | excluded |

## Source Rows

| row_id | source_ref | req_id | button | business_need | action | requirement_text |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `FT4AutoFinFinal.xhtml`, table index 5, action table row `«Очистить»` | `BSR 32` | `«Очистить»` | `Очистить контекст поиска` | `Нажатие` | `Система очищает фильтры, сортировки, постраничность и состояние выделения строк.` |

## PDF Cross-Check

`BSR 32` is present in `source/FT4AutoFinFinal.pdf` on page 8 with the same button row and behavior. No PDF-only id or semantic mismatch was found for this scope.

## Constraints For Writer

- Preserve `BSR 32` as the requirement id in ledger, matrix and test-case source references.
- Do not invent concrete filter fields, default sort values, page size, pagination text, row count or messages unless the source or UI evidence provides them.
- Expected results may compare the post-clear state with the observable initial/default state of the same UI.
