# Source Locator Session Log

## Inputs Read

- `fts/AutoFin/source/FT4AutoFinFinal.docx`
- `fts/AutoFin/source/FT4AutoFinFinal.xhtml`
- `fts/AutoFin/source/FT4AutoFinFinal.pdf`
- `fts/AutoFin/AGENT-NOTES.md`
- `skills/ft-source-locator/SKILL.md`

## Inputs Not Used

- Existing generated test cases under `fts/AutoFin/test-cases/`
- Previous canary artifacts under `fts/AutoFin/work/canary-runs/`
- `source/AutoFinPreFinal.*`

## Key Decisions

- Selected FT package: `AutoFin`.
- Selected main source set: `FT4AutoFinFinal.docx`, `FT4AutoFinFinal.xhtml`, `FT4AutoFinFinal.pdf`.
- Confirmed XHTML availability: `yes`.

## Risks / Fallbacks

- PDF row-level text extraction is not clean; XHTML/DOCX are used for selected row evidence.

## Validation

- Runtime probe executed before shell work.
- DOCX section extraction and XHTML row extraction succeeded.

## Contamination Check

- Old generated test cases and canary work artifacts were not used as requirement source or template.

## Event Timeline

| event | status |
| --- | --- |
| Runtime probe | completed |
| FT package source inventory | completed |
| XHTML availability check | completed |
| Handoff to scope analyzer | completed |

## Quality Checkpoints

- Source selection has `selection_status: selected`.
- XHTML source has `xhtml_available: yes`.

## Technical Fallbacks

| id | issue | fallback | status |
| --- | --- | --- | --- |
| `TF-001` | Console stdout uses cp1251 and can display Cyrillic as mojibake. | Used JSON `ensure_ascii` for source extraction evidence. | applied |

## Handoff Notes For Next Session

- Continue with scope `iteration-smoke-widget-selection-types`.
