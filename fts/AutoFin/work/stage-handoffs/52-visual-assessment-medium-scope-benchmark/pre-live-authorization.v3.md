# Visual Assessment Medium-Scope Benchmark V3 — Pre-Live Authorization

## Authorization

- status: `authorized-once-final-iteration-live`
- authorized_at_utc: `2026-07-13T17:45:14Z`
- user_instruction: `Выполняй запланированную итерацию`
- checkpoint_sha: `7e1c6ae0bd3095302685aabb9958fdb62b2be8f7`
- checkpoint_remote_ref: `origin/audit/application-card-personal-data-iteration`
- checkpoint_remote_match: `yes`
- package_version: `7`
- package_id: `visual-assessment-medium-scope-benchmark-v3`
- package_digest: `d949590e68181f7c4a7ac5962e99b90bb6fb998748dccceff36ef8c20061a346`
- input_fingerprint: `56628223343eb6e9dedab5cdd98b6af336112fdc36d7035b94a7b4508cd5c85f`
- stage_package_sha256: `4153423b990b16bfcf04bfd3c5d9b957215ca7d64cd12e4b6e360a860317b795`
- atomic_obligations_sha256: `6018768ac6212111d9185bf446bf43130409c661b4c69f65f7b9a2e2b95eb8a4`
- dispatcher_config: `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/dispatcher-config.v3.json`
- dispatcher_config_sha256: `381fe8b87992f0ceb28db2d478e2b140e4d8b2351c476387c3fb5ee1152d7f8f`
- protected_visual_assessment_sha256: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`
- protected_personal_data_sha256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`
- protected_section_4_2_sha256: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`
- invocation_budget: `1`
- further_live_budget_this_iteration: `0`

## Разрешено

- После push этого authorization-коммита выполнить один fresh V3 writer и, при проходе deterministic gates, один fresh reviewer через один exec dispatcher invocation.
- Сохранить runner-owned evidence, metrics и terminal comparison handoff.

## Запрещено

- Любое изменение code/package/config после authorization.
- Retry, resume, rebind, repair, assisted mode, sharding, SDK fallback или transport switch.
- Promotion или изменение FT-first baseline.
- Любой следующий live-запуск в этой итерации.

## Terminal Rule

Первый V3 dispatcher invocation расходует последнюю live authorization независимо от результата. Любой следующий defect переносится в новую итерацию.
