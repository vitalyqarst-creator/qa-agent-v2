# TC-ADDR-023

Status: mismatch-ft-ui

Checked: registration `Квартира` format.

UI actions: entered `12`, `12A`, `1 2`, `1-2`, `1.2` into `Квартира`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur, `ДАЛЕЕ`.

Observed UI reaction:

- `12`: valid, no message.
- `12A`: invalid, exact message `Введено некорректное значение`.
- `1 2`: invalid, exact message `Введено некорректное значение`.
- `1-2`: valid, no message.
- `1.2`: invalid, exact message `Введено некорректное значение`.

Mismatch: baseline expectation `numeric only` is not accurate because hyphenated value `1-2` is accepted.

Required correction: update steps/expected result to digits plus hyphen allowed; letters, spaces and dots invalid.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-hyphen-after-blur.png`
