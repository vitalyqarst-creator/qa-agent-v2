# Pre-Live Stop Gate: V5

## Default decision

`STOP - not-authorized-before-checkpoint`

## Required conditions

- 128 compiler/runner tests pass.
- H41 environment-bound fixtures are rejected before package write.
- V5 preserves 42 atoms, 65 obligations, 47 unique `TC-ACPD-001..047`, `GAP-001..003` and `DICT-001`.
- Portable fixture definitions are carried into compiled evidence.
- Package digest/hashes, seed order and validate-only context gates pass.
- Verified exec is selected with no SDK fallback.
- V4r1 and FT-first baseline are unchanged; production shadow is absent.
- Pre-live checkpoint is committed.

## Live limit

After authorization run exactly one V5 dispatcher. Stop on any writer, deterministic gate, reviewer or runtime blocker. No retry, SDK fallback, promotion, overwrite, V4r1 mutation or manual draft copy.
