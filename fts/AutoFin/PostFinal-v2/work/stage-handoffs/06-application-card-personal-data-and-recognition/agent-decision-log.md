# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin/PostFinal-v2` |
| scope_slug | `application-card-personal-data-and-recognition` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/04-postfinal-v2-source-selection/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | `1` | `scope-boundary` | `User selected `SCOPE-OPTION-002`` | `Confirmed `application-card-personal-data-and-recognition` in handoff dir `06-*`.` | `Scope option already bounded to Table 4 rows 2-15 and BSR 43-83.` | `scope-contract.md` | `high` | `applied` |
| `DEC-002` | `2` | `source-boundary` | ``source-selection.md`; XHTML availability` | `Proceed with XHTML extraction because `xhtml_available=yes`.` | `XHTML is mandatory extraction source.` | `source-row-inventory.md` | `high` | `applied` |
| `DEC-003` | `3` | `source-boundary` | `Prepared context has 41 rows` | `Use standard/legacy scope handoff, not lean-production.` | `Lean limit is 12 rows; integrations are heterogeneous.` | `workflow-state.yaml` | `high` | `applied` |
| `DEC-004` | `4` | `source-boundary` | `Prepared context lacks approved-clarification binding` | `Do not create compiler-v3 `source-assertions.json` in this handoff.` | `A production manifest must hash-bind approved clarification evidence.` | `workflow-state.yaml` | `risk:production-rematerialization-required` | `applied` |
| `DEC-005` | `5` | `coverage` | `BSR 83 recognition branch` | `Classify recognition observation and field mapping as blocking gaps.` | `Source lacks observation interface and field mapping.` | `scope-coverage-gaps.md` | `high` | `applied` |
| `DEC-006` | `6` | `coverage` | `BSR 79/82/83 file attachment` | `Classify file type/count/size/valid fixture as blocking for positive recognition branch.` | `No stable positive recognition fixture can be derived.` | `scope-coverage-gaps.md` | `medium` | `applied` |
| `DEC-007` | `7` | `coverage` | ``CLR-006` and negative-ui policy` | `Preserve validation/requiredness obligations as `candidate_tc_required`.` | `Source defines restrictions but exact UI reaction is for UI calibration.` | `negative-oracle-inventory.md; requiredness-oracle-inventory.md` | `high` | `applied` |
| `DEC-008` | `8` | `source-boundary` | `Dictionary references `Пол клиента`, `типы документов`` | `Extract only referenced dictionaries into dictionary inventory.` | `Do not use incomplete examples.` | `dictionary-inventory.md` | `high` | `applied` |
| `DEC-009` | `9` | `mockup` | `Figures 2, 4, 5 opened visually` | `Use mockups only for UI placement/interaction hints; FT/support wins on defaults.` | `Mockups show selected values that conflict with `CLR-008`.` | `mockup-visual-inventory.md` | `high` | `applied` |
| `DEC-010` | `10` | `routing` | `Coverage gaps exist` | `Route active next step to `ft-test-case-reviewer` mode `scope_gap_review`.` | `Skill requires `prompt.scope-gaps-to-reviewer.md` before writer.` | `workflow-state.yaml; prompt.scope-gaps-to-reviewer.md` | `high` | `applied` |
| `DEC-011` | `11` | `fallback` | `Python stdout cp1251 UnicodeEncodeError` | `Discard partial cp1251 output and rerun with `PYTHONIOENCODING=utf-8`.` | `UTF-8 file-based output preserves source text.` | `scope-analyzer-session-log.md` | `medium` | `applied` |
| `DEC-012` | `12` | `fallback` | `Initial PDF BSR search timed out` | `Rerun PDF search in one page pass.` | `Timeout was technical, not source ambiguity.` | `source-parity-check.md` | `medium` | `applied` |
| `DEC-013` | `13` | `artifact-format` | `User requested human-friendly gap answers` | `Render clarification requests as vertical CLR cards instead of a wide Markdown table.` | `Cards keep the same structured fields while making the answer area editable by a human.` | `scope-clarification-requests.md` | `high` | `applied` |
| `DEC-014` | `14` | `artifact-format` | `User rejected internal jargon and metadata editing for BA` | `Use plain Russian questions and make `response_status`/`response_type`/`updated_at` agent-managed fields.` | `BA should answer business questions, not maintain workflow metadata.` | `scope-clarification-requests.md; scope-coverage-gaps.md` | `high` | `applied` |
| `DEC-015` | `15` | `artifact-format` | `User requested FT text next to each gap question` | `Add `source_quote` and visible `Текст из ФТ` block to clarification cards.` | `BA should not have to search source documents to understand why a question exists.` | `scope-clarification-requests.md` | `high` | `applied` |
