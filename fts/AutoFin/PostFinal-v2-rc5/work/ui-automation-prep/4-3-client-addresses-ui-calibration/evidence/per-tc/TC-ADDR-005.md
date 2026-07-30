# TC-ADDR-005

Status: confirmed

Checked: registration address manual mode requires `Регион` and `Дом`.

UI actions:

1. Created a clean application card.
2. In `Адреса клиента`, clicked `Ввести вручную` for `Адрес регистрации`.
3. Left registration address fields empty.
4. Clicked `ДАЛЕЕ`.

Trigger: `ДАЛЕЕ`.

Observed UI reaction:

- `Регион`: required marker visible, invalid state, exact message `Выберите значение`.
- `Дом`: required marker visible, invalid state, exact message `Обязательно к заполнению`.
- Transition is blocked by validation; toast `Обязательные поля не заполнены` is shown.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-manual-enabled.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-required-empty-after-next.png`
