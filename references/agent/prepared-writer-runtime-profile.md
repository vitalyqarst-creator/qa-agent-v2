# Prepared Writer Runtime Profile

This is a technical execution profile inside the `ft-test-case-writer` phase. It contains no new QA policy. Upstream source/scope preparation already applied the full writer contracts when it built the immutable package; the fresh prepared writer executes only the allowlisted draft step.

## Eligibility

Continue only when the embedded payload confirms:

- package version `4`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- exact output path and attempt root;
- scope-local evidence;
- testable `ATOM-*` with observable oracles and explicit non-testable gaps;
- draft seed and runtime limits.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence and dependency/state packages return `route-to-standard-writer`. Do not open a full source to bypass eligibility.

## Fast Execution

1. Run the required environment probe only when no saved probe is confirmed.
2. Do not reread package files or general writer references: the runner embeds their verified prepared projection in the prompt.
3. The declared output file does not exist at stage start and is stage-owned. Create it as the first file write with `Add File` or an equivalent atomic create; use the inline draft seed only as a template. Do not use an update-only patch against the absent output and do not postpone the first write for additional design.
4. Create executable `TC-*` only for `coverage_status = testable` and implement the provided `test_intent` and `observable_oracle`.
5. Never turn `gap`, `unclear` or `not-applicable` into executable coverage.
6. Do not invent screens, fields, dictionaries, values, UI reactions, setup, API/DB effects or persistence.
7. Do not create split design artifacts, matrices, workflow state, logs or next-stage prompts. Runner and upstream package own them.
8. Finish after the complete unsigned draft is written. Reviewer and promotion belong to the runner.

## Quality Floor

- one TC covers one check and one main observable result;
- every TC has parseable runtime metadata, reproducible preconditions, concrete permitted data, numbered steps, final expected result and postconditions;
- traceability names an existing testable `ATOM-*`;
- placeholders and invented literals are forbidden;
- production `test-cases/` stays unchanged;
- draft must differ from the seed and contain no seed sentinel.

## Targeted Fallback

A registered full source may be opened only for one explicitly unresolved `ATOM-*` when the prompt allows fallback. Emit `targeted_source_fallback` with reason, source path and exact locator. Never scan a document. Insufficient evidence blocks the stage.
