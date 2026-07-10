# Сравнение SDK runner и `codex exec` prototype

## Evidence base

- Capability probe: AppX `codex` не исполняется, но user-local `codex-cli 0.144.0-alpha.4` доступен и авторизован; read-only auth probe завершился за ~20 секунд.
- Live writer evidence: новая exec session создана, но writer завершился `blocked-timeout` через `600.453` секунды без draft; reviewer не стартовал.
- Deterministic backend matrix проверяет общий completion path, fresh sessions, captures, timeout, attempt isolation, metrics и promotion safety без live Codex.
- Существующий SDK runner сохраняется без удаления и проверяется прежней test suite.

## Сравнение

| Критерий | SDK runner | Exec prototype |
|---|---|---|
| Lifecycle | Новый SDK thread на каждый stage внутри зрелого runner; completion manifest, lock и recovery остаются сложными. | Один OS process на stage; следующий stage стартует только после filesystem validation. Live writer действительно получил отдельный `thread_id`. |
| Completion contract | Зависит от SDK turn status, completion evidence и state advancement. | Exit code недостаточен: обязательны свежий cycle directory, ожидаемые файлы/status/validator result; stale outputs блокируют новый process. |
| Timeout/recovery | Поддерживает thread-aware recovery и stale locks, но логика сложная. | Timeout даёт явный blocked status; writer progress принимается только при наличии draft и validator pass; auto retry отсутствует. |
| Artifact passing | Prompt/session context плюс cycle artifacts. | Только explicit source/handoff/draft/validator paths. |
| Reviewer isolation | SDK sandbox policy и runner contracts. | Отдельное configured read-only sandbox value; findings возвращаются через stdout; production hash guard. Live enforcement ещё не подтверждён. |
| Promotion safety | Текущий runner уже обрабатывает unsigned drafts и terminal gates. | Draft всегда в work outputs; promotion выключена по умолчанию и выполняется только runner после accepted contract. |
| Debuggability | Богатые session maps/events, но completion/recovery взаимосвязаны. | Отдельные stdout/stderr/events/status на каждый process; меньше скрытого session state. |
| Скорость | Live comparative evidence ещё нет; существующая SDK suite подтверждает lifecycle, но не benchmark. | Текущий live writer не уложился в 600 секунд: 14 inputs / 38.8 MB и 62 command executions до timeout. Гипотеза быстрого handoff пока опровергнута для текущего prompt/input contract. |
| Основной риск | Сложность completion/recovery и v1 stage-owned state advancement. | Writer повторяет тяжёлую source/design работу, внешний scratch конфликтует с sandbox, terminal token usage отсутствует при timeout. |

## Рекомендация

Сохранить оба backend и не переключать default на exec. SDK остаётся production/fallback path. CLI/auth/session contract доказан, но текущая форма writer handoff не соответствует цели скорости: live writer не создал draft за 10 минут. Следующий эксперимент должен сначала уменьшить input/prompt surface и ограничить stage command budget; повторять reviewer/benchmark до этого нецелесообразно.

Полный Phase 10 benchmark не выполнен: Phase 9 остановлен на реальном completion/latency blocker-е согласно guardrail. Сравнивать backend latency без завершённого writer stage было бы некорректно.
