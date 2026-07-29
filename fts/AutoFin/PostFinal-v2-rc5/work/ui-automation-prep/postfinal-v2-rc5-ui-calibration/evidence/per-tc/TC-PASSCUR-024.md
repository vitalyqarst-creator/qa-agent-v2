# UI calibration evidence

## Metadata

- `tc_id`: TC-PASSCUR-024
- `source_test_case_file`: `test-cases/4-3-current-passport-data.md`
- `scope`: Current passport / issue date on 14th birthday
- `tester`: Codex FT Test Case Agent, UI calibration
- `date`: 2026-07-28
- `stand_url`: http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create
- `browser`: Playwright CLI / Chromium
- `user_role`: `<redacted>`
- `user_account`: `<redacted>`

## Preconditions actually used

1. Login to FormRunner and launch `cff`.
2. Open `Создать заявку`.
3. Use `Персональные данные` and `Паспортные данные`.

## Test data actually used

- `Дата рождения`: `28.07.2012`.
- `Дата выдачи`: `28.07.2026`.

## Calibration question

- What UI reaction occurs when `Дата выдачи` equals the 14th birthday?

## Executed steps

1. Entered DOB `28.07.2012`.
2. Entered issue date `28.07.2026`.
3. Blurred `Дата выдачи`.

## Observed UI reaction

- exact message: none visible.
- field/control state: issue date remained `28.07.2026`.
- visual marker: container `field_container label-align-top text-align-left`; no `invalid` class.
- filtering/blocking/save effect: no field-level blocking observed.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/passcur-024-issue-date-14th-birthday.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `confirmed`

## Recommended test-case update

- Add exact UI: after blur, value remains, no visible message appears, and no `invalid` class is present.

## Notes / risks

- Checked at field level, not full application submission.

