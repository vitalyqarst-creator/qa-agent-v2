# Source Selection

## Context

- request_summary: AutoFin-only prepared compiler contract and expanded matrix iteration.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-11`
- created_by: `Codex / ft-scope-analyzer`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative source of truth selected for the iteration. | `Final` | Exact stem matches XHTML and PDF. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable extraction source. | `Final XHTML` | Existing canonical row inventories remain the extraction basis. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural cross-check for the same FT. | `Final PDF` | Not used as a row-level replacement for XHTML. |

## Machine-Readable XHTML Source

- main_ft_xhtml: `source/FT4AutoFinFinal.xhtml`
- xhtml_available: `yes`
- xhtml_path: `source/FT4AutoFinFinal.xhtml`
- xhtml_matches_main_ft: `yes`
- xhtml_role: `mandatory_machine_readable_extraction_source`
- xhtml_required_for_downstream: `yes`
- blocking_reason: `none`

## Structural Cross-Check PDF

- pdf_available: `yes`
- pdf_path: `source/FT4AutoFinFinal.pdf`
- pdf_matches_main_ft: `yes`
- limitation: structural cross-check only; row extraction remains XHTML-first and DOCX-authoritative.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | `package-notes` | Mandatory AutoFin package context. | `yes` | Does not add requirements. |
| `support/` | `support` | May be referenced by an already confirmed scope. | `scope-dependent` | Cannot expand scope or replace FT sources. |
| `mockups/` | `mockups` | UI hints for confirmed UI scopes. | `scope-dependent` | Not a source of business rules. |

## Source Quality

- active source documents: `source/FT4AutoFinFinal.docx`; `source/FT4AutoFinFinal.xhtml`; `source/FT4AutoFinFinal.pdf`.
- parseability: confirmed by existing FT4 row-inventory and parity artifacts.
- exact source family: `FT4AutoFinFinal` only.
- forbidden evidence: `AutoFinPreFinal.*`, neighboring FT packages, generated test cases and previous cycle outputs.

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |
| `source/FT4AutoFinFinal.*` | Exact selected family exists. | selected |
| `source/AutoFinPreFinal.*` | Older family. | rejected |
| neighboring `fts/*` | Outside the authorized package boundary. | forbidden |

## Handoff

- next_skill: none while legacy obligation migrations remain.
- required_inputs: expanded matrix report and compiler contract v2 evidence.
- blocked_reasons: three large legacy scopes require semantic obligation-table migration before compilation.
