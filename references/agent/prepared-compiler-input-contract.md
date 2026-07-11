# Prepared Compiler Input Contract

This reference defines the canonical input accepted by `scripts/compile_prepared_stage_package.py`. It is a deterministic projection contract between canonical test-design artifacts and an immutable prepared stage package.

## Contract Version

The current input version is `2`:

```yaml
prepared_compiler_contract_version: 2
```

Missing and unknown versions are blocking. Use `scripts/migrate_prepared_compiler_contract.py` for a dry-run assessment and add `--write` only after the reported migration is understood.

## Required Compiler Input Fields

- `ft_slug` and `scope_slug`;
- `canonical_test_cases`, used only to derive the section id when it is not supplied explicitly;
- `latest_artifacts.source_selection`;
- `latest_artifacts.atomic_requirements_ledger`;
- `latest_artifacts.coverage_obligation_table`;
- `latest_artifacts.package_test_design_plan`;
- `latest_artifacts.test_design_applicability_matrix`;
- optional `latest_artifacts.coverage_gaps` and `latest_artifacts.dictionary_inventory` when the scope uses them.

All paths are FT-package relative. The compiler input, design artifacts, output and attempt root must remain inside the explicitly selected `fts/<ft-slug>` package.

## Traceability Contract

Contract v2 separates three concepts:

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

## Coverage Obligation Table

The compiler accepts only the canonical columns from `references/agent/coverage-obligation-table-format.md`:

`obligation_id`, `package_id`, `source_property_id`, `linked_atom_id`, `property_type`, `obligation_class`, `required_behavior`, `source_ref`, `planned_tc_or_gap`, `status`, `review_notes`.

Legacy `CO-*`, `linked_atom` and compact seven-column tables must be migrated before compilation. The migrator handles only recognized one-atom legacy rows. Missing obligation tables, unknown atoms and scope-exclusion rows without an atom require semantic review and are not auto-generated.

## Atomic Ledger Extension

`constraint_gap_ids` is an optional atomic-ledger column. It may contain only `GAP-*` identifiers. Use it when a source/extraction/setup limitation constrains a testable atom without invalidating its observable obligation.

Do not use constraint gaps to hide an unknown expected result. If the obligation itself is not executable, keep the atom and obligation at `gap` or `unclear`.

## Migration Safety

The migrator is conservative:

- dry-run by default;
- package-boundary checked;
- atomic writes in `--write` mode;
- recognized schema aliases only;
- refuses to invent obligations or attach rows without one known atom.

After migration, compile into a new immutable cycle directory. Do not overwrite an existing prepared package.
