# Prepared Reviewer Runtime Profile

This is a technical execution profile inside the `ft-test-case-reviewer` phase. It introduces no new QA policy. The canonical full reviewer rubric remains authoritative for standard review; this projection contains only the checks applicable to an eligible immutable `simple-field-property` prepared package.

## Eligibility

Continue only when the embedded payload confirms:

- package version `5`;
- `execution_profile = simple-field-property`;
- empty `unsupported_dimensions`;
- an immutable draft hash;
- scope-local evidence and atomic obligations;
- passed structure, seed, obligation and writer evidence-access gates.

Legacy/unclassified, table-parity, numeric-boundary, integration/persistence, dependency/state and other unsupported packages return `route-to-standard-reviewer`. Do not open full project instructions or sources to bypass eligibility.

## Review Procedure

1. Use only the verified inline payload. Do not reread the full reviewer skill, instruction manifest, package files, references, prior cycles, production test cases or full sources.
2. Review every supplied obligation exactly once, preserving its exact `obligation_id -> atom_id` pair, and bind the result to the supplied draft SHA-256.
3. For each `coverage_status = testable`, verify that linked `TC-*` steps and final expected result exercise the obligation condition and its concrete observable oracle.
4. For each `gap`, `unclear` or `not-applicable` obligation, verify that the draft does not claim executable coverage or invent the missing mechanism.
5. Reject invented screens, fields, literals, dictionaries, messages, statuses, UI reactions, API/DB effects, persistence or internal state.
6. Reject non-atomic cases, generic test data, placeholder steps, source-rule oracles and traceability that is present only nominally.
7. Classify every supplied semantic-overlap diagnostic group. Accept a shared body only when it is a justified observable multi-obligation check; otherwise return a `duplication` finding and require consolidation. Different titles do not justify identical steps and final expected results.
8. Return the exact structured review contract requested by the runner. Do not write files; the runner renders human-readable findings.

## Decision Floor

- `accepted` requires every obligation to have a consistent verdict, every testable obligation to be correctly covered, every non-testable obligation to stay non-executable, and no `error` finding.
- `changes-required` requires at least one concrete finding linked to a supplied `ATOM-*` or `TC-*` unless it is a set-level scope finding.
- A deterministic gate marked failed, a draft hash mismatch, an unknown atom/test-case id or insufficient inline evidence blocks trusted sign-off.

## Runtime Boundary

No shell command is needed to review the inline payload. If the runtime environment has not already been confirmed, one exact `python scripts/probe_environment.py` command is allowed. Any other command or workspace read violates the prepared fast path.
