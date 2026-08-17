# Controller-owned запуск и актуальность независимого review

Matrix и canonical TC проверяются в разных верхнеуровневых Codex-сессиях, зарегистрированных по `session-topology.md`. Reviewer не создаёт собственную сессию и не формирует dispatch evidence: запуском и регистрацией владеет controller.

## Двухфазный dispatch

1. Controller создаёт operational prompt в `work/reviews/<scope>/<matrix|tc>-review-prompt.md`.
2. Через встроенный Codex Desktop API controller вызывает `list_projects`, затем `create_thread` в local environment текущего проекта. Начальный bootstrap prompt запрещает читать artifacts и выполнять review до operational follow-up.
3. Полученный от `create_thread` `threadId` controller регистрирует командой `scripts/runtime_review_dispatch.py create`. Команда одновременно закрепляет reviewer за scope в `runtime-session-registry.json`. Receipt имеет имя `<kind>-review-dispatch-<artifact-hash-prefix>.json`.
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
  "dispatch_path": "work/reviews/<scope>/matrix-review-dispatch-<hash-prefix>.json",
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
- `dispatch_path` указывает на controller-owned receipt текущего artifact; thread ID и hashes в receipt и review-record должны совпадать.
- Writer не создаёт TC без успешной проверки принятой matrix. Набор TC не считается выпущенным без успешной проверки `tc-accepted` для текущих байтов файла.

Проверка:

```text
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind matrix --require-accepted
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind tc --require-accepted
```

Review-record подтверждает актуальность и форму независимого review, но не заменяет содержательную проверку источников.
