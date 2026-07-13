# V3 Pre-Live Stop Gate

Live is authorized only when every condition below passes:

- V3 is a new immutable cycle/package; V1/V2 remain unchanged.
- Package contains 42 atoms, 65 obligations, 47 planned TC, `GAP-001..003` and `DICT-001`.
- Seed order is exactly `TC-ACPD-001..047`.
- Writer validate-only context is at most 131 072 bytes.
- Patched reviewer transport replay is at most 131 072 bytes.
- Targeted runner/compiler tests pass.
- Dispatcher dry-run selects verified exec with no SDK fallback.
- Promotion and overwrite flags are absent.
- Production target is absent and tracked worktree boundary is clean.

After authorization, run exactly one dispatcher live. On any new blocker, preserve evidence and stop; do not retry V3.
