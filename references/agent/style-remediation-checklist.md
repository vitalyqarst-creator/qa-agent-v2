# Style Remediation Checklist

Compact style remediation only. Long examples are optional deep context, not default runtime.

| style finding class | compact action | validator/rule signal |
|---|---|---|
| Markdown or TC schema | Keep canonical headings, numbered steps and runtime TC fields from `test-case-format.md`. | `test-case-format` |
| Process marker in title | Remove candidate/calibration/process status from title; keep status in TC metadata/body. | `test-case-title-process-marker-smell` |
| Inline preconditions | Replace setup profile, stand, package or environment references with executable preconditions inside the TC. | `production-setup-profile-reference` |
| Concrete data | Replace generic data placeholders with literal values, named fixtures or explicit formulas. | `test-case-generic-test-data-reference-smell`, `test-case-generic-test-data-oracle-smell` |
| Meaning preservation | Do not change source scope, oracle, TC type or traceability while fixing wording/format. | reviewer sign-off / scoped validator |

Load `references/qa/test-case-style-examples.md` only in an explicit style example/debug scenario.
