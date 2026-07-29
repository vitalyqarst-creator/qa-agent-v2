# Post-UI product decisions: PostFinal-v2-rc5

## Назначение

Файл фиксирует продуктовые решения после разбора UI calibration evidence по спорным тест-кейсам. Эти решения не являются автоматической заменой ФТ наблюдаемым UI: для каждого пункта ниже явно указано, что считать требованием, что считать дефектом реализации, а что считать дефектом тест-дизайна.

## Решения

### DEC-UI-001 — `TC-CP-B78F72E22B`

- Область: `4.3-contact-persons`.
- Суть: при выборе значения `Иное` в поле `Отношение к заявителю` UI не показал дополнительное текстовое поле.
- Решение: ориентироваться на ФТ; отсутствие дополнительного поля в UI считать дефектом реализации.
- Действие по test-case: baseline TC не переписывать под фактическое UI-поведение.
- Действие по UI evidence: сохранять статус `mismatch-ft-ui`.

### DEC-UI-002 — `TC-CP-116443D9EB`

- Область: `4.3-contact-persons`.
- Суть: поля `Фамилия`, `Имя`, `Отчество` контактного лица в реализации работают как DaData/autocomplete поля.
- Решение: DaData/autocomplete для полей ФИО контактного лица считать требованием/уточнением, а не случайным UI-наблюдением.
- Действие по test-case: обновить TC так, чтобы обязательность поля `Имя` проверялась с учётом DaData/autocomplete поведения. Не выдумывать точный текст ошибки, если UI его не отображает.
- Действие по UI evidence: считать observed required marker / required empty state достаточным evidence для текущего TC.

### DEC-UI-002A — FIO DaData/autocomplete consistency

- Область: `4.3-contact-persons`.
- Суть: после принятия DEC-UI-002 все ФИО-кейсы должны использовать единую модель поля: DaData/autocomplete control, а не обычный свободный text input.
- Решение: закрыть FIO calibration candidates по уже собранному evidence:
  - `TC-CP-BF2F522CE8`: invalid `Имя` может временно вводиться, но очищается после blur.
  - `TC-CP-351CD544DE`: invalid `Фамилия` может временно вводиться, но очищается после blur.
  - `TC-CP-C0C583C405`: пустая `Фамилия` проверяется как обязательное DaData/autocomplete поле без обязательного exact error text.
  - `TC-CP-C5BCDBF312`: invalid `Отчество` очищается после blur; пустое `Отчество` остаётся допустимым.
  - `TC-CP-FD0683A355`: пустое `Отчество` подтверждено как необязательное поле без `*`, `required` и `invalid`.
- Действие по test-case: обновить перечисленные TC и убрать `ui-calibration-required` / `candidate-ui-calibration`.
- Editability consistency: `TC-CP-FD0866A774`, `TC-CP-1E7C130DD4`, `TC-CP-23A987DEFD` должны проверять ввод поискового значения в DaData/autocomplete поле, а не обычное свободное редактирование или выбор конкретного fixture.
- Ограничение: не создавать новые positive DaData-selection TC без конкретных проверенных query / fixture values.

### DEC-UI-003 — `TC-PASSCUR-011`, `TC-PASSCUR-032`, `TC-PASSCUR-040`

- Область: `4.3-current-passport-data`.
- Суть: при вводе значения сверх длины серия, номер и код подразделения обрезаются/форматируются до допустимой длины и становятся валидными.
- Решение: реализация корректна; это input mask behavior, а не дефект продукта.
- Действие по test-case: текущий baseline уже ожидает truncation/mask behavior, поэтому переписывать эти TC не требуется.
- Действие по UI evidence: заменить прежнюю классификацию `mismatch-ft-ui` на `confirmed`.

### DEC-UI-004 — `TC-DOC-023`, `TC-DOC-029`, `TC-DOC-034`

- Область: `11-4.3-application-documents-and-recognition`.
- Суть: после загрузки файла в поле документа file picker скрывается; видимого пути загрузить второй файл в то же поле нет.
- Решение: не тестировать загрузку второго файла в одно поле, если интерфейс не предоставляет такой путь.
- Действие по test-case: заменить duplicate-upload negative сценарии на single-file state проверки: файл отображается, доступны view/delete/download actions, file picker для второго файла в том же поле не отображается.
- Действие по UI evidence: считать новое single-file поведение подтверждённым.

## Дата фиксации

- Дата: 2026-07-29.
- Основание: пользовательское продуктовое решение после разбора UI calibration evidence.


### DEC-UI-005 ? `TC-PASSCUR-003`, `TC-PASSCUR-005`, `TC-PASSCUR-018`

- ???????: `4.3-current-passport-data`.
- ????: follow-up UI evidence ?????????? DaData/FMS ???? ??? ???? `??? ?????` ? fixture `FX-DADATA-FMS-POS-001`.
- ???????? ??????: `??? ????????????? = 772-053`; dropdown item `??? ?????? ?. ?????? 772-053`; ???????? ???????? ???? `??? ????? = ??? ?????? ?. ??????`.
- ???????: ??????? `TC-PASSCUR-003`, `TC-PASSCUR-005` ? `TC-PASSCUR-018` `confirmed` / automation-ready ??? ????? trigger `click/focus` ?? ???? `??? ?????` ????? ????? ???? ?????????????.
- ???????????: ?? ????????? ?????????????? ????? ????? ????? ????, blur ??? Enter; evidence ???????, ??? dropdown ?????????? ????? ?????? ?? `??? ?????`.
- Evidence: `work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md`.
