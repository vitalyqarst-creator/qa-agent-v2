# Writer Table Artifacts Format

Короткий runtime/deep reference для table-heavy и row-level parity writer scenarios. Полный исторически сложившийся контракт остается в `writer-output-format.md`; этот файл задает минимальный набор table artifacts, который resolver может грузить вместо полного writer output для обычного table writer.

## Required Order

Для каждого `WP-*` выполняй порядок:

1. handoff `source-row-inventory.md`;
2. writer-side `source-row-inventory.md`;
3. `source-row-completeness-matrix.md`, если source row содержит несколько `GSR-*` / `REQ-*` или несколько проверяемых свойств;
4. `source-table-normalization.md`;
5. `dictionary-inventory.md`, если есть `dictionary-source`, reference-list, tags или fixed-list properties;
6. `test-design-decision-table.md`;
7. `coverage-obligation-table.md`, если есть numeric/mask/date/amount/dictionary obligations;
8. `atomic-requirements-ledger.md`;
9. `package-test-design-plan.md`;
10. `test-design-review.md`;
11. `TC-*`;
12. `writer-quality-gate.md`.

Не создавай `TC-*`, пока normalization, TDDT и applicable coverage obligations не прошли self-check.

## Required Artifacts

Canonical placement: `fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/`.

Minimum table-heavy set:

- `source-row-inventory.md`;
- `source-table-normalization.md`;
- `dictionary-inventory.md`, если source/support задает справочник или фиксированный перечень;
- `test-design-decision-table.md`;
- `atomic-requirements-ledger.md`;
- `package-test-design-plan.md`;
- `coverage-gaps.md`, если есть `GAP-*`;
- `test-design-review.md`;
- `writer-quality-gate.md`;
- slim canonical test-case file in `test-cases/`.

## Hard Stops

Do not set `ready-for-review` when:

- handoff source row with `in_scope = yes | unclear` is missing from writer-side inventory;
- normalized row has no stable `source_property_id`;
- one normalization row mixes independent property classes;
- `metadata_only` or `gap_unclear` is linked to executable `TC-*`;
- observable source-backed behavior is hidden in `GAP-*`;
- normalized `dictionary-source` / reference-list row has no matching `dictionary-inventory.md` entry or no `DICT-*`/`GAP-*` downstream link;
- one `TC-*` is reused for several independent executable design rows;
- table artifacts contain unresolved extraction residue that changes expected behavior.

## Deep References

Use these formats for the exact table shape:

- `source-row-inventory-format.md`;
- `source-table-normalization-format.md`;
- `dictionary-inventory-format.md`;
- `test-design-decision-table-format.md`;
- `coverage-obligation-table-format.md`;
- `package-test-design-plan-format.md`;
- `test-design-review-format.md`;
- `writer-quality-gate-format.md`.

Use full `writer-output-format.md` only for validator-failure remediation, migration, audit, or when this runtime split is insufficient.
