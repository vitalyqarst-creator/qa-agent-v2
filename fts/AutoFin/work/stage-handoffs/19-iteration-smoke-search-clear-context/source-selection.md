# Source Selection

## Context

- request_summary: rerun end-to-end session-based iteration smoke after runner completion fix
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-09`
- created_by: `Codex`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Source of truth for AutoFin FT section 4.2. | `2026`, document history has `v2.0` on `22.06.2026` | DOCX parseability has section-id/oversized-block risks; XHTML is mandatory for table rows. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable extraction source for action table row `«Очистить»`. | same main FT package | Used for table index 5 row extraction. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural/visual cross-check for section and `BSR 32`. | same main FT package | PDF page 8 confirms relevant row. |

## Machine-Readable XHTML Source

- main_ft_xhtml: `FT4AutoFinFinal.xhtml`
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
- limitation: `PDF is structural/visual cross-check only; behavior remains sourced from DOCX with XHTML extraction.`

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | package notes | Defines AutoFin table shorthand and DaData limits. | `yes` | Does not add new requirements. |
| prior `test-cases/**` | historical artifacts | Existing generated artifacts are contamination risk for this clean rerun. | `no` | Not a source of truth or template. |
| `work/review-cycles/iteration-smoke-widget-selection-types/*` | historical process evidence | Used only for blocked-state regression check. | `no` | Not a source of requirements or wording. |

## Source Quality

- active source documents: `source/FT4AutoFinFinal.docx`, `source/FT4AutoFinFinal.xhtml`, `source/FT4AutoFinFinal.pdf`
- parseability: selected scope row was extracted from XHTML and cross-checked in PDF
- section-id confidence: section `4.2` confirmed from document contents/table of contents
- oversized blocks: package-level validator reports DOCX oversized/source-section risks outside this selected row
- strict warnings: none blocking for selected `BSR 32` row; row-level extraction uses XHTML

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` / `.xhtml` / `.pdf` | Main FT set is present and aligned for selected row. | Use as selected source package. |
| prior generated smoke artifacts | Could contaminate clean rerun. | Exclude as source/template; use only historical blocked-state process evidence. |

## Exclusions

- Old `test-cases/**` and review-cycle outputs are not source inputs.
- The historical `iteration-smoke-widget-selection-types` run is process evidence only and is not a wording or test-design template.

## Handoff

- next_skill: `ft-test-case-iteration`
- required_inputs:
  - `AGENT-NOTES.md`
  - `source/FT4AutoFinFinal.docx`
  - `source/FT4AutoFinFinal.xhtml`
  - `source/FT4AutoFinFinal.pdf`
  - `work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-contract.md`
  - `work/stage-handoffs/19-iteration-smoke-search-clear-context/source-row-inventory.md`
  - `work/stage-handoffs/19-iteration-smoke-search-clear-context/source-parity-check.md`
  - `work/stage-handoffs/19-iteration-smoke-search-clear-context/scope-coverage-gaps.md`
- latest_artifacts:
  - `work/review-cycles/iteration-smoke-search-clear-context/cycle-state.yaml`
- blocked_reasons: `none at source-selection stage`
