# Как работать с FT Test Case Agent

Эта инструкция нужна, чтобы агент работал предсказуемо, без лишних уточнений и без потери контекста между этапами.

Это быстрый reference по формату запросов. Полный пользовательский справочник хранится в [user-manual.md](user-manual.md) как редактируемый источник и выпускается для чтения в DOCX/PDF: `output/doc/ft-test-case-agent-user-manual.docx` и `output/pdf/ft-test-case-agent-user-manual.pdf`.

Перед запуском UI-прогонов или локального Python API проверь раздел `Что должно быть установлено или доступно` в полном справочнике: там перечислены Python, зависимости проекта, Playwright CLI, runtime-доступ к приложению и инструменты для сопровождения DOCX/PDF.

## Что писать в первом сообщении

Дай агенту ровно те данные, которые влияют на выбор skill-а и границы задачи:

- какой FT-пакет нужен, если он уже известен;
- какой этап нужен:
  - `ft-source-locator`
  - `ft-scope-analyzer`
  - `ft-test-case-writer`
  - `ft-test-case-reviewer`
  - `ft-test-case-iteration`
  - `ft-ui-automation-prep`
- какой scope нужен: раздел, подраздел, поле, блок, сценарий;
- что должно быть результатом:
  - новые тест-кейсы;
  - review существующих кейсов;
  - writer/reviewer iteration;
  - automation-ready версия;
  - аудит agent-layer;
- ограничения:
  - не расширять scope;
  - работать только по тексту ФТ;
  - сохранить существующий файл;
  - подготовить артефакты handoff.

## Шаг 1. Выбери режим работы со scope

Перед запуском `ft-scope-analyzer` пользователь должен выбрать один из двух режимов:

- `manual-scope` — пользователь сам задает границы scope;
- `agent-proposed-scope` — агент сначала предлагает подходящее разбиение FT на candidate scope.

Это разные сценарии. Не смешивай их в одном запросе.

## Предпочтительный формат запроса

Используй короткий структурированный запрос:

```md
FT-пакет: `fts/<ft-slug>/...` или описание пакета
Этап: `ft-...`
Режим scope: `manual-scope` | `agent-proposed-scope`
Scope: раздел / блок / поле / сценарий
Задача: что нужно сделать
Результат: какой артефакт нужен на выходе
Ограничения: что нельзя делать
```

## Что помогает агенту работать лучше всего

- Указывай точный `ft-slug`, если он уже известен.
- Указывай точный `scope-slug`, если он уже существует.
- Если нужен следующий этап pipeline, ссылайся на `workflow-state.yaml` и prompt-файл из фактической handoff-папки `work/stage-handoffs/NN-<scope-slug>/` для новых scope-ов.
- Если нужен revision, давай путь к:
  - каноническому набору `test-cases/<section-id>-<scope-slug>.md`;
  - `round-N-findings.md`;
  - `round-N-traceability-matrix.md`, если есть;
  - `round-N-writer-response.md`, если это второй review.
- Если нужен review, явно пиши `review_mode`, если он должен быть не `full`.
- Если есть package-specific контекст, указывай на `AGENT-NOTES.md` или `UI-AGENT-NOTES.md`.

## Как выбирать режим scope

### `manual-scope`

Используй, когда границы уже известны и их не нужно проектировать заново.

Пользователь должен дать:

- основной FT;
- дополнительные документы;
- точную границу scope:
  - раздел;
  - подраздел;
  - блок;
  - поле;
  - сценарий;
- ограничение, что scope нельзя расширять.

На выходе ожидается:

- один подтвержденный scope;
- `scope-contract.md` по каноническому формату;
- `scope-coverage-gaps.md` по каноническому формату;
- `prompt.scope-to-writer.md`;
- при необходимости `scope-execution-options.md` как подсказка по следующему запуску;
- обновленный `workflow-state.yaml`.

### `agent-proposed-scope`

Используй, когда FT большой или пользователь не уверен, как его лучше разбить.

Пользователь должен дать:

- основной FT;
- дополнительные документы;
- цель разбиения:
  - полный разбор;
  - поэтапное покрытие;
  - приоритизация;
- при необходимости ограничения по гранулярности.

На выходе ожидается:

- список candidate scope;
- краткие границы каждого scope;
- рекомендация, с какого scope начать;
- отдельный артефакт `scope-options.md`;
- отдельный артефакт `scope-selection-prompts.md` с готовыми prompt-шаблонами для подтверждения одного scope.

После `agent-proposed-scope` нельзя сразу переходить к writer. Сначала пользователь должен утвердить один конкретный scope.
Для этого пользователь должен взять один из prompt-шаблонов из `scope-selection-prompts.md`.

## Как формулировать задачу по этапам

### 1. Найти FT-пакет

Используй, когда не знаешь, с каким пакетом работать.

Пример:

```md
Найди FT-пакет для требований по расчету ПДН и подготовь handoff к scope analysis.
Если выбор неоднозначен, перечисли кандидатов и чего не хватает для точного выбора.
```

### 2. Выделить scope

Используй, когда FT-пакет уже известен, но границы работы еще не зафиксированы.

Пример:

```md
Режим scope: `manual-scope`
Для `fts/<ft-slug>` выдели scope по разделу `<section-id>`.
Нужны `scope-contract.md`, `scope-coverage-gaps.md` и handoff к writer.
Используй канонические форматы `scope-contract-format.md` и `scope-coverage-gaps-format.md`.
```

Пример для `agent-proposed-scope`:

```md
Режим scope: `agent-proposed-scope`
Для `fts/<ft-slug>` предложи разбиение FT на candidate scope для дальнейшего написания тест-кейсов.
Нужен список scope с краткими границами и рекомендацией, с какого начать.
```

### 3. Написать тест-кейсы

Используй, когда scope уже подтвержден.

Пример:

```md
Для scope `2.1.1.1.1.1.2-lichnaya-informaciya` подготовь initial draft тест-кейсов.
Работай только в границах `scope-contract.md`.
На выходе нужен канонический файл и handoff к reviewer.
```

### 4. Сделать review

Используй, когда набор тест-кейсов уже существует и нужен контроль покрытия или структуры.

Пример:

```md
Проведи review набора `fts/.../test-cases/<section-id>-<scope-slug>.md`.
Режим: `full`.
Не исправляй кейсы, верни findings, traceability matrix и handoff к writer при необходимости.
```

### 5. Запустить iteration

Используй, когда нужен полный writer/reviewer loop до `signed-off` или `round-cap-reached`.

Пример:

```md
Запусти `ft-test-case-iteration` для scope `<scope-slug>`.
Нужен полный цикл с обновлением `workflow-state.yaml` и всех handoff-артефактов.
```

### 6. Подготовить automation-ready

Используй только после `signed-off`.

Пример:

```md
Для scope `<scope-slug>` выполни `ft-ui-automation-prep`.
Проверь, что в `workflow-state.yaml` следующий этап — `ft-ui-automation-prep`.
Если есть `UI-AGENT-NOTES.md`, используй его.
```

## Как давать корректировки

Если нужно исправить уже сделанный результат, привязывай замечание к конкретному артефакту:

- `test_case_id`;
- `finding_id`;
- `scope-contract.md`;
- `cycle-state.yaml`;
- `workflow-state.yaml`;
- конкретному файлу в `work/stage-handoffs/` или `work/review-cycles/`.

Хороший формат:

```md
Исправь `FINDING-003`.
Scope не расширяй.
Нужен только revision существующего набора и обновление handoff к reviewer.
```

## Что ухудшает результат

- запрос вида «посмотри все и сделай правильно» без указания этапа;
- смешивание нескольких FT-пакетов в одной задаче;
- смешивание нескольких независимых scope в одном наборе тест-кейсов;
- просьба придумать поведение, которого нет в ФТ;
- запуск `ft-ui-automation-prep` до `signed-off`;
- отсутствие ссылки на текущие артефакты, если работа идет не с нуля.

## Минимальный шаблон для оптимальной работы

```md
FT-пакет: `fts/<ft-slug>/...`
Этап: `ft-...`
Режим scope: `manual-scope` | `agent-proposed-scope`
Scope: `<scope-slug>` или точный раздел ФТ
Входы: какие файлы использовать
Задача: что сделать
Выходы: какие файлы или артефакты нужны
Ограничения: что не менять и что не додумывать
```

## Практическое правило

Если задача идет не с нуля, считай историю чата вторичной. Основной контекст должен быть восстановим из файлов:

- `work/stage-handoffs/NN-<scope-slug>/workflow-state.yaml`
- `work/stage-handoffs/NN-<scope-slug>/prompt.*.md`
- `work/stage-handoffs/NN-<scope-slug>/scope-contract.md`
- `work/stage-handoffs/NN-<scope-slug>/scope-coverage-gaps.md`
- `work/stage-handoffs/NN-<scope-slug>/scope-execution-options.md`, если нужен быстрый user-facing выбор между `iteration` и ручным loop
- `work/review-cycles/<scope-slug>/cycle-state.yaml`
- `work/review-cycles/<scope-slug>/outputs/*`
- `work/review-cycles/<scope-slug>/versions/*/snapshot-manifest.yaml`

Если этих файлов недостаточно, лучше сначала попросить агента восстановить или дозаполнить handoff-артефакты, а потом запускать следующий этап.
