# Performance Analysis V6

## Итог

V6 transfer-canary завершился за `77 266 ms` stage time (`83 297 ms` dispatcher wall): один writer и один independent reviewer, оба без команд и file changes. Reviewer принял 11/11 obligations. Это быстрее V5, но scopes различаются, поэтому устойчивое ускорение и чистый causal effect одним запуском не доказаны.

## Сравнение С V5

| metric | V5 accepted | V6 accepted | change |
| --- | ---: | ---: | ---: |
| writer duration | 72 687 ms | 54 469 ms | -25,06% |
| reviewer duration | 29 204 ms | 22 797 ms | -21,94% |
| total stage duration | 101 891 ms | 77 266 ms | -24,17% |
| dispatcher wall | 108 030 ms | 83 297 ms | -22,89% |
| total tokens | 57 771 | 47 740 | -17,36% |
| uncached input tokens | 53 028 | 44 210 | -16,63% |
| uncached tokens / obligation | 4 079,08 | 4 019,09 | -1,47% |
| repo prompt bytes | 99 607 | 55 077 | -44,71% |
| primary context bytes | 108 524 | 63 994 | -41,03% |
| input artifact bytes | 324 634 | 160 711 | -50,50% |

## Нормализация По Размеру Scope

- prompt bytes / obligation: `7 662,08` → `5 007,00`, снижение `34,65%`;
- primary context bytes / obligation: `8 348,00` → `5 817,64`, снижение `30,31%`;
- uncached input tokens / obligation: только `-1,47%`.

Это подтверждает, что repository payload действительно уменьшен, но backend bootstrap/system context не имеет section attribution и почти поглощает выигрыш в token efficiency. Нельзя выдавать `44,71%` сокращения prompt bytes за такое же сокращение всех model tokens.

## Context Projection

- writer: package context `14 806` → `9 541` bytes, удалено `5 265`;
- reviewer: package context `14 806` → `9 541` bytes, удалено `5 265`;
- удалён только нерелевантный DaData H2 block; `О/Р`, obligations, oracles и fixtures сохранены;
- релевантность reviewer вычислена по полному evidence до reviewer truncation;
- prompt содержит только marker `DaData package notes: not applicable`, не удалённый content.

## Вывод

Guarded projection полезна и переносима на новый scope. Следующий приоритет — не дополнительное сокращение контекста, а source-to-package fidelity: V6 показал, что downstream reviewer может принять корректно переданный, но недостаточно строго сформированный upstream oracle.
