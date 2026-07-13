# Performance Analysis V3

## Итог

V3 впервые достиг semantic acceptance: 13/13 obligations покрыты, findings отсутствуют. Token efficiency и reviewer latency улучшились, но общий duration всё ещё на 4.532 s выше цели.

## Сравнение

| Метрика | V1 | V2 | V3 | V3 vs V1 | V3 vs V2 | Target | V3 result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Writer duration | 65,594 ms | 69,890 ms | 86,969 ms | +32.59% | +24.44% | - | bottleneck |
| Reviewer duration | 43,219 ms | 59,875 ms | 37,563 ms | -13.09% | -37.26% | - | improved |
| Stage duration total | 108,813 ms | 129,765 ms | 124,532 ms | +14.45% | -4.03% | <120,000 ms | fail by 4,532 ms |
| Total tokens | 55,198 | 58,989 | 59,451 | +7.70% | +0.78% | - | observation |
| Uncached input tokens | 49,970 | 53,173 | 40,434 | -19.08% | -23.96% | - | improved |
| Uncached tokens / OBL | 3,843.85 | 4,090.23 | 3,110.31 | -19.08% | -23.96% | <8,000 | pass |
| Validator invocations | n/a | 1 | 1 | n/a | 0 | <=1 | pass |
| Orchestration overhead | n/a | 1.55% | 1.48% | n/a | -0.07 pp | <=15% | pass |
| Reviewer result | 11/13 | 11/13 | 13/13 | +2 covered | +2 covered | 13/13 | pass |

## Выводы

- Quality improvement подтверждён независимым reviewer, а не только deterministic gate.
- V3 reviewer использовал 13,568 cached input tokens; uncached input снизился на 12,739 tokens относительно V2.
- Runner orchestration занимает 1,873 ms из 126,405 ms и не является значимым bottleneck.
- Writer потратил 86,969 ms и снова развернул полный dictionary list своими словами до runner-owned projection. В draft присутствуют и writer-rendered values, и deterministic projection block; это следующий проверяемый источник лишнего output/context.
- Один duration sample недостаточен для вывода о стабильной задержке модели: три runs дали 108.8 / 129.8 / 124.5 s при одинаковом масштабе. Следующий benchmark должен оценивать median, а не принимать архитектурное решение по одному шумному измерению.
