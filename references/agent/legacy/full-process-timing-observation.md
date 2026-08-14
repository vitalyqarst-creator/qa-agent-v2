# Наблюдательное измерение полного времени задачи

Этот профиль нужен для получения фактического baseline текущего процесса от
пользовательского запроса до завершения ответа Codex. Он только измеряет работу:
не задаёт target, warning threshold, hard stop или общий timeout и не меняет
quality gates. Scope analyzer в этом профиле запускается с его явной политикой
`measurement_mode = observational`, то есть без 120/150-секундного cutoff;
его capability probe также выполняется без отдельного 15-секундного budget.
Standard wrapper обязан передать observational mode downstream: source reviewer,
structured writer и reviewer не получают application-level hard/idle timeout;
bounded cleanup после terminal result остаётся допустим. Measurement layer не
добавляет новых ограничений.

## Две границы времени

Один timestamp внутри ответа не может доказать полное пользовательское время:
момент `task_complete` появляется только после отправки final. Поэтому используются
две связанные величины:

1. `observed_window_ms` — от точного старта root-turn до
   `pre-final-response`, зафиксированного последним инструментальным действием
   перед final;
2. `full_user_wall_ms` — длительность Codex `task_complete` или значение UI,
   добавленное после завершения turn.

До внешней сверки `full_user_wall_ms = null`, а
`claimable_as_full_user_wall = false`. Сумму model durations и сумму фаз нельзя
называть полным временем пользователя.

## Старт следующего тестового запуска

До executor primary root-agent выполняет ограниченный pre-bootstrap preflight:
объявляет routing, читает `AGENTS.md`, выбранный `SKILL.md`, checked-in launch и
сохранённый environment probe. До metadata запрещены прочие tool/model calls,
source discovery, старые результаты, запись и `--validate-only`. Затем один и тот
же root-agent выполняет атомарную пару metadata-bootstrap: получает `turn_id` и
`turn_started_at_unix_ms`, а следующим task action запускает schema-v2 bootstrap.
Timer открывается задним числом от metadata timestamp, поэтому preflight входит в
`routing-preflight`.

Для воспроизводимого чтения metadata вызови Node REPL tool именно из root-turn
(не из subagent) и импортируй подготовленный helper:

```javascript
var timingMetadataModule = await import("./scripts/read_codex_turn_metadata.mjs");
nodeRepl.write(JSON.stringify(timingMetadataModule.readCodexTurnMetadata()));
```

Helper fail-closed проверяет `thread_source = user`, `turn_id` и настоящий
`turn_started_at_unix_ms`; только после этого допустима `precision_ms = 1`.
Rollout timestamp секундной точности не заменяет этот anchor.

При наличии checked-in config сразу после metadata используй bootstrap:

```powershell
.\.venv\Scripts\python.exe scripts\start_full_process_observation.py `
  --config <bootstrap-config.json> `
  --request-started-epoch-ms <turn_started_at_unix_ms> `
  --codex-turn-id <turn_id> `
  --execute
```

Schema-v2 `--execute` проверяет package/source hashes и entrypoints, готовит
bounded context, выполняет dependency preflight и вызывает production wrapper
ровно один раз. `bootstrap-receipt.json` задаёт пути и source registry; его
`path`/`role`/`manifest_binding` не заменяются эвристикой. Config schema v1 остаётся start-only;
ручной запуск `workflow_wall_clock.py start` также допустим только как fallback
при отсутствии checked-in schema-v2 config. Без Codex metadata окно маркируется
`timer-start-to-pre-final-response` и не считается полным request-to-final.
Точное `task_complete` добавляется только post-turn reconciliation.

### Запуск из созданной контроллером Codex-задачи

Созданная контроллером задача получает `thread_source = subagent`. Для явно
порученного пользователем автозапуска checked-in launch должен одним Node REPL
call вызвать `scripts/read_codex_controller_turn_metadata.mjs`, затем без
промежуточных действий запустить schema-v2 executor с
`--request-start-source controller-job-start`. Helper проверяет metadata
fail-closed; user-turn helper и ручная проверка полей запрещены. Такой замер имеет
те же quality gates, но request-to-final reconciliation — `not-applicable`.

## Этапы текущего процесса

Для production route фиксируются следующие верхнеуровневые фазы:

| phase | Начало | Конец | Основные дополнительные метрики |
| --- | --- | --- | --- |
| `routing-preflight` | получение запроса | выбран маршрут и прочитаны обязательные инструкции | прочитанные instruction files |
| `source-selection` | начало поиска FT-пакета | main/support/mockup inputs зафиксированы | число и байты выбранных inputs |
| `source-preparation` | старт подготовки bounded context | cache/dependency result сохранён | input/output files и bytes, cache hit |
| `scope-analysis` | запуск boundary workflow | authoritative boundary или terminal failure сохранён | context/schema/mockup bytes, tokens, outcome |
| `semantic-design` | boundary зафиксирован | semantic design и bridge validation result сохранены | boundary/design bytes, assertions/atoms/obligations, tokens, outcome |
| `scope-materialization` | начало deterministic materialization | handoff готов либо отклонён | input/output inventory, assertions/atoms/obligations |
| `source-review` | source gate/reviewer start | independent receipt принят либо отклонён | input/output inventory, tokens, outcome |
| `compile-preflight` | compiler start | prepared package result | input/output inventory, cache hit, obligations/gaps |
| `writer-reviewer` | writer-reviewer runner start | accepted/blocked result | отдельные writer/reviewer stage metrics |
| `promotion` | promotion start | publication/terminal result | promotion breakdown, input/output inventory |
| `final-reporting` | downstream terminal result известен | ответ полностью подготовлен, перед отправкой final | итоговый artifact inventory и TC count |

Каждый observation обязан явно классифицировать `source-preparation` как
`cold-cache`, `warm-cache` или `cache-status-unavailable` по фактическому
`cache_hit`. Warm-cache результат допустим и полезен для повторного production
маршрута, но не может называться временем первичного извлечения или cold run.

`routing-preflight` обязательно раскладывается на компоненты
`request-metadata-read`, `instruction-loading`, `environment-probe`,
`workspace-check`, `ft-config-selection`, `source-registry-check`,
`hash-verification`, `command-preparation`, `external-backend-wait` и
`other-orchestration`. Неизмеренный компонент имеет значение `unavailable`, а не
ноль. Если отдельные компоненты измерены, `other-orchestration` может быть
рассчитана как неотрицательный residual до полного wall этой фазы.

Дополнительная работа получает собственную фазу из реестра:
`diagnostics-recovery`, `code-remediation`, `offline-verification`,
`retry-backoff`, `cycle-preparation`, `cross-scope-evaluation`,
`incremental-update`, `final-reconciliation`. Эти фазы условны: их отсутствие в
чистом production-run не является missing-phase finding.

В `standard-production` фаза `scope-analysis` содержит один boundary-v2
model call, а `semantic-design` — один author model call либо последовательные
bounded author shards и их deterministic merge. Shard только из authoritative
`context`/`excluded` строк материализуется без model call и учитывается отдельно
от model attempts. Нельзя склеивать фазы, автоматически повторять или заменять
их fallback-маршрутом. Failure model call завершает маршрут до materialization.

Каждый фактически запущенный model-stage сохраняет wall time, число попыток,
input/cached/output/total tokens, reasoning tokens, а также число и байты
входных/выходных артефактов. Недоступная метрика записывается как `unavailable`.
Это же правило действует для root Codex-agent: недоступные tokens нельзя
подменять нулём. Внутренние `metrics.json` writer и reviewer подключаются в отчет
как model-stage detail.
Общий `writer-reviewer` wall остаётся отдельным: разность между ним и model-stage
durations показывает deterministic gates, state updates и orchestration overhead.

Если возникает дополнительная работа, она не скрывается внутри ближайшей фазы.
Создаётся явно названная фаза, например `diagnostics-recovery` или
`offline-verification`. В чистом baseline нельзя выполнять разработку или
оптимизацию кода; обнаруженный дефект фиксируется как фактический terminal result.

Сверка времени обязана быть машинно проверяемой:

```text
observed_window_ms
= phase_sum_ms - explicit_interphase_overlap_ms + unattributed_ms
```

Здесь `unattributed_ms` — явно опубликованные интервалы до первой, между или
после фаз. Для непрерывного измерения он равен нулю, и равенство сводится к сумме
фаз минус пересечения. Отчёт публикует `reconciliation_delta_ms`; отличное от
нуля значение является дефектом измерения, а не временем backend.

## Переходы и объём артефактов

Для последовательных фаз используй одну атомарную границу:

```powershell
.\.venv\Scripts\python.exe scripts\workflow_wall_clock.py transition `
  --output <timer> `
  --phase source-selection `
  --status completed `
  --next-phase source-preparation `
  --metrics-json <optional-stage-summary.json> `
  --input-artifact-root <source-selection-input> `
  --output-artifact-root <source-selection-receipt> `
  --next-input-artifact-root <selected-source-file>
```

Передавай точные файлы или bounded directories, а не весь репозиторий. Один файл,
попавший в inputs нескольких стадий, учитывается в каждой стадии: это объём
контекста стадии, а не размер уникальных файлов всего run.

Для полного `standard-production` запуска bridge и downstream одной командой
используй `scripts/run_standard_production_iteration.py`; он сохраняет раздельные
фазы `scope-analysis`, `semantic-design`, `scope-materialization`, а затем
передаёт тот же caller-owned timer downstream runner-у. Узкий downstream runner
ниже используется самостоятельно только когда atomic handoff уже существует:

Outer wrapper принимает post-commit recovery только из receipt с ownership-token
текущего invocation. Если bridge summary отсутствует или не читается, модельные
`attempt_count` / `retry_count` восстанавливаются только из свежих stage summaries
или фаз того же timer. При неполном evidence оба значения равны `null`, а
`lifecycle_count_evidence.status = unknown`; `0` допустим только как доказанное
отсутствие попыток. Это правило сохраняет факт успешной atomic publication, но не
подменяет неизвестную часть измерения ложным нулём.

В summary полного `standard-production` route верхнеуровневые `attempt_count` и
`retry_count` являются кумулятивными: они включают boundary, semantic author,
source reviewer, writer и reviewer, фактически выполненные до terminal result.
Bridge и downstream дополнительно публикуются раздельно как
`bridge_attempt_count` / `bridge_retry_count` и
`downstream_attempt_count` / `downstream_retry_count`, каждый со своим
`*_lifecycle_count_evidence`. Writer/reviewer считаются по уникальной тройке
`stage_id + attempt_id + role`; повтор того же `stage_metrics` в timer и
performance payload не является новой попыткой. Downstream evidence принимается
только из свежих фаз caller-owned timer и связанных current-run summaries. Если
хотя бы один выполненный model component не подтвержден, именно общий счетчик
становится `null` и общий provenance — `unknown`; известные component counters при
этом сохраняются для диагностики. Успешный обычный проход с одной попыткой на
каждой из пяти модельных стадий поэтому имеет `attempt_count = 5`, а не `2`.

Перед downstream outer wrapper снимет точный snapshot уже существующих timer
phases и `cycle_dir/attempts/*/*/metrics.json`. После выполнения учитываются только
append-only phases и новые immutable metric identities; старые записи из reused
cycle игнорируются, а перезапись, конфликт identity/content, неизвестная role или
несогласованный `role/stage_id` переводят aggregate в `unknown`. Stale-only
`stage_metrics` не доказывает текущую попытку. Нулевой writer/reviewer count
разрешён только при явном current-phase reuse receipt с нулевыми counts.
Payload identity дополнительно обязан совпадать с filesystem-путём
`attempts/<stage_id>/<attempt_id>/metrics.json`. Для source-review действует та же
pre/post модель: executed count требует fresh summary и exact-equal timer payload;
reuse=0 допустим только при неизменном summary snapshot. Fresh/overwritten summary
вместе с reuse claim является конфликтом и даёт `unknown`.

Любая lifecycle-пара обязана соблюдать `0 <= retry_count <= attempt_count`;
нарушение переводит component и общий total в `unknown`. Для legacy
single-session source-review действует семантика
`retry_count = max(0, attempt_count - 1)`. Bounded-sharded source-review вместо
этого обязан публиковать exact `review_shard_count = model_session_count =
attempt_count` и `retry_count = 0`: каждый shard является fresh complete/disjoint
attempt, а не retry. Fresh executed count принимается только для согласованных
`phase.status = completed`, `summary.status = completed` и `attempt_count >= 1`.
Failed count требует явного complete-attempt evidence; fresh `status = reused` не
может выдать executed zero. Canonical writer/reviewer
`attempt_id` имеет вид `attempt-001` ... `attempt-999`; `attempt-000` не является
доказательством попытки.

Lean downstream при доказанном повторном использовании source-review не
перезаписывает persisted summary. В current timer phase он публикует отдельный
versioned reuse receipt с exact `attempt_count = 0`, `retry_count = 0` и digest/path
evidence исходного review receipt и persisted summary. Старый persisted summary не
может сам играть роль current-run receipt. Удаление preexisting writer/reviewer
metric так же нарушает append-only evidence, как его перезапись.

Путь source-assertion review для reuse берётся только из текущего materialized
`workflow-state.latest_artifacts.source_assertion_review`. Outer wrapper снимает
его pre/post snapshot; reuse принимается, только если artifact существовал до
downstream, остался byte-identical, а path и digest в timer receipt точно совпали
с ожидаемым snapshot. Missing, fresh, overwritten, deleted или foreign-path review
artifact переводит source lifecycle count в `unknown`.

Bridge recovery использует отдельный timer snapshot непосредственно перед bridge:
допустим только неизменный prefix и appended current suffix. Future-dated старые
phases, переписанный prefix и дубли текущих `scope-analysis`/`semantic-design` не
используются для восстановления counts; при отсутствии независимых fresh phase
summaries соответствующий component остаётся `unknown`.

```powershell
.\.venv\Scripts\python.exe scripts\run_lean_production_iteration.py `
  <current-process-arguments> `
  --timer <timer> `
  --defer-timer-finish
```

Он фиксирует `source-review`, `compile-preflight`, `writer-reviewer` и `promotion`,
но не закрывает общий timer. На failure он также оставляет timer caller-у, чтобы
в измерение вошёл честный `final-reporting`.

Обрабатываемый failure до downstream тоже не должен преждевременно закрывать
общий timer: текущая фаза завершается со статусом `failed`, затем выполняется
`final-reporting`, а `finish` получает фактический terminal status. Команда
`terminalize` остаётся аварийным fallback, когда продолжить turn и подготовить
обычный отчет невозможно.

Если root-turn уже завершился внешним `systemError`, следующая сессия должна
сначала найти exact `task_complete` этого `turn_id`, затем закрыть timer командой
`terminalize --finished-epoch-ms <request_started_epoch_ms + duration_ms>` и только
после этого выполнить `reconcile-codex-turn`. Без исторической границы recovery
ошибочно припишет аварийному turn время до запуска следующей сессии. Такой timer
сохраняется как failed diagnostic вне `fts/<ft-slug>` source-routing namespace;
его нельзя продолжать как clean benchmark.

## Завершение и сверка с Codex UI

После downstream terminal result открывается `final-reporting`. Сначала полностью
подготовь итоговый ответ и перечень результатов, затем последним tool action закрой
эту фазу и run одним timestamp:

```powershell
.\.venv\Scripts\python.exe scripts\workflow_wall_clock.py finish `
  --output <timer> `
  --status <signed-off-or-terminal-status> `
  --test-case-count <count> `
  --active-phase final-reporting `
  --compact `
  --artifact-root <handoff> `
  --artifact-root <review-cycle> `
  --artifact-root <final-test-cases>
```

После появления `task_complete`, обычно в следующем turn, одной командой выполни
сверку и выпуск итоговых отчетов:

```powershell
.\.venv\Scripts\python.exe scripts\workflow_wall_clock.py reconcile-report `
  --output <timer> `
  --json-output <run-dir>\timing-report.json `
  --markdown-output <run-dir>\timing-report.md
```

Команда находит exact `duration_ms` по сохранённому `turn_id`, не копирует текст
ответа из rollout, добавляет внешнее наблюдение append-only и атомарно пишет
JSON/Markdown. Если exact `task_complete` ещё недоступен, она возвращает
`pending-task-complete` с кодом `3`, не меняет timer, не заявляет полное время и
не пишет отчеты; тот же вызов нужно повторить позже. Root-agent tokens
атрибутируются фазам по timestamp завершения model step; события после закрытия
recorder попадают в `post-recorder-to-task-complete` и не смешиваются с
subprocess tokens.

Если значение UI нужно внести вручную:

```powershell
.\.venv\Scripts\python.exe scripts\workflow_wall_clock.py reconcile-ui `
  --output <timer> `
  --elapsed-ms <ui-duration-ms> `
  --precision-ms 1000 `
  --claim-full-user-wall
```

Без явного `--claim-full-user-wall` ручное значение сохраняется как контрольное,
но не заменяет primary wall-clock. Claim отклоняется, если endpoint не
`ui-final`/`task-complete`, значение короче внутреннего окна или передан чужой
`turn_id`.

## Обязательные поля отчета

- `observed_window_ms` и внешний `full_user_wall_ms`;
- `phase_sum_ms`, `phase_union_ms`, overlap и `unattributed_ms`;
- все gaps до первой, между и после последней фазы;
- duration, input/output file count и bytes по каждой фазе;
- input/cached/output/total tokens каждой модельной стадии;
- отдельные input/cached/output/reasoning/total tokens root-agent по фазам и
  `post-recorder-to-task-complete`;
- terminal status, TC count и общий persistent artifact inventory;
- суммарные `attempt_count` / `retry_count` и
  `lifecycle_count_evidence` с `verified`, `recovered` или `unknown` provenance;
- coverage label и честный список исключенных endpoints;
- недостающие ожидаемые фазы как данные, а не как автоматически проваленный gate.

Observation-run не оценивается по времени и ничего не останавливает. Его результат
— фактическая картина, на основе которой ограничения или цели можно обсуждать
отдельно.
