# V5 Pre-Live Test Report

- Focused/full compiler-runner regression: 128 passed.
- H41 environment-bound fixture guard: blocked before package write with `environment-bound-fixture`.
- V5 package: 42 atoms, 65 obligations, 47 unique planned TC, `GAP-001..003`, `DICT-001`.
- Portable fixture definitions are embedded once in `source-evidence.md`; no unresolved `FIX-*` reference remains.
- Source evidence: 48 715 / 49 152 bytes.
- Validate-only: pass; writer context 100 811 / 131 072 bytes; no attempts created.
- Dispatcher dry-run: verified `exec`, contract v2, no SDK fallback.
- V4r1 and production baseline: unchanged; production shadow: absent.

Decision: ready for checkpoint; live remains unauthorized until the checkpoint commit exists.
