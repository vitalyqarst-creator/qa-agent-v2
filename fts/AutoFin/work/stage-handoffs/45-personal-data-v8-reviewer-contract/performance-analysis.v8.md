# V8 Performance Analysis

## Метрики

| stage | duration | input tokens | output tokens | total tokens |
| --- | ---: | ---: | ---: | ---: |
| targeted writer, 13 TC | 93.750 s | 30,875 | 4,840 | 35,715 |
| full reviewer, 65 OBL | 94.875 s | 42,959 | 4,863 | 47,822 |
| total | 188.625 s | 73,834 uncached | 9,703 | 83,537 |

Обе сессии выполнили `0` commands и `0` file changes. Validator invocation budget: `1 / 5`.

## Оценка

Targeted writer масштабировался предсказуемо и исправил 13 секций за одну bounded session. Основная потеря времени и токенов возникла не из-за writer, а из-за позднего semantic transport defect в DICT projection: после 83,537 токенов reviewer получил неправильный массив значений.

Следующая оптимизация должна убрать повтор writer для неизменяемого source-correct draft. После исправления DICT transport нужен reviewer-only recovery в новом immutable cycle с повтором deterministic gates, а не регенерация 47 TC и не фиктивный targeted repair.
