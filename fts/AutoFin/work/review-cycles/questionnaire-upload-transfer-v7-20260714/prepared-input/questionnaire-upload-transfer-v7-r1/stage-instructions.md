# Prepared Stage Instructions

- package_id: `questionnaire-upload-transfer-v7-r1`
- role: `writer`
- scenario: `writer.session_initial_draft`
- output_path: `fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v7-20260714/attempts/writer-r1/attempt-001/stage-output/draft.md`
- attempt_root: `fts/AutoFin/work/review-cycles/questionnaire-upload-transfer-v7-20260714/attempts/writer-r1/attempt-001`
- sandbox_policy: `read_only`
- hard_timeout_seconds: `900`
- idle_timeout_seconds: `180`
- command_budget: `0`

## Structured Standard Path

1. Use only the runner-embedded verified projection; do not reread workspace files.
2. Do not call shell or file tools; the command budget is zero.
3. Return the complete unsigned draft in the schema-constrained final contract.
4. The runner alone materializes output_path and applies deterministic gates.
5. Return blocked-input only when inline evidence cannot define test intent or an observable oracle without invention; missing stand IDs, locators, tokens or prerecorded provider responses are UI-prep bindings, not FT-first blockers.

## Targeted Fallback

Structured mode has no source fallback. Portable synthetic values, relative dates and runtime-selected integration responses with source-defined observable properties are reproducible FT-first fixtures; block only when test intent or oracle still requires invention.
