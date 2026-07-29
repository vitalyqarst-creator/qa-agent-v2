# GAP-CONTACT-PHONE-TYPE-OPTIONALNESS-UI-001

## Scenario

Added phone row exists. `Номер телефона` is filled, `Тип телефона` is left empty.

## Observed UI facts

- `Тип телефона` shows a required marker and DOM `required=true`.
- After blur/validation, `Тип телефона` state is `empty required invalid`.
- Exact message: `Выберите значение`.
- `Номер телефона` value remains `+7 (999) 123–45–67`, state `valid`.
- After clicking `ДАЛЕЕ`, URL stayed on `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`.

## Status

`confirmed`

## Evidence

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-phone-type-empty-number-filled-before-next.png`
