# Prepared Writer Runtime Profile

This is a technical execution profile inside the `ft-test-case-writer` phase. It contains no new QA policy. Upstream source/scope preparation already applied the full writer contracts when it built the immutable package; the fresh prepared writer executes only the allowlisted draft step.

## Eligibility

Continue only when the embedded payload confirms:

- package version `5`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- exact runner-owned output path and attempt root;
- scope-local evidence;
- testable `ATOM-*` with observable oracles and explicit non-testable gaps;
- draft seed and runtime limits.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence and dependency/state packages return `route-to-standard-writer`. Do not open a full source to bypass eligibility.

## Structured Fast Execution

1. Do not call the environment probe, shell or file tools. The runner already supplies the verified prepared projection and the structured mode has a zero-command budget.
2. Do not reread package files or general writer references: the runner embeds their verified prepared projection in the prompt.
3. Return one schema-constrained JSON object. For `draft-ready`, put the complete unsigned Markdown in `draft_markdown` and leave `blocking_reasons` empty. The runner alone atomically materializes `draft.md`.
4. Create executable `TC-*` only for `coverage_status = testable` and implement the provided `test_intent` and `observable_oracle`.
5. Never turn `gap`, `unclear` or `not-applicable` into executable coverage.
6. Do not invent screens, fields, dictionaries, values, UI reactions, setup, API/DB effects or persistence.
7. Do not create split design artifacts, matrices, workflow state, logs or next-stage prompts. Runner and upstream package own them.
8. Return `blocked-input` with an empty `draft_markdown` and precise `blocking_reasons` when inline evidence is insufficient. Reviewer and promotion belong to the runner.

## Explicit Legacy Workspace Mode

Use this mode only when the runner prompt explicitly selects `workspace`. The declared output is then stage-owned and absent at start: create it as the first file change from the inline seed, keep all writes under the declared stage-output root, use only an exact targeted fallback authorized by the prompt, and finish only after the complete draft is written. Never switch from structured mode to workspace mode inside a running attempt.

## Quality Floor

- one TC covers one check and one main observable result;
- every TC has parseable runtime metadata, reproducible preconditions, concrete permitted data, numbered steps, final expected result and postconditions;
- traceability names both the existing testable `OBL-*` and its linked `ATOM-*`;
- placeholders and invented literals are forbidden;
- the read-only writer performs no workspace mutation; production `test-cases/` stays unchanged;
- draft must differ from the seed and contain no seed sentinel.

## Targeted Fallback

Structured fast mode does not open registered full sources. Insufficient inline evidence returns `blocked-input` and routes to an explicitly selected standard writer. The legacy workspace mode retains targeted fallback only when the caller selects that mode explicitly; it is not a silent recovery path.
