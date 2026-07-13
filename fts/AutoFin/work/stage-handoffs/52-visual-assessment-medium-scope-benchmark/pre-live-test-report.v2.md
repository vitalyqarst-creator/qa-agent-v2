# Visual Assessment Medium-Scope Benchmark V2 — Pre-Live Test Report

## Результат

`PASS — live запрещён до checkpoint push и отдельной hash-bound authorization`

## Scope И Package

- Scope: тот же полный current-source блок `Визуальная информация` и Appendix 1, что и в V1.
- Current anchors: `BSR 311`-`BSR 317`, XHTML rows 182-184, PDF pp.34/40-41.
- Package: `visual-assessment-medium-scope-benchmark-v2`, version `7`.
- Package digest: `1bfc73af25743222eefb336d8408d1d7593ff96f370ee3feb2f4e0e859e3ba01`.
- Input fingerprint: `ce50c8b1b5051f032c56915e75831bcfe7ec7ac4790b62f85828867af99eda4b`.
- Stage-package SHA-256: `ce30bb3e60e7722282eaf0f7e8ab0da2e19fed80128d5cc760a894daa1d54776`.
- Atomic-obligations SHA-256: `8f337e9684acc2a63bcda3c55a74cbfe9832e87709bf9d701fedfbeed1c95960`.
- Route: `standard-required`; unsupported dimensions: `dependency-state`, `evidence-qualified-ui-calibration`.
- Size: `13` obligations, `12` unique planned TC, `9` dictionary references, `0` active gaps.

## Исправляемые V1 Инварианты

- `OBL-006` требует полную иерархию `DICT-001`: `47` значений.
- `OBL-007` требует полный набор leaf-значений: `39` значений.
- `OBL-008` и `OBL-010` имеют `calibration_status = ui-calibration-required` без искусственного `GAP-*`.
- Негативные мутации подтверждают, что потеря dictionary values или calibration markers блокируется до semantic sign-off.

## Source Identity

- DOCX SHA-256: `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b`.
- XHTML SHA-256: `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66`.
- PDF SHA-256: `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58`.

## Validate-Only

- Runtime identity: pass; current runner validates version/id/digest/fingerprint from the immutable package.
- Writer: structured and runner-materialized; effective command budget `0`; LLM required.
- Writer context: `50,025 / 131,072` bytes, pass.
- Writer output capacity: `12` TC / `13` obligations, one session, limit `12`, pass.
- Observable-oracle preflight: `13` checked, `0` findings, pass.
- Reviewer output capacity: `13 / 100` obligations, pass.
- Target absent; validate-only created no cycle attempt.

## Backend Dry-Run

- Backend requested/selected: `exec` / `exec`.
- Contract version: `2`.
- Capability: available and verified; missing flags: none.
- SDK fallback: `false`.
- Dispatcher-config SHA-256: `4053b05b316e471245123061ea5a65c76982ce4536769ec26e7d0311ee94d8d7`.

## Regression And Architecture Evidence

- Full agent-layer suite: `460 passed`, `1 skipped`.
- Focused prepared/compiler/runner/backend suite: `242 passed`.
- Architecture audit: `7` skills, `61` checks, `0` findings; all instruction budgets pass.
- Six dictionary/calibration negative-mutation regressions: pass.
- Full repository suite before the bounded runtime-profile edit: pass, including all `7/7` artifact-validator shards.
- Runtime-profile regression is included in the post-edit agent-layer run.
- Restored `ui-evidence-policy` fixture and isolated diagnostic output were committed and pushed as `f91b476` before V2 preparation.

## Production Boundary

- Existing visual-assessment baseline SHA-256: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`.
- Protected personal-data baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.
- Protected section 4.2 baseline SHA-256: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`.
- Promotion target `section-18-visual-assessment-medium-scope-benchmark.md`: absent.

## Benchmark Targets

- Exactly one fresh structured writer and one fresh semantic reviewer through one dispatcher invocation.
- No retry, resume, rebind, repair, assisted mode, sharding, SDK fallback or promotion.
- Stage duration: `< 120 s`.
- Uncached input efficiency: `< 8,000 tokens / obligation`.
- Validator invocations: `<= 1`.
- Orchestration overhead: `<= 15%` of runner wall time.

## Stop Conditions

- Any package identity, transport, deterministic, semantic, evidence-access or production-boundary blocker is terminal for V2.
- A second live cycle requires a separate evidence-backed fix, checkpoint and authorization; it is not implied by this report.
