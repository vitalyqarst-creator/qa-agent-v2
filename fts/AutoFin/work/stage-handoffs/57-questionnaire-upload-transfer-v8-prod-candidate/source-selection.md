# Source Selection — Questionnaire Upload Transfer V8 Prod Candidate

## Context

- request_summary: новая immutable revision после H56 routing blocker; открытый non-blocking gap сохраняется.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-14`
- created_by: `Codex / ft-scope-analyzer`

## Main FT Documents

| path | role | selection_reason | sha256 | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Авторитетный source of truth. | `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b` | Таблица 6, строки 81–82. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Обязательный extraction source. | `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66` | Строки 134–135; BSR 206–212. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Structural/visual cross-check. | `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58` | Страницы 26–27. |

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
- limitation: PDF используется только для кодов, структуры и visual cross-check.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | `package-notes` | Расшифровывает `О/Р` и ограничивает внешний context. | `yes` | Не добавляет новых требований. |
| `work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/scope-gap-review.md` | `process-evidence` | Фиксирует routing blocker H56. | `yes` | Не является requirement source. |

Mockups для выбранного source-fidelity scope не требуются.

## Source Quality

- source family: только `FT4AutoFinFinal.*` с зафиксированными hashes.
- mandatory XHTML: доступен и совпадает с DOCX/PDF scope.
- known extraction risk: oversized section-16 block компенсирован bounded row inventory и XHTML anchors.
- production test cases: запрещены как requirement evidence.

## Ambiguity And Decision Log

| candidate | issue | decision |
| --- | --- | --- |
| `FT4AutoFinFinal.*` | Три представления одного Final. | selected with parity |
| `GAP-QUT-001` | `40 МБ` без byte convention. | keep open-non-blocking; no exact bytes |
| H56 routing | Active prompt противоречил canonical reviewer contract. | superseded by new H57 review route |
| H56 compiler semantics | Требования и fidelity checks прошли review. | carried forward in new immutable scope slug |
| V6/V7 drafts и production TC | Производные результаты. | forbidden as requirement evidence |

## Handoff

- next_skill: `ft-test-case-reviewer` в режиме `scope_gap_review`.
- blocked_reasons: none.
