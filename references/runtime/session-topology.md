# Топология сессий practical route

Controller — одна верхнеуровневая Codex-сессия на весь FT-пакет. Она управляет переходами, но не анализирует требования, не пишет matrix/TC и не выносит review-verdict.

## Роли

- Один `source-locator` на FT-пакет, в отдельной от controller верхнеуровневой сессии.
- Для каждого внешнего scope — свой `scope-analyzer` в отдельной верхнеуровневой сессии.
- Для каждого scope — свой `writer` в отдельной верхнеуровневой сессии. Этот же writer создаёт matrix, выполняет разрешённую правку matrix, после `matrix-accepted` материализует данные, пишет TC и выполняет разрешённую правку TC.
- Для каждого scope — отдельные `matrix-reviewer` и `tc-reviewer`. Они отличаются от controller, locator, analyzer, writer и друг от друга.

Новые сессии для fixture materialization, запуска validator-а и каждой revision не создаются, пока commit agent-layer не изменился. Повторная работа по тому же scope возвращается в ранее зарегистрированную analyzer/writer/reviewer-сессию соответствующей роли только при совпадении `runtime_commit`. После обновления agent-layer controller создаёт новую верхнеуровневую сессию для каждой реально вызываемой semantic role и заменяет её stale-запись в registry; существующие артефакты переиспользуются, полный этап не повторяется без содержательной причины.

Исторический `accepted` review неизменного artifact не становится stale только из-за смены commit agent-layer: он остаётся привязан к собственным receipt, reviewer thread и SHA-256. Новую reviewer-сессию создавай после обновления runtime лишь тогда, когда действительно требуется новый review или re-review.

Новый practical route по существующему пакету начинается не с source locator, а с определения первого отсутствующего, stale или невалидного артефакта. Controller последовательно проверяет существующие source (`validate_runtime_source.py --resume-existing`), handoff, matrix/review и canonical TC/review и переиспользует все валидные предшествующие результаты. Semantic role вызывается только для первого этапа, который действительно требует изменения; смена runtime commit сама по себе не является причиной пересоздавать артефакты.

`validate_runtime_source.py --resume-existing` запускается только после того, как controller нашёл существующий source handoff и подтвердил наличие обоих обязательных файлов `source-selection.md` и `workflow-state.yaml`; package root и handoff directory передаются как два позиционных аргумента. Если handoff отсутствует, validator не вызывается с неполной командой — первым этапом сразу считается source locator.

Один analyzer или writer нельзя использовать для двух scope: перенос контекста между разделами ухудшает независимость и увеличивает риск скрытого смешения требований.

Scope analyzer-ы одного FT-пакета не работают одновременно: они последовательно обновляют общий `work/scope-clarification-requests.md`. Controller запускает следующий analyzer только после завершения предыдущего и успешного scope-validator-а.

## Controller-owned registry

До запуска semantic role controller создаёт `work/runtime-session-registry.json` и регистрирует фактический `threadId`/`hostId`, полученные от Codex Desktop. Допустим только `codex-thread`; subagent, fork и выдуманный ID запрещены. Операции Codex Desktop, поддерживаемые параметры `create_thread` и их порядок заданы активным tool contract и ниже: controller не выполняет web search документации перед стандартным dispatch. Если встроенная операция или указанный профиль недоступны, route останавливается, а не ищет обход в интернете.

При инициализации registry фиксируется SHA-256 пользовательского `AGENT-NOTES.md`. Его изменение внутри route блокирует следующий self-check: generated XHTML, runtime-классификация и поздний support принадлежат source handoff, а не переписывают package-specific вход.

Обычный dispatch source locator, analyzer и writer всегда двухфазный:

1. Controller вызывает `list_projects` и выбирает текущий сохранённый проект.
2. `create_thread` вызывается с project target и `environment: {type: "local"}`. Начальный prompt только просит ждать operational follow-up; он запрещает читать или менять FT-пакет. `worktree` и последующий `handoff_thread` для semantic role не используются: перенос меняет checkout/ID, создаёт гонку реестра и отделяет результаты от текущего пакета.
3. Controller получает фактические `threadId` и `hostId`, регистрирует их штатной командой `runtime_session_registry.py record` и проверяет успешность записи.
4. Только после регистрации controller отправляет через `send_message_to_thread` рабочий prompt с ролью, scope и self-check.
5. Controller ожидает `turnCompleted` через `wait_threads`, затем независимо запускает artifact validator и только после `valid=true` объявляет этап завершённым. Controller не завершает собственный turn сообщением «review запущен», пока reviewer ещё работает: stage summary допустим только после terminal status semantic thread и проверки review-record. `waitingOnApproval`, `needsAttention`, незавершённый turn или один лишь текст semantic role не являются завершением этапа. Если требуется действие пользователя, controller сообщает `blocked-user-action`, но не выдаёт устаревший успешный stage summary; при продолжении сначала повторно проверяет состояние semantic thread и validator.

Начальный semantic prompt непосредственно в `create_thread` запрещён: сессия может начать self-check раньше, чем controller успеет записать её ID в registry.

### Модель и уровень рассуждений

Если пользователь в задаче текущего этапа явно задал модель и уровень рассуждений создаваемой semantic-сессии, controller передаёт точные поддерживаемые значения в `create_thread` как `model` и `thinking`. Это параметры запуска сессии, а не текст operational prompt. Controller не заменяет указанную модель близкой, не понижает уровень рассуждений и не переносит выбор автоматически на другие роли или следующие этапы.

Если пользователь не задал профиль, controller использует cost-aware role default:

| Роль | Модель | Уровень рассуждений |
| --- | --- | --- |
| `source-locator` | `gpt-5.6-luna` | `medium` |
| `scope-analyzer` | `gpt-5.6-terra` | `xhigh` |
| `writer` | `gpt-5.6-terra` | `high` |
| `matrix-reviewer` | `gpt-5.6-terra` | `xhigh` |
| `tc-reviewer` | `gpt-5.6-terra` | `xhigh` |

Для controller-сессии рекомендуемый профиль при ручном создании — `gpt-5.6-terra` / `low`. Эти defaults заданы по смысловой сложности роли: analyzer и независимые reviewer используют `xhigh`, writer — `high`; профиль не повышается из-за длины инструкций или ошибки формата. Модель `gpt-5.6-sol` в default route не используется.

Фактический выбор фиксируется в `runtime-session-registry.json`; команда `record` получает оба флага `--model` и `--thinking`. В итоговом stage summary controller берёт этот факт из registry, а не из памяти; это служебная информация и не попадает в FT-артефакты.

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

К соответствующей команде `record` добавь фактически использованные `--model <model> --thinking <level>`. Для reviewer те же значения передаются в `runtime_review_dispatch.py create` через `--reviewer-model` и `--reviewer-thinking`.

Для reviewer запись выполняется автоматически командой `runtime_review_dispatch.py create` по имени review-каталога `<scope>`.

Каждый operational prompt содержит роль, scope, собственный `threadId` и команду self-check:

```text
python scripts/runtime_session_registry.py verify --package-root <FT-package> --through <stage> --scope <scope> --expected-role <role> --expected-thread-id <threadId>
```

Source locator использует `--through source-locator` без `--scope`. Ошибка registry останавливает этап до чтения semantic inputs.

Сразу после успешного self-check semantic-сессия полностью читает role-skill, путь и SHA-256 которого возвращены командой. Controller обязан дословно включить в operational prompt требование прочитать этот файл до любых semantic inputs. Соответствие ролей фиксировано:

- `source-locator` → `skills/ft-source-locator/SKILL.md`;
- `scope-analyzer` → `skills/ft-scope-analyzer/SKILL.md`;
- `writer` → `skills/ft-test-case-writer/SKILL.md`;
- `matrix-reviewer` и `tc-reviewer` → `skills/ft-test-case-reviewer/SKILL.md`.

Название роли в prompt или ссылка на `skills/README.md` не заменяют чтение точного `SKILL.md`. Если self-check не вернул skill contract, файл отсутствует или его SHA-256 не совпал, этап останавливается до чтения FT-пакета.

Operational prompt — только транспортный конверт этапа, а не место для тест-дизайна. Controller указывает роль, scope, self-check, пути входных/выходных артефактов из canonical references или `workflow-state.yaml` и требование запустить штатный validator. Он не пересказывает findings, не трактует требования, не вводит дополнительные решения по `TC`/`coverage-gap`/готовности, не запрещает допустимые статусы и не придумывает путь результата. Для revision достаточно дать путь к review-record: semantic role сама читает конечные findings и применяет свой skill. Если controller считает нужным добавить содержательное ограничение, он должен остановиться и вернуть вопрос соответствующей semantic role, а не встраивать своё решение в prompt.

## Переходы

Controller запускает следующий этап только после успешного artifact validator-а и проверки registry. Отдельная сессия не означает новый цикл: замечания matrix reviewer возвращаются исходному writer, затем текущая matrix повторно проверяется тем же matrix reviewer; аналогично для TC. Первое review всегда полное. После revision controller передаёт прежний review-record в `runtime_review_dispatch.py create --previous-review`; controller не выбирает объём вручную. Штатный manifest разрешает delta re-review только для заявленных и локализованных изменений при неизменных semantic inputs, структуре и порядке artifact, иначе автоматически требует полный review.

Для scope-validator controller использует поля `scope_revision_count`, `correction_allowed` и `error_counts_by_class` из JSON. При первом `valid=false` локальная коррекция разрешена только при `correction_allowed=true`; analyzer перед ней меняет count с `0` на `1`. Повторный `valid=false` при count `1` завершает этап как `scope-stage-failed`: controller не отправляет третью попытку и не называет ошибки форматными, если классификация содержит смысловые категории.

При `tc-changes-required` controller запускает `validate_runtime_review.py` и использует только его `repair_stage`. Для `repair_stage: tc` findings возвращаются writer-у на ограниченную правку canonical TC. Для `repair_stage: matrix` первым невалидным артефактом снова становится matrix: writer исправляет matrix, отдельный matrix reviewer проверяет её новую версию, после `matrix-accepted` writer заново проецирует затронутые TC, а отдельный TC reviewer проверяет весь актуальный набор. Старые matrix/TC review-record после изменения соответствующего artifact остаются историческими и не разрешают следующий этап. Controller не определяет происхождение дефекта сам и не пересказывает findings в operational prompt.

При повторной проекции после `repair_stage: matrix` operational prompt содержит путь исходного TC review-record как входной artifact, но не пересказывает его findings. Writer обязан закрыть все `tc|both` findings и применимые изменения принятой matrix; неизменный canonical TC при наличии таких findings не считается завершённой проекцией.

Перед dispatch re-review controller проверяет не только новый SHA и общий validator, но и closure-отчёт writer-а: для каждого `finding_id` должны быть перечислены все `affected_items` исходного record и подтверждено `остаточных нарушений: 0` после повторного чтения этих элементов. Отсутствующий элемент или частично выполненная массовая замена не передаются reviewer-у как завершённая revision. Controller не решает семантику finding-а заново, а проверяет полноту заявленного набора и наличие residual-check.

Если зарегистрированная сессия недоступна, controller не подменяет её другой ролью и не продолжает в собственной сессии. Требуется явное решение пользователя о замене роли или новом practical route.
