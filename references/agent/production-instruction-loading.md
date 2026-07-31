# Production Instruction Loading

This manifest defines the only instruction context for the downstream production bundle. The bundle receives an independently qualified, hash-bound scope package. Discovery, source qualification, benchmark, incremental update, UI automation, and historical session/cycle orchestration are intentionally absent.

Global profile rules live in [production-global-rules.md](production-global-rules.md). The development root `AGENTS.md` is not an instruction dependency of this bundle.

<!-- instruction-loading-manifest:v1 -->
```json
{
  "version": 1,
  "budget_unit": "KiB",
  "baseline": {
    "captured_at": "2026-07-23",
    "method": "explicit production allowlist"
  },
  "groups": {
    "production_global": {
      "rationale": "Global project rules required by the downstream production iteration.",
      "paths": [
        "references/agent/production-global-rules.md",
        "references/agent/runtime-environment-encoding-policy.md"
      ]
    },
    "production_iteration": {
      "rationale": "One public schema-v2 source-qualified iteration and its compact runtime quality contract; new production configs use model-runtime-prose writer mode.",
      "paths": [
        "skills/ft-test-case-iteration/SKILL.md",
        "references/agent/lean-v2-iteration.md",
        "references/agent/negative-ui-calibration-policy.md"
      ]
    }
  },
  "scenarios": [
    {
      "id": "iteration.source_qualified_model_runtime",
      "phase": "iteration",
      "mode": "source_qualified_model_runtime",
      "scope_profile": "source-qualified-schema-v2",
      "required_groups": ["production_global", "production_iteration"],
      "conditional_groups": [],
      "audit_only_groups": [],
      "budget_limit_kib": 60,
      "rationale": "Single public schema-v2 production iteration with required writer_mode=model-runtime-prose."
    }
  ]
}
```

Resolver runs inside the production bundle must always use this file explicitly:

```powershell
python scripts/resolve_instruction_context.py `
  --manifest references/agent/production-instruction-loading.md `
  --scenario iteration.source_qualified_model_runtime `
  --budget-report --fail-on-budget
```
