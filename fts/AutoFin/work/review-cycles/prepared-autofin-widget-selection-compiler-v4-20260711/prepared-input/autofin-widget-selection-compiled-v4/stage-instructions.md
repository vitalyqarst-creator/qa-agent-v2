# Prepared Stage Instructions

- package_id: `autofin-widget-selection-compiled-v4`
- role: `writer`
- scenario: `writer.session_prepared_initial_draft`
- output_path: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-compiler-v4-20260711/attempts/writer-r1/attempt-001/stage-output/draft.md`
- attempt_root: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-compiler-v4-20260711/attempts/writer-r1/attempt-001`
- sandbox_policy: `workspace_write`
- hard_timeout_seconds: `180`
- idle_timeout_seconds: `60`
- command_budget: `12`

## Fast Path

1. Use the runner-embedded verified projection; do not reread package files in the stage.
2. Do not rerun source locator, scope analyzer, source parity, DOCX extraction or PDF rendering.
3. Write a structurally complete minimum output before optional refinement.
4. Keep output and scratch inside attempt_root.
5. Do not read generated test cases, earlier cycles or canary artifacts as evidence.

## Targeted Fallback

Use a registered full source only when one named ATOM/source locator is unresolved by the package.
Record targeted_source_fallback with the reason, source path and exact locator.
Do not scan a complete document or use external scratch paths. Return blocked if evidence stays insufficient.
