# Skill Boundaries

## Активные skill-и

- `ft-source-locator`
- `ft-scope-analyzer`
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
- зафиксировать границы, source refs, visual bindings и существенные gaps в
  `source-scope.md`;
- создать единый файл вопросов БА, если вопрос меняет test intent.

Не входит:

- поиск FT-пакета с нуля;
- подмена внешних scope-ов внутренними рабочими пакетами;
- финальное написание кейсов;
- review кейсов;
- аудит skill-архитектуры.

### `ft-test-case-writer`

- писать новые тест-кейсы по подтвержденному scope.
- править существующий набор тест-кейсов по findings artifact.
- использовать принятую matrix, source refs и решения БА как входы для
  покрытия и правок.

Не входит:

- выбор FT-пакета;
- первичное определение scope;
- review existing cases;
- orchestration of the session-based review-cycle;
- аудит agent-layer.

### `ft-test-case-reviewer`

- review существующих кейсов;
- выполнять review-mode `traceability`, `structure`, `test-design` и режим `full` по умолчанию;
- проверять matrix до TC и TC после принятия matrix в независимой верхнеуровневой сессии;
- проверять, что source refs и коды требований сохранены в matrix и тест-кейсах;
- findings по coverage, atomarity, traceability, structure, expected results и test design;
- structured findings artifact и human summary.

Не входит:

- написание новых кейсов как основной режим;
- исправление тест-кейсов;
- выбор FT-пакета и scope с нуля;
- аудит agent-layer.

### `ft-ui-automation-prep`

- запускаться только после accepted practical v1 baseline с `tc-accepted` final review;
- проходить утвержденные ручные кейсы в реальном UI;
- использовать package-level UI operational notes из `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`, если они есть;
- собирать Playwright evidence и индекс артефактов;
- фиксировать расхождения `FT vs UI` и blockers;
- выпускать отдельную automation-ready версию тест-кейсов без перезаписи baseline-набора.

Не входит:

- выбор FT-пакета и первичное определение scope;
- выпуск или изменение FT-first baseline;
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
