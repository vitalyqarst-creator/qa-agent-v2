# Source Selection

## Context

- Request summary: run an end-to-end iteration smoke on a new small scope from `FT4AutoFinFinal`.
- Selected FT slug: `AutoFin`
- selected_ft_slug: `AutoFin`
- Selection status: `selected`
- selection_status: `selected`
- Created at: `2026-07-09`
- Created by: `codex`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | User explicitly requested `FT4AutoFinFinal` as source of truth. | not extracted | Parsed by `test_case_agent.resolve_sections()` for DOCX section evidence. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable extraction source for tables/rows/lists. | not extracted | Parsed with `bs4`; selected rows found in section `3`. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural cross-check for the same FT package. | not extracted | PDF extraction confirms selected block on page 5; row-level table evidence remains XHTML/DOCX. |
| `source/FT4AutoFinFinal.mht` | `main-ft-other` | Same named source artifact available in package. | not used | Not required for this scope. |

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
- limitation: PDF text extraction is line-wrapped and not used as row-level source evidence.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | package notes | Package-specific context required by project rules. | yes | Does not add requirements for this scope. |
| `support/` | support files | No support file needed for selected section `3`. | no | Must not expand scope. |
| `mockups/` | mockups | No mockup is required for this global constraint scope. | no | Mockups are not source of business rules. |

## Source Quality

- active source documents: `source/FT4AutoFinFinal.docx`, `source/FT4AutoFinFinal.xhtml`, `source/FT4AutoFinFinal.pdf`
- parseability: DOCX section extraction succeeded; XHTML table row extraction succeeded; PDF page/block check succeeded with text wrapping limitations.
- section-id confidence: `high` for DOCX section `3 Ограничения`.
- oversized blocks: none for selected scope.
- strict warnings: none found for selected scope.

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |
| `source/AutoFinPreFinal.docx` | Earlier package version present. | Not selected; user requested `FT4AutoFinFinal`. |
| `fts/AutoFin/test-cases/*` | Existing generated artifacts present. | Not used as source of truth or template. |
| `fts/AutoFin/work/canary-runs/*` | Previous canary artifacts present. | Not used as source or template. |

## Handoff

- next_skill: `ft-scope-analyzer`
- required_inputs: `source-selection.md`, `source/FT4AutoFinFinal.docx`, `source/FT4AutoFinFinal.xhtml`, `source/FT4AutoFinFinal.pdf`, `AGENT-NOTES.md`
- latest_artifacts: `source-selection.md`
- blocked_reasons: `none`
