# Atomic Requirements Ledger

| atom_id | source_ref | req_id | atomic_statement | coverage_status | linked_tc_or_gap | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `SRC-001` | `no_requirement_code:SRC-001` | Виджет типа `Список` использует значения из справочника. | `gap` | `GAP-002` | Scope не идентифицирует конкретный справочник и полный inventory значений. |
| `ATOM-002` | `SRC-001` | `no_requirement_code:SRC-001` | В виджете типа `Список` возможно выбрать только одно значение. | `covered` | `TC-WIDGET-SELECTION-TYPES-001` | Проверяется заменой первого выбранного значения вторым. |
| `ATOM-003` | `SRC-002` | `no_requirement_code:SRC-002` | Виджет типа `Список с множественным выбором` использует значения из справочника. | `gap` | `GAP-002` | Scope не идентифицирует конкретный справочник и полный inventory значений. |
| `ATOM-004` | `SRC-002` | `no_requirement_code:SRC-002` | В виджете типа `Список с множественным выбором` возможно выбрать несколько значений. | `covered` | `TC-WIDGET-SELECTION-TYPES-002` | Проверяется одновременным отображением двух выбранных значений. |
| `ATOM-005` | `SRC-003` | `no_requirement_code:SRC-003` | По умолчанию значения в виджетах отсутствуют. | `covered` | `TC-WIDGET-SELECTION-TYPES-003` | Покрывается UI-наблюдением отсутствия выбранного или заполненного значения. |
| `ATOM-006` | `SRC-003` | `no_requirement_code:SRC-003` | Отсутствующие значения в виджетах интерпретируются как `NULL`. | `unclear` | `GAP-001` | Внутренняя интерпретация `NULL` не имеет разрешенного UI-only observable artifact в данном scope. |
