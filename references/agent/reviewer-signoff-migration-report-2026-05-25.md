# Reviewer Sign-off Self-check Migration Report

## Context

`scripts/validate_agent_artifacts.py --reviewer-signoff-policy strict` finds 11 legacy UI-prep handoffs without `Reviewer Sign-off Self-check`.

This report is intentionally a migration assessment, not an automatic backfill. A missing self-check is a contract gap, but adding one retroactively is only acceptable when existing artifacts already support the claimed sign-off.

## Current Result

Command:

```powershell
python scripts\validate_agent_artifacts.py --root . --json --reviewer-signoff-policy strict
```

Initial summary:

- workflow states checked: `20`
- reviewer sign-off warnings: `11`
- all 11 warnings are `reviewer-signoff-self-check-missing`

After low-risk backfill:

- reviewer sign-off warnings: `8`
- backfilled scopes: `podpisanie-kod`, `postobsluzhivanie-kredita`, `formirovanie-kod-pechatnye-formy-i-tegi`

## Assessment Rules

Use these rules before adding a self-check to a legacy handoff:

- Do not add `Reviewer Sign-off Self-check` only to satisfy the validator.
- Prefer `loop-summary.md` as the migration target because it is the reviewer-loop final status artifact.
- `blocking_findings_absent: yes` is acceptable only if the final reviewer round has no `error` or `warning`.
- `traceability_gaps_absent: yes` is acceptable only if the final traceability matrix has no `gap`.
- `known_unclear_items` must be `none` only when the final matrix/summary has no remaining `unclear`.
- If loop summary and matrix disagree, do not backfill until the discrepancy is reviewed.

## Migration Candidates

| Scope | Evidence | Risk | Recommendation |
| --- | --- | --- | --- |
| `podpisanie-kod` | Round 1 `full`; loop summary says `Round 1 findings: none`; final status `signed-off`; latest matrix has `gap=0`, `unclear=0`. | Low | Backfilled in `loop-summary.md` with `known_unclear_items: none`. |
| `postobsluzhivanie-kredita` | Round 1 `full`; loop summary says `Round 1 findings: none`; final status `signed-off`; latest matrix has `gap=0`, `unclear=0`. | Low | Backfilled in `loop-summary.md` with `known_unclear_items: none`. |
| `formirovanie-kod-pechatnye-formy-i-tegi` | Round 1 `full`; loop summary says `Round 1 findings: none`; final status `signed-off`; latest matrix has `gap=0`, `unclear=0`. | Low | Backfilled in `loop-summary.md` with `known_unclear_items: none`. |
| `bp-collateral-deal-issue` | Loop summary has `Findings error=0`, `warning=0`, `Traceability gap=0`, `unclear=1`; latest matrix lists `BP-CDI-ATOM-011` as unclear. | Medium | Backfill is acceptable only as qualified sign-off; `known_unclear_items` must name `BP-CDI-ATOM-011`. |
| `ui-employment-core-fields` | Loop summary has `Findings error=0`, `warning=0`, `Traceability gap=0`, `unclear=7`; latest matrix uses legacy `UNCLEAR-001..007`. | Medium | Backfill is acceptable only as qualified sign-off; keep all seven unclear ids explicit. |
| `bp-initiation-client-offers` | Loop summary has `Findings error=0`, `warning=0`, `Traceability gap=0`, `unclear=2`; latest matrix has two legacy unclear rows. | Medium | Backfill is acceptable only as qualified sign-off; list both unclear items from the matrix/summary rather than using `none`. |
| `ui-main-info` | Loop summary has `Findings error=0`, `warning=0`, `Traceability gap=0`, `unclear=8`; latest matrix has eight legacy unclear rows. | Medium | Backfill is acceptable only as qualified sign-off; list all remaining unclear items. |
| `pdd-dokumenty-klienta` | Two-round loop; round 1 had 2 warning findings; loop summary says writer closed them and round 2 has `error=0`, `warning=0`; final matrix has `gap=0`, `unclear=4`. | Medium-high | Do not bulk-backfill. First spot-check `round-2-findings.md`, `round-1-writer-response.md`, and the four unclear rows, then add a qualified self-check if consistent. |
| `pdd-detalizaciya-dohodov-obshchaya-logika` | Two-round loop; round 1 had 1 traceability warning; loop summary says writer closed it and round 2 has `error=0`, `warning=0`; summary still mentions one residual unclear, while latest matrix extraction reports no unclear rows. | High | Do not backfill until the summary/matrix discrepancy is resolved. |
| `pdd-detalizaciya-2-ndfl` | Two-round loop; round 1 had 9 atomarity warnings; loop summary says round 2 verified them as fixed; latest matrix extraction reports `gap=0`, `unclear=0`. | Medium-high | Spot-check `round-2-findings.md` and writer response before backfill; this is too large for blind migration. |
| `pdd-ostalnye-tipy-dpd` | Two-round loop; round 1 had warning findings; loop summary says round 2 has `error=0`, `warning=0`; summary mentions residual info/unclear, while latest matrix extraction reports no unclear rows. | High | Do not backfill until residual unclear items are reconciled with final matrix. |

## Recommended Migration Order

1. Backfill the four medium-risk scopes with explicit `known_unclear_items`.
2. Review the four PDD two-round scopes manually before any backfill.
3. Reconcile summary/matrix discrepancies before adding any self-check that claims `known_unclear_items: none`.
4. Re-run:

```powershell
python scripts\validate_agent_artifacts.py --root . --json --reviewer-signoff-policy strict --fail-on warning
```

## Non-Recommendation

Do not add the same generic self-check block to all 11 files. That would hide real uncertainty in the migration history and weaken the value of the new validator gate.

## Learning Trace

The validator found a structural absence, not proof that the old reviews were bad. The migration decision must therefore use evidence from the loop summary, findings, writer response, and traceability matrix. This is the difference between enforcing a contract and manufacturing compliance.
