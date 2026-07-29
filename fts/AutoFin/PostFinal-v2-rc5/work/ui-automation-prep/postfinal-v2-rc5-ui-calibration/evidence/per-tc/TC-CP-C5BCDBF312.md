# UI calibration evidence

## Metadata

- `tc_id`: TC-CP-C5BCDBF312
- `source_test_case_file`: `test-cases/4-3-contact-persons.md`
- `scope`: Contact persons / patronymic input
- `tester`: Codex FT Test Case Agent, UI calibration
- `date`: 2026-07-28
- `stand_url`: http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create
- `browser`: Playwright CLI / Chromium
- `user_role`: `<redacted>`
- `user_account`: `<redacted>`

## Preconditions actually used

1. Login to FormRunner and launch `cff`.
2. Open `Создать заявку`.
3. Click `Добавить контактное лицо`.

## Test data actually used

- `Иван-Петров1`
- `Иван-Петров@`

## Calibration question

- What UI reaction is displayed when a digit or disallowed special character is entered in `Отчество`?

## Executed steps

1. Filled `Отчество` with `Иван-Петров1`, then blurred.
2. Filled `Отчество` with `Иван-Петров@`, checked before blur and after blur.

## Observed UI reaction

- exact message: none visible.
- field/control state: invalid value is present before blur; after blur value clears to empty.
- visual marker: after blur, container was `field_container label-align-top text-align-left empty`.
- filtering/blocking/save effect: invalid value is not retained.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-text-digit-after-blur.png`
- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-text-special-after-blur.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `confirmed-after-test-case-update`

## Recommended test-case update

- Applied in `test-cases/4-3-contact-persons.md`: invalid non-selected input can be typed before blur, clears on blur, and no visible error message is expected; empty `Отчество` remains optional.

## Notes / risks

- `Отчество` is optional; invalid non-empty input still clears on blur.
- Product decision after evidence review: DaData/autocomplete behavior for contact person FIO fields is treated as a requirement/clarification.
