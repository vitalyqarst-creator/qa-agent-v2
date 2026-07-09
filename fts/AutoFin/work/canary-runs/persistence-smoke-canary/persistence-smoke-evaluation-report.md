# Persistence Smoke Evaluation Report

| item | value |
| --- | --- |
| branch | `audit/stabilize-testcase-agent-persistence-smoke-canary` |
| commit | recorded in final execution report after commit |
| production artifact | `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts-persistence-smoke.md` |
| work directory | `fts/AutoFin/work/canary-runs/persistence-smoke-canary/` |
| source artifacts used | `FT4AutoFinFinal.docx`; `FT4AutoFinFinal.xhtml`; `FT4AutoFinFinal.pdf` for cross-check availability; `fts/AutoFin/AGENT-NOTES.md` |
| v4 field-level canary role | not overwritten; used only as style/reference fixture and list of already covered field-level areas |

## Source-Backed Save / Reopen Decision

Reopen path is source-backed through `BSR 35`: selecting exactly one application row and using the transition action opens the selected application card within role permissions.

Exact save action is not source-backed in the inspected section 4.3 field rows or adjacent application-list action rows. Therefore the persistence smoke TC are `candidate-persistence-calibration`: they contain concrete valid data, save/reopen/verify structure and cleanup strategy, but require BA/UI confirmation for the exact save action and exit-after-save path before execution.

## TC Summary

| metric | value |
| --- | --- |
| TC count | 7 |
| executable without save-flow confirmation | 0 |
| candidate / require confirmation | 7 |
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

## Out Of Scope

- Exhaustive address component persistence matrix.
- All home/work phone add/delete combinations.
- All contact-person relation values.
- Invalid-value rejection persistence; negative input validation remains covered by v4 candidate-negative policy.
- Backend/internal persistence assertions not observable through UI.

## BA Questions / Blockers

Blocking for execution:
- `BA-PS-001`: exact save action.
- `BA-PS-002`: exit-after-save and return flow.
- `BA-PS-003`: cleanup/isolation strategy for persistent smoke data.

Open follow-up:
- `BA-PS-004`: whether phone-row deletion persistence must be added.

## Validator And Budget Results

| check | result |
| --- | --- |
| targeted persistence validator tests | `8 passed` |
| scoped validator on persistence smoke artifact | `0 errors`; warnings only for standalone package inventory / writer gate sections |
| scoped validator on persistence smoke work dir | `0 errors`; warning only for missing workflow-state in isolated work-dir scan |
| scoped validator on v4 field-level artifact | `0 errors`; no regression from persistence follow-up |
| architecture suite | passed |
| agent-layer-fast suite | passed: `215 tests`, `1 skipped` |
| artifact-validator-sharded suite | passed: `7/7 shards` |
| instruction budget sweep | passed; nearest margin `reviewer.full_existing_cases` at `15.0 KiB` headroom |

## Remaining Risks

- Save/autosave behavior may differ by application status or role; source does not specify status-specific save mechanics.
- Cleanup may require isolated applications until BA confirms safe restoration.
- Reopen through `BSR 35` depends on being able to find/select the same application in the applications table.
