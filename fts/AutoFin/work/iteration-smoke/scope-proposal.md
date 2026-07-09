# Scope Proposal

## Context

- Branch: `audit/stabilize-testcase-agent-iteration-process-smoke`
- Base branch: `audit/stabilize-testcase-agent-persistence-calibration-handoff`
- Base HEAD: `bb8b71117652b70fc9863dad9c81baf9040397e0`
- Base tracking branch: `origin/audit/stabilize-testcase-agent-persistence-calibration-handoff`
- Initial working tree: unrelated untracked `evals/sdk-turn-diagnostics/*` directories and `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`; not used and not staged.
- Agent-layer changed before primary generation: `no`

## Selected Scope

- FT package: `fts/AutoFin`
- Main FT: `fts/AutoFin/source/FT4AutoFinFinal.docx`
- Mandatory XHTML source: `fts/AutoFin/source/FT4AutoFinFinal.xhtml`
- PDF cross-check: `fts/AutoFin/source/FT4AutoFinFinal.pdf`
- Section: `3 Ограничения`
- Scope slug: `iteration-smoke-widget-selection-types`
- Working title: UI widget value selection constraints for list and multi-select types

## Selected Source Rows

| source_row_id | source | anchor | statement |
| --- | --- | --- | --- |
| `SRC-001` | `FT4AutoFinFinal.xhtml`; DOCX section `3` | table `Ограничения по типам данных`, row `Список` | Values are taken from a dictionary; only one value can be selected. |
| `SRC-002` | `FT4AutoFinFinal.xhtml`; DOCX section `3` | table `Ограничения по типам данных`, row `Список с множественным выбором` | Values are taken from a dictionary; several values can be selected. |
| `SRC-003` | `FT4AutoFinFinal.xhtml`; DOCX section `3` | paragraph after data type table | Default widget values are absent and interpreted as `NULL`. |

BSR/source code count: `0`; these global section rows do not include BSR identifiers.

## Selection Rationale

- The scope is small enough for an end-to-end iteration smoke: three source-backed atomic statements and expected output of about three test cases.
- The scope is not a persistence/save-flow scope.
- The scope does not repeat the v4 field-level canary or persistence smoke artifacts, which are centered on application-card address/contact and save-flow behavior.
- The scope is not based on existing generated test cases; existing test-case names were used only as contamination control to avoid old canary/persistence areas.
- The scope uses XHTML for row extraction, DOCX as source of truth for meaning, and PDF only as structural cross-check.

## Expected Result Size

- Expected TC count: `3`
- Expected source rows: `3`
- Expected BSR count: `0`
- Expected iteration loops: `0-2`, depending on runner reviewer findings.

## Risks And Uncertainties

- Section `3` is a global constraint section rather than a single concrete screen; writer must keep cases executable without inventing fields or dictionaries not present in the selected source.
- PDF text extraction confirms the block location on page 5 but is not clean enough to be the row-level source.
- No BA clarification is required before starting the process; unresolved fixture needs, if any, must be kept as gaps by writer/reviewer rather than invented.

## Canonical Handoff

- Scope handoff: `fts/AutoFin/work/stage-handoffs/18-iteration-smoke-widget-selection-types/`
- Review cycle state: `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`
- Intended canonical TC artifact: `fts/AutoFin/test-cases/3-iteration-smoke-widget-selection-types.md`
