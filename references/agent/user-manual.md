# FT Test Case Agent. Пользовательская документация

Версия: 1.1

Этот документ описывает, как пользоваться FT Test Case Agent для работы с функциональными требованиями, макетами, тест-кейсами, session-based review-cycle и подготовкой automation-ready версии. Финальные пользовательские версии руководства выпускаются в DOCX и PDF. Markdown-файл нужен как редактируемый источник.

Руководство является навигационным документом. Если оно расходится с каноническими контрактами, приоритет имеют:

1. `references/agent/instruction-contract-index.md` как карта владельцев правил и validator coverage;
2. конкретный форматный reference в `references/agent/` или `references/qa/`;
3. phase-specific workflow в соответствующем `skills/*/SKILL.md`;
4. техническая проверка в `scripts/validate_agent_artifacts.py`.

Новые правила не должны добавляться только в этот manual без обновления канонического источника.

## 1. Что должно быть установлено или доступно

Перед работой с агентом пользователь должен иметь рабочее окружение проекта и доступ к исходным материалам.

| Что нужно | Когда нужно | Комментарий |
|---|---|---|
| Python `>= 3.11` | Всегда | Требование проекта из `pyproject.toml`. |
| Зависимости проекта | Для чтения DOCX/PDF и Python API | Рекомендуемый запуск: `uv sync`. Минимальные библиотеки: `pydantic`, `pypdf`, `python-docx`. |
| Git-доступ к репозиторию | Всегда | Агент читает и обновляет файлы в структуре проекта. |
| FT-документы `.docx` / `.pdf` | Для всех QA-этапов | Основной текст ФТ является приоритетным источником требований. |
| PDF-версия основного ФТ | Желательно для scope analysis, writer и reviewer | Используется для structural cross-check разделов, границ scope и source parity. Если PDF нет, агент должен явно зафиксировать это ограничение. |
| Табличный редактор для `.xlsx` | Для review traceability | Каждая `round-N-traceability-matrix.md` должна иметь XLSX companion-файл с теми же строками и колонками. |
| Playwright CLI / wrapper | Только для `ft-ui-automation-prep` | Нужен для UI-прогона, snapshot, screenshots, traces и logs. |
| Браузеры Playwright | Только для `ft-ui-automation-prep` | Должны быть установлены и доступны wrapper-у. |
| Runtime URL приложения | Только для `ft-ui-automation-prep` | Можно передать в запросе или зафиксировать в `UI-AGENT-NOTES.md`. |
| Доступ к приложению | Только для `ft-ui-automation-prep` | Учетные данные, тестовая сессия или storage state. В этом репозитории `playwright-cli.json` может ссылаться на `output/playwright/auth/...`. |
| LibreOffice / Poppler | Только для сопровождения DOCX/PDF документации | Нужны не для обычного QA workflow, а для генерации и визуальной проверки финальных руководств. |

Если пользователь запускает только агентный workflow по требованиям, ему обычно достаточно Python, зависимостей проекта и доступа к FT-пакетам. Playwright нужен не всегда: он обязателен только для UI-подготовки automation-ready версии.

## 2. Назначение агента

FT Test Case Agent помогает QA-инженеру получать проверяемые артефакты по функциональным требованиям:

- находить нужный FT-пакет и связанные материалы;
- выделять границы анализа по разделу, блоку, полю или сценарию;
- фиксировать coverage gaps и вопросы к пользователю или аналитику;
- писать ручные тест-кейсы по подтвержденному scope;
- проверять существующие тест-кейсы на покрытие, структуру и качество test design;
- проводить writer/reviewer iteration до `signed-off` или фиксации unresolved findings;
- готовить отдельную `automation-ready` версию после UI-проверки;
- аудитить agent-layer: `AGENTS.md`, `skills/`, `references/`, scripts.

Агент не является источником бизнес-требований. Канонический источник поведения системы - текст ФТ. Макеты, support-файлы, UI и старые тест-кейсы помогают интерпретировать требования, но не заменяют их.

## 3. Что нужно указать в запросе

Минимальный запрос к агенту должен отвечать на четыре вопроса:

1. С каким FT-пакетом работать?
2. Какой этап нужен?
3. Какой scope или какую область требований использовать?
4. Какой артефакт должен получиться?

Если FT-пакет или scope неизвестны, сначала запускаются режимы поиска источника и анализа scope. Не стоит просить агента "посмотреть все и сделать правильно" без этапа и границ: такой запрос почти всегда приводит к смешиванию требований и слабой трассировке.

Рекомендуемый шаблон:

```md
FT-пакет: `fts/<ft-slug>` или описание нужного ФТ
Этап: `ft-...`
Режим scope: `manual-scope` | `agent-proposed-scope`
Scope: раздел / блок / поле / сценарий / `<scope-slug>`
Задача: что нужно сделать
Выходы: какие файлы или артефакты нужны
Ограничения: что не менять и что не додумывать
```

## 4. Структура проекта

Рабочие материалы группируются по FT-пакетам в `fts/`. Один FT-пакет должен хранить все, что относится к конкретному функциональному требованию или группе требований:

```text
fts/
  <ft-slug>/
    source/            основной документ ФТ: DOCX/PDF
    support/           справочники, дополнительные документы, приложения
    mockups/           макеты экранов
    test-cases/        тест-кейсы только по этому FT-пакету
    work/              промежуточные артефакты и handoff
    AGENT-NOTES.md     package-specific контекст, если есть
    README.md          краткая карточка FT-пакета, если есть
```

Главное правило: не смешивать тест-кейсы разных FT-пакетов. Если в проекте несколько основных ФТ, набор тест-кейсов сохраняется рядом со своим FT-пакетом.

## 5. Базовые принципы качества

Агент работает по следующим правилам:

- текст требований приоритетнее макета, если между ними есть расхождение;
- поведение, статусы, поля, кнопки и интеграции нельзя выдумывать;
- неоднозначность фиксируется в `coverage gaps`, `scope-clarification-requests.md` или `unclear`, а не закрывается догадкой;
- один тест-кейс покрывает одну проверку и один основной ожидаемый результат;
- если требование имеет буквенно-цифровой код, например `GSR 22`, в трассировке указывается именно он;
- если основной FT доступен в DOCX и PDF, для подтвержденного scope создается `source-parity-check.md`; коды требований, найденные только в PDF, сохраняются в `req_id`;
- человекочитаемые отчеты и артефакты формируются на русском языке, если другой язык явно не запрошен;
- каждое знание должно иметь один канонический источник; текущая карта источников и validator coverage фиксируется в `references/agent/instruction-contract-index.md`.

## 6. Общая схема работы

| Шаг | Режим | Что делает | Основной результат |
|---|---|---|---|
| 1 | `ft-source-locator` | Находит FT-пакет, основное ФТ, support-файлы и макеты | `source-selection.md`, первичный `workflow-state.yaml` |
| 2 | `ft-scope-analyzer` | Фиксирует границы анализа или предлагает candidate scope | `scope-contract.md`, `source-parity-check.md` при DOCX+PDF или `scope-options.md` |
| 3 | `ft-test-case-writer` | Пишет initial draft или исправляет набор по findings | `test-cases/<section-id>-<scope-slug>.md`, atomic ledger, writer self-check |
| 4 | `ft-test-case-reviewer` | Проверяет покрытие, структуру и test design | `round-N-findings.md`, `round-N-traceability-matrix.md/.xlsx` |
| 5 | `ft-test-case-iteration` | Оркестрирует session-based writer/reviewer cycle | `cycle-state.yaml`, `signed-off` или `round-cap-reached` |
| 6 | `ft-ui-automation-prep` | Проверяет signed-off набор в UI и готовит automation-ready | `automation-ready/<section-id>-<scope-slug>.md`, UI evidence |

Схема pipeline:

```text
Пользовательский запрос
  -> ft-source-locator
  -> ft-scope-analyzer
  -> ft-test-case-writer или ft-test-case-iteration
  -> ft-test-case-reviewer
  -> ft-ui-automation-prep
  -> automation-ready версия
```

Реальный запуск может начинаться не с первого шага. Если FT-пакет и scope уже выбраны, можно сразу запускать writer, reviewer или iteration, но только при наличии нужных handoff-артефактов.

## 7. Handoff-модель

Проект использует `Design A / Hybrid Handoff`. Это означает:

- межэтапный статус хранится только в `workflow-state.yaml`;
- stage handoff для новых scope-ов хранится в numbered-папке `work/stage-handoffs/NN-<scope-slug>/`;
- review-cycle артефакты хранятся в `work/review-cycles/<scope-slug>/`;
- prompt-файлы помогают запустить следующий этап, но не заменяют findings, matrix, writer response или `cycle-state.yaml`.

Базовая структура:

```text
fts/<ft-slug>/
  test-cases/
    <scope-slug>.md
    automation-ready/
      <scope-slug>.md
  work/
    stage-handoffs/
      <scope-slug>/
        workflow-state.yaml
        source-selection.md
        scope-options.md
        scope-selection-prompts.md
        scope-contract.md
        source-parity-check.md
        scope-coverage-gaps.md
        scope-clarification-requests.md
        scope-execution-options.md
        prompt.scope-to-writer.md
        prompt.scope-to-iteration.md
        prompt.*.md
    review-cycles/
      <scope-slug>/
        cycle-state.yaml
        codex-session-map.yaml
        prompts/
        outputs/
        versions/
    ui-automation-prep/
      <scope-slug>/
        ui-validation-report.md
        ui-evidence-index.md
```

Если задача продолжается после перерыва, история чата вторична. Агент должен восстановить контекст из файлов handoff и review-cycle.

## 8. Режим `ft-source-locator`

Используется, когда пользователь не уверен, какой FT-пакет нужен, или нужно подтвердить входные материалы перед анализом.

### Входы

- описание пользовательской задачи;
- структура `fts/`;
- файлы `source/`, `support/`, `mockups/`, `test-cases/`;
- карточки FT-пакетов, если есть.

### Что делает агент

- выбирает подходящий `ft-slug`;
- определяет основной документ ФТ;
- ищет PDF-версию основного ФТ для сверки структуры;
- перечисляет support-файлы и макеты;
- проверяет наличие `AGENT-NOTES.md`;
- фиксирует, куда должны сохраняться будущие тест-кейсы;
- если выбор неоднозначен, возвращает кандидатов и недостающие данные.

### Выходы

- `source-selection.md`;
- обновленный `workflow-state.yaml`;
- handoff к `ft-scope-analyzer`.

### Пример запроса

```md
Найди FT-пакет для требований по расчету ПДН.
Нужен handoff к scope analysis.
Если есть несколько кандидатов, перечисли их и укажи, чего не хватает для точного выбора.
```

### Ограничения

Этот режим не пишет тест-кейсы, не делает review и не определяет детальный scope.

## 9. Режим `ft-scope-analyzer`

Используется после выбора FT-пакета, но до написания или review тест-кейсов. Главная задача - определить границы работы.

### Два режима scope

| Режим | Когда использовать | Результат |
|---|---|---|
| `manual-scope` | Граница уже известна: раздел, поле, блок, сценарий | Подтвержденный `scope-contract.md`, gaps и handoff к writer/iteration |
| `agent-proposed-scope` | FT большой, пользователь просит весь документ или не знает, как лучше разбить работу | `scope-options.md` и prompts для выбора одного внешнего scope по правилам `scope-decomposition-policy.md` |

### Схема выбора scope

```text
FT-пакет выбран
  -> Пользователь знает границу?
       -> да: manual-scope
          -> scope-contract.md
          -> scope-coverage-gaps.md
          -> scope-clarification-requests.md, если есть gaps
          -> prompt.scope-to-writer.md
          -> prompt.scope-to-iteration.md
       -> нет: agent-proposed-scope
          -> scope-options.md
          -> scope-selection-prompts.md
          -> пользователь выбирает один candidate scope
          -> затем запускается manual-scope
```

После `agent-proposed-scope` нельзя сразу переходить к writer. Сначала пользователь должен утвердить один конкретный scope.

Для большого ФТ агент сначала предлагает внешние scope-ы по разделам или подразделам ФТ. Внутренние рабочие пакеты появляются только после выбора одного внешнего scope и не заменяют карту scope-ов.

### Правило про coverage gaps и clarification requests

Каждый gap в `scope-coverage-gaps.md` должен указывать, к чему именно в ФТ он относится: раздел, GSR/код требования при наличии, таблицу/строку, поле/условие, цитату или atomic statement.

Если в `scope-coverage-gaps.md` есть хотя бы один gap, агент создает `scope-clarification-requests.md`. Этот файл:

- является companion-артефактом к gaps;
- связывает каждый вопрос с конкретным `GAP-*`;
- показывает краткую привязку вопроса к конкретному утверждению ФТ;
- не заменяет основной ФТ;
- не хранит process-status;
- используется writer-ом только для подтвержденных ответов.

Writer может использовать только ответы со `response_status = answered` и `response_type = user-confirmed | analyst-confirmed | product-confirmed` как уточняющий вход. `working-assumption` не считается равной тексту ФТ и должна явно отмечаться как assumption.

### Выходы для `manual-scope`

- `scope-contract.md`;
- `source-parity-check.md`, если доступны DOCX+PDF основного ФТ;
- `scope-coverage-gaps.md`;
- `scope-clarification-requests.md`, если есть gaps;
- `prompt.scope-to-writer.md` для одиночного writer-pass;
- `prompt.scope-to-iteration.md` для полного writer-reviewer loop;
- опционально `scope-execution-options.md`;
- обновленный `workflow-state.yaml`.

Важно: если базовый `next_skill` остается `ft-test-case-writer`, `prompt.scope-to-iteration.md` добавляется в `latest_artifacts`, но не обязан попадать в `required_inputs`.

### Выходы для `agent-proposed-scope`

- `scope-options.md`;
- `scope-selection-prompts.md`;
- рекомендация, с какого candidate scope начать.

### Пример `manual-scope`

```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-scope-analyzer`
Режим scope: `manual-scope`
Scope: раздел `<section-id>`
Нужны `scope-contract.md`, `scope-coverage-gaps.md`, `prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md`.
Если есть gaps, укажи их точную привязку к ФТ и создай `scope-clarification-requests.md`.
Scope не расширять.
```

### Пример `agent-proposed-scope`

```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-scope-analyzer`
Режим scope: `agent-proposed-scope`
Предложи разбиение ФТ на candidate scope для поэтапного покрытия тест-кейсами.
Нужны краткие границы каждого scope и рекомендация, с чего начать.
```

## 10. Режим `ft-test-case-writer`

Используется, когда FT-пакет и scope уже подтверждены. Writer не должен сам выбирать новый FT-пакет или расширять scope.

### Подрежимы

| Подрежим | Когда использовать | Что делает |
|---|---|---|
| `initial_draft` | Набор создается с нуля | Сначала строит atomic requirements ledger, затем пишет тест-кейсы и self-check |
| `revision_from_findings` | Reviewer вернул findings | Исправляет существующий набор и готовит writer response |

### Входы

- FT-пакет;
- основной документ ФТ и PDF для сверки, если есть;
- `scope-contract.md`;
- `scope-coverage-gaps.md`;
- `scope-clarification-requests.md`, если есть подтвержденные ответы;
- `workflow-state.yaml`;
- support-файлы и mockups, если они разрешены scope contract;
- для revision: текущий набор, findings, review round, traceability matrix при наличии.

### Выходы

- `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`;
- atomic requirements ledger или traceability matrix со стабильными atomic statement id, например `ATOM-001`;
- краткая карта покрытия;
- `coverage gaps` и открытые вопросы;
- writer self-check для initial draft: uncovered atoms, possible merged checks, assumptions, unclear items;
- `round-N-writer-response.md` в revision mode;
- `prompt.writer-to-reviewer.round-N.md`;
- обновленный `workflow-state.yaml`.

### Правила написания

- В `initial_draft` сначала создается atomic requirements ledger: одно атомарное утверждение ФТ или отдельное правило = одна строка.
- Каждый тест-кейс связывается с одним или несколькими atomic statement id.
- Каждый кейс должен быть атомарным.
- Нельзя требовать поведения, которого нет в ФТ, разрешенных материалах пакета или подтвержденном clarification-ответе.
- Нельзя добавлять точные значения, разделители, статусы, тексты ошибок, порядок нормализации или UI-реакции, если они не следуют из источников.
- Если проверяется поле, порядок обычно такой: видимость и редактируемость, значение по умолчанию и обязательность, позитивные проверки, негативные проверки.
- Для ограничений вида "допустимы только ..." не стоит сводить все негативные проверки к одному общему кейсу, если из ФТ явно следуют разные классы недопустимого ввода.
- Неоднозначности уходят в `coverage gaps` или `unclear`.
- Перед передачей initial draft reviewer-у writer явно фиксирует self-check.

### Пример initial draft

```md
Для scope `2.1.1.1.1.1.2-lichnaya-informaciya` подготовь initial draft тест-кейсов.
Работай только в границах `scope-contract.md`.
Сначала построй atomic requirements ledger, затем тест-кейсы и writer self-check.
На выходе нужен канонический файл в `test-cases/` и handoff к reviewer.
```

### Пример revision

```md
Исправь findings из `round-1-findings.md`.
Режим writer: `revision_from_findings`.
Scope не расширяй.
Нужны обновленный набор и `round-1-writer-response.md` с response status по каждому finding.
```

## 11. Режим `ft-test-case-reviewer`

Используется для review уже существующих тест-кейсов. Reviewer не исправляет кейсы сам, а возвращает findings, matrix и handoff.

### Режимы review

| Режим | Назначение |
|---|---|
| `full` | Режим по умолчанию: `traceability` -> `structure` -> `test-design` |
| `traceability` | Проверяет покрытие атомарных утверждений ФТ |
| `structure` | Проверяет формат, группировку, сквозную нумерацию, порядок и обязательные секции |
| `test-design` | Проверяет позитивные, негативные, boundary, equivalence, dependency, combinations и неподтвержденную конкретику |

Если пользователь не указал режим review, агент использует `full`. Узкие режимы `traceability`, `structure` и `test-design` стоит выбирать только тогда, когда нужна точечная проверка без полного umbrella-review.

### Входы

- существующий набор тест-кейсов;
- FT-пакет и подтвержденный scope;
- PDF-версия ФТ для сверки, если есть;
- `review_mode`;
- `workflow-state.yaml` и handoff-файлы;
- `scope-clarification-requests.md`, если writer использовал ответы пользователя или аналитика;
- для второго review: предыдущие findings, writer response и traceability matrix.

### Выходы

- structured findings artifact;
- human summary;
- `round-N-traceability-matrix.md` и соседний `round-N-traceability-matrix.xlsx` для `traceability` и `full`;
- `prompt.reviewer-to-writer.round-N.md`, если нужна доработка;
- `prompt.reviewer-to-ui-prep.md`, если набор готов к следующему этапу;
- обновленный `workflow-state.yaml`.

### Новое правило про XLSX companion

Если создается или обновляется `round-N-traceability-matrix.md`, рядом в той же директории должен быть создан или обновлен `round-N-traceability-matrix.xlsx` с тем же basename, теми же колонками и строками. Markdown остается человекочитаемым артефактом, XLSX нужен для фильтрации, сортировки и передачи вне markdown workflow.

### Что проверяет reviewer

- наличие atomic requirements ledger или traceability matrix со стабильными atomic statement id;
- согласованность ledger и traceability matrix;
- writer self-check: нет ли скрытых uncovered atoms, merged checks, assumptions или unclear items;
- использование только подтвержденных clarification answers;
- атомарность кейсов;
- полноту позитивных, негативных, boundary, equivalence, dependency и combination проверок;
- полноту явно перечисленных вариантов;
- отсутствие unsupported expected-result specificity: точных разделителей, форматов строк, текстов ошибок, статусов, нормализации или side effects без опоры на ФТ.

### Как читать результат review

Findings сортируются по severity:

- `error` - блокирующая проблема, набор нельзя считать готовым;
- `warning` - значимый риск покрытия или качества;
- `info` - улучшение без блокировки.

Если есть `error`, `warning` или traceability `gap`, набор возвращается writer-у. Если остаются только допустимые `unclear` или `info`, reviewer может рекомендовать следующий этап, но итоговый `signed-off` фиксируется review-cycle.

### Пример запроса

```md
Проведи review набора `fts/.../test-cases/<section-id>-<scope-slug>.md`.
Режим: `full`.
Проверь atomic ledger, writer self-check и traceability matrix.
Создай findings, `round-1-traceability-matrix.md` и `round-1-traceability-matrix.xlsx`.
Не исправляй кейсы.
```

## 12. Режим `ft-test-case-iteration`

Используется, когда нужен полный writer/reviewer loop. Это оркестратор: он не заменяет writer и reviewer, а запускает их последовательно.

### Схема review-cycle

```text
Подтвержденный scope
  -> Writer initial_draft
       -> atomic requirements ledger
       -> тест-кейсы
       -> writer self-check
  -> Reviewer round 1
       -> нет blocking findings: signed-off
       -> есть error/warning/gap:
            -> Writer revision_from_findings
            -> Reviewer round 2
                 -> нет blocking findings: signed-off
                 -> остаются error/warning/gap: round-cap-reached
```

Максимум - два review rounds. Бесконечный цикл запрещен.

### Входы

- FT-пакет;
- `AGENT-NOTES.md`, если есть;
- основной документ ФТ и PDF для сверки, если есть;
- подтвержденный scope;
- `workflow-state.yaml`;
- handoff-файлы;
- целевой файл тест-кейсов или имя нового артефакта.

### Выходы

- финальный или обновленный набор тест-кейсов;
- atomic requirements ledger или traceability matrix со stable atomic statement id;
- `round-1-findings.md`;
- `round-1-traceability-matrix.md` и `round-1-traceability-matrix.xlsx`, если применимо;
- `round-1-writer-response.md`, если была доработка;
- `round-2-findings.md`, если нужен второй review;
- `round-2-traceability-matrix.md` и `round-2-traceability-matrix.xlsx`, если применимо;
- `cycle-state.yaml`;
- обновленный `workflow-state.yaml`.

### Статусы завершения

| Статус | Значение |
|---|---|
| `signed-off` | Набор готов к post-iteration этапу |
| `round-cap-reached` | После второго review остались unresolved findings или gaps |

### Пример запроса

```md
Запусти `ft-test-case-iteration` для scope `<scope-slug>`.
Нужен полный цикл writer -> reviewer -> writer -> reviewer.
Initial draft должен идти через atomic-ledger-first workflow.
Для traceability matrix создай Markdown и XLSX companion.
Обнови `workflow-state.yaml` и все handoff-артефакты.
```

## 13. Режим `ft-ui-automation-prep`

Используется только после `ft-test-case-iteration`, когда набор получил `signed-off`. UI не становится новым источником требований. Текст ФТ остается каноническим.

### Назначение

Режим проверяет signed-off кейсы в реальном интерфейсе, собирает Playwright evidence и готовит отдельную `automation-ready` версию для дальнейшей автоматизации.

### Схема lifecycle

```text
baseline test-cases/<section-id>-<scope>.md
  -> initial automation-ready/<section-id>-<scope>.md
  -> UI rerun через Playwright
  -> ui-validation-report.md
  -> ui-evidence-index.md
  -> updated automation-ready/<section-id>-<scope>.md
```

### Входы

- signed-off набор;
- `cycle-state.yaml` со статусом `signed-off`;
- `workflow-state.yaml` со `stage_status: ready-for-next-stage` и `next_skill: ft-ui-automation-prep`;
- `prompt.reviewer-to-ui-prep.md`;
- runtime URL или route entrypoint приложения;
- доступ к приложению;
- `AGENT-NOTES.md`, если есть;
- `work/ui-automation-prep/UI-AGENT-NOTES.md`, если есть.

### Выходы

- `fts/<ft-slug>/test-cases/automation-ready/<section-id>-<scope-slug>.md`;
- `work/ui-automation-prep/<scope-slug>/ui-validation-report.md`;
- `work/ui-automation-prep/<scope-slug>/ui-evidence-index.md`;
- Playwright artifacts в `output/playwright/<scope-slug>/`;
- blockers и limitations, если UI недоступен или шаги не наблюдаемы.

### UI Verification Status

| Статус | Значение |
|---|---|
| `confirmed` | Поведение воспроизведено в UI |
| `mismatch-ft-ui` | UI воспроизводится, но расходится с ФТ |
| `blocked-ui-unavailable` | UI недоступен |
| `blocked-access` | Нет доступа или авторизации |
| `blocked-observability` | Нельзя наблюдать критерий проверки |
| `not-automatable-manual-only` | Кейс остается ручным |

### Важные ограничения

- Baseline FT-first набор не перезаписывается.
- Если `automation-ready` отсутствует, но baseline есть, агент сначала создает initial `automation-ready`.
- Если нет ни baseline, ни `automation-ready`, агент останавливается и фиксирует blocker.
- Статус кейса нельзя менять только по комментарию пользователя без повторной UI-проверки.
- Если UI расходится с ФТ, расхождение явно фиксируется в `FT/UI Divergence`.

### Пример запроса

```md
Для scope `<scope-slug>` выполни `ft-ui-automation-prep`.
Проверь `workflow-state.yaml` и `prompt.reviewer-to-ui-prep.md`.
Если есть `UI-AGENT-NOTES.md`, используй его.
Нужны automation-ready версия, UI report и evidence index.
```

## 14. Режим `agent-architecture-auditor`

Используется для проверки агентного слоя проекта: `AGENTS.md`, `skills/`, `references/`, scripts.

### Что проверяет

- дублирование правил между `AGENTS.md`, `skills/` и `references/`;
- неправильное размещение знаний;
- устаревшие файлы и ссылки;
- разрастание skill-слоя;
- соответствие канонической модели content placement.

### Основной workflow

Сначала запускается helper script. Предпочтительный путь по skill-у:

```powershell
python scripts/audit_agent_architecture.py --text
```

Если скрипта нет в `scripts/`, в этом репозитории может использоваться skill-local путь:

```powershell
python skills/agent-architecture-auditor/scripts/audit_agent_architecture.py --text
```

Затем агент вручную интерпретирует зоны, где скрипт не может вынести архитектурное суждение.

### Выходы

- findings по severity;
- duplication map;
- recommended moves;
- stale items;
- remediation plan.

### Пример запроса

```md
Проведи аудит agent-layer.
Используй `agent-architecture-auditor`.
Нужны findings, duplication map и remediation plan.
```

## 15. Типовые цепочки использования

### Новый набор тест-кейсов без review-cycle

```text
ft-source-locator
  -> ft-scope-analyzer manual-scope
  -> ft-test-case-writer initial_draft
```

Этот путь быстрее, но слабее по контролю качества. Его стоит использовать для черновиков или когда review будет выполнен отдельно.

### Новый набор с review-cycle

```text
ft-source-locator
  -> ft-scope-analyzer manual-scope
  -> ft-test-case-iteration
```

Это предпочтительный путь для production-ready набора тест-кейсов.

### Большое ФТ без готового scope

```text
ft-source-locator
  -> ft-scope-analyzer agent-proposed-scope (карта внешних scope-ов по разделам/подразделам)
  -> пользователь выбирает один candidate scope
  -> ft-scope-analyzer manual-scope
  -> ft-test-case-iteration
```

Этот путь снижает риск взять слишком широкий или неоднородный scope.

### Review существующего набора

```text
ft-source-locator
  -> ft-scope-analyzer manual-scope
  -> ft-test-case-reviewer full
```

Используется, когда кейсы уже написаны и нужно проверить качество.

### Подготовка automation-ready

```text
ft-test-case-iteration signed-off
  -> ft-ui-automation-prep
  -> automation-ready версия
```

Нельзя запускать этот путь до `signed-off`.

## 16. Как давать ответы на clarification requests

Если агент создал `scope-clarification-requests.md`, пользователь или аналитик отвечает в карточках `CLR-*`. Человек заполняет только:

- блок `Ответ БА` (`user_response`).

Перед вопросом карточка должна содержать `Текст из ФТ`: это конкретная цитата
или несколько коротких цитат из требований, из-за которых возник вопрос. Если
цитаты нет, файл нужно вернуть агенту на исправление, а не заставлять БА искать
исходный текст вручную.

Не меняйте `clarification_id`, `gap_id`, scope, ссылки на ФТ, текст вопроса и служебные поля. После получения ответа агент сам проставляет `response_status`, `response_type` и `updated_at`.

Служебные значения для агента:

| Поле | Значения |
|---|---|
| `response_status` | `unanswered`, `answered`, `superseded`, `rejected` |
| `response_type` | `not-provided`, `working-assumption`, `user-confirmed`, `analyst-confirmed`, `product-confirmed`, `rejected` |

Ответы `analyst-confirmed` и `product-confirmed` могут использоваться writer-ом как уточняющий вход. `working-assumption` можно использовать только как явную рабочую гипотезу, не как замену ФТ.

## 17. Как давать корректировки

Корректировка должна ссылаться на конкретный артефакт:

- `test_case_id`;
- `finding_id`;
- `GAP-*`;
- `ATOM-*`;
- `scope-contract.md`;
- `scope-clarification-requests.md`;
- `workflow-state.yaml`;
- `round-N-findings.md`;
- `round-N-traceability-matrix.md` или `.xlsx`;
- `round-N-writer-response.md`;
- `cycle-state.yaml`;
- конкретный файл в `stage-handoffs/` или `review-cycles/`.

Хороший пример:

```md
Исправь `FINDING-003`.
Scope не расширяй.
Используй `round-1-traceability-matrix.md` и `round-1-traceability-matrix.xlsx`.
Нужен только revision существующего набора и обновление handoff к reviewer.
```

Плохой пример:

```md
Переделай нормально и учти все.
```

Во втором примере нет границ, нет ссылки на finding и нет проверяемого результата.

## 18. Частые ошибки пользователя

| Ошибка | Почему это плохо | Как лучше |
|---|---|---|
| Просить "посмотри все ФТ" | Scope становится слишком широким | Сначала `agent-proposed-scope` с внешними scope-ами по разделам/подразделам |
| Смешивать несколько FT-пакетов | Ломается трассировка | Один FT-пакет на один набор |
| Запускать writer без scope contract | Writer начнет сам угадывать границы | Сначала `ft-scope-analyzer manual-scope` |
| Игнорировать `scope-clarification-requests.md` | Неясные требования попадут в тесты как догадки | Ответить по `GAP-*` или оставить `unclear` |
| Запускать UI-prep до `signed-off` | UI-prep не заменяет review-cycle | Сначала `ft-test-case-iteration` |
| Просить придумать недостающую логику | Это нарушает FT-first подход | Фиксировать `coverage gaps` |
| Использовать историю чата как единственный контекст | Контекст теряется между сессиями | Работать через handoff-файлы |

## 19. Кратко о Python API

В проекте есть легкий Python-пакет `test_case_agent`. Он помогает читать и сужать большие DOCX/PDF требования до нужных разделов.

Основные функции:

| API | Назначение |
|---|---|
| `load_sections(source)` | Получить разделы и метаданные по документу |
| `resolve_sections(source, section_prefix=None, max_sections=None)` | Выбрать релевантные разделы |
| `preview_chunks(source, section_prefix=None, max_sections=None, max_chars=12000)` | Получить чанки для просмотра большого scope |
| `inspect_source_quality(source, max_chars=12000)` | Проверить качество извлечения структуры и chunking перед downstream QA-работой |

Пример:

```python
from pathlib import Path

from test_case_agent import load_sections, preview_chunks, resolve_sections

source = Path("fts/<ft-slug>/source/<main-ft>.docx")

sections = resolve_sections(source, section_prefix="2.2.3")
chunks = preview_chunks(source, section_prefix="2.2.3", max_chars=12000)
all_sections = load_sections(source)
```

Python API помогает с техническим чтением документов, но не заменяет QA-суждение, scope contract и review-cycle.

## 20. Минимальный checklist перед запуском этапа

Перед запуском любого этапа проверь:

- выбран ли правильный FT-пакет;
- есть ли `AGENT-NOTES.md` и нужно ли его учитывать;
- определен ли `scope-slug`;
- есть ли `workflow-state.yaml`;
- есть ли входные артефакты из `required_inputs`;
- есть ли `scope-clarification-requests.md` и подтвержденные ответы, если writer или reviewer на них ссылается;
- есть ли XLSX companion для traceability matrix, если используется `round-N-traceability-matrix.md`;
- не расширяет ли запрос scope без явного решения;
- не требует ли запрос поведения, которого нет в ФТ;
- соответствует ли выбранный skill текущей фазе.

## 21. Быстрый выбор режима

| Если нужно | Используй |
|---|---|
| Найти нужный FT-пакет | `ft-source-locator` |
| Разбить большое ФТ на варианты scope | `ft-scope-analyzer` + `agent-proposed-scope` |
| Подтвердить конкретный раздел или блок | `ft-scope-analyzer` + `manual-scope` |
| Написать кейсы без review-cycle | `ft-test-case-writer` |
| Проверить существующие кейсы | `ft-test-case-reviewer` |
| Получить production-ready набор с review | `ft-test-case-iteration` |
| Проверить signed-off кейсы в UI | `ft-ui-automation-prep` |
| Проверить архитектуру агентного слоя | `agent-architecture-auditor` |

## 22. Ключевое правило

Если задача идет не с нуля, агент должен восстанавливать состояние из файлов, а не из памяти чата:

```text
workflow-state.yaml
source-selection.md
scope-contract.md
source-parity-check.md
scope-coverage-gaps.md
scope-clarification-requests.md
prompt.*.md
round-N-findings.md
round-N-traceability-matrix.md
round-N-traceability-matrix.xlsx
round-N-writer-response.md
cycle-state.yaml
ui-validation-report.md
ui-evidence-index.md
```

Если этих файлов недостаточно, сначала нужно восстановить или дозаполнить handoff, а уже затем запускать следующий этап.
