# AutoFin prepared compiler matrix report

## Boundary

- FT package: `fts/AutoFin` only.
- Source family: `FT4AutoFinFinal.docx/xhtml/pdf` only.
- Production promotion: disabled.
- Neighboring FT packages and `AutoFinPreFinal.*`: not used as requirement evidence.

## Compiler results

| matrix item | result | obligations | gaps | route | unsupported dimensions |
| --- | --- | ---: | ---: | --- | --- |
| widget selection | `built` | 6 | 2 | `simple-field-property` | none |
| search clear context | `built` | 4 | 0 | `standard-required` | `limited-default-oracle`; `state-transition-or-navigation` |
| print form generation | `blocked-semantic-fidelity` | not emitted | not emitted | expected standard | `GAP-001`, `GAP-002`, `GAP-003`, `GAP-005` are absent from atomic ledger |
| visual assessment | `rejected-before-compile` | n/a | n/a | expected standard | repeated `DICT-001` rows require semantic dictionary migration |

The reproducibility rerun used immutable `compiler-v2-20260711` cycle directories. Widget selection and search-clear reproduced the same counts and routes; print-form reproduced the same semantic-fidelity block before package emission.

## Real blocker

`section-16-print-form-generation/coverage-gaps.md` declares six gaps. The atomic ledger links only `GAP-004` and `GAP-006`. Silently compiling only linked gaps would lose four recorded source limitations:

- XHTML/PDF template discrepancy handling;
- tag spelling/parity handling;
- missing generation entrypoint;
- fixture preparation outside the selected section.

Some may be resolved limitations rather than open executable gaps, but that classification is not encoded consistently. It requires semantic review of ledger, gap status and package plan; the compiler must not guess.

## Completed remediation before stop

- Compiler requires explicit expected FT slug and package-local workflow/output/attempt paths.
- Source registry is pinned to the workflow-linked source selection.
- DOCX/XHTML/PDF stems and XHTML confirmation are checked.
- Applicable complex dimensions route to `standard-required` rather than the optimized fast path.
- Canonical `atomic_statement`, table-shaped gaps and titled gap headings are supported.
- Widget selection design separates executable cardinality from unproven dictionary provenance.

## Stop decision

Cross-scope live validation and promotion dry-run were not started. Phase-4 stop-condition was triggered by semantic fidelity loss risk before any LLM session or production mutation.

Validation after the stop:

- compiler and runner unit suites: 59 tests passed;
- agent architecture audit: 59 checks, 0 findings;
- matrix handoff artifact validation: 0 errors, 0 warnings (three informational source-extraction quality notes remain visible).

## Required next remediation

1. Review print-form `GAP-001/002/003/005` and classify each as resolved limitation, linked atomic gap or out-of-scope setup constraint.
2. Update atomic ledger and package plan so every remaining gap is linked exactly once or explicitly closed with evidence.
3. Recompile all three matrix items into new immutable cycle directories.
4. Only after 3/3 compiler preflight succeeds, run the widget-selection promotion-off canary.

Visual-assessment dictionary hierarchy should be handled as a separate migration; it is not required to unblock the current matrix because search-clear replaced that candidate.
