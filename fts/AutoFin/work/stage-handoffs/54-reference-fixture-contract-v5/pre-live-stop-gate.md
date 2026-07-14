# Pre-Live Stop Gate V5

## Status

`awaiting-offline-checkpoint`

## До live обязательно

- Focused, full agent-layer и artifact-validator tests проходят.
- Architecture audit имеет 0 findings.
- Package v8 и dispatcher config проходят validate-only и exec dry-run.
- V4 rejected draft блокируется новым gate до reviewer.
- Protected baseline hashes подтверждены, target отсутствует.
- Offline checkpoint отправлен в origin; local/remote SHA совпадают.
- Отдельный authorization artifact связывает user instruction, checkpoint SHA, package/config hashes и ровно один invocation budget.

## Запрещено

Live до выполнения всех условий; повтор после terminal result; SDK fallback; исправление benchmark draft вручную; promotion или изменение FT-first baseline.
