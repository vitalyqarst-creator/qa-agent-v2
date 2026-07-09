# Agent Decision Log

| id | order | type | input | decision | rationale | risk | status |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | source-selection | `source/FT4AutoFinFinal.docx`; `source/FT4AutoFinFinal.xhtml`; `source/FT4AutoFinFinal.pdf`; `AGENT-NOTES.md` | Use `FT4AutoFinFinal` as source package and XHTML as row extraction source. | Project rules require DOCX source of truth and mandatory XHTML extraction. | PDF is only a cross-check, not behavior source. | applied |
| `DEC-002` | 2 | scope-selection | Section `4.2`, `BSR 32` | Select `iteration-smoke-search-clear-context`. | Small one-row source-backed scope suitable for end-to-end iteration smoke; independent of previous section 3 widget smoke. | The exact default sort/page-size values are not source-defined. | applied |
| `DEC-003` | 3 | runner-routing | `session-based-review-cycle-format.md` | Start cycle at `scope-ready-for-writer` with active writer prompt. | No blocking scope gaps were identified; separate writer/reviewer stages must be started by the runner. | Live SDK may be unavailable or may fail to advance state. | applied |
