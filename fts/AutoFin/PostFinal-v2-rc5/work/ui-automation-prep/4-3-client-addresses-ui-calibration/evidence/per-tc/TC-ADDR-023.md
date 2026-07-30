# TC-ADDR-023

Status: mismatch-ft-ui

Checked: registration `Квартира` format.

UI actions: entered `12`, `12A`, `12Д`, `1 2`, `1-2`, `1.2` into `Квартира`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur, `ДАЛЕЕ`.

Observed UI reaction:

- `12`: valid, no message.
- `12A`: invalid, exact message `Введено некорректное значение`.
- `12Д`: valid, no message.
- `1 2`: invalid, exact message `Введено некорректное значение`.
- `1-2`: valid, no message.
- `1.2`: invalid, exact message `Введено некорректное значение`.

Mismatch: baseline expectation `numeric only` is not accurate because hyphenated value `1-2` and checked Cyrillic value `12Д` are accepted.

Required correction: update steps/expected result to reflect the actual distinction: `12A`, spaces and dots are invalid, but `1-2` and `12Д` are valid. Do not state a blanket `letters invalid` rule unless the product rule is clarified.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-12-cyrillic-d-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-hyphen-after-blur.png`
