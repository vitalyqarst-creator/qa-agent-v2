# Pre-Live Stop Gate V6

## Status

`offline-gates-pass-checkpoint-pending`

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

Offline gates подтверждены в `pre-live-test-report.v6.md`. Live всё ещё запрещён: checkpoint ещё не создан и не отправлен, authorization artifact отсутствует.
