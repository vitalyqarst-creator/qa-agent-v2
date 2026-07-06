# Manual Decision Matrix Format

Stage 9D.6 creates a reviewer-facing compression artifact for unresolved create-new-TC decisions. It is not Stage 9E and does not create revised draft proposals.

The matrix is read-only. It may read canonical test-case files only as comparison evidence through upstream artifacts. It must not create or edit canonical test cases.

## Inputs

- `new-tc-revision-decision-pack-<package_id>.json`
- `residual-source-grounding-gap-analysis-<package_id>.json`
- `agent-capability-improvement-plan-<package_id>.json`
- `new-tc-draft-proposal-<package_id>.json`
- `new-tc-draft-review-<package_id>.json`
- `new-tc-draft-revision-plan-<package_id>.json`
- `create-new-tc-context-bundle-<package_id>.json`
- requirements registry/diff, impact report and update plan as supporting evidence
- canonical `test-cases` directory as read-only comparison context

## Outputs

- `manual-decision-matrix-<package_id>.json`
- `manual-decision-matrix-<package_id>.md`

## Top-Level Fields

- `package_id`
- `matrix_status`: `pass`, `pass-with-warnings`, or `blocked`
- `benchmark_name`
- `source_artifacts`
- `summary`
- `decision_clusters`
- `reviewer_decision_rows`
- `compressed_manual_questions`
- `duplicate_risk_decision_groups`
- `source_grounding_decision_groups`
- `replacement_decision_groups`
- `defer_decision_groups`
- `readiness_impact`
- `expected_reviewer_outputs`
- `safety_statement`
- `canonical_write_allowed`: always false
- `manual_review_required`: true
- `ready_for_revised_draft_proposal_after_matrix`: false unless validated reviewer answers are supplied in a later stage
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## Compression Rules

Raw manual findings from decision pack, residual analysis, draft review and revision plan are grouped into reviewer rows by:

- duplicate-risk cluster or similar existing TC evidence;
- source requirement or candidate requirement;
- missing source fact type: user action, observable expected behavior, object/screen/field, condition;
- replacement strategy mode;
- defer/no-new-TC disposition.

The JSON may retain raw findings as `compressed_manual_questions`. Markdown should prioritize compact reviewer rows and concise evidence summaries.

## Req-To-Draft Mapping

Stage 9D.6 should build a conservative `req_uid -> draft_id` map from real source proposal drafts and supporting Stage 9 artifacts. It must not create synthetic draft ids.

Summary diagnostics should include:

- `draft_mapping_diagnostics`
- `req_to_draft_map_count`
- `unmapped_req_uids`
- `rows_with_missing_affected_drafts`
- `fixed_rows`

High-confidence mappings require the source draft proposal to directly list the `req_uid` or `candidate_req_uid`. Medium confidence may use a unique `source_req_id` relation. Low-confidence mappings must not be used to make a row Stage 9E eligible.

Reviewer rows should populate `affected_drafts` when affected requirements map to real draft candidates. If no real draft maps, the row remains draftless and the diagnostic warning should explain the gap.

## Decision Options

Each reviewer row exposes explicit options. Options record reviewer intent only and must have `creates_or_edits_canonical_tc=false`.

Allowed next actions:

- `revise_draft`
- `replace_draft`
- `extend_existing_tc`
- `defer`
- `no_new_tc_with_rationale`
- `request_source_clarification`
- `split_candidate`
- `keep_manual_only`

No option directly creates or edits canonical test cases. Any option that later enables Stage 9E still requires reviewer answer validation.

## Duplicate-Risk Decisions

Duplicate-risk rows must show:

- affected draft ids and requirement ids;
- similar existing TC refs;
- why overlap exists;
- whether the reviewer should choose separate new TC, extend existing TC, no-new-TC, or defer.

Existing TC text is coverage evidence only. It must not be treated as a source of business rules.

## Source-Grounding Decisions

Source-grounding rows distinguish:

- facts available from real table/header/row context;
- facts still ambiguous;
- facts still absent;
- facts blocked by duplicate risk rather than source extraction.

If a fact is ambiguous or absent, the row should route to source clarification, defer, split candidate, or keep manual-only. The matrix must not invent executable steps or expected behavior.

## Replacement And Defer Decisions

Rejected or weak drafts are not patched in place. The reviewer must choose whether a future stage should:

- rewrite from source;
- split the candidate;
- extend an existing TC;
- defer;
- close as no-new-TC with rationale.

## Readiness Rules

Stage 9D.6 never marks Stage 9E ready merely because rows were compressed.

Required values for this stage:

- `canonical_write_allowed=false`
- `manual_review_required=true`
- `ready_for_revised_draft_proposal_after_matrix=false`
- `readiness_impact.can_proceed_to_stage_9e_without_answers=false`

The matrix can improve `manual_decision_flow` from `gap` to `partial` when raw findings are substantially compressed into actionable rows. It should not mark the capability as `works` unless the remaining rows are small, complete and directly answerable.

## Markdown Sections

Markdown output should include:

1. Summary.
2. Compression summary.
3. Reviewer Decision Matrix.
4. Duplicate-risk decision groups.
5. Source-grounding decision groups.
6. Replacement/defer groups.
7. Required reviewer outputs.
8. Readiness impact.
9. Safety statement.
10. Warnings and blocking reasons.
