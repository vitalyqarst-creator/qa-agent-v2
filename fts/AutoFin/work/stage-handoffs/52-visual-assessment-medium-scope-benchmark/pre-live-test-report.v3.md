# Visual Assessment Medium-Scope Benchmark V3 — Pre-Live Test Report

## Результат

`PASS — live запрещён до checkpoint push и отдельной hash-bound authorization`

## Bounded Fix

- Compiler finding `dictionary-group-locator-not-preserved` запрещает терять child dictionary locator между `test_data` и executable action.
- Runner finding `ambiguous-execution-action` блокирует альтернативные действия вида `установить или сохранить` до reviewer.
- Runner finding `ambiguous-dictionary-value-path` блокирует дублирующийся label без child group id/name; явная политика `в любой группе` разрешена.
- V3 plan уточняет OBL-005 как одно действие `Выбрать Нет` и OBL-013 как выбор двух значений внутри `Признаки алкоголика (DICT-101)`.

## Package

- Version/id: `7` / `visual-assessment-medium-scope-benchmark-v3`.
- Package digest: `d949590e68181f7c4a7ac5962e99b90bb6fb998748dccceff36ef8c20061a346`.
- Input fingerprint: `56628223343eb6e9dedab5cdd98b6af336112fdc36d7035b94a7b4508cd5c85f`.
- Stage-package SHA-256: `4153423b990b16bfcf04bfd3c5d9b957215ca7d64cd12e4b6e360a860317b795`.
- Atomic-obligations SHA-256: `6018768ac6212111d9185bf446bf43130409c661b4c69f65f7b9a2e2b95eb8a4`.
- Dispatcher-config SHA-256: `381fe8b87992f0ceb28db2d478e2b140e4d8b2351c476387c3fb5ee1152d7f8f`.
- Scope: unchanged 13 obligations / 12 planned TC / 9 dictionary refs / 0 gaps.

## Validate-Only And Tests

- Runtime identity: pass; no numeric package allowlist in writer/reviewer profiles.
- Writer context: `50,119 / 131,072` bytes; output capacity 12 TC / 13 OBL, pass.
- Oracle preflight: 13 checked, 0 findings; reviewer capacity 13/100.
- Target absent; validate-only created no cycle attempt.
- Full agent-layer suite: 462 passed, 1 skipped.
- Focused new positive/negative regressions: 6 passed.
- Architecture audit: 7 skills, 61 checks, 0 findings, all instruction budgets pass.
- Exec dry-run: contract v2, capability verified, no missing flags, SDK fallback false.

## Production Boundary

- Visual-assessment baseline: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`.
- Personal-data baseline: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.
- Section 4.2 baseline: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`.
- Production target: absent.

## Terminal Contract

V3 receives at most one dispatcher invocation and is the last live run of this iteration. Retry, resume, rebind, repair, SDK fallback, sharding and promotion are disabled.
