# Regression eval: writer must preserve ui-main-info revalidation lessons

## Scenario

This eval checks `ft-test-case-writer` behavior for the `2.3-ui-main-info` scope after a writer-from-scratch regression was found.

The writer is asked to create or revise a baseline for `fts/ft-2-OF/test-cases/2.3-ui-main-info.md` using the FT package `fts/ft-2-OF`. A same-scope revalidated baseline exists in `fts/ft-2-obshchaya-funkcionalnost/test-cases/ui-main-info.md`, and the writer-eval findings in the current package show that a simplified from-scratch baseline incorrectly promoted internal/integration assertions to `covered`.

The eval target is not visual polish or total TC count. It is whether the writer preserves traceability discipline:

- no competing simplified baseline that ignores a more complete same-scope baseline/revalidation result;
- no `covered` status for internal/integration behavior without an observable artifact;
- no multi-property `ATOM-*` records that hide partially unobservable requirements.

## Input artifacts

- `fts/ft-2-OF/source/ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.docx`
- `fts/ft-2-OF/AGENT-NOTES.md`
- `fts/ft-2-OF/work/stage-handoffs/04-ui-main-info/scope-contract.md`
- `fts/ft-2-OF/work/stage-handoffs/04-ui-main-info/scope-coverage-gaps.md`
- `fts/ft-2-OF/work/review-loops/2.3-ui-main-info-writer-eval/round-1-findings.md`
- comparison baseline: `fts/ft-2-obshchaya-funkcionalnost/test-cases/ui-main-info.md`
- current flawed writer output under review: `fts/ft-2-OF/test-cases/2.3-ui-main-info.md`

## Expected failures / must-catch rules

### Rule 1: Existing baseline conflict rule

The writer must detect that a same-scope revalidated baseline exists and must not create a competing simplified baseline that contradicts it without an explicit resolving source.

Must catch:

- prior baseline treats `kladr`, saved `esiaUserId`, `CorrelationId`, Connect/RabbitMQ results, no further CP calls, and retry async behavior as `unclear` / `GAP-*`;
- new writer output marks the same classes of assertions as `covered`;
- no new source is cited that resolves the older limitation.

### Rule 2: Revalidation lesson carry-over

The writer must carry over the regression lesson from `round-1-findings.md`:

> Writer did not carry over revalidation lessons from `ui-main-info`: do not count `kladr`, `esiaUserId`, `CorrelationId`, RabbitMQ/API calls, saved attributes, async waiting, or internal routing as covered unless the scope defines a confirmed observable artifact for pass/fail verification.

Must catch:

- fake coverage for `ATOM-024`, `ATOM-039`, `ATOM-040`, `ATOM-041`, `ATOM-042` or equivalent internal/integration atoms;
- TC steps such as `проверить модель данных`, `проверить вызов`, `проверить сохранение`, `проверить RabbitMQ` without a named artifact source;
- coverage maps that report `Uncovered atoms: none` while internal/integration artifact gaps remain unresolved.

### Rule 3: No internal/integration coverage without observable artifact

The writer must split observable UI initiation from internal results.

Allowed as covered only when directly observable or backed by a named artifact:

- opening/using the UI action `Проверить`, if the expected result is limited to user-facing initiation or observable state;
- DaData address selection and visible field decomposition, if verified in the UI.

Must remain `gap` / `unclear` unless an artifact is defined:

- `kladr` in data model;
- saved `esiaUserId`;
- saved or new `CorrelationId`;
- actual-version call result;
- `POST /api/v3/persons/check-consent` and `POST /public/v2/messages/send` verification;
- RabbitMQ event waiting/restart;
- absence of further CP calls;
- routing to scoring without CP data if no UI/log/API artifact is named.

### Rule 4: Strict atom atomicity

The writer must not create multi-property atoms that allow a single `covered` flag to hide unverified obligations.

Must catch ATOM rows that combine independent properties such as:

- visibility + mandatory + editability + numeric format + min/max boundary;
- DaData UI decomposition + internal `kladr` persistence;
- status branch + API call + saved attribute + async event + downstream routing.

Each independent assertion must be a separate `ATOM-*` with its own `covered | gap | unclear` status.

### Rule 5: No automation-ready sign-off laundering

If UI runtime is unavailable, the writer or UI-prep step may create an initial `automation-ready` artifact only under the lifecycle rules, but this must not be used as evidence that the baseline is signed off.

Must catch:

- `blocked-ui-unavailable` status assigned without access/runtime blocker evidence;
- automation-ready existence used as proof of baseline coverage;
- `confirmed` or `mismatch-ft-ui` statuses without normal UI path evidence.

## Pass criteria

The writer output passes this eval only if all of the following are true:

- It explicitly uses the same-scope revalidated baseline or writer-eval findings as regression input.
- It does not create a simplified competing baseline that contradicts known `gap` / `unclear` decisions without a cited resolving source.
- Internal/integration assertions without a confirmed observable artifact are marked `gap` / `unclear`, not `covered`.
- `Test-design Applicability Matrix` still marks integration/async/persistence dimensions as applicable when present in FT, but links unobservable behavior to `GAP-*` rather than fake `TC-*` coverage.
- `ATOM-*` rows are strictly atomic: no row mixes independent UI, validation, persistence, API, async, or routing obligations.
- Test cases have one primary expected result; observable UI initiation is not bundled with unobservable internal outcomes.
- Writer self-check explicitly lists baseline/revalidation conflicts and internal/integration atoms without observable artifact, or states that none remain with evidence.

## Fail criteria

Any one of the following is a regression failure:

- Writer marks `kladr`, saved `esiaUserId`, `CorrelationId`, API calls, RabbitMQ waiting/restart, saved attributes, or internal routing as `covered` without a named artifact source.
- Writer reports `Uncovered atoms: none` while known internal/integration artifact gaps remain.
- Writer ignores `fts/ft-2-obshchaya-funkcionalnost/test-cases/ui-main-info.md` or `round-1-findings.md` and creates a shorter/simplified `ui-main-info` baseline with conflicting semantics.
- Writer creates multi-property `ATOM-*` records that combine observable UI behavior with persistence/API/async behavior under one `coverage_status`.
- Writer creates test cases whose pass/fail depends on vague actions like `проверить бэк`, `проверить модель данных`, `проверить вызов`, or `проверить очередь` without specifying the artifact to inspect.
- Writer treats `automation-ready` with `blocked-ui-unavailable` as baseline sign-off evidence.

## Regression lesson

Writer must carry over revalidation lessons from `ui-main-info`: do not count `kladr`, `esiaUserId`, `CorrelationId`, RabbitMQ/API calls, saved attributes, async waiting, no-further-call behavior, or internal routing as covered unless the scope defines a confirmed observable artifact for pass/fail verification. When no artifact exists, preserve the requirement as `gap` / `unclear` and keep it visible in the ledger, applicability matrix, risk map, coverage map and writer self-check.

Exception to preserve: source-backed save/no-save behavior for fields visible in the UI is not an internal-only artifact when the same object/section can be reopened in scope. In that case the displayed value after reopening is the observable artifact; routing the whole branch to `GAP-*` is a false gap.
