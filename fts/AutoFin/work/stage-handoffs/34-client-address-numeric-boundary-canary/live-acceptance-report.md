# Отчёт о numeric boundary canary

## Результат

- Cycle: `client-address-numeric-boundary-shadow-v2-20260713`.
- Профиль: `numeric-date-boundary`.
- Статус: `accepted-not-promoted`.
- Draft SHA-256: `1403dec17ce4ca223568c4111d7962845a808aadba98ad1a73cda859fb88f2f8`.
- Пять testable obligations покрыты пятью отдельными позитивными TC.
- `OBL-NUM-006` сохранил `GAP-NUM-001`; неподтверждённая реакция на неверный формат не превратилась в negative TC.
- Reviewer принял draft без blocking findings.

## Качество draft

- Названия уникальны и называют конкретное поле и проверяемое допустимое значение.
- Почтовые индексы проверяются на source-backed допустимом значении ровно из 6 цифр.
- Корпус и квартиры не получают выдуманного ограничения длины.
- Поведение для невалидных символов, длины, фильтрации и блокировки явно остаётся gap.
- Семантических пересечений нет; obligation gate и quality bundle прошли.

## Производительность

| показатель | результат | stop-gate |
| --- | ---: | ---: |
| duration | 58062 ms | <= 180000 ms |
| total tokens | 60295 | informational |
| uncached input tokens | 57814 | <= 100000 |
| primary context | 108176 bytes | <= 150000 bytes |
| input artifacts | 218191 bytes | informational |
| commands | 0 | 0 |
| file changes | 0 | 0 |
| uncached / testable obligation | 11562.8 | informational |

Абсолютные thresholds пройдены. Удельная стоимость выше V4 character canary (`4364.5` uncached tokens/obligation), потому что fixed writer/reviewer overhead распределяется только на пять obligations. Это не quality blocker, но следующий benchmark не следует делать ещё меньше.

## Preflight finding v1

Первый immutable package v1 не запускался live. Его constraint gaps на положительных obligations выбрали `character-restriction-calibration` и подготовили бы негативные calibration cases. Stop-gate сработал до запуска. В v2 отрицательная неопределённость оформлена отдельной gap-obligation, поэтому выбран корректный `numeric-date-boundary` профиль и положительные TC не искажены.

## Ограничения результата

- Canary подтверждает только формирование исполнимых позитивных TC по допустимым numeric values.
- Он не доказывает фактическую реакцию UI на невалидные значения и не закрывает `GAP-NUM-001`.
- Draft не является production baseline и не должен продвигаться без отдельного решения.
