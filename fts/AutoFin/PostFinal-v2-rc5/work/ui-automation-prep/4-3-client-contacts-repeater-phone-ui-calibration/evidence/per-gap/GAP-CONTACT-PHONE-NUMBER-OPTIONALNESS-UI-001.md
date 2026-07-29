# GAP-CONTACT-PHONE-NUMBER-OPTIONALNESS-UI-001

## Scenario

Added phone row exists. `Тип телефона` is selected as `Мобильный`, `Номер телефона` is left empty.

## Observed UI facts

- `Номер телефона` shows a required marker and DOM `required=true`.
- After blur/validation, `Номер телефона` state is `invalid required empty`.
- Exact message: `Обязательно к заполнению`.
- `Тип телефона` remains `Мобильный`, state `valid`.
- Observed type dropdown options: `Мобильный`, `Рабочий`, `Домашний`.
- After clicking `ДАЛЕЕ`, URL stayed on `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`.

## Status

`confirmed`

## Evidence

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-phone-number-empty-type-selected-before-next.png`
