# Prepared Compiler Input Contract

This reference defines the canonical input accepted by `scripts/compile_prepared_stage_package.py`. It is a deterministic projection contract between canonical test-design artifacts and an immutable prepared stage package.

## Contract Version

The current source-first input version is `3`:

```yaml
prepared_compiler_contract_version: 3
```

Missing and unknown versions are blocking. Use `scripts/migrate_prepared_compiler_contract.py` for a dry-run assessment and add `--write` only after the reported migration is understood.

Version `2` remains readable for legacy diagnostic package compilation, but it
does not carry the independent source assertion receipt required by the current
source-first route. Even with `output_mode = release`, it returns
`release_eligible = false` and `legacy-source-contract`; it cannot be promoted.

## Required Compiler Input Fields

- `ft_slug` and `scope_slug`;
- `canonical_test_cases`, used only to derive the section id when it is not supplied explicitly;
- `latest_artifacts.source_selection`;
- `latest_artifacts.atomic_requirements_ledger`;
- `latest_artifacts.coverage_obligation_table`;
- `latest_artifacts.package_test_design_plan`;
- `latest_artifacts.test_design_applicability_matrix`;
- optional `latest_artifacts.coverage_gaps` and `latest_artifacts.dictionary_inventory` when a legacy scope uses them; contract v3 always requires `coverage_gaps` because the manifest hash-binds that artifact, even when it contains no open gap.
- optional `latest_artifacts.source_to_package_fidelity`; when declared, the compiler enforces the bindings from `references/agent/source-to-package-fidelity-format.md`.
- optional standard-route `latest_artifacts.semantic_design`; when present it
  requires declared `latest_artifacts.scope_boundary_decision` and
  `latest_artifacts.semantic_design_bridge_receipt`. The design must be ready
  `semantic-design-bridge-v2` v4 and use the compiled package id. The verified,
  atomically published receipt must hash-bind both JSON artifacts, the accepted
  source assertion manifest and the passed canonical source-review evidence
  preflight. Its semantic obligation, dependency and oracle graph must preserve
  the accepted `ASSERT -> ATOM -> OBL` manifest/ledger/materialized-obligation
  chain exactly. Newly materialized receipts also carry
  `publication_ownership_contract_version = 1` and a per-invocation UUIDv4.
  These fields are operational recovery provenance, not requirement semantics;
  standard wrappers require them, while a legacy receipt without them cannot be
  recovered as the current invocation and must be rematerialized. The immutable
  projection intentionally preserves the concrete receipt and its SHA, so a
  fresh publication has per-run provenance/fingerprint even when its semantic
  graph is equivalent. Non-empty negative/requiredness collections require their
  respective declared Markdown inventories; those inventories are invalid
  without `semantic_design`.
- for contract v3, required `latest_artifacts.source_row_inventory`,
  `latest_artifacts.source_row_extraction_spec`,
  `latest_artifacts.source_row_baseline`, `latest_artifacts.source_assertions` and
  `latest_artifacts.source_assertion_review`; the review receipt must be
  current and `accepted`.

For contract v3 the inventory table must contain `source_row_id`, `in_scope`,
`source_path`, `source_locator`, `bounded_source_text`, `source_context_class`
and `requirement_codes`. Every row, including `in_scope = no`, enters the typed
expected registry. The manifest must match path/locator/text/context/scope/codes
exactly; matching only the `SRC-*` id set is insufficient. A `no` row permits
only `not-applicable` assertions. Primary assertion fragments are checked only
inside their bounded row; evidence from another row requires a structured
supporting binding.

All paths are FT-package relative. The compiler input and design artifacts must
remain inside the explicitly selected `fts/<ft-slug>` package. Prepared output
must equal `<cycle>/prepared-input/<package-id>` with its leaf equal to the
compiled package id; attempt root must equal
`<cycle>/attempts/<stage>/<attempt-id>`. Extra path levels are rejected. Version
2 ignores declared source-first/semantic artifacts because it does not read or
fingerprint them.

The compiler losslessly embeds all dependency/oracle fields, semantic and
inventory paths, SHA-256 values and exact inventory UTF-8 text in immutable
`source-evidence.md`; drift changes the input fingerprint and missing/mismatched
bindings block writer. Timing uses the same resolver and counts only actual
compiler inputs, including selected sources and package `AGENT-NOTES.md`.

## Traceability Contract

Contracts v2 and v3 separate three concepts:

- `ATOM-*` is one atomic source statement;
- `OBL-*` is one independently verifiable coverage obligation derived from exactly one atom;
- `TC-*` or `GAP-*` is the planned executable or unresolved outcome of the obligation.

Required invariants:

1. `ATOM-*` and `OBL-*` identifiers are unique.
2. Every `OBL-*` links exactly one known `ATOM-*`.
3. Every atom has at least one obligation; one atom may have several obligations.
4. A covered obligation links a `TC-*` present in a design-plan row for the same atom.
5. A gap/unclear obligation and its atom link the same single `GAP-*`.
6. Every open gap is linked either by a gap/unclear obligation or through `constraint_gap_ids` on a testable atom.
7. A constraint gap remains visible in the prepared package but does not change the testable obligation into a gap.
8. Every referenced `DICT-*` resolves to one unique non-empty dictionary inventory row.
9. Every declared source-fidelity binding preserves its literal in the named projection targets or records an explicit allowed decision; ambiguous source units do not become exact bytes without a source-backed policy.
10. Every source-first OBL row preserves the exact `source_property_id` of its
    ATOM ledger row. A positive reviewed source assertion cannot inherit an
    explicitly negative `property_type`, `obligation_class`, `check_type`,
    `coverage_class` or `input_class` from a cloned obligation/design row;
    rematerialize the assertion-specific mapping instead of reusing it.

## Output Mode And Release Boundary

`scripts/compile_prepared_stage_package.py` accepts explicit
`--output-mode release|draft-with-blocking-gaps`; `release` is the default and
retains the fail-closed release behavior. Only contract v3 in `release` mode
without release blockers can return `release_eligible = true`.

`draft-with-blocking-gaps` is allowed only for contract v3 after an independent
accepted source assertion receipt. It may preserve narrow primary blocking gap
obligations only when at least one obligation remains `testable`. It never
permits a blocking constraint gap. Broad primary gaps, nonblocking coverage-floor
failures, high/critical nonblocking gaps and every other ordinary compiler guard
remain blocking; the mode is not a waiver mechanism.

The compiler exposes `output_mode`, `release_eligible`, `blocking_gap_ids` and
`release_blocking_finding_codes`. It embeds the same values plus the full
coverage report in the immutable `prepared-compiler-release-status-v1` block of
`source-evidence.md`. A source assertion receipt authenticates the source model;
it does not make this draft release-eligible.

A reviewed `draft-with-blocking-gaps` artifact remains unsigned. Runner lifecycle
and promotion consequences are defined in `review-cycle-stage-contract-v2.md`
and `controlled-promotion-format.md`.

Execution readiness is independent from semantic gap routing. Any testable
assertion with `execution_readiness = dependency-blocked` fails `release` with
`source-execution-dependency-blocked`. In explicit
`draft-with-blocking-gaps`, compiler v3 instead builds the executable ready
subset and package v9 `release_status` carries the exact blocked
assertion/source-row/ATOM/OBL/GAP/risk/rationale registry. Those OBLs are excluded
from writer/reviewer projections and must not share a planned TC or design-plan
group with a ready OBL. The cycle remains unsigned as
`blocked-input/blocked-execution-dependencies`, emits no promotion seed,
canonical publication or signed-off snapshot. An all-blocked scope stops before
writer as `draft-no-ready-execution-assertions`; a clean draft request without
any blocker is also rejected.

The immutable package status is canonical. The similarly named JSON block in
`source-evidence.md` is a derived diagnostic projection and declares
`derived_from: stage-package.json#/release_status`; runner and promotion reload
and reconcile package status against the independently reviewed manifest and
compiled obligations at every trust boundary.

## Source-To-Package Fidelity Extension

Use `source-to-package-fidelity.json` only for named high-risk literals and unit conversions. It is optional for legacy scopes, but mandatory for the current compile whenever `latest_artifacts.source_to_package_fidelity` is present. The compiler validates it before creating package evidence and embeds the normalized bindings into `source-evidence.md` so binding changes affect the immutable input fingerprint.

The canonical schema, closed handling enums and diagnostics are defined in `references/agent/source-to-package-fidelity-format.md`. Do not replace the artifact with prose in a prompt or decision log.

## Coverage Obligation Table

The compiler requires the canonical columns from `references/agent/coverage-obligation-table-format.md`:

`obligation_id`, `package_id`, `source_property_id`, `linked_atom_id`, `property_type`, `obligation_class`, `required_behavior`, `source_ref`, `planned_tc_or_gap`, `status`, `review_notes`.

Dictionary-backed rows may add `dictionary_coverage` with the closed enum:

- `reference-only` — the scenario uses one named dictionary value or dependency and does not claim exhaustive composition;
- `all-leaf-values` — every active leaf value must be present in the linked TC;
- `full-hierarchy` — every child group name and active leaf value must be present with its hierarchy path.

New exhaustive rows should set this column explicitly. For existing contract-v2 artifacts only, the compiler maps the stable legacy classes `dictionary-hierarchy-shown`, `dictionary-values-shown` and `value-has-checkbox` to the corresponding exhaustive mode; all other dictionary references remain `reference-only`. It does not infer exhaustive coverage from free-form Russian/English prose.

Legacy `CO-*`, `linked_atom` and compact seven-column tables must be migrated before compilation. The migrator handles only recognized one-atom legacy rows. Missing obligation tables, unknown atoms and scope-exclusion rows without an atom require semantic review and are not auto-generated.

## Atomic Ledger Extension

`constraint_gap_ids` is an optional atomic-ledger column. It may contain only `GAP-*` identifiers. Use it when a source/extraction/setup limitation constrains a testable atom without invalidating its observable obligation.

Do not use constraint gaps to hide an unknown expected result. If the obligation itself is not executable, keep the atom and obligation at `gap` or `unclear`.

## Reset State-Change Extension

Semantic bridge v4 keeps this data in the closed top-level
`reset_lifecycle_bindings` registry keyed by `obligation_id`; generic semantic
OBL objects do not carry state-change fields. The deterministic legacy
projection restores the four plan columns below only for bound reset/re-add
obligations before the compiler reads the Markdown design plan.

When a covered obligation or its mapped plan row is classified as `reset`, `*-reset` or `reset-*`, every mapped executable Package Test Design Plan row must add:

- `initial_state_capture` — the visible initial state captured in the same test;
- `changed_state_setup` — how to choose a state relative to that capture, without assuming an exact product default;
- `pre_action_state_oracle` — the visible check proving the prepared state differs before the target action;
- `state_relation` — exactly `different-from-captured-initial`.

The compiler emits `execution_semantics = reset-to-captured-initial` and a structured `state_change` object. Missing or conflicting fields fail as `state-change-precondition-incomplete` / `state-change-precondition-conflict` before a prepared package or LLM attempt is created.

For a source-first package, `initial_state_capture` is a typed zero-based binding in the form `source-condition:<index>`. The compiler replaces it with the exact independently reviewed `condition_clause` at that index. Free prose, an action/oracle binding, or a missing condition index fails before LLM execution as `source-first-state-change-initial-binding-required` / `source-first-state-change-initial-binding-invalid`. Legacy v2 plan prose remains readable only outside the source-first contract.

## Migration Safety

The migrator is conservative:

- dry-run by default;
- package-boundary checked;
- atomic writes in `--write` mode;
- recognized schema aliases only;
- refuses to invent obligations or attach rows without one known atom.

After migration, compile into a new immutable cycle directory. Do not overwrite an existing prepared package. `--reuse-if-current` is allowed only for an identical current-version target-bound package: source registry, compiler evidence, obligations, instructions, output mode and attempt binding must produce the same `input_fingerprint`; otherwise compilation blocks and requires a new package id/output root.
