# Отчет по UI-калибровке: все test-cases PostFinal-v2-rc5

## Метаданные

- `package`: `fts/AutoFin/PostFinal-v2-rc5`
- `stand_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`
- `application_url`: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/application/card/create`
- `tester`: FT Test Case Agent / UI calibration
- `date`: 2026-07-28
- `browser`: Playwright Chromium session `ui-cal`
- `user_account`: `zhidkov`
- `user_role`: в UI отображается `Виталий Жидков`; точное название роли не отображалось.
- `source_files`:
  - `test-cases/4-3-contact-persons.md`
  - `test-cases/4-3-current-passport-data.md`
  - `test-cases/11-4.3-application-documents-and-recognition.md`

## Объем проверки и метод

На UI-стенде проверены все 124 TC-ID из трех файлов `test-cases`. Source analysis, writer, reviewer, bridge, benchmark, sharding и генерация новых test-cases не запускались. В первичном UI-прогоне исходные файлы test-case не редактировались; последующие точечные правки внесены только по зафиксированным product decisions и UI evidence.

Использованные статусы:

- `confirmed`: фактическое поведение UI соответствует смыслу теста и воспроизводится на стенде.
- `mismatch-ft-ui`: кейс удалось выполнить в UI, но фактические labels/messages/control behavior отличаются от текущей формулировки test-case или требуют отдельного FT/UI triage.
- `blocked-observability`: UI/data path недостаточны для выполнения кейса без выдумывания поведения.
- `not-automatable-manual-only`: проверка требует внешнего manual/mobile/drag-and-drop path, не воспроизведенного в текущей automation session.

## Сводка

- Всего проверено: 124
- `confirmed`: 105
- `mismatch-ft-ui`: 13
- `blocked-observability`: 1
- `not-automatable-manual-only`: 5

По файлам:

| Файл | Всего | Confirmed | Needs update | Blocked |
| --- | ---: | ---: | ---: | ---: |
| `4-3-contact-persons.md` | 38 | 32 | 6 | 0 |
| `4-3-current-passport-data.md` | 44 | 38 | 6 | 0 |
| `11-4.3-application-documents-and-recognition.md` | 42 | 35 | 1 | 6 |

## Confirmed TC-ID

### Контактные лица

`TC-CP-AD5F4C7217`, `TC-CP-069C73C682`, `TC-CP-59FA884A01`, `TC-CP-1031D2F0FF`, `TC-CP-547CF72DA6`, `TC-CP-3C9ECFD5DC`, `TC-CP-3D0077E42F`, `TC-CP-A84688D4DB`, `TC-CP-05637FFFE5`, `TC-CP-254BA94E1D`, `TC-CP-43B1FF4F19`, `TC-CP-3921E86CCA`, `TC-CP-216EC18624`, `TC-CP-2CBD2F1BE6`, `TC-CP-BF2F522CE8`, `TC-CP-FD0866A774`, `TC-CP-116443D9EB`, `TC-CP-D49350060B`, `TC-CP-443F3F4189`, `TC-CP-351CD544DE`, `TC-CP-1E7C130DD4`, `TC-CP-C0C583C405`, `TC-CP-382F750F94`, `TC-CP-2DD9D4E006`, `TC-CP-C5BCDBF312`, `TC-CP-23A987DEFD`, `TC-CP-FD0683A355`, `TC-CP-AB0B41DC31`, `TC-CP-9CF13C2E86`, `TC-CP-F374C4FBF7`, `TC-CP-36147078D3`, `TC-CP-FEEAF4F60E`

### Текущие паспортные данные

`TC-PASSCUR-001`, `TC-PASSCUR-002`, `TC-PASSCUR-003`, `TC-PASSCUR-004`, `TC-PASSCUR-005`, `TC-PASSCUR-006`, `TC-PASSCUR-007`, `TC-PASSCUR-008`, `TC-PASSCUR-009`, `TC-PASSCUR-011`, `TC-PASSCUR-013`, `TC-PASSCUR-014`, `TC-PASSCUR-015`, `TC-PASSCUR-016`, `TC-PASSCUR-017`, `TC-PASSCUR-018`, `TC-PASSCUR-019`, `TC-PASSCUR-020`, `TC-PASSCUR-021`, `TC-PASSCUR-022`, `TC-PASSCUR-023`, `TC-PASSCUR-024`, `TC-PASSCUR-025`, `TC-PASSCUR-026`, `TC-PASSCUR-027`, `TC-PASSCUR-028`, `TC-PASSCUR-029`, `TC-PASSCUR-030`, `TC-PASSCUR-032`, `TC-PASSCUR-034`, `TC-PASSCUR-035`, `TC-PASSCUR-036`, `TC-PASSCUR-037`, `TC-PASSCUR-039`, `TC-PASSCUR-040`, `TC-PASSCUR-042`, `TC-PASSCUR-043`, `TC-PASSCUR-044`

### Документы по заявке и распознавание

`TC-DOC-001`, `TC-DOC-002`, `TC-DOC-003`, `TC-DOC-004`, `TC-DOC-005`, `TC-DOC-006`, `TC-DOC-007`, `TC-DOC-008`, `TC-DOC-009`, `TC-DOC-010`, `TC-DOC-011`, `TC-DOC-012`, `TC-DOC-013`, `TC-DOC-014`, `TC-DOC-015`, `TC-DOC-016`, `TC-DOC-017`, `TC-DOC-018`, `TC-DOC-021`, `TC-DOC-022`, `TC-DOC-023`, `TC-DOC-024`, `TC-DOC-027`, `TC-DOC-028`, `TC-DOC-029`, `TC-DOC-030`, `TC-DOC-032`, `TC-DOC-033`, `TC-DOC-034`, `TC-DOC-035`, `TC-DOC-037`, `TC-DOC-038`, `TC-DOC-039`, `TC-DOC-041`, `TC-DOC-042`

## Требуют обновления test-case

### Контактные лица

| Test Case ID | UI Verification Status | Фактическое поведение UI | Требуемая корректировка |
| --- | --- | --- | --- |
| `TC-CP-B78F72E22B` | `mismatch-ft-ui` | При выборе отношения `иное` значение заполняется в поле отношения; дополнительное видимое поле уточнения в строке контактного лица не появилось. | Product decision: ориентироваться на ФТ; отсутствие дополнительного поля считать дефектом реализации. Baseline TC не менять. |
| `TC-CP-6560C2E054` | `mismatch-ft-ui` | Пустое поле отношения обязательно и получает invalid state; точное видимое сообщение в строке контакта в откалиброванном состоянии не отображалось. | Не ожидать конкретный error text, если шаг явно не приводит UI в то же состояние валидации, где этот текст появляется. |
| `TC-CP-B01529711C` | `mismatch-ft-ui` | Телефон принимает 10 цифр и визуально форматируется как `+7 (999) 123-45-67`; 11-я лишняя цифра игнорируется/обрезается; буквы игнорируются, неполное значение очищается при blur. | Заменить ожидание invalid-long на truncation/ignore behavior; указать точную валидную маску и поведение при blur. |
| `TC-CP-C76A595256` | `mismatch-ft-ui` | Пустой телефон обязателен, поле получает `invalid empty required`; отдельное видимое текстовое сообщение для телефона контактного лица не наблюдалось. | Использовать state поля/required marker как ожидаемый результат, а не выдуманный текст сообщения. |
| `TC-CP-7EC8C7FA5A` | `mismatch-ft-ui` | Будущая дата `29.07.2026` остается в поле, поле становится invalid; видимый текст сообщения для DOB контактного лица не наблюдался. | Ожидать invalid state без предположения о сообщении. |
| `TC-CP-30984FE5C2` | `mismatch-ft-ui` | Пустая DOB обязательна и invalid; отдельное текстовое сообщение для DOB контактного лица не наблюдалось. | Использовать required marker/invalid state как expected result. |

### Текущие паспортные данные

| Test Case ID | UI Verification Status | Фактическое поведение UI | Требуемая корректировка |
| --- | --- | --- | --- |
| `TC-PASSCUR-010` | `mismatch-ft-ui` | Нечисловой номер паспорта очищается при blur и показывает required-style validation (`Обязательно к заполнению`), потому что значение становится пустым. | Expected result должен описывать clear-on-blur плюс required message, а не generic `invalid number`. |
| `TC-PASSCUR-012` | `mismatch-ft-ui` | 5-значный номер очищается при blur и показывает `Обязательно к заполнению`. | Использовать точное сообщение и clear-on-blur behavior. |
| `TC-PASSCUR-031` | `mismatch-ft-ui` | Нечисловая серия очищается при blur и показывает `Обязательно к заполнению`. | Использовать точное сообщение и clear-on-blur behavior. |
| `TC-PASSCUR-033` | `mismatch-ft-ui` | 3-значная серия очищается при blur и показывает `Обязательно к заполнению`. | Использовать точное сообщение и clear-on-blur behavior. |
| `TC-PASSCUR-038` | `mismatch-ft-ui` | Нечисловой код подразделения очищается при blur и показывает `Код подразделения не в формате 000-000`. | Использовать точное сообщение и clear-on-blur behavior. |
| `TC-PASSCUR-041` | `mismatch-ft-ui` | 5-значный код подразделения очищается и показывает `Код подразделения не в формате 000-000`. | Использовать точное сообщение и clear-on-blur behavior. |

### Документы по заявке и распознавание

| Test Case ID | UI Verification Status | Фактическое поведение UI | Требуемая корректировка |
| --- | --- | --- | --- |
| `TC-DOC-036` | `mismatch-ft-ui` | Иконка просмотра открывает загруженный PDF в новой вкладке браузера с `blob:http://...`; in-page modal не наблюдался. | Expected result должен говорить `открывается новая blob-вкладка/окно`, а не modal, если не требуется другая настройка viewer. |

## Resolved by follow-up DaData/FMS evidence

| Test Case ID | Previous status | New status | Evidence |
| --- | --- | --- | --- |

## Blocked UI input

| Test Case ID | UI Verification Status | Причина блокировки |
| --- | --- | --- |
| `TC-DOC-019` | `not-automatable-manual-only` | Drag-and-drop upload для `Анкета клиента` не удалось надежно выполнить в доступном browser automation path; вместо него проверен file chooser upload. |
| `TC-DOC-020` | `not-automatable-manual-only` | QR/mobile upload path для `Анкета клиента` требует внешнего phone/QR flow; usable QR dialog из видимого контрола не открылся. |
| `TC-DOC-025` | `not-automatable-manual-only` | Drag-and-drop upload для `Паспорт клиента` не удалось надежно выполнить в доступном browser automation path. |
| `TC-DOC-026` | `not-automatable-manual-only` | QR/mobile upload path для `Паспорт клиента` требует внешнего phone/QR flow. |
| `TC-DOC-031` | `not-automatable-manual-only` | Drag-and-drop upload для `Второй документ` не удалось надежно выполнить в доступном browser automation path. |
| `TC-DOC-040` | `blocked-observability` | `Прикрепить с телефона` отображается в `Документы по заявке`, но клик не открыл воспроизводимый QR dialog в проверенной сессии. |

## Ключевое фактическое поведение UI

- Новая заявка открывается с секциями `Паспортные данные`, `Контакты клиента`, `Документы по заявке`.
- `Добавить контактное лицо` добавляет одну строку контактного лица с полями `Фамилия *`, `Телефон`, `Имя *`, `Отношение к заявителю *`, `Отчество`, `Дата рождения *`.
- Product decision после разбора evidence: поля `Фамилия`, `Имя`, `Отчество` контактного лица считать DaData/autocomplete полями.
- Иконка удаления контактного лица - пустая icon button справа от строки; клик удаляет все поля контактного лица и оставляет `Добавить контактное лицо`.
- Наблюдаемые варианты отношения: `супруг/супруга`, `отец/мать`, `сестра/брат`, `теща/свекровь/тесть/свекр`, `сын/дочь`, `друг/знакомый/коллега`, `иное`.
- Ошибка будущей даты выдачи паспорта: `Дата не может быть больше 28.07.2026.`
- Ошибка выдачи паспорта до 14 лет: `Выдача паспорта предусмотрена с 14 лет`.
- Ошибка просроченного паспорта: `Паспорт недействителен (просрочен)`.
- Ошибка повторяющихся цифр в серии паспорта: `Не должно быть трех одинаковых цифр подряд`.
- Ошибка повторяющихся цифр в номере паспорта: `Не должно быть шести одинаковых цифр подряд`.
- Ошибка формата кода подразделения: `Код подразделения не в формате 000-000`.
- Required text в паспортных полях: `Обязательно к заполнению`; DaData-style empty select: `Выберите значение`; empty date: `Введите дату`.
- Переключатель `Ввести вручную подразделение` делает `Кем выдан` вручную редактируемым и обязательным.
- `Клиент менял паспорт` видим и в откалиброванной заявке не имеет класса `checked`.
- Наблюдаемые варианты `Тип документа`: `ВУ`, `СНИЛС`, `Загран. паспорт`.
- Для `ВУ` и `Загран. паспорт` видны поля второго документа `Серия`, `Номер`, `Дата выдачи`, `Кем выдан`.
- Будущая дата выдачи второго документа показывает `Дата не может быть больше 28.07.2026.`
- Валидная загрузка small PDF показывает `valid-small.pdf` и action icons view/delete/download.
- Невалидный формат файла и PDF больше 40 МБ показывают: `Документы не загружены. Проверьте соответствуют ли документы требованиям: формат pdf, размер не более 40 МБ`.
- Действие `Скачать (документ)` скачало `document.pdf`.

## Созданные evidence-файлы

Подробные per-TC evidence files, созданные по шаблону:

- `TC-CP-116443D9EB.md`
- `TC-CP-30984FE5C2.md`
- `TC-CP-351CD544DE.md`
- `TC-CP-6560C2E054.md`
- `TC-CP-7EC8C7FA5A.md`
- `TC-CP-B01529711C.md`
- `TC-CP-BF2F522CE8.md`
- `TC-CP-C0C583C405.md`
- `TC-CP-C5BCDBF312.md`
- `TC-CP-C76A595256.md`
- `TC-CP-FD0683A355.md`
- `TC-PASSCUR-012.md`
- `TC-PASSCUR-023.md`
- `TC-PASSCUR-024.md`
- `TC-PASSCUR-025.md`
- `TC-PASSCUR-026.md`
- `TC-PASSCUR-033.md`
- `TC-PASSCUR-041.md`

Дополнительные скриншоты:

- `application-create-after-contact-add-attempt.png`
- `contact-person-empty-after-add.png`
- `contact-person-empty-after-next.png`
- `contact-required-and-future-date.png`
- `contact-phone-valid-after-blur.png`
- `contact-phone-long-after-blur.png`
- `contact-phone-alpha-after-blur.png`
- `contact-text-digit-after-blur.png`
- `contact-text-special-after-blur.png`
- `contact-relation-options.png`
- `contact-relation-other-selected.png`
- `contact-delete-icon-visible.png`
- `passport-short-values-cleared-after-blur.png`
- `passport-short-values-after-blur.png`
- `passport-short-values-targeted.png`
- `alltc-passport-dadata-code-770000.png`
- `alltc-passport-manual-toggle-click.png`
- `passcur-023-issue-date-45-minus-1-at-90.png`
- `passcur-024-issue-date-14th-birthday.png`
- `passcur-025-issue-date-20-at-90.png`
- `passcur-026-issue-date-45th-birthday.png`
- `alltc-doc-type-vu-selected.png`
- `doc-type-zagran-selected.png`
- `doc-second-issue-date-future.png`
- `alltc-doc-anketa-valid-upload.png`
- `alltc-doc-anketa-after-delete.png`
- `alltc-doc-anketa-invalid-format.png`
- `alltc-doc-anketa-large-file.png`
- `alltc-doc-passport-second-valid-upload.png`
- `doc-passport-second-invalid-large.png`
- `alltc-doc-visible-view-click.png`
- `alltc-doc-attach-phone-click.png`
- `alltc-doc-download-click.png`

Upload fixture filenames used on the remote stand; fixture files were not committed as evidence artifacts:

- valid-small.pdf
- invalid-format.txt
- large-over-40mb.pdf

## Точные изменения для внесения в test-cases после калибровки

1. Выполнено: assertions про generic invalid input в имени/фамилии/отчестве контактного лица заменены на фактическое поведение DaData/autocomplete: невалидные символы могут появляться при вводе, но поле очищается при blur; persistent standalone error text не наблюдался.
2. Заменить ожидания для long/alpha/short телефона контактного лица на фактическое mask behavior: валидные 10 цифр форматируются в `+7 (999) 123-45-67`; лишние цифры игнорируются; буквы игнорируются; неполное значение очищается при blur.
3. Для обязательных контактных полей проверять required marker и observed UI state, а не ненаблюдаемые error messages. Для `Имя` и `Фамилия` это выполнено с учётом DaData/autocomplete поведения.
4. Обновить список вариантов отношения до наблюдаемых значений в нижнем регистре. Ожидание дополнительного поля при выборе `иное` не убирать: по продуктовому решению отсутствие поля в UI считается дефектом реализации.
5. Для серии/номера паспорта/кода подразделения с short и nonnumeric values зафиксировать clear-on-blur и точные сообщения. Для long values зафиксировать truncation до максимальной валидной длины; это признано корректным mask behavior.
6. Выполнено follow-up evidence для DaData/FMS: для `TC-PASSCUR-003`, `TC-PASSCUR-005` и `TC-PASSCUR-018` использовать fixture `FX-DADATA-FMS-POS-001`, код `772-053`, focus/click в `Кем выдан`, выбор `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`.
7. Использовать точные сообщения passport date validation и current-date-sensitive value `28.07.2026` в expected results, где проверяются future/expiry boundaries.
8. Обновить ожидание просмотра документа: загруженный PDF открывается в новой вкладке `blob:http://...`, а не в наблюдаемой in-page modal.
9. Заменить duplicate upload cases на single-file-control behavior. Picker скрывается после валидного файла, отображаются view/delete/download icons; путь загрузки второго файла в то же поле не тестируется.
10. Добавить explicit test-environment prerequisites для drag-and-drop и QR/mobile upload cases. В проверенной automation session drag-and-drop не был надежным, а phone upload не открыл usable QR dialog.

## Automation-ready handoff

Создан automation-ready draft: `fts/AutoFin/PostFinal-v2-rc5/test-cases/automation-ready/`. Baseline `test-cases/*.md` не перезаписываются. Все TC-ID сохранены; TC без воспроизводимого UI path остаются в наборе со статусом `blocked-observability`.
