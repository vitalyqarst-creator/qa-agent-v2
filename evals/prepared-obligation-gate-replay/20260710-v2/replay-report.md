# Prepared obligation gate v2 replay

## Итог

Оба ранее сохранённых immutable draft повторно проверены новым `prepared-package-obligation-gate-v2` без изменения исходных cycle artifacts.

| artifact | draft SHA-256 | TC | testable covered | findings | result |
| --- | --- | ---: | ---: | ---: | --- |
| benchmark-01 blocker | `a7721991ddfeebe7a3070a685cc7f634f403edb0353df48fdfeed78f19ec76e3` | 3 | 3/3 | 0 | passed |
| canary-v4 | `7c68a6b593b191231cc13e5d28e02c5f13ddcd73909d22da71cd9f2d81dc308b` | 3 | 3/3 | 0 | passed |

Оба draft использовали один immutable obligations artifact: `af98598a32b1a207c660f2d7e544aa2c5bfdc9e49737b3eb4d8a668c120f065a`.

Set-level `ATOM-PREP-004` больше не приписывается последнему `TC-PREP-003`. Ложноположительный blocker воспроизведён на v1 evidence и устранён на v2 parser-е.
