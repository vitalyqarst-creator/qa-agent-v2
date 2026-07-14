# Prepared Writer Runtime Profile

This is the technical execution projection inside `ft-test-case-writer`. It introduces no new QA policy. Upstream source/scope preparation and the prepared compiler have already applied the canonical writer contracts; the fresh writer executes the allowlisted draft step from an immutable package.

## Eligibility

Continue only when the embedded payload confirms:

- runner-validated current package metadata, including non-empty SHA-256 `package_digest` and `input_fingerprint`;
- `execution_profile = simple-field-property` or `standard-required`;
- an explicit context profile and unsupported dimensions;
- scope-local source evidence and atomic obligations;
- every testable obligation has a concrete intent, a portable fixture contract and observable oracle;
- every unresolved or non-blocking constraint is linked to an explicit `GAP-*`;
- a runner-owned draft seed and schema-constrained output contract.

Return `blocked-input` when these conditions do not hold. Do not open project instructions or full sources to bypass eligibility.

## Structured Execution

1. Use only the embedded payload. Do not call the environment probe, shell, file, Git or search tools.
   This is a zero-command budget: the runner alone atomically materializes the returned draft.
2. Return one schema-constrained JSON object. For `draft-ready`, put the complete unsigned Markdown in `draft_markdown`; the runner atomically materializes `draft.md`.
3. Create executable `TC-*` only for `coverage_status = testable` and implement the supplied `test_intent`, concrete fixture and `observable_oracle`.
4. Preserve exact `OBL-* -> ATOM-* -> TC-*` traceability. Use a shared planned TC only when the package already groups those obligations.
5. Never turn `gap`, `unclear` or `not-applicable` into executable coverage.
6. Preserve every `constraint_gap_ids` marker in the linked TC. Independently preserve `calibration_status = ui-calibration-required` with both `ui-calibration-required` and `candidate-ui-calibration`, even when no GAP exists.
7. For every entry in `runner_owned_dictionary_materializations`, keep the exhaustive check symbolic through its `DICT-*` id and coverage mode. Exact exhaustive leaf payloads may be intentionally omitted from the writer-only evidence projection because the immutable package remains available to runner gates and reviewer. Do not enumerate two or more supplied group/leaf labels in the writer output: the runner adds the exact complete hierarchy once before deterministic gates and reviewer handoff. Concrete values required by a separate `reference-only` obligation remain writer-owned and must keep their exact group path.
8. Do not invent screens, fields, dictionaries, values, messages, validation mechanisms, setup, API/DB effects, state transitions or persistence.
9. Keep one primary check and one main observable result per TC. Use unique titles that name the field/action and exact positive, boundary or invalid class.
10. A concrete FT-first fixture may be a synthetic value, relative date or runtime-selected integration response with source-defined observable properties. A stand record ID, locator, token, session or prerecorded provider response is not required until UI-prep.
11. Return `blocked-input` with empty `draft_markdown` and precise reasons only when inline evidence cannot define the test intent or observable oracle without invention.

## Targeted Repair Projection

When the runner declares a hash-bound targeted-repair plan, return only the assigned `## TC-*` replacement sections in the declared order. Treat prior unsigned sections as repair input, never as requirement evidence; source-backed evidence and the exact obligation projection remain authoritative. Preserve assigned OBL/ATOM and gap markers. For calibration candidates, make the expected result an evidence record containing the exact input/action, visible state and outcome without inventing a UI mechanism. For permitted-value checks, state the exact visible value. Do not add an H1 or any unassigned TC; the runner owns byte-preserving splice and full-set validation.

## Assisted Fallback

`prepared-standard --prepared-standard-writer-mode assisted` is an explicit recovery route, never an automatic retry. It may use only manifest-listed instruction artifacts and a single targeted registered-source fallback for a named unresolved OBL/ATOM. Record the path, locator and reason. Broad discovery, production test cases, prior cycles and generated drafts remain forbidden.

## Quality Floor

- structurally complete Markdown with no seed sentinels or angle-bracket placeholders;
- reproducible preconditions and concrete permitted data;
- numbered user actions and one final observable expected result;
- exact requirement/OBL/ATOM traceability;
- unique IDs and titles;
- exhaustive dictionary values are emitted only by the runner-owned projection; writer output keeps their `DICT-*` reference and does not duplicate the value set;
- explicit calibration lifecycle for every package-declared calibration candidate, with or without a constraint gap;
- no workspace mutation by the structured writer;
- no production write or promotion.
