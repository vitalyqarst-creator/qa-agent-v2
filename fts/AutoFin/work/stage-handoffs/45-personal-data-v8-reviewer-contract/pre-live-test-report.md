# V8 Pre-live Test Report

## Вывод

V8 готов к checkpoint, но live пока запрещён. Reviewer contract, DICT projection, metadata migration и 13-TC bounded repair проходят preflight; FT-first baseline не изменён.

## Проверки

| проверка | результат |
| --- | --- |
| Runner + instruction-context | `120 passed` (`94` runner, `26` context) |
| Расширенные prepared/compiler/dispatcher/instruction/artifact проверки | Совокупно `627` passing checks; новый context-headroom failure исправлен и повторно прошёл |
| Унаследованные fixture-dependent tests | `2 failed`: отсутствует `tests/fixtures/agent-artifacts/ui-evidence-policy`; вне H45 |
| Instruction context | reviewer prepared headroom `20.0 KiB`; целевой regression pass |
| V8 compile | `65` obligations; logical evidence `49104 / 49152` bytes |
| V8 validate-only | `13` targets; `34` preserved; oracle `65/65`; capacity pass; attempts отсутствуют |
| Exec dry-run | contract v2; backend `exec`; fallback `false` |
| H45 artifact validator | `0 errors / 0 warnings / 3` inherited source-quality info |
| Baseline boundary | SHA-256 `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`; shadow absent |

## Первый compiler stop

Первая компиляция была корректно остановлена: evidence превышал лимит на `2103` bytes. Лимит не повышался. Повторяющийся текст design plan был сокращён при сохранении конкретного поля, действия, branch-precondition и наблюдаемого oracle; повторная компиляция прошла с запасом `48` logical bytes.

## Live boundary

До checkpoint/push и отдельного `pre-live-authorization.md` нельзя запускать dispatcher. После авторизации допускается один запуск V8; retry, resume, SDK fallback и recompile запрещены.
