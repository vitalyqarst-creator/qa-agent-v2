# Search Clear Context V4 Iteration Summary

## Результат

V4 достиг `accepted-not-promoted`: fresh writer создал четыре атомарных TC, fresh reviewer принял все `4/4` obligations, blocking findings отсутствуют. Production promotion был намеренно отключён.

## Что Исправлено

- Package version больше не дублируется numeric text в runtime profile.
- Writer и reviewer получают одинаковые runner-validated `package_version`, `package_id`, `package_digest`.
- Stale profile и отсутствующий digest блокируются до LLM.
- Все четыре TC доказывают изменённое видимое состояние до `Очистить` и возврат к captured initial state после действия.
- Writer/reviewer работали в разных fresh sessions, без commands, fallback и workspace mutations.

## Что Не Улучшилось

- Токены: `43,535`, что на `1.9%` выше V2.
- Стоимость на obligation: `10,364.5` uncached tokens; fixed context всё ещё доминирует на малом scope.
- V4 не доказывает medium-scope scaling или sharded writer path.

## Значение Для Агента

Теперь доказан нужный end-to-end outcome: immutable requirements package → fresh writer → deterministic gates → fresh reviewer → accepted draft примерно за минуту. Следующая задача — проверить этот процесс на более крупном scope, а не повторять тот же малый benchmark.
