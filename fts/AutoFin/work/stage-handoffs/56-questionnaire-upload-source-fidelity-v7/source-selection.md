# Source Selection

## Context

- request_summary: V7 source-fidelity package по загрузке анкеты клиента без изменения FT-first baseline.
- selected_ft_slug: `AutoFin`
- selection_status: `selected`
- created_at: `2026-07-14`
- created_by: `Codex / ft-scope-analyzer`

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Авторитетный source of truth для текущего Final. | `Final` | Таблица 6, строки 81-82. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Обязательный машиночитаемый источник BSR и структуры строк. | `Final XHTML` | Строки таблицы 134-135; BSR 206-212. |
| `source/FT4AutoFinFinal.pdf` | `main-ft-pdf` | Визуальная и структурная сверка. | `Final PDF` | Страницы 26-27; BSR 206-212. |

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
- limitation: PDF используется только для кодов/структуры/визуальной сверки; текстовая истина остаётся в DOCX.

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |
| `AGENT-NOTES.md` | `package-notes` | Расшифровывает колонки `О` и `Р`; ограничивает внешний DaData context. | `yes` | Не добавляет новых требований. |

## Source Quality

- source family: только `FT4AutoFinFinal.*`.
- rejected: `AutoFinPreFinal.*` и созданные по нему старые BSR mappings.
- machine-readable status: XHTML подтверждён.
- production test cases: запрещены как requirement evidence.

## Ambiguity And Decision Log

| candidate | issue | decision |
| --- | --- | --- |
| `source/FT4AutoFinFinal.*` | Три источника имеют одинаковый Final stem и подтверждённую parity. | selected |
| `source/AutoFinPreFinal.*` | Legacy BSR mapping расходится с текущим Final. | rejected |
| production test cases | Производный результат, а не source of truth. | forbidden as requirement evidence |

## Handoff

- next_skill: `ft-scope-analyzer / source-fidelity compilation`.
- required_inputs: этот source selection, `AGENT-NOTES.md`, bounded parity и scope artifacts.
- blocked_reasons: none.
