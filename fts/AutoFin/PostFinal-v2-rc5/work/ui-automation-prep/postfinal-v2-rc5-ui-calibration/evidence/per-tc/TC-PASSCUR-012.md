# UI calibration evidence

## Metadata

- `tc_id`: TC-PASSCUR-012
- `source_test_case_file`: `test-cases/4-3-current-passport-data.md`
- `scope`: Current passport / short number
- `tester`: Codex FT Test Case Agent, UI calibration
- `date`: 2026-07-28
- `stand_url`: http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create
- `browser`: Playwright CLI / Chromium
- `user_role`: `<redacted>`
- `user_account`: `<redacted>`

## Preconditions actually used

1. Login to FormRunner and launch `cff`.
2. Open `Создать заявку`.
3. Use `Паспортные данные`.

## Test data actually used

- `Номер`: `12345`.

## Calibration question

- What exact UI reaction confirms that a short value is not accepted as valid?

## Executed steps

1. Filled `Номер` with `12345`.
2. Blurred the field and inspected DOM state.

## Observed UI reaction

- exact message: `Обязательно к заполнению`.
- field/control state: value cleared to empty after blur.
- visual marker: container `field_container label-align-top text-align-left invalid empty required`.
- filtering/blocking/save effect: short value is not retained; UI treats the field as empty required.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/passport-short-values-cleared-after-blur.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `needs-test-case-update`

## Recommended test-case update

- Expected result should say `12345` clears on blur and the field shows `Обязательно к заполнению`; no length-specific visible message was observed.

## Notes / risks

- The short value was not preserved for save-level validation.

