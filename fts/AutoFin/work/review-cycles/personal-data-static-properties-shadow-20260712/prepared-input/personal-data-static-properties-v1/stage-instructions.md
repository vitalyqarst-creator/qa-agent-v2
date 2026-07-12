# Prepared Stage Instructions

- package_id: `personal-data-static-properties-v1`
- role: `writer`
- scenario: `writer.session_prepared_initial_draft`
- output_path: `fts/AutoFin/work/review-cycles/personal-data-static-properties-shadow-20260712/attempts/writer-r1/attempt-001/stage-output/draft.md`
- attempt_root: `fts/AutoFin/work/review-cycles/personal-data-static-properties-shadow-20260712/attempts/writer-r1/attempt-001`
- sandbox_policy: `read_only`
- hard_timeout_seconds: `180`
- idle_timeout_seconds: `60`
- command_budget: `0`

## Structured Fast Path

1. Use only the runner-embedded verified projection; do not reread workspace files.
2. Do not call shell or file tools; the command budget is zero.
3. Return the complete unsigned draft in the schema-constrained final contract.
4. The runner alone materializes output_path and applies deterministic gates.
5. Return blocked-input when inline evidence is insufficient; do not open full sources.

## Targeted Fallback

Structured fast mode has no source fallback; return blocked-input when inline evidence is insufficient.
