# Source Row Inventory Format

`Source Row Inventory` - обязательная инвентаризация строк источника, если scope строится по таблицам полей, таблицам действий, XHTML/PDF/DOCX extraction или другому табличному источнику.

Цель inventory - доказать полноту переноса source rows до атомаризации. Агент сначала инвентаризирует все строки источника внутри подтвержденного scope, используя XHTML как primary machine-readable extraction source для таблиц, строк, списков, вложенных списков и перечней значений, затем нормализует их в `Source Table Normalization`, затем строит `Atomic Requirements Ledger`.

## Write Strategy

`source-row-inventory.md` is a generated table-heavy artifact. In clean/audit runs, write it through:

```powershell
python scripts\write_artifact_sections.py --manifest <manifest.json>
```

Do not first try a one-shot PowerShell/here-string/inline command. The stage session log must declare `## Artifact Write Strategy` before writing this artifact.

## Где Используется

Есть два обязательных места использования:

1. `source-row-inventory.md` в handoff-папке scope-а. Его создает `ft-scope-analyzer` до writer-а, если `source-parity-check.md` содержит row-level/table parity или scope явно основан на таблице полей/действий. Это независимый вход для writer-а.
2. `work/test-design/<scope-slug>/source-row-inventory.md`. Его создает writer как часть набора split test-design artifacts и сверяет с handoff inventory.

Writer не должен сам становиться единственным источником inventory для табличного scope-а: иначе он может потерять строку источника до атомаризации, а затем формально пройти собственную проверку полноты.

## Формат

Минимальная таблица:

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-001` | `WP-01` | `Сумма на руки` | `PDF p.46, row ...` | `GSR 1` | `yes` | `ATOM-001` |
| `SRC-002` | `WP-01` | `Скрытый internal attribute kladr` | `PDF p.52, row ...` | `GSR 115` | `yes` | `GAP-002` |

Для `prepared_compiler_contract_version: 3` эта же таблица обязана дополнительно
содержать typed registry columns:

| source_path | source_locator | bounded_source_text | source_context_class | candidate_id |
| --- | --- | --- | --- | --- |
| `fts/pkg/source/main.xhtml` | `/*/*[2]/*[68]` | `BSR 3. <полный ограниченный текст строки>` | `document-global-constraints` | `SRC-CAND-<24 hex>` |

`source_path`, `source_locator`, `bounded_source_text`, `source_context_class`,
nullable `candidate_id`, `requirement_codes` и нормализованный
`in_scope = yes | unclear | no` входят в hash-bound
`source-assertions.json/source_rows`. Compiler v3 требует точное совпадение
registry с inventory, а не только совпадение множества `SRC-*` ids. Правила
детерминированного candidate registry и bijection определены в
`references/agent/source-row-baseline-format.md`.

## Правила

- Одна строка inventory = одна строка или явный фрагмент source внутри подтвержденного scope.
- Для table/list-heavy scope source rows/list items извлекай в первую очередь из XHTML; DOCX остается source of truth для смысла, PDF - structural/visual cross-check.
- Если одна source row содержит несколько независимых свойств, inventory все равно хранит source row один раз, а `Source Table Normalization` может ссылаться на тот же `source_row_id` несколькими строками.
- Если одна source row содержит несколько `GSR`/`REQ` или несколько самостоятельных свойств, writer обязан добавить `Source Row Completeness Matrix` перед `Source Table Normalization`: один `source_row_id` должен быть разложен на отдельные `source_property_id`, а каждый `source_property_id` должен вести к `ATOM-*` или `GAP-*`.
- Handoff `source-row-inventory.md` должен создаваться до `prompt.scope-to-writer.md` / `prompt.scope-to-iteration.md` и передаваться как обязательный input, если `source-parity-check.md` содержит секцию `Table / Row Parity`.
- Writer-side `Source Row Inventory` должен сохранять все in-scope rows из handoff inventory. Нельзя удалять source row только потому, что writer не планирует писать по ней TC: используй `GAP-*` или явное out-of-scope решение.
- `ready-for-review` должен блокироваться, если writer-side inventory не содержит in-scope/unclear `source_row_id` из handoff `source-row-inventory.md`.
- `in_scope = yes` требует `mapped_atom_or_gap` с существующим `ATOM-*` или `GAP-*`.
- `in_scope = unclear` требует `GAP-*` или clarification question.
- `in_scope = no | out-of-scope` требует понятного решения scope, но не требует `ATOM-*`.
- В source-first v3 строки `in_scope = no` не удаляются из expected registry:
  они сохраняются как `scope_disposition = no`, имеют только
  `semantic_disposition = not-applicable` assertions и не создают executable
  obligations. Testable/ambiguous assertion на такой row блокируется.
- `bounded_source_text` — полный ограниченный текст именно этой source row из
  зарегистрированного UTF-8 extraction source. Нельзя подставлять фрагмент
  другой строки, даже если он встречается в том же файле.
- `requirement_codes` перечисляет точные коды этой row через `;`, включая
  PDF-only codes из parity evidence; при отсутствии кода используется
  `none_required`.
- Requirement codes должны сохраняться в том же смысле, что в source/parity artifact. Нельзя просто перенести `GSR N` рядом с другим полем или другим expected behavior.

## Blocking Defects

Writer не должен ставить `stage_status: ready-for-review`, если:

- для row-level/table parity нет handoff `source-row-inventory.md`;
- package-based writer output не содержит split artifact `work/test-design/<scope-slug>/source-row-inventory.md`;
- writer-side inventory потерял in-scope строку из handoff `source-row-inventory.md`;
- строка source внутри подтвержденного scope отсутствует в inventory;
- `Source Table Normalization` содержит `source_row_id`, которого нет в inventory;
- source row с несколькими `GSR`/`REQ` не разложена на отдельные `source_property_id` через `Source Row Completeness Matrix`;
- `in_scope = yes`, но нет `ATOM-*` или `GAP-*`;
- `mapped_atom_or_gap` ссылается на несуществующий `ATOM-*`;
- requirement code сохранен формально, но связан с другим полем, условием или expected behavior.
