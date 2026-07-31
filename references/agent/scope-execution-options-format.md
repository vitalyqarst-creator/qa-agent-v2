# Формат `scope-execution-options.md`

Этот документ задает канонический формат для `scope-execution-options.md`.

`scope-execution-options.md` — optional helper artifact после подтверждения scope, если есть реальный выбор маршрута. Он помогает пользователю выбрать следующий маршрут выполнения, но не заменяет `workflow-state.yaml`, `scope-contract.md`, `prompt.scope-to-writer.md`, `prompt.scope-to-iteration.md` или strict `prompt.scope-assertions-to-reviewer.md`.

## Когда создавать

- только после подтвержденного scope;
- после создания `scope-contract.md`, `scope-coverage-gaps.md` и active writer-ready handoff;
- только как user-facing helper, а не как обязательный downstream-вход.

## Где хранить

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-execution-options.md` для новых handoff-папок

## Обязательные секции

- `## Контекст`
- `## Подтвержденные Входы`
- `## Рекомендуемый Следующий Шаг`
- `## Вариант 1. Practical Writer/Reviewer Loop`
- `## Вариант 2. Strict Iteration`
- `## Обязательные Guardrails`
- `## Ожидаемые Выходы По Выбранному Пути`
- `## Что Этот Файл Не Делает`

## Правила формата

- файл относится к одному подтвержденному `scope_slug`;
- файл не меняет process-status и не подтверждает scope повторно;
- файл не является обязательным входом для writer, reviewer или iteration;
- `ft-test-case-writer` -> `ft-test-case-reviewer` должен быть указан как рекомендуемый путь по умолчанию;
- strict `ft-test-case-iteration` должен быть описан как opt-in альтернатива только при явном запросе;
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

`ft-test-case-writer` -> `ft-test-case-reviewer`

Почему рекомендуется:
- быстрее доводит scope до написанных тест-кейсов;
- оставляет unresolved UI/data/source issues видимыми в самих TC;
- избегает pre-writer repair loop вокруг strict source-contract artifacts.

## Вариант 1. Practical Writer/Reviewer Loop

Когда использовать:
- нужно получить итоговые тест-кейсы;
- допустимы честные пометки `candidate-ui-calibration`, `blocked-observability`, `needs-test-data`;
- strict source-contract qualification не является целью.

Готовый prompt:
```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-test-case-writer`
Scope: `<scope-slug>`
Входы: использовать `scope-contract.md`, `scope-coverage-gaps.md`, `prompt.scope-to-writer.md`, `workflow-state.yaml` и связанные материалы FT-пакета
Задача: написать тест-кейсы для этого scope и подготовить handoff на independent review
Выходы: канонический набор тест-кейсов, writer artifacts, `prompt.writer-to-reviewer.round-1.md`
Ограничения: не расширять scope
```

## Вариант 2. Strict Iteration

Когда использовать:
- пользователь явно попросил source-qualified shadow / qualification;
- есть accepted exact-digest source assertion review;
- цель — проверить strict route, а не просто получить тест-кейсы.

Готовый prompt:

```md
FT-пакет: `fts/<ft-slug>`
Этап: `ft-test-case-iteration`
Scope: `<scope-slug>`
Входы: использовать accepted exact-digest source assertion review, `run-config.json`, `prompt.scope-to-iteration.md`
Задача: выполнить один strict immutable source-qualified writer/reviewer attempt
Выходы: immutable attempt directory, terminal summary, shadow suite или explicit terminal blocker
Ограничения: не запускать bridge/benchmark/sharding, не использовать старые failed attempts как input
```

## Обязательные Guardrails

- Не запускать две сессии на один и тот же `scope-slug`.
- Не расширять scope за пределы `scope-contract.md`.
- Не использовать этот файл как замену `workflow-state.yaml`.
- Не использовать этот файл как замену `prompt.scope-to-writer.md`.
- Не использовать этот файл как замену `prompt.scope-to-iteration.md`.
- Не писать тест-кейсы до появления обязательных handoff-артефактов.

## Ожидаемые Выходы По Выбранному Пути

Если выбран practical writer/reviewer loop:
- после writer: `test-cases/<section-id>-<scope-slug>.md`, `prompt.writer-to-reviewer.round-1.md`
- после reviewer: `round-1-findings.md`, при необходимости `round-1-traceability-matrix.md`, следующий prompt-файл

Если выбран strict `ft-test-case-iteration`:
- `test-cases/<section-id>-<scope-slug>.md`
- `work/iterations/<attempt-id>/*`
- terminal summary and reviewer receipt when reached

## Что Этот Файл Не Делает

- не меняет process-status;
- не подтверждает scope повторно;
- не заменяет `scope-contract.md`;
- не заменяет `scope-coverage-gaps.md`;
- не заменяет `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`;
- не является обязательным входом для writer или reviewer.
````
