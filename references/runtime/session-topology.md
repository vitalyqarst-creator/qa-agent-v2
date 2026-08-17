# Топология сессий practical route

Controller — одна верхнеуровневая Codex-сессия на весь FT-пакет. Она управляет переходами, но не анализирует требования, не пишет matrix/TC и не выносит review-verdict.

## Роли

- Один `source-locator` на FT-пакет, в отдельной от controller верхнеуровневой сессии.
- Для каждого внешнего scope — свой `scope-analyzer` в отдельной верхнеуровневой сессии.
- Для каждого scope — свой `writer` в отдельной верхнеуровневой сессии. Этот же writer создаёт matrix, выполняет разрешённую правку matrix, пишет TC и выполняет разрешённую правку TC.
- Для каждого scope — отдельные `matrix-reviewer` и `tc-reviewer`. Они отличаются от controller, locator, analyzer, writer и друг от друга.

Новые сессии для fixture materialization, запуска validator-а и каждой revision не создаются, пока commit agent-layer не изменился. Повторная работа по тому же scope возвращается в ранее зарегистрированную analyzer/writer/reviewer-сессию соответствующей роли только при совпадении `runtime_commit`. После обновления agent-layer controller создаёт новую верхнеуровневую сессию для каждой реально вызываемой semantic role и заменяет её stale-запись в registry; существующие артефакты переиспользуются, полный этап не повторяется без содержательной причины.

Исторический `accepted` review неизменного artifact не становится stale только из-за смены commit agent-layer: он остаётся привязан к собственным receipt, reviewer thread и SHA-256. Новую reviewer-сессию создавай после обновления runtime лишь тогда, когда действительно требуется новый review или re-review.

Новый practical route по существующему пакету начинается не с source locator, а с определения первого отсутствующего, stale или невалидного артефакта. Controller последовательно проверяет существующие source (`validate_runtime_source.py --resume-existing`), handoff, matrix/review и canonical TC/review и переиспользует все валидные предшествующие результаты. Semantic role вызывается только для первого этапа, который действительно требует изменения; смена runtime commit сама по себе не является причиной пересоздавать артефакты.

Один analyzer или writer нельзя использовать для двух scope: перенос контекста между разделами ухудшает независимость и увеличивает риск скрытого смешения требований.

## Controller-owned registry

До запуска semantic role controller создаёт `work/runtime-session-registry.json` и регистрирует фактический `threadId`/`hostId`, полученные от Codex Desktop. Допустим только `codex-thread`; subagent, fork и выдуманный ID запрещены. Операции Codex Desktop и их порядок уже перечислены ниже и в `AGENTS.md`: controller не выполняет web search документации перед стандартным dispatch. Если встроенная операция недоступна, route останавливается.

В начале каждого следующего turn controller проверяет, что открытая сессия работает по текущему commit agent-layer:

```text
python scripts/runtime_session_registry.py controller-check --package-root <FT-package> --expected-thread-id <controller-threadId>
```

Если проверка сообщает об изменившемся runtime commit, controller сначала перечитывает текущие `AGENTS.md` и этот файл, затем явно подтверждает новую версию и повторяет `controller-check`:

```text
python scripts/runtime_session_registry.py acknowledge-runtime --package-root <FT-package> --controller-thread-id <controller-threadId>
```

До успешного `controller-check` создавать или продолжать semantic role запрещено. Обычный role self-check также проверяет runtime commit текущей semantic role. Старую semantic role нельзя подтвердить после изменения кода: для следующего вызова этой роли нужна новая верхнеуровневая сессия, чтобы инструкции гарантированно загрузились заново.

```text
python scripts/runtime_session_registry.py init --package-root <FT-package> --controller-thread-id <threadId> --controller-host-id <hostId>
python scripts/runtime_session_registry.py record --package-root <FT-package> --role source-locator --thread-id <threadId> --host-id <hostId>
python scripts/runtime_session_registry.py record --package-root <FT-package> --role scope-analyzer --scope <scope> --thread-id <threadId> --host-id <hostId>
python scripts/runtime_session_registry.py record --package-root <FT-package> --role writer --scope <scope> --thread-id <threadId> --host-id <hostId>
```

Для reviewer запись выполняется автоматически командой `runtime_review_dispatch.py create` по имени review-каталога `<scope>`.

Каждый operational prompt содержит роль, scope, собственный `threadId` и команду self-check:

```text
python scripts/runtime_session_registry.py verify --package-root <FT-package> --through <stage> --scope <scope> --expected-role <role> --expected-thread-id <threadId>
```

Source locator использует `--through source-locator` без `--scope`. Ошибка registry останавливает этап до чтения semantic inputs.

Operational prompt — только транспортный конверт этапа, а не место для тест-дизайна. Controller указывает роль, scope, self-check, пути входных/выходных артефактов из canonical references или `workflow-state.yaml` и требование запустить штатный validator. Он не пересказывает findings, не трактует требования, не вводит дополнительные решения по `TC`/`coverage-gap`/готовности, не запрещает допустимые статусы и не придумывает путь результата. Для revision достаточно дать путь к review-record: semantic role сама читает конечные findings и применяет свой skill. Если controller считает нужным добавить содержательное ограничение, он должен остановиться и вернуть вопрос соответствующей semantic role, а не встраивать своё решение в prompt.

## Переходы

Controller запускает следующий этап только после успешного artifact validator-а и проверки registry. Отдельная сессия не означает новый цикл: замечания matrix reviewer возвращаются исходному writer, затем текущая matrix повторно проверяется тем же matrix reviewer; аналогично для TC.

При `tc-changes-required` controller запускает `validate_runtime_review.py` и использует только его `repair_stage`. Для `repair_stage: tc` findings возвращаются writer-у на ограниченную правку canonical TC. Для `repair_stage: matrix` первым невалидным артефактом снова становится matrix: writer исправляет matrix, отдельный matrix reviewer проверяет её новую версию, после `matrix-accepted` writer заново проецирует затронутые TC, а отдельный TC reviewer проверяет весь актуальный набор. Старые matrix/TC review-record после изменения соответствующего artifact остаются историческими и не разрешают следующий этап. Controller не определяет происхождение дефекта сам и не пересказывает findings в operational prompt.

При повторной проекции после `repair_stage: matrix` operational prompt содержит путь исходного TC review-record как входной artifact, но не пересказывает его findings. Writer обязан закрыть все `tc|both` findings и применимые изменения принятой matrix; неизменный canonical TC при наличии таких findings не считается завершённой проекцией.

Если зарегистрированная сессия недоступна, controller не подменяет её другой ролью и не продолжает в собственной сессии. Требуется явное решение пользователя о замене роли или новом practical route.
