# UI Pass Report: 4.3 Test Case Files

Date: 2026-07-30

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`

Input files:

- `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-contact-persons.md`
- `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-current-passport-data.md`
- `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-personal-data.md`

Evidence index:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-three-files-ui-pass/ui-evidence-index.md`

## General Prerequisites Observed

- Login with the provided user works.
- After login, the application launch screen is shown. The row `cff` must be selected before pressing `ЗАПУСТИТЬ`; otherwise the launch button does not open the application list.
- New application is created from the application list by `СОЗДАТЬ ЗАЯВКУ`.

## 4-3-current-passport-data.md

Total test cases in file: 44.

Confirmed or UI-ready:

- `TC-PASSCUR-001`, `TC-PASSCUR-002`, `TC-PASSCUR-004`, `TC-PASSCUR-006`, `TC-PASSCUR-007`, `TC-PASSCUR-008`, `TC-PASSCUR-009`, `TC-PASSCUR-013`, `TC-PASSCUR-014`, `TC-PASSCUR-015`, `TC-PASSCUR-016`, `TC-PASSCUR-017`, `TC-PASSCUR-019`, `TC-PASSCUR-020`, `TC-PASSCUR-021`, `TC-PASSCUR-022`, `TC-PASSCUR-023`, `TC-PASSCUR-024`, `TC-PASSCUR-025`, `TC-PASSCUR-026`, `TC-PASSCUR-027`, `TC-PASSCUR-028`, `TC-PASSCUR-029`, `TC-PASSCUR-030`, `TC-PASSCUR-034`, `TC-PASSCUR-035`, `TC-PASSCUR-036`, `TC-PASSCUR-037`, `TC-PASSCUR-039`, `TC-PASSCUR-042`, `TC-PASSCUR-043`, `TC-PASSCUR-044`.

Confirmed after additional UI clarification:

- `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018`.
- Actual trigger: enter a stable department code such as `772013` or `770001`, blur `Код подразделения`, then put focus into `Кем выдан` and wait about 3 seconds.
- Observed dropdown selector: `.ui-menu-item`.
- For `772013`, visible options included:
  - `ОВД ДМИТРОВСКИЙ УВД САО Г. МОСКВЫ 772-013`
  - `ОВД ДМИТРОВСКОГО РАЙОНА Г. МОСКВЫ 772-013`
  - `ПАСПОРТНО-ВИЗОВЫМ ОТДЕЛЕНИЕМ ОВД РАЙОНА ДМИТРОВСКИЙ Г. МОСКВЫ 772-013`
- After selecting the first option and blurring the field, displayed value became `ОВД ДМИТРОВСКИЙ УВД САО Г. МОСКВЫ`; field became not invalid.

Needs test-case correction:

- `TC-PASSCUR-011`, `TC-PASSCUR-032`, `TC-PASSCUR-040`: too-long numeric input is not rejected as an invalid value. UI truncates by mask:
  - passport number `1234567` displays `123456`;
  - passport series `12345` displays `1234`;
  - department code `1234567` displays `123-456`.
- `TC-PASSCUR-010`, `TC-PASSCUR-012`, `TC-PASSCUR-031`, `TC-PASSCUR-033`, `TC-PASSCUR-038`, `TC-PASSCUR-041`: incomplete/mixed masked values are cleared on blur and usually fall back to required/format validation. Expected steps should assert clear-on-blur behavior and exact UI messages:
  - `Обязательно к заполнению`;
  - `Код подразделения не в формате 000-000`.
- `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018`: add prerequisite with stable code `772013` or `770001`; add mandatory focus into `Кем выдан`; do not use `770000` or `123456` as positive DaData data because no options appeared for them in this pass.

Blocked / not fully closed:

- None after the additional `Кем выдан` focus check, but auto-prefill without focusing `Кем выдан` was not observed.

## 4-3-contact-persons.md

Total test cases in file: 38.

Confirmed or UI-ready:

- `TC-CP-AD5F4C7217`, `TC-CP-3C9ECFD5DC`, `TC-CP-547CF72DA6`: `ДОБАВИТЬ КОНТАКТНОЕ ЛИЦО` adds a row with `Фамилия`, `Телефон`, `Имя`, `Отношение к заявителю`, `Отчество`, `Дата рождения`.
- `TC-CP-069C73C682`, `TC-CP-59FA884A01`, `TC-CP-1031D2F0FF`: delete control in the added contact-person row was found and clicked; no confirmation dialog appeared; the row fields disappeared after click.
- `TC-CP-3D0077E42F`, `TC-CP-A84688D4DB`, `TC-CP-05637FFFE5`, `TC-CP-254BA94E1D`, `TC-CP-6560C2E054`: relationship dropdown is editable/required and shows options:
  - `супруг/супруга`
  - `отец/мать`
  - `сестра/брат`
  - `теща/свекровь/тесть/свекр`
  - `сын/дочь`
  - `друг/знакомый/коллега`
  - `иное`
- `TC-CP-43B1FF4F19`, `TC-CP-B01529711C`, `TC-CP-3921E86CCA`, `TC-CP-C76A595256`, `TC-CP-216EC18624`, `TC-CP-2CBD2F1BE6`: phone field is required/editable and uses phone mask.
- `TC-CP-116443D9EB`, `TC-CP-C0C583C405`: `Имя` and `Фамилия` have required markers; after invalid/empty blur they can show `Выберите значение`.
- `TC-CP-351CD544DE`, `TC-CP-1E7C130DD4`, `TC-CP-382F750F94`, `TC-CP-2DD9D4E006`: contact surname positive/edit/display path is confirmed with stable value `Петров-Бояров`. Manual input remains after blur as valid; dropdown also contains exact option `Петров-Бояров`, and selected value remains after blur.
- `TC-CP-BF2F522CE8`, `TC-CP-FD0866A774`, `TC-CP-D49350060B`, `TC-CP-443F3F4189`: contact name positive/edit/display path is confirmed with `Иван`; value remains after blur as valid.
- `TC-CP-C5BCDBF312`, `TC-CP-23A987DEFD`, `TC-CP-AB0B41DC31`, `TC-CP-9CF13C2E86`: contact patronymic positive/edit/display path is confirmed with `Иванович`; value remains after blur as valid.
- `TC-CP-FD0683A355`: patronymic has no required marker.
- `TC-CP-7EC8C7FA5A`, `TC-CP-F374C4FBF7`, `TC-CP-30984FE5C2`, `TC-CP-36147078D3`, `TC-CP-FEEAF4F60E`: contact birth date is editable/required; future date `31.07.2026` stays displayed but field remains invalid; valid date `30.07.2000` is valid.

Phone format observations:

- `9991234567` -> displayed `+7 (999) 123-45-67`, valid after blur.
- `999123456` -> displayed as incomplete mask during input, then cleared on blur; required/invalid.
- `99912345678` -> displayed `+7 (999) 123-45-67`; extra digit ignored/truncated, valid after blur.
- `99912A4567` -> letter is filtered/ignored, resulting masked value is incomplete and clears on blur; required/invalid.
- `99912 4567` -> space is filtered/ignored, resulting masked value is incomplete and clears on blur; required/invalid.

Needs test-case correction:

- `TC-CP-B78F72E22B`: selecting `иное` did not show an additional visible text field in the contact-person row. UI only kept value `иное` in `Отношение к заявителю`.
- `TC-CP-B01529711C`: expected behavior for too-long phone must be truncation/ignored extra digit, not invalid rejection.
- FIO positive tests should use stable values from rerun evidence:
  - `Фамилия`: `Петров-Бояров`;
  - `Имя`: `Иван`;
  - `Отчество`: `Иванович`.
  These values were retained after blur as valid in the rerun.

Blocked / not fully closed:

- None for the previously reopened contact-person delete/FIO positive checks.

## 4-3-personal-data.md

Total test cases in file: 40.

Confirmed or UI-ready:

- `TC-PERSON-001`: gender options visible: `Мужской`, `Женский`.
- `TC-PERSON-002`: gender is filled by DaData surname selection. With slow input and dropdown selection, selecting `Иванов` from `li.ui-menu-item` sets `Пол = Мужской`; selecting `Иванова` sets `Пол = Женский`.
- `TC-PERSON-003`, `TC-PERSON-004`: `Клиент менял ФИО` switch is visible and off by default.
- `TC-PERSON-005`: current `Имя` is filled by DaData selection. Slow input `Иван` opens `.ui-menu-item` options including `Иван`; selected value remains valid after blur.
- `TC-PERSON-011`, `TC-PERSON-016`, `TC-PERSON-036`: previous-FIO DaData fields are executable after enabling `Клиент менял ФИО`. `Предыдущая фамилия = Иванов`, `Предыдущее имя = Иван`, `Предыдущее отчество = Иванович` were selected from dropdown and remained valid after blur.
- `TC-PERSON-006`, `TC-PERSON-022`, `TC-PERSON-026`, `TC-PERSON-037`: invalid characters in FIO-like fields produce/retain invalid behavior; observed message: `Введено некорректное значение`.
- `TC-PERSON-008`, `TC-PERSON-010`, `TC-PERSON-024`, `TC-PERSON-028`, `TC-PERSON-035`: fields are visible/displayed; `ID Клиента` is readonly and empty before save.
- `TC-PERSON-014`, `TC-PERSON-019`, `TC-PERSON-039`: previous-FIO fields become visible/required after enabling `Клиент менял ФИО`; after selecting values from dropdown the fields are not invalid.
- `TC-PERSON-021`: current `Фамилия` is filled by DaData selection. Slow input is required; in the visible Chrome pass the dropdown appeared after additional wait and exposed `.ui-menu-item` options including `Иванов`, `Иванова`, `Ивановская`, `Ивановский`.
- `TC-PERSON-025`: current `Отчество` is filled by DaData selection. In the final visible-Chrome rerun, after current surname `Иванов` and gender `Мужской`, slow input `Иванович` opened `li.ui-menu-item` options including `Ивановна` and `Иванович`; selecting `Иванович` left the field valid after blur. Previous-FIO patronymic `Иванович` was also selected successfully.
- `TC-PERSON-029`, `TC-PERSON-030`, `TC-PERSON-031`, `TC-PERSON-032`, `TC-PERSON-033`, `TC-PERSON-034`: DOB field accepts date input and shows valid/invalid state.

DOB observations on 2026-07-30:

- `31.07.2026` stays displayed, invalid.
- `31.07.2008` stays displayed, invalid.
- `30.07.2008` stays displayed, invalid.
- `29.07.1926` stays displayed, valid.
- `30.07.1926` stays displayed, valid.

Needs test-case correction:

- DaData/FIO positive cases must use slow input and dropdown selection, not simple fill+blur:
  - type characters slowly;
  - wait until `.ui-menu-item` options appear;
  - select the target option;
  - then blur and assert final field state.
- `TC-PERSON-007`, `TC-PERSON-013`, `TC-PERSON-018`, `TC-PERSON-023`, `TC-PERSON-027`, `TC-PERSON-038`: do not assert that simple manually typed FIO strings are retained as valid free text unless a dropdown/suggestion is selected.
- `TC-PERSON-029` and `TC-PERSON-031`: current UI treated both `29.07.1926` and `30.07.1926` as valid on 2026-07-30. If the expected rule is strict 100-year upper age boundary, test data or expected result must be corrected.
- `TC-PERSON-032`: current UI treated exact 18th birthday `30.07.2008` as invalid on 2026-07-30. Clarify whether this is a UI defect or the expected business rule.

Blocked / not fully closed:

- `TC-PERSON-009`: `ID Клиента` after save was not closed. It needs a safe full save path and a reliable expected-value oracle/source for the generated ID.
- No DaData/FIO personal-data cases remain blocked after the slow-input visible-Chrome rerun.

## Summary

- Files attempted: 3.
- Test cases attempted by file count: 122.
- Best-covered file: `4-3-current-passport-data.md`; all previously blocked `Кем выдан` DaData cases can be made UI-ready with corrected preconditions.
- `4-3-contact-persons.md`: all previously reopened execution blockers were passed in UI; remaining issues are expected-result mismatches only (`иное` does not open an extra field; too-long phone is truncated/accepted).
- `4-3-personal-data.md`: DaData/FIO, gender autofill, and previous-FIO positive path are confirmed after the slow-input visible-Chrome rerun. The only remaining blocked item is `TC-PERSON-009`, because `ID Клиента` after save needs a safe full save path and an expected-value oracle/source.

## Required Test-Case Updates

- Add global prerequisite: after login select `cff`, press `ЗАПУСТИТЬ`, then create a new application by `СОЗДАТЬ ЗАЯВКУ`.
- For passport `Кем выдан`, use code `772013` or `770001`; after entering code, focus `Кем выдан`, wait about 3 seconds, select `.ui-menu-item`, then blur before asserting valid state.
- For masked numeric fields, replace "too long is invalid" expectations with "extra input is ignored/truncated by mask" where observed.
- For short masked values, assert clear-on-blur plus required/format message.
- For contact phone, assert exact displayed values from this report, especially `99912345678` becoming valid masked `+7 (999) 123-45-67`.
- For contact relationship `иное`, remove expectation for an extra text field unless a different trigger is found.
- For personal/contact FIO fields, use stable dropdown selection in positive tests; do not treat manually typed FIO text as reliably retained free text.
- For DOB boundary tests, update expected results or flag a product question: exact 18th birthday was invalid, while dates at/over 100-year boundary were valid on this stand as of 2026-07-30.
- For `ID Клиента` save effect, add full required-data setup and define an external expected-value oracle before making the test automation-ready.
