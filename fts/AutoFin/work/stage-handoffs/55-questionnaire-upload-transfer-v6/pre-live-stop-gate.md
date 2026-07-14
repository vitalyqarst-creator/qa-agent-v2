# Pre-Live Stop Gate V6

## Status

`authorized-one-shot`

## До Live Обязательно

- focused/full agent tests and artifact validator pass;
- architecture audit has 0 findings;
- current-source package compile, validate-only and exec dry-run pass;
- generic reference-only regression proves no invented fixture values;
- protected baselines and absent V6 target confirmed;
- offline checkpoint committed and pushed; local/origin SHA match;
- separate hash-bound authorization binds package/config/checkpoint and one invocation.

## Запрещено

- live до checkpoint и authorization;
- retry, SDK fallback, repair, rebind, sharding or promotion;
- manual benchmark draft edits;
- any production test-case write.

## Current Gate

Offline gates подтверждены в `pre-live-test-report.v6.md`. Checkpoint `5135c023f51253fb8dce992b0396942e3e7a37d2` отправлен, local/origin SHA совпали, а `pre-live-authorization.v6.md` связал immutable package/config с одним invocation. Live разрешён ровно один раз; любой terminal result обнуляет budget.
