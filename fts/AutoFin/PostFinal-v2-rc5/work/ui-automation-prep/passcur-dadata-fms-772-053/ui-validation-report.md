# UI calibration report: DaData/FMS `772-053`

## Metadata

- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `scope_slug`: `passcur-dadata-fms-772-053`
- `checked_tc`: `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `date`: 2026-07-29
- `browser`: Playwright Chromium session `ui-cal`
- `user_account`: `zhidkov`
- `ui_user_label`: `Виталий Жидков`
- `fixture`: `FX-DADATA-FMS-POS-001`
- `provider`: `DaData`
- `endpoint_fixture_source`: `suggest/fms_unit`
- `query`: `772-053`
- `expected_suggestion`: `ОВД ЗЮЗИНО Г. МОСКВЫ`
- `fixture_response_sha256`: `5575e4fbb9e28df33d8826a00580594eccde839bb6d625bfa84a6bf53d2bf90e`

## Scope and restrictions

Only AutoFin UI behavior was checked. No direct DaData/API calls were made. Manual/mobile/drag-and-drop cases were not checked. Baseline files in `fts/AutoFin/PostFinal-v2-rc5/test-cases/*.md` were not edited.

## Preconditions actually used

1. Logged in to FormRunner UI.
2. Launched `cff`.
3. Opened `Новая заявка (Заёмщик)`.
4. Navigated to block `Паспортные данные`.
5. Confirmed `Ввести вручную подразделение` is in `Нет` state: DOM row did not contain `checked`.
6. `Код подразделения` and `Кем выдан` were empty before input.

## Trigger sequence checked

1. Entered exact query `772-053` into `Код подразделения`.
2. Immediate state after input: `Код подразделения = 772-053`, `Кем выдан` remained empty, no visible suggestions.
3. Triggered `blur` from `Код подразделения` via `Tab`.
4. State after blur: `Код подразделения = 772-053`, `Кем выдан` remained empty, no visible suggestions, message under `Кем выдан`: `Выберите значение`.
5. Triggered `Enter` on/after `Код подразделения`.
6. State after Enter: `Кем выдан` remained empty, no visible suggestions.
7. Triggered `click/focus` on field `Кем выдан`.
8. A dropdown opened and contained exact fixture suggestion as first visible item: `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`.
9. Selected `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`.
10. Field `Кем выдан` became `ОВД ЗЮЗИНО Г. МОСКВЫ`.
11. Triggered `blur`/transition via `Tab`.
12. Field `Кем выдан` still contained `ОВД ЗЮЗИНО Г. МОСКВЫ`.

## Observed suggestions

Visible suggestions after `click/focus` on `Кем выдан`:

- `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`
- `ОВД ЗЮЗИНО Г. МОСКВЫ ПАСПОРТНЫЙ СТОЛ 1 772-053`
- `ОВД ЗЮЗИНО ПС УВД ЮЗАО Г. МОСКВЫ 772-053`
- `ОВД ЗЮЗИНО ПС № 1 УВД ЮЗАО Г. МОСКВЫ 772-053`
- `ОВД РАЙОНА ЗЮЗИНО УВД ЮГО-ЗАО Г. МОСКВЫ 772-053`
- `ПАСПОРТНО-ВИЗОВЫМ ОТДЕЛЕНИЕМ ОВД РАЙОНА ЗЮЗИНО Г. МОСКВЫ 772-053`
- `ПАСПОРТНО-ВИЗОВЫМ ОТДЕЛЕНИЕМ ОВД РАЙОНА СЕВЕРНЫЙ Г. МОСКВЫ 772-053`
- `ПВО ОВД РАЙОНА ЗЮЗИНО Г. МОСКВЫ 772-053`

Ordering/full count should not be used as an assertion. The automation-ready assertion should target the exact suggestion text and resulting field value.

## TC results

| TC-ID | status | observed trigger | observed result | automation-ready? | evidence files |
| --- | --- | --- | --- | --- | --- |
| `TC-PASSCUR-003` | `confirmed-ui-ready` | Input `772-053` into `Код подразделения`; then `click/focus` `Кем выдан`; then select suggestion | No auto-fill after input/blur/Enter. After focusing `Кем выдан`, dropdown contains `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`; after selection field value is `ОВД ЗЮЗИНО Г. МОСКВЫ`. | Yes, with explicit trigger `click/focus Кем выдан` before selection. | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-before-input.png`; `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-input.png`; `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-kem-focus.png`; `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-suggestion-select.png` |
| `TC-PASSCUR-005` | `confirmed-ui-ready` | Manual switch `Нет`; input `772-053`; `click/focus` on `Кем выдан` | `Кем выдан` works as selectable/autocomplete control. Dropdown appears only after focusing `Кем выдан`; exact suggestion `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053` is present. | Yes. | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-before-input.png`; `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-kem-focus.png` |
| `TC-PASSCUR-018` | `confirmed-ui-ready` | Input `772-053`; `click/focus` `Кем выдан`; select `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`; `blur` via `Tab` | Selection fills `Кем выдан` with `ОВД ЗЮЗИНО Г. МОСКВЫ`. After blur/transition the selected value remains. | Yes. | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-kem-focus.png`; `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-suggestion-select.png`; `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-selection-blur.png` |

## Automation-ready notes

1. Do not assert auto-fill of `Кем выдан` immediately after `Код подразделения = 772-053`.
2. Do not assert suggestions after `blur` or `Enter` on `Код подразделения`; neither produced the dropdown in this run.
3. Automation should:
   - set `Ввести вручную подразделение` to `Нет`;
   - fill `Код подразделения` with `772-053`;
   - click/focus `Кем выдан`;
   - wait for dropdown item containing `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`;
   - click the exact item;
   - assert field `Кем выдан` equals `ОВД ЗЮЗИНО Г. МОСКВЫ`;
   - blur/transition and assert the value is still present.

