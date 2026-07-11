# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| stage | `ft-scope-analyzer` |
| started_from | `work/stage-handoffs/26-prepared-standard-calculator-summary/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `source-boundary` | handoff 20 and handoff 26 | Use only `FT4AutoFinFinal` DOCX/XHTML/PDF as active evidence | Final family is selected and XHTML is mandatory; PreFinal mappings caused verified drift | handoff 27 | `high` | `applied` |
| `DEC-002` | 2 | `history-preservation` | signed-off handoff 05 and old review cycles | Create handoff 27 instead of rewriting historical snapshots | Historical signed-off evidence must remain auditable even when superseded | handoff 27 | `high` | `applied` |
| `DEC-003` | 3 | `inventory` | legacy BSR generator scans all artifacts | Correct the generator and regenerate against Final rather than manually swapping rows | Historical mentions are not proof of active source mapping | package BSR inventory and generator | `high` | `applied` |
| `DEC-004` | 4 | `scope-boundary` | Final rows for BSR 35–38 | Route them to `section-4.2-applications-menu-search`, not calculator-summary or generic card actions | Final XHTML/PDF and active source-row inventory identify Continue/Create application-list actions | scope contract and BSR inventory | `high` | `applied` |
| `DEC-005` | 5 | `inventory-risk` | BSR 43–46 also occur in active personal-data inventory | Flag multiple active mappings instead of rewriting personal-data artifacts in this scope | Cross-scope source rebase exceeds calculator iteration and must remain visible | package BSR inventory | `high` | `applied` |
| `DEC-006` | 6 | `review-validity` | first compatible scope-gap review read canonical test cases and design artifacts | Treat its blocked verdict as invalid for scope acceptance and retain it only as failed orchestration evidence | Scope-gap mode explicitly forbids test-case review; supplied inputs contradicted the stage contract | failed gap-review cycle and runner fix | `high` | `applied` |
| `DEC-007` | 7 | `routing` | blocked scope review generated a writer prompt | Route blocked scope review back to scope analyzer and never to writer | A failed pre-writer gate cannot authorize writer start | generic runner transition prompt | `high` | `applied` |
| `DEC-008` | 8 | `quality-gate` | immutable gap-review v2 | Accept the Final scope/gap handoff and route to prepared iteration | Reviewer checked only explicit scope inputs, found no issues and preserved GAP-001 limits | `scope-gap-review.md`; workflow state | `high` | `applied` |
| `DEC-009` | 9 | `live-output-contract` | v8 reviewer put `GAP-001` into `test_case_ids` | Keep v8 terminal and invalid, then constrain non-testable obligation arrays to zero items | Semantic validator was correct; output schema was weaker than its downstream invariant | runner fix `1ff44d4`; v8 evidence | `high` | `applied` |
| `DEC-010` | 10 | `correction-cap` | plan allows one source-backed correction | Use exactly one fresh immutable v9 cycle after the contract fix | The draft/source obligations did not require rewriting; replaying v8 would violate terminal immutability | v9 prepared package and cycle | `high` | `applied` |
| `DEC-011` | 11 | `promotion` | v9 reviewer accepted with zero findings | Retain candidate as accepted-not-promoted and keep production unchanged | This iteration is a diagnostic readiness gate; explicit human-reviewed promotion belongs to the first battle rehearsal | iteration summary and next prompt | `high` | `applied` |
