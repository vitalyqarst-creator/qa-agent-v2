# Specialized Reviewer Contracts

Этот reference загружается только для explicit `source_assertion_review` или
legacy `scope_gap_review`. Он не относится к обычному practical route v0.9.

## `source_assertion_review`

Apply `source-assertions-format.md` directly: challenge the manifest against
XHTML/DOCX-parity and mockup evidence, then emit one exact-digest receipt. This
pass subsumes gap review for compiler contract v3 and never edits assertions,
obligations or test cases.

Start the boundary check outside the selected section: inspect document-global
constraints, ancestor/section preambles and cross-referenced constraints.
Receipt v6 must record polarity, semantic disposition, execution readiness and
risk for every assertion, plus the typed `scope_boundary_review`. Compare the
complete hash-bound `source_rows` registry with `source-row-inventory.md`,
including `in_scope = no`, exact locators, bounded text/context, candidate ids
and requirement codes. Independently verify extraction regions and complete
candidate mapping, then emit the digest-bound `source_inventory_review`.

Apply `source-assertion-semantic-rule-card.md` to every statement/action/oracle
chain. Each assertion has the canonical thirteen-key `dimension_verdicts` map;
its aggregate and `verdict` must agree. Verify the hash-bound coverage-gaps
artifact, exact ASSERT/ATOM/OBL chain and every execution-dependency gap
binding. Testable/not-applicable assertions cannot claim a primary gap.

Before acceptance, verify every declared evidence-source hash/role. Reject an
XHTML-based FT manifest that omits the DOCX source of truth, available PDF parity
source or support material used for a dictionary/oracle. Approved clarification
may affect readiness only through a canonical answered record with truthful
authority/type, exact hash, resolved GAP binding and local clause/code binding.
For PDF-only requirement-code bindings, verify canonical `page:<n>` locator and
literal extraction from that exact registered page.

## `scope_gap_review`

This is a legacy pre-writer mode for a confirmed scope with `GAP-*`. Using the
active scope-gap prompt, verify complete XHTML/source-row anchors, narrow gap and
blocking classification, clarification routing, parity/mockup limitations and
the absence of invented coverage. Emit `scope-gap-review.md` and route only to
writer, scope revision or `blocked-input`; never review TCs or sign off. Do not
run it in addition to compiler-contract-v3 `source_assertion_review`.
