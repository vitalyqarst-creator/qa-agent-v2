# TC-ADDR-053

Status: mismatch-ft-ui

Checked: actual `Почтовый индекс` longer than 6 numeric chars.

UI actions: entered `4430179`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur.

Observed UI reaction:

- During input displayed value is `443017`.
- After blur displayed value remains `443017`.
- Field state: valid, no message.
- The 7th digit is ignored/truncated; UI does not show invalid state or rejection message.

Mismatch: if baseline expects longer-than-6 input to be rejected as invalid, that does not match UI behavior.

Required correction: expected result should say extra digits are ignored/truncated to the first 6 digits.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-4430179-after-blur.png`
