# V8 Pre-live Stop Gate

## Текущий статус

`blocked-input` до checkpoint/push и отдельной авторизации.

## Уже выполнено

- V7 не изменён и не возобновлялся.
- Reviewer schema связывает verdict с фактическим `coverage_status` на transport-уровне; parser check сохранён.
- `DICT-001` передаётся reviewer как structured `active_values`.
- Targeted splice мигрирует только `package_id`, отдельно доказывая byte и normalized-semantic preservation.
- Source-backed repair set содержит ровно 13 TC; `F-002` исключён.
- Compile, validate-only, capacity, regression и exec dry-run прошли.
- Baseline неизменён; production shadow отсутствует.

## Условия снятия gate

1. Зафиксировать и отправить pre-live checkpoint с кодом, тестами, H45 compiler inputs и immutable V8 package.
2. Проверить совпадение local/remote commit SHA и отсутствие staged/user-owned contamination.
3. Отдельным последующим артефактом записать authorizing commit SHA, package digest и разрешение ровно на один dispatcher.

## После снятия gate

Разрешён один `review_cycle_backend_dispatcher.py --backend exec` с `dispatcher-config.v8.json`. Любой live blocker терминален; повтор, resume, SDK fallback, ручной sign-off или promotion запрещены.
