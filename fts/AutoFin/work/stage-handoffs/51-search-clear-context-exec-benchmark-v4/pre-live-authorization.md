# Search Clear Context V4 Pre-Live Authorization

## Authorization

- status: `authorized-once`
- authorized_at_utc: `2026-07-13T14:23:53Z`
- user_instruction: `Продолжай`
- checkpoint_sha: `40641ad3c45f7bd9ca51aab7bf4d34aa469616ba`
- checkpoint_remote_ref: `origin/audit/application-card-personal-data-iteration`
- checkpoint_remote_match: `yes`
- package_id: `search-clear-context-exec-benchmark-v4`
- package_digest: `5a11807225be6671176d35bc2cc2a30656d6fe1692e67a97b6ecb2076ea9f97f`
- dispatcher_config: `fts/AutoFin/work/stage-handoffs/51-search-clear-context-exec-benchmark-v4/dispatcher-config.v4.json`
- invocation_budget: `1`

## Разрешено

- После push этого authorization-коммита выполнить ровно один dispatcher invocation с backend `exec`.
- Запустить один fresh structured writer и, только если writer gates пройдены, один fresh semantic reviewer.
- Сохранить runner-owned V4 evidence и terminal handoff.

## Запрещено

- Retry, resume, rebind or second invocation for V4.
- SDK fallback, assisted writer mode or transport switch.
- Изменение immutable V4 package, V3 evidence, FT-first baseline или promotion target.
- Использование V2/V3 draft как requirement evidence.

## Terminal Rule

Authorization consumed by the first dispatcher invocation regardless of outcome. Any configuration, runtime-identity, transport, deterministic, semantic, evidence-access or production-boundary blocker closes V4 as terminal evidence.
