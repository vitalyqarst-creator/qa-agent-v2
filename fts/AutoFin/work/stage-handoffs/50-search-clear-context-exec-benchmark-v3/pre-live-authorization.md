# Search Clear Context V3 Pre-Live Authorization

## Authorization

- status: `authorized-once`
- authorized_at_utc: `2026-07-13T13:49:53Z`
- user_instruction: `Выполняй v3`
- checkpoint_sha: `934fb893f56123539e7b811f771284f0dd8e19b8`
- checkpoint_remote_ref: `origin/audit/application-card-personal-data-iteration`
- checkpoint_remote_match: `yes`
- package_id: `search-clear-context-exec-benchmark-v3`
- package_digest: `880e4ec00bd6f3cb6e2d04dde04967beab2387c541ef3bead3da3acfe827895d`
- dispatcher_config: `fts/AutoFin/work/stage-handoffs/50-search-clear-context-exec-benchmark-v3/dispatcher-config.v3.json`
- invocation_budget: `1`

## Разрешено

- После push этого authorization-коммита выполнить ровно один dispatcher invocation с backend `exec`.
- Запустить один fresh structured writer и, только если writer gates пройдены, один fresh semantic reviewer.
- Сохранить runner-owned V3 evidence и terminal handoff.

## Запрещено

- Retry, resume, rebind or second invocation for V3.
- SDK fallback or assisted writer mode.
- Использование V2 draft как requirement evidence.
- Promotion или изменение FT-first baseline.

## Terminal Rule

Authorization consumed by the first dispatcher invocation regardless of its outcome. Any configuration, transport, deterministic, semantic, evidence-access or production-boundary blocker closes V3 as terminal evidence.
