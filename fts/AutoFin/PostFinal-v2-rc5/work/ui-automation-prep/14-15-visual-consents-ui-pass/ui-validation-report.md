# UI validation report: 14-4.3-visual-assessment-info and 15-4.3-consents-and-checks

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`

Date: 2026-07-30

Baseline files were used read-only:

- `fts/AutoFin/PostFinal-v2-rc5/test-cases/14-4.3-visual-assessment-info.md`
- `fts/AutoFin/PostFinal-v2-rc5/test-cases/15-4.3-consents-and-checks.md`

## Summary

Checked: 28 test cases.

Confirmed UI-ready: 23

`TC-VISUAL-001`, `TC-VISUAL-002`, `TC-VISUAL-003`, `TC-VISUAL-004`, `TC-VISUAL-007`, `TC-VISUAL-011`, `TC-VISUAL-012`, `TC-VISUAL-013`, `TC-VISUAL-014`, `TC-VISUAL-015`, `TC-VISUAL-016`, `TC-CONSENT-001`, `TC-CONSENT-002`, `TC-CONSENT-003`, `TC-CONSENT-004`, `TC-CONSENT-005`, `TC-CONSENT-006`, `TC-CONSENT-007`, `TC-CONSENT-008`, `TC-CONSENT-009`, `TC-CONSENT-010`, `TC-CONSENT-011`, `TC-CONSENT-012`.

Needs test-case update / dynamic UI wording: 3

`TC-VISUAL-005`, `TC-VISUAL-009`, `TC-VISUAL-010`.

Blocked / not reliably observable: 2

`TC-VISUAL-006`, `TC-VISUAL-008`.

## Visual Assessment Findings

`Визуальная информация` is displayed as a switch-like checkbox. Default state on the current create card was unchecked, which corresponds to `Нет`; the UI does not show a literal `Нет` text next to the field.

After enabling the switch, the visual assessment list appears immediately under the field. There is no separate visible heading `Параметры визуальной оценки`; the UI directly shows numbered categories.

The list supports multiple selection. In category `4. Признаки «преображенного» бомжа`, two different checkbox values stayed selected simultaneously.

Selecting `Другое (комментарий обязателен)` in a category creates a text input `Комментарий` immediately below that category. The created input has a required marker. This was confirmed by automated evidence for category 4 and by manual UI evidence for categories 1 and 2. The required/invalid trigger for that dynamic comment was not reliably isolated: `Ctrl+Enter` did not produce an additional visible invalid state/message for this field in the current session, and the `ДАЛЕЕ` button was partially clipped at the bottom of the internal scroll container.

When `Визуальная информация` was enabled and no visual parameter was selected, clicking `ДАЛЕЕ` produced the general message `Обязательные поля не заполнены`. The visible invalid field in the visual block was `Комментарий` under `8. Прочие признаки (комментарий обязателен)`. No separate observable message like “select at least one visual assessment parameter” was found in this pass.

Category composition observed in UI:

- `1. Признаки алкоголика`: 4 base checkbox values plus `Другое (комментарий обязателен)`. After selecting `Другое`, UI displays required text field `Комментарий *` below category 1.
- `2. Признаки наркомана`: 7 base checkbox values plus `Другое (комментарий обязателен)`. After selecting `Другое`, UI displays required text field `Комментарий *` below category 2.
- `3. Признаки бывшего заключенного`: 2 base checkbox values plus `Другое (комментарий обязателен)`.
- `4. Признаки «преображенного» бомжа`: 4 base checkbox values plus `Другое (комментарий обязателен)`.
- `5. Поведенческие признаки потенциального неплательщика`: 4 base checkbox values plus `Другое (комментарий обязателен)`.
- `6. Сопровождение Клиента`: 5 base checkbox values plus `Другое (комментарий обязателен)`.
- `7. Признаки подделки документов`: 5 base checkbox values plus `Другое (комментарий обязателен)`.
- `8. Прочие признаки (комментарий обязателен)`: text field `Комментарий`; no separate `Другое` checkbox.

## Consents And Checks Findings

`Согласия/Проверки` is collapsed by default. The block is opened by clicking the right side/header area of the `Согласия/Проверки` panel. After opening, the same panel expands in place.

Observed structure:

- `Согласия`
- `БКИ и персональные данные. Согласие на передачу данных в БКИ, на получение данных из БКИ, на обработку персональных данных, на запрос в ПФР, налоговую`
- `FATCA/CRS проверка`
- `FATCA/CRS проверка`
- `AML проверка`
- `Иностранное публичное должностное лицо`
- `Должностное лицо публичной международной организации`
- `Должностное лицо Российской Федерации, включенное в перечни должностей, определяемые Президентом Российской Федерации, а также назначаемое/ освобождаемое от должности Президентом или Правительством Российской Федерации (РПДЛ)`
- `Родственник ИПДЛ`
- `Родственник МПДЛ`
- `Родственник РПДЛ`

Default values:

- `БКИ и персональные данные`: checked / `Да`.
- `FATCA/CRS проверка`: unchecked / `Нет`.
- All 6 AML fields: unchecked / `Нет`.

Editability:

- `БКИ и персональные данные` can be toggled to unchecked / `Нет`.
- `FATCA/CRS проверка` can be toggled to checked / `Да`.
- All 6 AML fields can be toggled to checked / `Да`.
- Values were restored after the editability check: BKI checked, FATCA unchecked, all AML unchecked.

No separate FATCA/CRS/AML check result area was observed in this scope; only the source checkboxes/default values were visible.

## Per-TC Results

| TC-ID | Result | Actual UI behavior | Evidence |
|---|---|---|---|
| TC-VISUAL-001 | confirmed-ui-ready | `Визуальная информация` block/field is visible. | `evidence/screenshots/visual-01-initial-block.png` |
| TC-VISUAL-002 | confirmed-ui-ready | Default switch state is unchecked, interpreted as `Нет`; no literal `Нет` label is displayed. | `evidence/screenshots/visual-01-initial-block.png` |
| TC-VISUAL-003 | confirmed-ui-ready | Clicking the switch sets it checked and shows the numbered visual assessment categories. | `evidence/screenshots/visual-02-after-enable-yes.png`, `evidence/screenshots/visual-03-categories-top.png` |
| TC-VISUAL-004 | confirmed-ui-ready | Two visual assessment checkbox values stayed selected simultaneously. | `evidence/screenshots/visual-07-multiple-values-selected.png` |
| TC-VISUAL-005 | needs-test-case-update | UI uses checkboxes for assessment values and text inputs for `Комментарий`; `Комментарий` should not be expected as a checkbox. | `evidence/screenshots/visual-03-categories-top.png`, `evidence/screenshots/visual-08-other-selected.png` |
| TC-VISUAL-006 | blocked-observability | With visual assessment enabled and no selected parameter, `ДАЛЕЕ` showed general `Обязательные поля не заполнены`; no isolated select-one message/state was found. | `evidence/screenshots/visual-05-after-next-no-params-validation.png` |
| TC-VISUAL-007 | confirmed-ui-ready | Selecting `Другое (комментарий обязателен)` displays a required `Комментарий` input below that category. Confirmed for category 4 by automation and for categories 1/2 by manual UI evidence. | `evidence/screenshots/visual-08-other-selected.png`, `evidence/screenshots/manual-visual-other-categories-1-2-comments.png` |
| TC-VISUAL-008 | blocked-observability | Required marker for the dynamic `Комментарий` input is visible, but invalid/message trigger was not reliably isolated in this pass. Manual evidence confirms required markers for categories 1/2. | `evidence/screenshots/visual-09-other-empty-before-next.png`, `evidence/screenshots/visual-12-other-empty-after-ctrl-enter.png`, `evidence/screenshots/manual-visual-other-categories-1-2-comments.png` |
| TC-VISUAL-009 | needs-test-case-update | Category `Признаки алкоголика` shows expected checkbox values and `Другое`; `Комментарий *` appears dynamically after selecting `Другое`. | `evidence/screenshots/visual-03-categories-top.png`, `evidence/screenshots/manual-visual-other-categories-1-2-comments.png` |
| TC-VISUAL-010 | needs-test-case-update | Category `Признаки наркомана` shows expected checkbox values and `Другое`; `Комментарий *` appears dynamically after selecting `Другое`. | `evidence/screenshots/visual-03-categories-top.png`, `evidence/screenshots/manual-visual-other-categories-1-2-comments.png` |
| TC-VISUAL-011 | confirmed-ui-ready | Category `Признаки бывшего заключенного` contains the expected values. | `evidence/screenshots/visual-03-categories-top.png` |
| TC-VISUAL-012 | confirmed-ui-ready | Category `Признаки «преображенного» бомжа` contains the expected values. | `evidence/screenshots/visual-06-mid-before-multiple-select.png` |
| TC-VISUAL-013 | confirmed-ui-ready | Category `Поведенческие признаки потенциального неплательщика` contains the expected values. | `evidence/screenshots/visual-06-mid-before-multiple-select.png` |
| TC-VISUAL-014 | confirmed-ui-ready | Category `Сопровождение Клиента` contains the expected values. | `evidence/screenshots/visual-10-other-empty-after-next-validation.png` |
| TC-VISUAL-015 | confirmed-ui-ready | Category `Признаки подделки документов` contains the expected values. | `evidence/screenshots/visual-10-other-empty-after-next-validation.png` |
| TC-VISUAL-016 | confirmed-ui-ready | Category `Прочие признаки (комментарий обязателен)` contains only required text field `Комментарий`; no separate `Другое` checkbox. | `evidence/screenshots/visual-10-other-empty-after-next-validation.png` |
| TC-CONSENT-001 | confirmed-ui-ready | `Согласия/Проверки` is collapsed before manual opening. | `evidence/screenshots/consent-02-header-visible.png` |
| TC-CONSENT-002 | confirmed-ui-ready | Clicking the panel header/right side expands the block in place. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-003 | confirmed-ui-ready | All Appendix 2 subblocks and fields are present in the expanded block. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-004 | confirmed-ui-ready | Field `БКИ и персональные данные` is present with full description text. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-005 | confirmed-ui-ready | `БКИ и персональные данные` default is checked / `Да`. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-006 | confirmed-ui-ready | BKI field can be toggled to unchecked / `Нет`, then restored. | `evidence/screenshots/consent-04-edited-values.png`, `evidence/screenshots/consent-06-values-restored.png` |
| TC-CONSENT-007 | confirmed-ui-ready | `FATCA/CRS проверка` field is present. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-008 | confirmed-ui-ready | `FATCA/CRS проверка` default is unchecked / `Нет`. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-009 | confirmed-ui-ready | FATCA/CRS field can be toggled to checked / `Да`, then restored. | `evidence/screenshots/consent-04-edited-values.png`, `evidence/screenshots/consent-06-values-restored.png` |
| TC-CONSENT-010 | confirmed-ui-ready | All 6 expected AML fields are present. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-011 | confirmed-ui-ready | All 6 AML fields default to unchecked / `Нет`. | `evidence/screenshots/consent-03-opened.png` |
| TC-CONSENT-012 | confirmed-ui-ready | All 6 AML fields can be toggled to checked / `Да`, then restored. | `evidence/screenshots/consent-05-all-aml-edited-values.png`, `evidence/screenshots/consent-06-values-restored.png` |

## Test-Case Corrections Needed

1. `TC-VISUAL-005`: clarify that checkbox applies to visual assessment options, while `Комментарий` is a text input, not a checkbox.
2. `TC-VISUAL-006`: add an automation-ready trigger/oracle for “at least one parameter must be selected”. Current UI evidence shows only general `Обязательные поля не заполнены` and `Комментарий` invalid; no isolated select-one UI message was found.
3. `TC-VISUAL-008`: keep as UI-observability gap until the exact validation trigger/message for empty dynamic `Комментарий` after `Другое` is confirmed.
4. `TC-VISUAL-009` and `TC-VISUAL-010`: update expected composition to say `Комментарий` appears dynamically after selecting `Другое`, not as a static list item before selection.
5. `TC-CONSENT-002`: automation steps should open the block by clicking the `Согласия/Проверки` panel header/right-side expand control; the block expands in place.
