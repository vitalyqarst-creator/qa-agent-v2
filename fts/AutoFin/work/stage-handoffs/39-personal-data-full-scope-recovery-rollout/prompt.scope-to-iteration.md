# Next Stage: V3 Reviewer Recovery Rollout

Continue `ft-test-case-iteration` for scope `application-card-client-personal-data`.

## Goal

Confirm the compact reviewer transport in one new immutable V3 writer/reviewer cycle without changing the FT-first baseline.

## Inputs

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/compiler-inputs/application-card-client-personal-data/`
- `fts/AutoFin/work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/reviewer-context-blocker-report.md`
- `fts/AutoFin/work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/reviewer-context-remediation-report.md`
- `fts/AutoFin/work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/v2-cycle-integrity-warning.yaml`
- `fts/AutoFin/work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/stop-gate.md`
- Code at or after commit `15889ad`.

## Steps

1. Read the V2 integrity warning and do not reuse V1 or V2 cycles, attempts or target-bound packages.
2. Compile `application-card-client-personal-data-v3` into a new V3 cycle from the existing verified compiler inputs. Do not launch generic AI input preparation.
3. Verify 42 atoms, 65 obligations, 47 planned TC, `GAP-001..003` and `DICT-001`.
4. Verify exact seed order `TC-ACPD-001..047` and validate-only writer context <= 131 072.
5. Replay the patched reviewer prompt against immutable V2 writer/gate artifacts only as a transport-size regression; require <= 131 072. Do not use the V2 draft as requirement evidence.
6. Run exactly one dispatcher live with verified exec, no SDK fallback, promotion or overwrite.
7. Stop on any new blocker and preserve immutable evidence.

## Acceptance Criteria

- Writer structure: pass.
- Obligation gate: 65/65.
- Quality bundle: pass.
- Semantic overlap: clean.
- Reviewer context: <= 131 072.
- Reviewer decision: `accepted` with zero blocking findings.
- Terminal status: `accepted-not-promoted`.
- Production target: absent.

## Guardrails

- Do not modify production test cases.
- Do not resume or rewrite V1/V2 artifacts.
- Treat `v2-cycle-integrity-warning.yaml` as the machine-readable quarantine for the stale V2 cycle state.
- Do not treat V1/V2 drafts as signed-off baselines or source evidence.
- Do not begin broader input-preparation architecture changes until V3 is accepted.
