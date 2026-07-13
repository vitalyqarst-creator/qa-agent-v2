# V7 Terminal Stop Gate

## Terminal state

`blocked-invalid-output`

## Обязательные запреты

- Не запускать V7 dispatcher повторно.
- Не выполнять resume writer или reviewer sessions.
- Не принимать отклонённый reviewer JSON как sign-off или authoritative findings set.
- Не редактировать generated V7 evidence и не использовать draft как requirement source.
- Не создавать и не продвигать production shadow.
- Не изменять FT-first baseline.

## Разрешённый successor

Только новый immutable V8 cycle после regression-проверки status-specific reviewer schema, deterministic package-id consistency/migration и dictionary evidence projection. Диагностические `F-001/F-003/F-004/F-005` можно включать в repair set лишь после source-backed verification; `F-002` нельзя переносить, пока он противоречит `DICT-001` source evidence.
