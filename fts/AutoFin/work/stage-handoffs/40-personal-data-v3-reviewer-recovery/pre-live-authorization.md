# V3 Pre-Live Authorization

Decision: `AUTHORIZED — exactly one dispatcher live`.

Evidence:

- immutable V3 package only; V1/V2 tracked diff = 0;
- 42 atoms, 65 obligations, 47 planned TC, `GAP-001..003`, `DICT-001`;
- package and compiler-input hashes verified;
- seed is exact and unique `TC-ACPD-001..047`;
- targeted runner/compiler suite: 118 tests, pass;
- writer validate-only context: 96 886 / 131 072 bytes;
- reviewer transport replay: 117 439 / 131 072 bytes;
- dispatcher dry-run: verified exec, contract v2, no fallback;
- promotion/overwrite disabled; production target absent;
- no V3 attempt artifact exists before authorization.

Run exactly one dispatcher command. If it returns any non-accepted status or new blocker, preserve evidence and stop without retrying V3.
