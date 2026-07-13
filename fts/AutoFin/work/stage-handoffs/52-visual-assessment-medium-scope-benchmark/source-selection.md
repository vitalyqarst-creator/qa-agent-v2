# Source Selection

## Context

- request_summary: current-source medium-scope prepared exec benchmark.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-13`
- created_by: `Codex / ft-scope-analyzer`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative current source of truth. | `Final` | `resolve_sections()` found relevant `section-16` and `section-20`. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable extraction source. | `Final XHTML` | Relevant Table 4 rows are 182-184. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural/visual cross-check. | `Final PDF` | Relevant pages are 34, 40 and 41. |

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
- limitation: PDF confirms layout and BSR 311-317; XHTML remains the row/list extraction source and DOCX remains authoritative for meaning.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | `package-notes` | Mandatory package context. | `yes` | Does not add requirements. |
| `open-scope-coverage-gaps_ответы Соболева.md` | `analyst-answer` | Confirms standalone `Комментарий` rows as separate inputs. | `yes` | Applies only to the answered mapping ambiguity. |
| `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | `mockup` | Confirms visible checkbox/comment mechanics. | `yes` | UI hints only; not a business-rule source. |

## Source Quality

- scope boundary: Table 4 block `Визуальная информация` plus Appendix 1 only.
- current requirement codes: `BSR 311`-`BSR 317`.
- current PDF refs: p.34 and pp.40-41.
- current XHTML refs: rows 182-184 plus Appendix 1 list structure.
- forbidden evidence: `AutoFinPreFinal.*`, production test cases, review-cycle outputs, user-owned untracked draft.

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |
| `source/FT4AutoFinFinal.*` | Exact current DOCX/XHTML/PDF family exists. | `selected` |
| `source/AutoFinPreFinal.*` | Legacy anchors and BSR values are stale. | `rejected` |
| production test cases / prior outputs | Historical results could contaminate requirement extraction. | `forbidden as requirement evidence` |

## Handoff

- next_skill: `ft-test-case-iteration` after scope gates.
- blocked_reasons: none at source-selection stage.
