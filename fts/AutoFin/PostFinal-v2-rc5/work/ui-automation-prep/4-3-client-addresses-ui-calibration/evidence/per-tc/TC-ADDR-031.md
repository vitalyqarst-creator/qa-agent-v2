# TC-ADDR-031

Status: confirmed

Checked: actual address manual mode requires `Регион` and `Дом`.

UI actions:

1. Created a clean application card.
2. Turned off `Адрес фактического места жительства совпадает с адресом регистрации`.
3. Clicked the second `Ввести вручную` switch for `Адрес фактического места жительства`.
4. Left actual address fields empty.
5. Clicked `ДАЛЕЕ`.

Trigger: `ДАЛЕЕ`.

Observed UI reaction:

- `Регион`: required marker visible, invalid state, exact message `Выберите значение`.
- `Дом`: required marker visible, invalid state, exact message `Обязательно к заполнению`.
- Transition is blocked by validation; toast `Обязательные поля не заполнены` is shown.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-address-manual-enabled.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-required-empty-after-next.png`
