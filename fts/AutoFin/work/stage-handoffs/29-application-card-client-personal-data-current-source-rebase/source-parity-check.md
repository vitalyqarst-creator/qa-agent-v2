# Source Parity Check

- FT package: `fts/AutoFin`.
- Scope: `application-card-client-personal-data`.
- DOCX: `source/FT4AutoFinFinal.docx`, table 6 rows 3–13, `python-docx`.
- XHTML: `source/FT4AutoFinFinal.xhtml`, table rows 56–66, `lxml` XHTML-first extraction.
- PDF: `source/FT4AutoFinFinal.pdf`, pages 16–17, `pypdf` cross-check.
- Evidence: `final-bsr-evidence.json`.

## Boundary Parity

| item | docx_ref | xhtml_ref | pdf_ref | status | note |
| --- | --- | --- | --- | --- | --- |
| Start | table 6 row 3 block header | tr 56 | p.16 | `match` | Calculator rows end before this block. |
| Personal-data rows | table 6 rows 4–13 | tr 57–66 | pp.16–17 | `match` | Meaning/ordering agree. |
| End | row 13 previous patronymic | tr 66 | p.17 | `match` | Recognition button `BSR 78` starts out of scope. |

## Requirement Id Inventory

| source rows | req_ids | docx | xhtml | pdf | decision |
| --- | --- | --- | --- | --- | --- |
| `SRC-002..SRC-004` | `BSR 47–55` | behavior without labels | present | present p.16 | mandatory IDs from XHTML/PDF |
| `SRC-005..SRC-008` | `BSR 56–65` | behavior without labels | present | pp.16–17 | mandatory IDs from XHTML/PDF |
| `SRC-009..SRC-011` | `BSR 66–77` | behavior without labels | present | p.17 | mandatory IDs from XHTML/PDF |

## Table / Row Parity

| row_anchor | docx_ref | xhtml_ref | pdf_ref | status | action |
| --- | --- | --- | --- | --- | --- |
| `SRC-001` block | table 6 row 3 | tr 56 | p.16 | `match` | use |
| `SRC-002..SRC-011` | table 6 rows 4–13 | tr 57–66 | pp.16–17 | `match` | use XHTML IDs, DOCX meaning |
| Recognition neighbor | table 6 row 14 | tr 67 | p.17 | `match-out-of-scope` | exclude |

## Mandatory Traceability Inputs

- Preserve all IDs `BSR 47–77`.
- PDF-only IDs: none; labels are present in both XHTML and PDF but absent from DOCX table extraction.
- Semantic mismatches: none found.
- Extraction risk: DOCX contains duplicated logical columns in table extraction; normalize from XHTML and cross-check meaning in DOCX.

## Historical Baseline Delta

- Historical handoff `06` used `AutoFinPreFinal.*` and originally mapped rows to `BSR 39–69`.
- Canonical file later received partial BSR backfill and two additional cases without a new complete reviewer loop.
- Current writer must rebuild ledger/design artifacts from `BSR 47–77`, then reuse only semantically matching case content.

## Decision

- Scope parity status: `pass-with-extraction-risk`.
- Writer/reviewer rule: XHTML-first row/ID map, DOCX-authoritative semantics, PDF structural cross-check.
- Open gaps: `GAP-001..GAP-003`.
