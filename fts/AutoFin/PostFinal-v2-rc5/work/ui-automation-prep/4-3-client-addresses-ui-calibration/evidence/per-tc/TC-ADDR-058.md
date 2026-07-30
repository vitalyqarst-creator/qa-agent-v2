# TC-ADDR-058

Status: confirmed

Checked: registration `Дом` required.

UI actions: enabled registration manual mode, left `Дом` empty, clicked `ДАЛЕЕ`.

Trigger: `ДАЛЕЕ`.

Observed UI reaction:

- `Дом` has required marker.
- Empty `Дом` becomes invalid.
- Exact message: `Обязательно к заполнению`.
- Transition is blocked by validation.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-required-empty-after-next.png`
