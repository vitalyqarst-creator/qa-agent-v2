# Source Normalization Diagnostic Format

`source-normalization-diagnostic.md` - диагностический артефакт для проверки нормализации источника до создания `Atomic Requirements Ledger`, `Package Test Design Plan` и `TC-*`.

Используй этот формат, когда нужно проверить, способен ли агент корректно разложить строки ФТ на атомарные source properties без генерации полного набора тест-кейсов.

Если `source-normalization-diagnostic.md` лежит в handoff-папке рядом с `source-row-inventory.md` и передается как input следующему writer/iteration этапу, он больше не считается выборочным spot-check. В этом случае diagnostic обязан покрывать все строки `source-row-inventory.md` с `in_scope = yes` и `in_scope = unclear`.

## Write Strategy

Diagnostic artifacts are generated/table-heavy artifacts. For clean runs, write them through:

```powershell
python scripts\write_artifact_sections.py --manifest <manifest.json>
```

Do not first try a one-shot PowerShell/here-string/inline command. The session log must include `## Artifact Write Strategy` before the first write and must name `scripts/write_artifact_sections.py`.

## Required Sections

Диагностический файл должен содержать только проверку нормализации и не должен создавать downstream coverage:

1. `Source Row Completeness Matrix`
2. `Source Table Normalization`
3. `Self-check`

## Source Row Completeness Matrix

| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision | diagnostic_atom_status |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-005` | `GSR 9` | `SRC-005.P01; SRC-005.P02; SRC-005.P03` | `-` | `GAP-001; GAP-002; GAP-003` | `split-complete` | `not-created` |

Rules:

- `normalized_property_ids` must list every `source_property_id` created for the source row.
- If same-directory `source-row-inventory.md` exists, every inventory row with `in_scope = yes` or `in_scope = unclear` must appear in this matrix.
- If same-directory `source-row-inventory.md` exists, `source_requirement_codes` must preserve every `GSR-*` / `REQ-*` code from the matching inventory row. Do not drop a code because the row is "only diagnostic" or because the behavior routes to `GAP-*`.
- If the diagnostic does not create `ATOM-*`, use `linked_atoms = -`.
- If the diagnostic does not create `ATOM-*`, set `diagnostic_atom_status = not-created`.
- If behavior is not directly testable from the available source, use `gap_ids`.
- Do not use placeholder gaps such as `GAP-900` to mean "atoms were not created". That is a diagnostic state, not a coverage gap.
- One `source_row_id` may map to several `source_property_id` values even when there is only one `GSR`.

## Source Table Normalization

Use the canonical columns from `source-table-normalization-format.md`:

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms | source_column | source_text_fragment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SRC-005` | `SRC-005.P01` | `WP-01` | `Срок кредитования` | `dictionary-source` | `справочник доступен` | `значение берется из справочника` | `GSR 9` | `PDF p.47` | `high` | `GAP-001` | `-` | `Тип значения` | `Значение из справочника «Сроки кредитования»` |
| `SRC-005` | `SRC-005.P02` | `WP-01` | `Срок кредитования` | `max-boundary` | `известен product catalog max` | `максимальное значение берется из продуктового каталога` | `GSR 9` | `PDF p.47` | `high` | `GAP-002` | `-` | `Примечание` | `Максимальное значение из Продуктового каталога` |
| `SRC-005` | `SRC-005.P03` | `WP-01` | `Срок кредитования` | `min-boundary` | `известен product catalog min` | `минимальное значение берется из продуктового каталога` | `GSR 9` | `PDF p.47` | `high` | `GAP-003` | `-` | `Примечание` | `Минимальное значение из Продуктового каталога` |

Rules:

- Do not create `ATOM-*`, `Package Test Design Plan`, `TC-*`, review artifacts or `signed-off` state in a diagnostic-only run.
- Diagnostic normalization table must add `source_column` and `source_text_fragment`. These columns prove which source column and exact text fragment produced each normalized property.
- Do not combine different semantic property classes in one row. Split dictionary source, min boundary, max boundary, visibility, requiredness, editability, format and integration behavior.
- Do not keep a row like `term_dictionary_and_bounds`; split it even if all resulting rows point to `GAP-*`.
- `expected_behavior` must contain the actual behavior from source. Do not write placeholders such as `follows GSR 10`, `according to GSR 10` or `по GSR 10`.
- Integration/API/model/DB/RabbitMQ/async behavior must be split into observable behavior and internal effect. Internal effects require a real functional `GAP-*` unless source provides a visible artifact, log, API, DB or queue evidence rule.
- Do not put `GAP-900` or another placeholder in `gap_id`. Use real scope gaps only; use `diagnostic_atom_status` for diagnostic-only atom absence.
- Every `source_property_id` in `Source Table Normalization` must appear in `Source Row Completeness Matrix`.
- Every `normalized_property_ids` value in the matrix must exist in `Source Table Normalization`.
- If same-directory `source-row-inventory.md` exists, every inventory row with `in_scope = yes` or `in_scope = unclear` must have at least one Source Table Normalization row.
- If same-directory `source-row-inventory.md` exists, every `GSR-*` / `REQ-*` code from an in-scope/unclear inventory row must appear in at least one Source Table Normalization row for the same `source_row_id`.

## Self-check

Minimum content:

- `status`: `pass` or `fail`
- `checked_rows`: list of source rows
- `known_gaps`: list of `GAP-*`
- `ready_for_writer`: `yes` only if every selected row is split into atomic source properties

If self-check is failed, do not continue to writer-pass.

## Validator

Run:

```powershell
python scripts\validate_agent_artifacts.py --root <package-or-diagnostic-file> --json --fail-on warning
```

Validator checks:

- required diagnostic sections;
- canonical `Source Table Normalization`;
- completeness against same-directory `source-row-inventory.md` for all `in_scope = yes/unclear` rows and all their `GSR-*` / `REQ-*` codes;
- mixed property classes;
- `source_property_id` completeness between matrix and normalization;
- placeholder diagnostic gaps such as `GAP-900`;
- missing `source_column` / `source_text_fragment`;
- `expected_behavior` that only points to a `GSR` instead of stating behavior;
- integration/internal rows without observable behavior or real `GAP-*`;
- failed diagnostic self-check.
