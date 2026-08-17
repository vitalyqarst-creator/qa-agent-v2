# Топология сессий practical route

Controller — одна верхнеуровневая Codex-сессия на весь FT-пакет. Она управляет переходами, но не анализирует требования, не пишет matrix/TC и не выносит review-verdict.

## Роли

- Один `source-locator` на FT-пакет, в отдельной от controller верхнеуровневой сессии.
- Для каждого внешнего scope — свой `scope-analyzer` в отдельной верхнеуровневой сессии.
- Для каждого scope — свой `writer` в отдельной верхнеуровневой сессии. Этот же writer создаёт matrix, выполняет разрешённую правку matrix, пишет TC и выполняет разрешённую правку TC.
- Для каждого scope — отдельные `matrix-reviewer` и `tc-reviewer`. Они отличаются от controller, locator, analyzer, writer и друг от друга.

Новые сессии для fixture materialization, запуска validator-а и каждой revision не создаются. Повторная работа по тому же scope возвращается в ранее зарегистрированную analyzer/writer/reviewer-сессию соответствующей роли.

Один analyzer или writer нельзя использовать для двух scope: перенос контекста между разделами ухудшает независимость и увеличивает риск скрытого смешения требований.

## Controller-owned registry

До запуска semantic role controller создаёт `work/runtime-session-registry.json` и регистрирует фактический `threadId`/`hostId`, полученные от Codex Desktop. Допустим только `codex-thread`; subagent, fork и выдуманный ID запрещены.

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

## Переходы

Controller запускает следующий этап только после успешного artifact validator-а и проверки registry. Отдельная сессия не означает новый цикл: замечания matrix reviewer возвращаются исходному writer, затем текущая matrix повторно проверяется тем же matrix reviewer; аналогично для TC.

Если зарегистрированная сессия недоступна, controller не подменяет её другой ролью и не продолжает в собственной сессии. Требуется явное решение пользователя о замене роли или новом practical route.
