# Prepared Source Evidence

- package_id: `autofin-search-clear-compiled-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-search-clear-compiler-v3-20260711/prepared-input/.autofin-search-clear-compiled-v3.compiled-evidence.md`
- source_sha256: `bb1b5f58269ac0bbda98b51782a7f7325d365bee83508c5c1d4e8ba4b3418da3`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## ATOM-001

ATOM-001 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает примененные фильтры поиска. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-001 | covered

- plan: PLAN-001 | WP-BSR32 | filters | BSR 32; SRC-001 | ATOM-001 | Проверить возврат измененного фильтра к initial/default state после `Очистить`. | positive-ui-action | reset | changed-filter-state | Фильтр сброшен к initial/default state. | source-backed | TC-BSR32-001 | covered

## ATOM-002

ATOM-002 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает примененные сортировки. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-002 | covered

- plan: PLAN-002 | WP-BSR32 | sorting | BSR 32; SRC-001 | ATOM-002 | Проверить возврат примененной сортировки к initial/default state после `Очистить`. | positive-ui-action | reset | changed-sort-state | Сортировка сброшена к initial/default state. | source-backed | TC-BSR32-002 | covered

## ATOM-003

ATOM-003 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает постраничность. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-003 | covered

- plan: PLAN-003 | WP-BSR32 | pagination | BSR 32; SRC-001 | ATOM-003 | Проверить возврат измененной постраничности к initial/default state после `Очистить`. | positive-ui-action | reset | changed-pagination-state | Постраничность сброшена к initial/default state. | source-backed | TC-BSR32-003 | covered

## ATOM-004

ATOM-004 | BSR 32 | SRC-001 | Нажатие `Очистить` очищает состояние выделения строк. | section 4.2; XHTML table_index=5 row `Очистить`; PDF page 8 | TC-BSR32-004 | covered

- plan: PLAN-004 | WP-BSR32 | row-selection | BSR 32; SRC-001 | ATOM-004 | Проверить возврат выделения строк к initial/default state после `Очистить`. | positive-ui-action | reset | selected-row-state | Выделение строк сброшено к initial/default state. | source-backed | TC-BSR32-004 | covered
