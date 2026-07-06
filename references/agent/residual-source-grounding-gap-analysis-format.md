# Residual Source Grounding Gap Analysis Format

Stage 9D.4 is a read-only diagnostic stage for create-new-candidate packages after source-grounding and draft-quality guardrails have been implemented.

It explains why drafts still need manual decisions or source-grounding work. It must not create revised drafts, canonical test cases, apply plans, or patches.

## Output Files

- `residual-source-grounding-gap-analysis-<package_id>.json`
- `residual-source-grounding-gap-analysis-<package_id>.md`

For AutoFin benchmark package `WPKG-000001`, the output names are:

- `residual-source-grounding-gap-analysis-WPKG-000001.json`
- `residual-source-grounding-gap-analysis-WPKG-000001.md`

## ResidualSourceGroundingGapAnalysis

Fields:

- `package_id`
- `analysis_status`: `pass | pass-with-warnings | blocked`
- `benchmark_name`
- `source_artifacts`
- `summary`
- `draft_gap_analyses`
- `requirement_gap_analyses`
- `extractor_gap_findings`
- `source_absence_findings`
- `manual_decision_findings`
- `aggregate_context_findings`
- `duplicate_risk_blockers`
- `recommended_agent_improvements`
- `recommended_manual_questions`
- `next_stage_recommendation`
- `canonical_write_allowed`: always `false`
- `manual_review_required`: always `true`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

`analysis_status=blocked` is required when core Stage 9 artifacts are missing, unparsable, or have package-id mismatches.

## DraftGroundingGapAnalysis

Fields:

- `draft_id`
- `proposed_tc_id`
- `is_executable_draft`
- `contains_generic_placeholders`
- `source_grounding_status`
- `duplicate_risk_status`
- `candidate_req_uids`
- `source_req_ids`
- `missing_facts`
- `available_facts`
- `gap_classification`
- `root_cause`
- `evidence`
- `recommended_action`
- `manual_questions`
- `can_be_fixed_by_extractor`
- `can_be_fixed_by_instruction_update`
- `requires_human_decision`
- `should_defer`

Executable drafts are still diagnostic only. They must not be marked create-ready if duplicate-risk or manual decisions remain.

## RequirementGroundingGapAnalysis

Fields:

- `req_uid`
- `source_req_id`
- `source_text`
- `normalized_text`
- `object`
- `condition`
- `expected_behavior`
- `source_anchors`
- `has_object`
- `has_condition`
- `has_user_action`
- `has_expected_behavior`
- `missing_facts`
- `available_source_fragments`
- `registry_evidence`
- `diff_evidence`
- `impact_evidence`
- `gap_classification`
- `recommended_action`

Existing TC content may appear only as duplicate-risk comparison evidence from upstream artifacts. It is not a source of business rules.

## Gap Classifications

- `source_fact_absent`: the checked artifacts do not contain the fact needed for safe executable drafting.
- `source_fact_present_not_extracted`: a fact appears in registry/source text but was not promoted into grounding fields.
- `source_fact_ambiguous`: source text exists but does not define a safe action or oracle.
- `aggregate_context_only`: only aggregate/assembled source context is available.
- `table_or_anchor_context_needed`: table row/header/xpath/anchor context is needed before drafting.
- `duplicate_risk_prevents_decision`: duplicate-risk review blocks create-new readiness.
- `manual_business_decision_required`: a human decision remains necessary.
- `draft_generation_rule_gap`: draft generation emitted output that should be blocked by quality rules.
- `unknown`: artifacts do not support a narrower classification.

## RecommendedAgentImprovement

Fields:

- `improvement_id`
- `capability_area`: `source_grounding | draft_quality | duplicate_risk_handling | manual_decision_flow | requirement_registry | impact_mapping`
- `priority`: `P0 | P1 | P2 | P3`
- `problem`
- `evidence`
- `proposed_change`
- `target_files`
- `acceptance_criteria`
- `expected_metric_change`
- `ready_for_implementation`

Recommendations must generalize to future FT packages. Do not add AutoFin-specific hacks.

## Stage 9D.5 Table/Anchor Metrics

`summary` should include:

- `table_context_available_count`
- `table_context_used_count`
- `real_table_context_available_count`
- `real_table_context_used_count`
- `fallback_table_context_count`
- `header_cells_available_count`
- `row_cells_available_count`
- `neighboring_rows_available_count`
- `table_context_ambiguous_count`
- `table_context_missing_count`
- `anchor_context_available_count`
- `anchor_context_used_count`
- `source_fact_ambiguous_count`
- `source_fact_present_not_extracted_count`
- `source_fact_absent_count`

Use these metrics to separate:

- table context found and usable;
- real OOXML row/header context found;
- fallback table context used because real context is unavailable;
- table context found but ambiguous;
- table context absent;
- aggregate context only;
- duplicate-risk blockers;
- manual business decisions.

## Markdown Expectations

The Markdown artifact must include:

- summary;
- Stage 9D.3 metrics;
- residual gap breakdown;
- draft-level gap table;
- requirement-level gap table;
- root cause categories;
- extractor gaps;
- source absence findings;
- aggregate/table/anchor context findings;
- duplicate-risk blockers;
- manual decision findings;
- recommended agent improvements;
- recommended manual questions;
- next stage recommendation;
- safety statement.

## Safety Rules

- Do not create or edit canonical test-case files.
- Do not create canonical TC markdown.
- Do not create revised draft proposal artifacts.
- Do not modify Stage 9A-9D.3 artifacts.
- Write only the Stage 9D.4 analysis JSON/Markdown artifacts.
- Do not run `--apply`.
- Do not use `git apply` or `patch`.
- Do not process completed packages `WPKG-000002` / `WPKG-000003` or large/unlinked packages `WPKG-000004` / `WPKG-000005`.
- Keep `canonical_write_allowed=false`.
- Keep `manual_review_required=true`.
