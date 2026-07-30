# TC-ADDR-021

Status: mismatch-ft-ui

Checked: registration `Корпус` format.

UI actions: entered `12`, `12A`, `12Д`, `1 2`, `1-2`, `1.2` into `Корпус`, blurred the field, then clicked `ДАЛЕЕ`.

Trigger: input, blur, `ДАЛЕЕ`.

Observed UI reaction:

- `12`: valid, no message.
- `12A`: invalid, exact message `Введено некорректное значение`.
- `12Д`: valid, no message.
- `1 2`: valid, no message.
- `1-2`: invalid, exact message `Введено некорректное значение`.
- `1.2`: invalid, exact message `Введено некорректное значение`.

Mismatch: baseline expectation `numeric only` is not accurate because `1 2` and `12Д` are accepted.

Required correction: update expected format to the observed UI rule, or remove `numeric only` wording until the product rule is confirmed. Do not generalize Latin and Cyrillic letters as one class: `12A` is invalid, while checked Cyrillic value `12Д` is valid.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-12-cyrillic-d-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-hyphen-after-blur.png`
