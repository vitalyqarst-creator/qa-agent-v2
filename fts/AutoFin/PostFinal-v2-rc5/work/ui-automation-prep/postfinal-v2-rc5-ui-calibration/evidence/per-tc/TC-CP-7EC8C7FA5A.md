# UI calibration evidence

## Metadata

- `tc_id`: TC-CP-7EC8C7FA5A
- `source_test_case_file`: `test-cases/4-3-contact-persons.md`
- `scope`: Contact persons / future birth date
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

- Current calibration date: `28.07.2026`.
- D+1: `29.07.2026`.

## Calibration question

- What action triggers validation of future birth date, and what UI reaction is displayed?

## Executed steps

1. Filled contact `Дата рождения` with `29.07.2026`.
2. Blurred the field and inspected DOM state.

## Observed UI reaction

- exact message: none visible.
- field/control state: value remained `29.07.2026`; input `required=true`.
- visual marker: container became `field_container required label-align-top text-align-left invalid`.
- filtering/blocking/save effect: no value clearing; no isolated save/next blocking was proven because unrelated required fields exist.
- network/backend evidence, if checked: not checked.

## Evidence files

- screenshot: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-required-and-future-date.png`
- video/trace: none
- log/network: Playwright DOM eval output

## Result

- `needs-test-case-update`

## Recommended test-case update

- Specify `D+1` as a dynamic date; after blur the value stays visible and the container becomes `invalid`, with no visible exact message.

## Notes / risks

- Observed concrete D+1 for this run was `29.07.2026`.

