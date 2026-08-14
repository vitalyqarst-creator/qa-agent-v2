# FT Test Case Agent. Practical User Manual

This is the current user-facing entrypoint for ordinary FT test-case writing.

Default route:

```text
ft-practical-route
-> source obligations
-> test-design matrix
-> separate-session matrix review
-> canonical test cases
-> separate-session final TC review
-> accepted baseline or honest blocker
```

Use `references/agent/practical-test-case-route-v0.9.md` as the controlling
workflow. In the default route:

- `source-parity-check.md` is created before writer handoff when DOCX and PDF
  are both available;
- `test-design-matrix.md` is Markdown only by default;
- XLSX export is created only by explicit user request;
- matrix and final TC reviewers run in separate top-level Codex sessions;
- benchmark, sharding, semantic bridge, `source_assertion_review`,
  source-qualified immutable `ft-agent run`, `work/iterations/` and legacy
  session-based review-cycle are unavailable from the active skill layer.

Historical session-based manuals are retained outside the active skill layer:

- `references/agent/legacy/session-based-user-manual.md`
- `references/agent/legacy/session-based-test-case-writing-use-case.md`

Those legacy files are retained for historical/development routes only. Do not
use them to choose the default route for ordinary test-case writing.
