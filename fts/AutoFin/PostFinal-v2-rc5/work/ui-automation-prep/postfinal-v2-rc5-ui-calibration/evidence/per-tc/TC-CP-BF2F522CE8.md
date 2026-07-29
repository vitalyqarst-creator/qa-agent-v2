# UI calibration evidence

## Metadata

- `tc_id`: TC-CP-BF2F522CE8
- `source_test_case_file`: `test-cases/4-3-contact-persons.md`
- `scope`: Contact persons / first name input
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

- What UI reaction is displayed when a digit or disallowed special character is entered in `Имя`?

## Executed steps

1. Filled `Имя` with `Иван-Петров1`, then blurred.
2. Filled `Имя` with `Иван-Петров@`, checked before blur and after blur.

## Observed UI reaction

- exact message: none visible.
- field/control state: invalid value is present before blur; after blur value clears to empty.
- visual marker: after blur, container was `field_container label-align-top text-align-left required empty`.
- filtering/blocking/save effect: invalid value is not retained.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-text-digit-after-blur.png`
- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-text-special-after-blur.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `needs-test-case-update`

## Recommended test-case update

- Expected behavior should say invalid input can be typed before blur but is cleared on blur; no visible error message appears.

## Notes / risks

- Field is an autocomplete/select-style input.

