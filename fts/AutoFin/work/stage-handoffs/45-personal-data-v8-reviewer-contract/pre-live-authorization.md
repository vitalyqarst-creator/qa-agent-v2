# V8 Pre-Live Authorization

## Решение

`AUTHORIZED — exactly one dispatcher`

## Выполненные условия

- Reviewer schema связывает verdict с `coverage_status`; parser validation сохранена.
- Structured DICT projection содержит `DICT-001 active_values`; missing evidence блокирует до reviewer.
- Repair plan содержит ровно 13 source-verified TC и сохраняет остальные 34 TC за исключением runner-owned `package_id` migration.
- Prepared oracle preflight: `65 checked / 0 findings`.
- Writer route: одна fresh read-only targeted-repair session; limit `13`.
- Reviewer route: одна fresh full-set session; `65` obligations в capacity limits.
- Runner + instruction-context: `120 passed`; H45 validator: `0 errors / 0 warnings`.
- Dispatcher dry-run: verified `exec`, contract v2, fallback `false`.
- V8 attempts и production shadow отсутствуют.
- FT-first baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.

## Checkpoint

- Commit: `fc03115f610fe3361a59dee635cb1ab8b1d51365`.
- Local и `origin/audit/application-card-personal-data-iteration` совпали.
- Package digest: `3ac15bc3d846e71f5a8b5bf6fccb2f937b98c277b3570659ed0c9b80ec1a2ea7`.
- Repair plan digest: `80fbb773372e037e4cdb3455af920791263f8430c23eba925273e588833648f6`.

## Stop rule

После push этой авторизации разрешён ровно один V8 dispatcher с `dispatcher-config.v8.json`. Любой process, contract, repair, metadata, splice, full-set, reviewer или production-boundary blocker терминален без retry/resume, смены transport, recompile, ручного sign-off или изменения FT-first baseline.
