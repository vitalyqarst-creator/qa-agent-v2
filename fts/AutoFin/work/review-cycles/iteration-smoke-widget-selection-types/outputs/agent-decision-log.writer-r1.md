# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `iteration-smoke-widget-selection-types` |
| stage | `ft-test-case-writer` |
| session_stage | `writer-r1` |
| started_from | `work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Limit writer output to `SRC-001`, `SRC-002`, `SRC-003`. | Scope explicitly excludes other section 3 rows, screen-specific field rules, save-flow, persistence, API and old generated artifacts. | canonical TC file; split design artifacts | high | applied |
| `DEC-002` | 2 | `source-boundary` | `source-selection.md`; `source-row-inventory.md`; `source-parity-check.md` | Use XHTML row extraction and handoff DOCX/PDF parity as source evidence. | XHTML is mandatory machine-readable source; parity artifact says no discrepancy for selected rows. | `source-excerpt.writer-r1.md`; `source-row-inventory.md` | medium | applied |
| `DEC-003` | 3 | `test-design` | `RISK-001`; selected source rows define generic widgets | Write candidate UI-calibration TCs with fixture parameters instead of inventing concrete fields or dictionary values. | Requirements are generic widget constraints; concrete screen field and dictionary contents are not source-defined. | `fixture-catalog.md`; canonical TCs | high | applied |
| `DEC-004` | 4 | `coverage` | `SRC-003` | Split visible empty default state from internal `NULL` interpretation. | UI-only scope can observe absence of visible value but cannot prove internal null semantics. | `ATOM-005`; `ATOM-006`; `GAP-001`; `TC-WIDGET-SELECTION-TYPES-003` | high | applied |
| `DEC-005` | 5 | `artifact-write` | session-based writer stage | Replace current scope artifacts in place and do not use previous generated content as template. | Prompt requires fresh iteration smoke and excludes old generated/canary artifacts as source or template. | canonical TC file; split design artifacts; writer outputs | high | applied |
| `DEC-006` | 6 | `fallback` | stage-local extraction helper path bug | Fix helper root path and rerun source excerpt generation. | First run resolved `fts/fts/AutoFin`; no source decision used that failed output. | `extract-section3-source.py`; `source-excerpt.writer-r1.md` | low | applied |
| `DEC-007` | 7 | `fallback` | stage-local DOCX helper extracted no selected rows | Treat helper DOCX gap as diagnostic limitation and rely on required handoff parity evidence for DOCX confirmation. | `source-row-inventory.md` and `source-parity-check.md` already record DOCX confirmation; helper was only supplemental. | session log; source row inventory writer notes | medium | applied |
| `DEC-008` | 8 | `routing` | writer artifacts and scoped validator gate | Route to `structure-preflight-r1` with `stage_status: writer-draft-ready` if scoped validator profile remains clean. | Session-based matrix allows `writer.session_initial_draft` -> `writer-draft-ready`; writer must not start reviewer directly. | `cycle-state.yaml`; `prompt.structure-preflight-r1.md` | high | applied |
