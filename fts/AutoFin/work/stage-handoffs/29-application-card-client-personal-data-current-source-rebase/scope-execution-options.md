# Scope Execution Options

## Рекомендация

1. Выполнить отдельный `scope_gap_review` по текущему handoff.
2. После passed verdict запустить новый writer/reviewer cycle в режиме `rebuild-from-scope` с delta reuse historical canonical file.
3. Не продолжать исторический signed-off cycle и не редактировать его snapshots.

## Допустимые варианты

| option | use_when | result |
| --- | --- | --- |
| `scope-gap-review-then-iteration` | рекомендовано | current-source reviewer gate, затем полный loop |
| `writer-only` | только для диагностики draft | без sign-off |
| `stop-for-clarification` | если reviewer повысит gap до blocking | workflow `blocked-input` |

## Запрещено

- считать historical `signed-off` текущим sign-off;
- копировать старые `BSR 39–69` mappings;
- тихо удалять новые `TC-ACPD-014/015` или принимать их без review;
- превращать calibration candidates в regression-ready cases без source/UI evidence.
