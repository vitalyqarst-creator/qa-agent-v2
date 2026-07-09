# Source / Scope Inventory

## Source Artifacts Used

| artifact | role | status | notes |
| --- | --- | --- | --- |
| `fts/AutoFin/source/FT4AutoFinFinal.docx` | authoritative main FT | used | DOCX section `3 Ограничения` confirms the meaning of selected rows. |
| `fts/AutoFin/source/FT4AutoFinFinal.xhtml` | mandatory machine-readable source | used | XHTML table extraction produced rows `SRC-001` and `SRC-002`; paragraph extraction produced `SRC-003`. |
| `fts/AutoFin/source/FT4AutoFinFinal.pdf` | structural cross-check | used | PDF page 5 confirms the selected block; row-level text is not used as primary evidence. |
| `fts/AutoFin/AGENT-NOTES.md` | package context | used | Confirms package-specific rules; no added source requirement for this scope. |

## Scope Inventory

| source_row_id | section | source text summary | included | reason |
| --- | --- | --- | --- | --- |
| `SRC-001` | `3 Ограничения` | Data type `Список`: dictionary values, only one value can be selected. | yes | Directly testable widget value selection constraint. |
| `SRC-002` | `3 Ограничения` | Data type `Список с множественным выбором`: dictionary values, several values can be selected. | yes | Directly testable widget value selection constraint. |
| `SRC-003` | `3 Ограничения` | Default widget values are absent and interpreted as `NULL`. | yes | Directly testable initial/default value constraint if the implementation exposes an empty widget. |

## Out Of Scope

- Date, datetime, numeric, text, boolean and binary type restrictions from the same table.
- Concrete fields from sections `7`, `16` and later sections unless the writer uses them only as source-backed fixtures and keeps traceability to this scope.
- Persistence behavior, database storage, API effects and save-flow behavior.
- Previous canary artifacts and old generated test-case wording.

## Contamination Control

- Not used as source of truth: `fts/AutoFin/test-cases/*`.
- Not used as templates: `fts/AutoFin/work/canary-runs/*`.
- Not touched: unrelated untracked diagnostics under `evals/sdk-turn-diagnostics/`.
- Not touched: untracked `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`.
