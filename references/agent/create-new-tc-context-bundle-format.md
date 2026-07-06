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
