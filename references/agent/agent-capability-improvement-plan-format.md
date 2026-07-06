# Agent Capability Improvement Plan Format

This artifact converts `agent_capability_findings` from a benchmark decision pack into a planning-only implementation roadmap.

It does not create canonical test cases, revised draft proposals, patches, or apply steps.

## Inputs

- `new-tc-revision-decision-pack-<package_id>.json` as the primary source of truth.
- Related Stage 9A-9D artifacts only for context.
- Instruction surfaces and QA references only to identify candidate documentation targets.

## Outputs

- `agent-capability-improvement-plan-<package_id>.json`
- `agent-capability-improvement-plan-<package_id>.md`

## Top-Level Fields

- `package_id`
- `benchmark_name`
- `plan_status`: `pass`, `pass-with-warnings`, or `blocked`
- `source_decision_pack_path`
- `capability_findings_summary`
- `improvement_items`
- `instruction_update_plan`
- `code_update_plan`
- `test_update_plan`
- `safety_preservation_plan`
- `implementation_sequence`
- `acceptance_criteria`
- `non_goals`
- `expected_next_stage`
- `input_paths`
- `warnings`
- `blocking_reasons`
- `created_at_utc`
- `created_by_tool`

## Improvement Items

Each item records:

- `improvement_id`
- `capability_area`
- `priority`: `P0`, `P1`, `P2`, or `P3`
- `problem_statement`
- `root_cause_hypothesis`
- `proposed_change_type`
- `proposed_change_summary`
- `target_files`
- `expected_benefit`
- `risk`
- `dependencies`
- `acceptance_criteria`
- `out_of_scope`
- `ready_for_implementation`

`gap` findings should normally become `P1` or `P2` items. `partial` findings usually become `P2` items. A working safety gate should become a preservation item, not a risky rewrite.

## Safety Rules

- Do not create or edit canonical test cases.
- Do not create revised draft proposals.
- Do not run `--apply`.
- Do not apply patches or use `git apply`.
- Do not modify the benchmark proposal/review/revision-plan/decision-pack artifacts.
- Do not use existing TC content as a source of new business behavior.
- Do not force readiness to true.
