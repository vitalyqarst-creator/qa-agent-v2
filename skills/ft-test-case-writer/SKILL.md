---
name: ft-test-case-writer
description: Writes new manual test cases for an already selected and bounded requirement fragment, or revises an existing suite by structured findings. In revision mode it must account for the reviewer's `review_mode` and use the traceability matrix when available.
---

# FT Test Case Writer

Use this skill only when these are already defined:

- target FT package;
- scope boundaries;
- main FT source and related materials;
- work mode: `practical_v0_8_matrix`, `practical_v0_8_tc_after_matrix_accepted`,
  `initial_draft`, `revision_from_findings`, or remediation.

If the package, source, or scope is not selected yet, use `ft-source-locator` and `ft-scope-analyzer` first.

## Default practical mode

For ordinary user work “write test cases for this FT/scope”, use
`practical_v0_8` from
[../../references/agent/practical-test-case-route-v0.8.md](../../references/agent/practical-test-case-route-v0.8.md).

In this mode the writer optimizes for a useful released baseline, not for
benchmark-grade process evidence. It is split into two writer passes:

- first write only `test-design-matrix.md` and route it to independent matrix
  review;
- write the canonical test-case file only after `test-design-matrix-review.md`
  has verdict `matrix-accepted`, or after one bounded matrix repair from
  `matrix-changes-required` is recorded in `matrix-repair-summary.md`;
- create `dictionary-inventory.md`, `fixture-catalog.md` or BA-question files
  only when the current scope needs them;
- require `source-parity-check.md` before writing when the main FT has both
  DOCX and PDF; require `source-row-inventory.md` when the scope is driven by FT
  table/action/field/status rows;
- keep the canonical file in a writer/review-ready state until the independent
  TC review gate completes; the writer must not mark the suite `released-*`,
  `signed-off` or equivalent before review;
- after the independent TC review, perform at most one bounded TC revision and
  publish the baseline with explicit residual statuses; do not request a second
  reviewer pass by default;
- do not create XLSX duplicates for practical matrices unless the user
  explicitly requests XLSX export;
- do not create source assertions, source assertion review prompts, semantic
  bridge projections, immutable attempts, sharding artifacts, benchmark configs,
  large obligation ledgers, final-format-review packages or session-cycle
  snapshots;
- do not stop the whole scope merely because some executable detail is unknown;
  release those cases with `candidate-ui-calibration`, `blocked-observability`
  or `needs-test-data` when the FT obligation itself is clear.

Use session-based, prepared-package, source-qualified or immutable runner routes
only when explicitly requested by the user or by an already selected route.

## Входы

- FT package path `fts/<ft-slug>/...`;
- main FT document;
- `source-selection.md` with `xhtml_available: yes` and main FT XHTML;
- PDF version of the main FT for structural cross-check, when present;
- `source-parity-check.md`, when the main FT is available as DOCX and PDF;
- `source-row-inventory.md`, when the handoff requires row-level/table parity;
- `dictionary-inventory.md`, when source/support already references a dictionary or fixed value list;
- `mockup-visual-inventory.md`, when the confirmed UI scope contains a mockup / screen image / `mockups/`;
- selected section, subsection, or narrow requirement fragment;
- package-specific `AGENT-NOTES.md`, when present;
- mode: `practical_v0_8_matrix`, `practical_v0_8_tc_after_matrix_accepted`,
  `initial_draft`, `revision_from_findings`, or remediation;
- for `practical_v0_8_tc_after_matrix_accepted`: accepted
  `test-design-matrix-review.md` and `review-independence.md` from a separate
  reviewer session, or `matrix-changes-required` plus one bounded
  `matrix-repair-summary.md`;
- for `revision_from_findings`: existing test-case suite, structured findings artifact, review round number, `review_mode`, and traceability matrix when available.

If a verified `stage-package.json` is provided, use the prepared fast path: read only the four package files, do not repeat source discovery/extraction, and access the full source only through the targeted fallback contract from [prepared-stage-package-format.md](../../references/agent/prepared-stage-package-format.md).

For source-first packages, follow the accepted exact-digest contract; conflicts return `blocked-input`.

## Выходы

- for `practical_v0_8_matrix`: compact `test-design-matrix.md` in `fts/<ft-slug>/work/practical/<section-id>-<scope-slug>/`, matrix writer self-check, and `prompt.matrix-to-reviewer.md`;
- canonical test-case file: `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`, only in `practical_v0_8_tc_after_matrix_accepted`, legacy `initial_draft`, or revision modes;
- for `initial_draft`: split test-design artifacts in `fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/`;
- when `dictionary-source` / reference-list rows exist: `dictionary-inventory.md` next to split test-design artifacts before TDDT/plan/TC;
- for revision in a session-based cycle: `fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/writer-rN-response.md`;
- traceability matrix when writer creates or updates it; `.xlsx` duplicate only
  for explicit session-based/promotion routes or explicit user-requested XLSX
  export, not for `practical_v0_8` by default;
- `coverage-obligation-table.md`, `coverage-metrics.md`, `fixture-catalog.md` when applicable, coverage gaps, open questions, `test-design-review.md`, Writer Quality Gate, and writer self-check in the appropriate split artifacts;
- `writer-session-log.md` and `agent-decision-log.md` when required by the stage workflow;
- `workflow-state.yaml` routing to matrix review after `practical_v0_8_matrix`, or
  to TC review only after successful canonical TC gates;
- `prompt.matrix-to-reviewer.md` after matrix-only writing;
- `prompt.tc-to-reviewer.md` after TC drafting, or `prompt.writer-to-reviewer.round-N.md` in legacy/session routes.

## Runtime Contract Anchors

- If a PDF version of the main FT is available for structural cross-check, use it to verify section structure, requirement codes, and source order; do not use PDF as a replacement for the main FT text.
- Before `initial_draft`, check `source-selection.md`: without `xhtml_available: yes`, return `blocked-input`; take tables/lists from XHTML, treat DOCX as source of truth, and do not let PDF/mockups replace the main FT.
- If sources do not define behavior, do not invent behavior; record it in `coverage gaps` or UI calibration candidates by the runtime contract.
- In `revision_from_findings`, use the structured findings artifact and traceability matrix artifact; process findings according to `review_mode`.
- For traceability findings and writer response, preserve `traceability_ref = ATOM-*`.
- Handoff by review mode: `traceability` closes coverage gaps; `structure` aligns template, order, grouping, and continuous numbering; `test-design` adds or corrects checks and expected results.
- In `practical_v0_8`, the compact `test-design-matrix.md` is a writer-authored coverage claim under review, not source of truth. It must use Russian visible headers/text and include explicit `Классы покрытия` rows for every source-backed class required by [../../references/qa/coverage-class-catalog.md](../../references/qa/coverage-class-catalog.md), including validation, format, length, mask, requiredness, dictionary, dependency, repeatable-block and integration rules when those rules exist in the source. Do not build a large atomic ledger unless an explicit legacy/development route requires it. In legacy `initial_draft`, writer builds the atomic requirements ledger first, then test cases with canonical fields and writer self-check.
- In `practical_v0_8`, the first writer invocation is always
  `practical_v0_8_matrix`: write the matrix only and do not create or modify
  `fts/**/test-cases/*.md`. If the user asks to "write test cases" but no
  accepted matrix review exists, this still means matrix-only first.
- In `practical_v0_8_tc_after_matrix_accepted`, fail closed unless
  `test-design-matrix-review.md` exists, `review-independence.md` records a
  separate reviewer session, and either the verdict is `matrix-accepted` or the
  verdict is `matrix-changes-required` with exactly one bounded
  `matrix-repair-summary.md`. A same-session or missing matrix review cannot
  unlock canonical TC writing.
- In `practical_v0_8`, Markdown `test-design-matrix.md` is the required matrix
  artifact and XLSX is optional only by explicit user request. In
  session-based/promotion routes, follow the route-specific XLSX companion
  contract.
- In production TC files, use Russian user-facing headings with natural sentence
  casing. Examples: `## Сведения о наборе`, `## Границы покрытия`, `## Сводка`.
  Do not write English process headings such as `## Summary` / `## Coverage
  Summary`, and do not title-case Russian service words as in `Сведения О
  Наборе`.
- Check smell markers from canonical QA references: test-case-forbidden-formulation-smell, test-case-abstract-oracle-smell, test-case-input-restriction-transition-oracle-smell, test-case-unsupported-numeric-validation-feedback-smell, test-case-mechanical-field-step-smell.

## Workflow

Follow the runtime workflow: [../../references/agent/writer-runtime-workflow.md](../../references/agent/writer-runtime-workflow.md).

Load deep workflow only for the actual scenario:

- process artifacts, logs, artifact-write strategy: [../../references/agent/writer-process-workflow.md](../../references/agent/writer-process-workflow.md);
- table-heavy / row-level parity writing: [../../references/agent/writer-table-workflow.md](../../references/agent/writer-table-workflow.md);
- revision by findings: [../../references/agent/writer-revision-workflow.md](../../references/agent/writer-revision-workflow.md);
- validator, Writer Quality Gate, or style remediation: [../../references/agent/writer-remediation-workflow.md](../../references/agent/writer-remediation-workflow.md).

Minimum runtime rules:

1. Do not expand scope while writing.
2. Do not invent system behavior, fields, statuses, buttons, integrations, or expected results.
3. One `TC-*` covers one check and one main expected result.
4. Preserve requirement codes literally, for example `GSR 22`.
5. Do not turn pure source gaps into fake executable `TC-*`. If the FT obligation is real but data, UI reaction or observability is missing, write a clearly marked `candidate-ui-calibration`, `blocked-observability` or `needs-test-data` case by practical route v0.8.
6. If source/support defines a dictionary, create/update `dictionary-inventory.md` and link `DICT-*`; branch examples from the FT do not replace the full dictionary.
6a. Production files under `fts/**/test-cases/*.md` must be self-contained runtime TC artifacts: no setup profile references in `Предусловия`, no stand/environment wording, no package-name leakage such as `AutoFin`, and no embedded diagnostic/design sections. Use split/work artifacts for diagnostics.
7. For `practical_v0_8_matrix`, hand off to reviewer only after creating
   `prompt.matrix-to-reviewer.md` suitable for a separate Codex session. The
   matrix must be internally consistent, every source-backed restriction must
   have explicit coverage classes or class-specific deferrals. Exact invariant:
   requiredness checks must be split by input mechanism. Current-scope blockers must be
   visible as allowed planned statuses. Do not create or update canonical TC in
   this pass.
7a. For `practical_v0_8_tc_after_matrix_accepted`, hand off to reviewer only
   after creating `prompt.tc-to-reviewer.md` suitable for a separate Codex
   session. The canonical file and accepted or once-repaired
   `test-design-matrix.md` must be synchronized, and the canonical file must
   remain `draft-ready-for-review` / `review-ready` rather than `released-*` or
   `signed-off`. For legacy/session routes, do not set
   `stage_status: ready-for-review` until
   source/parity/mockup/table/dictionary inputs, Writer Quality Gate, and
   validator blockers are closed.
8. Before `ready-for-review`, check canonical TC for unresolved generic fixture/test-data/oracle smells: `Минимальный валидный набор данных`, `валидные данные`, `валидная заявка`, `значение из тестовых данных принято/не принимается`. These formulations are allowed only when a concrete reproducible baseline, literal/parameter, or linked fixture artifact is adjacent; otherwise fix the TC or record `GAP-*` / `unclear`.
8a. `Предусловия`: reproducible setup steps = numbered action setup or fixture/API/profile; passive state only after the action that creates it.
8b. Parameter tables are allowed only when every row has the same start screen, UI level, navigation path, user action, trigger and observable expected result. Split parent/child entities, nested blocks or different screens into separate `TC-*`; do not optimize TC count over automation-readiness.
9. Before `ready-for-review`, `semantic-review-ready`, and final handoff, check each `TC-*` by [../../references/qa/test-case-runtime-format.md](../../references/qa/test-case-runtime-format.md): `Трассировка` is mandatory, optional source fields are allowed only when they add non-duplicating navigation or real source evidence. If `TC-*` uses `DICT-*`, the same id must appear in `Трассировка`; a synthetic quote cannot be presented as an FT quote.
10. Do not mix TC schemas: a metadata table does not replace parser-supported bold metadata fields from `test-case-format.md` (`**Название:**`, `**Тип:**`, `**Приоритет:**`, `**package_id:**`, `**Трассировка:**`); table-only metadata such as `| Поле | Значение |` / `| package_id | WP-01 |` is invalid. Do not duplicate runtime headings with inline/bold fields.
11. After any change to `TC-*`, `ATOM-*`, `GAP-*`, `DICT-*`, or `package_id`, synchronize canonical TC, ledger, traceability matrix, Test-design Decision Table, Package Test Design Plan, coverage artifacts, and writer response. Status `fixed` is allowed only after all affected artifacts are checked, not only the canonical file.
12. Writer-ready handoff (`ready-for-review`, `writer-draft-ready`, `semantic-review-ready`) is allowed only when current-scope validator warning/error from canonical TC, active test-design dir, and cycle outputs is either fixed, recorded as a valid `false-positive`/waiver with id/path/evidence/rationale, or unrelated to the current scope. Writer self-check and Writer Quality Gate must link to scoped validator evidence or runner validator gate evidence; do not expect reviewer to handle an obvious current-scope validator blocker after handoff.
12a. For source-backed negative/requiredness restrictions with unknown UI reaction, remediation cannot simply replace one unsupported UI mechanism with another: preserve the obligation and create a candidate TC by `negative-ui-calibration-policy.md`, or a narrow `GAP-*` / `unclear` if a candidate is impossible.
13. If an applicable dimension requires mandatory coverage classes (`numeric-format`, `exact-length`, dependency transitions, repeatable blocks, checkbox-list, generated document mapping), decompose them in `Coverage Obligation Table`, `Package Test Design Plan`, and `coverage-metrics.md` before `TC-*`.
14. If writer cannot prepare a verifiable result without new scope/source decisions, use `blocked-input`.
15. Before writer-ready handoff, run `artifact-shape-preflight` from `writer-output-format.md` and `writer-quality-gate-format.md`: split artifacts must use exact canonical headings/table columns without alias columns and without neighboring duplicates such as `# X` + `## X`; `writer-quality-gate.md` must have `gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review`; canonical TC file must not duplicate split artifact tables. On any such defect, set `blocked-input` or fix artifacts before review handoff.
16. Do not use non-canonical status aliases in writer-side artifacts: `Writer Quality Gate` and `Test Design Review` accept only `pass | fail | blocked | needs-rewrite`; `Coverage Obligation Table` accepts only `covered | gap | unclear | blocked | not-applicable | n/a`. `pass-with-gap`, `pass-with-gaps`, `planned`, `ok`, `yes`, `passed`, `failed`, and local variants are validator defects.
17. `writer-self-check.md` must not contain empty sections. Every heading section, including `Artifact Write Evidence`, must have evidence, a table/list, a link to session log / split artifact, or explicit `not-applicable` with reason.
18. `placeholder-sentinel-normalization`: in traceability-bearing split-artifact tables and reviewer matrices, do not use placeholder `-` / `N/A` in link or traceability columns. Write an explicit sentinel: `not_applicable:covered`, `not_covered:<GAP-ID>`, `unclear:<GAP-ID>`, `no_requirement_code:<source_ref>`, or `none_required:<reason>`.

## Test-design Applicability Matrix Rule

In `initial_draft`, build `Test-design applicability matrix` after the atomic requirements ledger and before finalizing test cases. See short runtime rules in [../../references/qa/coverage-runtime-checklist.md](../../references/qa/coverage-runtime-checklist.md); deep remediation uses [../../references/qa/coverage-checklist.md](../../references/qa/coverage-checklist.md).

Rules:

- every applicable coverage dimension must have linked `ATOM-*` and linked `TC-*` or `GAP-*`;
- `applicable = unclear` always requires linked `GAP-*`;
- `applicable = no` requires a source-based reason;
- linked `TC-*` must actually cover the dimension, not merely look similar.

## Canonical References

- Skill map: [../README.md](../README.md)
- Instruction contract index: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Task-start routing: [../../references/agent/task-start-skill-routing-format.md](../../references/agent/task-start-skill-routing-format.md)
- Writer runtime workflow: [../../references/agent/writer-runtime-workflow.md](../../references/agent/writer-runtime-workflow.md)
- Writer runtime contract: [../../references/agent/writer-runtime-contract.md](../../references/agent/writer-runtime-contract.md)
- Writer process workflow: [../../references/agent/writer-process-workflow.md](../../references/agent/writer-process-workflow.md)
- Writer table workflow: [../../references/agent/writer-table-workflow.md](../../references/agent/writer-table-workflow.md)
- Writer revision workflow: [../../references/agent/writer-revision-workflow.md](../../references/agent/writer-revision-workflow.md)
- Writer remediation workflow: [../../references/agent/writer-remediation-workflow.md](../../references/agent/writer-remediation-workflow.md)
- Workflow state: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Session log format: [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md)
- Agent decision log format: [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md)
- Artifact write strategy: [../../references/agent/artifact-write-strategy-format.md](../../references/agent/artifact-write-strategy-format.md)
- Writer output format: [../../references/agent/writer-output-format.md](../../references/agent/writer-output-format.md)
- Writer table artifacts format: [../../references/agent/writer-table-artifacts-format.md](../../references/agent/writer-table-artifacts-format.md)
- Dictionary inventory format: [../../references/agent/dictionary-inventory-format.md](../../references/agent/dictionary-inventory-format.md)
- Writer handoff format: [../../references/agent/writer-handoff-format.md](../../references/agent/writer-handoff-format.md)
- Writer revision output format: [../../references/agent/writer-revision-output-format.md](../../references/agent/writer-revision-output-format.md)
- Source parity check format: [../../references/agent/source-parity-check-format.md](../../references/agent/source-parity-check-format.md)
- Source-first assertion contract: [../../references/agent/source-assertions-format.md](../../references/agent/source-assertions-format.md)
- Mockup visual inventory format: [../../references/agent/mockup-visual-inventory-format.md](../../references/agent/mockup-visual-inventory-format.md)
- Test case runtime format: [../../references/qa/test-case-runtime-format.md](../../references/qa/test-case-runtime-format.md)
- Test case format: [../../references/qa/test-case-format.md](../../references/qa/test-case-format.md)
- Review findings format: [../../references/qa/review-findings-format.md](../../references/qa/review-findings-format.md)
- Traceability matrix format: [../../references/qa/traceability-matrix-format.md](../../references/qa/traceability-matrix-format.md)
- Coverage runtime checklist: [../../references/qa/coverage-runtime-checklist.md](../../references/qa/coverage-runtime-checklist.md)
- Coverage class catalog: [../../references/qa/coverage-class-catalog.md](../../references/qa/coverage-class-catalog.md)
- Coverage checklist: [../../references/qa/coverage-checklist.md](../../references/qa/coverage-checklist.md)
- Coverage obligation table format: [../../references/agent/coverage-obligation-table-format.md](../../references/agent/coverage-obligation-table-format.md)
- Test-design coverage metrics format: [../../references/agent/test-design-coverage-metrics-format.md](../../references/agent/test-design-coverage-metrics-format.md)
- Fixture catalog format: [../../references/agent/fixture-catalog-format.md](../../references/agent/fixture-catalog-format.md)
- Risk / Priority Map format: [../../references/agent/risk-priority-map-format.md](../../references/agent/risk-priority-map-format.md)
- Experience-based coverage format: [../../references/agent/experience-based-coverage-format.md](../../references/agent/experience-based-coverage-format.md)
- State model coverage format: [../../references/agent/state-model-coverage-format.md](../../references/agent/state-model-coverage-format.md)
- Traceability rules: [../../references/qa/traceability-rules.md](../../references/qa/traceability-rules.md)
- Skill boundaries: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)

## Ограничения

- Do not select a new FT package or answer “what should we take” instead of `ft-source-locator`.
- Do not define scope from scratch instead of `ft-scope-analyzer`.
- Do not review an existing suite instead of `ft-test-case-reviewer`.
- Do not run writer-reviewer orchestration instead of `ft-test-case-iteration`.
- Do not audit the agent layer instead of `agent-architecture-auditor`.
- Do not duplicate shared QA rules in this skill; add or change canonical references.
