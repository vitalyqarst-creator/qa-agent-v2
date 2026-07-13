# Search Clear Context V2 Pre-Live Authorization

## Решение

`AUTHORIZED — exactly one fresh writer/reviewer dispatcher after this authorization is pushed`

## Выполненные Условия

- Checkpoint `b1ff0bdbd5617659c13c286fb3fe33fcb53cc9a3` is pushed; local and `origin/audit/application-card-personal-data-iteration` match.
- V2 package digest is `b7deab9b345a83cb038db6ea504dcf0b4a4e23ac98c5e01429c425f9632d1c24`.
- V2 is `standard-required` with `dependency-state`; four obligations preserve `BSR 32` in structured source refs.
- Validate-only passed with one read-only structured writer, zero writer commands and one fresh reviewer.
- Exec capability is verified; contract v2; fallback disabled.
- `108` clean targeted tests passed; H47/H48/H49 validators have zero errors and warnings.
- Rejected V1 package is immutable audit evidence and is not authorized.
- Promotion target is absent; section 4.2 and protected personal-data baseline hashes match pre-live evidence.

## Разрешённая Команда

- Exactly one invocation of `scripts/review_cycle_backend_dispatcher.py`.
- Config: `work/stage-handoffs/49-search-clear-context-exec-benchmark-iteration/dispatcher-config.v2.json`.
- Backend: explicit `exec`; no SDK fallback.
- Expected sessions: one fresh structured standard writer and, only after deterministic gates pass, one fresh structured semantic reviewer.

## Stop Rule

After this authorization commit is pushed, one dispatcher is allowed. Any process, timeout, contract, source-traceability, command/evidence-access, deterministic-gate, semantic-review or production-boundary blocker is terminal. Do not retry, resume, rebind, switch transport, use assisted mode, recompile, manually sign off or promote.
