# TC-ADDR-059

Status: confirmed

Checked: registration `Квартира` required when `Клиент зарегистрирован в частном доме` is unchecked.

UI actions: enabled registration manual mode, left private-house checkbox unchecked, left `Квартира` empty, clicked `ДАЛЕЕ`.

Trigger: checkbox state, `ДАЛЕЕ`.

Observed UI reaction:

- Private-house checkbox unchecked.
- `Квартира` has required marker.
- Empty `Квартира` becomes invalid.
- Exact message: `Обязательно к заполнению`.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-private-house-no-flat-after-next.png`
