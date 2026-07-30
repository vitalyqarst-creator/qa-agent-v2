# TC-ADDR-013

Status: confirmed

Checked: registration `Почтовый индекс` accepts only a complete 6-digit masked value.

UI actions:

1. Enabled manual mode for `Адрес регистрации`.
2. Entered postal values `443017`, `44301`, `4430179`, `44301A`, `443 17`, `443-17`.
3. Moved focus out of the field.
4. Clicked `ДАЛЕЕ` to confirm field state.

Trigger: input, blur, `ДАЛЕЕ`.

Observed UI reaction:

- `443017`: displayed `443017`, valid, no message.
- `44301`: displayed `44301_` during input, cleared to empty after blur, no message.
- `4430179`: displayed `443017`; extra digit is ignored/truncated, no message.
- `44301A`: displayed `44301_` during input, cleared to empty after blur, no message.
- `443 17` and `443-17`: separator is filtered, displayed incomplete mask `44317_`, cleared to empty after blur, no message.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-443017-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-44301-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-4430179-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-44301A-after-blur.png`
