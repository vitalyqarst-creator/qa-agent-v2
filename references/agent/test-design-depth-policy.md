# Test Design Depth Policy

Purpose: choose enough test-design depth for a confirmed FT scope without dropping source-backed coverage or adding low-value process artifacts.

## Profiles

| coverage_depth_profile | artifact_mode | Use when | Required shape |
| --- | --- | --- | --- |
| `simple` | `compact` | small homogeneous low-risk scope; no tables/lists/dictionaries, lifecycle/status rules, integrations/API/async/persistence, generated documents, complex dependencies, blocking gaps, high-risk dimensions or complex equivalence/boundary rules | scope contract, atomic ledger, compact Package Test Design Plan, canonical TC file, compact Writer Quality Gate |
| `standard` | `standard` | normal functional scope with ordinary validation/branching and no deep trigger | package plan plus applicable source/table/design artifacts; compact embedded review is allowed for moderate low-risk scope |
| `deep` | `full` | table/list-heavy scope, nested XHTML lists, dictionaries/repeated rows, money/security/roles, irreversible lifecycle/status, generated documents, integrations/API/async/persistence, complex dependencies, 3+ combinatorial factors, high-risk atoms, many blocking/unclear gaps or reviewer under-coverage history | full source/design artifact chain, metrics when applicable, risk map when high-risk, Test Design Review and TC Set Optimization Review |

Start from `standard`. Downgrade to `simple` only when Scope Complexity Assessment explicitly shows no risk/table/list/dependency signals. Escalate to `deep` as soon as one deep trigger is present. If evidence is unclear, keep `standard` and record the uncertainty as risk/gap.

## Hard Rules

- `table_list_heavy = yes` means profile cannot be `simple`.
- Non-empty `high_risk_dimensions` means profile cannot be `simple`.
- `deep` requires source/risk rationale in `risk_escalation_reasons`.
- Compact artifacts never remove traceability: every atom maps to `TC-*`, `GAP-*` or `unclear`.
- Full artifact chain is required for `deep`, table/list-heavy, high-risk, generated document, integration/API/async/persistence, lifecycle/status, complex dependency or combinatorial scopes.

## TC Set Optimization

`TC Set Optimization Review` is required for:

- every `deep` scope;
- `standard` when TC count >= 15, Package Test Design Plan rows >= 20, high-risk dimensions exist, or writer/reviewer marks over-testing risk.

It checks both under-coverage and over-testing before sign-off. It must not remove source-backed obligations; unresolved source-backed checks become `GAP-*`, accepted risk or labeled `deep` coverage.

## Smells

Under-testing: missing source rows, dictionary values, inverse branch, high-risk TC/GAP, concrete boundary/class, unsupported gap promotion, or one broad scenario replacing independent assertions.

Over-testing: duplicate TC with same source/input/oracle, low-value non-source-backed negatives, excessive fragmentation of one observable flow, deep checks mixed into mandatory core regression, or full artifacts for a simple scope without rationale.

## Reviewer Gate

Reviewer checks profile selection, artifact mode, required/conditional artifacts, TC Set Optimization when required, and separation of `core`, `regression-candidate`, `deep`, `optional`, and `blocked-by-gap` coverage. `simple` for table-heavy/high-risk scope and compact/full mismatch for `deep` are findings.

Related: `scope-contract-format.md`, `package-test-design-plan-format.md`, `test-design-coverage-metrics-format.md`, `test-design-review-format.md`, `tc-set-optimization-format.md`.
