# UI calibration evidence

## Metadata

- `tc_id`: TC-PASSCUR-025
- `source_test_case_file`: `test-cases/4-3-current-passport-data.md`
- `scope`: Current passport / 20-year replacement boundary
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

- Current date: `28.07.2026`.
- `Дата рождения`: `29.04.2006`.
- `Дата выдачи`: `29.04.2026`.

## Calibration question

- What UI reaction occurs for `дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 90 дней`?

## Executed steps

1. Entered DOB `29.04.2006`.
2. Entered issue date `29.04.2026`.
3. Blurred `Дата выдачи`.

## Observed UI reaction

- exact message: none visible.
- field/control state: issue date remained `29.04.2026`.
- visual marker: container `field_container label-align-top text-align-left valid`.
- filtering/blocking/save effect: no field-level blocking observed.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/passcur-025-issue-date-20-at-90.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `confirmed`

## Recommended test-case update

- Add exact UI: after blur, `Дата выдачи` remains populated, container is `valid`, and no visible message appears.

## Notes / risks

- Automation should calculate DOB dynamically from the actual run date.

