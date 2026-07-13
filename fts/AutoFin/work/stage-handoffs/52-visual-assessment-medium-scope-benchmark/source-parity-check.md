# Source Parity Check

- FT package: `fts/AutoFin`
- Scope: `visual-assessment-medium-scope-benchmark`
- DOCX source: `source/FT4AutoFinFinal.docx`
- XHTML source: `source/FT4AutoFinFinal.xhtml`
- PDF source: `source/FT4AutoFinFinal.pdf`
- DOCX extraction: `test_case_agent.resolve_sections()` plus DOCX table extraction.
- XHTML extraction: lxml HTML recovery parser with `huge_tree`; primary table/list source.
- PDF extraction: pypdf text plus rendered visual inspection.
- DOCX scope refs: `section-16` Table 4 block and `section-20` Appendix 1.
- PDF scope refs: p.34 and pp.40-41.

## Boundary Parity

| item | docx_ref | pdf_ref | status | note |
| --- | --- | --- | --- | --- |
| Table 4 visual information block | `section-16` | p.34 | `match` | Two fields and BSR behavior align. |
| Appendix 1 criteria | `section-20` | pp.40-41 | `match` | Eight groups and all values align across page break. |
| XHTML extraction | rows 182-184 plus Appendix 1 | p.34; pp.40-41 | `match` | Machine-readable rows match visual PDF text. |

## Requirement Id Inventory

| req_id | docx_ref | pdf_ref | status | source_decision | note |
| --- | --- | --- | --- | --- | --- |
| `BSR 311` | `Визуальная информация`: always visible | p.34 | `match` | `mandatory-req-id` | Preserve as visibility obligation. |
| `BSR 312` | default `Нет` | p.34 | `match` | `mandatory-req-id` | Preserve separately. |
| `BSR 313` | select `Да` -> parameters shown with multiple selection | p.34 | `match` | `mandatory-req-id` | Shares one TC with BSR 314, not one obligation. |
| `BSR 314` | parameters visible when visual info = `Да` | p.34 | `match` | `mandatory-req-id` | Same observable visibility result as BSR 313. |
| `BSR 315` | checkbox for each dictionary value | p.34 | `match` | `mandatory-req-id` | Complete Appendix 1 list required. |
| `BSR 316` | at least one value required | p.34 | `match` | `mandatory-req-id` | Exact UI mechanism not stated. |
| `BSR 317` | per-block `Другое` reveals mandatory text input | p.34 | `match` | `mandatory-req-id` | Visibility source-backed; requiredness mechanism requires calibration. |

## Table / Row Parity

| row_anchor | docx_ref | pdf_ref | docx_text | pdf_text | status | action |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` block | section-16 | p.34 | Block heading | Same heading | `match` | use |
| `SRC-002` visual info | section-16 | p.34 / BSR 311-313 | visible/default/dependency/multiple selection | same | `match` | use |
| `SRC-003` parameters | section-16 | p.34 / BSR 314-317 | visibility/checkbox/minimum/Other comment | same | `match` | use |
| `SRC-004`-`SRC-052` | section-20 | pp.40-41 | eight groups and complete values | same | `match` | use |

## Mandatory Traceability Inputs

- Requirement IDs to preserve: `BSR 311`-`BSR 317`.
- PDF-only IDs to preserve: `none`; ids are also present in XHTML/current source structure.
- No-code rows to preserve: `SRC-004`-`SRC-052`, `DICT-101`-`DICT-108`.
- Semantic mismatches requiring gaps: `none`.
- Source hashes: DOCX `c6892bfa...`; XHTML `cbf7ce8e...`; PDF `8caee78c...`.

## Decision

- Scope parity status: `pass`.
- Writer/reviewer rule: use current anchors only; preserve 52 rows, BSR 311-317 and complete dictionary.
- Open gaps/questions: `none`.
