# V4r1 Pre-Live Test Report

- Bounded eval: V3-shaped fixture rejected with `generic-execution-fixture`, `undefined-execution-action`, `non-observable-expected-result`; corrected fixture accepted.
- Compiler guard: original handoff 38 input rejected at `PLAN-022` before package write.
- Compiler/runner regression: 124 tests, pass in 30.355 seconds.
- V4r1 package: 42 atoms, 65 obligations, 47 planned TC, `GAP-001..003`, `DICT-001`.
- Exact per-TC intent selection: pass for all 11 affected obligations.
- Package manifest/hash verification: pass.
- Writer validate-only: 97 507 / 131 072 bytes, pass; no attempts created.
- Reviewer conservative envelope: 126 150 / 131 072 bytes, pass; exact live gate remains authoritative.
- Dispatcher dry-run: verified exec, contract v2, no fallback.
- V1/V2/V3/handoff38 tree hashes unchanged; production target absent.

The first built V4 package is quarantined as rejected preflight evidence because it predates the exact per-TC compiler mapping fix. Only V4r1 may proceed.
