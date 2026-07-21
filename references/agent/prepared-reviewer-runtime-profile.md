# Prepared Reviewer Runtime Profile

This is the technical execution projection inside `ft-test-case-reviewer`. It introduces no new QA policy. Raw DOCX/XHTML/PDF/support semantics are independently checked once by the source-assertion reviewer. The TC reviewer is a separate independent control over the resulting exact accepted typed assertions, compiled obligations and writer draft; it must not repeat the raw-source audit.

## Eligibility

Continue only when the payload confirms:

- runner-validated current package metadata, including a non-empty SHA-256 `package_digest`, and immutable draft SHA-256;
- compiler `output_mode`, `release_eligible` and exact blocking source-gap ids;
- explicit execution/context profiles and unsupported dimensions;
- an accepted source-assertion receipt bound to the current manifest digest, plus a digest-bound compact projection of every assertion/OBL actually referenced by the draft;
- exact typed condition/action/oracle, requirement-code, gap, dictionary and readiness bindings, plus the complete compiled obligation semantics;
- passed structure, seed, obligation, quality and evidence-access gates;
- semantic-overlap diagnostic and calibration lifecycle.

Return a blocking finding when a digest is stale, a draft trace id is unknown, a referenced assertion/OBL is absent, or the accepted assertion and compiled obligation semantics are inconsistent. Do not use production test cases, earlier cycles or generated package prose as requirement evidence. Do not open raw FT/support files in this stage: a disputed source interpretation requires a fresh source-review receipt, not an ad-hoc TC-review reread.

`unsupported_dimensions` is a legacy package-field name: it means "unsupported by the prepared fast path and therefore routed to this standard semantic reviewer". It does not mean that the dimension lacks evidence or must receive verdict `unsupported`. Review each listed dimension from its bound accepted semantics and return `verified` when that evidence and the draft support it.

## Review Procedure

1. Compare every digest-bound accepted typed assertion with its compiled obligation first. Reject a missing assertion, changed polarity/readiness, broadened condition, action or oracle, invented behavior, changed code/gap/dictionary binding or lost source-to-ATOM-to-OBL link before reviewing TC wording. Do not reinterpret the raw FT in this stage.
2. Review every supplied obligation exactly once. Return its exact
   `obligation_id` and a compact verdict compatible with its coverage status;
   the runner derives and verifies the bound `atom_id`, planned TC and draft
   SHA-256 rather than accepting those values from reviewer prose.
3. For every testable obligation, verify that its linked TC performs the source-backed condition/action with concrete data and reaches the source-backed observable oracle.
4. For every gap, unclear or not-applicable obligation, verify that the compiled classification exactly matches the accepted source contract and that the draft does not invent executable coverage. Reclassification requires a fresh source review rather than a TC-review guess.
5. For every non-blocking constraint gap, verify that the linked TC preserves the `GAP-*` and does not choose an unspecified mechanism.
6. Apply the embedded context rule card: boundary points remain independent; invalid classes remain independent; branch preconditions and integration triggers remain explicit.
7. Reject invented UI, literals, messages, API/DB effects or internal state; validate UI locators against the supplied mockup inventory and dictionary claims against projected `active_values`.
8. Reject non-atomic cases, generic fixtures, placeholder steps, source-rule-only expected results, duplicate titles and nominal traceability.
9. Classify every semantic-overlap group. Accept a shared body only when the package explicitly groups one observable multi-obligation check.
10. Review every declared routed cross-cutting dimension exactly once. Repeat
    the complete canonical sorted source-ref array listed for that same
    dimension in the immutable `reviewer-dimension-source-bindings-v1` map.
    Omitting or reordering a bound ref, or citing a ref listed only for another
    dimension, is invalid. An unverified or unsupported applicable dimension
    prevents sign-off; it cannot be silently accepted as metadata.
11. For UI-calibration candidates, require `ui-calibration-required`, `candidate-ui-calibration`, every linked constraint GAP when present, and a neutral expected result that does not preselect filtering/message/highlight/save behavior. Package-declared calibration without a GAP remains a valid lifecycle item.
12. Return exactly the structured review contract requested by the runner. Do not write files.

## Decision Floor

- `accepted` requires every compiled obligation and draft check to match the exact accepted typed assertion semantics, every testable obligation to have verdict `covered`, every gap/unclear/not-applicable obligation to have verdict `gap-preserved`, every routed review dimension to be `verified` and no error finding.
- `changes-required` requires at least one concrete finding linked to supplied ATOM/TC identifiers, unless it is a set-level scope finding.
- A failed deterministic gate, draft hash mismatch, unknown identifier, lost constraint gap or insufficient evidence prevents sign-off.
- `accepted` for `draft-with-blocking-gaps` validates the unsigned test-case
  draft only. It does not close a source gap or make the cycle release-eligible.

The independent source assertion receipt authenticates the reviewed source
model, not production readiness. When blocking source gaps remain, return the
ordinary complete obligation receipt; the runner owns the terminal
`blocked-input`/`blocked-source-gaps` transition and must not create promotion
artifacts.

## Structured Output Boundary

The source-first prepared reviewer returns contract v4. It binds the exact draft,
source-basis and obligation-set SHA-256 values; includes one compact
`{obligation_id, verdict}` item for every obligation; includes one
`dimension_reviews` item for every routed cross-cutting dimension; and carries
only the findings needed to explain defects. Missing, duplicate or unknown
obligation ids, coverage-incompatible verdicts, incomplete/reordered dimension
source refs, cross-dimension source refs, a `covered` verdict whose compiler-planned TC is
absent from the reviewed draft, or a non-passing obligation verdict without a
linked error finding invalidate the receipt. Legacy source-first output without
the exact per-obligation receipt is obsolete and must not be promoted.

## Runtime Boundary

No command is normally needed because the digest-bound accepted assertion and compiled-obligation projections are embedded. If runtime confirmation is absolutely required, only the explicitly allowlisted environment probe may be used. Any raw-source reread, broad repository exploration or workspace mutation violates the compact prepared reviewer contract.
