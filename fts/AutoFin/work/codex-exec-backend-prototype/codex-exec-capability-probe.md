# Capability probe: `codex exec`

Дата проверки: `2026-07-10`.

## Итог

Статус: `blocked-codex-exec-unavailable`.

Команда `codex` разрешается через `PATH`, но найденный packaged executable нельзя запустить из текущего non-interactive процесса. Это блокирует проверку версии, subcommand help, auth и live smoke. Статус не классифицирован как auth failure: выполнение останавливается раньше auth handshake.

## Наблюдения

| Проверка | Результат |
|---|---|
| `Get-Command codex -All` | Найдены `codex` и `codex.exe` в `C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources`. |
| Второй CLI в `PATH` | Не найден. В локальном Codex bin присутствует только `rg.exe`; временный arg0-каталог содержит только apply-patch wrappers. |
| `codex --version` | Exit code `1`; PowerShell сообщает `Access is denied` / `NativeCommandFailed`. Версия CLI не получена. |
| `codex --help` | Exit code `1`; тот же executable-access blocker. |
| `codex exec --help` | Exit code `1`; тот же executable-access blocker. |
| Наличие `codex exec` | Не подтверждено исполнимым probe. |
| Sandbox flags | Не подтверждены; имена и значения не предполагаются. |
| JSON/JSONL output | Не подтверждён. |
| Output-last-message или эквивалент | Не подтверждён. |
| Working-directory flag | Не подтверждён. |
| Auth | Не достигнут из-за executable-access blocker; `available/absent` определить нельзя. |
| Non-interactive approval blocker | Не достигнут; поведение определить нельзя. |
| Minimal dry run | Не запускался: даже version/help не стартуют. Фактический exit code probe-команд — `1`, stdout пуст, ошибка находится в PowerShell stderr/error stream. |

## Решение для прототипа

- Live flags не зашиты в runner как якобы подтверждённые.
- Runner принимает sandbox, JSON и cwd flags как явную конфигурацию и требует `--cli-contract-verified`.
- Unit-тесты используют fake process executor и не требуют Codex/auth.
- Live smoke заблокирован отдельным отчётом; fake final artifact не создаётся.

## Следующий capability probe

Повторять только в среде, где `codex --version` и `codex exec --help` реально исполняются. После этого зафиксировать точный help output, проверить безопасный read-only dry run, exit code, stdout/stderr, auth и approval behavior до разрешения live backend.
