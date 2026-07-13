# Performance Analysis V2

## Итог

V2 повысил полноту prepared execution, но не достиг semantic sign-off и ухудшил длительность. Token efficiency, validator budget и orchestration overhead остались в целевых пределах.

## Сравнение С V1

| Метрика | V1 | V2 | Изменение | Target | V2 result |
| --- | ---: | ---: | ---: | ---: | --- |
| Writer duration | 65,594 ms | 69,890 ms | +6.55% | - | observation |
| Reviewer duration | 43,219 ms | 59,875 ms | +38.54% | - | regression |
| Stage duration total | 108,813 ms | 129,765 ms | +19.26% | <120,000 ms | fail |
| Total tokens | 55,198 | 58,989 | +6.87% | - | observation |
| Uncached input tokens | 49,970 | 53,173 | +6.41% | - | observation |
| Uncached tokens / OBL | 3,843.85 | 4,090.23 | +6.41% | <8,000 | pass |
| Validator invocations | n/a | 1 | n/a | <=1 | pass |
| Orchestration overhead | n/a | 1.55% | n/a | <=15% | pass |
| Reviewer coverage | 11 covered / 2 incorrect | 11 covered / 2 incorrect | old defects replaced by new defects | 13 covered | fail |

## Интерпретация

- V1 blocker `prepared-dictionary-values-not-materialized` закрыт: OBL-006 и OBL-007 reviewer-covered.
- Оба source-backed calibration candidates присутствуют в lifecycle artifact.
- Увеличение input связано с материализованным dictionary payload и новыми deterministic artifacts; оно остаётся далеко ниже token target.
- Основной time regression — reviewer: +16,656 ms. Runner orchestration занимает только 2,047 ms из 131,812 ms, поэтому причина не в Python orchestration.
- V2 не должен продвигаться: два шага неоднозначны для ручного исполнителя.
