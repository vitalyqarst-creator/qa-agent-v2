# Source Parity Check

## Context

- Scope: `application-card-calculator-summary-entrypoints`
- DOCX: `source/FT4AutoFinFinal.docx`, SHA-256 `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b`.
- XHTML: `source/FT4AutoFinFinal.xhtml`, SHA-256 `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66`.
- PDF: `source/FT4AutoFinFinal.pdf`, SHA-256 `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58`.
- Evidence: `final-bsr-evidence.json`.

## Section / Structure Parity

| subject | docx_ref | xhtml_ref | pdf_ref | status | note |
| --- | --- | --- | --- | --- | --- |
| Calculator-summary table | table 6 rows 1–2 | table rows 54–55 | page 16, table 4 | `pass` | The same two UI rows and semantics are present. |
| Neighboring common actions | table 5 rows 4–5 | rows 49–50 | page 9 | `pass` | `BSR 35–38` belong to other actions and are excluded. |

## Requirement Id Inventory

| req_id | docx_ref | xhtml_ref | pdf_ref | status | source_decision | note |
| --- | --- | --- | --- | --- | --- | --- |
| `BSR 43` | table 6 row 1 semantic clause | row 54 | page 16 | `xhtml-pdf-code` | `mandatory-req-id` | Always-visible widget. |
| `BSR 44` | table 6 row 1 semantic clause | row 54 | page 16 | `xhtml-pdf-code` | `mandatory-req-id` | Five summary parameters from calculator stage. |
| `BSR 45` | table 6 row 1 semantic clause | row 54 | page 16 | `xhtml-pdf-code` | `mandatory-req-id` | Widget navigation. |
| `BSR 46` | table 6 row 2 semantic clause | row 55 | page 16 | `xhtml-pdf-code` | `mandatory-req-id` | Window opening with prefilled application data. |

## Table / Row Parity

| row_anchor | docx_ref | xhtml_ref | pdf_ref | semantic_status | code_status | action |
| --- | --- | --- | --- | --- | --- | --- |
| `Краткая информация с калькулятора` | table 6 row 1 | row 54 | page 16 | `pass` | `BSR 43–45` in XHTML/PDF | Use as `SRC-001`; preserve five-value list. |
| `Кредитный калькулятор` | table 6 row 2 | row 55 | page 16 | `pass` | `BSR 46` in XHTML/PDF | Use as `SRC-002`; split observable prefill from exact-mapping gap. |

## Source Differences

- DOCX matching rows do not contain visible BSR labels, while XHTML and PDF do; the semantic clauses match.
- DOCX extraction duplicates some merged cells, so XHTML is used for row/list structure and DOCX for meaning.
- No semantic contradiction was found between the three Final representations.

## Mandatory Traceability Inputs

- Requirement IDs: `BSR 43`; `BSR 44`; `BSR 45`; `BSR 46`.
- PDF/XHTML-only IDs remain mandatory in ledger and test cases.
- Source rows: `SRC-001`; `SRC-002`.
- Residual uncertainty: `GAP-001` for exhaustive prefill fields and exact mapping only.

## Decision

- Scope parity status: `pass-with-non-blocking-gap`.
- Writer/reviewer may proceed only after `scope_gap_review` passes.
- `BSR 35–38` must not appear in active calculator-summary traceability.
