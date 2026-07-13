# V5 Pre-Live Authorization

## Decision

`CONDITIONAL — authorize exactly one dispatcher after checkpoint commit`

## Conditions already satisfied

- Source-first boundary and portable DaData/save fixtures are explicit.
- Compiler/runner regression: 128 passed.
- V5 package digest, 47-TC seed order and validate-only gates passed.
- Writer context fits the configured limit.
- Verified exec selected; SDK fallback is disabled.
- Production baseline is unchanged and shadow target is absent.

## Remaining condition

- Create and record the pre-live checkpoint commit.

## Stop rule

Run one dispatcher after the checkpoint. Any blocker is terminal for this iteration; do not retry. Do not promote or create a production shadow.
