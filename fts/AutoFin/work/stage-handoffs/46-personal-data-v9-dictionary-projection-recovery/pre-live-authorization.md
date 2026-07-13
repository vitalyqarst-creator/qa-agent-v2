# V9 Pre-Live Authorization

## Решение

`AUTHORIZED — exactly one reviewer-only dispatcher`

## Выполненные условия

- Compiler-owned `DICT-001 active_values` равны `['Мужчина', 'Женщина']`; empty, punctuation-only и malformed payload блокируются.
- V8 draft hash-bound по SHA-256 `cd8cf5c8ab9cedfe5d2358e9f13a1341d12eb8805f62430f6fee63aabd8f5884`.
- Rebind меняет только per-TC `package_id`; semantic preservation доказан для всех `47` TC.
- Writer LLM отключён; разрешена одна fresh reviewer session после полного deterministic gate bundle.
- Regression: `196 passed`; H46 validator: `0 errors / 0 warnings`.
- Dispatcher dry-run выбрал verified `exec`, contract v2, fallback `false`.
- V9 live attempts и production shadow отсутствуют.
- FT-first baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.

## Checkpoint

- Commit: `7b0743f5a23e594e574994ccb9ffd5a86140eccc`.
- Local и `origin/audit/application-card-personal-data-iteration` совпали.
- Package digest: `81a3f3ae32d77fcd8109a897f989b2db5153cbc0c07a7f43c8940e9863c61003`.
- Reviewer rebind plan digest: `04ab3c97076b4bf4ef68bc5cbff741b7553e19b8a2b6b691063aa6e8913f078f`.

## Stop rule

После push этой авторизации разрешён ровно один V9 dispatcher с `dispatcher-config.v9.json`. Любой process, contract, rebind, metadata, semantic-preservation, deterministic-gate, reviewer или production-boundary blocker терминален без retry/resume, смены transport, fallback, recompile, ручного sign-off, promotion или изменения FT-first baseline.
