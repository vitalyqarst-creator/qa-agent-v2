# Сравнение SDK runner и `codex exec` prototype

## Evidence base

- Capability probe: packaged `codex` обнаружен, но не исполняется (`Access is denied`), поэтому live evidence отсутствует.
- Mocked exec backend suite: `19 passed`; command construction, isolation values, captures, timeout, missing/stale outputs, reuse deterministic structure gate, draft hash pinning и promotion safety проверяются детерминированно.
- Существующий SDK runner сохраняется без удаления и проверяется прежней test suite.

## Сравнение

| Критерий | SDK runner | Exec prototype |
|---|---|---|
| Lifecycle | Long-lived SDK thread/turn, completion manifest, lock и resume recovery. | Один OS process на stage; следующий stage стартует только после filesystem validation. |
| Completion contract | Зависит от SDK turn status, completion evidence и state advancement. | Exit code недостаточен: обязательны свежий cycle directory, ожидаемые файлы/status/validator result; stale outputs блокируют новый process. |
| Timeout/recovery | Поддерживает thread-aware recovery и stale locks, но логика сложная. | Timeout даёт явный blocked status; writer progress принимается только при наличии draft и validator pass; auto retry отсутствует. |
| Artifact passing | Prompt/session context плюс cycle artifacts. | Только explicit source/handoff/draft/validator paths. |
| Reviewer isolation | SDK sandbox policy и runner contracts. | Отдельное configured read-only sandbox value; findings возвращаются через stdout; production hash guard. Live enforcement ещё не подтверждён. |
| Promotion safety | Текущий runner уже обрабатывает unsigned drafts и terminal gates. | Draft всегда в work outputs; promotion выключена по умолчанию и выполняется только runner после accepted contract. |
| Debuggability | Богатые session maps/events, но completion/recovery взаимосвязаны. | Отдельные stdout/stderr/events/status на каждый process; меньше скрытого session state. |
| Скорость | Потенциально быстрее за счёт повторного использования SDK/app-server context, но recovery может быть дорогим. | Process startup на каждый stage добавляет overhead; фактическая скорость не измерена без live smoke. |
| Основной риск | Сложность completion/resume и partial stage advancement. | Непроверенный CLI/sandbox/auth contract; stdout event schema; crash window при promotion; пока только structure validator для work draft. |

## Рекомендация

Сохранить оба backend, но не переключать default на exec. SDK остаётся production/fallback path. Следующий шаг — повторить capability probe в исполнимой CLI-среде, зафиксировать реальные flags/event schema, добавить staging-compatible full validator и провести небольшой source-backed live cycle без promotion по умолчанию. Только после этого сравнивать надёжность и скорость на фактических данных.
