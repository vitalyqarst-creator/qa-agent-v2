# Отчёт о conditional-state canary

## Итог

- Cycle: `visual-assessment-conditional-shadow-v1-20260713`.
- Context profile: `conditional-state`.
- Runner status: `accepted-not-promoted`.
- Release classification: `runner-accepted-release-blocked`.
- Production baseline не создан и не изменён.

Пять state-transition cases получились атомарными, исполнимыми и без semantic overlap. `GAP-COND-001` сохранён отдельной gap-obligation без выдуманного negative feedback. Однако все пять TC потеряли обязательные `SRC-*`, `BSR 312–317` и dictionary refs. Поэтому canary не считается quality pass.

## Performance

| показатель | conditional V1 | numeric V2 | character V4 |
| --- | ---: | ---: | ---: |
| duration, ms | 56985 | 58062 | 84469 |
| total tokens | 54721 | 60295 | 56267 |
| uncached input tokens | 52709 | 57814 | 52374 |
| primary context, bytes | 97048 | 108176 | 95302 |
| testable obligations | 5 | 5 | 12 |
| uncached / obligation | 10541.8 | 11562.8 | 4364.5 |
| commands / file changes | 0 / 0 | 0 / 0 | 0 / 0 |

Performance thresholds пройдены. Fixed overhead для пяти-case packages остаётся высоким, но это не blocker. Blocker — false acceptance трассировки.

## Controlled rollout decision

Трёх profile canaries пока недостаточно для rollout:

- character profile: quality/performance pass;
- numeric profile: quality/performance pass;
- conditional profile: performance pass, quality fail из-за gate blind spot.

Следующий live запрещён до deterministic source-ref gate и regression tests.
