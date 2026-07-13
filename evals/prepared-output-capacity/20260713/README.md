# Prepared writer output-capacity eval

Пара проверяет transport-регрессию, обнаруженную в Personal Data V5: большой structured draft нельзя отправлять в одну live writer-сессию только на основании input-context budget.

- `bad-one-shot.json` — небезопасная конфигурация: полный набор превышает single-session limit, sharding отключён; preflight обязан завершиться до live с `blocked-prepared-writer-output-capacity`.
- `corrected-sharded.json` — исправленная конфигурация: группы `planned_test_case_id` разбиваются на bounded shards; union обязан быть полным, shards — непересекающимися, каждый TC и obligation принадлежит ровно одному shard.

Исполняемые проверки находятся в `tests/test_codex_exec_review_cycle_runner.py` и используют тот же runner contract, что production launch.
