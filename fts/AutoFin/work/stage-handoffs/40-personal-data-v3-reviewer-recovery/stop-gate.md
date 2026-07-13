# Stop Gate: V3 Reviewer Changes Required

## Decision

`STOP - reviewer-changes-required`

## Proven

- Separate writer and reviewer `codex exec` sessions work live.
- Compact reviewer transport fits the context limit.
- Reviewer outcome is persisted correctly.
- Production/V1/V2 boundaries remain intact.

## Not proven

- Semantic reviewer acceptance.
- Production readiness of the 47-case draft.
- Deterministic rejection of generic fixtures, undefined continuation actions and non-observable oracles.

## Blocking evidence

- 4 error findings.
- 11 incorrect obligations.
- 9 unique affected test cases.
- `accepted_terminal_state=false`; `final_promoted=false`.

## Resume conditions

1. Remediate affected design/package inputs without inventing behavior absent from FT.
2. Add and pass a bounded regression for the observed failure shapes.
3. Pass existing compiler/runner regression and context/hash preflight.
4. Use a fresh immutable V4 cycle. Do not retry or edit V3.
