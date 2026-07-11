# Prepared Source Evidence

- package_id: `autofin-widget-selection-compiled-v4`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-compiler-v4-20260711/prepared-input/.autofin-widget-selection-compiled-v4.compiled-evidence.md`
- source_sha256: `3dfdccc44280c3b6364532fed6b07ed47b9eefb12d18fc1977acdd37286d55e6`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## OBL-001

- obligation: OBL-001 | WP-01 | SRC-001 | ATOM-001 | dictionary-source | dictionary-provenance | Не заявлять состав справочника без идентифицированного source inventory. | SRC-001 | GAP-002 | gap | Точный справочник не задан.
- atom: ATOM-001 | SRC-001 | no_requirement_code:SRC-001 | Виджет типа `Список` использует значения из справочника. | gap | GAP-002 | Scope не идентифицирует конкретный справочник и полный inventory значений.

- plan: PD-001 | WP-01 | dictionary-source | SRC-001 | ATOM-001 | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | gap | dictionary-provenance | unidentified dictionary | none_required:gap | GAP-002 | GAP-002 | gap

## OBL-002

- obligation: OBL-002 | WP-01 | SRC-001 | ATOM-002 | selection-cardinality | single-selection | После второго выбора в виджете остаётся ровно одно выбранное значение. | SRC-001 | TC-WIDGET-SELECTION-TYPES-001 | covered | Проверка cardinality, не состава справочника.
- atom: ATOM-002 | SRC-001 | no_requirement_code:SRC-001 | В виджете типа `Список` возможно выбрать только одно значение. | covered | TC-WIDGET-SELECTION-TYPES-001 | Проверяется заменой первого выбранного значения вторым.

- plan: PD-002 | WP-01 | selection-cardinality | SRC-001 | ATOM-002 | Последовательно выбрать два разных доступных значения в single-select fixture. | positive | single-selection | two distinct fixture values | После второго выбора в виджете отображается ровно одно выбранное значение. | FT4AutoFinFinal; SRC-001 | TC-WIDGET-SELECTION-TYPES-001 | covered

## OBL-003

- obligation: OBL-003 | WP-01 | SRC-002 | ATOM-003 | dictionary-source | dictionary-provenance | Не заявлять состав справочника без идентифицированного source inventory. | SRC-002 | GAP-002 | gap | Точный справочник не задан.
- atom: ATOM-003 | SRC-002 | no_requirement_code:SRC-002 | Виджет типа `Список с множественным выбором` использует значения из справочника. | gap | GAP-002 | Scope не идентифицирует конкретный справочник и полный inventory значений.

- plan: PD-003 | WP-01 | dictionary-source | SRC-002 | ATOM-003 | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | gap | dictionary-provenance | unidentified dictionary | none_required:gap | GAP-002 | GAP-002 | gap

## OBL-004

- obligation: OBL-004 | WP-01 | SRC-002 | ATOM-004 | selection-cardinality | multiple-selection | Два выбранных значения одновременно отображаются в виджете. | SRC-002 | TC-WIDGET-SELECTION-TYPES-002 | covered | Минимальная репрезентативная проверка multiple selection.
- atom: ATOM-004 | SRC-002 | no_requirement_code:SRC-002 | В виджете типа `Список с множественным выбором` возможно выбрать несколько значений. | covered | TC-WIDGET-SELECTION-TYPES-002 | Проверяется одновременным отображением двух выбранных значений.

- plan: PD-004 | WP-01 | selection-cardinality | SRC-002 | ATOM-004 | Выбрать два разных доступных значения в multi-select fixture. | positive | multiple-selection | two distinct fixture values | Оба выбранных значения одновременно отображаются в виджете. | FT4AutoFinFinal; SRC-002 | TC-WIDGET-SELECTION-TYPES-002 | covered

## OBL-005

- obligation: OBL-005 | WP-01 | SRC-003 | ATOM-005 | default-value | visible-empty-default | До первого ввода в виджете нет выбранного или заполненного значения. | SRC-003 | TC-WIDGET-SELECTION-TYPES-003 | covered | Только UI-наблюдение.
- atom: ATOM-005 | SRC-003 | no_requirement_code:SRC-003 | По умолчанию значения в виджетах отсутствуют. | covered | TC-WIDGET-SELECTION-TYPES-003 | Покрывается UI-наблюдением отсутствия выбранного или заполненного значения.

- plan: PD-005 | WP-01 | default-value | SRC-003 | ATOM-005 | Проверить новый fixture-виджет до первого пользовательского ввода. | positive | empty-default | new untouched widget | В виджете отсутствует выбранное или заполненное значение. | FT4AutoFinFinal; SRC-003 | TC-WIDGET-SELECTION-TYPES-003 | covered

## OBL-006

- obligation: OBL-006 | WP-01 | SRC-003 | ATOM-006 | persistence | internal-null-interpretation | Не заявлять внутреннее `NULL` без API/DB/persistence evidence. | SRC-003 | GAP-001 | unclear | Внутреннее значение не наблюдается через UI.
- atom: ATOM-006 | SRC-003 | no_requirement_code:SRC-003 | Отсутствующие значения в виджетах интерпретируются как `NULL`. | unclear | GAP-001 | Внутренняя интерпретация `NULL` не имеет разрешенного UI-only observable artifact в данном scope.

- plan: PD-006 | WP-01 | persistence | SRC-003 | ATOM-006 | Не заявлять внутреннее представление `NULL` без API/DB/persistence evidence. | gap | internal-null | unobservable internal value | none_required:gap | GAP-001 | GAP-001 | unclear

## GAP-001

source_refs: SRC-003; ATOM-006
The selected sources state that absent widget values are interpreted as `NULL`, but the confirmed scope excludes persistence, database, API and async artifacts that could observe internal null semantics.
Preserve for reviewer and future scope expansion; do not assert internal `NULL` in UI-only TC.

## GAP-002

source_refs: SRC-001; SRC-002; ATOM-001; ATOM-003
The selected scope does not identify concrete dictionaries or provide an independent complete inventory for source-origin assertions.
Preserve dictionary provenance as a gap; cardinality remains executable with two distinct fixture values.
