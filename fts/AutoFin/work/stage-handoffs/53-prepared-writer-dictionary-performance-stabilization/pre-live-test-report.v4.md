# V4 Pre-Live Test Report

## Результат

`PASS — live остаётся запрещён до offline checkpoint push и отдельной hash-bound authorization`

## Bounded Implementation

- Structured obligation transport объявляет `runner_owned_dictionary_materializations` с OBL/TC/DICT, coverage mode и value count.
- Writer-only source evidence сохраняет dictionary identity/source/count, но исключает exact leaf payload.
- `writer-owned-exhaustive-dictionary-values` блокирует повторное перечисление до materialization.
- Runner по-прежнему добавляет полный source-backed hierarchy и выполняет exact completeness gate.
- `reference-only` values и group paths остаются writer-owned.

## Context Comparison

| metric | V3 | V4 validate-only | delta |
| --- | ---: | ---: | ---: |
| writer prompt bytes | 45 710 | 42 664 | -3 046 (-6,66%) |
| writer instruction bytes | 4 409 | 5 198 | +789 |
| writer primary context bytes | 50 119 | 47 862 | -2 257 (-4,50%) |
| raw source evidence bytes | 28 002 | 27 831 | -171 |
| evidence bytes included in writer payload | 28 002 | 23 534 | -4 468 (-15,96%) |

Token/latency improvement is not inferred from bytes; it must be measured in V4 live runs.

## Immutable Packages

Все runs имеют package version/id `7` / `visual-assessment-medium-scope-benchmark-v4`, 13 obligations, 12 planned TC, 9 dictionary refs, 0 gaps и identical atomic obligations SHA-256 `6fd49ada148da93d1ad059988b898eeeca70a00ddf16a7eb0b18748c2eb7bd0f`.

| run | package_digest | input_fingerprint | stage_package_sha256 | config_sha256 |
| --- | --- | --- | --- | --- |
| r1 | `0ef00ba00344229211375efcd280e7c3d2940e68e4f2af248d106c8181cb64ae` | `3bb4ae09be3b241aa119e15b3a62d5d8ecf36d556d579cd14f16e7568aff9871` | `2ccfe07793af816cb2269372cb4594b884038cf87f6a8ccf3bc4f5fefb7c09ab` | `e39c755e666f7c719f69b82b6723aaedd921e31d38e11461cc1f65a30f453142` |
| r2 | `1bb41cc63071aa2fa59ba5b9d24b520670310b064052656103c99567097ce95e` | `3166ea14fab09e0d1c77b7539c1505341c3bff8affc205ff61712aebb3921d29` | `d6bf1bb17b042335991acbc71c5770736dd9668f72b8603098717f040ae923bb` | `b370210c1c02ebc444dd3ad79303c3e5b9d5231fc7cbbffdd8395855cb2bccc8` |
| r3 | `62e44ec2d22aae3a958f3b05e4ddf45ac9d538a9440a30692596566f851ab596` | `b181ba24a67620534dc2c28b3522536db9ea840fc2bdf6a5d856c61d57fb4ce0` | `9b6d231e68fa0412eb4f9881f5aeb470173f33d9d9fe6a2430ade89c416b19d8` | `018eee45c71b81eb1a1c439474dfff73a69f660c4cc48350b041c5d309585aa8` |

Source-evidence file hashes differ only because each file records its fresh cycle-local `source_path`. Embedded compiled fidelity `source_sha256` is identical: `7f87475366a44cd13c3a5b9a342699807e26c29cd3cd66ab6589408320398ddf`.

## Offline Gates

- Focused prepared gate/runner/context suite: 154 passed.
- Full agent-layer: 464 passed, 1 skipped.
- Artifact-validator shards: 7/7 passed, 391 tests total.
- Architecture audit: 61 checks, 0 findings; all instruction budgets pass.
- H53 scoped artifact audit: 0 errors, 0 warnings.
- Three validate-only runs: pass; 13 oracle checks, 0 findings; reviewer capacity 13/100; target absent; no attempts created.
- Three exec capability dry-runs: selected exec, contract v2, verified flags, no fallback.

## Production Boundary

- Visual assessment baseline: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`.
- Personal data baseline: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.
- Section 4.2 baseline: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`.
- Production target `section-18-visual-assessment-medium-scope-benchmark.md`: absent.

## Live Gate

r1 may run only after this package set and implementation are committed, pushed, local/origin SHA equality is verified and an authorization artifact binds that checkpoint. r2/r3 remain conditional on full r1 quality pass.
