# Prepared reviewer benchmark v2: semantic blocker

## Итог

- Цикл 1 завершился со статусом `changes-required`.
- Runtime-исправление подтверждено: writer и reviewer завершились без hard/idle timeout.
- Reviewer работал в отдельной read-only ephemeral-сессии, выполнил `0` команд и прошёл evidence-access gate.
- Benchmark-циклы 2 и 3 не запускались: первый цикл выявил воспроизводимо объяснимый дефект prepared obligations, который нельзя маскировать повторными удачными verdict.
- Promotion выключен; production test case не создан.

## Метрики цикла 1

| показатель | результат |
| --- | ---: |
| writer session | `019f4c23-dacd-73b3-a39d-cbd71a60cd18` |
| writer first meaningful artifact | `83.860 s` |
| writer duration | `114.250 s` |
| writer commands | `3 / 8` |
| reviewer session | `019f4c25-9a66-7400-b78c-c003e995eb76` |
| reviewer duration | `49.375 s` |
| reviewer termination | `completed` |
| reviewer idle timeout | `false` |
| reviewer commands | `0 / 1` |
| reviewer evidence-access | `passed` |
| draft SHA-256 | `f9a4001166507ad6801872ead72d9fd85c55881bfdcf3a14ac8fbc5a514c62b5` |

## Реальный blocker

`ATOM-PREP-001` и `ATOM-PREP-002` не атомарны. Каждый объединяет два независимо проверяемых свойства:

1. доступные значения происходят из справочника;
2. виджет допускает соответственно один или несколько одновременных выборов.

Draft наблюдаемо проверяет только кратность выбора. Происхождение значений из справочника указано как предусловие и тестовые данные, но не сравнивается с независимым подтверждённым oracle. Поэтому трассировка текущих `TC-PREP-001` и `TC-PREP-002` на составные атомы заявляет более полное покрытие, чем фактически выполняется.

Finding reviewer обоснован и соответствует глобальному правилу проекта: один код/statement нельзя считать одной проверкой, если он содержит несколько независимых обязанностей системы.

## Почему deterministic obligation gate не остановил writer

Gate v2 корректно проверяет Markdown-границы и наличие traceability ids, но не выполняет semantic decomposition составного atomic statement. Он подтвердил номинальное `3/3` покрытие testable ids; semantic reviewer обнаружил, что два id были подготовлены недостаточно атомарно. Это не regression obligation gate v2, а дефект upstream prepared-obligation design.

## Следующая узкая итерация

Рекомендуемое разложение:

| новая обязанность | статус до появления независимого oracle |
| --- | --- |
| значения обычного списка происходят из справочника | `gap` |
| обычный список допускает только один одновременный выбор | `testable` |
| значения списка с множественным выбором происходят из справочника | `gap` |
| список с множественным выбором допускает несколько одновременных выборов | `testable` |
| начальное значение отсутствует | `testable` |
| отсутствующее значение интерпретируется как NULL | `gap` |

Для двух source-origin обязанностей допустимы только два честных пути:

- предоставить runtime fixture/dictionary inventory с независимым ожидаемым составом и сделать отдельные тест-кейсы;
- сохранить их как gaps и не приписывать существующим кейсам кратности выбора.

После обновления prepared package нужно повторить один canary и затем заново начать benchmark из трёх независимых циклов.

## Readiness

Статус остаётся `experimental-only`. Reviewer hard-deadline policy готова к дальнейшим прогонам, но prepared-obligation preparation ещё не обеспечивает стабильную атомарную трассировку.
