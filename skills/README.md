# Skills Map

Canonical list of active skills:

- `ft-source-locator` - locate the target FT package and related materials.
- `ft-scope-analyzer` - propose external scopes by FT sections/subsections, confirm selected-scope boundaries, and record `coverage gaps`.
- `ft-test-case-iteration` - build a source-bound shadow suite from an accepted source package and run the writer/gate/reviewer route through `ft-agent run`.
- `ft-test-case-writer` - write new test cases for an already selected scope.
- `ft-test-case-reviewer` - review existing test cases.
- `ft-ui-automation-prep` - post-iteration verification of signed-off cases in the real UI and preparation of an automation-ready version.
- `agent-architecture-auditor` - audit `AGENTS.md`, `skills/`, `references/`, and scripts.

## Which Skill to Use

- If the first task is to identify which FT to use: `ft-source-locator`.
- If the FT package is selected but the exact requirement fragment is not selected yet, or a large FT must be split into scopes: `ft-scope-analyzer`.
- If the scope is fixed and new cases must be written in one writer pass without a review cycle: `ft-test-case-writer`.
- If the scope is independently qualified and a production shadow is needed: `ft-test-case-iteration` through `ft-agent run`.
- If the scope has compiler-v3 obligations and an independently accepted v4 source contract: source-qualified `ft-test-case-iteration` `lean_v2` through one public `ft-agent run`; for new production attempts, explicitly set `writer_mode: model-runtime-prose`.
- If a new FT version must update a signed-off suite: conditional `ft-test-case-iteration` mode `incremental-update` through `scripts/run_incremental_update_iteration.py`; normal full-loop runs do not load its instructions.
- If a checked-in full-process config with `schema_version = 2` is explicitly provided: route directly to `ft-test-case-iteration` through `scripts/start_full_process_observation.py --execute`; generic discovery/scope chains remain for runs without that config.
- The old session-based writer/reviewer cycle remains a qualification/development compatibility tool and is not the production route.
- If cases already exist and review is needed: `ft-test-case-reviewer`. By default, it runs in `full` mode and performs `traceability` -> `structure` -> `test-design`.
- If the suite already has `signed-off` and must be checked against the real UI before automation: `ft-ui-automation-prep`.
- If the request is about agent architecture, duplication, knowledge placement, and skill boundaries: `agent-architecture-auditor`.

## Typical Chains

- New test-case suite: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-writer`
- Recommended production shadow after qualification: `ft-test-case-iteration` through `ft-agent run` with schema-v2 config.
- Full new scope in the development environment: `ft-source-locator` -> `ft-scope-analyzer` -> independent source review -> `ft-test-case-iteration`.
- New FT-version update: `ft-test-case-iteration` in `incremental-update` mode after explicit selection of both versions and target scope.
- Automation-ready preparation after sign-off: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-iteration` -> `ft-ui-automation-prep`
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
- Source-qualified iteration: [../references/agent/lean-v2-iteration.md](../references/agent/lean-v2-iteration.md)
- Session-based review cycle: [../references/agent/session-based-review-cycle-format.md](../references/agent/session-based-review-cycle-format.md)
- Codex SDK orchestration: [../references/agent/codex-sdk-orchestration-format.md](../references/agent/codex-sdk-orchestration-format.md)
- Quality feedback loop: [../references/agent/quality-feedback-loop.md](../references/agent/quality-feedback-loop.md)
- User interaction guide: [../references/agent/user-interaction-guide.md](../references/agent/user-interaction-guide.md)
- End-to-end use case: [../references/agent/test-case-writing-use-case.md](../references/agent/test-case-writing-use-case.md)
