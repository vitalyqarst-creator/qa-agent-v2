# UI evidence index: DaData/FMS `772-053`

All paths are repo-relative.

## Evidence files

| File | Purpose |
| --- | --- |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | Final report for `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018`. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-before-input.png` | Before input: passport block, `Ввести вручную подразделение` = `Нет`, empty `Код подразделения`/`Кем выдан`. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-input.png` | After entering `772-053`: code set, no auto-fill yet. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-blur.png` | After `blur` from `Код подразделения`: no dropdown, `Кем выдан` empty. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-enter.png` | After `Enter`: no dropdown, `Кем выдан` empty. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-kem-focus.png` | After `click/focus` on `Кем выдан`: dropdown with FMS suggestions, including `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-suggestion-select.png` | After selecting `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`: `Кем выдан` is populated. |
| `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-selection-blur.png` | After blur/transition: selected value remains. |

## Per-TC traceability

| TC-ID | Что проверялось | Точные действия в UI | Trigger проверки | Фактическая реакция UI | Точный текст сообщения | Итог | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TC-PASSCUR-003` | Предзаполнение/выбор `Кем выдан` по коду подразделения `772-053` | Ввести `772-053` в `Код подразделения`; проверить immediate state, blur, Enter; затем сфокусировать `Кем выдан`; выбрать `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`; проверить значение | input / blur / Enter / click-focus / selection | Без выбора автозаполнения нет. После `click/focus` по `Кем выдан` список появляется. После выбора значение поля: `ОВД ЗЮЗИНО Г. МОСКВЫ`. | До выбора в поле `Кем выдан`: `Выберите значение`. | `confirmed-ui-ready` | `passcur-dadata-before-input.png`, `passcur-dadata-after-code-input.png`, `passcur-dadata-after-code-blur.png`, `passcur-dadata-after-code-enter.png`, `passcur-dadata-after-kem-focus.png`, `passcur-dadata-after-suggestion-select.png` |
| `TC-PASSCUR-005` | Отображение списка `Кем выдан` при manual switch = `Нет` | Проверить switch `Ввести вручную подразделение` без `checked`; ввести `772-053`; сфокусировать `Кем выдан` | click-focus on `Кем выдан` | Поле работает как autocomplete/select. Dropdown содержит `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`. | До фокуса/выбора: `Выберите значение`. | `confirmed-ui-ready` | `passcur-dadata-before-input.png`, `passcur-dadata-after-kem-focus.png` |
| `TC-PASSCUR-018` | Выбор значения `Кем выдан` из предложений DaData/FMS | Ввести `772-053`; сфокусировать `Кем выдан`; выбрать exact suggestion; выполнить blur/transition | click-focus / selection / blur | Выбор устанавливает `Кем выдан = ОВД ЗЮЗИНО Г. МОСКВЫ`; после blur значение сохраняется. | Нет error message после выбора. | `confirmed-ui-ready` | `passcur-dadata-after-kem-focus.png`, `passcur-dadata-after-suggestion-select.png`, `passcur-dadata-after-selection-blur.png` |

