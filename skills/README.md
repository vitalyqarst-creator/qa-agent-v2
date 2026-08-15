# Skills Map

Canonical list of active skills:

- `ft-source-locator` - locate the target FT package and related materials.
- `ft-practical-route` - default v1 route for one confirmed FT scope.
- `ft-scope-analyzer` - propose external scopes by FT sections/subsections, confirm selected-scope boundaries, and record `coverage gaps`.
- `ft-test-case-writer` - write new test cases for an already selected scope.
- `ft-test-case-reviewer` - review existing test cases.
- `ft-ui-automation-prep` - verify an accepted practical baseline in the real UI and prepare an automation-ready version.
- `agent-architecture-auditor` - audit `AGENTS.md`, `skills/`, `references/`, and scripts.

## Which Skill to Use

- If the first task is to identify which FT to use: `ft-source-locator`.
- If the FT package is selected but the exact requirement fragment is not selected yet, or a large FT must be split into scopes: `ft-scope-analyzer`.
- If the user asks to write test cases for a normal FT scope, use `ft-practical-route` v1. Chain: source scope and BA questions -> matrix -> mandatory separate-session matrix review -> TC -> final separate-session TC review. Each review phase permits one complete writer revision, one closure check and at most one narrow micro-closure of an existing local finding. Separate-session means a real top-level Codex thread; sub-agents do not count. Missing data/UI/observability receives `needs-test-data`, `candidate-ui-calibration` or `blocked-observability` and does not stop unambiguous tests. Full contract: `references/agent/practical-test-case-route-v1.md`.
- If the scope is fixed and new cases must be written in one writer pass without independent review: `ft-test-case-writer`, but still follow practical-route quality gates.
- If cases already exist and review is needed: `ft-test-case-reviewer`. By default, it runs in `full` mode and performs `traceability` -> `structure` -> `test-design`.
- If an accepted baseline must be checked against the real UI before automation: `ft-ui-automation-prep`.
- If the request is about agent architecture, duplication, knowledge placement, and skill boundaries: `agent-architecture-auditor`.

## Typical Chains

- New test-case suite, macro-stage default: `ft-practical-route` v1. Isolated phase skills remain available only for a user-requested isolated stage. Do not materialize manifests, attestations, receipts or workflow state in v1.
- Automation-ready preparation after baseline release: `ft-ui-automation-prep`
- Existing-suite review: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-reviewer`
- Agent-layer audit: `agent-architecture-auditor` with script-first workflow (`skills/agent-architecture-auditor/scripts/audit_agent_architecture.py` -> manual interpretation)

## Instruction Context

For tasks where instruction volume matters, use the resolver:

```powershell
python scripts/resolve_instruction_context.py --phase writer --mode initial_draft --scope-profile table --budget-report
```

The canonical loading manifest lives in `references/agent/instruction-loading-manifest.md`. It defines only the set of instruction files for a scenario; workflow and QA rules remain in `SKILL.md` and `references/`.

## Canonical References

- Agent governance: [../references/agent](../references/agent)
- QA rules and formats: [../references/qa](../references/qa)
- Instruction contracts: [../references/agent/instruction-contract-index.md](../references/agent/instruction-contract-index.md)
- Instruction loading manifest: [../references/agent/instruction-loading-manifest.md](../references/agent/instruction-loading-manifest.md)
- Task-start skill routing: [../references/agent/task-start-skill-routing-format.md](../references/agent/task-start-skill-routing-format.md)
- Practical test-case route v1: [../references/agent/practical-test-case-route-v1.md](../references/agent/practical-test-case-route-v1.md)
- Legacy practical v0.9: [../references/agent/practical-test-case-route-v0.9.md](../references/agent/practical-test-case-route-v0.9.md)
- Coverage class catalog: [../references/qa/coverage-class-catalog.md](../references/qa/coverage-class-catalog.md)
- User interaction guide: [../references/agent/user-interaction-guide.md](../references/agent/user-interaction-guide.md)
- End-to-end use case: [../references/agent/test-case-writing-use-case.md](../references/agent/test-case-writing-use-case.md)
