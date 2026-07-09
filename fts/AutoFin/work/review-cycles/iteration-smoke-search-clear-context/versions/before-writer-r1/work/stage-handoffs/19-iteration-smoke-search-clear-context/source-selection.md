# Source Selection

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Selected main FT DOCX: `source/FT4AutoFinFinal.docx`
- Selected main FT XHTML: `source/FT4AutoFinFinal.xhtml`
- Selected main FT PDF: `source/FT4AutoFinFinal.pdf`
- Package notes: `AGENT-NOTES.md`
- Selection status: `selected`

## Source Roles

| artifact | role | downstream rule |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | main source of truth | Requirement behavior comes from this FT. |
| `source/FT4AutoFinFinal.xhtml` | mandatory machine-readable extraction source | Used for table row extraction and row inventory. |
| `source/FT4AutoFinFinal.pdf` | structural/visual cross-check | Used to verify section/page and requirement id presence. |
| `AGENT-NOTES.md` | package-specific context | Only abbreviation/context rules; does not add requirements. |

## Exclusions

- Old `test-cases/**` and review-cycle outputs are not source inputs.
- The historical `iteration-smoke-widget-selection-types` run is process evidence only and is not a wording or test-design template.
