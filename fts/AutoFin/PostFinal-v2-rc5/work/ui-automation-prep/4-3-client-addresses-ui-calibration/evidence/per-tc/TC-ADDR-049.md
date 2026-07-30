# TC-ADDR-049

Status: mismatch-ft-ui

Checked: actual `Квартира` format.

UI actions: entered `12`, `12A`, `12Д`, `1 2`, `1-2`, `1.2` into actual `Квартира`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur, `ДАЛЕЕ`.

Observed UI reaction:

- `12`: valid, no message.
- `12A`: invalid, exact message `Введено некорректное значение`.
- `12Д`: valid, no message.
- `1 2`: invalid, exact message `Введено некорректное значение`.
- `1-2`: valid, no message.
- `1.2`: invalid, exact message `Введено некорректное значение`.

Mismatch: baseline expectation `numeric only` is not accurate because hyphenated value `1-2` and checked Cyrillic value `12Д` are accepted.

Required correction: update expected result to distinguish Latin and Cyrillic input: `12A`, spaces and dot are invalid, but `1-2` and `12Д` are valid in the actual address `Квартира` field.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-12-cyrillic-d-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-hyphen-after-blur.png`
