# Writer Runtime Contract

This reference defines the compact runtime contract for `ft-test-case-writer`. The resolver uses it as default writer context. Full formats and deep rules remain in linked references and load conditionally.

## When to Use

Use this contract for:

- `writer.practical_v0_8` matrix-only and post-matrix TC drafting;
- `writer.initial_draft.simple`;
- `writer.initial_draft.ui`, when the scope is not table-heavy;
- `writer.revision_from_findings`;
- preflight that decides whether writer can start without routing back to locator/scope.

If the scope contains field/action tables, row-level parity, package-heavy decomposition, or validator findings on design artifacts, also read `writer-output-format.md` and table/deep references from the manifest.

## Required Inputs

Writer may start only when these are already defined:

- FT package;
- confirmed scope and its boundaries;
- main FT source;
- `scope-contract.md`;
- `scope-coverage-gaps.md`;
- `workflow-state.yaml` or an equivalent handoff with `next_skill = ft-test-case-writer`;
- package-specific `AGENT-NOTES.md`, when present in the FT package root.

Conditional inputs:

- `source-parity-check.md` is mandatory when the main FT is available as DOCX and PDF;
- `source-row-inventory.md` is mandatory for row-level/table parity;
- `mockup-visual-inventory.md` is mandatory for a UI scope with mockup/screen image;
- `negative-oracle-inventory.md` / `requiredness-oracle-inventory.md` are mandatory when the scope handoff contains validation/format restrictions or requiredness obligations;
- accepted `test-design-matrix-review.md` and separate-session `review-independence.md` are mandatory before `practical_v0_8` canonical TC drafting, unless the bounded matrix review cap was reached and `practical-stage-summary.md` explicitly allows status-marked TC writing because the source obligation is clear and only data/UI/observability remains unresolved;
- structured findings and traceability matrix are mandatory for `revision_from_findings` when the reviewer provided them.

## Hard Stops

Do not set `stage_status: ready-for-review` when:

- FT package or scope is not selected;
- a mandatory handoff input is missing;
- blocking `coverage gaps` have no accepted-risk decision;
- expected behavior cannot be derived from the FT or allowed materials, and the obligation cannot honestly become a `ui-calibration-required` candidate TC;
- writer found a new gap that blocks an executable result;
- the simple runtime context is insufficient and table/UI/revision/validator deep context from the manifest is required;
- technical fallback produced a compact draft, loss of detail, one-shot giant write, or unchecked mojibake output.

In these cases, use `stage_status: blocked-input`, fill `blocking_reasons`, and route the task to the right skill or to the user through a handoff prompt.

## Runtime Workflow

1. State the selected writer scenario and resolved instruction context.
2. Read required inputs and record missing inputs before generating matrix rows or `TC-*`.
3. Confirm scope boundaries; do not expand scope on your own.
4. Decompose requirements into coverage obligations, atomic statements, or explicit gaps.
5. Build coverage plan and metrics by `coverage-runtime-checklist.md`; use `Coverage Obligation Table` for mandatory classes.
6. In `practical_v0_8_matrix`, write only `test-design-matrix.md` and a matrix-review prompt; do not create or update `TC-*`.
6.1. After matrix review or matrix re-review, require `practical-stage-summary.md` with accepted scopes, blocked/round-cap scopes, reasons, whether TC may be written with explicit statuses, and next safe step before continuing.
6.2. In `practical_v0_8` canonical TC drafting, first verify accepted matrix review or a bounded round-cap practical-policy decision in `practical-stage-summary.md`, then write `TC-*` by `test-case-runtime-format.md`.
6a. Runtime prose must be human-executable: do not put `subject:<hash>`,
`OBL-*`, `ATOM-*`, `ASSERT-*` or `SRC-*` in `Название` or user-action steps.
Keep those identifiers only in traceability/design artifacts.
6b. For `oracle_status = ui-calibration-required`, create a candidate TC by `negative-ui-calibration-policy.md`; do not replace it with a generic `GAP-*` and do not invent an exact UI reaction without a source-backed oracle.
6c. In each `TC-*`, write `Предусловия` as reproducible setup: numbered action setup steps, fixture/API setup, or reusable setup profile. Do not leave magic/passive UI states without the action that creates them. `Дождаться` / `Убедиться` are allowed only after a setup action.
6c.1. Production files under `fts/**/test-cases/*.md` are self-contained runtime artifacts: no setup profile references, stand/environment wording, or package-name leakage; dynamically created fields must include the reveal/create action in preconditions; for contact-person fields, use `Добавить контактное лицо`.
6b.2. Preserve the complete source-backed scope entry path in every case. If the seed/context contains both a parent card/form opening action and a block navigation action, each TC must keep both in the same order; `Перейти к блоку ...` alone is not equivalent to `Открыть карточку ...` + `Перейти к блоку ...`.
6b.3. For positive allowed-value or boundary checks, do not use negated rejection/blocking wording such as `не отклоняется` or `не блокируется` as the oracle. State the concrete observable positive artifact instead, for example that the exact entered value is displayed in the field; if no source-bound positive artifact exists, return/keep a calibration candidate instead of inventing acceptance semantics.
6c. For a source-backed input restriction, always decompose allowed classes and invalid classes; write positive TC for allowed representative values and negative/candidate-negative TC for invalid representative values. A candidate negative TC does not replace a positive allowed-class TC.
6d. If one TC references more than two independent source-backed obligations, split it unless one visible source-backed workflow justifies grouping. Grouped TC must include `**Сценарное обоснование:**` and must not hide missing atomic TC/GAP coverage.
6e. For similar fields/classes with shared restrictions, representative or pairwise coverage is allowed only when the artifact states selected combinations, omitted combinations, and residual risk. Otherwise write the missing TC/GAP items.
7. Check traceability: every `TC-*` links to `ATOM-*` / requirement code / source reference.
8. Run writer self-check and applicable quality gates.
9. Update `workflow-state.yaml` and create `prompt.matrix-to-reviewer.md`, `prompt.tc-to-reviewer.md` or legacy `prompt.writer-to-reviewer.round-N.md` only when the artifact is ready for the next review gate.

## Output Contract

Default writer output:

- for `practical_v0_8_matrix`: `test-design-matrix.md`, short coverage summary, matrix writer self-check and `prompt.matrix-to-reviewer.md`;
- for `practical_v0_8` after `matrix-accepted` and for legacy TC drafting: canonical test-case file in `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`;
- short coverage summary;
- explicit `Coverage Gaps`, when `GAP-*` exists;
- writer self-check;
- updated `workflow-state.yaml`;
- next-step prompt for reviewer.

For table-heavy/package-based scope, use the full output contract from `writer-output-format.md`: split artifacts, Source Row Inventory, normalization, TDDT, Coverage Obligation Table, Package Test Design Plan, coverage metrics, Fixture Catalog when applicable, Risk / Priority Map, Test Design Review, Writer Quality Gate, and coverage maps.

## Logging

For writer-pass, save session log and decision log by canonical formats. Runtime contract does not replace:

- `workflow-state-format.md`;
- `session-log-format.md`;
- `agent-decision-log-format.md`;
- `next-step-prompt-format.md`.

These references load as deep/process context when corresponding artifacts must be created or checked in detail.

## Deep References

- Full writer output: `writer-output-format.md`
- Writer Quality Gate details: `writer-quality-gate-format.md`
- Coverage obligations: `references/agent/coverage-obligation-table-format.md`
- Negative UI calibration: `references/agent/negative-ui-calibration-policy.md`
- Coverage metrics: `references/agent/test-design-coverage-metrics-format.md`
- Fixture catalog: `references/agent/fixture-catalog-format.md`
- Risk / Priority Map: `references/agent/risk-priority-map-format.md`
- Test-case full format: `references/qa/test-case-format.md`
- Coverage deep checklist: `references/qa/coverage-checklist.md`
- Review findings/writer response: `references/qa/review-findings-format.md`
- Traceability matrix: `references/qa/traceability-matrix-format.md`
