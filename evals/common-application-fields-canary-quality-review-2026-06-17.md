# Common Application Fields Canary Quality Review - 2026-06-17

## Context

| field | value |
| --- | --- |
| FT package | `fts/ft-2-OF_17` |
| Scope | `common-application-fields` / `section-34` |
| Canonical TC | `fts/ft-2-OF_17/test-cases/section-34-common-application-fields.md` |
| Cycle state | `fts/ft-2-OF_17/work/review-cycles/common-application-fields/cycle-state.yaml` |
| Final status | `signed-off` |
| Review purpose | Manual quality assessment of the latest canary before broader test-case generation. |

## Executive Summary

The canary is useful and materially better than the earlier problematic runs. The writer/reviewer loop produced a signed-off set with `22` test cases, preserved `SRC-001`..`SRC-010`, preserved PDF-only `GSR 205`..`GSR 214`, and ended with `28 covered / 32 unclear / 0 gap` in semantic R2.

The set is not perfect as a manual QA handoff. Its main weakness is not formal traceability, but practical execution: several cases depend on fixture data, primary-save state, and prefilled external-status values that are intentionally not specified by the FT. This is acceptable for FT-first baseline, but it should be tightened before UI automation prep.

## Point 1 - Test-Case Quality Review

### Strengths

| area | assessment | evidence |
| --- | --- | --- |
| Source traceability | Strong. The set keeps `GSR 205`..`GSR 214`, `SRC-001`..`SRC-010`, and `ATOM-*` links. | `round-2-findings.md`: `SRC-001`..`SRC-010`, `GSR 205`..`GSR 214`, `WP-01`..`WP-03`, and `TC-CAF-001`..`TC-CAF-022` are preserved. |
| Scope discipline | Good. Actions, history forms, internal CDI/Gosuslugi behavior and exact generated values are excluded or gap-tracked. | `coverage-gaps.md`: `GAP-001`..`GAP-004`; TC examples avoid exact generated application number/status values. |
| Atomicity | Mostly good. Field visibility/editability/source-prefill behavior is split into separate cases. | `TC-CAF-001`, `TC-CAF-005`, `TC-CAF-010`, `TC-CAF-021` show one main expected result per case. |
| Reviewer effectiveness | Good. R1 semantic review found real quality issues; final format review caught missing canonical TC fields. | `round-1-findings.md`; `final-format-review-findings.md`; `final-semantic-regression-findings.md`. |
| Regression safety | Good. The final semantic regression confirmed the format-only fix did not alter semantics. | `final-semantic-regression-findings.md`: `semantic_diff_count = 0`; test-design artifacts byte-identical to baseline. |

### Weaknesses / Risks

| id | severity | issue | impact | recommendation |
| --- | --- | --- | --- | --- |
| `QA-CANARY-001` | medium | Several TC use generic setup such as "opened card in selected scope" or "after primary save" without enough concrete navigation/data setup. | Manual executor may need project knowledge outside the TC to make the case pass. | Before UI automation prep, add an automation-ready layer that spells out login role, navigation path, how to create/open a saved application, and required fixture records. Do not rewrite FT-first baseline unless evidence demands it. |
| `QA-CANARY-002` | medium | Fixture references such as `FIX-CAF-004.cp_status_from_gosuslugi` are source-safe but not operationally defined in the TC file. | The cases are traceable but only partially executable until fixture data exists. | Create a fixture catalog for `FIX-CAF-*` before UI/API execution. |
| `QA-CANARY-003` | low | Some TC titles are precise but repetitive because field-property scope naturally creates similar visibility/editability checks. | Readability is acceptable, but a human reviewer may find the set verbose. | Keep the current split for traceability; do not merge until UI execution shows repeated cases are redundant in practice. |
| `QA-CANARY-004` | medium | `32 unclear` atoms are valid for metadata-only or unsupported exact-value checks, but the high count can hide whether the baseline is practically sufficient. | A signed-off result can look weaker than it is, or unclear debt can be normalized too easily. | Track a separate metric: executable coverage vs metadata-only unclear vs true source gaps. Current canary already separates these, but dashboards/reports should surface it explicitly. |

## Point 2 - Systemic Findings To Preserve

| finding | why it matters | should become regression/eval criterion |
| --- | --- | --- |
| Metadata-only atoms must not count as executable TC coverage. | R1 caught that requiredness/input/value-type metadata can be overclaimed as covered when the selected UI scope has no observable behavior. | Yes. Reviewer must keep blocking or warning when metadata-only atoms are linked to executable TC coverage without observable pass/fail. |
| Final format review is not optional after semantic closure. | Semantic R2 passed, but format review still found missing canonical fields across all TC. Without this stage, a signed-off set would be structurally incomplete. | Yes. Keep `structure_format_final` as mandatory before sign-off. |
| Format-only writer revision needs semantic regression. | The final writer added template/source fields to 22 TC. Semantic regression proved no traceability/runtime semantics changed. | Yes. Keep `semantic_regression` after any final format writer pass. |
| Model-capacity failure is recoverable if cycle state advanced safely before the failure. | First run failed at `writer-r2` with `Selected model is at capacity`; `doctor` found valid state, no lock, and recommended `run-next-stage`; retry completed. | Yes. Add this as an operational recovery scenario for runner docs/tests if not already covered by a synthetic failure fixture. |
| Terminal validator gate is necessary but not sufficient for human quality. | Terminal gate had `blocking_unwaived_count = 0`, but the practical execution review still found fixture/navigation risks. | Yes. Canary report should include manual executability findings in addition to validator metrics. |

## Point 3 - Git / Artifact Retention Check

### Findings

| check | result |
| --- | --- |
| `git status --short --ignored` for new FT artifacts | Reports the path as ignored: `!! fts/`. |
| `git check-ignore -v` for canonical TC, test-design, cycle-state and handoff files | All are ignored by `.gitignore:34: fts/`. |
| `.gitignore` rationale | The file states: "FT packages and generated/manual test-case artifacts are intentionally out of the agent repository." |
| Snapshot directory traversal | `git status --ignored` also emits many `Filename too long` warnings under `work/review-cycles/common-application-fields/versions/.../_artifact_write/...`. |

### Interpretation

The empty `git status --short` for the canary artifacts is expected, not a git malfunction. The entire `fts/` tree is intentionally local/generated and ignored.

This is still a process risk: a successful local canary can disappear from repository-level review unless its conclusions are copied into a tracked artifact. This report is stored under `evals/`, which is not ignored by the root `.gitignore`.

The `Filename too long` warnings are separate and more concerning. They come from nested snapshot copies of `work/test-design/.../_artifact_write/...` under review-cycle versions. This should be treated as runner artifact hygiene debt: snapshots should avoid copying scratch `_artifact_write` directories or should flatten/trim snapshot paths.

## Recommended Next Steps

1. Add or confirm a regression criterion for metadata-only atoms not being counted as executable coverage.
2. Add or confirm a regression criterion for final format review catching sparse TC templates before sign-off.
3. Add a runner artifact hygiene task: exclude `_artifact_write/` scratch directories from version snapshots, or cap snapshot path depth.
4. Before UI automation prep for this canary, create a fixture catalog for `FIX-CAF-*` and an automation-ready copy with concrete navigation/setup details.
5. For the next canary, use an action-flow scope rather than another field-property table to test scenario quality, transitions, dialogs and validation feedback.

## Evidence Commands

```powershell
python scripts\codex_review_cycle_runner.py validate --state fts\ft-2-OF_17\work\review-cycles\common-application-fields\cycle-state.yaml
git status --short --ignored -- fts/ft-2-OF_17/test-cases/section-34-common-application-fields.md fts/ft-2-OF_17/work/test-design/section-34-common-application-fields fts/ft-2-OF_17/work/review-cycles/common-application-fields fts/ft-2-OF_17/work/stage-handoffs/06-common-application-fields
git check-ignore -v fts/ft-2-OF_17/test-cases/section-34-common-application-fields.md fts/ft-2-OF_17/work/test-design/section-34-common-application-fields/atomic-requirements-ledger.md fts/ft-2-OF_17/work/review-cycles/common-application-fields/cycle-state.yaml fts/ft-2-OF_17/work/stage-handoffs/06-common-application-fields/scope-contract.md
```
