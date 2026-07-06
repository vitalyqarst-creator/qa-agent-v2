# Controlled Traceability Update Workflow

This document is the canonical safety workflow for updating generated `REQ-AUTOFIN-*` refs in existing canonical test cases after a requirements diff.

It covers traceability-only updates. It does not authorize semantic test-case edits, new test-case creation, large/unlinked package execution, or writer/reviewer workflow changes.

## Proven Scope

The workflow was proven on small file-bound packages:

- `WPKG-000003`: `TC-AMSR-012`
- `WPKG-000002`: `TC-ACCEI-012`, `TC-ACCEI-013`

For large, unlinked, or `create_new_candidate` packages, stop before writer execution and create a separate reviewed plan.

## End-To-End Stages

1. Detect mismatch.

   Use mismatch diagnostics when a linked TC has legacy refs but lacks generated `REQ-AUTOFIN-*` refs, or when a writer dry-run proposal cannot find old `REQ-*` refs in the traceability line. The important mismatch class is `req_uid_generated_after_tc_creation`.

2. Build repair strategy.

   Automatic replacement is forbidden while old generated `REQ-*` refs are absent from the TC. `source_req_id` fallback can be used as evidence for a mapping, but never as a silent rewrite rule. The allowed next action must be `create_backfill_proposal`.

3. Build backfill proposal.

   Backfill proposal is preview-only. It may append missing generated `REQ-*` refs only to the listed TC traceability line. It must preserve legacy refs and must not change steps, expected results, test data, headings, unrelated metadata, or unrelated TC blocks. Patch files are preview artifacts only.

4. Review backfill proposal.

   Review must prove the proposal changes only traceability lines, added refs exist in registry, candidate refs match repair strategy, supporting source refs are present, legacy refs are preserved, and no unrelated TC is touched. `safe_for_controlled_apply=true` is allowed only after these checks pass.

5. Controlled backfill apply.

   Dry-run is default. Real apply requires explicit `--apply`; `approved-with-warnings` additionally requires `--ack-warnings`. The executor must use structured proposal data only, never `git apply` or `patch`. A backup and post-apply validation are mandatory before considering the package complete.

6. Re-run writer proposal after backfill.

   After backfill, old generated `REQ-*` refs must be present in the traceability line. The writer dry-run proposal should either produce traceability old->new replacements or clearly report a new blocker. The original missing-old-ref mismatch should be gone.

7. Review writer proposal.

   Writer proposal review is read-only. It must verify traceability-line-only replacement, old refs present before replacement, new refs present after replacement, legacy refs preserved, registry refs valid, update-plan mapping valid, and no duplicate `REQ-*` refs.

8. Controlled writer traceability update apply.

   Dry-run is default. Real apply requires explicit `--apply`; `approved-with-warnings` requires `--ack-warnings`. The executor must use structured proposal data, create a backup before writing, and run post-apply validation. It must not change steps, expected results, test data, headings, or unrelated TC blocks.

9. Post-apply validation.

   Validation must check final state independently of current git diff. Supported git states are:

   - `uncommitted_expected_change`
   - `final_state_already_baselined`
   - `unexpected_changes`
   - `missing_expected_final_state`

   `final_state_already_baselined` is not an error when `final_state_valid=true`. In that state `safe_to_commit=false` and `commit_action=nothing_to_commit` are normal; pipeline continuation depends on `safe_for_next_stage=true`.

10. Completed package regression.

    After small packages are complete, run read-only mini-regression. Stale writer proposals after final apply are warnings, not TC defects. Unrelated dirty test-case files block the regression and must be isolated manually; do not automatically revert, stash, or commit them.

## Decision Table

| Situation | Allowed action | Forbidden action | Required artifact | Next stage |
| --- | --- | --- | --- | --- |
| Old `REQ-*` refs are absent in TC traceability line | Run mismatch diagnostics and repair strategy | Direct old->new replacement | `traceability-mismatch-diagnostics.*.json`, `traceability-repair-strategy.*.json` | Backfill proposal |
| Legacy refs exist but generated `REQ-*` refs are absent | Use legacy/source refs as evidence for backfill candidate | Silent generated-ref insertion without proposal/review | Repair item with `allowed_next_action=create_backfill_proposal` | Backfill proposal |
| Backfill proposal is `approved-with-warnings` | Real apply only with `--apply --ack-warnings`; dry-run without ack is allowed | Real apply without `--ack-warnings` | `traceability-backfill-review-<package>.json` | Controlled backfill apply |
| Writer proposal is `approved-with-warnings` | Real apply only with `--apply --ack-warnings`; dry-run without ack is allowed | Real apply without `--ack-warnings` | `writer-proposal-review-<package>-after-backfill.json` | Controlled writer traceability update apply |
| Post-apply validation has clean git state and `final_state_valid=true` | Treat as `final_state_already_baselined`; continue when `safe_for_next_stage=true` | Fail only because `git diff` is empty | `writer-traceability-post-apply-validation-*.json` | Completed package regression or next package |
| Writer proposal still contains completed replacements after final apply | Classify as stale proposal warning | Treat as TC defect | Completed apply and post-apply validation reports | Completed package regression |
| Unrelated dirty test-case file during regression | Stop and triage/commit/stash/revert only with explicit user action | Mix unrelated file into package regression; automatic restore/stash/commit | `completed-package-regression-*.json`, git triage output | Rerun regression after isolation |
| Large or unlinked package | Split or create manual work package | One-shot writer execution or apply | Manual update package/task artifacts | Separate reviewed plan |
| `create_new_candidate` package | Draft-only proposal and review | Create canonical TC without reviewed draft workflow | Manual package/task artifact | Writer draft proposal |

## Hard Safety Rules

- Never edit canonical test-cases during proposal, review, or validation stages.
- Never run real apply unless the user explicitly asks or the stage prompt explicitly requires `--apply`.
- Never apply patch artifacts through `git apply` or `patch`; use structured proposal data.
- Never silently replace legacy refs with generated refs.
- Never use `source_req_id` fallback as a silent rewrite.
- Never process a large or unlinked package as one writer task.
- Never mix unrelated dirty files into completed-package regression.
- Never treat `approved-with-warnings` as safe for real apply without `--ack-warnings`.
- Never treat stale proposal after successful final apply as a TC defect.
- Never create a new TC from `create_new_candidate` without a draft-only proposal and review.

## Completion Criteria

A small package is complete only when:

- controlled apply report is `applied`;
- backup exists for real apply;
- post-apply validation has `final_state_valid=true`;
- `safe_for_next_stage=true`;
- old/intermediate `REQ-*` refs are absent;
- final new `REQ-*` refs are present;
- legacy refs are preserved;
- no duplicate `REQ-*` refs are present;
- completed-package regression has no regressions for the package.
