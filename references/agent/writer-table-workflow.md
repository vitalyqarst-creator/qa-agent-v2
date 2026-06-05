# Writer Table Workflow

Use this workflow when the confirmed scope is table-heavy, field/action-table based, PDF/DOCX extraction based, or requires row-level parity.

## Required Inputs

Before writing the ledger or test cases, read:

- scope contract and workflow state;
- `source-parity-check.md` when DOCX and PDF are both available;
- handoff `source-row-inventory.md` when row-level parity is required;
- support dictionary/catalog files when source rows reference dictionaries, tags or fixed value lists;
- relevant source table fragments.

If a required handoff inventory is missing, do not write a compact draft. Return `blocked-input` to scope analysis.

## Split Artifacts

Create split artifacts under:

`fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/`

Required table-flow artifacts usually include:

- writer-side `source-row-inventory.md`;
- `source-row-completeness-matrix.md` when one source row contains several requirement codes;
- `source-table-normalization.md`;
- `dictionary-inventory.md` when normalized rows or support files reference dictionaries, tags or fixed lists;
- `test-design-decision-table.md`;
- `coverage-obligation-table.md` when normalized properties imply coverage classes;
- `package-test-design-plan.md`;
- `coverage-metrics.md` for applicable dimensions;
- `fixture-catalog.md` when reusable baselines or negative transition fixtures are used;
- `risk-priority-map.md` when high-risk atoms/dimensions are present;
- `state-model.md` when lifecycle/status/form-state complexity is present;
- `test-design-review.md`;
- Writer Quality Gate.

Use `writer-table-artifacts-format.md` for the compact artifact summary and individual format references for detailed shape.

## Normalization Rules

Every in-scope or unclear source row from the handoff inventory must be preserved and mapped to `ATOM-*`, `GAP-*` or an explicit out-of-scope decision.

Each normalization row must:

- have stable `source_property_id`;
- preserve exact `GSR-*`, `REQ-*` or local requirement codes;
- keep one semantic property class per row;
- cite `source_column` and `source_text_fragment` when diagnostic fidelity matters;
- avoid table-header residue, adjacent-field pollution and extraction artifacts.

Do not combine independently checkable classes such as dictionary source, min/max boundary, format, mask, default value, visibility, requiredness, editability and integration prefill in one normalization row.

Rows with `confidence = low` or unresolved source meaning must link to `GAP-*` or remain diagnostic; they cannot become covered atoms.

For `dictionary-source` / reference-list rows, extract the referenced source/support dictionary into `dictionary-inventory.md` before TDDT. Use `DICT-*` in downstream artifacts; two branch-driver examples from FT do not replace the full active-value inventory.

## Test Design Decision Table

Create the decision table before ledger, package plan or test cases.

Allowed decisions include:

- standalone executable TC;
- covered by existing TC;
- scenario-only support;
- metadata-only;
- gap or unclear;
- out of scope.

Metadata-only rows must not link to `TC-*` unless there is a separate observable behavior. A gap decision must have a real `GAP-*`; do not use placeholder gap IDs.

## Diagnostic-Only Runs

If the task asks only to check or build Source Table Normalization, create `source-normalization-diagnostic.md` and stop before ledger, package plan, reviewer artifacts or signed-off claims.

Diagnostic output must include all in-scope and unclear inventory rows, not just a high-risk subset.

## Gate

Do not route to reviewer if table artifacts show:

- compressed normalization rows;
- mixed property classes;
- missing `source_property_id`;
- broad covered requirement ranges;
- missing mask, numeric, dictionary, date-window or visible-behavior classes;
- missing exact-length, repeatable-block, checkbox-list, generated document or action-created optionality classes when source implies them;
- missing coverage metrics for applicable dimensions;
- missing fixture catalog or concrete baseline for negative transition checks;
- missing risk model for high-risk atoms;
- missing `dictionary-inventory.md` or missing `DICT-*`/`GAP-*` downstream link for dictionary-source rows;
- false or overbroad gaps;
- one `TC-*` used to hide several independent design rows.
