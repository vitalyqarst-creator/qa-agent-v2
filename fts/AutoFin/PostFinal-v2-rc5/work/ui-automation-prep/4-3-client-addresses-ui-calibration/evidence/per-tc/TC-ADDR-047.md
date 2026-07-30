# TC-ADDR-047

Status: confirmed

Checked: actual `Квартира` requiredness depends on `Клиент проживает в частном доме`.

UI actions:

1. Enabled manual mode for actual address.
2. Left `Дом` and `Квартира` empty while `Клиент проживает в частном доме` was unchecked.
3. Clicked `ДАЛЕЕ`.
4. Checked `Клиент проживает в частном доме`.
5. Clicked `ДАЛЕЕ` again.

Trigger: checkbox, `ДАЛЕЕ`.

Observed UI reaction:

- Checkbox unchecked: `Квартира` is required/invalid, exact message `Обязательно к заполнению`.
- Checkbox checked: `Квартира` becomes optional/valid empty with no message.
- `Дом` remains required/invalid with `Обязательно к заполнению`.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-private-house-no-flat-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-private-house-yes-after-toggle.png`
