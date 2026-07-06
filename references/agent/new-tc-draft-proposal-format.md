# New TC Draft Proposal Format

Stage 9B creates draft-only test-case candidates from a Stage 9A create-new-TC context bundle. It is a proposal stage, not a canonical create/apply stage.

## Scope

This format applies to `create_new_candidate` packages such as `WPKG-000001`.

It must not:

- create canonical `.md` test-case files;
- edit existing canonical test-case files;
- apply patches;
- run `--apply`;
- assign authoritative final `TC-*` ids;
- process completed traceability packages;
- process large/unlinked packages that require a split/map flow.

## Required Inputs

- `create-new-tc-context-bundle-<package-id>.json`
- canonical `fts/<ft-slug>/test-cases` directory, read-only
- optional supporting pipeline artifacts for traceability review:
  - `manual-update-packages.<old>-to-<new>.json`
  - `writer-package-tasks.<old>-to-<new>.json`
  - `test-case-update-plan.<old>-to-<new>.json`
  - `impact-report.<old>-to-<new>.json`
  - `requirements-diff.<old>-to-<new>.json`
  - requirements registries

## Output Artifacts

- `new-tc-draft-proposal-<package-id>.json`
- `new-tc-draft-proposal-<package-id>.md`

No patch file is produced because there is no canonical target to patch in this stage.

## JSON Model

Top-level `NewTcDraftProposal` fields:

- `package_id`
- `proposal_status`: `pass | pass-with-warnings | blocked`
- `package_type`
- `source_bundle_path`
- `draft_test_cases`
- `deferred_groups`
- `duplicate_risk_decisions`
- `coverage_summary`
- `recommended_review_focus`
- `manual_review_required`: always `true`
- `canonical_write_allowed`: always `false`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

`DraftTestCaseCandidate` fields:

- `draft_id`
- `proposed_tc_id`: draft-only id such as `DRAFT-TC-WPKG-000001-001`
- `target_file_path`
- `target_section`
- `requires_new_file`
- `title`
- `source_requirement_uids`
- `source_req_ids`
- `change_ids`
- `impact_ids`
- `plan_item_ids`
- `coverage_intent`
- `preconditions`
- `test_data`
- `steps`
- `expected_results`
- `traceability_refs`
- `traceability_line`
- `duplicate_risk_level`: `low | medium | high`
- `duplicate_risk_notes`
- `draft_confidence`: `low | medium | high`
- `requires_manual_review`: always `true`
- `warnings`

`DeferredGroup` fields:

- `group_id`
- `candidate_req_uids`
- `reason`
- `required_manual_decision`
- `warnings`

`DuplicateRiskDecision` fields:

- `candidate_req_uid`
- `similar_tc_id`
- `similar_file_path`
- `risk`
- `decision`: `draft_with_warning | defer | maybe_extend_existing_tc | needs_manual_review`
- `rationale`

## Drafting Rules

- Build drafts from `candidate_groups`.
- Respect `suggested_tc_count`; split multi-requirement groups when the bundle suggests multiple checks.
- Use draft ids only; never output final authoritative canonical TC IDs.
- Preserve traceability to generated `REQ-*`, `source_req_id` values when available, plan items, impact ids and change ids.
- Do not reuse traceability refs from existing similar TC unless the bundle explicitly supports that relation.
- For low duplicate risk, draft with warning when needed.
- For medium duplicate risk, draft only with clear duplicate-risk notes and manual review.
- For high duplicate risk, defer unless a later reviewed instruction explicitly allows `draft_with_warning`.
- If source behavior is ambiguous or aggregate-derived, add warnings and require manual review.
- If expected behavior cannot be made observable from source context, defer instead of inventing a business rule.

## Status Rules

- `blocked`: bundle is missing, unparsable, has blocking reasons, or is not `create_new_candidate`.
- `pass-with-warnings`: drafts or deferrals exist and manual review is required. This is the normal status.
- `pass`: only possible when there are no warnings, no duplicate-risk decisions and no deferred groups. This is uncommon.

## Markdown Expectations

The Markdown artifact must include:

- summary;
- safety statement;
- draft TC candidates with draft id, traceability, preconditions, test data, steps, expected results, coverage intent and duplicate-risk notes;
- deferred groups;
- duplicate risk decisions;
- review focus checklist;
- warnings and blocking reasons.

## Stage 9D.3 Source Grounding And Draft Quality Rules

Each draft candidate must expose `source_grounding_profiles`, `grounding_confidence`, `manual_questions`, `contains_generic_placeholders`, `draft_quality_flags`, and `is_executable_draft`.

Executable draft steps require source-backed facts for:

- concrete object, screen, section, field, table, value, or rule under test;
- concrete condition or data state;
- user action explicitly supported by source text or anchors;
- observable expected behavior supported by source text.

If these facts are missing, the draft must remain draft-only and non-executable. It may include manual source-grounding questions, but it must not pretend that a writer can execute or apply it safely.

The proposal builder must not emit generic placeholder steps such as "open the source screen", "set up the source-backed condition", or "perform the action needed to observe the behavior". Missing source facts must be recorded in `missing_facts`, `manual_questions`, warnings, and review focus instead of being converted into invented steps.

Existing similar TC content may be used only as duplicate-risk or comparison evidence. It is not a source of business rules and must not be copied into a new draft unless the source requirements independently support the behavior.

## Stage 9D.5 Enriched Source Facts

Draft grounding must use `enriched_source_facts`, `source_anchor_contexts`, and `table_source_contexts` before falling back to legacy `object`, `condition`, and `expected_behavior` fields.

Rules:

- Source anchors are evidence, not instructions to invent missing behavior.
- Table row/header/cell context may support object or expected behavior only when the evidence is explicit.
- User action may be promoted only when source text or table context explicitly describes an action or user interaction.
- Table context without action or oracle must keep `is_executable_draft=false`.
- Aggregate-only context must remain manual-review-only.
