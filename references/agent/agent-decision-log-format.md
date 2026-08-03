# Agent Decision Log Format

`agent-decision-log.md` - постоянный audit artifact для промежуточных решений агента внутри стадии. Он дополняет `*session-log*.md`: session log дает сводку стадии, а decision log фиксирует последовательность наблюдаемых решений, которые повлияли на scope, покрытие, формат, маршрутизацию или качество результата.

## Назначение

Decision log нужен, чтобы следующая сессия или reviewer мог восстановить путь от входов к результату без истории чата и без скрытых рассуждений агента.

Логируй только наблюдаемые действия и решения:

- выбор source/scope/package boundary;
- принятую или отклоненную трактовку неоднозначного требования;
- классификацию строки источника как `standalone_tc`, `gap_unclear`, `metadata_only`, `out_of_scope` и другие решения, если они влияют на покрытие;
- решение не использовать соседний package, старый baseline или mockup-only поведение;
- техническое решение, меняющее способ записи или проверки artifact;
- routing decision: reviewer, writer revision, blocked-input, round-cap, UI prep;
- исправление после self-check, validator или reviewer finding.

Не логируй:

- скрытые chain-of-thought рассуждения;
- полный transcript команд;
- каждую мелкую правку текста;
- длинные выдержки из ФТ;
- секреты, токены, private credentials.

## Расположение

Храни decision log в текущей stage-handoff папке:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/agent-decision-log.md
```

Для session-based review cycle связывай активный decision log из `cycle-state.yaml` или совместимого `workflow-state.yaml` текущего scope. Если нужен stage-specific файл, используй имя вида `agent-decision-log.semantic-review-r1.md` и явно укажи его в `latest_artifacts.decision_log`.

## Workflow Link

`workflow-state.yaml` должен ссылаться на decision log:

```yaml
required_inputs:
  - work/stage-handoffs/NN-<scope-slug>/agent-decision-log.md
latest_artifacts:
  decision_log: work/stage-handoffs/NN-<scope-slug>/agent-decision-log.md
```

Для новых clean/eval runs проверяй наличие и формат:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --decision-log-policy strict
```

## Required Format

Используй точные заголовки и колонки:

```md
# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `<ft-slug>` |
| scope_slug | `<scope-slug>` |
| stage | `ft-test-case-writer` |
| started_from | `workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Использовать только раздел 2.3 | Scope подтвержден, соседние разделы не являются источником | `test-cases/2.3-ui.md` | high | applied |
```

## Column Rules

- `decision_id` - стабильный ID вида `DEC-001` или `DL-001`.
- `step` - порядок появления решения внутри стадии.
- `decision_type` - короткий тип: `source-boundary`, `scope-boundary`, `coverage`, `test-design`, `gap`, `artifact-write`, `validation`, `routing`, `fallback`.
- `input_or_trigger` - файл, finding, validator result, пользовательское уточнение или технический триггер.
- `decision` - что агент решил сделать или не делать.
- `rationale` - проверяемая причина без скрытого chain-of-thought.
- `artifact_or_output` - куда решение попало: test-case file, gap, matrix, prompt, workflow-state.
- `risk_or_confidence` - `high`, `medium`, `low`, `risk:<...>` или конкретный caveat.
- `status` - `applied`, `rejected`, `deferred`, `superseded`, `blocked`.

## Relationship To Other Artifacts

- `session-log.md` может кратко суммировать `Key Decisions`, но не заменяет `agent-decision-log.md`.
- `coverage gaps` должны ссылаться на source statements; decision log объясняет, почему агент оставил или снял gap.
- `writer-quality-gate.md` и `test-design-review.md` фиксируют pass/fail checks; decision log фиксирует решения, принятые по результатам этих checks.
- `workflow-state.yaml` остается единственным источником process-status; decision log не должен противоречить `current_stage`, `stage_status`, `next_skill` и `latest_artifacts`.
