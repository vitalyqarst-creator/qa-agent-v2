# UI validation report: 12-4.3-participants

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`

Date: 2026-07-30

Scope: `12-4.3-participants`, block `Участники`.

Baseline file was used read-only: `fts/AutoFin/PostFinal-v2-rc5/test-cases/12-4.3-participants.md`.

## Summary

Checked: 27 test cases.

Confirmed UI-ready: 20

`TC-PART-001`, `TC-PART-003`, `TC-PART-005`, `TC-PART-007`, `TC-PART-010`, `TC-PART-011`, `TC-PART-012`, `TC-PART-014`, `TC-PART-015`, `TC-PART-016`, `TC-PART-017`, `TC-PART-018`, `TC-PART-019`, `TC-PART-020`, `TC-PART-021`, `TC-PART-022`, `TC-PART-023`, `TC-PART-024`, `TC-PART-025`, `TC-PART-026`.

Needs test-case update / observed UI difference: 5

`TC-PART-002`, `TC-PART-004`, `TC-PART-006`, `TC-PART-008`, `TC-PART-013`.

Blocked by missing observable UI oracle: 1

`TC-PART-009`.

Blocked by ABS/save observability: 1

`TC-PART-027`.

## Key Findings

The `Участники` block is visible on a fresh card. Buttons `Добавить созаемщика` and `Добавить залогодателя` are visible. `EDIT` and `DELETE` are visible but disabled while no participant row is selected. The table headers are visible: `Тип участия`, `ФИО`, `Паспорт`, `ID клиента`.

Clicking `Добавить созаемщика` does not navigate to a new route and does not open a separate modal window. The UI adds an embedded same-page section titled `Добавление созаемщика`. Inside this section, the calculator summary widget is absent.

Role replacement for `созаемщик` is incomplete. The section has role-specific labels such as `Добавление созаемщика`, `Созаемщик менял паспорт`, `Адреса созаемщика`, `Контакты созаемщика`, `Доход созаемщика`, `Анкета созаемщика`, `Паспорт созаемщика`, `Визуальная оценка созаемщика`; however it still contains `Клиент менял ФИО`, `ID Клиента`, `ИНН клиента`, and document instruction text `Распечатайте, подпишите с клиентом и загрузите скан в заявку`.

Clicking `Добавить залогодателя` also adds an embedded same-page section titled `Добавление залогодателя`, without navigation and without separate modal window. The excluded elements from `TC-PART-007` were not present inside the pledgor section: calculator summary, employment/income block, contact persons, code word, SNILS, INN verification, marital status, dependents, social status, income confirmation.

Role replacement for `залогодатель` is incomplete. The section has role-specific labels such as `Добавление залогодателя`, `Залогодатель менял паспорт`, `Адреса залогодателя`, `Контакты залогодателя`, `Анкета залогодателя`, `Паспорт залогодателя`, `Визуальная оценка залогодателя`; however it still contains `Клиент менял ФИО`, `ID Клиента`, and document instruction text `Распечатайте, подпишите с клиентом и загрузите скан в заявку`.

Initial automated setup could not reliably create a participant row because the embedded form required additional select/document fields. A later user-prepared create-card session contained one manually created participant row, which closed the row-dependent checks.

Observed row values in the user-prepared session:

- `Тип участия`: `Созаемщик`
- `ФИО`: `Иванов Иван Петрович`
- `Паспорт`: `4234 543534`
- `ID клиента`: empty

Before selecting the row, `EDIT` and `DELETE` were visible but disabled. After selecting the row, both controls became enabled.

Clicking `EDIT` did not navigate to a new route and did not open a separate modal/window. The same route `#/application/card/create` remained, and a same-page participant edit form appeared with buttons `ОТМЕНИТЬ` and `ПОДТВЕРДИТЬ`. This requires a test-case wording update for `TC-PART-013`.

Clicking `DELETE` on the selected row opened a confirmation dialog with exact text `Вы уверены, что хотите удалить участника?` and buttons `ДА`, `ОТМЕНА`. `ОТМЕНА` closed the dialog and left the row in the table. Repeating delete and pressing `ДА` removed the row from the table.

## Per-TC Results

| TC-ID | Result | Trigger | Actual UI behavior | Evidence |
|---|---|---|---|---|
| TC-PART-001 | confirmed-ui-ready | visual inspection | Button `Добавить созаемщика` is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-002 | needs-test-case-update | click `Добавить созаемщика` | Same route remains; an embedded same-page section `Добавление созаемщика` appears. No separate modal/window was observed. | `evidence/screenshots/TC-PART-002-003-004-coborrower-section-focused.png` |
| TC-PART-003 | confirmed-ui-ready | inspect embedded co-borrower section | Calculator summary fields/widgets were absent inside `Добавление созаемщика`. | `evidence/screenshots/TC-PART-002-003-004-coborrower-section-focused.png` |
| TC-PART-004 | mismatch-ft-ui | inspect embedded co-borrower section | Role replacement is partial. Several role-specific `созаемщик` labels are present, but `Клиент менял ФИО`, `ID Клиента`, `ИНН клиента`, and `...с клиентом...` remain. | `evidence/screenshots/TC-PART-002-003-004-coborrower-section-focused.png` |
| TC-PART-005 | confirmed-ui-ready | visual inspection | Button `Добавить залогодателя` is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-006 | needs-test-case-update | click `Добавить залогодателя` | Same route remains; an embedded same-page section `Добавление залогодателя` appears. No separate modal/window was observed. | `evidence/screenshots/TC-PART-006-007-008-pledgor-section-focused.png` |
| TC-PART-007 | confirmed-ui-ready | inspect embedded pledgor section | Excluded elements were not present in `Добавление залогодателя`: calculator summary, employment/income, contact persons, code word, SNILS, INN verification, marital status, dependents, social status, income confirmation. | `evidence/screenshots/TC-PART-006-007-008-pledgor-section-focused.png` |
| TC-PART-008 | mismatch-ft-ui | inspect embedded pledgor section | Role replacement is partial. Several `залогодатель` labels are present, but `Клиент менял ФИО`, `ID Клиента`, and `...с клиентом...` remain. | `evidence/screenshots/TC-PART-006-007-008-pledgor-section-focused.png` |
| TC-PART-009 | blocked-needs-observable-ui-place | fresh card / card 1702 / create card with separate co-borrower row | No specific UI place showing “borrower is pledgor by default” was identified in the `Участники` block or elsewhere in the visible card UI when no separate pledgor is added. | `evidence/screenshots/TC-PART-009-012-016-021-023-025-card-1702-initial-participants.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-010 | confirmed-ui-ready | visual inspection | `EDIT` control is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-011 | confirmed-ui-ready | no selected row | `EDIT` has disabled state when no participant row is selected. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-012 | confirmed-ui-ready | select manually created participant row | After selecting row `Созаемщик Иванов Иван Петрович 4234 543534`, `EDIT` became enabled. | `evidence/screenshots/TC-PART-012-016-row-selected-edit-delete-enabled.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-013 | needs-test-case-update | click `EDIT` on selected row | Same route `#/application/card/create` remained; no separate `Заявка` window/route was observed. A same-page participant edit form appeared with buttons `ОТМЕНИТЬ` and `ПОДТВЕРДИТЬ`. | `evidence/screenshots/TC-PART-013-edit-selected-participant-opened.png`, `evidence/screenshots/TC-PART-013-edit-participant-form-actions.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-014 | confirmed-ui-ready | visual inspection | `DELETE`/trash control is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-015 | confirmed-ui-ready | no selected row | `DELETE` has disabled state when no participant row is selected. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-016 | confirmed-ui-ready | select manually created participant row | After selecting row `Созаемщик Иванов Иван Петрович 4234 543534`, `DELETE` became enabled. | `evidence/screenshots/TC-PART-012-016-row-selected-edit-delete-enabled.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-017 | confirmed-ui-ready | click `DELETE` on selected row | Confirmation dialog appeared with exact text `Вы уверены, что хотите удалить участника?` and buttons `ДА`, `ОТМЕНА`. | `evidence/screenshots/TC-PART-017-delete-confirmation-popup.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-018 | confirmed-ui-ready | click `ОТМЕНА` in delete confirmation | Dialog closed; row `Созаемщик Иванов Иван Петрович 4234 543534` remained in the table. | `evidence/screenshots/TC-PART-018-delete-cancel-row-remains.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-019 | confirmed-ui-ready | click `ДА` in delete confirmation | Dialog closed; participant row was removed from the table. | `evidence/screenshots/TC-PART-019-delete-confirm-row-removed.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-020 | confirmed-ui-ready | visual inspection | Column `Тип участия` is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-021 | confirmed-ui-ready | inspect manually created participant row | Row field `Тип участия` displayed `Созаемщик`. | `evidence/screenshots/TC-PART-012-016-021-023-025-user-created-row-visible.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-022 | confirmed-ui-ready | visual inspection | Column `ФИО` is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-023 | confirmed-ui-ready | inspect manually created participant row | Row field `ФИО` displayed `Иванов Иван Петрович`. | `evidence/screenshots/TC-PART-012-016-021-023-025-user-created-row-visible.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-024 | confirmed-ui-ready | visual inspection | Column `Паспорт` is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-025 | confirmed-ui-ready | inspect manually created participant row | Row field `Паспорт` displayed `4234 543534`. | `evidence/screenshots/TC-PART-012-016-021-023-025-user-created-row-visible.png`, `evidence/per-tc/card-1702-recheck-TC-PART-009-012-013-016-017-018-019-021-023-025.md` |
| TC-PART-026 | confirmed-ui-ready | visual inspection | Column `ID клиента` is visible. | `evidence/screenshots/TC-PART-001-005-010-011-014-015-020-022-024-026-initial-participants.png` |
| TC-PART-027 | blocked-observability | save/ABS path required | ABS ID after save requires a safely saved application and expected ABS response/oracle. The user-created row pass did not provide a safe save path or expected ABS value source. | `evidence/screenshots/TC-PART-setup-pledgor-confirm-after-minimal-fill.png` |

## Required Corrections / Follow-Up For Test Cases

1. `TC-PART-002` and `TC-PART-006`: update wording from “opens window” to observed same-page embedded section unless source explicitly treats that embedded section as the window. The route stayed `#/application/card/create`.
2. `TC-PART-004`: clarify whether labels `Клиент менял ФИО`, `ID Клиента`, `ИНН клиента`, and document instruction `...с клиентом...` must also be role-replaced. Observed UI does not replace them for co-borrower.
3. `TC-PART-008`: clarify the same role-replacement scope for pledgor. Observed UI does not replace `Клиент менял ФИО`, `ID Клиента`, and `...с клиентом...`.
4. `TC-PART-009`: add a concrete UI place/oracle where default borrower-as-pledgor must be observed. It is not visible in the `Участники` table on a fresh card or on card `1702`.
5. `TC-PART-013`: update wording from “opens window `Заявка`” to same-page participant edit form, unless source explicitly treats the embedded form as the window. The route stayed `#/application/card/create`.
6. `TC-PART-012`, `TC-PART-016`, `TC-PART-017`, `TC-PART-018`, `TC-PART-019`, `TC-PART-021`, `TC-PART-023`, `TC-PART-025`: UI behavior is confirmed when a participant row already exists. For automation, add a reproducible participant-row fixture/setup; manual creation by the user was used in this pass.
7. `TC-PART-027`: keep blocked until there is a safe save path and ABS expected-value oracle.
