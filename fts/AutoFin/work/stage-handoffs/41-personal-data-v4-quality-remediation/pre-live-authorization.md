# V4r1 Pre-Live Authorization

## Decision

`AUTHORIZED - exactly one dispatcher live`

## Conditions satisfied

- Bad/corrected execution-oracle eval passes.
- Compiler and runner prevention are covered by focused regression.
- V4r1 package is immutable, hash-verified and within compiled-evidence budget.
- 42 atoms / 65 obligations / 47 TC / 3 gaps / 1 dictionary preserved.
- Writer exact context and conservative reviewer envelope fit 131 072 bytes.
- Verified exec selected with no SDK fallback.
- Production target absent; V1/V2/V3/handoff38 unchanged.
- A checkpoint commit must be created before live.

## Stop rule

Run one V4r1 dispatcher only. Stop on context, quality, reviewer or runner blocker. Do not retry, mutate V4/V4r1, promote or overwrite.
