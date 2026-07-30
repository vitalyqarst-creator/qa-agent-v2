# UI validation report: 10-4.3-additional-client-info

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`

Date: 2026-07-30

Scope: `10-4.3-additional-client-info`, block `Дополнительная информация`.

Baseline file was used read-only: `fts/AutoFin/PostFinal-v2-rc5/test-cases/10-4.3-additional-client-info.md`.

## Summary

Checked: 33 test cases.

Confirmed UI-ready: 23

`TC-ADDINFO-001`, `TC-ADDINFO-002`, `TC-ADDINFO-003`, `TC-ADDINFO-004`, `TC-ADDINFO-005`, `TC-ADDINFO-006`, `TC-ADDINFO-007`, `TC-ADDINFO-009`, `TC-ADDINFO-014`, `TC-ADDINFO-015`, `TC-ADDINFO-016`, `TC-ADDINFO-021`, `TC-ADDINFO-022`, `TC-ADDINFO-023`, `TC-ADDINFO-025`, `TC-ADDINFO-026`, `TC-ADDINFO-027`, `TC-ADDINFO-028`, `TC-ADDINFO-029`, `TC-ADDINFO-030`, `TC-ADDINFO-031`, `TC-ADDINFO-032`, `TC-ADDINFO-033`.

Needs test-case correction: 1

`TC-ADDINFO-028` was corrected in baseline to check prefilled value `0` instead of empty requiredness.

Source-retained / do not correct now: 3

`TC-ADDINFO-010`, `TC-ADDINFO-011`, `TC-ADDINFO-024`.

Blocked by integration / not implemented functionality: 7

`TC-ADDINFO-008`, `TC-ADDINFO-012`, `TC-ADDINFO-013`, `TC-ADDINFO-017`, `TC-ADDINFO-018`, `TC-ADDINFO-019`, `TC-ADDINFO-020`.

## Key Findings

`ИНН клиента` is visible as an enabled text input, has required marker `*`, and is invalid/empty on a fresh application. Inline text: `Обязательно к заполнению`.

The `ВЕРИФИЦИРОВАТЬ ИНН` button is visible on a fresh card even when `ИНН клиента` and the personal/passport prerequisites are empty. Clicking it with empty INN shows snackbar/message `ИНН не заполнен`.

Manual recheck of `ИНН клиента` by per-key input confirmed that a 12-digit INN can persist after blur. Value tested: `123456789123`; after blur the field value remained `123456789123` and field state was `valid`. Earlier `locator.fill`/bulk type results were an automation artifact of the masked field and should not be used as product evidence for `TC-ADDINFO-004`.

`ИНН проверен` is displayed as a readonly checkbox. It remained unchecked after click and after an empty-INN verification attempt.

`Кодовое слово` is visible, editable, not required, and accepted `secretWord123`.

The UI label for the marriage field is `Семейное положение`. The observed dropdown values were `Холост / не замужем`, `Женат / замужем`, `Разведен/Разведена`, `Вдовец/Вдова`. Per user decision, baseline expectation for `TC-ADDINFO-024` is retained as FT-first and not corrected in this pass.

`Семейное положение` has required marker on a fresh card. After `ДАЛЕЕ`, the field becomes invalid when empty; no separate inline message was visible inside this field, while the common message `Обязательные поля не заполнены` was shown.

`Количество иждивенцев` is visible with default value `0`, numeric input, and spinner arrows. Leaving it empty returns it to `0`; entering `2A` returns it to `0` after blur without inline error. Spinner buttons were checked: `0 -> 1 -> 2`, then `2 -> 1 -> 0`; an extra decrement at `0` kept the value at `0`.

## Per-TC Results

| TC-ID | Result | Trigger | Actual UI behavior | Evidence |
|---|---|---|---|---|
| TC-ADDINFO-001 | confirmed-ui-ready | visual/DOM inspection | `ИНН клиента` is a visible enabled text input. | `evidence/screenshots/TC-ADDINFO-001-003-014-016-021-023-024-026-027-029-visible-controls.png` |
| TC-ADDINFO-002 | confirmed-ui-ready | fresh card, `ДАЛЕЕ`, empty-INN verify button | Required marker is present. Empty field is invalid with inline text `Обязательно к заполнению`; verify button with empty INN shows `ИНН не заполнен`. | `evidence/screenshots/TC-ADDINFO-002-025-028-fresh-required-markers.png`, `evidence/screenshots/TC-ADDINFO-010-012-013-verify-button-empty-inn.png` |
| TC-ADDINFO-003 | confirmed-ui-ready | visual inspection | `ИНН клиента` is always visible in the block. | `evidence/screenshots/TC-ADDINFO-001-003-014-016-021-023-024-026-027-029-visible-controls.png` |
| TC-ADDINFO-004 | confirmed-ui-ready | manual per-key input + blur | `123456789123` persisted after blur and field state was `valid`. Earlier bulk fill/type attempts were treated as automation artifacts of the masked field. | `evidence/screenshots/TC-ADDINFO-004-recheck-keypress-12-digit-inn-after-blur.png` |
| TC-ADDINFO-005 | confirmed-ui-ready | input + blur | Short value `12345678901` did not persist after blur; field became empty required/invalid. | `evidence/screenshots/TC-ADDINFO-004-007-inn-values-after-blur.png` |
| TC-ADDINFO-006 | confirmed-ui-ready | input + blur | Long value `1234567890123` did not persist after blur; field became empty required/invalid. | `evidence/screenshots/TC-ADDINFO-004-007-inn-values-after-blur.png` |
| TC-ADDINFO-007 | confirmed-ui-ready | input + blur | Alphanumeric value `12345678901A` did not persist after blur; field became empty required/invalid. | `evidence/screenshots/TC-ADDINFO-004-007-inn-values-after-blur.png` |
| TC-ADDINFO-008 | blocked-observability | attempted prerequisites + blur | Automatic INN request/result requires a controlled integration fixture/oracle. Attempted manual prerequisite filling did not produce observable INN autofill. | `evidence/screenshots/TC-ADDINFO-008-011-prerequisites-filled-attempt.png` |
| TC-ADDINFO-009 | confirmed-ui-ready | manual per-key input + blur | Manual INN input is available. `123456789123` persisted after blur and field state was `valid`. | `evidence/screenshots/TC-ADDINFO-004-recheck-keypress-12-digit-inn-after-blur.png` |
| TC-ADDINFO-010 | source-retained | fresh-card visual inspection | Baseline test is kept as FT-first per user instruction. Observed UI note: `ВЕРИФИЦИРОВАТЬ ИНН` was visible on the tested fresh card. | `evidence/screenshots/TC-ADDINFO-002-025-028-fresh-required-markers.png` |
| TC-ADDINFO-011 | source-retained | fresh-card visual inspection + prerequisite attempt | Baseline test is kept as FT-first per user instruction. Manual INN acceptance was rechecked separately in `TC-ADDINFO-004`. | `evidence/screenshots/TC-ADDINFO-004-recheck-keypress-12-digit-inn-after-blur.png` |
| TC-ADDINFO-012 | blocked-not-implemented | button click | INN verification functionality is not implemented on the stand yet; only empty-INN guard message `ИНН не заполнен` was observable. | `evidence/screenshots/TC-ADDINFO-010-012-013-verify-button-empty-inn.png` |
| TC-ADDINFO-013 | blocked-not-implemented | button click | Failed INN verification path cannot be checked because INN verification functionality is not implemented on the stand yet. | `evidence/screenshots/TC-ADDINFO-010-012-013-verify-button-empty-inn.png` |
| TC-ADDINFO-014 | confirmed-ui-ready | visual/DOM inspection + click attempt | `ИНН проверен` is a checkbox with readonly input. Click did not change unchecked state. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-015 | confirmed-ui-ready | visual/DOM inspection | Checkbox has no required marker and is not a manually required field. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-016 | confirmed-ui-ready | visual inspection | `ИНН проверен` is always visible in the block. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-017 | blocked-not-implemented | not fully executable | Automatic checkbox fill depends on INN request/verification functionality, which is not implemented on the stand yet. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-018 | blocked-not-implemented | not fully executable | `ИНН проверен = Да` after successful verification cannot be checked because INN verification is not implemented on the stand yet. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-019 | blocked-not-implemented | not fully executable | Unavailable-verification behavior cannot be checked because INN verification is not implemented on the stand yet. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-020 | blocked-not-implemented | not fully executable | Locking personal/passport fields after `ИНН проверен = Да` cannot be checked because the verified state is not reachable on the stand yet. | `evidence/screenshots/TC-ADDINFO-014-016-inn-checked-readonly.png` |
| TC-ADDINFO-021 | confirmed-ui-ready | input + blur | `Кодовое слово` is editable text input; `secretWord123` persisted. | `evidence/screenshots/TC-ADDINFO-021-031-codeword-dependents-input-behavior.png` |
| TC-ADDINFO-022 | confirmed-ui-ready | visual/DOM inspection | `Кодовое слово` has no required marker and no invalid state when empty. | `evidence/screenshots/TC-ADDINFO-001-003-014-016-021-023-024-026-027-029-visible-controls.png` |
| TC-ADDINFO-023 | confirmed-ui-ready | visual inspection | `Кодовое слово` is always visible in the block. | `evidence/screenshots/TC-ADDINFO-001-003-014-016-021-023-024-026-027-029-visible-controls.png` |
| TC-ADDINFO-024 | source-retained | dropdown open/select | Observed UI values: `Холост / не замужем`, `Женат / замужем`, `Разведен/Разведена`, `Вдовец/Вдова`. Baseline is kept as FT-first per user instruction. | `evidence/screenshots/TC-ADDINFO-024-marital-dropdown-open.png`, `evidence/screenshots/TC-ADDINFO-024-marital-actual-option-selected.png` |
| TC-ADDINFO-025 | confirmed-ui-ready | fresh card + `ДАЛЕЕ` | Required marker exists; after `ДАЛЕЕ`, empty field becomes invalid. Common message: `Обязательные поля не заполнены`. | `evidence/screenshots/TC-ADDINFO-002-025-028-fresh-next-validation.png` |
| TC-ADDINFO-026 | confirmed-ui-ready | visual inspection | `Семейное положение` is always visible in the block. | `evidence/screenshots/TC-ADDINFO-001-003-014-016-021-023-024-026-027-029-visible-controls.png` |
| TC-ADDINFO-027 | confirmed-ui-ready | visual/input inspection | `Количество иждивенцев` is editable numeric text input with spinner arrows and default `0`. | `evidence/screenshots/TC-ADDINFO-027-031-dependents-values-after-blur.png` |
| TC-ADDINFO-028 | confirmed-ui-ready | fresh card visual inspection | Field is prefilled with `0`; baseline corrected to check the default value instead of empty requiredness. | `evidence/screenshots/TC-ADDINFO-002-025-028-fresh-required-markers.png` |
| TC-ADDINFO-029 | confirmed-ui-ready | visual inspection | `Количество иждивенцев` is always visible in the block. | `evidence/screenshots/TC-ADDINFO-001-003-014-016-021-023-024-026-027-029-visible-controls.png` |
| TC-ADDINFO-030 | confirmed-ui-ready | input + blur | Numeric value `2` persisted and field stayed valid. | `evidence/screenshots/TC-ADDINFO-027-031-dependents-values-after-blur.png` |
| TC-ADDINFO-031 | confirmed-ui-ready | input + blur | Nonnumeric value `2A` did not persist; field returned to `0` without inline error. | `evidence/screenshots/TC-ADDINFO-027-031-dependents-values-after-blur.png` |
| TC-ADDINFO-032 | confirmed-ui-ready | spinner up/down buttons | Spinner increment/decrement confirmed: `0 -> 1 -> 2 -> 1`. | `evidence/screenshots/TC-ADDINFO-032-033-dependents-spinner-exact-centers-min-zero.png` |
| TC-ADDINFO-033 | confirmed-ui-ready | spinner down button at `0` | Lower boundary confirmed: decrement at `0` keeps value `0`; negative value is not set. | `evidence/screenshots/TC-ADDINFO-032-033-dependents-spinner-exact-centers-min-zero.png` |

## Required Corrections For Baseline / Automation-Ready Test Cases

1. `TC-ADDINFO-028`: corrected to check that `Количество иждивенцев` is prefilled with `0`.
2. Added `TC-ADDINFO-032`: increment/decrement by spinner buttons.
3. Added `TC-ADDINFO-033`: lower boundary, value must not go below `0`.
4. `TC-ADDINFO-010`, `TC-ADDINFO-011`, and `TC-ADDINFO-024`: kept unchanged as FT-first per user instruction.
5. `TC-ADDINFO-009`: corrected to a manual INN filling check; confirmed by per-key input and blur.
6. `TC-ADDINFO-012`, `TC-ADDINFO-013`, `TC-ADDINFO-017`, `TC-ADDINFO-018`, `TC-ADDINFO-019`, `TC-ADDINFO-020`: keep blocked because INN verification/related checkbox and lock behavior is not implemented on the stand yet.
