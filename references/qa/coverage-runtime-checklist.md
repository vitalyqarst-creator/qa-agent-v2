# Coverage Runtime Checklist

This reference defines the compact runtime coverage checklist. The full `coverage-checklist.md` remains the deep reference for specialized dimensions and reviewer analysis.

## Runtime Dimensions

Before writing `TC-*`, check whether the scope contains:

- visibility / availability;
- requiredness;
- editability;
- default value;
- list or dictionary composition;
- positive acceptance;
- negative rejection;
- boundary / length / numeric classes;
- exact length and allowed-symbol classes;
- conditional branches and dependencies;
- state transition or navigation;
- persistence after save/reopen;
- calculation oracle;
- integration/API/async/internal effects;
- repeated blocks, tables, files or documents;
- generated document content mapping;
- cross-view projection after mutation;
- visible history or audit;
- role/status/security/NFR dimensions.

## Runtime Rules

- Add a baseline case only when the expected behavior follows from the FT or allowed package materials.
- If a dimension applies but the oracle is not described, record `GAP-*` / `unclear`.
- Do not close internal/integration/API/async/persistence behavior with a UI-only test case unless there is an observable artifact.
- For conditional visibility, check the positive branch and the inverse branch when inverse behavior follows from the requirement; otherwise record a gap.
- For a closed list, check expected values and absence of extra values only when closed-set behavior follows from the source.
- For numeric/date/length/mask rules, load the deep coverage reference for the relevant scenario.
- For numeric-only, exact length, repeatable/action-created blocks, checkbox-list, and generated documents, use `Coverage Obligation Table`; do not stop at one generic TC.
- For allowed-symbol/input restrictions, do not replace class coverage with one mixed invalid value. If the source says `only ...`, decompose it into source-derivable classes: valid representative, whitespace, alphabet/script class, special/disallowed symbols, and relevant boundaries. Unknown UI reaction for a class becomes a narrow `GAP-*` / `candidate-ui-calibration`, not silent coverage.
- For 3+ independent factors with multiple values, pairwise/combinatorial coverage is mandatory; choose `2-way | 3-way | t-way`, prove coverage strength, or record a gap.
- For reusable baseline and negative transition, use a concrete fixture or `fixture-catalog.md`.
- Record coverage metrics for applicable dimensions; missing metrics mean unfinished design work.
- For source-defined multiple views after a mutation or a visible history/audit, mark `cross-view-projection` / `audit-history`; load the full checklist. Do not infer behavior absent from the source.

## Deep Coverage Triggers

Load the full `coverage-checklist.md` or a specialized deep reference when the scope contains:

- numeric, amount, mask, exact length or allowed-symbol constraints;
- date/time windows, timezone, business date or boundary inclusivity;
- integration/API/server-side validation;
- async/race/retry behavior;
- security/roles/permissions;
- complex decision table;
- pairwise/combinatorial factors;
- file upload/download or generated documents;
- cross-view projection after mutation or visible history/audit;
- repeatable blocks or action-created optional blocks;
- checkbox-list / multi-select behavior;
- performance/reliability/compatibility/usability/accessibility expectations;
- reviewer/validator finding about a missed coverage dimension.
