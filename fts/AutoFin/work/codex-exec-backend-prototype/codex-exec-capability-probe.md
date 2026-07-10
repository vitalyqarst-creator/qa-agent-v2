# Capability probe: `codex exec`

Дата проверки: `2026-07-10`.

## Итог

Статус: `available-authenticated`.

CLI из `PATH` по-прежнему недоступен из-за AppX ACL, однако найдены две исполнимые user-local копии. Read-only ephemeral auth probe на более новой копии завершился с exit code `0`, вернул `CAPABILITY_OK` и JSONL `thread.started` с новым `thread_id`. Для live runner требуется явный `--codex-command`; полагаться на `PATH` нельзя.

## Наблюдения

| Проверка | Результат |
|---|---|
| `Get-Command codex -All` | Найдены `codex` и `codex.exe` в `C:\Program Files\WindowsApps\OpenAI.Codex_26.707.3748.0_x64__2p2nqsd0c76g0\app\resources`. |
| User-local CLI | `.codex/.sandbox-bin/codex.exe` — `codex-cli 0.119.0-alpha.28`; `.codex/plugins/.plugin-appserver/codex.exe` — `codex-cli 0.144.0-alpha.4`. Обе копии исполняют `exec --help`. |
| `codex --version` через `PATH` | AppX executable возвращает PowerShell `Access is denied`; этот путь непригоден. |
| Наличие `codex exec` | Подтверждено на обеих user-local копиях. |
| Sandbox flags | `--sandbox read-only|workspace-write|danger-full-access`; для prototype допустимы только первые два по role. |
| JSON/JSONL output | `--json`; фактические event types: `thread.started`, `turn.started`, `item.completed`, `turn.completed`. |
| Session identity | `thread.started.thread_id`; probe id присутствовал и был непустым. |
| Usage | `turn.completed.usage` содержит `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`. |
| Output-last-message | `--output-last-message <FILE>` / `-o`; файл содержал ровно `CAPABILITY_OK`. |
| Working-directory flag | `--cd <DIR>` / `-C`. |
| Ephemeral mode | `--ephemeral`; probe не сохранял resumable session. |
| Auth | Подтверждено успешным model turn, exit code `0`. |
| Non-interactive approval | Probe не запрашивал tool execution, поэтому отсутствие approval prompt для model-only turn подтверждено, а blocker для tool-команд ещё должен проверяться live smoke sandbox-ом. |
| Minimal dry run | Read-only, ephemeral, без tools; exit code `0`, final message `CAPABILITY_OK`. Captures сохранены в `capability-live/`. |

## Решение для прототипа

- Runner продолжает принимать executable и flags как явную конфигурацию и требует `--cli-contract-verified`.
- Проверенная конфигурация: `--sandbox`, writer `workspace-write`, reviewer `read-only`, `--cd`, `--json`, writer `--output-last-message`, `--ephemeral` как extra arg.
- Live smoke разрешён, но promotion остаётся выключенной по умолчанию.
- AppX path не использовать; выбран user-local CLI `0.144.0-alpha.4`.

## Следующий capability probe

Перед каждым live smoke повторять `--version` на явно выбранном executable. Если user-local path исчез или event schema больше не содержит `thread.started.thread_id`, live execution блокируется до адаптации wrapper-а.
