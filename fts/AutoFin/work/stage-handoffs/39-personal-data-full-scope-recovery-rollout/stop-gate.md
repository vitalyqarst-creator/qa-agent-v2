# Stop Gate

## Decision

`STOP — reviewer-live-confirmation-required`.

## Trigger

The single authorized V2 live run completed writer gates but reviewer context exceeded its hard limit. Reviewer was not launched.

## Proven

- Numeric seed-order remediation works live.
- Writer output contains 47 ordered TC and covers 65/65 obligations.
- All deterministic writer gates pass.
- Production target remains absent.
- Reviewer transport is reduced offline from 183 402 to 117 439 bytes and regression tests pass.
- Stale pre-fix V2 state is quarantined by `v2-cycle-integrity-warning.yaml`; V2 cannot be resumed.

## Not Proven

- Semantic reviewer acceptance.
- Complete writer/reviewer duration and token cost.
- End-to-end `accepted-not-promoted` terminal state.

## Conditions To Remove STOP

1. Create a new immutable V3 cycle and target-bound package from the same compiler inputs.
2. Use code at or after commit `15889ad`.
3. Verify writer seed `001..047`, writer context <= 131 072 and reviewer transport replay <= 131 072 before live.
4. Run exactly one dispatcher live without SDK fallback, promotion or overwrite.
5. Require structure pass, 65/65 obligation gate, quality pass, semantic-overlap clean and reviewer `accepted`.

Do not resume V2 and do not treat its draft as signed off.
