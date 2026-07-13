# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `visual-assessment-medium-scope-benchmark` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/51-search-clear-context-exec-benchmark-v4/prompt.iteration-to-medium-scope.md` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | H20 source selection | Use only `FT4AutoFinFinal` DOCX/XHTML/PDF | Current source family is mandatory | `source-selection.md` | high | applied |
| `DEC-002` | 2 | `scope-boundary` | H21 expanded matrix | Select full visual-assessment criteria scope | 13 OBL, complete dictionary, zero active gaps; closest valid medium target | `scope-contract.md` | high | applied |
| `DEC-003` | 3 | `scope-boundary` | H47 blockers | Reject employment scope | Driver alias and dictionary divergence remain unresolved | session log | high | applied |
| `DEC-004` | 4 | `source-boundary` | `resolve_sections()` and FT4 parity | Replace legacy anchors with section-16/20, XHTML 182-184, PDF 34/40-41, BSR 311-317 | Direct current-source evidence | parity/inventory | high | applied |
| `DEC-005` | 5 | `test-design` | BSR 313 and 314 | Keep two obligations but map both to one visibility TC | One action produces one main observable result; avoids duplicate TC | benchmark projection | high | applied |
| `DEC-006` | 6 | `coverage` | BSR 316/317 lack exact UI mechanism | Route two requiredness checks as candidate UI calibration | Policy forbids invented messages/highlights/transitions | requiredness inventory | high | applied |
| `DEC-007` | 7 | `artifact-write` | 52-row inventory | Use manifest helper before target write | Mandatory table-heavy write strategy | source-row inventory | high | applied |
| `DEC-008` | 8 | `routing` | Scope gates prepared | Route to `ft-test-case-iteration` | Full loop is the benchmark under test | workflow/prompt | high | applied |
| `DEC-009` | 9 | `test-design` | Prepared compiler grouping gate | Use one shared plan row for `ATOM-003; ATOM-004` and retain separate obligations | Compiler proves the only merged case has one action and one expected result | compiler projection | high | applied |
| `DEC-010` | 10 | `execution` | Validate-only and regression evidence | Permit checkpoint preparation but keep live blocked | Runtime identity/capacity/oracles pass; live still needs pushed checkpoint and separate authorization | `pre-live-test-report.md`; `pre-live-stop-gate.md` | high | applied |
| `DEC-011` | 11 | `risk` | Full validator suite | Treat two absent `ui-evidence-policy` fixture tests as recorded infrastructure debt, not a benchmark blocker | 389 tests passed; failures reproduce a missing untracked fixture directory and do not exercise changed code or selected scope | `pre-live-test-report.md` | medium | applied |
| `DEC-012` | 12 | `execution` | Pushed checkpoint `ab67a274...` matches origin | Authorize exactly one hash-bound exec dispatcher invocation | User authorized the complete plan; separate authorization preserves stop/replay safety | `pre-live-authorization.md` | high | applied |
