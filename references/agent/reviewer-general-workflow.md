# Reviewer General Workflow

Этот reference применяется только для direct `full` / `traceability` /
`structure` / `test-design` review и explicit session-based promotion routes.
Practical route v0.8 использует свой компактный контракт в reviewer skill и
`practical-test-case-route-v0.8.md`.

## Режимы и границы

- `scope_gap_review` проверяет только coverage gaps, questions, source anchors
  и routing до writer; TC не читает и не подписывает.
- `source_assertion_review` работает по
  `reviewer-specialized-review-contracts.md`; это explicit production route.
- `structure_preflight`, `semantic_traceability_test_design`,
  `structure_format_final` и `semantic_regression` используются только в
  явном qualification/development route, а не в practical v0.8.

## Входы и выходы

Read the confirmed FT package, selected scope, canonical TC file, XHTML source,
available PDF parity, `source-parity-check.md`, and only the support,
dictionary and mockup artifacts relevant to the review mode. For a later round,
also read structured findings, writer response and the prior traceability matrix.

Emit findings ordered `error -> warning -> info`, a structured findings artifact
and a Russian human summary. `traceability` / `full` may emit a traceability
matrix. XLSX is only for an explicit promotion route or user request, never the
ordinary practical default. Artifact structure follows
`reviewer-output-format.md` and `review-findings-format.md`.

## Direct review procedure

1. Confirm the selected scope and source package. Missing mandatory XHTML or
   required DOCX/PDF parity evidence blocks sign-off.
2. Re-derive current-source obligations; do not accept writer ledger/matrix as
   the source of truth. Preserve `gap` / `unclear` when behavior is not safely
   derivable.
3. Review mockup inventory only as navigation/visible-label evidence and
   dictionary inventory as the complete value source; neither creates a new
   business rule.
4. In `structure` / `full`, verify parser-compatible format, numbering,
   grouping and that the tested action is not hidden in setup.
5. In `test-design` / `full`, apply `test-design-review-rubric.md`,
   `coverage-checklist.md`, `test-case-runtime-format.md` and
   `runtime-quality-rule-cards.md`. Re-derive applicability before accepting
   matrix coverage; source links alone do not prove the steps exercise a rule.
6. Every finding names its review mode, required change, concrete TC or source
   anchor, and applicable coverage dimension. Do not invent unconfirmed UI
   mechanisms.
7. Write the reviewer log and decision log. The reviewer never rewrites the
   canonical TC file. In a controller-owned practical task it also never edits
   workflow state or stage summary.

## Canonical references

- `references/qa/test-design-review-rubric.md`
- `references/qa/test-case-runtime-format.md`
- `references/qa/coverage-runtime-checklist.md`
- `references/qa/review-findings-format.md`
- `references/agent/reviewer-output-format.md`
- `references/agent/reviewer-specialized-review-contracts.md`
