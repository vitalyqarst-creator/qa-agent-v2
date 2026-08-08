# Practical use case for FT test-case writing

This file describes the current default path for getting test cases quickly with
source-bound quality controls.

## Default path

```text
ft-source-locator
-> ft-scope-analyzer
-> ft-test-case-writer
-> separate-session ft-test-case-reviewer
-> one bounded revision when needed
-> final baseline
```

## What each stage must produce

1. `ft-source-locator`
   - Select the FT package and register DOCX, mandatory XHTML, PDF, support,
     mockups and package notes when present.

2. `ft-scope-analyzer`
   - Create a compact practical `scope-brief.md`.
   - Create `source-parity-check.md` before writer when DOCX and PDF are both
     present.
   - Create `source-row-inventory.md` when the scope is table/row/status/list
     driven.

3. `ft-test-case-writer`
   - Create Markdown `test-design-matrix.md`.
   - Create canonical test cases in `fts/<ft-slug>/test-cases/`.
   - Keep the suite review-ready, not released/signed-off.

4. `ft-test-case-reviewer`
   - Run in a separate top-level Codex session by default.
   - Re-derive coverage from FT/PDF/XHTML/support/mockups instead of trusting
     the writer matrix.
   - Produce `review-findings.md` and `review-independence.md` only for
     separate-session review. Advisory non-independent review uses
     `advisory-review-findings.md` and cannot authorize writer revision without
     explicit controller approval.

5. Revision
   - Perform one bounded writer revision for blocking findings.
   - If information remains unavailable, keep the affected TC with
     `candidate-ui-calibration`, `blocked-observability` or `needs-test-data`
     instead of starting an unbounded repair loop.

## Explicit-only routes

The following are not default for ordinary writing and must be used only by
explicit request: benchmark, sharding, semantic bridge, source assertion review,
immutable/source-qualified `ft-agent run`, session-based review-cycle and XLSX
traceability export.

Legacy session-based use case:
`references/agent/legacy/session-based-test-case-writing-use-case.md`.
