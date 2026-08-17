# Controller-owned запуск и актуальность независимого review

Matrix и canonical TC проверяются в разных верхнеуровневых Codex-сессиях, зарегистрированных по `session-topology.md`. Reviewer не создаёт собственную сессию и не формирует dispatch evidence: запуском и регистрацией владеет controller.

## Двухфазный dispatch

1. Controller создаёт operational prompt в `work/reviews/<scope>/<matrix|tc>-review-prompt.md`.
2. Через встроенный Codex Desktop API controller вызывает `list_projects`, затем `create_thread` в local environment текущего проекта. Начальный bootstrap prompt запрещает читать artifacts и выполнять review до operational follow-up.
3. Полученный от `create_thread` `threadId` controller регистрирует командой `scripts/runtime_review_dispatch.py create`. Команда одновременно закрепляет reviewer за scope в `runtime-session-registry.json`. Receipt имеет имя `<kind>-review-dispatch-<artifact-hash-prefix>-<reviewer-thread-prefix>.json`; поэтому повторный review неизменных байтов в новой сессии не перезаписывает историческое evidence.
4. Только после успешной регистрации controller отправляет в созданную сессию operational prompt через `send_message_to_thread`, включая путь receipt.
5. Reviewer первым действием запускает `scripts/runtime_review_dispatch.py verify`. При ошибке он останавливается без verdict.
6. Controller ожидает завершения через `wait_threads`, сверяет фактические thread/host ID, проверяет неизменность SHA-256 receipt относительно значения, возвращённого командой `create`, и валидирует итоговый review-record.

Controller не меняет review inputs между созданием receipt и завершением reviewer. Reviewer изменяет только `<matrix|tc>-review.md` и `<matrix|tc>-review.json`. При вызове `create_thread` controller не переопределяет model/thinking, если пользователь явно этого не запросил.

Controller не использует subagent, fork, analyzer, другой reviewer или текущую writer-сессию как независимый reviewer. После revision controller возвращает re-review в уже зарегистрированную reviewer-сессию того же вида только при неизменном commit agent-layer. Если runtime commit изменился, новый receipt создаётся для новой верхнеуровневой reviewer-сессии, чтобы она заново загрузила текущие инструкции. Если thread API недоступен или пользователь ещё не разрешил создание отдельных сессий, route останавливается до получения возможности/разрешения. Разрешение запрашивается один раз на текущий practical route.

Bootstrap prompt:

```text
Ты создан как независимый reviewer. Не читай файлы проекта, не выполняй review и не изменяй artifacts до отдельного operational prompt controller-а с путём controller-owned dispatch receipt.
```

После получения реального `threadId` controller выполняет:

```text
python scripts/runtime_review_dispatch.py create --package-root <FT-package> --artifact <matrix-or-TC> --review-prompt <prompt.md> --review-dir <work/reviews/scope> --kind <matrix|tc> --reviewer-thread-id <threadId> --reviewer-host-id <hostId>
```

Reviewer проверяет receipt:

```text
python scripts/runtime_review_dispatch.py verify --package-root <FT-package> --artifact <matrix-or-TC> --review-prompt <prompt.md> --dispatch <dispatch.json> --kind <matrix|tc> --reviewer-thread-id <own-threadId>
```

## Итог review

Человекочитаемый итог хранится в `work/reviews/<scope>/<matrix|tc>-review.md`, а рядом создаётся машиночитаемая запись `<matrix|tc>-review.json`.

## Формат записи

```json
{
  "schema_version": 1,
  "review_kind": "matrix",
  "artifact_path": "work/practical/<scope>/test-design-matrix.md",
  "artifact_sha256": "<64 hex>",
  "dispatch_path": "work/reviews/<scope>/matrix-review-dispatch-<hash-prefix>-<thread-prefix>.json",
  "dispatch_sha256": "<64 hex>",
  "reviewer_session_type": "codex-thread",
  "reviewer_session_id": "<top-level thread id>",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "verdict": "matrix-accepted",
  "findings": []
}
```

- `review_kind`: `matrix` или `tc`.
- Допустимые verdict: `matrix-accepted`, `matrix-changes-required`, `tc-accepted`, `tc-changes-required`.
- Accepted verdict требует пустой `findings`; changes-required требует непустой конечный список findings.
- Любое изменение проверенного artifact меняет SHA-256 и делает review устаревшим. После правки нужен новый review-record из отдельной сессии.
- Обновление agent-layer само по себе не отменяет уже принятый review неизменного artifact. Проверка исторического review-record сверяет его собственные immutable receipt, thread ID и hashes, но не требует, чтобы та reviewer-сессия оставалась текущей ролью registry. Свежая сессия обязательна только при фактическом новом review.
- `dispatch_path` указывает на controller-owned receipt текущего artifact; thread ID и hashes в receipt и review-record должны совпадать.
- Writer не создаёт TC без успешной проверки принятой matrix. Набор TC не считается выпущенным без успешной проверки `tc-accepted` для текущих байтов файла.

Для `review_kind: tc` запись дополнительно обязана содержать:

```json
{
  "total_tc_count": 34,
  "reviewed_tc_count": 34,
  "review_scope_complete": true
}
```

Каждый finding при `tc-changes-required` дополнительно содержит `origin_stage`:

```json
{
  "id": "TC-R-001",
  "severity": "material",
  "affected_tc": ["TC-001"],
  "origin_stage": "matrix",
  "description": "Принятая matrix не содержит обязательную ветку покрытия.",
  "required_correction": "Добавить ветку в matrix и заново спроецировать TC."
}
```

- `matrix` — дефект присутствует в принятой matrix, но проверенный TC уже корректен относительно источника и после исправления matrix не требует изменения. Сначала исправляется matrix.
- `tc` — matrix достаточна, а дефект возник только при её проекции в canonical TC. Исправляются TC.
- `both` — содержательная ошибка есть и в matrix, и в TC либо отсутствие matrix-ветки уже привело к отсутствию/ошибке соответствующего покрытия в TC. Сначала исправляется matrix, затем TC.

Reviewer классифицирует происхождение, а не только место проявления. Если любой finding имеет `origin_stage: matrix|both`, validator возвращает `repair_stage: matrix`; только набор из `origin_stage: tc` возвращает `repair_stage: tc`. Controller использует это поле как исполнимую маршрутизацию и не трактует findings самостоятельно.

После принятия исправленной matrix controller передаёт writer-у путь исходного `tc-changes-required` review-record. Writer применяет все findings с `origin_stage: tc|both` и заново проецирует matrix-изменения. Если при наличии `tc|both` findings SHA-256 canonical TC остался равен проверенному review artifact, `validate_runtime_tc.py` отклоняет no-op repair.

Оба счётчика должны совпадать с фактическим числом заголовков `## TC-...` в canonical-файле. В человекочитаемом отчёте обязательна строка `Проверено TC: 34/34` с фактическими значениями. Это исполнимое доказательство полного, не fail-fast review; заявление без совпадающих счётчиков валидатор не принимает.

Проверка:

```text
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind matrix --require-accepted
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind tc --require-accepted
```

Review-record подтверждает актуальность и форму независимого review, но не заменяет содержательную проверку источников.
