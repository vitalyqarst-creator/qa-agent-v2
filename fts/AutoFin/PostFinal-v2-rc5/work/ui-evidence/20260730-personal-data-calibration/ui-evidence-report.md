# UI evidence report: 20260730 personal data calibration

## Metadata

- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `scope`: `4.3-personal-data`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `date`: 2026-07-30
- `current_date_for_date_cases`: 2026-07-30
- `candidate_cases_checked`: 10
- `local_note`: requested iteration file `work/iterations/20260729-4-3-personal-data-model-runtime-prose-r20/iteration/shadow-test-cases.md` was not present in this checkout; TC list was taken from the attached request.

Only the test stand UI was used. No source DOCX/XHTML/PDF/support/mockups, baseline/canonical test-cases, credentials, cookies, auth/session/storage files were edited or staged.

## Summary

| Result | TC IDs |
| --- | --- |
| `confirmed` | `TC-PERSON-006`, `TC-PERSON-022`, `TC-PERSON-026`, `TC-PERSON-037`, `TC-PERSON-017`, `TC-PERSON-012`, `TC-PERSON-029`, `TC-PERSON-033` |
| `mismatch-ft-ui` | `TC-PERSON-030` |
| `blocked-not-implemented` | `TC-PERSON-009` |

General FIO-format observation:

- Trigger sequence: direct input, then blur, then `ДАЛЕЕ`.
- During input, all invalid FIO values were accepted temporarily as typed, field state became `invalid`, exact field-level message: `Введено некорректное значение`.
- After blur, the invalid value was cleared.
- For `Фамилия`, `Имя`, `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество`, the invalid message disappeared after blur; fields stayed empty.
- For current `Отчество`, the invalid message persisted after blur and after `ДАЛЕЕ`, while value was empty.
- `ДАЛЕЕ` also triggers unrelated required fields in the card, so full-form blocking should not be used as isolated oracle for these FIO-format checks.

## Evidence table

| TC ID | BSR | Поле | Значение | Trigger | Фактический UI-отклик | Screenshot refs | Итог | Рекомендация для TC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TC-PERSON-006` | 51 | `Имя` | `Иванов Петров` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов Петров`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. After `ДАЛЕЕ`: remains empty, no field message. | `evidence/screenshots/TC-PERSON-006-Имя-Иванов-Петров-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Replace calibration question with exact expected result: field temporarily shows typed value, marks invalid with `Введено некорректное значение`, then clears on blur; do not assert persistent message after blur. |
| `TC-PERSON-006` | 51 | `Имя` | `Иванов1` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов1`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. | `evidence/screenshots/TC-PERSON-006-Имя-Иванов1-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for digit input. |
| `TC-PERSON-006` | 51 | `Имя` | `Иванов@` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов@`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. | `evidence/screenshots/TC-PERSON-006-Имя-Ивановat-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for `@` input. |
| `TC-PERSON-022` | 48 | `Фамилия` | `Иванов Петров` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов Петров`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. | `evidence/screenshots/TC-PERSON-022-Фамилия-Иванов-Петров-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Expected result: invalid message during input, value clears on blur; no persistent field message after blur. |
| `TC-PERSON-022` | 48 | `Фамилия` | `Иванов1` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов1`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. | `evidence/screenshots/TC-PERSON-022-Фамилия-Иванов1-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for digit input. |
| `TC-PERSON-022` | 48 | `Фамилия` | `Иванов@` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов@`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. | `evidence/screenshots/TC-PERSON-022-Фамилия-Ивановat-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for `@` input. |
| `TC-PERSON-026` | 54 | `Отчество` | `Иванов Петров` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов Петров`, state `invalid`, message `Введено некорректное значение`. After blur and after `ДАЛЕЕ`: value cleared to empty, state remains `invalid`, message remains `Введено некорректное значение`. | `evidence/screenshots/TC-PERSON-026-Отчество-Иванов-Петров-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Expected result should mention persistent invalid message for current `Отчество` after blur. |
| `TC-PERSON-026` | 54 | `Отчество` | `Иванов1` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов1`, invalid, message `Введено некорректное значение`. After blur/`ДАЛЕЕ`: value empty, invalid message persists. | `evidence/screenshots/TC-PERSON-026-Отчество-Иванов1-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for digit input. |
| `TC-PERSON-026` | 54 | `Отчество` | `Иванов@` | input -> blur -> `ДАЛЕЕ` | After input: value `Иванов@`, invalid, message `Введено некорректное значение`. After blur/`ДАЛЕЕ`: value empty, invalid message persists. | `evidence/screenshots/TC-PERSON-026-Отчество-Ивановat-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for `@` input. |
| `TC-PERSON-037` | 67 | `Предыдущая фамилия` | `Петрова Сидорова` | `Клиент менял ФИО` = yes, input -> blur -> `ДАЛЕЕ` | After input: value `Петрова Сидорова`, state `invalid`, message `Введено некорректное значение`. After blur: value cleared to empty, message absent. | `evidence/screenshots/TC-PERSON-037-Предыдущая фамилия-Петрова-Сидорова-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Expected result: invalid message during input, clear-on-blur, no persistent message after blur. |
| `TC-PERSON-037` | 67 | `Предыдущая фамилия` | `Петрова1` | same | After input: value `Петрова1`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-037-Предыдущая фамилия-Петрова1-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for digit input. |
| `TC-PERSON-037` | 67 | `Предыдущая фамилия` | `Петрова@` | same | After input: value `Петрова@`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-037-Предыдущая фамилия-Петроваat-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for `@` input. |
| `TC-PERSON-017` | 71 | `Предыдущее имя` | `Петрова Сидорова` | `Клиент менял ФИО` = yes, input -> blur -> `ДАЛЕЕ` | After input: value `Петрова Сидорова`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-017-Предыдущее имя-Петрова-Сидорова-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Expected result: invalid message during input, clear-on-blur, no persistent message after blur. |
| `TC-PERSON-017` | 71 | `Предыдущее имя` | `Петрова1` | same | After input: value `Петрова1`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-017-Предыдущее имя-Петрова1-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for digit input. |
| `TC-PERSON-017` | 71 | `Предыдущее имя` | `Петрова@` | same | After input: value `Петрова@`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-017-Предыдущее имя-Петроваat-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for `@` input. |
| `TC-PERSON-012` | 75 | `Предыдущее отчество` | `Петрова Сидорова` | `Клиент менял ФИО` = yes, input -> blur -> `ДАЛЕЕ` | After input: value `Петрова Сидорова`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-012-Предыдущее отчество-Петрова-Сидорова-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Expected result: invalid message during input, clear-on-blur, no persistent message after blur. |
| `TC-PERSON-012` | 75 | `Предыдущее отчество` | `Петрова1` | same | After input: value `Петрова1`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-012-Предыдущее отчество-Петрова1-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for digit input. |
| `TC-PERSON-012` | 75 | `Предыдущее отчество` | `Петрова@` | same | After input: value `Петрова@`, invalid, message `Введено некорректное значение`. After blur: empty, no message. | `evidence/screenshots/TC-PERSON-012-Предыдущее отчество-Петроваat-before.png`; `...-after-input.png`; `...-after-blur.png`; `...-after-next.png` | `confirmed` | Same expected result as above for `@` input. |
| `TC-PERSON-029` | 61 | `Дата рождения` | `31.07.2008` | fill -> blur -> `ДАЛЕЕ` | Value remains `31.07.2008`. After input/blur/`ДАЛЕЕ`: field state `invalid`; no inline message text captured. | `evidence/screenshots/TC-PERSON-029-birth-under-18-31-07-2008-retry-before.png`; `...-retry-after-input.png`; `...-retry-after-blur.png`; `...-retry-after-next.png` | `confirmed` | Expected result: value stays, field becomes invalid, no exact inline message observed. Do not invent message text. |
| `TC-PERSON-030` | 63 | `Дата рождения` | `29.07.1926` | fill -> blur -> `ДАЛЕЕ` | Value remains `29.07.1926`. After blur and after `ДАЛЕЕ`: field state `valid`; no inline message. | `evidence/screenshots/TC-PERSON-030-birth-over-100-29-07-1926-retry-before.png`; `...-retry-after-input.png`; `...-retry-after-blur.png`; `...-retry-after-next.png` | `mismatch-ft-ui` | Do not assert this value is rejected as older than 100. TC needs correction or additional boundary calibration; observed UI accepts `29.07.1926` on 2026-07-30. |
| `TC-PERSON-033` | 62 | `Дата рождения` | `31.07.2026` | fill -> blur -> `ДАЛЕЕ` | Value remains `31.07.2026`. After input/blur/`ДАЛЕЕ`: field state `required invalid`; no inline message. This also violates age lower bound, so cause is not isolated. | `evidence/screenshots/TC-PERSON-033-birth-future-31-07-2026-retry-before.png`; `...-retry-after-input.png`; `...-retry-after-blur.png`; `...-retry-after-next.png` | `confirmed` | Expected result: value stays, field invalid, no exact message captured; do not claim isolated future-date reason. |
| `TC-PERSON-009` | 57 | `ID Клиента` | before save | clean card observation only | Field `ID Клиента` is visible, value empty, `readOnly=true`, `disabled=false`, container includes `empty readonly`. Visible action: `ДАЛЕЕ`; no visible `СОХРАНИТЬ`. No safe ABS save path or ABS oracle available. | `evidence/screenshots/TC-PERSON-009-id-client-observability.png` | `blocked-not-implemented` | Leave candidate-ui-calibration until ABS/test save integration is configured. Do not invent expected ID, format, or ABS response. |

## Notes for TC updates

- FIO-format cases can be updated with exact UI oracle above. The strongest trigger is input itself: invalid message appears immediately while the typed value is still visible. Blur clears invalid values.
- For current `Отчество`, keep the difference: invalid message persists after blur, unlike other checked FIO fields.
- For `Дата рождения` age checks, use field invalid/valid state rather than nonexistent inline message text.
- `TC-PERSON-030` needs correction: the tested value `29.07.1926` is accepted by the UI on 2026-07-30.
- `TC-PERSON-009` should remain calibration-pending/blocked until ABS is implemented and a safe expected-source oracle exists.
