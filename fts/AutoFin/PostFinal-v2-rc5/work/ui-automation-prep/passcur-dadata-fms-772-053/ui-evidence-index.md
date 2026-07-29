# UI evidence index: DaData/FMS `772-053`

All paths are repo-relative.

## Evidence files

| test_case_id | artifact_type | path | note |
| --- | --- | --- | --- |
| `TC-PASSCUR-003` | report | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | confirmed; full trigger sequence and result for FMS fixture `772-053`. |
| `TC-PASSCUR-005` | report | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | confirmed; dropdown appears after focus on `??? ?????`. |
| `TC-PASSCUR-018` | report | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md` | confirmed; exact suggestion selected and retained after blur. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-before-input.png` | Before input: passport block, switch `?????? ??????? ?????????????` = `???`, empty `??? ?????????????`/`??? ?????`. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-input.png` | After entering `772-053`: code set, no auto-fill yet. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-blur.png` | After blur from `??? ?????????????`: no dropdown, `??? ?????` empty. |
| `TC-PASSCUR-003` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-code-enter.png` | After Enter: no dropdown, `??? ?????` empty. |
| `TC-PASSCUR-003;TC-PASSCUR-005;TC-PASSCUR-018` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-kem-focus.png` | After click/focus on `??? ?????`: dropdown includes `??? ?????? ?. ?????? 772-053`. |
| `TC-PASSCUR-003;TC-PASSCUR-018` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-suggestion-select.png` | After selecting `??? ?????? ?. ?????? 772-053`: `??? ?????` is populated. |
| `TC-PASSCUR-018` | screenshot | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/passcur-dadata-fms-772-053/evidence/screenshots/passcur-dadata-after-selection-blur.png` | After blur/transition: selected value remains. |

## Per-TC result summary

- `TC-PASSCUR-003`: `confirmed`; trigger is input `772-053`, focus `??? ?????`, select exact suggestion.
- `TC-PASSCUR-005`: `confirmed`; field `??? ?????` behaves as autocomplete/select when manual switch is `???`.
- `TC-PASSCUR-018`: `confirmed`; selected value remains after blur.

## Automation trigger contract

1. Set `?????? ??????? ?????????????` to `???`.
2. Fill `??? ?????????????` with `772-053`.
3. Click/focus `??? ?????`.
4. Wait for dropdown item containing `??? ?????? ?. ?????? 772-053`.
5. Click the exact item.
6. Assert field `??? ?????` equals `??? ?????? ?. ??????`.
7. Blur/transition and assert the value is still present.
