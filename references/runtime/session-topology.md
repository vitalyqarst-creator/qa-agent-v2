# Топология сессий practical route

Controller — одна верхнеуровневая Codex-сессия на весь FT-пакет. Она управляет переходами, но не анализирует требования, не пишет matrix/TC и не выносит review-verdict.

Source handoff всегда находится в `work/stage-handoffs/00-<package-root.name>/`. Scope handoff находится отдельно в `work/stage-handoffs/<canonical-scope>/`. Целевой scope из пользовательской задачи не участвует в имени source handoff; controller проверяет это source-validator-ом до регистрации analyzer-а.

## Роли

- Один `source-locator` на FT-пакет, в отдельной от controller верхнеуровневой сессии.
- Для каждого внешнего scope — свой `scope-analyzer` в отдельной верхнеуровневой сессии.
- Для каждого scope — свой `writer` в отдельной верхнеуровневой сессии. Этот же writer создаёт matrix, выполняет разрешённую правку matrix, после `matrix-accepted` материализует данные, пишет TC и выполняет разрешённую правку TC.
- Для каждого scope — отдельные `matrix-reviewer` и `tc-reviewer`. Они отличаются от controller, locator, analyzer, writer и друг от друга.

Новые сессии для fixture materialization, запуска validator-а и revision не создаются. Commit agent-layer фиксируется при `init` и становится неизменяемым после регистрации первой semantic role. Повторная работа по тому же scope возвращается в ранее зарегистрированную analyzer/writer/reviewer-сессию соответствующей роли только внутри этого frozen runtime.

Исторический `accepted` review неизменного artifact не становится stale только из-за смены commit agent-layer: он остаётся привязан к собственным receipt, reviewer thread и SHA-256. Новую reviewer-сессию создавай после обновления runtime лишь тогда, когда действительно требуется новый review или re-review.

После изменения agent-layer активный run не обновляется: controller создаёт новую чистую practical run-папку. Новый route по существующему пакету начинается с определения первого отсутствующего, stale или невалидного артефакта и может унаследовать валидные immutable source/scope handoff штатными командами ниже. Историческая session identity подтверждает происхождение унаследованного artifact, но такая сессия не возобновляется в новом runtime.

Если валидный source handoff скопирован в новую чистую папку того же FT-пакета, controller не выдумывает locator session и не запускает locator повторно. После `init` он переносит точную историческую запись из исходного пакета штатной командой, затем запускает source validator с `--resume-existing`:

```text
python scripts/runtime_session_registry.py inherit-source --package-root <new-package> --from-package-root <source-package>
```

Команда разрешает перенос только при совпадении SHA-256 `AGENT-NOTES.md`, сохраняет исходные thread/host/runtime/timestamp/profile и не переносит controller или scope-роли.

Если вместе с source handoff в чистую папку перенесён уже завершённый scope handoff, controller не запускает analyzer только ради заполнения нового registry. После `inherit-source` и успешных source/scope validator-ов он переносит историческую analyzer-запись:

```text
python scripts/runtime_session_registry.py inherit-scope --package-root <new-package> --from-package-root <source-package> --scope <scope>
```

`inherit-scope` разрешён только при одинаковом `AGENT-NOTES.md`, том же унаследованном source-locator и совпадении SHA-256 нормализованного UTF-8 текста всех analyzer-owned scope-файлов вместе с общим реестром вопросов. Нормализуются только BOM и переводы строк LF/CRLF; содержательные символы и пробелы остаются значимыми. Команда сохраняет фактические thread/host/runtime/timestamp/profile analyzer-а и не переносит writer/reviewer. Несовпадение любого входа означает, что scope действительно изменился и требует новой analyzer-сессии; вручную копировать запись запрещено.

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
5. Controller ожидает `turnCompleted` через `wait_threads`, затем независимо запускает artifact validator и только после `valid=true` объявляет этап завершённым. Timeout одного вызова `wait_threads` — только результат polling, не terminal status и не основание просить замену роли. Пока thread имеет `active`/`inProgress` либо меняются cursor/revision/tool/file events, controller продолжает ждать ту же сессию с последним cursor; одно лишь прошедшее время не означает недоступность. Недоступность подтверждается только ошибкой thread API/not-found либо terminal `failed`/`interrupted`. Controller не завершает собственный turn сообщением «review запущен», пока reviewer ещё работает: stage summary допустим только после terminal status semantic thread и проверки review-record. `waitingOnApproval`, `needsAttention`, незавершённый turn или один лишь текст semantic role не являются завершением этапа. Если требуется действие пользователя, controller сообщает `blocked-user-action`, но не выдаёт устаревший успешный stage summary; при продолжении сначала повторно проверяет состояние semantic thread и validator.

Если сразу после dispatch semantic role сообщает об отсутствии handoff, но controller в том же project/cwd подтверждает канонический путь и `valid=true`, controller повторно передаёт тот же operational prompt той же зарегистрированной сессии один раз. Новая role-сессия не создаётся. Повторное отсутствие становится `blocked-input` с фактическими project/cwd/path.

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

`acknowledge-runtime` допустим только до регистрации первой semantic role, например если commit изменился между `init` и фактическим стартом. После начала semantic work изменившийся commit означает обязательный новый clean run:

```text
python scripts/runtime_session_registry.py acknowledge-runtime --package-root <FT-package> --controller-thread-id <controller-threadId>
```

До успешного `controller-check` создавать или продолжать semantic role запрещено. Запрещено частично переносить новый runtime в активный route либо заменять отдельные role-сессии после изменения кода.

```text
python scripts/runtime_session_registry.py init --package-root <FT-package> --controller-thread-id <threadId> --controller-host-id <hostId>
python scripts/runtime_session_registry.py record --package-root <FT-package> --role source-locator --thread-id <threadId> --host-id <hostId>
python scripts/runtime_session_registry.py record --package-root <FT-package> --role scope-analyzer --scope <scope> --thread-id <threadId> --host-id <hostId>
python scripts/runtime_session_registry.py record --package-root <FT-package> --role writer --scope <scope> --thread-id <threadId> --host-id <hostId>
```

К соответствующей команде `record` добавь фактически использованные `--model <model> --thinking <level>`. Для reviewer те же значения передаются в `runtime_review_dispatch.py prepare` через `--reviewer-model` и `--reviewer-thinking`.

Для reviewer controller одной командой `runtime_review_dispatch.py prepare` создаёт ограниченный input manifest, operational prompt, dispatch receipt и record/summary scaffolds, а также автоматически регистрирует reviewer по имени review-каталога `<scope>`. Ручная сборка этих transport artifacts не является default.

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

Параметр registry `--through` называет semantic role, а не создаваемый artifact: допустимы `source-locator`, `scope-analyzer` и `writer`. Для matrix, materialization, TC и обеих writer revision всегда используется `--through writer`; значения `matrix` и `tc` недопустимы.

## Переходы

Controller не редактирует `matrix_status` или `data_status` вручную. После каждого валидного matrix review он вызывает `runtime_workflow_state.py apply-review`. После `matrix-accepted` выполняется ровно один явный data-stage: `data-start`, материализация всех `TD-*`/`REL-*` текущей matrix тем же writer-ом и `data-complete`; для matrix без ролей helper фиксирует `not-required`. Canonical TC разрешены только после успешного data gate. Если bounded revision cycle исчерпан и остались findings, controller вызывает `runtime_workflow_state.py exhausted`; это закрывает route для TC, а не разрешает обход review.

Controller запускает следующий этап только после успешного artifact validator-а и проверки registry. Замечания reviewer возвращаются исходному writer, затем artifact повторно проверяется тем же reviewer. Первое review всегда полное. На matrix и TC допускается один bounded revision cycle. После него разрешена только одна узкая integrity correction, если validator возвращает `integrity_correction_allowed: true`: все новые findings классифицированы `introduced-by-revision`, относятся только к изменённым элементам и текущему writer-owned stage, semantic inputs не менялись, а review остаётся delta. Любой carried-forward, omission, source/matrix drift или третья попытка завершает cycle как exhausted. Controller передаёт предыдущий record в `runtime_review_dispatch.py prepare --previous-review`; объём и допустимость вычисляет manifest, а не prompt.

Review input manifest содержит только artifact, source package, analyzer-owned файлы текущего scope, общий реестр вопросов, companion matrix/data plan и явно связанные support/visual/data artifacts. Все sibling support, mockups и materializations заново не загружаются. Reviewer расширяет manifest только при доказанной внешней зависимости и фиксирует причину.

После matrix review controller запускает `validate_runtime_review.py` и использует только его машинное поле `review_quality_blocking`. Значение `true` возможно только у manifest-backed re-review после writer revision с `review_quality_status: failed-prior-review-incomplete`; тогда controller останавливает текущий route как `review-quality-failed`: новые findings сохраняются, но не расходуют ещё один обычный revision cycle. Fresh full review, заменяющий record, который стал невалиден после изменения runtime-контракта, не имеет revision manifest; даже если его raw record ошибочно содержит quality-status, `review_quality_blocking=false`, а полный текущий verdict остаётся исправимым штатной writer revision. Controller не трактует raw `review_quality_status` самостоятельно.

Для scope-validator controller использует только машинные поля `correction_allowed`, `next_scope_revision_count`, `correction_exhausted` и `writer_allowed`. При разрешённой коррекции он возвращает analyzer-у полный неизменённый список `blocking_errors`; analyzer исправляет его целиком, устанавливает точный следующий count и повторяет validator. Допускается максимум четыре прохода, без отдельных режимов по типу ошибки. При `correction_exhausted=true` этап завершается как agent-stage failure, а не как вопрос пользователю; writer не запускается. При `writer_allowed=true` controller переходит к matrix; `quality_findings` проверяются writer-ом и independent matrix review.

При `tc-changes-required` controller запускает `validate_runtime_review.py` и использует только его `repair_stage`. Для `repair_stage: tc` findings возвращаются writer-у на ограниченную правку canonical TC. Для `repair_stage: matrix` первым невалидным артефактом снова становится matrix: writer исправляет matrix, отдельный matrix reviewer проверяет её новую версию, после `matrix-accepted` writer заново проецирует затронутые TC, а отдельный TC reviewer проверяет весь актуальный набор. Старые matrix/TC review-record после изменения соответствующего artifact остаются историческими и не разрешают следующий этап. Controller не определяет происхождение дефекта сам и не пересказывает findings в operational prompt.

При `matrix-changes-required` версии checklist 3 controller также запускает `validate_runtime_review.py` и использует машинный `repair_stage`. `scope` возвращает findings analyzer-у, после чего writer заново проектирует matrix; `matrix` возвращает их сразу текущему writer-у. Controller не выводит эту маршрутизацию из текста finding и не пересказывает замечания в prompt.

При повторной проекции после `repair_stage: matrix` operational prompt содержит путь исходного TC review-record как входной artifact, но не пересказывает его findings. Writer обязан закрыть все `tc|both` findings и применимые изменения принятой matrix; неизменный canonical TC при наличии таких findings не считается завершённой проекцией.

Перед dispatch re-review controller проверяет не только новый SHA и общий validator, но и closure-отчёт writer-а: для каждого `finding_id` должны быть перечислены все `affected_items` исходного record и подтверждено `остаточных нарушений: 0` после повторного чтения этих элементов. Отсутствующий элемент или частично выполненная массовая замена не передаются reviewer-у как завершённая revision. Controller не решает семантику finding-а заново, а проверяет полноту заявленного набора и наличие residual-check.

Writer revision может изменять текущую matrix и writer-owned `matrix-data-plan.md`. Она не изменяет analyzer-owned handoff. Поэтому новые `TD-*`/`REL-*`, выводимые из уже зафиксированного source-backed профиля, закрываются в том же matrix cycle; только новый source-level смысл требует возврата к analyzer.

Поздний внешний input проходит теми же ролями по `external-dependency-coverage.md`; несвязанные scope не запускаются. Пока внешний GAP открыт, stage summary фиксирует частичное покрытие.

Если зарегистрированная сессия недоступна, controller не подменяет её другой ролью и не продолжает в собственной сессии. Требуется явное решение пользователя о замене роли или новом practical route.
