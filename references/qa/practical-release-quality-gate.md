# Practical Release Quality Gate

Этот reference задает компактный финальный gate для production-oriented маршрута:
быстро получить usable тест-кейсы, но не выпускать набор с очевидными потерями
покрытия, служебными маркерами или неисполняемыми заглушками.

Gate применяется после writer/reviewer правок и перед передачей набора
пользователю как текущего результата.

## Обязательные артефакты

Для FT package с готовыми per-scope файлами в `test-cases/` агент должен
создать:

- единый файл со сквозной нумерацией;
- lightweight coverage matrix;
- release quality report.

Каноническая команда:

```powershell
python scripts\build_test_case_release.py `
  --root fts/<ft-slug>/<ft-version> `
  --release-name <ft-version>-all-test-cases
```

Если несколько файлов имеют одинаковый section prefix или filename order не
доказывает порядок ФТ, передай явный порядок:

```powershell
python scripts\build_test_case_release.py `
  --root fts/<ft-slug>/<ft-version> `
  --release-name <ft-version>-all-test-cases `
  --files test-cases/<scope-1>.md test-cases/<scope-2>.md
```

Порядок `--files` должен быть взят из DOCX/XHTML/PDF структуры, а не из истории
создания файлов.

Команда пишет файлы в `fts/<ft-slug>/<ft-version>/work/exports/`:

- `<release-name>.md`;
- `<release-name>.coverage-matrix.md`;
- `<release-name>.quality-report.md`;
- `<release-name>.quality-report.json`.

## Что gate проверяет автоматически

- Все `TC-*` имеют required runtime поля, включая `Статус тест-кейса`.
- `TC-*` id не дублируются.
- `Статус тест-кейса` использует только canonical release statuses.
- `Трассировка` содержит parseable source/reference ids.
- В runtime TC нет internal design marker `Сценарное обоснование`.
- В runtime TC нет заглушек вида `будет определено в ФТ ...`.
- В runtime TC нет явных agent/process markers, которые должны жить в `work/**`.

Автоматическая проверка не заменяет semantic review. Она закрывает только
дешевые structural/release-smell классы.

## Canonical release statuses

Разрешены:

- `confirmed`;
- `needs-ui-calibration`;
- `candidate-ui-calibration`;
- `needs-test-data`;
- `blocked-observability`;
- `blocked-ui-unavailable`;
- `blocked-access`;
- `needs-future-clarification`;
- `mismatch-ft-ui`;
- `not-automatable-manual-only`.

Свободные локальные статусы запрещены. Если нужен новый статус, сначала обнови
этот reference, скрипт release gate и тесты.

## Manual Senior QA pass перед выпуском

Reviewer обязан отдельно проверить то, что скрипт не может доказать сам:

- каждый requirement code / AS / BSR / GSR / REQ из выбранного scope покрыт
  тест-кейсом либо явно отражен в gap/status;
- PDF-сверка выполнена по страницам, таблицам, приложениям и структуре разделов;
- file upload/download, generated document, dictionary/list, DaData/API/BIC,
  role/status, boundary/exact-length/allowed-symbol dimensions не пропущены;
- `needs-test-data` стоит только там, где действительно нужен fixture/data
  artifact, а не вместо конкретизации;
- `blocked-observability` используется только для поведения, которое нельзя
  наблюдать в текущем FT package/UI без внешнего flow;
- `mismatch-ft-ui` не подгоняет ФТ под реализацию: если пользователь/БА решил,
  что реализация дефектна, baseline остается по ФТ;
- названия, предусловия, шаги и expected results остаются ручными и
  исполнимыми, без ссылок на будущий чат/сессию/agent decision.

Если manual pass нашел проблему, writer/reviewer выполняют bounded revision.
Не запускай benchmark, bridge, sharding или strict iteration для обычного
исправления release quality.

## Success criteria

Набор можно передать пользователю как текущий production-oriented результат,
если:

- release quality report имеет `status = passed` или только явно принятые
  non-blocking warnings;
- validator по FT package возвращает `errors_count = 0` и `warnings_count = 0`
  либо warnings документированно unrelated;
- coverage matrix создана и соответствует всем per-scope файлам;
- остаточные `needs-*` / `blocked-*` / `mismatch-*` статусы перечислены в summary
  и не скрывают missing source coverage.
