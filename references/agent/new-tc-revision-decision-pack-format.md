# New TC Revision Decision Pack Format

This artifact resolves what can be resolved from existing Stage 9A-9D artifacts and records the manual decisions that remain before creating a revised draft proposal.

It is read-only. It does not create revised drafts and does not authorize canonical test-case creation.

## Inputs

- `new-tc-draft-revision-plan-<package_id>.json`
- `new-tc-draft-review-<package_id>.json`
- `new-tc-draft-proposal-<package_id>.json`
- `create-new-tc-context-bundle-<package_id>.json`
- optional requirements diff, impact report, update plan and registries
- canonical `test-cases` directory as read-only comparison context

## Outputs

- `new-tc-revision-decision-pack-<package_id>.json`
- `new-tc-revision-decision-pack-<package_id>.md`

## Top-Level Fields

- `package_id`
- `decision_pack_status`: `pass`, `pass-with-warnings`, or `blocked`
- `source_revision_plan_path`
- `source_review_path`
- `source_proposal_path`
- `draft_decisions`
- `duplicate_risk_clusters`
- `existing_tc_comparisons`
- `source_grounding_resolutions`
- `replacement_strategies`
- `agent_capability_findings`
- `manual_decisions_required`
- `revised_draft_readiness`
- `canonical_write_allowed`: always false
- `manual_review_required`: true
- `input_paths`
- `warnings`
- `blocking_reasons`

## DraftDecision

The per-draft decision is one of:

- `revise_ready`
- `replace_ready`
- `defer`
- `maybe_extend_existing_tc`
- `needs_manual_decision`

`revise_ready` and `replace_ready` require source-backed executable steps, observable expected result, and resolved duplicate risk. If duplicate risk or source grounding is not resolved from artifacts, the draft remains `needs_manual_decision`.

## DuplicateRiskCluster

Duplicate-risk actions are clustered to reduce review volume. Clustering uses similar TC id, file path, draft id, source id and candidate behavior. A cluster records:

- involved drafts and candidate requirements
- similar TC ids and files
- highest risk
- cluster action: `differentiate`, `maybe_extend_existing_tc`, `defer`, or `no_action`
- whether manual decision and comparison are required

## ExistingTcComparison

Existing TC comparison is read-only. Existing TC text may be used only to identify overlap or difference; it must not be used as a source for new behavior unless the requirement context supports it.

## SourceGroundingResolution

Source grounding records usable source facts and missing facts. Executable steps require source-backed action/context plus a concrete object. Expected result must be observable and source-backed.

## ReplacementStrategy

Rejected drafts are handled explicitly. A replacement may be allowed only when the candidate has valid source facts and no blocking duplicate comparison. Otherwise the strategy is `defer` or `maybe_extend_existing_tc`.

## AgentCapabilityFinding

The decision pack includes one automatically generated finding for each agent capability area:

- `duplicate_risk_handling`
- `source_grounding`
- `draft_quality`
- `replacement_strategy`
- `manual_decision_flow`
- `safety_gate`

Each finding has:

- `finding_id`
- `capability_area`
- `status`: `works`, `partial`, or `gap`
- `evidence`
- `recommendation`
- `should_update_agent_instructions`

The findings are diagnostic. They do not change readiness by themselves and do not authorize writes.

Expected interpretation:

- `works` means the current agent behavior is sufficient for this capability in the observed pack.
- `partial` means the mechanism exists but still leaves meaningful manual work or weak evidence.
- `gap` means the current agent behavior is insufficient and agent instructions or implementation should be improved.

## Safety Rules

- Work only with the requested package.
- Do not create or edit canonical test-case files.
- Do not create revised draft proposal artifacts.
- Do not modify original Stage 9B, 9C, or 9D artifacts.
- Do not run `--apply`.
- Do not apply patches or use `git apply`.
- Keep `canonical_write_allowed=false`.

## Stage 9D.3 Source Grounding And Readiness Rules

Revision decisions must use source-grounding profiles from the draft proposal when available. A candidate is not ready for a revised draft proposal until the decision pack can identify source-backed usable facts for object, condition, user action, and observable expected behavior.

`needs_manual_decision_count` must remain greater than zero when duplicate-risk decisions, missing source actions, missing expected behavior, or unresolved manual questions remain.

The decision pack may recommend implementation improvements, but it must not force `ready_for_revised_draft_proposal=true` while grounding or duplicate-risk decisions are unresolved.

Agent capability findings should report source-grounding and draft-quality gaps separately from safety-gate behavior. A working safety gate is expected to keep canonical writes disabled even when the draft pipeline is incomplete.
