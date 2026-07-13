# Visual Assessment Medium-Scope Benchmark V2 — Pre-Live Authorization

## Authorization

- status: `authorized-once`
- authorized_at_utc: `2026-07-13T17:25:33Z`
- user_instruction: `Выполняй запланированную итерацию`
- checkpoint_sha: `8223d580c3d8157ce69fd721f7988d47ff172f07`
- checkpoint_remote_ref: `origin/audit/application-card-personal-data-iteration`
- checkpoint_remote_match: `yes`
- package_version: `7`
- package_id: `visual-assessment-medium-scope-benchmark-v2`
- package_digest: `1bfc73af25743222eefb336d8408d1d7593ff96f370ee3feb2f4e0e859e3ba01`
- input_fingerprint: `ce50c8b1b5051f032c56915e75831bcfe7ec7ac4790b62f85828867af99eda4b`
- stage_package_sha256: `ce30bb3e60e7722282eaf0f7e8ab0da2e19fed80128d5cc760a894daa1d54776`
- atomic_obligations_sha256: `8f337e9684acc2a63bcda3c55a74cbfe9832e87709bf9d701fedfbeed1c95960`
- dispatcher_config: `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/dispatcher-config.v2.json`
- dispatcher_config_sha256: `4053b05b316e471245123061ea5a65c76982ce4536769ec26e7d0311ee94d8d7`
- protected_visual_assessment_sha256: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`
- protected_personal_data_sha256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`
- protected_section_4_2_sha256: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`
- invocation_budget: `1`

## Разрешено

- После push этого authorization-коммита выполнить ровно один dispatcher invocation с backend `exec` и run profile `benchmark`.
- Запустить один fresh structured writer и, только если writer/deterministic gates пройдены, один fresh semantic reviewer.
- Сохранить runner-owned evidence, метрики и terminal handoff.

## Запрещено

- Retry, resume, rebind, targeted repair, assisted writer mode или второй invocation.
- SDK fallback, sharding или transport switch.
- Изменение immutable package/config/runtime profile после authorization.
- Promotion либо изменение любого FT-first baseline.
- Использование V1 draft/reviewer output как requirement evidence.

## Terminal Rule

Authorization consumed by the first dispatcher invocation regardless of outcome. Any configuration, runtime-identity, transport, deterministic, semantic, evidence-access or production-boundary blocker closes V2 as terminal benchmark evidence.
