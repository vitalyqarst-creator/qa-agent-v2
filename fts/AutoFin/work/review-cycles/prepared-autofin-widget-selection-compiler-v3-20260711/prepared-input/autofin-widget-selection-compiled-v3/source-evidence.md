# Prepared Source Evidence

- package_id: `autofin-widget-selection-compiled-v3`

## Compiled fidelity projection

- source_path: `fts/AutoFin/work/review-cycles/prepared-autofin-widget-selection-compiler-v3-20260711/prepared-input/.autofin-widget-selection-compiled-v3.compiled-evidence.md`
- source_sha256: `986ae4e089e5b22006dc8d6f22d6cb0d503d3e0f11ca28764a3fdbaaab0199c0`
- selectors: `full-explicit`

# Compiled Prepared Evidence

## ATOM-001

ATOM-001 | SRC-001 | no_requirement_code:SRC-001 | Виджет типа `Список` использует значения из справочника. | gap | GAP-002 | Scope не идентифицирует конкретный справочник и полный inventory значений.

- plan: PD-001 | WP-01 | dictionary-source | SRC-001 | ATOM-001 | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | gap | dictionary-provenance | unidentified dictionary | none_required:gap | GAP-002 | GAP-002 | gap

## ATOM-002

ATOM-002 | SRC-001 | no_requirement_code:SRC-001 | В виджете типа `Список` возможно выбрать только одно значение. | covered | TC-WIDGET-SELECTION-TYPES-001 | Проверяется заменой первого выбранного значения вторым.

- plan: PD-002 | WP-01 | selection-cardinality | SRC-001 | ATOM-002 | Последовательно выбрать два разных доступных значения в single-select fixture. | positive | single-selection | two distinct fixture values | После второго выбора в виджете отображается ровно одно выбранное значение. | FT4AutoFinFinal; SRC-001 | TC-WIDGET-SELECTION-TYPES-001 | covered

## ATOM-003

ATOM-003 | SRC-002 | no_requirement_code:SRC-002 | Виджет типа `Список с множественным выбором` использует значения из справочника. | gap | GAP-002 | Scope не идентифицирует конкретный справочник и полный inventory значений.

- plan: PD-003 | WP-01 | dictionary-source | SRC-002 | ATOM-003 | Не заявлять происхождение значений без идентифицированного справочника и полного inventory. | gap | dictionary-provenance | unidentified dictionary | none_required:gap | GAP-002 | GAP-002 | gap

## ATOM-004

ATOM-004 | SRC-002 | no_requirement_code:SRC-002 | В виджете типа `Список с множественным выбором` возможно выбрать несколько значений. | covered | TC-WIDGET-SELECTION-TYPES-002 | Проверяется одновременным отображением двух выбранных значений.

- plan: PD-004 | WP-01 | selection-cardinality | SRC-002 | ATOM-004 | Выбрать два разных доступных значения в multi-select fixture. | positive | multiple-selection | two distinct fixture values | Оба выбранных значения одновременно отображаются в виджете. | FT4AutoFinFinal; SRC-002 | TC-WIDGET-SELECTION-TYPES-002 | covered

## ATOM-005

ATOM-005 | SRC-003 | no_requirement_code:SRC-003 | По умолчанию значения в виджетах отсутствуют. | covered | TC-WIDGET-SELECTION-TYPES-003 | Покрывается UI-наблюдением отсутствия выбранного или заполненного значения.

- plan: PD-005 | WP-01 | default-value | SRC-003 | ATOM-005 | Проверить новый fixture-виджет до первого пользовательского ввода. | positive | empty-default | new untouched widget | В виджете отсутствует выбранное или заполненное значение. | FT4AutoFinFinal; SRC-003 | TC-WIDGET-SELECTION-TYPES-003 | covered

## ATOM-006

ATOM-006 | SRC-003 | no_requirement_code:SRC-003 | Отсутствующие значения в виджетах интерпретируются как `NULL`. | unclear | GAP-001 | Внутренняя интерпретация `NULL` не имеет разрешенного UI-only observable artifact в данном scope.

- plan: PD-006 | WP-01 | persistence | SRC-003 | ATOM-006 | Не заявлять внутреннее представление `NULL` без API/DB/persistence evidence. | gap | internal-null | unobservable internal value | none_required:gap | GAP-001 | GAP-001 | unclear

## GAP-001

source_refs: SRC-003; ATOM-006
The selected sources state that absent widget values are interpreted as `NULL`, but the confirmed scope excludes persistence, database, API and async artifacts that could observe internal null semantics.
Preserve for reviewer and future scope expansion; do not assert internal `NULL` in UI-only TC.

## GAP-002

source_refs: SRC-001; SRC-002; ATOM-001; ATOM-003
The selected scope does not identify concrete dictionaries or provide an independent complete inventory for source-origin assertions.
Preserve dictionary provenance as a gap; cardinality remains executable with two distinct fixture values.
