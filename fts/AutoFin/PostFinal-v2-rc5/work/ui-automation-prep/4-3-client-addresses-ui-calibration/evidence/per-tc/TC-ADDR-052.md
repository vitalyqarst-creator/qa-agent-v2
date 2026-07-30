# TC-ADDR-052

Status: confirmed

Checked: actual `Почтовый индекс` shorter than 6 numeric chars.

UI actions: entered `44301`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur.

Observed UI reaction:

- During input displayed value is `44301_`.
- After blur, incomplete masked value is cleared to empty.
- Field state: empty, not invalid, no message.

Required correction: expected result should mention blur-based clear and no inline error message.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-44301-after-blur.png`
