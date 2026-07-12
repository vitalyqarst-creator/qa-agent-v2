# Prepared Stage Instructions

- package_id: `personal-data-character-restrictions-v1`
- role: `writer`
- scenario: `writer.session_initial_draft`
- output_path: `fts/AutoFin/work/review-cycles/personal-data-character-restrictions-shadow-v1-20260712/attempts/writer-r1/attempt-001/stage-output/draft.md`
- attempt_root: `fts/AutoFin/work/review-cycles/personal-data-character-restrictions-shadow-v1-20260712/attempts/writer-r1/attempt-001`
- sandbox_policy: `workspace_write`
- hard_timeout_seconds: `900`
- idle_timeout_seconds: `180`
- command_budget: `80`

## Prepared Standard Context

1. Load the full standard writer instruction scenario selected by the runner.
2. Use the runner-embedded verified projection as the primary scope evidence.
3. Do not rerun source locator, scope analyzer or broad full-document discovery.
4. Keep output and scratch inside attempt_root.
5. Do not read generated test cases, earlier cycles or canary artifacts as evidence.

## Targeted Fallback

Use a registered full source only when one named ATOM/source locator is unresolved by the package.
Record targeted_source_fallback with the reason, source path and exact locator.
Do not scan a complete document or use external scratch paths. Return blocked if evidence stays insufficient.
