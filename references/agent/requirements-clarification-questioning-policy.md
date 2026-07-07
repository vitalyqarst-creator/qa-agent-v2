# Requirements Clarification Questioning Policy

This policy defines clarification questions for requirement-based testing. It complements `scope-coverage-gaps.md` and `scope-clarification-requests.md`; it does not replace the source FT.

## Core Rule

A question is valid only when it is anchored to a concrete source statement and explains which test-design decision is blocked or limited. Do not ask broad questions such as "How should this work?" when the missing decision can be stated precisely.

Every analyst-facing question includes:

- source anchor: section, requirement code, table/row, field/condition, quote, `ATOM-*` or explicit extraction limitation;
- affected test-design dimension from `review-findings-format.md`;
- concrete missing oracle, condition, actor, value set, transition, validation, calculation, integration behavior, persistence, timing, error or source priority;
- answer options when the FT implies a small finite set of plausible meanings;
- impact if unanswered.

## Controlled Vocabularies

`question_type`:

`missing-behavior | ambiguous-behavior | conflicting-sources | missing-trigger | missing-condition | missing-actor-role | missing-permission-rule | missing-state-transition | missing-validation-rule | missing-negative-behavior | missing-boundary | missing-equivalence-class | missing-allowed-values | missing-dictionary-source | missing-display-format | missing-error-message | missing-timing-rule | missing-persistence-rule | missing-reopen-behavior | missing-audit-log-rule | missing-integration-behavior | missing-async-retry-behavior | missing-generated-document-rule | missing-calculation-rule | missing-rounding-rule | missing-sort-filter-rule | missing-priority-between-rules | missing-cross-ft-dependency | mockup-vs-ft-conflict | support-vs-main-ft-conflict | xhtml-vs-docx-conflict | pdf-vs-docx-conflict | source-extraction-limitation | other`

`priority`:

`P0-blocker | P1-high | P2-medium | P3-low`

`blocking_level`:

`blocks-scope-confirmation | blocks-writer-start | blocks-ready-for-review | blocks-sign-off | allows-limited-coverage | non-blocking`

`requested_from`:

`business-analyst | product-owner | system-analyst | developer | qa-lead | unknown`

`answer_usage_rule`:

`source-update-required | analyst-confirmation-enough | product-confirmation-required | working-assumption-only | accepted-risk-required | do-not-use-until-documented`

## Blocking Rules

Do not hand off to writer when an unanswered `P0-blocker` or `P1-high` question has `blocking_level = blocks-*` and affects expected result, validation, state transition, dictionary completeness, integration behavior, source priority or source extraction completeness.

An unanswered blocking question may proceed only with an explicit accepted risk in `workflow-state.yaml` that names the same `GAP-*`, owner/role, rationale and revisit condition.

`blocking_level` values that start with `blocks-` require `blocking = yes` in `scope-clarification-requests.md`.

## Answer Usage

- `source-update-required`: do not use until the FT or approved support source is updated.
- `analyst-confirmation-enough`: writer may use and trace it to `scope-clarification-requests.md`.
- `product-confirmation-required`: do not treat analyst-only confirmation as enough.
- `working-assumption-only`: may guide limited draft structure, but must not become a final expected result.
- `accepted-risk-required`: proceed only with a qualified accepted risk.
- `do-not-use-until-documented`: preserve the gap; do not cover it with `TC-*`.

## Reviewer Rule

Reviewer must raise category `clarification-question-quality` when a gap question lacks source anchor, affected dimension, concrete missing decision, impact if unanswered, answer options for finite-choice ambiguity, valid classification or correct blocking/answer-usage rule.

## Writer Rule

Writer must not close an unanswered `P0-blocker` or `P1-high` question with a test case. Writer may cover the safe source-backed part, but must preserve the open `GAP-*`. Analyst-confirmed or product-confirmed answers used in a TC must be traceable. A working assumption cannot become an expected result without accepted risk and residual gap disclosure.
