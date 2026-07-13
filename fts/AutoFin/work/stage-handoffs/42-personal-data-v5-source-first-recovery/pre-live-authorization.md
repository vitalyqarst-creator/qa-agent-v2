# V5 Pre-Live Authorization

## Decision

`AUTHORIZED — exactly one dispatcher`

## Conditions already satisfied

- Source-first boundary and portable DaData/save fixtures are explicit.
- Compiler/runner regression: 128 passed.
- V5 package digest, 47-TC seed order and validate-only gates passed.
- Writer context fits the configured limit.
- Verified exec selected; SDK fallback is disabled.
- Production baseline is unchanged and shadow target is absent.

## Checkpoint

- Commit: `8bf43729e38762b615e531e9b5be99058a6af0a1`.
- Checkpoint created after all listed gates passed and before any V5 live attempt.

## Stop rule

Run one dispatcher after the checkpoint. Any blocker is terminal for this iteration; do not retry. Do not promote or create a production shadow.
