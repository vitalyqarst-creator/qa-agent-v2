# Source Selection

## Context

- request_summary: AutoFin-only prepared compiler cross-scope validation.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-11`
- created_by: `Codex / ft-source-locator`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Explicit continuation boundary and authoritative source of truth. | `Final` | Exact stem matches XHTML and PDF. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable extraction source. | `Final XHTML` | Used by existing selected-scope row inventories. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural cross-check for the same FT. | `Final PDF` | Not used as row-level replacement for XHTML. |

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
- parseability: confirmed by existing FT4 source-selection, row-inventory and parity artifacts.
- section-id confidence: high for selected existing scopes with explicit section and source rows.
- oversized blocks: full XHTML is large; compiler reads only canonical prepared evidence artifacts.
- strict warnings: `AutoFinPreFinal.*`, neighboring `fts/*`, generated TC and previous cycle outputs are forbidden as requirement evidence.

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |
| `fts/AutoFin/source/FT4AutoFinFinal.*` | Exact requested source family exists. | selected |
| `fts/AutoFin/source/AutoFinPreFinal.*` | Older source family used by legacy scopes. | rejected for this validation |
| neighboring `fts/*` | Outside user-authorized FT boundary. | forbidden |

## Handoff

- next_skill: `agent-architecture-auditor / prepared compiler preflight`
- required_inputs: this source selection, compiler workflow snapshots, existing FT4 canonical design artifacts.
- latest_artifacts: `scope-matrix.md`, `workflow-state.yaml`, `source-locator-session-log.md`, `agent-decision-log.md`.
- blocked_reasons: none.
