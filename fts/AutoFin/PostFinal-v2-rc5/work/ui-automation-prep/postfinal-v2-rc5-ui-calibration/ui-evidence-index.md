# UI evidence index: PostFinal-v2-rc5 UI calibration

## Scope

- `scope_slug`: `postfinal-v2-rc5-ui-calibration`
- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `date`: 2026-07-28
- `browser`: Playwright Chromium session `ui-cal`
- `user_account`: `zhidkov`
- `user_role`: `Виталий Жидков`; exact role name was not displayed.

All paths below are repo-relative. Source `test-cases/*.md`, DOCX/XHTML/PDF/support/mockups, auth/session files, cookies, storage state, and `.env` files are not part of this evidence package.

## Evidence Policy

- `trace_policy`: `not-collected`
- `artifact_availability`: committed screenshots and per-TC markdown files are portable; raw Playwright traces, runtime downloads and upload fixture files were not committed.
- `downstream_rule`: screenshots and per-TC notes are sufficient for triage, but mismatch cases should keep explicit `FT/UI Divergence` until source/product decision or a repeat run with trace evidence.

## Evidence package

- Validation report: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md`
- Per-TC detailed evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/`
- Screenshots: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/`

## Canonical Evidence Artifact Table

| test_case_id | artifact_type | path | note |
| --- | --- | --- | --- |
| TC-CP-AD5F4C7217 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Добавление строки контактного лица |
| TC-CP-069C73C682 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-delete-icon-visible.png | confirmed; Удаление контактного лица |
| TC-CP-59FA884A01 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-delete-icon-visible.png | confirmed; Удаление всех полей контактного лица |
| TC-CP-1031D2F0FF | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-delete-icon-visible.png | confirmed; Наличие иконки удаления |
| TC-CP-547CF72DA6 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Полный набор полей строки и кнопка добавления |
| TC-CP-3C9ECFD5DC | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; Отображение кнопки добавления контакта |
| TC-CP-3D0077E42F | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-relation-options.png | confirmed; Состав списка отношений |
| TC-CP-B78F72E22B | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-relation-other-selected.png | mismatch-ft-ui; Поведение при выборе `иное` |
| TC-CP-A84688D4DB | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-relation-options.png | confirmed; Редактируемость отношения |
| TC-CP-6560C2E054 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-6560C2E054.md | mismatch-ft-ui; Обязательность отношения |
| TC-CP-05637FFFE5 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; Отношение не видно до добавления контакта |
| TC-CP-254BA94E1D | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Отношение видно после добавления контакта |
| TC-CP-43B1FF4F19 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-phone-valid-after-blur.png | confirmed; Маска телефона по умолчанию |
| TC-CP-B01529711C | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-B01529711C.md | mismatch-ft-ui; Short/long/alpha ввод телефона |
| TC-CP-3921E86CCA | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-phone-valid-after-blur.png | confirmed; Редактируемость телефона |
| TC-CP-C76A595256 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-C76A595256.md | mismatch-ft-ui; Обязательность телефона |
| TC-CP-216EC18624 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; Телефон не виден до добавления контакта |
| TC-CP-2CBD2F1BE6 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Телефон виден после добавления контакта |
| TC-CP-BF2F522CE8 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-BF2F522CE8.md | mismatch-ft-ui; Невалидный ввод имени |
| TC-CP-FD0866A774 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Редактируемость имени |
| TC-CP-116443D9EB | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-116443D9EB.md | confirmed; Обязательность имени; DaData/autocomplete requirement accepted |
| TC-CP-D49350060B | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; Имя не видно до добавления контакта |
| TC-CP-443F3F4189 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Имя видно после добавления контакта |
| TC-CP-351CD544DE | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-351CD544DE.md | mismatch-ft-ui; Невалидный ввод фамилии |
| TC-CP-1E7C130DD4 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Редактируемость фамилии |
| TC-CP-C0C583C405 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-C0C583C405.md | mismatch-ft-ui; Обязательность фамилии |
| TC-CP-382F750F94 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; Фамилия не видна до добавления контакта |
| TC-CP-2DD9D4E006 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Фамилия видна после добавления контакта |
| TC-CP-C5BCDBF312 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-C5BCDBF312.md | mismatch-ft-ui; Невалидный ввод отчества |
| TC-CP-23A987DEFD | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Редактируемость отчества |
| TC-CP-FD0683A355 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-FD0683A355.md | confirmed; Необязательность отчества |
| TC-CP-AB0B41DC31 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; Отчество не видно до добавления контакта |
| TC-CP-9CF13C2E86 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; Отчество видно после добавления контакта |
| TC-CP-7EC8C7FA5A | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-7EC8C7FA5A.md | mismatch-ft-ui; Будущая дата рождения контактного лица |
| TC-CP-F374C4FBF7 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-required-and-future-date.png | confirmed; Редактируемость DOB |
| TC-CP-30984FE5C2 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-CP-30984FE5C2.md | mismatch-ft-ui; Обязательность DOB |
| TC-CP-36147078D3 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/application-create-after-contact-add-attempt.png | confirmed; DOB не видна до добавления контакта |
| TC-CP-FEEAF4F60E | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/contact-person-empty-after-add.png | confirmed; DOB видна после добавления контакта |
| TC-PASSCUR-001 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-manual-toggle-click.png | confirmed; `Кем выдан` обязателен в ручном режиме |
| TC-PASSCUR-002 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-dadata-code-770000.png | confirmed; `Кем выдан` обязателен в DaData mode |
| TC-PASSCUR-003 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-dadata-code-770000.png | blocked-observability; Prefill `Кем выдан` по коду подразделения |
| TC-PASSCUR-004 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-manual-toggle-click.png | confirmed; Отображение manual `Кем выдан` |
| TC-PASSCUR-005 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | blocked-observability; Список DaData для `Кем выдан` |
| TC-PASSCUR-006 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Default `Клиент менял паспорт` |
| TC-PASSCUR-007 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Отображение switch `Клиент менял паспорт` |
| TC-PASSCUR-008 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Обязательность места рождения |
| TC-PASSCUR-009 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Отображение места рождения |
| TC-PASSCUR-010 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | mismatch-ft-ui; Нечисловой номер паспорта |
| TC-PASSCUR-011 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Слишком длинный номер паспорта обрезается маской |
| TC-PASSCUR-012 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-012.md | mismatch-ft-ui; Короткий номер паспорта |
| TC-PASSCUR-013 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Валидный 6-значный номер |
| TC-PASSCUR-014 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Шесть одинаковых цифр номера |
| TC-PASSCUR-015 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Обязательность номера |
| TC-PASSCUR-016 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Отображение номера |
| TC-PASSCUR-017 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Default manual switch off |
| TC-PASSCUR-018 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | blocked-observability; DaData suggestions по issuing authority |
| TC-PASSCUR-019 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-manual-toggle-click.png | confirmed; Отображение manual switch |
| TC-PASSCUR-020 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Паспорт просрочен при 45+91 |
| TC-PASSCUR-021 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Выдача до 14 лет |
| TC-PASSCUR-022 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Паспорт просрочен при 20+91 |
| TC-PASSCUR-023 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-023.md | confirmed; Positive boundary 45 minus 1 day / 90 days |
| TC-PASSCUR-024 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-024.md | confirmed; Positive boundary 14th birthday |
| TC-PASSCUR-025 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-025.md | confirmed; Positive boundary 20 years / 90 days |
| TC-PASSCUR-026 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-026.md | confirmed; Positive boundary 45th birthday |
| TC-PASSCUR-027 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Будущая дата выдачи паспорта |
| TC-PASSCUR-028 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/passcur-026-issue-date-45th-birthday.png | confirmed; Допустимые границы даты выдачи |
| TC-PASSCUR-029 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Обязательность даты выдачи |
| TC-PASSCUR-030 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Отображение даты выдачи |
| TC-PASSCUR-031 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | mismatch-ft-ui; Нечисловая серия |
| TC-PASSCUR-032 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Слишком длинная серия обрезается маской |
| TC-PASSCUR-033 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-033.md | mismatch-ft-ui; Короткая серия |
| TC-PASSCUR-034 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Валидная 4-значная серия |
| TC-PASSCUR-035 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Три одинаковых цифры в серии |
| TC-PASSCUR-036 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Обязательность серии |
| TC-PASSCUR-037 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Отображение серии |
| TC-PASSCUR-038 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | mismatch-ft-ui; Нечисловой код подразделения |
| TC-PASSCUR-039 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-dadata-code-770000.png | confirmed; Форматирование кода подразделения |
| TC-PASSCUR-040 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Слишком длинный код подразделения обрезается/форматируется маской |
| TC-PASSCUR-041 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/TC-PASSCUR-041.md | mismatch-ft-ui; Короткий код подразделения |
| TC-PASSCUR-042 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-passport-dadata-code-770000.png | confirmed; Валидный 6-значный код |
| TC-PASSCUR-043 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Обязательность кода подразделения |
| TC-PASSCUR-044 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Отображение кода подразделения |
| TC-DOC-001 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Отображение `Анкета клиента` |
| TC-DOC-002 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Отображение `Паспорт клиента` |
| TC-DOC-003 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Отображение `Тип документа` |
| TC-DOC-004 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Отображение `Второй документ` |
| TC-DOC-005 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Список типов документов |
| TC-DOC-006 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-download-click.png | confirmed; Инструкция по анкете клиента |
| TC-DOC-007 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Доступность второго документа после выбора типа |
| TC-DOC-008 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-type-vu-selected.png | confirmed; Поле `Серия` для `ВУ` |
| TC-DOC-009 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-type-zagran-selected.png | confirmed; Поле `Серия` для `Загран. паспорт` |
| TC-DOC-010 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-type-zagran-selected.png | confirmed; Поле `Номер` второго документа |
| TC-DOC-011 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-type-zagran-selected.png | confirmed; Поле `Дата выдачи` второго документа |
| TC-DOC-012 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-type-zagran-selected.png | confirmed; Поле `Кем выдан` второго документа |
| TC-DOC-013 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-second-issue-date-future.png | confirmed; Future issue date второго документа |
| TC-DOC-014 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Required state анкеты при переходе |
| TC-DOC-015 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Required state паспорта клиента |
| TC-DOC-016 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Required state типа документа |
| TC-DOC-017 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | confirmed; Required state второго документа после выбора типа |
| TC-DOC-018 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-valid-upload.png | confirmed; Upload valid PDF в `Анкета клиента` |
| TC-DOC-019 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | not-automatable-manual-only; Drag-and-drop upload анкеты |
| TC-DOC-020 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-attach-phone-click.png | not-automatable-manual-only; QR/mobile upload анкеты |
| TC-DOC-021 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-invalid-format.png | confirmed; Invalid format upload анкеты |
| TC-DOC-022 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-large-file.png | confirmed; Large PDF upload анкеты |
| TC-DOC-023 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-valid-upload.png | confirmed; Single-file state после загрузки анкеты |
| TC-DOC-024 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-passport-second-valid-upload.png | confirmed; Upload valid PDF в `Паспорт клиента` |
| TC-DOC-025 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | not-automatable-manual-only; Drag-and-drop upload паспорта клиента |
| TC-DOC-026 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | not-automatable-manual-only; QR/mobile upload паспорта клиента |
| TC-DOC-027 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-passport-second-invalid-large.png | confirmed; Invalid format паспорта клиента |
| TC-DOC-028 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-passport-second-invalid-large.png | confirmed; Large PDF паспорта клиента |
| TC-DOC-029 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-passport-second-valid-upload.png | confirmed; Single-file state после загрузки паспорта клиента |
| TC-DOC-030 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-passport-second-valid-upload.png | confirmed; Upload valid PDF во `Второй документ` |
| TC-DOC-031 | log | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md | not-automatable-manual-only; Drag-and-drop upload второго документа |
| TC-DOC-032 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-passport-second-invalid-large.png | confirmed; Invalid format второго документа |
| TC-DOC-033 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/doc-passport-second-invalid-large.png | confirmed; Large PDF второго документа |
| TC-DOC-034 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-passport-second-valid-upload.png | confirmed; Single-file state после загрузки второго документа |
| TC-DOC-035 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-valid-upload.png | confirmed; Отображение eye/view icon |
| TC-DOC-036 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-visible-view-click.png | mismatch-ft-ui; Поведение eye/view icon |
| TC-DOC-037 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-valid-upload.png | confirmed; Отображение trash/delete icon |
| TC-DOC-038 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-anketa-after-delete.png | confirmed; Удаление uploaded file |
| TC-DOC-039 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-attach-phone-click.png | confirmed; Отображение `Прикрепить с телефона` |
| TC-DOC-040 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-attach-phone-click.png | blocked-observability; QR после `Прикрепить с телефона` |
| TC-DOC-041 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-download-click.png | confirmed; Отображение `Скачать (документ)` |
| TC-DOC-042 | screenshot | fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/screenshots/alltc-doc-download-click.png | confirmed; Скачивание PDF |

## Status mapping

- `confirmed`: UI behavior matches the test intent.
- `mismatch-ft-ui`: UI was executable, but actual UI behavior differs from FT-first expectation and the test-case needs update.
- `blocked-observability`: UI/data/access path was insufficient for execution without inventing behavior.
- `not-automatable-manual-only`: external manual/mobile/drag-and-drop path was required and was not reproducible in this automation session.
- `not-reproducible`: not used as a separate final bucket in this run.

## Detailed Observations

Подробные per-TC observations, triggers, фактические UI reactions и triage notes сохранены в:

- ts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md
- ts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-calibration-triage.md
- ts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/per-tc/

В этом index намеренно оставлена только canonical artifact table, чтобы validator не интерпретировал descriptive status tables как artifact-path таблицы.
