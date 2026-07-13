# Next Stage: Personal Data V4 Quality Remediation

Continue `ft-test-case-iteration` for scope `application-card-client-personal-data`.

## Goal

Eliminate the non-executable test-design patterns found by V3 before spending another live reviewer run, then confirm the correction in one fresh immutable V4 cycle without changing the FT-first baseline.

## Inputs

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/compiler-inputs/application-card-client-personal-data/`
- `fts/AutoFin/work/stage-handoffs/40-personal-data-v3-reviewer-recovery/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/40-personal-data-v3-reviewer-recovery/reviewer-outcome-analysis.md`
- `fts/AutoFin/work/stage-handoffs/40-personal-data-v3-reviewer-recovery/stop-gate.md`
- `fts/AutoFin/work/stage-handoffs/40-personal-data-v3-reviewer-recovery/iteration-session-log.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/cycle-state.yaml`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v3-20260713/attempts/reviewer-r1/attempt-001/runner-output/findings.md`
- `evals/candidates/2026-07-13-action-without-observable-oracle-personal-data.md`

## Phase 1 - bounded diagnosis and fixture design

1. Preserve V1/V2/V3 and production test cases as read-only.
2. Map `FIND-001..004` to all 11 incorrect obligations and 9 TC.
3. For ABS/DaData checks, define reproducible fixture or explicit calibration-fixture contracts; do not invent unavailable integration values.
4. For requiredness/optionality checks, replace "continue scenario" with a concrete confirmed action or an explicit neutral evidence-capture procedure under `GAP-002`.
5. For date/type checks, use concrete relative data and an observable oracle without inventing format/widget behavior.

## Phase 2 - prevention

1. Turn the eval candidate into a bounded fixture/eval.
2. Add the narrowest deterministic or simulated check that rejects:
   - generic "values needed to save" fixtures;
   - undefined attempt/continue actions;
   - expected results that only restate the FT or say the exact result is unknown.
3. Avoid a broad keyword ban that would reject legitimate traceability text or GAP descriptions.

## Phase 3 - package and preflight

1. Recompile a fresh `application-card-client-personal-data-v4` package from remediated inputs.
2. Require 42 atoms, 65 obligations, 47 planned TC, `GAP-001..003`, `DICT-001`, exact `TC-ACPD-001..047` seed order and matching hashes.
3. Run targeted eval, runner/compiler regression, validate-only and reviewer transport-size replay.
4. Create a checkpoint commit before live.

## Phase 4 - one live confirmation

Run exactly one verified-exec V4 dispatcher cycle with no SDK fallback, promotion or overwrite. Stop on a new blocker.

## Acceptance criteria

- Targeted eval detects the V3 bad fixture and passes the corrected fixture.
- All existing relevant regression tests pass.
- All writer deterministic gates pass.
- Reviewer reports zero blocking findings and `accepted`.
- Terminal state is accepted but not promoted.
- Production target remains absent and V1/V2/V3 are unchanged.

## Guardrails

- Do not edit or resume V3.
- Do not convert unknown UI behavior into invented expected results.
- Do not run V4 live until the prevention gate fails on the V3-shaped fixture and passes on the corrected fixture.
