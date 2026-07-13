# Visual Assessment Medium-Scope Benchmark — Pre-Live Authorization

## Authorization

- status: `authorized-once`
- authorized_at_utc: `2026-07-13T15:13:00Z`
- user_instruction: `Выполняй предложенный тобой план`
- checkpoint_sha: `ab67a27469a5864f39aed4ab4e1c693f74afa75a`
- checkpoint_remote_ref: `origin/audit/application-card-personal-data-iteration`
- checkpoint_remote_match: `yes`
- package_version: `6`
- package_id: `visual-assessment-medium-scope-benchmark-v1`
- package_digest: `ffb7a7a8a44bd8ee53b76b6f8745fa0c8653eabbdfa7ef20bb0166c592be8d35`
- stage_package_sha256: `0728918306d8bcc6f40fa1cc1517fffebe381a4ab067af6935137f5ba19b65ac`
- atomic_obligations_sha256: `209fd75663b86f9c5a5da7dcbc51599dc70c1e1d64948b471262121b17ce8086`
- dispatcher_config: `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/dispatcher-config.v1.json`
- dispatcher_config_sha256: `ffefad286fe9026c563142b399422f61c6f7e79029961843a7d8103691b210f2`
- protected_visual_assessment_sha256: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`
- protected_personal_data_sha256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`
- protected_section_4_2_sha256: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`
- invocation_budget: `1`

## Разрешено

- После push этого authorization-коммита выполнить ровно один dispatcher invocation с backend `exec`.
- Запустить один fresh structured writer и, только если writer/deterministic gates пройдены, один fresh semantic reviewer.
- Сохранить runner-owned evidence, метрики и terminal handoff.

## Запрещено

- Retry, resume, rebind, targeted repair или второй invocation.
- SDK fallback, assisted writer mode, sharding или transport switch.
- Изменение immutable package/config после authorization.
- Promotion либо изменение любого FT-first baseline.
- Использование предыдущих test cases/review-cycle outputs как requirement evidence.

## Terminal Rule

Authorization consumed by the first dispatcher invocation regardless of outcome. Any configuration, runtime-identity, transport, deterministic, semantic, evidence-access or production-boundary blocker closes this run as terminal benchmark evidence.
