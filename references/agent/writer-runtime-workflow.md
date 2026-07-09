# Writer Runtime Workflow

This is the compact runtime workflow for `ft-test-case-writer`. It is loaded for all writer scenarios and must stay short. Deep table, revision, process and remediation details live in separate writer references.

## Preconditions

Use the writer only when the FT package and scope are already selected. If the package, source document or scope boundary is unclear, route back to `ft-source-locator` or `ft-scope-analyzer`.

Required runtime inputs:

- FT package path under `fts/<ft-slug>/...`;
- confirmed scope or stage handoff;
- main FT source and relevant support files;
- package `AGENT-NOTES.md` when present;
- mode: `initial_draft`, `revision_from_findings` or remediation.

Do not expand the scope while writing. New source ambiguity, missing mandatory handoff artifacts or unresolved coverage gaps must become `blocked-input` or explicit `coverage gap`, not assumed behavior.

## Common Flow

1. Confirm the selected package, source files, scope boundary and mode.
2. Read package-specific `AGENT-NOTES.md` before scope analysis, writing or review handoff.
3. If DOCX and PDF are both available for the main FT, read `source-parity-check.md` before writer handoff. Missing mandatory parity evidence blocks `ready-for-review`.
4. For UI scopes, read `mockup-visual-inventory.md` before using mockups. Use mockups only to make UI steps concrete; do not infer business rules, allowed values, requiredness, validation or expected results from screenshots.
5. For table-heavy or row-level parity scopes, follow `writer-table-workflow.md` before ledger and TC writing.
6. Build coverage obligations and metrics for applicable dimensions before TC writing; one independently checkable obligation becomes one atom, one candidate TC obligation, or one explicit `GAP-*`.
7. Build atomic requirements from source-backed statements. One independently checkable obligation becomes one atom.
8. Create or update the canonical test-case file under `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`.
9. Keep every `TC-*` executable, observable and traceable to `ATOM-*`, requirement code, source row or explicit `GAP-*`.
10. Run `Test Design Review`, `Writer Quality Gate` and writer self-check before routing to reviewer.
11. Update `workflow-state.yaml`, session log, decision log and `prompt.writer-to-reviewer.round-N.md` only after the output is actually ready for review.

## Test-Case Rules

Use `test-case-runtime-format.md` for the default manual TC shape and `test-case-format.md` only for deep style or validator remediation.

Runtime rules:

- one test case covers one check and one main expected result;
- do not combine positive acceptance and invalid-value rejection in one `TC-*`;
- do not use `TC-*` as a container for gap or unclear notes; candidate UI calibration TC are allowed only with `oracle_status = ui-calibration-required` and explicit calibration marker;
- do not turn metadata-only statements such as value type into standalone behavior without a source-backed observable oracle;
- do not use source dumps, extraction artifacts or generic FT references as expected results;
- keep exact requirement codes such as `GSR 22` when present;
- use concrete user intent in steps, not mouse mechanics, unless the mechanism itself is the tested behavior.
- split TC that reference more than two independent source-backed obligations, unless a single visible source-backed workflow has `Scenario rationale` and atomic coverage stays traceable elsewhere.
- keep setup inside `Предусловия` as numbered action setup steps, fixture/API setup or reusable setup profile. Do not add a separate `Подготовительные шаги` section unless the current TC format already uses it. Avoid magic/passive states and ambiguous setup alternatives such as `выбрать или ввести`, `при необходимости` or `если нужно`; put `Дождаться...` / `Убедиться...` only after the action that creates the setup state.
- for production `fts/**/test-cases/*.md`, inline full preconditions in every TC: no setup profile references, stand/environment wording, package-name leakage, or missing reveal action for action-created fields such as contact-person `Фамилия`/`Имя`/`Отчество`.

## Coverage Rules

Use `coverage-runtime-checklist.md` as the default coverage prompt. Load deep coverage references only when the task profile requires them:

- numeric/date/length/mask/symbol constraints: `coverage-input-boundaries.md`;
- integration/API/async/persistence/internal effects: `coverage-integration-async.md`;
- full validator or quality-gate remediation: `coverage-checklist.md`.

If a requirement has no observable artifact, route it to `coverage gap` or `unclear`; do not fabricate API, DB, queue, status or UI evidence. Exception: source-backed input restriction/requiredness obligations with unknown UI mechanism become candidate TC with `ui-calibration-required`, not pure gaps.

For every source-backed input restriction, apply this decomposition before writing `TC-*`:

1. Derive allowed equivalence classes from the source wording.
2. Derive invalid equivalence classes from the excluded values.
3. Write positive TC for allowed representative values.
4. Write negative or candidate-negative TC for invalid representative values.
5. Emit BA questions for the unknown observable rejection mechanism.
6. For shared restrictions across similar fields/classes, state representative/pairwise selected combinations, omitted combinations and residual risk.
7. Never suppress a positive allowed-class TC because a negative candidate exists.

Example: `Возможен ввод только текстовых символов и специальный символ «-».`

- positive: letters only, for example `Иванов`;
- positive: letters with hyphen, for example `Иванов-Петров`;
- negative candidate: digit, for example `Иванов1`;
- negative candidate: special symbol other than hyphen, for example `Иванов@`;
- question/candidate for ambiguous classes such as space, Latin letters, apostrophe and `ё`, if the source does not define them.

For numeric-only, exact-length, action-created blocks, repeatable blocks, checkbox-list, generated document mapping or high-risk combinations, use `coverage-obligation-table-format.md`, `test-design-coverage-metrics-format.md`, `fixture-catalog-format.md` and `risk-priority-map-format.md` as applicable before writing `TC-*`.

## Revision Mode

For `revision_from_findings`, do not regenerate from scratch. Use `writer-revision-workflow.md`, the existing TC set, structured findings, review mode and traceability matrix when provided.

## Ready-For-Review Gate

Do not set `stage_status: ready-for-review` when any of the following is true:

- required source, parity, mockup or row-inventory artifact is missing;
- blocking coverage gap is unresolved;
- Writer Quality Gate has failed rows;
- applicable coverage metrics or required fixture catalog rows are missing;
- validator reports blocking smells;
- output was created through contaminated one-shot or fallback process;
- revision findings were ignored or only partially mapped.

Use `blocked-input` or keep the round open until the blocking condition is resolved.
