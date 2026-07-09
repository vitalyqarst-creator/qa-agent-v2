# Source Parity Check

## Context

- FT package: `AutoFin`
- Scope slug: `iteration-smoke-widget-selection-types`
- DOCX: `source/FT4AutoFinFinal.docx`
- XHTML: `source/FT4AutoFinFinal.xhtml`
- PDF: `source/FT4AutoFinFinal.pdf`
- Checked scope: section `3 Ограничения`, selected rows `SRC-001`..`SRC-003`

## Structure Parity

| item | DOCX | XHTML | PDF | decision |
| --- | --- | --- | --- | --- |
| Section `3 Ограничения` | found | found | found | `pass` |
| Data type restrictions table | found | found | found on page 5 | `pass` |
| Row `Список` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Row `Список с множественным выбором` | found | found | PDF table extraction not used row-level | `pass-with-limitation` |
| Default widget values paragraph | found | found | found on page 5 | `pass` |

## Requirement Code Parity

| source_row_id | DOCX BSR | XHTML BSR | PDF BSR | decision |
| --- | --- | --- | --- | --- |
| `SRC-001` | none | none | none | `no_code_expected` |
| `SRC-002` | none | none | none | `no_code_expected` |
| `SRC-003` | none | none | none | `no_code_expected` |

## Limitations

- PDF structural cross-check is sufficient for section/block presence, but row-level extraction is not clean enough to use as primary source.
- No discrepancy between DOCX and XHTML was found for the selected source rows.
