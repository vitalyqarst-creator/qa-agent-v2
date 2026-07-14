# V5 Pre-Live Test Report

## Результат

`PASS OFFLINE — live запрещён до pushed checkpoint и отдельной authorization`

## Реализация

- Package version повышена до 8; v1-v7 остаются совместимыми.
- `reference-only.fixture_values` содержит только явно названные plan fixtures.
- Runner seed и post-writer materialization используют один canonical block.
- Gate различает missing и incomplete exact projection.
- Exhaustive dictionary ownership V4 не изменён.

## Regression evidence

- Focused prepared package/compiler/gate/runner/context: 245 passed.
- Full agent-layer: 467 passed, 1 skipped.
- Artifact-validator: 391 passed, 7/7 shards.
- Architecture audit: 61 checks, 0 findings; instruction budgets pass.
- Actual rejected V4-r1 draft: blocked before reviewer only by `reference-fixture-projection-missing`.
- Positive materialization passes; exact-value mutation yields `reference-fixture-projection-incomplete`.

## Immutable package

- Package: `visual-assessment-medium-scope-benchmark-v5`, version 8.
- Obligations / planned TC / dictionary refs / gaps: 13 / 12 / 9 / 0.
- Stage package SHA-256: `3217d9b90906250c817fd467c61c7af5c003f4452d08cc55b19903cf9f33a30e`.
- Package digest: `83ee169e8e5d338f8dfd9cd977d8c3bf2443538b553a47b7365d40d083fe51ab`.
- Input fingerprint: `7c59d70707bc2156c5adc93e8391bff3a55dc4e1e360a82db515149b54913cb3`.
- Atomic obligations SHA-256: `8695ec41e98f02da98e1cb5e6390a534a3d5e5b9abdc07bcc3cf153fd4ffb0e3`.
- Dispatcher config SHA-256: `4bb7736d12cbf8df2cad6ba97916becdc088fdc2db800b24b27b80e49b24ec5e`.
- Exec dry-run: selected/verified contract v2, fallback false; selection SHA-256 `d546e71fc8bb5e6bb67b1b27e0a311bf73ece92db3876e11884a19560cf97638`.
- Validate-only: pass; 13 oracle checks, reviewer capacity 13/100, target absent, cycle artifacts not created.
- OBL-013: group `DICT-101` plus two exact leaf fixtures; `required_values` empty.

## Production boundary

- Visual assessment baseline: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`.
- Personal data baseline: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.
- Section 4.2 baseline: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`.
- Promotion target: absent.
