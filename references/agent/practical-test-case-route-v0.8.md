# Practical Test Case Route v0.8

This is the default route for ordinary FT test-case writing.

The goal is to produce useful, source-bound manual test cases quickly, without
benchmark, sharding, semantic bridge, immutable runner, source assertion receipt
loops or multi-session repair cycles.

Compared with v0.7, v0.8 keeps the lightweight practical route but makes three
quality controls non-optional:

- `test-design-matrix.md` is reviewed as writer output, not trusted as source;
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
   - The brief must contain:
     - scope boundary and source references;
     - relevant FT text / table rows / PDF pages;
     - relevant mockups and support references;
     - dictionary values required by the scope;
     - open questions and assumptions;
     - candidate UI-calibration points.

3. `ft-test-case-writer`
   - Create or update exactly these required artifacts:
     - `test-design-matrix.md` in the practical scope folder;
     - canonical test cases in
       `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`.
   - Optional artifacts are allowed only when they directly improve the current
     scope:
     - `dictionary-inventory.md`;
     - `fixture-catalog.md`;
     - `ba-questions.md` or `scope-clarification-requests.md`.
   - Do not create source-assertions, source-assertion review receipts,
     semantic bridge projections, immutable attempts, benchmark configs,
     sharding artifacts, large ledgers, or final-format review artifacts in this
     route.

4. `ft-test-case-reviewer`
   - Run one practical review over the FT/PDF context, `scope-brief.md`,
     `test-design-matrix.md` and canonical test cases.
   - Default behavior: run reviewer in a separate Codex task/session. If thread
     orchestration is available, hand off the reviewer prompt to that separate
     task/session. If it is not available, stop after writer handoff and ask the
     user to run the reviewer prompt in a new session.
   - The reviewer input must exclude writer transcript, writer private
     reasoning, and process diagnostics that are not needed to judge the suite.
   - A same-session review is allowed only as a fallback practical review and
     must be labeled `reviewed-not-independent`; it cannot produce an
     independent sign-off.
   - Produce `review-findings.md` and `review-independence.md` in the practical
     scope folder.
   - Produce an explicit matrix verdict before the final TC verdict:
     `matrix-accepted`, `matrix-changes-required`, or `matrix-rejected`.
   - Classify findings as:
     - `blocking` when the test case is materially wrong or misleading;
     - `nonblocking` when the issue is wording, grouping or minor priority;
     - `needs-ui-calibration` when the FT obligation exists but the observable UI
       reaction is unknown;
     - `needs-test-data` when execution needs a fixture that is not in the
       package.

5. Revision
   - The writer performs one revision pass for blocking findings.
   - A second reviewer pass is allowed only to confirm that blocking findings
     were resolved; for independent sign-off it also runs in a separate
     reviewer task/session.
   - Do not enter an unbounded repair loop. If unresolved information remains,
     release the cases with explicit statuses instead of blocking the whole
     scope.

## Release statuses

Use these statuses in canonical test cases:

- `ready`
- `candidate-ui-calibration`
- `blocked-observability`
- `needs-test-data`
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

- `matrix-accepted` means every current-scope source obligation is represented
  as a TC, a class-specific deferred TC, or a narrow documented gap;
- `matrix-changes-required` means writer can repair the matrix and affected TC
  in one bounded revision;
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
| reviewer_task_or_session | `<id or not-available>` |
| reviewer_was_separate_session | `yes/no` |
| reviewer_input_excluded_writer_transcript | `yes/no` |
| reviewer_input_excluded_writer_private_reasoning | `yes/no` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `yes/no` |

Rules:

- `independent_signoff_claim_allowed = yes` only when
  `reviewer_was_separate_session = yes` and the reviewer did not receive writer
  transcript/private reasoning.
- If a separate reviewer session is not available, stop after writer handoff and
  ask the user/controller to launch the reviewer prompt in a new session. If the
  user explicitly chooses a same-session fallback, complete only a practical
  review and label it `reviewed-not-independent`; do not call the suite signed
  off or independently signed off.
