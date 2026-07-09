# Timeout Recovery Diagnostic Report

- FT package: `fts/AutoFin`
- Scope slug: `iteration-smoke-search-clear-context`
- Timed-out SDK writer session: `019f47a4-5be9-73e2-a70a-088e6c74d1a7`
- Timed-out stage: `writer-r1`
- Current cycle status: `blocked-input`

## Profile Contract

The old timeout recovery path reported the expected scoped validator profile as:

- `work/review-cycles/iteration-smoke-search-clear-context/outputs/scoped-validator-profile.writer-r1.json`

The profiles that actually exist in the active outputs directory are:

- `work/review-cycles/iteration-smoke-search-clear-context/outputs/scoped-validator-profile.structure-preflight-r1.json`

The existing profile has:

- `current_stage: structure-preflight-r1`
- `scope_slug: iteration-smoke-search-clear-context`
- `unresolved_warning_error_count: 2`
- blocking scoped findings: `source-row-inventory-missing`, `writer-quality-gate-missing`

## Root Cause

The writer session advanced `cycle-state.yaml` from `writer-r1|scope-ready-for-writer` to `structure-preflight-r1|blocked-input` before the supervised SDK process timed out. During that advanced state, the runner wrote the stage-appropriate scoped profile for `structure-preflight-r1`.

The recovery diagnostics used the original timed-out writer stage name (`writer-r1`) instead of the advanced/current stage. That made the report claim the writer profile was missing, even though the real post-writer validation profile existed and was unresolved.

## Source Of Truth

For writer timeout recovery:

- if the child process advanced `cycle-state.yaml`, the current state's `current_stage` profile is the source of truth;
- otherwise, recovery may use the writer-stage profile for artifact-only recovery;
- for this smoke rerun, the source of truth is `scoped-validator-profile.structure-preflight-r1.json`.

## Fallback Decision

The runner should not invent a clean fallback profile. It may generate a deterministic scoped profile from the current cycle state when the expected stage-appropriate profile is absent, but recovery can advance only if that generated profile has `unresolved_warning_error_count=0`.

In this rerun, fallback generation is not needed because the stage-appropriate profile already exists.

## Stage Completion Gate

Writer stage completion must not route to reviewer/preflight without scoped validator evidence. If the stage-appropriate profile is absent, recovery must block with `writer-timeout-recovery-missing-profile` and include the exact missing profile path and recovery action.

If the profile exists but has unresolved warnings or errors, the runner must keep the cycle blocked and surface the unresolved count. That is the correct result for this rerun.

## State Advancement Impact

The cycle remains terminal `blocked-input`.

- Reviewer did not start.
- No sign-off exists.
- The unsigned draft was moved out of production `test-cases/` to `work/review-cycles/iteration-smoke-search-clear-context/outputs/writer-r1-draft.md`.
- `canonical_test_cases` remains the future post-signoff target: `test-cases/4.2-iteration-smoke-rerun-search-clear-context.md`.
