# FT Test Case Agent. Practical User Manual

This is the current user-facing entrypoint for ordinary FT test-case writing.

Default route:

```text
ft-source-locator
-> ft-scope-analyzer
-> ft-test-case-writer
-> separate-session ft-test-case-reviewer
-> one bounded revision when needed
-> final baseline
```

Use `references/agent/practical-test-case-route-v0.8.md` as the controlling
workflow. In the default route:

- `source-parity-check.md` is created before writer handoff when DOCX and PDF
  are both available;
- `test-design-matrix.md` is Markdown only by default;
- XLSX export is created only by explicit user request;
- reviewer runs in a separate Codex task/session for independent sign-off;
- benchmark, sharding, semantic bridge, `source_assertion_review`,
  source-qualified immutable `ft-agent run`, `work/iterations/` and
  session-based review-cycle are not default routes.

Legacy session-based manuals were moved to:

- `references/agent/legacy/session-based-user-manual.md`
- `references/agent/legacy/session-based-test-case-writing-use-case.md`

Those legacy files are retained for historical/development routes only. Do not
use them to choose the default route for ordinary test-case writing.
