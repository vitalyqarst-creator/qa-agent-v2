# UI calibration index

Пакет: `fts/AutoFin/PostFinal-v2-rc5`

Версия агента в bundle:

- branch: `codex/postfinal-v2-ui-calibration-pack`
- base agent commit: `e10cd53d56500660fee97890be4d081b4453b83c`

## Included test-case files

| Файл | Всего TC | Calibration TC |
| --- | ---: | ---: |
| `test-cases/4-3-contact-persons.md` | 38 | 5 |
| `test-cases/4-3-current-passport-data.md` | 44 | 7 |
| `test-cases/11-4.3-application-documents-and-recognition.md` | 42 | 0 |

Итого: 124 test cases, 12 требуют UI-калибровки после закрытия ФИО-кейсов продуктовым решением в `work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/post-ui-product-decisions.md`.


## Resolution update 2026-07-29

The active automation-ready draft is now in `test-cases/automation-ready/`. The 12 calibration questions listed below were consumed into that draft where UI evidence was sufficient. DaData/FMS blockers `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018` are resolved by `work/ui-automation-prep/passcur-dadata-fms-772-053/`. Manual/mobile-only cases are intentionally not processed in this iteration.

## Calibration cases

| TC-ID | Файл | Название | Что нужно уточнить в UI |
| --- | --- | --- | --- |
| `TC-CP-6560C2E054` | `test-cases/4-3-contact-persons.md` | Поле `Отношение к заявителю` является обязательным после добавления контактного лица | Какое действие запускает проверку обязательности пустого поля Отношение к заявителю и какой фактический UI-отклик отображается? |
| `TC-CP-B01529711C` | `test-cases/4-3-contact-persons.md` | Ввод допустимого значения: «Телефон» | Какой фактический UI-отклик отображается при вводе значения короче 10 цифр, длиннее 10 цифр или нечислового символа в поле Телефон? |
| `TC-CP-C76A595256` | `test-cases/4-3-contact-persons.md` | Поле `Телефон` является обязательным после добавления контактного лица | Какое действие запускает проверку обязательности пустого поля Телефон и какой фактический UI-отклик отображается? |
| `TC-CP-7EC8C7FA5A` | `test-cases/4-3-contact-persons.md` | Дата рождения контактного лица не может быть больше текущей даты | Какое действие запускает проверку будущей даты рождения и какой фактический UI-отклик отображается? |
| `TC-CP-30984FE5C2` | `test-cases/4-3-contact-persons.md` | Поле `Дата рождения` является обязательным после добавления контактного лица | Какое действие запускает проверку обязательности пустого поля Дата рождения и какой фактический UI-отклик отображается? |
| `TC-PASSCUR-012` | `test-cases/4-3-current-passport-data.md` | Короткое значение в поле «Номер» | Какой точный UI-отклик подтверждает, что значение короче точной длины не принимается как валидное? |
| `TC-PASSCUR-023` | `test-cases/4-3-current-passport-data.md` | Срок действия паспорта на 90-й день после 45-летия | Какой точный наблюдаемый UI-отклик возникает при использовании значения «дата выдачи = дата 45-летия - 1 день; текущая дата = дата 45-летия + 90 дней» для элемента «Дата выдачи»? |
| `TC-PASSCUR-024` | `test-cases/4-3-current-passport-data.md` | Дата выдачи в день 14-летия клиента | Какой точный наблюдаемый UI-отклик возникает при использовании значения «дата 14-летия» для элемента «Дата выдачи»? |
| `TC-PASSCUR-025` | `test-cases/4-3-current-passport-data.md` | Срок действия паспорта на 90-й день после 20-летия | Какой точный наблюдаемый UI-отклик возникает при использовании значения «дата выдачи = дата 20-летия; текущая дата = дата 20-летия + 90 дней» для элемента «Дата выдачи»? |
| `TC-PASSCUR-026` | `test-cases/4-3-current-passport-data.md` | Дата выдачи паспорта в день 45-летия | Какой точный наблюдаемый UI-отклик возникает при использовании значения «дата выдачи = дата 45-летия» для элемента «Дата выдачи»? |
| `TC-PASSCUR-033` | `test-cases/4-3-current-passport-data.md` | Короткое значение в поле «Серия» | Какой точный UI-отклик подтверждает, что значение короче точной длины не принимается как валидное? |
| `TC-PASSCUR-041` | `test-cases/4-3-current-passport-data.md` | Короткое значение в поле «Код подразделения» | Какой точный UI-отклик подтверждает, что значение короче точной длины не принимается как валидное? |

## Expected output

Заполняй результаты в `work/ui-calibration-prep/results/`.

Не переписывай `test-cases/*.md` во время первичного UI-прохода. После сбора evidence можно отдельной задачей подготовить automation-ready/update report.
