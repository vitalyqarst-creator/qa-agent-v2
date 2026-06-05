# Skill Boundaries

## Активные skill-и

- `ft-source-locator`
- `ft-scope-analyzer`
- `ft-test-case-iteration`
- `ft-test-case-writer`
- `ft-test-case-reviewer`
- `ft-ui-automation-prep`
- `agent-architecture-auditor`

Целевой диапазон active skills: от 4 до 7.

## Ответственность

### `ft-source-locator`

- выбрать правильный FT-пакет;
- определить основные и связанные файлы;
- зафиксировать, где должны храниться результаты.

Не входит:

- анализ секций;
- написание тест-кейсов;
- review кейсов;
- аудит agent-layer.

### `ft-scope-analyzer`

- для большого ФТ сначала предложить внешние candidate scope-ы по разделам/подразделам;
- определить релевантный раздел или подраздел для выбранного внешнего scope;
- сузить scope;
- создать `source-parity-check.md` для подтвержденного scope, если доступны DOCX и PDF основного ФТ;
- создать `source-row-inventory.md` для подтвержденного scope, если source parity содержит таблицы/строки или scope основан на таблице полей/действий;
- разделить выбранный внешний scope на внутренние рабочие пакеты, если он неоднородный;
- сформировать `coverage gaps`.

Не входит:

- поиск FT-пакета с нуля;
- подмена внешних scope-ов внутренними рабочими пакетами;
- финальное написание кейсов;
- review кейсов;
- аудит skill-архитектуры.

### `ft-test-case-writer`

- писать новые тест-кейсы по подтвержденному scope.
- править существующий набор тест-кейсов по findings artifact.
- использовать `source-parity-check.md` как обязательный вход для сохранения requirement IDs при наличии DOCX+PDF.
- использовать `source-row-inventory.md` как независимый вход, чтобы не терять строки источника до атомаризации.
- учитывать findings по режимам `traceability`, `structure`, `test-design`.
- использовать traceability matrix как входной артефакт для правок покрытия.

Не входит:

- выбор FT-пакета;
- первичное определение scope;
- review existing cases;
- orchestration of the session-based review-cycle;
- аудит agent-layer.

### `ft-test-case-iteration`

- оркестрировать цикл writer -> reviewer -> writer -> reviewer;
- передавать findings artifact и writer response artifact между раундами;
- передавать traceability matrix между reviewer и writer, если она требуется;
- завершать цикл со статусом `signed-off` или `round-cap-reached`.

Не входит:

- писать тест-кейсы вместо writer;
- делать review вместо reviewer;
- выбирать FT-пакет и scope с нуля;
- аудит agent-layer.

### `ft-test-case-reviewer`

- review существующих кейсов;
- выполнять review-mode `traceability`, `structure`, `test-design` и режим `full` по умолчанию;
- проверять, что mandatory IDs из `source-parity-check.md` сохранены в ledger/matrix и тест-кейсах;
- проверять, что все in-scope rows из `source-row-inventory.md` сохранены в writer-side inventory и связаны с `ATOM-*`, `GAP-*` или явным out-of-scope решением;
- строить отдельную traceability matrix по атомарным утверждениям ФТ;
- findings по coverage, atomarity, traceability, structure, expected results и test design;
- structured findings artifact и human summary.

Не входит:

- написание новых кейсов как основной режим;
- исправление тест-кейсов;
- выбор FT-пакета и scope с нуля;
- аудит agent-layer.

### `ft-ui-automation-prep`

- запускаться только после `ft-test-case-iteration` со статусом `signed-off`;
- проходить утвержденные ручные кейсы в реальном UI;
- использовать package-level UI operational notes из `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`, если они есть;
- собирать Playwright evidence и индекс артефактов;
- фиксировать расхождения `FT vs UI` и blockers;
- выпускать отдельную automation-ready версию тест-кейсов без перезаписи baseline-набора.

Не входит:

- выбор FT-пакета и первичное определение scope;
- session-based review-cycle и sign-off ручного набора;
- перезапись FT-first baseline;
- трактовка UI как нового source of truth;
- генерация Playwright test specs.

### `agent-architecture-auditor`

- проверять размещение знаний;
- искать дублирование;
- проверять согласованность `AGENTS.md`, `skills/`, `references/`, scripts и tests.

Не входит:

- быть источником доменных QA-правил;
- подменять writer/reviewer/source/scope skill-и.


