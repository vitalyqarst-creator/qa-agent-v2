# AutoFin Prepared Compiler Scope Matrix

| matrix_id | scope | source family | intended class | canonical design input | expected route | live policy |
| --- | --- | --- | --- | --- | --- | --- |
| `MATRIX-001` | `iteration-smoke-widget-selection-types` | `FT4AutoFinFinal` | simple selection cardinality with preserved gaps | `work/test-design/3-iteration-smoke-widget-selection-types/` | `simple-field-property` | promotion-off canary allowed after compile gates |
| `MATRIX-002` | `iteration-smoke-search-clear-context` | `FT4AutoFinFinal` | reset of filters, sorting, pagination and row selection | `work/test-design/4.2-iteration-smoke-rerun-search-clear-context/` | `standard-required:state transition / limited default oracle` | no prepared fast-path live run |
| `MATRIX-003` | `print-form-generation` | `FT4AutoFinFinal` | document mapping, dictionaries and dependencies | `work/test-design/section-16-print-form-generation/` | `standard-required:dependency-state` | no prepared fast-path live run |

Numeric was not forced into the matrix: an applicable numeric/boundary scope is outside the current `simple-field-property` fast-path contract. The compiler must route such a package to `standard-required`, not weaken eligibility or switch FT packages.

`visual-assessment-criteria` was rejected from this matrix because its legacy dictionary inventory repeats `DICT-001` for multiple category rows. Repair requires a separate semantic migration of the dictionary hierarchy and is not safe as a mechanical benchmark preparation step.

## Preflight Result

- `MATRIX-001`: built, fast-path eligible.
- `MATRIX-002`: built, correctly routed to standard writer.
- `MATRIX-003`: blocked because four coverage gaps are not represented in the atomic ledger.
- Matrix status: `blocked-semantic-fidelity`; live validation is prohibited until remediation.
