# V6 Terminal Stop Gate

## Terminal state

`blocked-quality-gate`

## Обязательные запреты

- Не запускать V6 dispatcher повторно.
- Не выполнять resume ни одной из четырёх writer sessions.
- Не запускать reviewer на заблокированном draft.
- Не редактировать V6 generated evidence и не использовать его как requirement source.
- Не создавать и не продвигать production shadow.

## Разрешённый successor

Только новый immutable V7 cycle после реализации и regression проверки prepared oracle preflight и hash-bound targeted repair route. V7 может использовать V6 merged draft как unsigned repair input при сохранении source-backed package как единственного requirement evidence.
