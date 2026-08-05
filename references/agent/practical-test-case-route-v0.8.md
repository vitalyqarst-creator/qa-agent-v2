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
- one bounded matrix repair plus one matrix re-review was performed and the
  matrix is still not accepted; apply the practical round-cap policy below:
  write status-marked TC for clear source obligations and block only source
  contradictions or unrepresentable obligations;
- one bounded TC revision was performed and the remaining issue is represented
  by explicit `candidate-ui-calibration`, `blocked-observability`,
  `needs-test-data` or `needs-future-clarification` statuses;
- source/support/mockup input is contradictory or missing enough to require a BA
  answer before the obligation can be represented;
- a real tool/runtime failure prevents safe continuation.

Do not stop for user confirmation after internal practical handoffs when the next
prompt is already materialized and no external decision is needed. In particular,
continue automatically across:

- matrix-only writer handoff -> independent matrix review;
- `matrix-changes-required` -> one bounded matrix repair -> one independent
  matrix re-review; if the matrix is still not `matrix-accepted`, stop before TC
  writing;
- `matrix-accepted` -> canonical TC writing;
- TC writer handoff -> independent TC review;
- `tc-changes-required` -> one bounded TC revision -> release with explicit
  residual statuses, without a second TC review by default.

If the next stage for a signed-off scope is `ft-ui-automation-prep`, first check
whether the FT package contains package-local UI access inputs:
`work/ui-automation-prep/UI-AGENT-NOTES.md`, runtime URL/entrypoint, login method
and a test account or storage-state. If these inputs are absent, do not create
an empty `automation-ready` file, empty UI evidence, or `ui-run-not-started.log`
just to mark the stage attempted. Record `ui-prep blocked-input` in the current
workflow/summary and continue with the next productive practical-route scope
when one exists. UI-prep without runtime/access input is a known external input
blocker, not a useful stage.

Default review budget per scope is capped at:

- one independent matrix review, plus one matrix re-review only after a bounded
  matrix repair;
- one independent TC review;
- one bounded writer repair/revision.

Do not start an extra matrix review beyond the single repair re-review, a second
TC review, final-format review, semantic regression or another repair loop unless
a validator contract failure prevents publication or the user explicitly requests
another review round. A reviewer finding is not by itself permission to loop
indefinitely: after the bounded revision, publish a transparent FT-first baseline
and keep unresolved execution details in the case statuses.

## Root consistency gate

At the start of every practical stage and in every `practical-stage-summary.md`,
record the roots used for code, FT data and artifact writes:

| field | value |
| --- | --- |
| code_root | `<version-gated repository/worktree root>` |
| ft_package_root | `<FT package root used as input>` |
| artifact_write_root | `<root where this stage writes artifacts>` |
| root_split_allowed | `yes/no` |
| root_split_authority | `<user/controller approval, or not-applicable>` |

Also record the version gate:

| field | value |
| --- | --- |
| code_branch | `<branch name, or detached HEAD>` |
| code_commit | `<exact commit SHA>` |
| version_gate_status | `passed / blocked-input` |

Detached HEAD is acceptable only when the exact expected commit matches and the
named branch cannot be checked out because it is already occupied by another
worktree. In that case, record the branch occupancy reason and continue only
against the exact expected commit. Detached HEAD without an exact expected commit
match is `blocked-input`.

`ft_package_root` and `artifact_write_root` should normally be inside
`code_root`. If the FT package is outside the version-gated worktree, this is a
split-root run. Split-root is allowed only when the user/controller explicitly
approved that exact arrangement. Otherwise stop as `blocked-input`; do not
silently read requirements from one checkout and write artifacts after checking a
different checkout.

Nested FT packages are valid. For example, `fts/Partners/Partners-v1` is the FT
package root when that directory contains the selected package materials. In such
cases all practical artifacts, `workflow-state.yaml`, handoffs, summaries and
test cases must stay under `fts/Partners/Partners-v1`. Do not create
`fts/Partners/work/stage-handoffs/*` or other parent/domain-level workflow files
as a workaround for package discovery. If a validator or prompt cannot recognize
the nested package root, classify it as an agent-layer/root-detection defect and
fix the rule/tooling; do not mask the problem by adding a fake package index
outside `ft_package_root`.

Before matrix writing, matrix review or canonical TC writing, perform a physical
source package completeness preflight for the declared `ft_package_root`.
`AGENT-NOTES.md`, at least one main `source/*.docx`, mandatory
`source/*.xhtml`, and PDF cross-check `source/*.pdf` must exist in the package.
If any are missing, set `next_stage_transition = writer blocked`, classify the
validator/preflight issue as `next-stage-blocker`, and restore or relink the
source package before continuing. Do not treat this as a reason to create
handoff artifacts above `ft_package_root`.

When split-root is approved, the summary and final report must state it plainly
and must name both roots. The stage must not claim that version gate covers data
artifacts that live outside the version-gated root.

After every matrix review stage, the acting agent must stop the internal chain
long enough to produce a user-facing `practical-stage-summary.md` and include
the same facts in the final/user-visible report before sending the next prompt.
This is not a permission gate when no external decision is needed; it is a
mandatory transparency gate.

For a single-scope stage, place the summary in
`fts/<ft-slug>/work/practical/<scope-slug>/practical-stage-summary.md`.
For a multi-scope package stage, place the package-level summary in
`fts/<ft-slug>/work/practical-stage-summary.md`.

Create the file from
[practical-stage-summary-template.md](./practical-stage-summary-template.md).
Canonical path: `references/agent/practical-stage-summary-template.md`.
Machine enum fields must contain only enum values; explanatory prose belongs in
`next_safe_step`, scope `reason` or notes. Do not improvise new enum values.

The summary must be linked from `workflow-state.yaml` for every affected scope
through `latest_artifacts.practical_stage_summary` or an equivalent package-level
state/index pointer. A summary that is not linked is not a safe handoff for the
next stage.

The summary must list:

- accepted scopes that may proceed to canonical TC writing;
- blocked / `round-cap-reached` scopes;
- the concrete reason each scope is blocked or capped;
- whether TC can still be written with explicit statuses;
- the next safe step for each scope;
- a `Current stage actions` section that lists only actions performed in the
  current turn/stage;
- a `Prior state context` section for older history that explains current state
  but was not performed in this stage;
- `next_stage_transition`: exactly one of `writer allowed`,
  `writer conditional`, `writer blocked`, `tc-review allowed`,
  `tc-review conditional`, `tc-review blocked`, or `not-applicable`.

If a validator was run, add these fields:

| field | value |
| --- | --- |
| validator_errors_count | `<integer>` |
| validator_errors_classification | `none / next-stage-blocker / pre-existing-unrelated / validator-false-positive / mixed` |
| validator_errors_evidence | `<paths/finding ids or not-applicable>` |
| validator_warnings_count | `<integer>` |
| validator_warnings_classification | `none / blocking-for-scope / expected-pre-writer / nonblocking-info / mixed` |
| validator_warnings_evidence | `<paths/finding ids or not-applicable>` |
| validator_info_count | `<integer>` |
| validator_info_evidence | `<paths/finding ids or not-applicable>` |
| per_scope_next_stage_transitions | `yes / not-applicable` |
| production_tc_clean | `yes / no / mixed / not-applicable` |
| git_persistence | `tracked / ignored-by-git / mixed / not-applicable` |
| source_restore_provenance | `<source path/checkpoint used to restore package files, or not-applicable>` |
| source_restore_sha256 | `<SHA-256 bindings for restored files, or not-applicable>` |

When `validator_errors_count > 0`, the summary must not say unconditional
`writer allowed` or `tc-review allowed`. It must classify the errors and use a
conditional/blocked transition unless every error is explicitly proven
irrelevant or a validator false positive.

When `validator_warnings_count > 0`, classify warnings separately from errors:

- `blocking-for-scope`: blocks only the affected scope(s);
- `expected-pre-writer`: expected because TC artifacts do not exist yet, for
  example oracle-candidate obligations before writer;
- `nonblocking-info`: does not affect the next practical stage;
- `mixed`: more than one category is present.

A package-level conditional state must include per-scope transitions: which
scopes are `writer allowed`, `writer conditional`, `writer blocked`,
`tc-review allowed`, `tc-review conditional`, or `tc-review blocked`, and why.
Do not let a scope-local warning block unrelated accepted scopes. Do not write
package-level `writer allowed` or `tc-review allowed` when warnings are
`blocking-for-scope` or `mixed`.

`tc-review allowed` / `tc-review conditional` require clean production TC files:
`production_tc_clean = yes` for reviewed scopes. Findings
`test-case-split-artifact-duplicated-sections` and
`internal-diagnostic-section-in-production-testcases` are TC-review blockers;
move split-design sections to `work/test-design/<scope>/` before review.

When validator errors mention unresolved source/package artifacts, summary must
distinguish the cause explicitly:

- `physical-source-missing`: the files are absent under `ft_package_root`;
- `workflow-link-stale`: files exist, but `required_inputs` /
  `latest_artifacts` point to stale or wrong paths;
- `validator-root-selection-defect`: files and links are correct, but the
  validator resolved the wrong package root;
- `mixed`: more than one of the above is true.

Only `workflow-link-stale` may be repaired by editing links. Physical missing
source files must be restored. Root-selection defects must be fixed in the
agent-layer validator/policy, not by writing new parent-level handoff artifacts.
When files are restored or copied from another checkout, summary must record
`source_restore_provenance` and SHA-256 for the restored package files. Without
that provenance, the next stage cannot audit contamination risk.

After every repair, rerun the validator and refresh
`validator_errors_count`, `validator_warnings_count`, `validator_info_count` and
evidence ids from the latest report. Stale counts or stale finding ids block the
next practical stage.
Use
`python scripts/refresh_practical_stage_summary.py --root . --summary <path> --print-fields`
to compute the current validator counts/evidence, including info findings, and
`git_persistence` before updating the summary.
If changed FT/package artifacts are ignored by git, set
`git_persistence = ignored-by-git` or `mixed` and state that ordinary
commit/push will not persist those files. The stage/final response must also
say that persistence requires `git add -f <paths>` or an export/bundle.

`practical-stage-summary.md` must be linked from workflow-state files inside the
actual FT package root. An "equivalent package-level state/index pointer" is
allowed only inside that same `ft_package_root`; a parent folder such as
`fts/<domain>/work/stage-handoffs` is outside the package and is invalid unless
the user explicitly selected that parent folder as the FT package root.

For `round-cap-reached` after the bounded matrix repair/re-review, use this
practical default:

- if there is no source contradiction and the remaining issue is missing data,
  unknown UI reaction, unknown observability, or a future clarification that does
  not change the source obligation, write the TC baseline with explicit
  `candidate-ui-calibration`, `needs-test-data`, `blocked-observability` or
  `needs-future-clarification` statuses instead of blocking the whole scope;
- if source/support/mockup evidence contradicts itself, or the requirement
  cannot be represented without inventing a business rule, do not write TC for
  that obligation; keep the scope or obligation as `blocked-source` /
  `blocked-input` and state the exact contradictory source references.

The round-cap summary must be machine-checkable per scope: include
`source_contradiction: yes/no` and `tc_with_status_decision:
write-with-statuses / block-source-contradiction`. A generic "controller
decision required" is not a valid default unless the summary also names the
source contradiction or the exact status-based TC route.

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
   - Re-derive the coverage plan from FT/PDF/XHTML/support before trusting the
     writer matrix. Check visible field names, button/action labels, table rows,
     mockup figures and disputed source/support notes directly against the
     source package. A matrix cannot be accepted when reviewer only validates
     matrix formatting or traceability tokens.
   - Do not review canonical test cases in this pass. The expected current TC file
     state is "not created yet" or "old draft ignored".
  - Default behavior: run reviewer in a separate Codex task/session. If thread
    orchestration is available, hand off the reviewer prompt to that separate
    task/session. A sub-agent spawned inside the writer/controller turn does not
    count as a separate Codex task/session for independent sign-off. If separate
    thread orchestration is not available, stop after writer handoff and ask the
    user to run the reviewer prompt in a new session.
  - When the controller creates a separate reviewer Codex task/thread, set a
    short human-readable title such as `Partners-v1 TC review 9.1+9.3.1`;
    never leave the full reviewer prompt as the task title.
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
   - Also produce or update `practical-stage-summary.md` after the matrix review
     or matrix re-review. The summary must expose accepted scope, blocked /
     capped scope, reasons, whether TC can be written with explicit statuses, and
     the next safe step. It must include the root consistency fields,
     validator-error classification fields when validation was run, and
     `next_stage_transition`. It must be linked from affected `workflow-state.yaml`
     artifacts. This summary is required before the controller/user receives the
     next-stage prompt.

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
     input must exclude writer transcript and private reasoning. The controller
     must give the separate reviewer task/thread a concise title, not the full
     prompt body.
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

- Canonical TC writing is unlocked only by verdict `matrix-accepted` from
  `test-design-matrix-review.md`. If the first matrix review returns
  `matrix-changes-required`, the writer may perform exactly one bounded matrix
  repair, record it in `matrix-repair-summary.md`, but the repaired matrix must
  pass one matrix re-review before any canonical `TC-*` writing starts.
- `matrix-accepted` means every current-scope source obligation is represented
  as a planned TC, a class-specific deferred TC, or a narrow documented gap, and
  the reviewer has independently checked the plan against FT/PDF/XHTML/support
  rather than relying on writer's matrix alone;
- `matrix-changes-required` means writer can repair the matrix in one bounded
  revision and route the repaired matrix to one independent matrix re-review;
  canonical TC writing remains blocked until the verdict is `matrix-accepted`;
- `matrix-rejected` means the coverage plan is materially unreliable and TC
  review must stop until the matrix is rebuilt.
- Matrix review must block a plan that uses one representative invalid value as
  complete coverage for a source-backed restriction, omits applicable classes
  from `coverage-class-catalog.md`, creates standalone tests from glossary/status
  rows when later FT sections define real actions, or plans TC whose expected
  result has no observable UI/API/document artifact.

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
- before `review-ready`, writer must run an explicit runtime language/style
  self-check and validator pass; if any agent-process phrase remains in
  `Название`, `Цель`, `Предусловия`, `Тестовые данные`, `Шаги`,
  `Итоговый ожидаемый результат`, `Постусловия`, or
  `Требуется подтверждение`, the draft is blocked at writer gate;
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
- business states/statuses are separated from observable artifacts: keep values
  such as `Подтвержден` / `Скрыт` as setup/business state, but verify the
  displayed indicator, available action, row visibility, API field or generated
  output; do not expect status text unless source/support/UI evidence says it is
  visible;
- one test case has one main expected result;
- positive, negative and boundary coverage is driven by the FT text, dictionaries
  and support notes, not by one-code-one-case mechanics;
- if a dictionary or fixed list is referenced, the writer uses the full relevant
  list from support/source, not a few examples;
- if DaData or another integration is in scope, test cases use a fixed verified
  fixture with exact query/input and exact expected suggestion/result; do not ask
  the tester to call a live service during test execution.
- final TC source navigation stays slim: `Трассировка` carries codes/atoms/section,
  while `Источник / цитата требования` carries only a short real quote. Do not
  duplicate the same `ATOM-*`/`SRC-*`/section list again in `Ссылка на ФТ` or
  `Источник требования` unless those fields add nonduplicating navigation.

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
- a matrix review that does not show source-side checks for coverage, field/button
  labels, table rows, mockup figures and disputed notes that are relevant to the
  scope;
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
- TC whose expected result verifies only a business/internal state label without
  a concrete observable artifact, or assumes visible status text when source/UI
  evidence only supports an indicator/action/list visibility/API field.

The reviewer should not require heavy process artifacts when the matrix,
scope brief and canonical test cases are sufficient to prove coverage.

## Reviewer independence evidence

Create `review-independence.md` in the practical scope folder.

Minimum fields:

| field | value |
| --- | --- |
| reviewer_task_or_session | `<actual Codex thread/session id>` |
| reviewer_execution_surface | `codex-task/codex-thread` |
| reviewer_thread_url_or_id | `<durable Codex task/thread id or URL>` |
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
- `reviewer_execution_surface` must be `codex-task` or `codex-thread` for
  independent sign-off. Values such as `sub-agent`, `same-session`,
  `in-process`, `local-helper` or `not-available` are allowed only for
  `reviewed-not-independent`.
- `reviewer_thread_url_or_id` must contain the same durable Codex thread/task id
  or a user-visible Codex task URL. It exists to make the evidence auditable from
  the Codex sidebar/task list, not merely from an internal agent transcript.
- A sub-agent, local helper or same-session pass may be used only as auxiliary
  analysis. It cannot be the final reviewer verdict for matrix acceptance, TC
  review acceptance or independent release.
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
