# Save-flow source review

## Sources checked

| source | checked section | result |
|---|---|---|
| `fts/AutoFin/source/FT4AutoFinFinal.xhtml` | Section 4.2 actions table; section 4.3 card field table; appendix mapping rows | `BSR 35` found as reopen path. Exact save action, save success signal, exit-after-save flow, cleanup/isolation and application date source for `D` were not found for section 4.3 persistence execution. |
| `fts/AutoFin/source/FT4AutoFinFinal.docx` | Main FT DOCX text extraction cross-check | Confirmed source text contains `Отношение к заявителю`, `Перейти в выбранную заявку`, `сохранения заявки`, and `текущая дата`; `Отношение к клиенту` was not found in extracted main source text. |
| `fts/AutoFin/source/FT4AutoFinFinal.pdf` | Main FT PDF text extraction cross-check | Confirmed source text contains `Отношение к заявителю`, `сохранения заявки`, and `текущая дата`; exact save action was not found in extracted PDF text. |
| `fts/AutoFin/AGENT-NOTES.md` | Package-specific notes | No save-flow, cleanup or relation-field override for section 4.3. Notes only constrain DaData usage and source priority. |

## Save action evidence

| question | source-backed answer | source reference | confidence |
|---|---|---|---|
| Exact action to save card changes in section 4.3 | not found | No section 4.3 row names a save control/action for card edits. Source mentions effects after saving in some fields, but not the user action. | high that source is missing the action |
| Manual save vs autosave | not found | No source row says autosave or manual save for section 4.3 card edits. | high that source is missing this distinction |
| Save success oracle | not found | No source row gives success notification, disabled control, transition, or other observable save-success signal for section 4.3 edits. | high that source is missing the oracle |
| Behavior after save | not found | Section 4.3 field rows do not define whether the user remains in the card, moves to a list, sees a notification, or enters another state after saving. | high that source is missing post-save behavior |

## Reopen path evidence

| question | source-backed answer | source reference | confidence |
|---|---|---|---|
| How to reopen the same application card | Select exactly one application row in the applications table and use `Продолжить` / `Перейти в выбранную заявку`. | `FT4AutoFinFinal.xhtml` lines 855-860; `BSR 35`: the system opens the selected application card within role permissions. | high |
| Is `BSR 35` enough to identify the same application after save | Partially. It defines opening a selected application card, but not the search/filter steps needed to locate the same saved application. | `BSR 35` plus section 4.2 table context. | medium |

## Cleanup/isolation evidence

| question | source-backed answer | source reference | confidence |
|---|---|---|---|
| Use isolated application vs restore shared data | not found | No source artifact defines persistence smoke test data isolation or restore procedure. | high that source is missing cleanup policy |
| Delete created phone/contact rows after smoke | Partially source-backed at UI action level, not cleanup strategy level. Phone/contact delete controls exist, but safe cleanup procedure after save/reopen is not defined. | `BSR 172`; `BSR 188`; `BSR 189`. | medium |
| Restore changed scalar fields | not found | No source artifact defines restoring previous address, phone or email values after test execution. | high that source is missing restore policy |

## Date source evidence

| question | source-backed answer | source reference | confidence |
|---|---|---|---|
| Source of current application date `D` | not found | `BSR 185` says contact-person birth date cannot be greater than current date, but does not define UI business date, server date, or tester local date as the authority. | high that source is missing date authority |
| Date input format for persistence TC | not found for display format in section 4.3. | Generic date rules exist in source type definitions, but section 4.3 does not define display format for this field. | medium |

## Terminology evidence

| UI/business term | source-backed term | artifact usage | decision |
|---|---|---|---|
| Relation field for contact person | `Отношение к заявителю` | Persistence artifact previously used `Отношение к клиенту` in `TC-AF43-PS-006`; v4 uses `Отношение к заявителю`. | Use `Отношение к заявителю` in persistence artifacts. `Отношение к клиенту` is not source-backed for section 4.3. |
| Relation dictionary | `Значения из справочника «Отношение к заявителю»` | Value `сестра/брат` is used in persistence smoke setup/data. | Keep value, normalize field label to `Отношение к заявителю`. |
