# Task-Start Skill Routing Format

This reference is the canonical contract for the short preflight line an agent emits before substantive work on a new user task.

It does not replace `skills/README.md` or `instruction-loading-manifest.md`:

- `skills/README.md` remains the human dispatch map for active skills.
- `instruction-loading-manifest.md` remains the source of instruction groups and budgets.
- This file connects task types to skill chains and manifest scenarios.

## Preflight Disclosure

Before substantive work, state:

- selected skill or skill chain;
- why this route matches the task;
- instruction-loading scenario or scenarios;
- verification gates that will prove the work.

Keep the disclosure brief. It is not a consent step unless the task itself is ambiguous or unsafe.

## Routing Map

The JSON block is canonical. Tests and architecture audit parse it directly.

<!-- task-start-skill-routing:v1 -->
```json
{
  "version": 1,
  "preflight_required_fields": [
    "task_type",
    "selected_skills",
    "skill_order",
    "selection_reason",
    "instruction_scenarios",
    "verification_gates"
  ],
  "routes": [
    {
      "id": "source.locate_ft_package",
      "task_type": "Find an FT package, source document, support files or mockups.",
      "skill_chain": ["ft-source-locator"],
      "instruction_scenarios": [
        {"skill": "ft-source-locator", "scenario": "source_locator.discovery"}
      ],
      "verification_gates": ["source-selection.md exists or user-facing source ambiguity is recorded"]
    },
    {
      "id": "scope.propose_candidates",
      "task_type": "Propose external scopes before the user confirms one scope.",
      "skill_chain": ["ft-source-locator", "ft-scope-analyzer"],
      "instruction_scenarios": [
        {"skill": "ft-source-locator", "scenario": "source_locator.discovery"},
        {"skill": "ft-scope-analyzer", "scenario": "scope.agent_proposed"}
      ],
      "verification_gates": ["scope-options.md exists", "scope-selection prompt exists when user choice is needed"]
    },
    {
      "id": "scope.confirm_manual",
      "task_type": "Analyze a user-provided section or scope boundary.",
      "skill_chain": ["ft-source-locator", "ft-scope-analyzer"],
      "instruction_scenarios": [
        {"skill": "ft-source-locator", "scenario": "source_locator.discovery"},
        {"skill": "ft-scope-analyzer", "scenario": "scope.manual"}
      ],
      "verification_gates": ["scope-contract.md exists", "coverage gaps are linked to source evidence"]
    },
    {
      "id": "writer.initial_simple",
      "task_type": "Write new test cases for a confirmed simple scope.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.initial_draft.simple"}
      ],
      "verification_gates": ["test-case file exists", "writer quality gate passes"]
    },
    {
      "id": "writer.prepared_session_initial",
      "task_type": "Write an initial draft in a fresh session from a verified compact prepared stage package.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.session_prepared_initial_draft"}
      ],
      "verification_gates": ["prepared package hashes pass", "atomic obligation gate passes", "writer quality gate passes"]
    },
    {
      "id": "writer.initial_table",
      "task_type": "Write new test cases for a confirmed table-heavy or row-level parity scope.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.initial_draft.table"}
      ],
      "verification_gates": ["source-row-inventory.md exists when row parity is required", "table design artifacts exist", "writer quality gate passes"]
    },
    {
      "id": "writer.initial_table_deep_debug",
      "task_type": "Debug a table-heavy writer package with optional coverage metrics, risk/state templates or reviewer-oriented table diagnostics.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.initial_draft.table.deep_debug"}
      ],
      "verification_gates": ["deep/debug need is explicit", "default table writer remains compact", "scoped validator or reviewer finding is rerun"]
    },
    {
      "id": "writer.initial_ui",
      "task_type": "Write new test cases for a confirmed UI scope with mockups or screen images.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.initial_draft.ui"}
      ],
      "verification_gates": ["mockup-visual-inventory.md exists when mockups are used", "test-case file exists", "writer quality gate passes"]
    },
    {
      "id": "writer.initial_numeric",
      "task_type": "Write new test cases for numeric, date, length, mask or allowed-symbol constraints.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.initial_draft.numeric"}
      ],
      "verification_gates": ["boundary/equivalence coverage is explicit", "writer quality gate passes"]
    },
    {
      "id": "writer.initial_integration",
      "task_type": "Write new test cases for integration, async, API, persistence or internal effects.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.initial_draft.integration"}
      ],
      "verification_gates": ["observable artifacts are identified", "internal-only effects are routed to gaps when not observable"]
    },
    {
      "id": "writer.revision_from_findings",
      "task_type": "Revise an existing test-case set from structured reviewer findings.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.revision_from_findings"}
      ],
      "verification_gates": ["writer response maps every finding", "updated test cases exist", "no unresolved blocking findings are hidden"]
    },
    {
      "id": "writer.remediate_style",
      "task_type": "Fix style, wording or formatting findings without changing source/scope.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.remediation.style"}
      ],
      "verification_gates": ["style finding is resolved", "test meaning and traceability are unchanged"]
    },
    {
      "id": "writer.remediate_style_deep_examples",
      "task_type": "Use long style examples for a rare wording or formatting remediation that the compact checklist cannot resolve.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.remediation.style.deep_examples"}
      ],
      "verification_gates": ["deep example need is explicit", "test meaning and traceability are unchanged"]
    },
    {
      "id": "writer.remediate_validator_failure",
      "task_type": "Repair validator or Writer Quality Gate failures.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.remediation.validator_failure"}
      ],
      "verification_gates": ["failed validator rule is rerun", "Writer Quality Gate passes or residual risk is explicit"]
    },
    {
      "id": "writer.remediate_validator_failure_deep_debug",
      "task_type": "Repair validator or Writer Quality Gate failures that require detailed deep references after the compact finding map is insufficient.",
      "skill_chain": ["ft-test-case-writer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-writer", "scenario": "writer.remediation.validator_failure.deep_debug"}
      ],
      "verification_gates": ["deep/debug need is explicit", "failed validator rule is rerun", "unaffected TC remain unchanged"]
    },
    {
      "id": "reviewer.full_existing_cases",
      "task_type": "Review existing test cases for coverage, structure and test design.",
      "skill_chain": ["ft-test-case-reviewer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.full_existing_cases"}
      ],
      "verification_gates": ["findings artifact exists", "traceability matrix exists when coverage review is required", "direct full review does not create lifecycle sign-off without session-based gates"]
    },
    {
      "id": "scope.review_gaps",
      "task_type": "Review scope coverage gaps and clarification requests before writer starts.",
      "skill_chain": ["ft-test-case-reviewer"],
      "instruction_scenarios": [
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.scope_gap_review"}
      ],
      "verification_gates": ["scope-gap-review.md exists", "gap review verdict routes to writer or back to scope analyzer"]
    },
    {
      "id": "review_cycle.session_based",
      "task_type": "Run a session-based writer/reviewer cycle with separate Codex sessions, max two semantic review rounds, versioned snapshots and final format review.",
      "skill_chain": ["ft-source-locator", "ft-scope-analyzer", "ft-test-case-writer", "ft-test-case-reviewer"],
      "instruction_scenarios": [
        {"skill": "ft-source-locator", "scenario": "source_locator.discovery"},
        {"skill": "ft-scope-analyzer", "scenario": "scope.manual"},
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.scope_gap_review"},
        {"skill": "ft-test-case-writer", "scenario": "writer.session_initial_draft"},
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.structure_preflight"},
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.semantic_traceability_test_design"},
        {"skill": "ft-test-case-writer", "scenario": "writer.session_semantic_revision"},
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.structure_format_final"},
        {"skill": "ft-test-case-writer", "scenario": "writer.session_format_revision"},
        {"skill": "ft-test-case-reviewer", "scenario": "reviewer.semantic_regression"},
        {"skill": "codex-sdk-runner", "scenario": "sdk_orchestration.review_cycle"}
      ],
      "verification_gates": ["cycle-state.yaml exists", "codex-session-map.yaml records each stage thread", "semantic review does not exceed two rounds", "version snapshots have snapshot-manifest.yaml", "signed-off requires semantic pass, format pass and semantic regression when format changed"]
    },
    {
      "id": "iteration.full_loop",
      "task_type": "Run writer-reviewer iteration until sign-off or unresolved findings are explicit.",
      "skill_chain": ["ft-source-locator", "ft-scope-analyzer", "ft-test-case-iteration"],
      "instruction_scenarios": [
        {"skill": "ft-source-locator", "scenario": "source_locator.discovery"},
        {"skill": "ft-scope-analyzer", "scenario": "scope.manual"},
        {"skill": "ft-test-case-iteration", "scenario": "iteration.full_loop"}
      ],
      "verification_gates": ["cycle-state.yaml exists", "cycle-state.yaml has terminal or next-stage status", "review-cycle snapshots exist when stages completed"]
    },
    {
      "id": "ui_automation_prep.signed_off",
      "task_type": "Verify signed-off test cases in UI and prepare automation-ready cases.",
      "skill_chain": ["ft-ui-automation-prep"],
      "instruction_scenarios": [
        {"skill": "ft-ui-automation-prep", "scenario": "ui_automation_prep.signed_off"}
      ],
      "verification_gates": ["ui-validation-report.md exists", "ui-evidence-index.md exists", "automation-ready file exists or blocker is recorded"]
    },
    {
      "id": "architecture.audit",
      "task_type": "Audit or change AGENTS.md, skills, references, instruction routing or architecture scripts.",
      "skill_chain": ["agent-architecture-auditor"],
      "instruction_scenarios": [
        {"skill": "agent-architecture-auditor", "scenario": "architecture.audit"}
      ],
      "verification_gates": ["architecture audit passes with --fail-on warning", "agent-layer tests pass when contracts changed"]
    }
  ],
  "golden_examples": [
    {
      "prompt": "Найди нужный FT-пакет и основной ФТ.",
      "expected_route_id": "source.locate_ft_package",
      "expected_skill_chain": ["ft-source-locator"],
      "expected_instruction_scenarios": ["source_locator.discovery"]
    },
    {
      "prompt": "Разбей большое ФТ на scope-ы и предложи, с чего начать.",
      "expected_route_id": "scope.propose_candidates",
      "expected_skill_chain": ["ft-source-locator", "ft-scope-analyzer"],
      "expected_instruction_scenarios": ["source_locator.discovery", "scope.agent_proposed"]
    },
    {
      "prompt": "Напиши тест-кейсы по подтвержденному простому scope.",
      "expected_route_id": "writer.initial_simple",
      "expected_skill_chain": ["ft-test-case-writer"],
      "expected_instruction_scenarios": ["writer.initial_draft.simple"]
    },
    {
      "prompt": "Создай draft в новой сессии из проверенного prepared stage-package.",
      "expected_route_id": "writer.prepared_session_initial",
      "expected_skill_chain": ["ft-test-case-writer"],
      "expected_instruction_scenarios": ["writer.session_prepared_initial_draft"]
    },
    {
      "prompt": "Напиши тест-кейсы по таблице с построчной трассировкой.",
      "expected_route_id": "writer.initial_table",
      "expected_skill_chain": ["ft-test-case-writer"],
      "expected_instruction_scenarios": ["writer.initial_draft.table"]
    },
    {
      "prompt": "Проверь существующие тест-кейсы по ФТ.",
      "expected_route_id": "reviewer.full_existing_cases",
      "expected_skill_chain": ["ft-test-case-reviewer"],
      "expected_instruction_scenarios": ["reviewer.full_existing_cases"]
    },
    {
      "prompt": "Run writer and reviewer in separate Codex sessions with two semantic review rounds and snapshots.",
      "expected_route_id": "review_cycle.session_based",
      "expected_skill_chain": ["ft-source-locator", "ft-scope-analyzer", "ft-test-case-writer", "ft-test-case-reviewer"],
      "expected_instruction_scenarios": ["source_locator.discovery", "scope.manual", "reviewer.scope_gap_review", "writer.session_initial_draft", "reviewer.structure_preflight", "reviewer.semantic_traceability_test_design", "writer.session_semantic_revision", "reviewer.structure_format_final", "writer.session_format_revision", "reviewer.semantic_regression", "sdk_orchestration.review_cycle"]
    },
    {
      "prompt": "Проведи writer-reviewer iteration до sign-off.",
      "expected_route_id": "iteration.full_loop",
      "expected_skill_chain": ["ft-source-locator", "ft-scope-analyzer", "ft-test-case-iteration"],
      "expected_instruction_scenarios": ["source_locator.discovery", "scope.manual", "iteration.full_loop"]
    },
    {
      "prompt": "Подготовь signed-off кейсы к UI automation.",
      "expected_route_id": "ui_automation_prep.signed_off",
      "expected_skill_chain": ["ft-ui-automation-prep"],
      "expected_instruction_scenarios": ["ui_automation_prep.signed_off"]
    },
    {
      "prompt": "Проверь архитектуру агента и instruction loading.",
      "expected_route_id": "architecture.audit",
      "expected_skill_chain": ["agent-architecture-auditor"],
      "expected_instruction_scenarios": ["architecture.audit"]
    }
  ]
}
```

## Maintenance Rules

- Add a route only when it changes skill selection or instruction scenario selection.
- Every route skill must exist in `skills/README.md`.
- Every route scenario must exist in `instruction-loading-manifest.md`.
- Every manifest scenario should be reachable from at least one route.
- Golden examples must point to route ids and scenarios from this JSON block.
