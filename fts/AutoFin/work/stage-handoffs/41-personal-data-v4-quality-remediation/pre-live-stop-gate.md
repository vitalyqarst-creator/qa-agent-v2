# Pre-live Stop Gate: V4

## Default decision

`STOP - not-authorized`

## Required conditions

- V3-shaped bad fixture is rejected with all three expected categories.
- Corrected calibration-aware fixture passes.
- Original handoff 38 compiler input is rejected by the new guard for the observed defect class.
- V4 remediated compiler input produces 42 atoms, 65 obligations and 47 planned TC.
- `GAP-001..003`, `DICT-001` and exact `TC-ACPD-001..047` order are preserved.
- Relevant compiler/runner regression passes.
- Writer and reviewer contexts fit their limits.
- V1/V2/V3/handoff38 tree hashes are unchanged and production target is absent.
- Pre-live checkpoint is committed.

## Live limit

After authorization, run exactly one verified-exec V4 dispatcher. No SDK fallback, promotion, overwrite, retry or V3 reuse.
