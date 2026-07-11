# AutoFin Compiler Matrix V3 Report

## Source Boundary

- FT package: `fts/AutoFin`.
- Main source family: `FT4AutoFinFinal.docx/xhtml/pdf`.
- `AutoFinPreFinal.*` and neighboring FT packages were not used as requirement evidence.
- Live writer/reviewer and production promotion were not started.

## Print-form Semantic Closure

The four previously orphaned records are preserved as non-blocking constraints on testable atoms:

| gap | linked atom | classification |
| --- | --- | --- |
| `GAP-001` | `ATOM-002` | source-parity constraint for the template cell |
| `GAP-002` | `ATOM-004` | extraction constraint; exact tag spelling comes from DOCX |
| `GAP-003` | `ATOM-001` | generation entrypoint is not specified and is outside the executable assertion |
| `GAP-005` | `ATOM-005` | fixture preparation is outside section `4.4` |

`GAP-004` and `GAP-006` remain executable coverage gaps. They are still linked to gap/unclear atoms and were not converted into testable behavior.

## Reproducible Compiler Result

| scope | result | obligations | gaps | route |
| --- | --- | ---: | ---: | --- |
| widget selection | `built` | 6 | 2 | `simple-field-property` |
| search clear context | `built` | 4 | 0 | `standard-required` |
| print form generation | `built` | 18 | 6 | `standard-required` |

The prepared package contract now supports `constraint_gap_ids` on testable obligations. Constraint gaps remain visible in the package without falsely changing the obligation itself to `gap`.
