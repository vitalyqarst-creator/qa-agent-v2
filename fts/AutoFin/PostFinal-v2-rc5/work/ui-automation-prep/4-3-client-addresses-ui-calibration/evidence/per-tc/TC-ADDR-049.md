# TC-ADDR-049

Status: mismatch-ft-ui

Checked: actual `Квартира` format.

UI actions: entered `12`, `12A`, `1 2`, `1-2`, `1.2` into actual `Квартира`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur, `ДАЛЕЕ`.

Observed UI reaction:

- `12`: valid, no message.
- `12A`: invalid, exact message `Введено некорректное значение`.
- `1 2`: invalid, exact message `Введено некорректное значение`.
- `1-2`: valid, no message.
- `1.2`: invalid, exact message `Введено некорректное значение`.

Mismatch: baseline expectation `numeric only` is not accurate because hyphenated value `1-2` is accepted.

Required correction: update expected result to allow hyphen and reject letters/spaces/dot.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-hyphen-after-blur.png`
