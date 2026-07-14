# Independent Scope-Gap Review Execution V8

Act as an independent `ft-test-case-reviewer` in mode `scope_gap_review`.

Read repository `AGENTS.md`, `skills/ft-test-case-reviewer/SKILL.md`, instruction scenario `reviewer.scope_gap_review`, package `fts/AutoFin/AGENT-NOTES.md`, and the active prompt:

`fts/AutoFin/work/stage-handoffs/57-questionnaire-upload-transfer-v8-prod-candidate/prompt.scope-gaps-to-reviewer.md`

Read every input listed by the active prompt. This is a read-only review. Do not edit repository files, review test cases, invoke another agent, compile a package, or run writer/reviewer cycle stages.

Judge the corrected V8 artifacts independently. An open non-blocking gap may proceed only if it remains explicit downstream and exact-byte boundary tests remain forbidden.

Return only JSON matching the provided schema. Put the complete Russian-language review body in `report_markdown` and a concise Russian session summary in `session_summary_markdown`.
