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

The practical route is fixed: matrix only → separate-session matrix review →
canonical TC → separate-session TC review → at most one bounded revision →
final separate-session TC review. Do not create canonical TC until `test-design-matrix-review.md` is
`matrix-accepted`, except for a documented `round-cap-reached` decision with
`source_contradiction: no` and `tc_with_status_decision: write-with-statuses`.
Record matrix and TC-review routing in the linked
`practical-stage-summary.md` with `next_stage_transition`; write status-marked TC when the obligation is
clear but UI/data evidence is missing, and block only a source contradiction.
In the matrix pass, do not create or modify canonical test cases.

Practical default: do not create source assertions, XLSX duplicates, semantic
bridge projections, immutable attempts, sharding or benchmark artifacts unless
the user explicitly selects such a route. The detailed transition, validation,
root-consistency and round-cap policy is canonical in
`practical-test-case-route-v0.8.md`.

The first writer invocation is always `practical_v0_8_matrix`; fail closed unless a separate-session matrix review has verdict `matrix-accepted`, or the documented round-cap exception above applies, before canonical TC writing. For `matrix-changes-required`, at most one bounded matrix repair; for `tc-changes-required`, at most one bounded TC revision followed by a final separate-session TC review.
Default: do not create XLSX duplicates.

The practical-stage summary records `code_root`, `ft_package_root`,
`artifact_write_root`, `root_split_allowed`, `validator_errors_classification`,
`validator_warnings_classification`, `per_scope_next_stage_transitions`,
`production_tc_clean`, `git_persistence`, `source_restore_provenance` and
`source_restore_sha256` before the next safe step.

## Входы

- selected FT package, bounded scope, main DOCX/XHTML and package `AGENT-NOTES.md`;
- required parity, row, dictionary and mockup artifacts only when their source
  type makes them applicable;
- selected mode and its active transition prompt;
- for `practical_v0_8_tc_after_matrix_accepted`: accepted separate-session
  `test-design-matrix-review.md`, matching `review-independence.md` and linked
  `practical-stage-summary.md`.

Use a verified `stage-package.json` only through its prepared-package contract.
Missing source or inconsistent handoff is `blocked-input`, never a reason to
invent behavior.

## Выходы

- matrix pass: `work/practical/<scope>/test-design-matrix.md` and
  `prompt.matrix-to-reviewer.md`, with no canonical TC change;
- TC pass: canonical `test-cases/<section-id>-<scope>.md`, current prompt,
  quality gate and only applicable split artifacts;
- revision: affected canonical TC, response to the structured findings and
  `work/practical/<scope>/tc-revision-summary.md` with `## Status Assertions`;
- always: current workflow links, session/decision logs only when the selected
  route requires them, and an accurate practical stage summary.

## Runtime Contract Anchors

- DOCX is source of truth, XHTML is mandatory extraction source and PDF is a
  structural cross-check. Mockups clarify steps only; they never create rules.
- One `TC-*` has one check and one main observable result. Preserve real
  requirement codes and `traceability_ref = ATOM-*` where applicable.
- Production prose is Russian. The matrix is a writer claim under review, not
  source of truth; its user-facing `Классы покрытия` rows are Russian.
- Never create an executable TC from a pure gap. Use the practical status policy
  for clear obligations whose UI reaction, data or access is not yet known.

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
   visible as allowed planned statuses. Use Codex thread tools as the default
   handoff path: first run `scripts/practical_review_preflight.py` and write an
   `allowed` `review-launch-preflight.json`; if it is blocked, do not create a
   reviewer task. If it passes and thread tools are not loaded, discover them with `tool_search`, then
   use `list_projects` / `create_thread` to launch the reviewer prompt in a
   separate Codex task and immediately create controller-owned
   `review-dispatch.json` with the returned thread id. If the runtime cannot
   expose thread tools, set `blocked-reviewer-session-tool-unavailable`; do not
   run same-session review as the route verdict. Do not create or update
   canonical TC in this pass.
7a. For matrix review completion, do not silently continue to TC writing or stop
   with only raw reviewer findings. Ensure `practical-stage-summary.md` exists
   and names accepted scopes, `round-cap-reached`/blocked scopes, concrete
   reasons, whether status-marked TC writing is allowed, and the next safe step.
7b. For `practical_v0_8_tc_after_matrix_accepted`, hand off to reviewer only
   after creating `prompt.tc-to-reviewer.md` suitable for a separate Codex
   session. First run `scripts/practical_review_preflight.py` for `tc_review`
   and create the reviewer task only on `allowed: true`. The canonical file and accepted or once-repaired
   `test-design-matrix.md` must be synchronized, and the canonical file must
   remain `draft-ready-for-review` / `review-ready` rather than `released-*` or
   `signed-off`. Use the same Codex thread-tool handoff contract as matrix
   review; same-session review can be advisory only and cannot authorize bounded
   revision, acceptance or release unless the workflow explicitly records
   `controller_authorized_advisory_revision: yes`. Advisory review findings must
   be read from `advisory-review-findings.md`, not from release-grade
   `review-findings.md`. For legacy/session routes, do not set
   `stage_status: ready-for-review` until
   source/parity/mockup/table/dictionary inputs, split `Writer Quality Gate`,
   clean production TC files, and validator blockers are closed.
8. Before `ready-for-review`, check canonical TC for unresolved generic fixture/test-data/oracle smells: `Минимальный валидный набор данных`, `валидные данные`, `валидная заявка`, `значение из тестовых данных принято/не принимается`. These formulations are allowed only when a concrete reproducible baseline, literal/parameter, or linked fixture artifact is adjacent; otherwise fix the TC or record `GAP-*` / `unclear`.
8a. `Предусловия`: reproducible setup steps = numbered action setup or fixture/API/profile; passive state only after the action that creates it.
8b. Parameter tables are allowed only when every row has the same start screen, UI level, navigation path, user action, trigger and observable expected result. Split parent/child entities, nested blocks or different screens into separate `TC-*`; do not optimize TC count over automation-readiness.
8c. Before `ready-for-review` and after any writer repair, check that production TC runtime fields are Russian user-facing prose; use the agent-process vocabulary blacklist in `test-case-runtime-format.md`. This is a writer gate blocker, not reviewer cleanup.
8d. Before `ready-for-review`, apply runtime rule cards from `test-case-runtime-format.md` and `coverage-class-catalog.md`: duplicate input = negative by default; no downstream-as-local-rejection; no injected requiredness; no optional-as-required; no field input after save. Treat violations as `tc-regression-smells`.
8e. Before `ready-for-review`, fill the recurrent-defect rows in `Writer Quality Gate`: `tc-metadata-integrity`, `lifecycle-execution-ownership`, `step-executability`, `fixture-resolution`, `source-obligation-completeness`, `closed-dictionary-completeness`, `boundary-class-completeness`, `creation-form-isolation-coverage`, `runtime-execution-semantics` and `expected-result-singularity`. These are writer gates, not optional reviewer cleanup. A reference to another TC step, a generic status TC that mixes object/UI levels, a made-up fixture/entity, a silently omitted member of a source list, an alternative pass oracle, only one arbitrary invalid sample, an applicable new-object form without an immediate, explicit field-level check against value leakage from the prior object, a create/edit alternative, an inferred manual change of an autofilled value, or an upload cardinality check phrased as document type fails this gate.
8f. A Writer Quality Gate is valid only with the current `**Версия контракта:**` from `writer-quality-gate-format.md`. When a new required gate item appears, do not append a `pass` row to migrate an old draft. Set `blocked-quality-gate`, rerun the current matrix/TC self-check and cite the checked artifacts/TC ids (or `not_applicable:` with source reason) before reviewer launch. One row per item; log history separately.
9. Before `ready-for-review`, `semantic-review-ready`, and final handoff, check each `TC-*` by [../../references/qa/test-case-runtime-format.md](../../references/qa/test-case-runtime-format.md): `Трассировка` is mandatory, optional source fields are allowed only when they add non-duplicating navigation or real source evidence. If `TC-*` uses `DICT-*`, the same id must appear in `Трассировка`; a synthetic quote cannot be presented as an FT quote.
10. Do not mix TC schemas: a metadata table does not replace parser-supported bold metadata fields from `test-case-format.md` (`**Название:**`, `**Тип:**`, `**Приоритет:**`, `**package_id:**`, `**Трассировка:**`); table-only metadata such as `| Поле | Значение |` / `| package_id | WP-01 |` is invalid. Do not duplicate runtime headings with inline/bold fields.
11. After any change to `TC-*`, `ATOM-*`, `GAP-*`, `DICT-*`, or `package_id`, synchronize canonical TC, ledger, traceability matrix, Test-design Decision Table, Package Test Design Plan, coverage artifacts, and writer response. Status `fixed` is allowed only after all affected artifacts are checked, not only the canonical file.
12. Writer-ready handoff (`ready-for-review`, `writer-draft-ready`, `semantic-review-ready`) is allowed only when current-scope validator warning/error from canonical TC, active test-design dir, and cycle outputs is either fixed, recorded as a valid `false-positive`/waiver with id/path/evidence/rationale, or unrelated to the current scope. Writer self-check and Writer Quality Gate must link to scoped validator evidence or runner validator gate evidence; do not expect reviewer to handle an obvious current-scope validator blocker after handoff.
12a. For source-backed negative/requiredness restrictions with unknown UI reaction, remediation cannot simply replace one unsupported UI mechanism with another: preserve the obligation and create a candidate TC by `negative-ui-calibration-policy.md`, or a narrow `GAP-*` / `unclear` if a candidate is impossible.
12b. After a bounded TC revision, compare every affected canonical case with its
runtime inputs. `Статус исполнения: ready` is forbidden when `Требуется подтверждение`
remains, or the case still needs an unverified fixture, concrete
test data, access path or observable oracle. Record each affected `TC-*` and its
exact final status under `## Status Assertions` in `tc-revision-summary.md`.
Before overwriting an existing canonical file, create and verify its immutable
`pre_write_baseline` with `scripts/practical_snapshot_preflight.py`; a failed
snapshot blocks the write and must not be repaired in place.
Route only to the final independent reviewer; writer cannot sign off, release or
start UI preparation from a bounded revision.
12c. If a validator detects only a status/confirmation/summary inconsistency
after that revision and before final review, perform at most one contract-only
status repair. It may not change coverage, test design, runtime steps, expected
results, traceability or source interpretation. Record `## Contract-only Repair`,
refresh `## Status Assertions` and refresh the practical stage summary with the
current Code Version Gate commit. This repair is not permission for another
writer/reviewer loop.
13. If an applicable dimension requires mandatory coverage classes (`numeric-format`, `exact-length`, dependency transitions, repeatable blocks, independent creation, checkbox-list, generated document mapping), decompose them in `Coverage Obligation Table`, `Package Test Design Plan`, and `coverage-metrics.md` before `TC-*`.
13a. For a status/permission/visibility check, one executable TC has one object
level, one actor capability and one observable outcome. Do not merge an
administrator-positive and a restricted-user-negative assertion into one TC.
Use exact visible labels from mockups or approved UI evidence in runtime steps;
a section title from the FT is not a UI label. Use only `Статус исполнения` for
the execution state; do not add `Статус oracle` or `Статус тест-кейса`.
14. If writer cannot prepare a verifiable result without new scope/source decisions, use `blocked-input`.
15. Before writer-ready handoff, run `artifact-shape-preflight` from `writer-output-format.md` and `writer-quality-gate-format.md`: split artifacts must use exact canonical headings/table columns without alias columns and without neighboring duplicates such as `# X` + `## X`; `writer-quality-gate.md` must have `gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review`; canonical TC file must not duplicate split artifact tables or embed split-design sections. On any such defect, set `blocked-input` or fix artifacts before review handoff.
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

- [Skill map](../README.md) and [instruction contract index](../../references/agent/instruction-contract-index.md).
- [Writer runtime contract](../../references/agent/writer-runtime-contract.md) and the selected writer workflow above.
- [Workflow-state format](../../references/agent/workflow-state-format.md), [writer output format](../../references/agent/writer-output-format.md) and [writer quality gate](../../references/agent/writer-quality-gate-format.md).
- For a source type or quality dimension, load only its matching format from the instruction contract index.

## Ограничения

- Do not select a new FT package or answer “what should we take” instead of `ft-source-locator`.
- Do not define scope from scratch instead of `ft-scope-analyzer`.
- Do not review an existing suite instead of `ft-test-case-reviewer`.
- Do not run writer-reviewer orchestration instead of `ft-test-case-iteration`.
- Do not audit the agent layer instead of `agent-architecture-auditor`.
- Do not duplicate shared QA rules in this skill; add or change canonical references.
