# UI evidence index: DaData/FMS `772-053`

## Scope

- Package: `fts/AutoFin/PostFinal-v2-rc5`.
- Checked TC-ID: `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018`.
- Fixture: `FX-DADATA-FMS-POS-001`.
- Query / code: `772-053`.
- Expected suggestion: `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`.
- Resulting field value: `ОВД ЗЮЗИНО Г. МОСКВЫ`.

## Canonical Evidence Artifact Table

| Test Case ID | Artifact Type | Path | Note |
| --- | --- | --- | --- |
| `TC-PASSCUR-003` | report | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | Confirmed with trigger: input `772-053`, focus `Кем выдан`, select exact suggestion. |
| `TC-PASSCUR-005` | report | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | Confirmed; `Кем выдан` behaves as autocomplete/select when manual switch is `Нет`. |
| `TC-PASSCUR-018` | report | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | Confirmed; selected value remains after blur/transition. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-before-input.png` | Before input: `Код подразделения` and `Кем выдан` empty. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-input.png` | After input `772-053`: no immediate autofill. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-blur.png` | After blur: `Кем выдан` still empty; message `Выберите значение`. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-enter.png` | After Enter: no dropdown/autofill observed. |
| `TC-PASSCUR-003;TC-PASSCUR-005;TC-PASSCUR-018` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-kem-focus.png` | After focus on `Кем выдан`: dropdown contains `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`. |
| `TC-PASSCUR-003;TC-PASSCUR-018` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-suggestion-select.png` | After selection: `Кем выдан = ОВД ЗЮЗИНО Г. МОСКВЫ`. |
| `TC-PASSCUR-018` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-selection-blur.png` | After blur/transition: selected value remains. |

## Automation contract

1. Set `Ввести вручную подразделение` to `Нет`.
2. Fill `Код подразделения` with `772-053`.
3. Click/focus `Кем выдан`.
4. Wait for dropdown item containing `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`.
5. Select the exact item.
6. Assert field `Кем выдан` equals `ОВД ЗЮЗИНО Г. МОСКВЫ`.
