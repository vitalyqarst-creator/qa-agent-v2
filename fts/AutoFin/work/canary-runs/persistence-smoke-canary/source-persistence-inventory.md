# Source Persistence Inventory

## Source Selection

| item | value |
| --- | --- |
| ft_slug | `AutoFin` |
| main_ft_docx | `fts/AutoFin/source/FT4AutoFinFinal.docx` |
| main_ft_xhtml | `fts/AutoFin/source/FT4AutoFinFinal.xhtml` |
| pdf_cross_check | `fts/AutoFin/source/FT4AutoFinFinal.pdf` |
| package_notes | `fts/AutoFin/AGENT-NOTES.md` |
| v4_field_level_canary_role | style/reference fixture only; not source of truth |
| decision_source_basis | FT source rows and BSR references from `FT4AutoFinFinal.xhtml` / DOCX source of truth |

## Persistence Source Findings

| source artifact | source location | BSR/source row | confirms | save action | reopen path | persistence data candidates | unresolved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FT4AutoFinFinal.xhtml` | Section 4.2, Table 3, action "Перейти в выбранную заявку" | `BSR 35` | The system opens the selected application card within role permissions. | Not specified. | Source-backed path to reopen the same card from the applications table. | Any saved application-card field visible in section 4.3 after reopen. | Exact search/select prerequisites for returning to the same card are outside section 4.3 and require BA/UI confirmation for execution. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 row 33 | `BSR 115`-`BSR 120` | Registration address field, DaData integration, no-result hint, decomposition/manual composition. | Not specified. | Use `BSR 35`. | Selected DaData registration address; manual address components. | Exact save action is not described in this row. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 rows 34-44 | `BSR 121`-`BSR 137` | Manual registration address branch and component fields. | Not specified. | Use `BSR 35`. | Postal index, region, city, street, house, apartment/private-house branch. | Exact save action is not described in these rows. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 rows 45-57 | `BSR 138`-`BSR 161` | Residence address same-as-registration branch, DaData/manual branch and postal index. | Not specified. | Use `BSR 35`. | Fact address differing from registration address. | Exact save action is not described in these rows. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 rows 59-60 | `BSR 162`-`BSR 166` | Client mobile phone and e-mail fields with format restrictions. | Not specified. | Use `BSR 35`. | Mobile phone and one e-mail address. | Exact save action is not described in these rows. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 rows 61-64 | `BSR 167`-`BSR 172` | Home/work phone add, display, format and delete behavior. | Not specified. | Use `BSR 35`. | Added work phone; deletion of added phone is a candidate out-of-scope smoke. | Exact save action and deletion persistence are not described in these rows. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 rows 66-72 | `BSR 173`-`BSR 185` | Contact-person FIO, relation, phone and birth date fields after adding a contact person. | Not specified. | Use `BSR 35`. | Added contact person with FIO, relation, phone and birth date. | Exact save action is not described in these rows. |
| `FT4AutoFinFinal.xhtml` | Section 4.3, Table 7 rows 72-73 | `BSR 186`-`BSR 189` | Add and delete contact-person row. | Not specified. | Use `BSR 35`. | Deleted contact person remains absent after reopen. | Exact save action and restore/cleanup strategy require BA/UI confirmation. |

## UI Block Naming

| section 4.3 source-backed term | artifact term | non-selected appendix/legacy term | decision |
| --- | --- | --- | --- |
| `Блок «Контакты клиента»` | `Контакты клиента` | `Контактная информация` | Use the section 4.3 term in persistence smoke TC. The appendix term is not used as the primary block label for this scope. |
| `Блок «Контактные лица» (блок-повторитель)` | `Контактные лица` | `Контактное лицо` | Use the section 4.3 repeated-block term in persistence smoke TC. Singular wording may describe an entity, not the UI block name. |

## Decision

Exact save action for the application card is not source-backed in the inspected section 4.3 rows or the adjacent source-backed reopen action. The persistence smoke TC therefore use confirmation-required save wording and are marked `candidate-persistence-calibration`.

Executable after confirmation:
- data entry and expected persisted values are source-backed by section 4.3 field rows;
- reopen path is source-backed by `BSR 35`;
- exact save action, exit-after-save path and cleanup mechanics require BA/UI confirmation.

## BA Questions / Blockers

| id | blocker | question | affected_tc |
| --- | --- | --- | --- |
| `BA-PS-001` | Exact save action is not source-backed. | What exact UI action saves changes in the application card for section 4.3? Is it manual save, autosave, transition save, or another mechanism? | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-002` | Exit-after-save path is not source-backed. | After saving, how should a tester leave the card before reopening it without discarding saved data? | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-003` | Cleanup mechanics are not source-backed. | Which values/entities can be safely reset, and should smoke tests use isolated applications instead of restoring shared data? | `TC-AF43-PS-001`..`TC-AF43-PS-007` |
| `BA-PS-004` | Application date source for rolling birth-date data is not source-backed. | Which date must be used as `D` for contact-person birth-date calculations: current UI business date, server date, or tester local date? | `TC-AF43-PS-006`; setup in `TC-AF43-PS-007` |
