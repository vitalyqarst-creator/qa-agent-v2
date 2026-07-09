# Source Parity Check

- FT package: `fts/AutoFin`
- Scope: `iteration-smoke-search-clear-context`
- DOCX source: `source/FT4AutoFinFinal.docx`
- XHTML source: `source/FT4AutoFinFinal.xhtml`
- PDF source: `source/FT4AutoFinFinal.pdf`
- DOCX extraction: manual scope selection from the main FT with XHTML table extraction as machine-readable companion
- XHTML extraction: BeautifulSoup table extraction, table index 5
- PDF extraction: `pypdf` page text extraction
- DOCX scope refs: section `4.2. Меню «Заявки в системе»`, action table row `«Очистить»`
- PDF scope refs: page 8, action table row `«Очистить»`

## Boundary Parity

| item | docx_ref | pdf_ref | status | note |
| --- | --- | --- | --- | --- |
| Section `4.2. Меню «Заявки в системе»` | main FT section 4.2 | PDF page 8 | match | Scope is inside the applications-system menu. |
| Action table row `«Очистить»` | row with business need `Очистить контекст поиска` | PDF page 8 | match | Same button/action/description found. |

## Requirement Id Inventory

| req_id | docx_ref | pdf_ref | status | source_decision | note |
| --- | --- | --- | --- | --- | --- |
| `BSR 32` | section 4.2, action table row `«Очистить»` | page 8 | match | mandatory-req-id | Preserve as `req_id` in writer ledger, matrix and test cases. |

## Table / Row Parity

| row_anchor | docx_ref | pdf_ref | docx_text | pdf_text | status | action |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | XHTML table index 5 row `«Очистить»` | PDF page 8 | `BSR 32. Система очищает фильтры, сортировки, постраничность и состояние выделения строк.` | same behavior text extracted around `BSR 32` | match | use |

## Mandatory Traceability Inputs

- Requirement IDs to preserve: `BSR 32`
- PDF-only IDs to preserve: `none`
- DOCX-only IDs to preserve: `none`
- Semantic mismatches requiring gaps: `none`

## Decision

- Scope parity status: `pass`
- Writer/reviewer rule: downstream artifacts must carry `BSR 32` and all four reset dimensions: filters, sorting, pagination and row selection.
- Open gaps/questions: `none`
