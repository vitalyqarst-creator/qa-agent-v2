# Test Design Depth Policy

## Purpose

Этот reference задает, как выбирать глубину test design для подтвержденного FT scope. Цель - достаточное покрытие без лишних артефактов и без сокращения source-backed проверок.

## Core Principle

Test design depth is risk-based and scope-sensitive: простой scope получает compact chain, обычный scope - standard chain, table-heavy/high-risk scope - deep chain. Профиль не может использоваться для обхода traceability, gaps, XHTML extraction или source-backed negative/boundary/branch coverage.

## Coverage Depth Profiles

### simple

Используй `simple`, когда scope небольшой, однородный и не содержит таблиц, списков, справочников, conditional visibility/requiredness, state lifecycle, integrations/API/async/persistence, generated documents, blocking gaps, high-risk behavior или сложные boundary/equivalence rules.

Required: `source-selection.md`, `scope-contract.md`, atomic requirements ledger, compact `Package Test Design Plan`, canonical TC file, compact Writer Quality Gate.

Optional: standalone `coverage-metrics.md`, `coverage-obligation-table.md`, `risk-priority-map.md`, separate `test-design-review.md`.

### standard

Используй `standard` по умолчанию для обычного функционального scope. Он требует `source-selection.md`, `scope-contract.md`, `source-parity-check.md` when applicable, source-row inventory/table normalization/TDDT when rows or normalized properties exist, atomic ledger, `Package Test Design Plan`, `Test Design Review` or compact embedded equivalent, canonical TC file and Writer Quality Gate.

Conditional: `coverage-obligation-table.md`, `coverage-metrics.md`, fixture catalog, risk map, dependency matrix, decision table, pairwise/combinatorial table.

### deep

Используй `deep`, если есть хотя бы один фактор: table/list-heavy scope; XHTML exposes nested lists, dictionaries, repeated rows or table-cell lists; financial/money movement; security/access/roles; irreversible status/lifecycle transitions; generated document mapping; integration/API/async/persistence; complex dependencies; 3+ independent factors for combinatorial reasoning; high-risk atoms; many blocking/unclear gaps; previous reviewer findings show under-coverage; history of LLM missing rows/lists/branches.

Required: full source-row inventory, source-row completeness matrix when needed, source-table normalization, TDDT, coverage obligation table when property types require classes, atomic ledger, full `Package Test Design Plan`, `coverage-metrics.md`, risk map for high-risk dimensions, `Test Design Review`, `TC Set Optimization Review`, canonical TC file and Writer Quality Gate.

## Profile Selection Criteria

Start from `standard`. Downgrade to `simple` only when absence of risk/table/list/dependency signals is explicit in `Scope Complexity Assessment`. Escalate to `deep` as soon as one deep criterion is present. If evidence is unclear, prefer `standard` and record the uncertainty as a gap or risk rationale.

## Mandatory Artifacts By Profile

| coverage_depth_profile | artifact_mode | mandatory shape |
| --- | --- | --- |
| `simple` | `compact` | compact plan/review/gate, no standalone metrics unless they add real measured coverage |
| `standard` | `standard` | normal package plan and applicable artifacts; compact embedded review allowed only for moderate low-risk scope |
| `deep` | `full` | full artifact chain, metrics, risk map when high-risk, and TC Set Optimization Review |

## Conditional Artifacts

Create conditional artifacts only when the source/risk model needs them. Do not create a standalone artifact that merely repeats the plan. Do not skip source-backed obligations because an artifact is optional for the selected profile.

## Risk-Based Escalation Rules

- `table_list_heavy = yes` means profile cannot be `simple`.
- Non-empty `high_risk_dimensions` means profile cannot be `simple`.
- XHTML nested lists/table-cell lists/repeated blocks require at least `standard`, often `deep`.
- `deep` requires explicit source/risk rationale in `risk_escalation_reasons`.
- Blocking gaps that affect expected results, state transitions, dictionary completeness, integration behavior or extraction completeness require `standard` or `deep`.

## When To Use Compact Artifacts

Use compact artifacts for `simple` scope and small low-risk `standard` scope. Compact means shorter sections, not missing traceability: every atom still maps to `TC-*`, `GAP-*` or `unclear`, and every expected result remains source-backed.

## When Full Artifact Chain Is Required

Use full chain for `deep`, table/list-heavy, high-risk, generated document, integration/API/async/persistence, lifecycle/status, complex dependency or combinatorial scopes.

## TC Set Optimization

`TC Set Optimization Review` is required for `deep` and for `standard` when TC count >= 15, Package Test Design Plan rows >= 20, high-risk dimensions exist, or writer/reviewer marks over-testing risk. It checks both under-coverage and over-testing before sign-off.

## Under-testing Smells

Missing source rows, missing dictionary values, generic invalid class, no inverse branch, high-risk atom without TC/GAP, unsupported gap promotion, or one broad scenario replacing independent assertions.

## Over-testing Smells

Duplicated TC with same source/input/oracle, low-value negative cases not source-backed and not risk-backed, excessive fragmentation of one observable flow, deep checks mixed into mandatory core regression without labels, and full artifact chain for a simple scope without rationale.

## Reviewer Gate

Reviewer checks profile selection, artifact mode, mandatory/conditional artifacts, TC Set Optimization when required, and separation of `core`, `regression-candidate`, `deep`, `optional`, and `blocked-by-gap` coverage. A simple profile for table-heavy/high-risk scope is a finding; compact mode for deep scope is a finding.

## Examples

- Single source-backed field with one positive oracle and no dependencies: `simple`, compact artifacts.
- Exact length/numeric-only rule: `standard` or `deep` when multiple classes or high-risk data exist.
- XHTML table with repeated rows/list values: at least `standard`, usually `deep`.
- High-risk status transition or money movement: `deep`.
- Duplicate low-value invalid input variants: keep one core representative, convert others to deep/optional only with source/risk evidence, or remove as duplicate.

## Related References

- `references/agent/scope-contract-format.md`
- `references/agent/package-test-design-plan-format.md`
- `references/agent/test-design-coverage-metrics-format.md`
- `references/agent/test-design-review-format.md`
- `references/agent/tc-set-optimization-format.md`
