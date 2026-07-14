# Manual Quality Gate V8

## Итог

Статус: `passed`.

Проверен immutable draft SHA-256 `30737645afe53d3535db78c005968225b495e63a11ec201edeed2db107e2080b`. Ручные исправления в draft не вносились.

## Проверки

| Проверка | Результат | Evidence |
| --- | --- | --- |
| Количество и идентификаторы | pass | 9 уникальных `TC-QUT-001`–`TC-QUT-009` |
| Названия | pass | Все 9 названий уникальны, включая три негативных сценария |
| Покрытие | pass | 10/10 testable obligations покрыты; один TC объединяет только совместимые результаты одного действия |
| Gap preservation | pass | `OBL-QUT-008` не превращён в TC; `GAP-QUT-001` явно сохранён |
| Exact boundary | pass | Нет 40 МБ exact-boundary/just-over byte fixture; decimal/binary convention не выдумана |
| Portable oversize | pass | 50 МБ используется только как размер, превышающий лимит при обеих conventions |
| Literal fidelity | pass | Информационный текст и текст ошибки совпадают с prepared source evidence |
| One-file limit | pass | Проверяется только наблюдаемое «не более одного имени»; replace/reject/message не выдуманы |
| Atomicity | pass | Каждый кейс имеет одно действие/группу однотипных значений и один основной oracle |
| Исполнимость | pass | Предусловия, fixtures, шаги и наблюдаемые результаты заданы явно |
| Contamination | pass | V6/V7 drafts, production baselines, UI evidence и пользовательские untracked материалы не использованы как requirements evidence |

## Residual Risk

- `GAP-QUT-001` остаётся открытым: точная граница 40 МБ появится только после source-backed уточнения byte convention.
- В проекте пока нет отдельной CLI-команды для post-hoc promotion уже принятого terminal cycle. Для первого контролируемого promotion допустима только явно разрешённая атомарная публикация проверенного draft с повторной сверкой hash; отдельный post-hoc promotion command следует добавить в следующей итерации.
