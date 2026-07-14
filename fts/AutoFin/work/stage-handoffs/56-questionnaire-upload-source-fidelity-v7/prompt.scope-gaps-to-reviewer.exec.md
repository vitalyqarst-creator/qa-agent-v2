# Independent Scope-Gap Review Execution

Act as an independent `ft-test-case-reviewer` in mode `scope_gap_review`.

Read and follow:

- repository `AGENTS.md`;
- `skills/ft-test-case-reviewer/SKILL.md`;
- instruction scenario `reviewer.scope_gap_review` from `references/agent/instruction-loading-manifest.md`;
- package `fts/AutoFin/AGENT-NOTES.md`;
- the active prompt `fts/AutoFin/work/stage-handoffs/56-questionnaire-upload-source-fidelity-v7/prompt.scope-gaps-to-reviewer.md`;
- every input listed by that active prompt.

This is an independent read-only review. Do not edit any repository file. Do not write or review test cases. Do not invoke another agent. Do not close `GAP-QUT-001` without source-backed evidence.

Pay special attention to the apparent routing tension between the canonical reviewer skill and the active prompt. Report whether a passed review may preserve the non-blocking open gap and route a new immutable revision to writer, or whether source revision/input is required first.

Return only JSON matching the provided output schema. Put a complete Russian-language `scope-gap-review.md` body in `report_markdown` and a concise Russian-language reviewer session summary in `session_summary_markdown`.
