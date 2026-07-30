# TC-ADDR-051

Status: confirmed

Checked: actual `Почтовый индекс` rejects nonnumeric input by mask/filtering.

UI actions: entered `44301A`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur.

Observed UI reaction:

- During input displayed value is `44301_`; letter `A` is not accepted into the mask.
- After blur, incomplete value is cleared to empty.
- Field state: empty, not invalid, no message.

Required correction: expected result should mention clearing on blur and no inline error message.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-44301A-after-blur.png`
