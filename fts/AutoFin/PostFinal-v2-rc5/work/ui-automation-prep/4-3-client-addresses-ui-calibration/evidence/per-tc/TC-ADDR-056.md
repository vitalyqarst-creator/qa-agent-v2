# TC-ADDR-056

Status: confirmed

Checked: registration `Населенный пункт` is required when `Город` is empty.

UI actions:

1. Enabled manual mode for registration address.
2. Left both `Населенный пункт` and `Город` empty.
3. Clicked `ДАЛЕЕ`.
4. Rechecked with `Город = Самара`, `Населенный пункт` empty.

Trigger: `ДАЛЕЕ`.

Observed UI reaction:

- When both fields are empty: `Населенный пункт` is required/invalid, exact message `Обязательно к заполнению`.
- When `Город` is filled with `Самара`: `Населенный пункт` is empty but valid/optional, no message.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-required-empty-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-city-only-after-next.png`
