# AutoFin Prepared Compiler Contract V2

## Implemented Contract

- Compiler input requires `prepared_compiler_contract_version: 2`.
- `coverage_obligation_table` is mandatory.
- Prepared package version is `4`; package versions `1..3` remain readable but are not fast-path eligible.
- Compiler validates unique `ATOM-*` and `OBL-*` ids.
- Every obligation links exactly one known atom.
- Every atom has at least one obligation.
- Covered obligations link a `TC-*` present in a plan row for the same atom.
- Gap/unclear atoms and obligations must link the same `GAP-*`.
- Open gaps must be linked by an executable gap obligation or a testable atom's `constraint_gap_ids`.
- Dictionary references resolve to unique non-empty inventory entries.

## Migration

`scripts/migrate_prepared_compiler_contract.py` provides a dry-run by default and atomic `--write` mode. It migrates recognized legacy one-atom obligation tables and refuses missing tables, unknown atoms and semantically ambiguous scope-exclusion rows.

The three active AutoFin compiler inputs report `already-current`:

| scope | canonical obligations |
| --- | ---: |
| widget selection | 6 |
| search clear context | 4 |
| print form generation | 21 |

## Immutable Compile Result

All three contract-v2 inputs built package-version-4 outputs in new `compiler-v4-20260711` cycle directories. Widget selection remains the only `simple-field-property` fast-path candidate; search-clear and print-form remain `standard-required`.
