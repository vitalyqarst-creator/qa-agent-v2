---
name: ft-test-case-reviewer
description: Делает review существующих тест-кейсов по подтвержденному FT-пакету и scope. Работает как umbrella-skill с режимами `full`, `traceability`, `structure`, `test-design`, возвращает structured findings artifact и при необходимости отдельную traceability matrix.
---

# FT Test Case Reviewer

Используй этот skill для review уже существующих тест-кейсов. Skill не пишет и не исправляет тест-кейсы сам: он только анализирует набор и возвращает findings.

## Когда использовать

- нужно проверить готовый набор тест-кейсов;
- нужно сверить кейсы с FT-пакетом и выбранным scope;
- нужно найти пробелы покрытия по утверждениям ФТ;
- нужно проверить единый формат и организацию набора;
- нужно проверить качество test design;
- нужно подготовить замечания для writer workflow.

## Reviewer roles и режимы review

Минимальный полезный split reviewer-а состоит из двух независимых ролей:

- `traceability reviewer` — отвечает только за полноту и стабильность трассировки: ФТ/code/source -> `ATOM-*` / traceability matrix -> `TC-*` или `GAP-*` / `unclear`.
- `test-design/TC-quality reviewer` — отвечает за смысловую достаточность test-design и качество самих `TC-*`: атомарность, исполнимость, наблюдаемость expected results, матрицы покрытия, gaps и приоритеты.

Эти роли могут выполняться одним skill-ом, но reviewer обязан мыслить их как разные passes. Test-design не доказывает traceability, а traceability не доказывает покрытие риска.

## Режимы review

- `practical_v0_8` — default practical review route for ordinary test-case
  writing. It has two gates by default:
  1) `matrix_review` checks `test-design-matrix.md` before any canonical TC is
     written;
  2) `tc_review` checks canonical test cases only after the matrix was accepted.
  Each gate runs from a separate Codex task/session by default and produces
  review evidence. The controller/writer session must launch that task through
  Codex thread tools (`tool_search` discovery if needed, then `list_projects` /
  `create_thread`) and write the returned durable thread id into a
  controller-owned `review-dispatch.json`. A
  sub-agent inside the writer/controller turn is not a separate Codex
  task/session and cannot produce independent sign-off. Before the controller
  creates that task, it must pass `scripts/practical_review_preflight.py`; the
  reviewer repeats it with `--verify-receipt` before it reads review inputs. If
  either preflight is blocked, create no review artifact. If thread tools are
  genuinely unavailable, stop as `blocked-reviewer-session-tool-unavailable`
  instead of issuing a same-session route verdict. It must not require source assertion receipts, semantic
  bridge, immutable runner attempts, benchmark artifacts, separate structure
  preflight, separate final-format review or semantic regression unless the user
  explicitly selected those routes. If matrix review returns
  `matrix-changes-required`, exactly one bounded matrix repair and one matrix re-review
  are allowed before TC writing. If the first TC review returns
  `tc-changes-required`, exactly one bounded writer revision and one final independent TC review in a separate session are allowed. It must not request extra matrix
  reviews, a third TC review or another automatic repair loop; remaining
  execution uncertainty is represented by accurate TC statuses.
- `full` — канонический режим по умолчанию для direct review. Выполняет `traceability`, затем `structure`, затем `test-design`; возвращает findings и traceability matrix при необходимости. Direct `full` не заменяет session-based sign-off: для `signed-off` используй `ft-test-case-iteration`.
- `traceability` — строит traceability matrix по атомарным утверждениям ФТ и проверяет, что каждое утверждение покрыто тест-кейсом или зафиксировано как `gap` / `unclear`.
- `structure` — проверяет формат тест-кейса, группировку набора, сквозную нумерацию `TC-*`, порядок позитивных и негативных кейсов, наличие базовых проверок по полю, если такие свойства явно описаны в ФТ.
- `test-design` — проверяет полноту позитивных и негативных сценариев, граничные значения, классы эквивалентности, зависимости и комбинации условий, а также неподтвержденные expected results в пределах подтвержденного scope; severity назначается по `test-design-review-rubric.md`.

For direct and explicit session-based modes, read
[../../references/agent/reviewer-general-workflow.md](../../references/agent/reviewer-general-workflow.md).
They are not part of practical v0.8.

### `practical_v0_8` contract

Use
[../../references/agent/practical-test-case-route-v0.8.md](../../references/agent/practical-test-case-route-v0.8.md)
as the controlling route.

Для `practical_v0_8` не создавай `.xlsx`-дубль по умолчанию: XLSX companion
нужен только если пользователь явно запросил XLSX export.

Review in two practical gates:

0. Matrix review gate: treat `test-design-matrix.md` as writer output, not source
   of truth. Re-derive coverage from FT DOCX/PDF/XHTML, support, dictionaries and
   mockups; return `matrix-changes-required` or `matrix-rejected` if dimensions,
   classes or source links are missing or misleading.
   This pass must run before canonical test-case writing. If current input
   already contains a newly written canonical TC file but no accepted matrix
   review, do not sign off the TC file; mark it as an old/unaccepted draft and
   complete `matrix_review` first.
1. TC review gate: after `matrix-accepted`, every source-backed obligation in the scope maps to a TC or
   to an explicit allowed deferred status. `Review Focus` is a priority list,
   not a scope boundary: a normal or final TC review must inspect the full
   current canonical suite, re-derive coverage from FT/PDF/XHTML/support and
   check that `ready` cases have no unresolved confirmation, fixture, data,
   access or observability dependency.
2. Test design: positive, negative, boundary, dictionary, dependency,
   repeatable-block and independent-creation classes from
   [../../references/qa/coverage-class-catalog.md](../../references/qa/coverage-class-catalog.md)
   are present when the FT requires them; a single invalid representative does
   not cover multiple independently derivable classes; requiredness checks are
   split by input mechanism instead of hidden in one generic "all required
   fields are empty" test case. For status/lifecycle rows, verify `Объект и
   место выполнения`: an accepted plan or TC has one concrete object, one
   screen/card/list/block and one observed user action. Reject generic
   availability/use TC that mix parent and child objects; the status row is
   supporting traceability when a later FT section owns the actual action.
   For `R-CREATE-FORM-ISOLATION`, when `Создать` / `Добавить` opens a form for a
   new independent object, reject the matrix or TC if it omits the check that a
   form for object B is not prefilled with distinctive values entered for object
   A. Do not flag
   source-defined defaults, context/inherited values, clone/import behavior or
   documented draft restoration as leakage.
   Reject a duplicate-prevention TC that expects a positive save, a downstream
   rule turned into a local save rejection, an optional field expected to have a
   required marker/save block, and `non-atomic-parameterization` across UI
   levels.
3. Runtime executability: steps are user actions/checks; expected results are
   observable or marked `blocked-observability`.
4. Language and wording: runtime fields are Russian; English is allowed only for
   approved metadata enum values such as `Positive`, `Negative`, `High`,
   `Medium`, `Low`; no agent-process phrases leak into test cases; practical
   `test-design-matrix.md` uses Russian visible headers and human-readable text.
5. Source precedence: FT text wins over mockups for business rules; mockups may
   refine visible labels and navigation.
6. Data readiness: concrete values are used where available; otherwise the case
   has `needs-test-data` with a clear fixture need.

For `matrix_review`, return `test-design-matrix-review.md` with exactly one
verdict: `matrix-accepted`, `matrix-changes-required`, or `matrix-rejected`. Do
not produce final TC sign-off from this pass.

The controller owns `workflow-state.yaml` and `practical-stage-summary.md`. An
independent reviewer writes only its review artifacts
(`test-design-matrix-review.md` or `review-findings.md`,
`review-independence.md`, and reviewer audit log/decision log). Do not update
controller aliases or the stage summary from the reviewer task: that creates
stale-alias repair loops. After reviewer return, the controller performs one
deterministic state/summary update only after
`scripts/practical_review_finalization_guard.py` accepts the separate review
artifacts and confirms that the reviewer did not mutate controller-owned state;
the controller-only details are in
[../../references/agent/practical-review-finalization-format.md](../../references/agent/practical-review-finalization-format.md).
If a delegated reviewer prompt asks you to update any of those controller-owned
files, treat that instruction as a contract conflict: stop before writing an
artifact, report `blocked-contract`, and request a corrected reviewer task
prompt. Do not resolve the conflict by changing controller state yourself.

Reviewer launch preflight is two commands, not one combined command: the
controller creates `review-launch-preflight.json` with `--output`; the separate
reviewer task verifies that unchanged receipt with `--verify-receipt`. Do not
rerun entry preflight after final sign-off, because terminal state naturally has
no next reviewer route.

After every matrix review or matrix re-review, produce/update
`practical-stage-summary.md` before the controller/user gets the next-stage
prompt. It must list accepted scopes, blocked/`round-cap-reached` scopes,
concrete blocker reasons, whether TC can be written with explicit statuses, and
the next safe step. It must also record `code_root`, `ft_package_root`,
`artifact_write_root`, `root_split_allowed`, `next_stage_transition`,
`per_scope_next_stage_transitions` for package-level `writer conditional` or
`tc-review conditional`,
`production_tc_clean`, `validator_errors_classification` and
`validator_warnings_classification` when validation was run, plus
`source_restore_provenance`, `source_restore_sha256` and `git_persistence`.
After repair/re-review, rerun validation and refresh the declared
validator counts/evidence from the latest report before handing off. Use
`python scripts/refresh_practical_stage_summary.py --root . --summary <path> --scope-id <two-digit scope id> --print-fields`
to compute those fields and keep summary enum fields enum-only.
When changed FT/package artifacts are git-ignored, record that explicitly in
`git_persistence` because ordinary commit/push will not persist them; the
stage/final response must name `git add -f <paths>` or export/bundle as the
persistence path.
Link the summary from every affected `workflow-state.yaml` or
package-level state/index inside the actual FT package root so the next stage
cannot miss it. If the bounded matrix repair/re-review cap is
reached, do not treat that as automatic failure to write TC: when the source
obligation is clear and only test data, UI reaction, observability or future
calibration is missing, the next safe step is TC writing with
`candidate-ui-calibration`, `needs-test-data`, `blocked-observability` or
`needs-future-clarification`. Record `source_contradiction: yes/no` per
round-cap scope. Block TC writing only for source contradiction
(`source_contradiction: yes`) or obligations that cannot be represented without
inventing behavior.

For independent `tc_review`, return `review-findings.md` and verify that
`test-design-matrix-review.md` has verdict `matrix-accepted` before judging TC
coverage. If an accepted matrix review is absent, block TC review and route back
to matrix review.

`review-findings.md` is release-grade review evidence and is allowed only when
the reviewer ran in a separate Codex task/thread. If review is performed as a
sub-agent, same-session pass, local helper or any other non-independent advisory
analysis, write `advisory-review-findings.md` instead. Advisory findings cannot
authorize `ready-for-writer-revision`, matrix/TC acceptance, sign-off or release
unless the workflow explicitly records
`controller_authorized_advisory_revision: yes`.

Before accepting a TC review handoff, verify `production_tc_clean = yes` for the
reviewed scopes. Findings `test-case-split-artifact-duplicated-sections` and
`internal-diagnostic-section-in-production-testcases` block TC review: production
`test-cases/*.md` must not contain embedded `Coverage Gaps`, `Source Row
Inventory`, `Package Test Design Plan`, `Writer Self-Check`, `Writer Quality
Gate` or other split-design sections.

Also verify `review-independence.md` for each gate. If the reviewer was not run
in a separate Codex task/session or received writer transcript/private reasoning,
review may continue but the matrix/suite must be labeled `reviewed-not-independent`,
not independently signed off.
For an independent verdict, `review-independence.md` must record
`reviewer_dispatch_receipt` created by the controller after `create_thread`.
The controller-owned receipt, rather than reviewer-authored fields, proves the
actual Codex task/thread id and execution surface. Role aliases, a sub-agent,
same-session, `in-process` or `local-helper` mean `reviewed-not-independent`.
A sub-agent/local-helper/same-session pass can
support analysis, but it cannot be the final independent reviewer verdict for
matrix acceptance, TC review acceptance, writer-revision routing or practical
release.
For `practical_v0_8`, `review-independence.md` must also include `review_mode`
and `review_round` matching the current review artifact. Matrix-review
independence does not prove TC-review independence.

Return independent `review-findings.md` with `blocking`, `nonblocking`,
`needs-ui-calibration` and `needs-test-data` findings. Do not block release only
because some cases legitimately remain `candidate-ui-calibration`,
`blocked-observability`, `needs-test-data` or `needs-future-clarification`.
After the writer applies the single bounded revision, require one final
independent full-scope reviewer pass before acceptance or release. Do not ask
for a third TC review or another automatic writer repair unless a validator
contract failure prevents publication or the user explicitly requests another
review round.
Block production sign-off when user-facing TC headings contain English process
headings such as `Summary` / `Coverage Summary` or unnatural title casing such
as `Сведения О Наборе`; require Russian sentence-style headings like
`Сведения о наборе`, `Границы покрытия`, `Сводка`.

For explicit `source_assertion_review` or legacy `scope_gap_review`, read
[../../references/agent/reviewer-specialized-review-contracts.md](../../references/agent/reviewer-specialized-review-contracts.md).
These modes are not part of practical route v0.8.

## Входы

For direct and explicit session-based modes, the required inputs are defined in
`reviewer-general-workflow.md`. Practical v0.8 reads only the confirmed scope,
current source package, matrix/TC artifact and selected review receipt inputs.

## Выходы

The reviewer creates only the selected review artifact, independence receipt
and its audit log/decision log. Output placement and required fields are defined
in `reviewer-general-workflow.md` and `review-findings-format.md`.

## Workflow

For inputs, outputs, direct-review workflow and canonical references, read
[../../references/agent/reviewer-general-workflow.md](../../references/agent/reviewer-general-workflow.md)
when the selected mode is not `practical_v0_8`.

## Ограничения

- Не используй этот skill для написания новых тест-кейсов вместо writer workflow.
- Не меняй FT-пакет и scope по ходу review, если это явно не требуется отдельной задачей.
- Не исправляй тест-кейсы сам. Возвращай remediation как findings artifact, human summary и traceability matrix при необходимости.
- Не расширяй scope на основании найденных пробелов. Out-of-scope замечания фиксируй как findings категории `scope`.
- Не дублируй общие правила из канонических references.
