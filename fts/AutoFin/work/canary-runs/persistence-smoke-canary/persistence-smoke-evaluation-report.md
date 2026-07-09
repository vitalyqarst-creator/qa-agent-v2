# Persistence Smoke Evaluation Report

| item | value |
| --- | --- |
| branch | `audit/stabilize-testcase-agent-persistence-calibration-handoff` |
| commit | recorded in final execution report after commit |
| production artifact | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-persistence-smoke.md` |
| work directory | `fts/AutoFin/work/canary-runs/persistence-smoke-canary/` |
| calibration package | `fts/AutoFin/work/calibration/persistence-save-flow/` |
| source artifacts used | `FT4AutoFinFinal.docx`; `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.pdf` for cross-check availability; `fts/AutoFin/AGENT-NOTES.md` |
| v4 field-level canary role | not overwritten; used only as style/reference fixture and list of already covered field-level areas |

## Source-Backed Save / Reopen Decision

Reopen path is source-backed through `BSR 35`: selecting exactly one application row and using the transition action opens the selected application card within role permissions.

Exact save action is not source-backed in the inspected section 4.3 field rows or adjacent application-list action rows. Therefore the persistence smoke TC are `candidate-persistence-calibration`: they contain concrete valid data, save/reopen/verify structure and cleanup strategy, but require BA/UI confirmation for the exact save action and exit-after-save path before execution.

Calibration handoff is recorded in `fts/AutoFin/work/calibration/persistence-save-flow/`. No TC is converted to executable in this task.

## TC Summary

| metric | value |
| --- | --- |
| TC count before polish | 7 |
| TC count after polish | 7 |
| executable without save-flow confirmation | 0 |
| candidate / require confirmation | 7 |
| converted to executable in this task | 0 |
| hard cap | 10 |

## Selected Persistence Areas

| area | TC |
| --- | --- |
| Registration address selected via DaData | `TC-AF43-PS-001` |
| Manual registration address | `TC-AF43-PS-002` |
| Fact address differing from registration | `TC-AF43-PS-003` |
| Client mobile phone and e-mail | `TC-AF43-PS-004` |
| Added work phone | `TC-AF43-PS-005` |
| Added contact person | `TC-AF43-PS-006` |
| Deleted contact person | `TC-AF43-PS-007` |

## Relationship With V4

This persistence smoke does not replace the v4 field-level / risk-based canary. The v4 canary does not replace this persistence smoke. Together they cover UI field behavior plus minimal save/reopen verification.

## Coverage Matrix Summary

The coverage matrix records saved data, source rows / BSR, reopen verification and cleanup strategy for each persistence area. Coverage is representative smoke, not exhaustive persistence regression.

## Polish Pass Fixes

| item | result |
| --- | --- |
| `TC-AF43-PS-001` trace | Removed `BSR 119` from primary trace; decomposition into manual components is not exercised by the DaData persistence oracle. |
| `TC-AF43-PS-003` trace | Removed `BSR 148` from primary trace; manual fact-address visibility is not exercised by the DaData fact-address persistence oracle. |
| `TC-AF43-PS-005` trace | Removed `BSR 167` from primary trace; add-phone visibility is supporting setup, while the TC verifies work-phone persistence. |
| passive preconditions | Fixed in all 7 TC by rewriting passive state as action-oriented setup. |
| `TC-AF43-PS-006` rolling date | Formalized `D - 30 calendar years`, `DD.MM.YYYY`, and example `09.07.2026 -> 09.07.1996`; expected result references the calculated value. |
| `TC-AF43-PS-007` setup | Made self-contained: create, save, close, reopen, verify presence, then delete/save/reopen. |
| `TC-AF43-PS-004` grouped smoke | Added explicit grouped persistence rationale and residual risk for mobile phone + e-mail. |
| UI block naming | Normalized section 4.3 block names to `Контакты клиента` and `Контактные лица`; appendix terms are not used as primary block labels. |
| relation terminology | Normalized persistence smoke field label to source-backed `Отношение к заявителю`; `Отношение к клиенту` is not used. |

## Calibration Package Summary

| artifact | purpose |
| --- | --- |
| `fts/AutoFin/work/calibration/persistence-save-flow/ba-ui-calibration-questions.md` | BA/UI questions `BA-PS-001`..`BA-PS-007` with priority and affected TC. |
| `fts/AutoFin/work/calibration/persistence-save-flow/persistence-tc-conversion-plan.md` | TC-by-TC conversion blockers and fields to update after confirmation. |
| `fts/AutoFin/work/calibration/persistence-save-flow/save-flow-calibration-checklist.md` | UI/BA/QA calibration checklist and per-TC readiness table. |
| `fts/AutoFin/work/calibration/persistence-save-flow/persistence-calibration-evaluation-report.md` | Summary of source evidence and remaining blockers. |

## Out Of Scope

- Exhaustive address component persistence matrix.
- All home/work phone add/delete combinations.
- All contact-person relation values.
- Invalid-value rejection persistence; negative input validation remains covered by v4 candidate-negative policy.
- Backend/internal persistence assertions not observable through UI.

## BA Questions / Blockers

Blocking for execution:
- `BA-PS-001`: exact save action.
- `BA-PS-002`: save success oracle.
- `BA-PS-003`: exit-after-save and return flow.
- `BA-PS-004`: exact reopen path for the same saved application beyond the partial `BSR 35` source-backed transition.
- `BA-PS-005`: cleanup/isolation strategy for persistent smoke data.

Open follow-up:
- `BA-PS-006`: authoritative application date for rolling `D` in birth-date calculations.
- `BA-PS-007`: BA/UI confirmation for the source-backed relation term.

## Validator And Budget Results

| check | result |
| --- | --- |
| targeted persistence calibration validator tests | passed: 10 targeted tests |
| scoped validator on persistence smoke artifact | passed: 0 errors; standalone package-format warnings only |
| scoped validator on persistence smoke work dir | passed: 0 errors; isolated work-dir scan warns only about missing workflow-state |
| scoped validator on v4 field-level artifact | passed: 0 errors; v4 was not overwritten |
| old independent-wide-canary gap-only fixture | compatible profile: warning; strict canary with `--fail-on error`: expected failure with `source-backed-input-restriction-gap-only` error |
| architecture suite | passed: 59 checks, 0 findings; no near_limit/fail budgets |
| agent-layer-fast suite | passed: 215 tests, 1 skipped |
| artifact-validator-sharded suite | passed: 7/7 shards, 385 validator tests |
| instruction budget sweep | passed; nearest margin `reviewer.full_existing_cases` at 15.6 KiB headroom |
| `git diff --check` | passed; CRLF conversion warnings only |

## Remaining Risks

- Save/autosave behavior may differ by application status or role; source does not specify status-specific save mechanics.
- Cleanup may require isolated applications until BA confirms safe restoration.
- Reopen through `BSR 35` depends on being able to find/select the same application in the applications table.
- A grouped mobile phone + e-mail smoke can miss a field-specific persistence defect until split into atomic persistence regression.
