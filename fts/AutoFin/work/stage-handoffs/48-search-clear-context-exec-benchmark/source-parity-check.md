# Source Parity Check

## Source Parity Check

- FT package: `fts/AutoFin`
- Scope: `search-clear-context-exec-benchmark-v1`
- DOCX source: `source/FT4AutoFinFinal.docx`
- XHTML source: `source/FT4AutoFinFinal.xhtml`
- PDF source: `source/FT4AutoFinFinal.pdf`
- DOCX extraction: `scripts/extract_autofin_bsr_evidence.py`, table 5 row 2
- XHTML extraction: same helper, global XHTML row 47
- PDF extraction: same helper, page 8
- DOCX scope refs: section `4.2`, action row `Очистить`
- PDF scope refs: page `8`, `BSR 32`

## Boundary Parity

| item | docx_ref | pdf_ref | status | note |
| --- | --- | --- | --- | --- |
| section 4.2 action table | DOCX table 5 | PDF p.8 | `match` | Button, business need, click and result remain inside applications menu. |
| BSR 32 row | DOCX table 5 row 2 | PDF p.8 | `match` | Same four reset dimensions. |

## Requirement Id Inventory

| req_id | docx_ref | pdf_ref | status | source_decision | note |
| --- | --- | --- | --- | --- | --- |
| `BSR 32` | DOCX table 5 row 2; list label not exposed by python-docx | PDF p.8 | `xhtml/pdf-code-visible` | `mandatory-req-id` | Preserve in all four atoms/TCs. |

## Table / Row Parity

| row_anchor | docx_ref | pdf_ref | docx_text | pdf_text | status | action |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | XHTML table 5 row 47; DOCX table 5 row 2 | PDF p.8 | `Очистить` resets filters, sorting, pagination and row selection | same | `match` | `use` |

## Mandatory Traceability Inputs

- Requirement IDs to preserve: `BSR 32`.
- PDF-only IDs to preserve: `none`.
- DOCX-only IDs to preserve: `none`.
- Semantic mismatches requiring gaps: `none`.

## Decision

- Scope parity status: `pass`.
- Writer/reviewer rule: preserve all four BSR 32 properties independently; absence of any property is blocking traceability loss.
- Open gaps/questions: `none`.
