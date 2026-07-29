# UI calibration evidence

## Metadata

- `tc_id`: TC-PASSCUR-041
- `source_test_case_file`: `test-cases/4-3-current-passport-data.md`
- `scope`: Current passport / short subdivision code
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

- `Код подразделения`: `12345`.

## Calibration question

- What exact UI reaction confirms that a short value is not accepted as valid?

## Executed steps

1. Filled `Код подразделения` with `12345`.
2. Blurred the field and inspected DOM state.

## Observed UI reaction

- exact message: `Код подразделения не в формате 000-000`.
- field/control state: value cleared to empty after blur.
- visual marker: container `field_container label-align-top text-align-left invalid empty required`.
- filtering/blocking/save effect: short value is not retained; UI displays a format-specific message.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/passport-short-values-cleared-after-blur.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `needs-test-case-update`

## Recommended test-case update

- Expected result should say `12345` clears on blur and exact message `Код подразделения не в формате 000-000` is displayed.

## Notes / risks

- This field differs from `Серия`/`Номер`, which showed `Обязательно к заполнению`.

