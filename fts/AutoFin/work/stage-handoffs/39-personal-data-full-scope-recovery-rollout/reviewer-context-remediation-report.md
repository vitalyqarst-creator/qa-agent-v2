# Reviewer Context Remediation Report

## Change

For `standard-required` compact reviewer only:

- selected source evidence and immutable writer draft remain unchanged;
- full obligations JSON is replaced by a digest-bound exact review index containing every obligation/atom ID, coverage status, source refs, planned TC, dictionary refs and gap refs;
- full calibration lifecycle is replaced by a digest-bound summary; per-obligation constraint gaps remain in the review index;
- prepared-fast reviewer behavior is unchanged.

The runner now also persists `blocked-reviewer-preflight`, completed writer evidence and `reviewer-context-budget.json` when a future standard reviewer budget gate fails.

## Measured Result On V2 Artifacts

| metric | before | after | limit |
| --- | ---: | ---: | ---: |
| reviewer primary context | 183 402 bytes | 117 439 bytes | 131 072 bytes |
| reviewer prompt | not persisted by pre-fix runner | 114 355 bytes | n/a |
| reviewer instruction bytes | 3 084 bytes | 3 084 bytes | n/a |

Reduction: 65 963 bytes, approximately 36.0%. Remaining headroom: 13 633 bytes.

## Verification

- Target runner/compiler tests: 118 pass.
- Agent-layer-fast: 421 pass, 1 skip.
- Architecture: 61 checks, 0 findings.
- V2 artifact replay of `_reviewer_prompt()`: context gate pass; exact obligation index present; full obligations payload absent; calibration summary present.

## Limitation

No reviewer live session was started after this code change. Acceptance requires a new target-bound V3 package/cycle.
