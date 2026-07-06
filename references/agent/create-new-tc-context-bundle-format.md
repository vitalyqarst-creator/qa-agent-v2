# Create New TC Context Bundle Format

Stage 9A builds a read-only context bundle for a `create_new_candidate` work package. It prepares evidence for a later draft-only writer proposal, but it does not create canonical test cases and does not edit existing test-case files.

## Scope

This format is intended for `WPKG-000001` style packages where:

- `package_type=create_new_candidate`;
- package items are not bound to existing canonical TC files;
- future work must first produce draft-only proposals and review artifacts;
- controlled canonical creation is a later stage and is not authorized here.

Large, unlinked manual-review, and completed traceability packages are out of scope.

## Required Inputs

- `manual-update-packages.<old>-to-<new>.json`
- `writer-package-tasks.<old>-to-<new>.json`
- `test-case-update-plan.<old>-to-<new>.json`
- `impact-report.<old>-to-<new>.json`
- `requirements-diff.<old>-to-<new>.json`
- `requirements.<old>.jsonl`
- `requirements.<new>.jsonl`
- `source-manifest.<old>.json`
- `source-manifest.<new>.json`
- canonical `fts/<ft-slug>/test-cases` directory, read-only

## Output Artifacts

- `create-new-tc-context-bundle-<package-id>.json`
- `create-new-tc-context-bundle-<package-id>.md`

## JSON Model

Top-level `CreateNewTcContextBundle` fields:

- `package_id`
- `bundle_status`: `pass | pass-with-warnings | blocked`
- `package_type`
- `plan_item_ids`
- `impact_ids`
- `change_ids`
- `candidate_requirements`
- `candidate_groups`
- `existing_tc_similarity`
- `recommended_draft_targets`
- `coverage_obligations`
- `duplicate_risks`
- `source_context`
- `registry_context`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

`CandidateRequirement` fields:

- `req_uid`
- `source_req_id`
- `source_version`
- `change_type`
- `requirement_type`
- `object`
- `condition`
- `expected_behavior`
- `source_text`
- `normalized_text`
- `source_anchors`
- `diff_entry_id`
- `impact_id`
- `plan_item_id`
- `confidence`
- `warnings`

`CandidateGroup` fields:

- `group_id`
- `group_reason`
- `candidate_req_uids`
- `source_req_ids`
- `suggested_tc_count`
- `suggested_tc_theme`
- `draft_allowed`
- `requires_manual_review`
- `warnings`

`ExistingTcSimilarity` fields:

- `candidate_req_uid`
- `similar_tc_id`
- `similar_file_path`
- `similarity_reason`
- `overlap_refs`
- `overlap_keywords`
- `risk`: `low | medium | high`

`RecommendedDraftTarget` fields:

- `target_file_path`
- `target_section`
- `suggested_tc_id_prefix`
- `reason`
- `requires_new_file`
- `warnings`

## Safety Rules

- Work only with the requested create-new package.
- Only include plan items whose action is `create_new_candidate`.
- Do not write or modify canonical test-case files.
- Do not create new canonical TC markdown.
- Do not generate final TC bodies.
- Do not assign final TC IDs as authoritative.
- Do not merge requirements into one TC without explicit grouping rationale.
- Do not process large/unlinked packages in this bundle.
- Do not process completed traceability packages.
- Do not run apply stages.
- If required artifacts are missing or inconsistent, set `bundle_status=blocked`.
- If an existing TC appears to cover the requirement, record a duplicate risk instead of treating the candidate as create-ready.
- If source context is ambiguous, set `requires_manual_review=true` on the relevant group or obligation.

## Status Rules

- `blocked`: a required input is missing, package is not `create_new_candidate`, task/package/plan links are inconsistent, or the package targets existing canonical TC files.
- `pass-with-warnings`: the bundle is usable but manual review, low-confidence requirements, aggregate/ambiguous source context, or duplicate risks exist.
- `pass`: all links are consistent and no warnings are present. This is uncommon because create-new candidates normally require manual review.

## Markdown Expectations

The Markdown artifact must include:

- package summary;
- candidate requirements table;
- candidate groups and grouping rationale;
- duplicate risks;
- recommended draft targets;
- coverage obligations;
- warnings and blockers;
- explicit statement that no canonical TC was created or modified.

## Stage 9D.3 Source Grounding Inputs

The context bundle should preserve source anchors and source text needed for later grounding. Draft stages must use those facts as the only business-rule source for new TC content.

Existing TC matches in the bundle are duplicate-risk evidence only. They may identify similar coverage, but they do not authorize copying steps, expected results, test data, headings, or traceability into a new draft.

When the bundle lacks a concrete object, condition, user action, or observable expected behavior, downstream draft stages must keep the item manual-review-only or non-executable until a source-backed clarification is available.

## Stage 9D.5 Table And Anchor Source Fact Enrichment

`CandidateRequirement` may include these optional backward-compatible fields:

- `source_anchor_contexts`
- `table_source_contexts`
- `enriched_source_facts`
- `source_fact_confidence`
- `source_fact_warnings`
- `manual_questions`

Table cell facts must be interpreted with row/header/anchor context. A table cell or OOXML anchor is evidence, not permission to invent missing object, action, condition, or expected behavior.

Aggregate context must be flagged. Aggregate-derived source context can support diagnostics, but it cannot by itself authorize an executable draft.

Existing TC comparison remains non-authoritative for business behavior. It may identify duplicate risk only.

## Stage 9D.5a Real OOXML Table Context

When a source anchor points to an available DOCX OOXML part with `w:tbl[n]/w:tr[m]/w:tc[k]`, the bundle should populate `TableSourceContext` from the real table:

- `header_cells`
- `row_cells`
- `cell_text`
- `row_text`
- `neighboring_rows`
- `table_id`, `row_index`, `column_index`

If the raw OOXML source is unavailable or the xpath lacks table/row/cell indexes, the bundle may keep a fallback table context, but it must label it with `table context fallback used; real row/header context unavailable`.

Header/row/neighbouring-row content is audit evidence. It must not be treated as permission to invent missing business behavior.
