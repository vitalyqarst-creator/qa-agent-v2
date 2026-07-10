# Prepared writer first-artifact deadline 120 s benchmark

## Итог

- Canary v9: `accepted-not-promoted`.
- Benchmark 1/3: `accepted-not-promoted`.
- Benchmark 2/3: `accepted-not-promoted`.
- Benchmark 3/3: `accepted-not-promoted`.
- Promotion во всех запусках выключен; production test case не создан.

## Результаты

| run | writer first artifact | writer duration | commands | first file event | reviewer |
| --- | ---: | ---: | ---: | --- | ---: |
| canary v9 | `48.969 s` | `56.437 s` | 0 | `add` | `accepted`, `35.469 s` |
| benchmark 1 | `44.766 s` | `113.875 s` | 5 | `add` | `accepted`, `21.110 s` |
| benchmark 2 | `73.734 s` | `91.281 s` | 2 | `add` | `accepted`, `24.266 s` |
| benchmark 3 | `48.500 s` | `131.484 s` | 3 | `add` | `accepted`, `26.781 s` |

## Вывод

Экспериментальный first-artifact deadline `120 s` устранил ложную остановку, наблюдавшуюся при `90 s`, без ослабления остальных guardrails:

- writer hard timeout остался `180 s`;
- post-write idle timeout остался `60 s`;
- first artifact во всех четырёх новых независимых запусках появился до deadline;
- deterministic gates и prepared reviewer приняли каждый draft;
- output ownership соблюдён: draft отсутствовал до writer и создавался первым событием `add`;
- production promotion не выполнялся.

Выборка мала и не доказывает статистический SLA, но достаточна для prototype readiness: canary и benchmark 3/3 прошли без process, evidence-access, package или semantic blocker.

## Readiness

Prepared pipeline можно перевести из `experimental-only` в `prototype-ready` для следующих непроизводственных scope-прогонов. Автоматическую promotion и общий production rollout включать пока не следует; для этого нужна отдельная проверка на реальном новом scope и явное решение о promotion.
