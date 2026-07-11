# Prepared Source Evidence

- package_id: `autofin-search-clear-compiled-v4`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-search-clear-compiler-v4-20260711/prepared-input/.autofin-search-clear-compiled-v4.compiled-evidence.md`
- source_sha256: `5bd71ebd88aabcc4d138e957e071ad18a1977f928dba3aad237b93f576814cb1`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## OBL-001

- obligation: OBL-001 | WP-BSR32 | SRC-001.P01 | ATOM-001 | filter-reset | clear-applied-filter | Нажатие `Очистить` очищает примененное значение фильтра. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-001 | covered | Exact filter fields and default values are intentionally not asserted.
- atom: ATOM-001 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает примененные фильтры поиска. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-001 | covered

- plan: PLAN-001 | WP-BSR32 | filters | BSR 32; SRC-001 | ATOM-001 | Проверить возврат измененного фильтра к initial/default state после `Очистить`. | positive-ui-action | reset | changed-filter-state | Фильтр сброшен к initial/default state. | source-backed | TC-BSR32-001 | covered

## OBL-002

- obligation: OBL-002 | WP-BSR32 | SRC-001.P02 | ATOM-002 | sorting-reset | clear-applied-sort | Нажатие `Очистить` очищает примененную сортировку. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-002 | covered | Exact default sort is intentionally not asserted.
- atom: ATOM-002 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает примененные сортировки. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-002 | covered

- plan: PLAN-002 | WP-BSR32 | sorting | BSR 32; SRC-001 | ATOM-002 | Проверить возврат примененной сортировки к initial/default state после `Очистить`. | positive-ui-action | reset | changed-sort-state | Сортировка сброшена к initial/default state. | source-backed | TC-BSR32-002 | covered

## OBL-003

- obligation: OBL-003 | WP-BSR32 | SRC-001.P03 | ATOM-003 | pagination-reset | clear-pagination-state | Нажатие `Очистить` очищает постраничность. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-003 | covered | Page size, page count and row count are intentionally not asserted.
- atom: ATOM-003 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает постраничность. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-003 | covered

- plan: PLAN-003 | WP-BSR32 | pagination | BSR 32; SRC-001 | ATOM-003 | Проверить возврат измененной постраничности к initial/default state после `Очистить`. | positive-ui-action | reset | changed-pagination-state | Постраничность сброшена к initial/default state. | source-backed | TC-BSR32-003 | covered

## OBL-004

- obligation: OBL-004 | WP-BSR32 | SRC-001.P04 | ATOM-004 | row-selection-reset | clear-selected-row-state | Нажатие `Очистить` очищает состояние выделения строк. | BSR 32; SRC-001; section 4.2; PDF page 8 | TC-BSR32-004 | covered | No persistence or backend state is asserted.
- atom: ATOM-004 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает состояние выделения строк. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-004 | covered

- plan: PLAN-004 | WP-BSR32 | row-selection | BSR 32; SRC-001 | ATOM-004 | Проверить возврат выделения строк к initial/default state после `Очистить`. | positive-ui-action | reset | selected-row-state | Выделение строк сброшено к initial/default state. | source-backed | TC-BSR32-004 | covered
