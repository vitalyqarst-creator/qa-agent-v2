# Practical Test Case Route v0.8

This is the default route for ordinary FT test-case writing.

The goal is to produce useful, source-bound manual test cases quickly, without
benchmark, sharding, semantic bridge, immutable runner, source assertion receipt
loops or multi-session repair cycles.

Compared with v0.7, v0.8 keeps the lightweight practical route but makes three
quality controls non-optional:

- when DOCX and PDF are both present, `source-parity-check.md` is created before
  writer handoff, not discovered late by reviewer;
- `test-design-matrix.md` is reviewed as writer output, not trusted as source;
- canonical `TC-*` writing is gated by accepted matrix review, so coverage defects
  are caught before the expensive prose-writing step;
- independent sign-off requires a separate reviewer Codex task/session by
  default;
- practical-route outputs must fail closed when heavy-route artifacts appear
  without an explicit user-selected route.

Use heavier routes only when the user explicitly asks for them by name, for
example benchmark, sharding, semantic bridge, source-qualified immutable
`ft-agent run`, incremental update, or UI automation preparation.

For a normal request such as "write test cases", the agent must not propose or
start those heavier routes as alternatives. If a prompt is ambiguous, choose
this practical route and record any remaining uncertainty as TC status, BA
question, or UI-calibration candidate.

## Macro-stage execution

Default user-facing execution for "write test cases for this scope" is one
macro-stage: continue from the current valid handoff until one of these terminal
conditions occurs:

- canonical test cases are accepted by independent TC review and published as an
  accepted baseline;
- one bounded matrix repair or one bounded TC revision was performed and the
  remaining issue is represented by explicit `candidate-ui-calibration`,
  `blocked-observability`, `needs-test-data` or `needs-future-clarification`
  statuses;
- source/support/mockup input is contradictory or missing enough to require a BA
  answer before the obligation can be represented;
- a real tool/runtime failure prevents safe continuation.

Do not stop for user confirmation after internal practical handoffs when the next
prompt is already materialized and no external decision is needed. In particular,
continue automatically across:

- matrix-only writer handoff -> independent matrix review;
- `matrix-changes-required` -> one bounded matrix repair -> TC writing from the
  repaired matrix, without a second matrix review by default;
- `matrix-accepted` -> canonical TC writing;
- TC writer handoff -> independent TC review;
- `tc-changes-required` -> one bounded TC revision -> release with explicit
  residual statuses, without a second TC review by default.

Default review budget per scope is capped at:

- one independent matrix review;
- one independent TC review;
- one bounded writer repair/revision.

Do not start a second matrix review, second TC review, final-format review,
semantic regression or another repair loop unless a validator contract failure
prevents publication or the user explicitly requests another review round. A
reviewer finding is not by itself permission to loop indefinitely: after the
bounded revision, publish a transparent FT-first baseline and keep unresolved
execution details in the case statuses.

After each internal handoff, run the relevant validator gate. If the gate fails
because practical-route infrastructure is inconsistent with this contract, fix
the smallest agent-layer rule that unlocks the documented route; do not create
fake canonical TC files, fake review evidence, heavy-route artifacts or
placeholder outputs just to satisfy a stale validator.

For small scopes (rough guide: no more than 15 source rows and no more than 20
planned TC), use the fast path inside this same route:

- keep `test-design-matrix.md` and both independent reviews;
- skip optional diagnostics, XLSX companions, large ledgers and alias prompts
  unless a validator or reviewer finding proves they are required;
- write only the artifacts required for the next gate and final traceability;
- report timings and blockers in the final summary rather than stopping between
  gates.

## Route

1. `ft-source-locator`
   - Select the FT package.
   - Register the main DOCX, mandatory XHTML, PDF cross-check, support files,
     mockups and package `AGENT-NOTES.md`.
   - Create only the source-selection / scope-options artifacts needed for the
     next step.

2. `ft-scope-analyzer`
   - Confirm one or more external scopes by FT section/subsection.
   - For each selected scope, create one compact `scope-brief.md` under
     `fts/<ft-slug>/work/practical/<section-id>-<scope-slug>/`.
   - If the main FT has both DOCX and PDF, create `source-parity-check.md`
     before writer handoff and list it in the brief. Missing parity evidence is
     `blocked-input`; do not let writer or reviewer discover it late.
   - If the scope is based on table rows, actions, fields, document mappings or
     status rows, create a compact `source-row-inventory.md` before writer
     handoff. It may be lightweight, but it must name every in-scope row/value
     class the writer must cover or defer.
   - The brief must contain:
     - scope boundary and source references;
     - relevant FT text / table rows / PDF pages;
     - source parity conclusions and mandatory requirement IDs, when
       `source-parity-check.md` exists;
     - relevant mockups and support references;
     - dictionary values required by the scope;
     - open questions and assumptions;
     - candidate UI-calibration points.

3. `ft-test-case-writer` — design-matrix-only pass
   - Create or update exactly these required artifacts:
     - `test-design-matrix.md` in the practical scope folder;
     - `writer-self-check.md` or an equivalent compact writer check for the
       matrix;
     - `prompt.matrix-to-reviewer.md` for a separate reviewer Codex task/session.
   - Do not create, update or overwrite canonical test cases under
     `fts/<ft-slug>/test-cases/*.md` in this pass. If such a file already exists
     from an earlier or failed run, do not treat it as current output until the
     matrix review is accepted and the TC-writing pass intentionally refreshes it.
   - Set routing to reviewer with `review_mode = matrix_review`.
   - Markdown `test-design-matrix.md` is the default and required matrix artifact.
     Do not create an XLSX duplicate in `practical_v0_8` unless the user
     explicitly asks for XLSX export.
   - Optional artifacts are allowed only when they directly improve the current
     scope:
     - `dictionary-inventory.md`;
     - `fixture-catalog.md`;
     - `ba-questions.md` or `scope-clarification-requests.md`.
   - Do not create source-assertions, source-assertion review receipts,
     semantic bridge projections, immutable attempts, benchmark configs,
     sharding artifacts, large ledgers, or final-format review artifacts in this
     route.

4. `ft-test-case-reviewer` — matrix review gate
   - Run `matrix_review` over FT/PDF context, `scope-brief.md`,
     `source-row-inventory.md` / dictionary / mockup context when present, and
     `test-design-matrix.md`.
   - Do not review canonical test cases in this pass. The expected current TC file
     state is "not created yet" or "old draft ignored".
   - Default behavior: run reviewer in a separate Codex task/session. If thread
     orchestration is available, hand off the reviewer prompt to that separate
     task/session. If it is not available, stop after writer handoff and ask the
     user to run the reviewer prompt in a new session.
   - The reviewer input must exclude writer transcript, writer private
     reasoning, and process diagnostics that are not needed to judge the suite.
   - A same-session review is allowed only as a fallback practical review and
     must be labeled `reviewed-not-independent`; it cannot produce an
     independent sign-off.
   - Produce `test-design-matrix-review.md` and `review-independence.md` in the
     practical scope folder.
   - Markdown matrix review is enough for practical route. Do not require or
     create `round-N-traceability-matrix.xlsx` unless the user explicitly asks
     for XLSX export or an explicit session-based/production-promotion route was
     selected.
   - Produce exactly one matrix verdict:
     `matrix-accepted`, `matrix-changes-required`, or `matrix-rejected`.
   - If verdict is not `matrix-accepted`, route back to writer for matrix repair;
     do not route to canonical TC writing.

5. `ft-test-case-writer` — TC draft after accepted matrix
   - Start only when `test-design-matrix-review.md` has verdict
     `matrix-accepted` and `review-independence.md` shows the matrix reviewer ran
     in a separate session for independent sign-off.
   - Create or update canonical test cases in
     `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`.
   - Keep the canonical file in `draft-ready-for-review` or `review-ready`;
     writer must not mark it `released-*`, `signed-off`,
     `independently-signed-off` or equivalent before TC review has accepted the
     suite.
   - The canonical file must remain draft/review-ready before an independent
     reviewer pass accepts it.
   - Exact release invariant: no `released-*`, `signed-off` or equivalent status
     before an independent reviewer pass accepts the canonical cases.
   - Create `prompt.tc-to-reviewer.md` for a separate TC reviewer Codex
     task/session.

6. `ft-test-case-reviewer` — TC review gate
   - Run practical TC review over FT/PDF context, `scope-brief.md`, accepted
     `test-design-matrix.md`, `test-design-matrix-review.md`, and canonical test
     cases.
   - Default behavior: run reviewer in a separate Codex task/session. The reviewer
     input must exclude writer transcript and private reasoning.
   - Produce `review-findings.md` and update `review-independence.md` with
     TC-review evidence.
   - Classify findings as:
     - `blocking` when the test case is materially wrong or misleading;
     - `nonblocking` when the issue is wording, grouping or minor priority;
     - `needs-ui-calibration` when the FT obligation exists but the observable UI
       reaction is unknown;
     - `needs-test-data` when execution needs a fixture that is not in the
       package.

7. Revision
   - The writer performs one revision pass for blocking findings.
   - A second reviewer pass is not part of the default practical route. It is
     allowed only when a validator contract failure prevents publication or the
     user explicitly requests another review round.
   - Do not enter an unbounded repair loop. If unresolved information remains,
     release the cases with explicit statuses instead of blocking the whole
     scope.

## Release statuses

Use these statuses in canonical test cases:

- `ready`
- `candidate-ui-calibration`
- `blocked-observability`
- `needs-test-data`
- `needs-future-clarification`
- `not-automatable-manual-only`

The scope can be released as:

- `released-ft-first`;
- `released-with-calibration-pending`;
- `released-with-blocked-observability`;
- `blocked-source`.

`blocked-source` is allowed only when the source package is missing or
contradictory enough that the requirement itself cannot be represented.

## Test-design matrix

The matrix is mandatory because it is the cheapest way to prove coverage without
large ledgers.

`test-design-matrix.md` is a user-facing artifact. Column headers and
human-readable cell text must be Russian, because the user can inspect this file
to verify whether the planned coverage is acceptable. English is allowed only for
stable metadata values or source literals that are intentionally English.

The matrix is writer output under review, not an accepted source of truth.
Reviewer must re-derive coverage from FT/PDF/XHTML/support/dictionaries/mockups
and then compare that independent view with the matrix. If the matrix is
incomplete or misleading, reviewer returns `matrix-changes-required` or
`matrix-rejected`; canonical test cases must not be independently signed off
until the matrix is accepted.

Minimum columns:

| Источник | Проверяемое утверждение | Измерение тест-дизайна | Классы покрытия | TC-ID | Статус | Примечания |
| --- | --- | --- | --- | --- | --- | --- |

Rules:

- one row represents one source-backed check, one coverage class, or one
  consciously deferred check;
- every executable FT obligation must map to a `TC-*`;
- every unexecutable obligation must map to a `candidate-ui-calibration`,
  `blocked-observability` or `needs-test-data` `TC-*`;
- `Классы покрытия` is mandatory for validation, format, length, mask,
  allowed-symbol, dictionary, requiredness, visibility-condition, dependency,
  file-upload, integration, status/lifecycle and repeatable-block rules;
- choose the exact class group from
  [../qa/coverage-class-catalog.md](../qa/coverage-class-catalog.md); activate a
  group only when the current source contains the matching rule;
- do not create test cases for glossary/status-table rows when later FT sections
  define the actual screen, action and expected result; use those rows as
  supporting context in `Источник`;
- do not use English technical aliases such as `source_ref`, `atomic_check`,
  `coverage_classes` as the visible headers in this Markdown file. Internal
  tools may normalize the Russian columns to stable keys, but the checked-in
  matrix remains Russian.

Matrix review gate:

- Canonical TC writing is unlocked by verdict `matrix-accepted` from
  `test-design-matrix-review.md`, or by exactly one bounded matrix repair after
  `matrix-changes-required`, recorded in `matrix-repair-summary.md`.
- `matrix-accepted` means every current-scope source obligation is represented
  as a planned TC, a class-specific deferred TC, or a narrow documented gap;
- `matrix-changes-required` means writer can repair the matrix in one bounded
  revision. After this repair, do not run a second matrix review by default; TC
  reviewer will judge the repaired matrix together with the canonical test cases;
- `matrix-rejected` means the coverage plan is materially unreliable and TC
  review must stop until the matrix is rebuilt.

## Mandatory coverage class decomposition

The writer must not treat one sample invalid value as complete negative
coverage. For every source-backed restriction, decompose the rule into explicit
classes first, then write or defer each class.

Use the canonical catalog:
[../qa/coverage-class-catalog.md](../qa/coverage-class-catalog.md).

The catalog covers the common source-backed rule groups:

- digits-only and allowed-symbol restrictions;
- text/name-like fields;
- alphanumeric fields;
- masks and patterns;
- exact length and min/max length;
- numeric ranges and amounts;
- dates and date/time;
- requiredness and conditional requiredness;
- dictionaries, closed lists, autocomplete and integrations;
- file upload;
- repeatable blocks and child rows;
- uniqueness and duplicate checks;
- status/lifecycle rules;
- cross-field dependencies and combinations;
- generated documents and mappings.

If the exact UI reaction is unknown, do not drop the class. Keep the class in the
matrix and create a `candidate-ui-calibration` or `blocked-observability` case
with concrete input and a clear `Требуется подтверждение`. Unknown UI mechanism
changes status and expected-result precision; it does not remove the obligation.

Requiredness classes must be split by input mechanism before writing TC. A single
"all required fields are empty" TC is valid only when all listed fields are
reachable by the same setup, have the same user input mechanism, the same trigger
and the same observable oracle. Otherwise use separate TC or a parameter table in
one TC, and ensure every listed field is actually exercised in the steps.

Parameter tables are allowed only when every row keeps the same start screen,
same UI level, same navigation path, user action, trigger, pass/fail oracle and
expected result. If rows cross parent/child entities, different cards, nested
blocks, tables, lists or screens, split them into separate `TC-*`; do not
optimize the case count at the cost of automation-readiness.

## Canonical test-case quality gates

Before handing off to reviewer, the writer checks every canonical file:

- no service/debug sections such as UI Automation Prep details, benchmark data,
  runner diagnostics, bridge/attempt metadata or internal process logs;
- human-facing runtime text is Russian, except allowed metadata values such as
  `Positive`, `Negative`, `High`, `Medium`, `Low`;
- no phrases such as `source-backed`, `observable source`, `registered-card`,
  `semantic projection`, `exact credit-conveyor screen`, `fixture`, `support`,
  `oracle`, `lifecycle`, `signed-off`, `hash`, `receipt`, `scope`, or other
  agent-process language in runtime test cases; stable IDs such as
  `FX-DADATA-*` may appear only as code-like fixture identifiers in `Трассировка`
  or `Тестовые данные`, while the surrounding prose remains Russian;
- title describes user-visible behavior, not traceability IDs or internal
  obligations;
- `Предусловия` first open the relevant form/card/screen/section before entering
  a block;
- `Тестовые данные` contain concrete values or a clear `needs-test-data` reason;
- setup/precondition data must respect the source-defined input mechanism of the
  fields used to create it. If a TC creates or prepares an entity through fields
  backed by DaData, BIK, dictionary/autocomplete or another integration, use a
  verified fixture for those fields even when the integration itself is not the
  main test objective; otherwise keep the TC `needs-test-data` with the exact
  missing fixture named;
- steps are executable user actions or checks, not restatements of `BSR-*`,
  `ATOM-*`, `ASSERT-*`, hashes, source rows or abstract obligations;
- expected result is observable in UI/API/document output or explicitly marked
  `blocked-observability`;
- one test case has one main expected result;
- positive, negative and boundary coverage is driven by the FT text, dictionaries
  and support notes, not by one-code-one-case mechanics;
- if a dictionary or fixed list is referenced, the writer uses the full relevant
  list from support/source, not a few examples;
- if DaData or another integration is in scope, test cases use a fixed verified
  fixture with exact query/input and exact expected suggestion/result; do not ask
  the tester to call a live service during test execution.

## Practical-route heavy-artifact guard

In `practical_v0_8`, these artifacts are forbidden unless the user explicitly
selected a heavy/development route by name:

- `source-assertions.json`;
- `source-assertion-review.json`;
- `source-evidence.md`;
- `semantic-design*` / `semantic_design*`;
- `*shard*` artifacts;
- `run-config*.json` for `ft-agent run`;
- `work/iterations/`;
- benchmark/eval configs inside the active FT package.

XLSX traceability duplicates are also not practical-route defaults. They are
allowed only by explicit user request or explicit session-based/promotion route.

If any of these appear during ordinary practical work, stop the route and repair
the handoff. Do not silently continue through a mixed practical/source-qualified
process.

## Business-analyst questions

Questions to BA must be useful without the analyst opening agent internals.

Each question must include:

- source section/table/row/code;
- affected field/action/status;
- current ambiguity;
- why it blocks or changes test-case execution;
- concrete answer format expected from BA;
- candidate TC/status affected.

If prior BA-answer files exist in `support/` or the package work folder, read and
reuse them before asking again.

If BA information is missing but the obligation can still be represented, release
the test case with `candidate-ui-calibration`, `blocked-observability` or
`needs-test-data` instead of stopping the whole scope.

## Reviewer focus

The practical reviewer must block:

- a matrix that has not been independently checked against FT/PDF/XHTML/support;
- a suite that claims independent sign-off without separate-session evidence;
- any final verdict called `signed-off` when `independent_signoff_claim_allowed`
  is not `yes`;
- pseudo-test cases that cannot be executed;
- generic fixtures such as “valid entity” without concrete data or a
  `needs-test-data` status;
- merged checks that hide independent positive/negative/boundary behavior;
- one invalid representative that claims to cover several independently
  derivable classes;
- a `candidate-ui-calibration` case that drops a source-backed class instead of
  preserving it with concrete input and a calibration question;
- invented UI messages, validation triggers, buttons, integrations or statuses;
- English agent-process wording in Russian runtime fields;
- missed dictionaries, missing boundary classes, missing equivalence classes and
  missing negative classes when the FT states restrictions;
- generic requiredness cases that list several fields but exercise only a subset
  of them, or merge typed input, dictionary/autocomplete, system-filled,
  autofilled, readonly and repeatable-row fields without a clear decomposition;
- English visible headers or English process wording in `test-design-matrix.md`
  when Russian human-readable wording is expected;
- use of status/glossary rows as standalone tests when later FT sections define
  the actual behavior.

The reviewer should not require heavy process artifacts when the matrix,
scope brief and canonical test cases are sufficient to prove coverage.

## Reviewer independence evidence

Create `review-independence.md` in the practical scope folder.

Minimum fields:

| field | value |
| --- | --- |
| reviewer_task_or_session | `<actual Codex thread/session id>` |
| reviewer_was_separate_session | `yes/no` |
| reviewer_input_excluded_writer_transcript | `yes/no` |
| reviewer_input_excluded_writer_private_reasoning | `yes/no` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `yes/no` |

Rules:

- `independent_signoff_claim_allowed = yes` only when
  `reviewer_was_separate_session = yes` and the reviewer did not receive writer
  transcript/private reasoning.
- `reviewer_task_or_session` must be the actual Codex thread/session id, for
  example `019fc5cf-8bfe-7693-bf2f-c3c55cca4824`. Do not write role aliases
  such as `matrix-review-round-2`, `<scope>-tc-review`, `not-available`, or
  invented pseudo ids. If the reviewer cannot know its own id, the controller
  that launches the separate session must pass that id into the reviewer prompt
  and the reviewer must copy it verbatim.
- If a separate reviewer session is not available, stop after writer handoff and
  ask the user/controller to launch the reviewer prompt in a new session. If the
  user explicitly chooses a same-session fallback, complete only a practical
  review and label it `reviewed-not-independent`; do not call the suite signed
  off or independently signed off.

## Production TC visible headings

Production files under `fts/**/test-cases/*.md` are user-facing Russian
artifacts. Use natural Russian sentence casing for visible headings:

- `## Сведения о наборе`, not `## Сведения О Наборе`;
- `## Границы покрытия`, not `## Границы Покрытия`;
- `## Сводка`, not `## Summary` or `## Coverage Summary`.

English remains allowed only for approved metadata enum values such as
`Positive`, `Negative`, `High`, `Medium`, `Low`.
