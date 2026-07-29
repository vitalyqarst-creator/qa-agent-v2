# UI calibration triage: PostFinal-v2-rc5

## Назначение

Этот triage принимает UI evidence из commit `5be541547f3b1ec4459c91272a2cfcaa64c275d5` и классифицирует, что можно делать дальше с тест-кейсами.

UI-наблюдение не заменяет ФТ. Baseline FT-first файлы в `test-cases/*.md` не должны переписываться автоматически по фактической реализации. Исключение — явно зафиксированное продуктовое решение в `post-ui-product-decisions.md`, где указано, что менять: сохранить FT-ожидание, признать дефект реализации, добавить уточнение требования или исправить дефект тест-дизайна.

## Входные артефакты

- `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-contact-persons.md`
- `fts/AutoFin/PostFinal-v2-rc5/test-cases/4-3-current-passport-data.md`
- `fts/AutoFin/PostFinal-v2-rc5/test-cases/11-4.3-application-documents-and-recognition.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-evidence-index.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/evidence/`

## Проверка полноты evidence

- Всего baseline TC-ID: `124`.
- UI report/index покрывает `124/124` baseline TC-ID.
- Evidence paths в index repo-relative.
- Missing evidence paths: `0`.
- В commit добавлены только UI evidence/report artifacts, baseline/source/support/mockups не изменялись.
- Automation-ready файлы отсутствуют.

## Форматные замечания к полученному UI report

Эти замечания не обесценивают evidence, но их нужно учесть перед downstream-использованием:

1. Scope указан агрегированно как `postfinal-v2-rc5-ui-calibration`, а не как три отдельных scope-а. Для automation-ready лучше вести результат по реальным scope-ам:
   - `4.3-contact-persons`;
   - `4.3-current-passport-data`;
   - `11-4.3-application-documents-and-recognition`.
2. Первичный report был нормализован на canonical status names: `mismatch-ft-ui`, `blocked-observability`, `not-automatable-manual-only`.
3. Trace-файлы не приложены. Для mismatch-результатов это limitation: screenshots и per-TC notes достаточны для triage, но для финального automation-ready желательно либо добавить trace, либо явно сохранять `trace_policy: not-collected`.
4. Часть evidence ссылается на DOM/Playwright eval output как текстовое наблюдение. Это допустимо как supporting note, но не должно быть единственным основанием для `confirmed` / `mismatch-ft-ui`.

## Сводка triage-решений

| Категория | Количество | Решение |
| --- | ---: | --- |
| Confirmed / applied decision | 102 | Можно переносить в automation-ready как `confirmed`, если у кейса есть воспроизводимый setup path и evidence. Для этой категории уже применены закрытые product decisions и FIO DaData/autocomplete updates. |
| Safe automation-ready wording/update | 12 | Можно уточнить automation-ready expected result/steps по observed UI без изменения FT-смысла. Baseline менять только после отдельной source-review проверки, если исходный TC реально был wording defect. |
| Resolved product decision | 8 | Решения зафиксированы в `post-ui-product-decisions.md`: 1 implementation defect, 1 requirement update, 3 confirmed mask behavior, 3 test-design replacements. |
| Blocked | 9 | Не обновлять expected result. Нужны стабильные данные, внешний path или ручной/повторный UI-прогон. |

## Triage по mismatch / needs update

### 4.3-contact-persons

| TC-ID | UI finding | Triage decision | Что делать дальше |
| --- | --- | --- | --- |
| `TC-CP-B78F72E22B` | При выборе `иное` дополнительное поле уточнения не появилось. | `implementation-defect` | Ориентироваться на ФТ: baseline не менять; отсутствие дополнительного поля считать дефектом реализации и сохранять `mismatch-ft-ui`. |
| `TC-CP-6560C2E054` | Пустое `Отношение к заявителю` invalid, но отдельный текст ошибки не виден. | `safe-automation-ready-update` | В automation-ready ожидать required/invalid state, не конкретный message. Baseline менять только если source не требует message. |
| `TC-CP-B01529711C` | Телефон: 10 цифр форматируются, лишняя цифра игнорируется, буквы игнорируются, неполное значение очищается при blur. | `safe-automation-ready-update` | В automation-ready зафиксировать exact mask и clear/truncate behavior. Не считать это изменением FT, если ФТ задаёт только формат/маску. |
| `TC-CP-C76A595256` | Пустой телефон invalid/required, отдельный текст не виден. | `safe-automation-ready-update` | В automation-ready проверять required/invalid state. |
| `TC-CP-BF2F522CE8` | Невалидное имя временно вводится, очищается при blur, persistent message нет. | `confirmed-after-test-case-update` | TC обновлён под DaData/autocomplete clear-on-blur behavior без выдуманного exact error text. |
| `TC-CP-116443D9EB` | Пустое имя required/invalid; ФИО контактного лица работает как DaData/autocomplete. | `requirement-update-confirmed` | DaData/autocomplete для ФИО считать требованием/уточнением. TC обновлён: проверяется обязательное DaData/autocomplete поле без выдуманного exact error text. |
| `TC-CP-351CD544DE` | Невалидная фамилия очищается при blur; persistent message нет. | `confirmed-after-test-case-update` | TC обновлён под DaData/autocomplete clear-on-blur behavior без выдуманного exact error text. |
| `TC-CP-C0C583C405` | Пустая фамилия required/invalid, отдельный текст не виден. | `confirmed-after-test-case-update` | TC обновлён: `Фамилия *` проверяется как обязательное DaData/autocomplete поле без exact error text. |
| `TC-CP-C5BCDBF312` | Отчество необязательно, но невалидные символы очищаются при blur. | `confirmed-after-test-case-update` | TC обновлён: invalid non-selected value clears on blur; empty `Отчество` remains optional. |
| `TC-CP-7EC8C7FA5A` | Будущая дата рождения остаётся в поле, field invalid, видимый message не наблюдался. | `safe-automation-ready-update` | В automation-ready ожидать invalid state без message. Значение даты делать динамическим `текущая дата + 1 день`, не hardcode evidence-date. |
| `TC-CP-30984FE5C2` | Пустая дата рождения required/invalid, отдельный текст не виден. | `safe-automation-ready-update` | В automation-ready проверять required/invalid state. |

### 4.3-current-passport-data

| TC-ID | UI finding | Triage decision | Что делать дальше |
| --- | --- | --- | --- |
| `TC-PASSCUR-010` | Нечисловой номер очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + точный message. |
| `TC-PASSCUR-011` | 7-значный номер обрезается до 6 цифр и становится valid. | `confirmed-mask-behavior` | Реализация корректна: это input mask behavior. Текущий baseline уже ожидает truncation до `123456`; переписывать TC не требуется. |
| `TC-PASSCUR-012` | 5-значный номер очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-031` | Нечисловая серия очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-032` | 5-значная серия обрезается до 4 цифр и становится valid. | `confirmed-mask-behavior` | Реализация корректна: это input mask behavior. Текущий baseline уже ожидает truncation до `1234`; переписывать TC не требуется. |
| `TC-PASSCUR-033` | 3-значная серия очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-038` | Нечисловой код подразделения очищается и даёт `Код подразделения не в формате 000-000`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-040` | 7-значный код подразделения обрезается/форматируется в `123-456` и становится valid. | `confirmed-mask-behavior` | Реализация корректна: это input mask behavior. Текущий baseline уже ожидает ограничение до шести цифр; переписывать TC не требуется. |
| `TC-PASSCUR-041` | 5-значный код подразделения очищается и даёт `Код подразделения не в формате 000-000`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |

### 11-4.3-application-documents-and-recognition

| TC-ID | UI finding | Triage decision | Что делать дальше |
| --- | --- | --- | --- |
| `TC-DOC-023` | После загрузки анкеты picker скрывается, второго file picker path нет. | `test-design-replaced` | Duplicate-upload сценарий заменён на single-file state проверку: файл отображается, доступны view/delete/download, picker второго файла отсутствует. |
| `TC-DOC-029` | После загрузки паспорта клиента picker скрывается. | `test-design-replaced` | Duplicate-upload сценарий заменён на single-file state проверку. |
| `TC-DOC-034` | После загрузки второго документа picker скрывается. | `test-design-replaced` | Duplicate-upload сценарий заменён на single-file state проверку. |
| `TC-DOC-036` | View icon открывает PDF в новой `blob:` вкладке, а не in-page modal. | `safe-automation-ready-update` | Если ФТ требует только просмотр, automation-ready можно обновить на observed new-tab behavior. Если ФТ/макет требует modal, пометить `FT/UI Divergence`. |

## Triage по blocked

| TC-ID | Причина | Canonical status | Что делать дальше |
| --- | --- | --- | --- |
| `TC-PASSCUR-003` | DaData/code fixture `770000` не автозаполнил `Кем выдан`. | `blocked-observability` | Нужен стабильный DaData/FMS fixture для стенда или ручной precondition. |
| `TC-PASSCUR-005` | DaData suggestions для `Кем выдан` не появились по проверенному вводу. | `blocked-observability` | Нужен проверенный query literal / fixture; не менять TC на отсутствие suggestions. |
| `TC-PASSCUR-018` | Та же зависимость от DaData suggestions/autocomplete. | `blocked-observability` | Нужен повторный UI-прогон со стабильными данными. |
| `TC-DOC-019` | Drag-and-drop upload анкеты не воспроизведён в automation session. | `not-automatable-manual-only` | Не удалять TC. Нужен ручной UI evidence или отдельный automation technique для drag/drop. |
| `TC-DOC-020` | QR/mobile upload анкеты требует внешнего phone/QR flow. | `not-automatable-manual-only` | Нужен отдельный ручной/мобильный сценарий или scope exclusion для automation. |
| `TC-DOC-025` | Drag-and-drop upload паспорта клиента не воспроизведён. | `not-automatable-manual-only` | То же, что `TC-DOC-019`. |
| `TC-DOC-026` | QR/mobile upload паспорта клиента требует external flow. | `not-automatable-manual-only` | То же, что `TC-DOC-020`. |
| `TC-DOC-031` | Drag-and-drop upload второго документа не воспроизведён. | `not-automatable-manual-only` | То же, что `TC-DOC-019`. |
| `TC-DOC-040` | `Прикрепить с телефона` видим, но QR dialog не открылся воспроизводимо. | `blocked-observability` | Нужна повторная проверка на стенде или clarification по expected QR flow. |

## Рекомендации по следующему шагу

1. Использовать `post-ui-product-decisions.md` как обязательный input перед downstream-работой с этим evidence.
2. Сохранить `TC-CP-B78F72E22B` как FT-ожидание и завести/передать дефект реализации по отсутствующему уточняющему полю для `Иное`.
3. При создании automation-ready:
   - confirmed TC получить `UI Verification Status: confirmed`;
   - safe update TC обновить по observed UI и evidence;
   - `TC-CP-B78F72E22B` оставить с `UI Verification Status: mismatch-ft-ui` и явным `FT/UI Divergence`;
   - `TC-CP-116443D9EB`, `TC-CP-C0C583C405`, `TC-CP-BF2F522CE8`, `TC-CP-351CD544DE`, `TC-CP-C5BCDBF312`, `TC-CP-FD0683A355` использовать как confirmed FIO DaData/autocomplete cases;
   - `TC-PASSCUR-011`, `TC-PASSCUR-032`, `TC-PASSCUR-040` считать confirmed mask behavior;
   - `TC-DOC-023`, `TC-DOC-029`, `TC-DOC-034` брать уже в заменённой single-file формулировке;
   - blocked TC оставить в файле с canonical blocker status и без выдуманного expected result.
4. Для DaData/FMS blocked TC подготовить отдельный короткий UI rerun prompt со стабильными query/fixture values.
5. Для QR/mobile upload оставить manual/blocked path до отдельной проверки.

## Что можно считать готовым к automation-ready без обсуждения

- 102 confirmed / applied-decision TC как перенос статуса/evidence.
- 12 remaining safe automation-ready wording/update TC из таблиц выше.

## Что закрыто продуктовым решением

- `TC-CP-B78F72E22B` — implementation defect, baseline preserved.
- `TC-CP-116443D9EB` — DaData/autocomplete requirement update.
- `TC-CP-BF2F522CE8`, `TC-CP-351CD544DE`, `TC-CP-C0C583C405`, `TC-CP-C5BCDBF312`, `TC-CP-FD0683A355` — aligned with FIO DaData/autocomplete product decision and UI evidence.
- `TC-PASSCUR-011`, `TC-PASSCUR-032`, `TC-PASSCUR-040` — confirmed mask behavior.
- `TC-DOC-023`, `TC-DOC-029`, `TC-DOC-034` — duplicate upload TC replaced by single-file state TC.

## Что требует повторного UI/data-prerequisite прогона

- `TC-PASSCUR-003`
- `TC-PASSCUR-005`
- `TC-PASSCUR-018`
- `TC-DOC-019`
- `TC-DOC-020`
- `TC-DOC-025`
- `TC-DOC-026`
- `TC-DOC-031`
- `TC-DOC-040`
