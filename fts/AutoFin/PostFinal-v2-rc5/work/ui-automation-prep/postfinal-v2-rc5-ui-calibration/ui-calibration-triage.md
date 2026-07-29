# UI calibration triage: PostFinal-v2-rc5

## Назначение

Этот triage принимает UI evidence из commit `5be541547f3b1ec4459c91272a2cfcaa64c275d5` и классифицирует, что можно делать дальше с тест-кейсами.

UI-наблюдение не заменяет ФТ. Baseline FT-first файлы в `test-cases/*.md` не должны переписываться автоматически по фактической реализации. Любая правка по UI допустима только в отдельной `automation-ready` версии или как явно помеченное `FT/UI Divergence`.

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
| Confirmed | 91 | Можно переносить в automation-ready как `confirmed`, если у кейса есть воспроизводимый setup path и screenshot evidence. Baseline не менять. |
| Safe automation-ready wording/update | 16 | Можно уточнить automation-ready expected result/steps по observed UI без изменения FT-смысла. Baseline менять только после отдельной source-review проверки, если исходный TC реально был wording defect. |
| Requires FT/UI decision | 8 | Нельзя молча менять тест-кейс под UI. Нужно решить: дефект реализации, дефект ФТ/макета, или устаревший тестовый intent. |
| Blocked | 9 | Не обновлять expected result. Нужны стабильные данные, внешний path или ручной/повторный UI-прогон. |

## Triage по mismatch / needs update

### 4.3-contact-persons

| TC-ID | UI finding | Triage decision | Что делать дальше |
| --- | --- | --- | --- |
| `TC-CP-B78F72E22B` | При выборе `иное` дополнительное поле уточнения не появилось. | `requires-ft-ui-decision` | Не удалять ожидаемое поле из baseline без проверки ФТ/source. В automation-ready можно отметить фактическое UI-поведение и `FT/UI Divergence`. |
| `TC-CP-6560C2E054` | Пустое `Отношение к заявителю` invalid, но отдельный текст ошибки не виден. | `safe-automation-ready-update` | В automation-ready ожидать required/invalid state, не конкретный message. Baseline менять только если source не требует message. |
| `TC-CP-B01529711C` | Телефон: 10 цифр форматируются, лишняя цифра игнорируется, буквы игнорируются, неполное значение очищается при blur. | `safe-automation-ready-update` | В automation-ready зафиксировать exact mask и clear/truncate behavior. Не считать это изменением FT, если ФТ задаёт только формат/маску. |
| `TC-CP-C76A595256` | Пустой телефон invalid/required, отдельный текст не виден. | `safe-automation-ready-update` | В automation-ready проверять required/invalid state. |
| `TC-CP-BF2F522CE8` | Невалидное имя временно вводится, очищается при blur, persistent message нет. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur. Baseline FT-first оставить как запрет невалидных символов, если ФТ задаёт класс допустимых символов. |
| `TC-CP-116443D9EB` | Пустое имя required/invalid; возможно сообщение `Выберите значение` из autocomplete/select-like control. | `requires-ft-ui-decision` | Нужно решить, корректен ли select/autocomplete для ФИО контактного лица. Не фиксировать `Выберите значение` как окончательный oracle без повторной проверки/подтверждения. |
| `TC-CP-351CD544DE` | Невалидная фамилия очищается при blur; persistent message нет. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur. |
| `TC-CP-C0C583C405` | Пустая фамилия required/invalid, отдельный текст не виден. | `safe-automation-ready-update` | В automation-ready проверять required/invalid state. |
| `TC-CP-C5BCDBF312` | Отчество необязательно, но невалидные символы очищаются при blur. | `safe-automation-ready-update` | В automation-ready разделить optional requiredness и format filtering. |
| `TC-CP-7EC8C7FA5A` | Будущая дата рождения остаётся в поле, field invalid, видимый message не наблюдался. | `safe-automation-ready-update` | В automation-ready ожидать invalid state без message. Значение даты делать динамическим `текущая дата + 1 день`, не hardcode evidence-date. |
| `TC-CP-30984FE5C2` | Пустая дата рождения required/invalid, отдельный текст не виден. | `safe-automation-ready-update` | В automation-ready проверять required/invalid state. |

### 4.3-current-passport-data

| TC-ID | UI finding | Triage decision | Что делать дальше |
| --- | --- | --- | --- |
| `TC-PASSCUR-010` | Нечисловой номер очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + точный message. |
| `TC-PASSCUR-011` | 7-значный номер обрезается до 6 цифр и становится valid. | `requires-ft-ui-decision` | Если ФТ требует строго 6 цифр, truncation может быть допустимым UI-механизмом или дефектом теста. Не называть это ошибкой продукта без source decision. |
| `TC-PASSCUR-012` | 5-значный номер очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-031` | Нечисловая серия очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-032` | 5-значная серия обрезается до 4 цифр и становится valid. | `requires-ft-ui-decision` | Не фиксировать как regression defect без source decision. Для automation-ready можно описать observed truncation с `FT/UI Divergence`, если baseline ожидал rejection. |
| `TC-PASSCUR-033` | 3-значная серия очищается при blur и даёт `Обязательно к заполнению`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-038` | Нечисловой код подразделения очищается и даёт `Код подразделения не в формате 000-000`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |
| `TC-PASSCUR-040` | 7-значный код подразделения обрезается/форматируется в `123-456` и становится valid. | `requires-ft-ui-decision` | Нужна source/product decision: это маска ввода или дефект обработки лишнего символа. |
| `TC-PASSCUR-041` | 5-значный код подразделения очищается и даёт `Код подразделения не в формате 000-000`. | `safe-automation-ready-update` | В automation-ready описать clear-on-blur + exact message. |

### 11-4.3-application-documents-and-recognition

| TC-ID | UI finding | Triage decision | Что делать дальше |
| --- | --- | --- | --- |
| `TC-DOC-023` | После загрузки анкеты picker скрывается, второго file picker path нет. | `requires-ft-ui-decision` | Проверить ФТ: если multiple upload не требуется, это test-design defect; если требуется, это FT/UI divergence. Не заменять молча на single-file behavior. |
| `TC-DOC-029` | После загрузки паспорта клиента picker скрывается. | `requires-ft-ui-decision` | То же: нужна проверка source intent по duplicate/multiple upload. |
| `TC-DOC-034` | После загрузки второго документа picker скрывается. | `requires-ft-ui-decision` | То же: не переписывать duplicate scenario без source decision. |
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

1. Не менять `test-cases/*.md`.
2. Создать отдельные initial automation-ready файлы по трём baseline files.
3. При создании automation-ready:
   - confirmed TC получить `UI Verification Status: confirmed`;
   - safe update TC обновить по observed UI и evidence;
   - requires-ft-ui-decision TC оставить с `UI Verification Status: mismatch-ft-ui` и явным `FT/UI Divergence`;
   - blocked TC оставить в файле с canonical blocker status и без выдуманного expected result.
4. Для DaData/FMS blocked TC подготовить отдельный короткий UI rerun prompt со стабильными query/fixture values.
5. Для duplicate upload, QR/mobile upload и `иное` в отношении сначала сверить ФТ/source. Если source не требует поведения, удалить/заменить можно только через обычный test-case review/revision, не через UI evidence alone.

## Что можно считать готовым к automation-ready без обсуждения

- 91 confirmed TC как перенос статуса/evidence.
- 16 safe automation-ready wording/update TC из таблиц выше.

## Что требует отдельного решения

- `TC-CP-B78F72E22B`
- `TC-CP-116443D9EB`
- `TC-PASSCUR-011`
- `TC-PASSCUR-032`
- `TC-PASSCUR-040`
- `TC-DOC-023`
- `TC-DOC-029`
- `TC-DOC-034`

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
