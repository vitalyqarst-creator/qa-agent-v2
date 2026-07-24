# Формат `scope-execution-options.md`

Этот документ задает канонический формат для `scope-execution-options.md`.

`scope-execution-options.md` — optional helper artifact после подтверждения scope и source-first review. Он помогает пользователю выбрать следующий маршрут выполнения, но не заменяет `workflow-state.yaml`, `scope-contract.md`, `prompt.scope-assertions-to-reviewer.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.

## Когда создавать

- только после подтвержденного scope;
- после создания `scope-contract.md`, `scope-coverage-gaps.md` и accepted `source_assertion_review` для production/promotion-capable workflow;
- только как user-facing helper, а не как обязательный downstream-вход.

## Где хранить

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-execution-options.md` для новых handoff-папок

## Обязательные секции

- `## Контекст`
- `## Подтвержденные Входы`
- `## Рекомендуемый Следующий Шаг`
- `## Вариант 1. Запуск Через Iteration`
- `## Вариант 2. Ручной Loop Через Writer И Reviewer`
- `## Обязательные Guardrails`
- `## Ожидаемые Выходы По Выбранному Пути`
- `## Что Этот Файл Не Делает`

## Правила формата

- файл относится к одному подтвержденному `scope_slug`;
- файл не меняет process-status и не подтверждает scope повторно;
- файл не является обязательным входом для writer, reviewer или iteration;
- `ft-test-case-iteration` должен быть указан как рекомендуемый путь по умолчанию;
- ручной `writer -> reviewer` loop должен быть описан как допустимая альтернатива;
- prompt-блоки должны быть готовы к копированию пользователем в новую сессию.

## Минимальный шаблон

````md
# Execution Options For `<scope-slug>`

## Контекст

- FT-пакет: `fts/<ft-slug>`
- `scope_slug`: `<scope-slug>`
- Рабочее название scope: `...`
- Основной FT: `...`
- Статус scope: `confirmed`
- Канонический handoff-state: `work/stage-handoffs/NN-<scope-slug>/workflow-state.yaml`

## Подтвержденные Входы

- `scope-contract.md`
- `scope-coverage-gaps.md`
- `prompt.scope-to-writer.md`
- `prompt.scope-to-iteration.md`
- `workflow-state.yaml`

## Рекомендуемый Следующий Шаг

`ft-test-case-iteration`

Почему рекомендуется:
- проходит полный writer/reviewer loop;
- снижает ручную оркестрацию;
- лучше подходит для доведения набора до `signed-off` или `round-cap-reached`.

## Вариант 1. Запуск Через Iteration

Когда использовать:
- нужен полный цикл;
- не требуется вручную управлять каждым этапом;
- цель — получить финальный status по scope.

Готовый prompt:
```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-test-case-iteration`
Scope: `<scope-slug>`
Входы: использовать `scope-contract.md`, `scope-coverage-gaps.md`, `prompt.scope-to-iteration.md`, `workflow-state.yaml` и связанные материалы FT-пакета
Задача: пройти полный writer/reviewer loop для этого scope
Выходы: канонический набор тест-кейсов, session-based cycle artifacts under `work/review-cycles/<scope-slug>/`, terminal `cycle-state.yaml`, snapshots
Ограничения: не расширять scope
```

## Вариант 2. Ручной Loop Через Writer И Reviewer

Когда использовать:
- нужен ручной контроль каждого этапа;
- нужно отдельно остановиться после draft или после review;
- пользователь хочет сам решать, когда запускать revision.

Последовательность:
1. `ft-test-case-writer`
2. `ft-test-case-reviewer`
3. при findings: снова `ft-test-case-writer`
4. затем снова `ft-test-case-reviewer`

### Prompt Для Initial Writer Run

```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-test-case-writer`
Scope: `<scope-slug>`
Входы: использовать `scope-contract.md`, `scope-coverage-gaps.md`, `prompt.scope-to-writer.md`, `workflow-state.yaml` и связанные материалы FT-пакета
Режим: `initial_draft`
Задача: подготовить initial draft тест-кейсов по подтвержденному scope
Выходы: канонический файл тест-кейсов, snapshot initial draft, `prompt.writer-to-reviewer.round-1.md`, обновленный `workflow-state.yaml`
Ограничения: не расширять scope
```

### Prompt Для First Review

```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-test-case-reviewer`
Scope: `<scope-slug>`
Входы: использовать канонический файл тест-кейсов, `scope-contract.md`, `workflow-state.yaml`, `prompt.writer-to-reviewer.round-1.md` и основной FT
Режим review: `full`
Задача: провести review initial draft тест-кейсов
Выходы: `round-1-findings.md`, `round-1-traceability-matrix.md` при необходимости, `prompt.reviewer-to-writer.round-1.md` или `prompt.reviewer-to-ui-prep.md`, обновленный `workflow-state.yaml`
Ограничения: не исправлять тест-кейсы, не расширять scope
```

## Обязательные Guardrails

- Не запускать две сессии на один и тот же `scope-slug`.
- Не расширять scope за пределы `scope-contract.md`.
- Не использовать этот файл как замену `workflow-state.yaml`.
- Не использовать этот файл как замену `prompt.scope-to-writer.md`.
- Не использовать этот файл как замену `prompt.scope-to-iteration.md`.
- Не писать тест-кейсы до появления обязательных handoff-артефактов.

## Ожидаемые Выходы По Выбранному Пути

Если выбран `ft-test-case-iteration`:
- `test-cases/<section-id>-<scope-slug>.md`
- `work/review-cycles/<scope-slug>/cycle-state.yaml`
- `work/review-cycles/<scope-slug>/outputs/*`
- `work/review-cycles/<scope-slug>/versions/*/snapshot-manifest.yaml`
- обновленный `workflow-state.yaml`

Если выбран ручной loop:
- после writer: `test-cases/<section-id>-<scope-slug>.md`, `prompt.writer-to-reviewer.round-1.md`
- после reviewer: `round-1-findings.md`, при необходимости `round-1-traceability-matrix.md`, следующий prompt-файл

## Что Этот Файл Не Делает

- не меняет process-status;
- не подтверждает scope повторно;
- не заменяет `scope-contract.md`;
- не заменяет `scope-coverage-gaps.md`;
- не заменяет `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`;
- не является обязательным входом для writer или reviewer.
````
