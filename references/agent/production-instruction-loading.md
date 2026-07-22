# Production Instruction Loading

Этот manifest задаёт единственный instruction context downstream production
bundle. Bundle принимает уже независимо квалифицированный и hash-bound пакет
scope; discovery и source qualification, benchmark, incremental, UI automation
и историческая session/cycle orchestration намеренно отсутствуют.

Глобальные правила профиля находятся в
[production-global-rules.md](production-global-rules.md); development-only
корневой `AGENTS.md` не является instruction dependency этого bundle.

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
      "rationale": "One public schema-v2 deterministic-first iteration and its compact runtime quality contract.",
      "paths": [
        "skills/ft-test-case-iteration/SKILL.md",
        "references/agent/lean-v2-iteration.md",
        "references/agent/negative-ui-calibration-policy.md"
      ]
    }
  },
  "scenarios": [
    {
      "id": "iteration.deterministic_production",
      "phase": "iteration",
      "mode": "deterministic_production",
      "scope_profile": "source-qualified-schema-v2",
      "required_groups": ["production_global", "production_iteration"],
      "conditional_groups": [],
      "audit_only_groups": [],
      "budget_limit_kib": 60,
      "rationale": "Single public schema-v2 production iteration."
    }
  ]
}
```

Запуск resolver внутри production bundle всегда использует этот файл явно:

```powershell
python scripts/resolve_instruction_context.py `
  --manifest references/agent/production-instruction-loading.md `
  --scenario iteration.deterministic_production `
  --budget-report --fail-on-budget
```
