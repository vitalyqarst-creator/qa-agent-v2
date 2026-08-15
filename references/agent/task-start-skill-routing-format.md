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

Keep instruction-loading scenarios and verification gates in the internal routing
decision, handoff and validation artifacts. Do not put internal route/profile
names or versions, instruction scenario IDs,
schema names or individual gate names into the user-facing preflight line unless
the user explicitly asks for them.

Keep the disclosure brief. It is not a consent step unless the task itself is ambiguous or unsafe.

When the user supplies an explicit checked-in full-process config with
`schema_version = 2`, prefer `production.checked_in_observation`. Do not select
that route from generic wording such as "full run" alone. Without an explicit
schema-v2 config, keep the generic `production.bounded_full_loop` route and its
source-locator/scope-analyzer chain.

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
      "id": "test_cases.practical_v1",
      "task_type": "Default route for ordinary FT test-case writing: compact source scope and BA questions, Russian matrix, separate-session matrix review, canonical test cases and separate-session TC review. It reaches baseline or review-failed without controller receipts or repair loops.",
      "skill_chain": ["ft-practical-route"],
      "instruction_scenarios": [
        {"skill": "ft-practical-route", "scenario": "practical.v1"}
      ],
      "verification_gates": ["source-scope.md identifies scope, source refs, visual bindings and applicable BA decisions", "scope-clarification-requests.md exists, including when it has no questions", "test-design-matrix.md is Russian and is accepted by a distinct top-level reviewer session before TC writing", "test-case file is visible as draft before final review", "TC review is performed by a distinct top-level reviewer session", "one complete writer revision and one finding-closure check per phase at most", "no manifests, attestations, receipts or repair loops are created"]
    },
    {
      "id": "test_cases.legacy_practical_v0_9",
      "task_type": "Resume an already started practical-v0.9 scope when the user explicitly requests that legacy route.",
      "skill_chain": ["ft-practical-route"],
      "instruction_scenarios": [
        {"skill": "ft-practical-route", "scenario": "practical.v0_9"}
      ],
      "verification_gates": ["legacy v0.9 scope already exists", "user explicitly requested v0.9 continuation"]
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
      "verification_gates": ["findings artifact exists", "traceability matrix exists when coverage review is required", "direct full review does not create an accepted practical baseline"]
    },
    {
      "id": "ui_automation_prep.accepted_baseline",
      "task_type": "Verify an accepted FT-first baseline in UI and prepare automation-ready cases.",
      "skill_chain": ["ft-ui-automation-prep"],
      "instruction_scenarios": [
        {"skill": "ft-ui-automation-prep", "scenario": "ui_automation_prep.accepted_baseline"}
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
      "prompt": "Напиши тест-кейсы по выбранному scope ФТ и доведи scope до accepted baseline или честного blocker-а.",
      "expected_route_id": "test_cases.practical_v1",
      "expected_skill_chain": ["ft-practical-route"],
      "expected_instruction_scenarios": ["practical.v1"]
    },
    {
      "prompt": "Подготовь accepted baseline к UI automation.",
      "expected_route_id": "ui_automation_prep.accepted_baseline",
      "expected_skill_chain": ["ft-ui-automation-prep"],
      "expected_instruction_scenarios": ["ui_automation_prep.accepted_baseline"]
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
