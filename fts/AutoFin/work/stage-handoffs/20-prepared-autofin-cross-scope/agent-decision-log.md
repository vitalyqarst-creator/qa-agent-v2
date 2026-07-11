# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-autofin-cross-scope` |
| stage | `ft-source-locator / architecture preflight` |
| started_from | `workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | user correction | Allow only `fts/AutoFin / FT4AutoFinFinal` | Previous automation expanded to another FT package without authority | `source-selection.md` | high | applied |
| `DEC-002` | 2 | `test-design` | prepared fast-path contract | Route numeric/dependency/integration dimensions to standard writer | Marking them simple would create semantic degradation | compiler applicability gate | high | applied |
| `DEC-003` | 3 | `coverage` | widget selection ledger vs accepted prepared evidence | Separate cardinality checks from unproven dictionary provenance | Two fixture values do not prove source dictionary composition | widget ledger/plan/gaps | high | applied |
| `DEC-004` | 4 | `routing` | FT4 applicability matrices | Use one fast-path control and two standard-required compiler cases | Current prototype intentionally supports only simple field properties | `scope-matrix.md` | high | applied |
| `DEC-005` | 5 | `test-design` | repeated `DICT-001` rows in visual assessment inventory | Reject visual assessment from this benchmark and use FT4 search-clear state scope | Dictionary ID migration would change semantic identity and requires its own review | `scope-matrix.md` | risk:legacy dictionary hierarchy | applied |
| `DEC-006` | 6 | `routing` | print-form orphan gaps | Stop before live validation | Compiler cannot discard four canonical gaps or infer whether they are resolved | `autofin-compiler-matrix-report.md` | risk:semantic fidelity loss | blocked |
