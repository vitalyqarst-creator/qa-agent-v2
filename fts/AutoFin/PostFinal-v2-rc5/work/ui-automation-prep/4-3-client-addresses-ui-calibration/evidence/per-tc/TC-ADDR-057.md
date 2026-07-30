# TC-ADDR-057

Status: confirmed

Checked: registration `Город` is required when `Населенный пункт` is empty.

UI actions:

1. Enabled manual mode for registration address.
2. Left both `Город` and `Населенный пункт` empty.
3. Clicked `ДАЛЕЕ`.
4. Rechecked with `Населенный пункт = Самара`, `Город` empty.

Trigger: `ДАЛЕЕ`.

Observed UI reaction:

- When both fields are empty: `Город` is required/invalid, exact message `Обязательно к заполнению`.
- When `Населенный пункт` is filled with `Самара`: `Город` is empty but valid/optional, no message.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-required-empty-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-locality-only-after-next.png`
