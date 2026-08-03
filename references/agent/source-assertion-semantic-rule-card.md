# Source assertion semantic rule card

Единый gate автора/reviewer. Нет evidence — не `ready`: неизвестный смысл =
`ambiguous`, известный без исполнимого evidence = `dependency-blocked` + GAP.

Если approved clarification явно делает календарную границу включительной, source
assertion и связанный obligation обязаны сохранить включённую граничную дату; сокращение
`до даты` вместо `до или в день даты` считается семантической потерей.

Если assertion прямо сообщает, что точный UI-отклик требует калибровки, связанный
obligation обязан иметь `review_notes=candidate-ui-calibration` и
`oracle_source=not_found`; одновременно объявлять такой oracle source-backed запрещено.

Открытый `missing-source-definition` GAP, связанный с отдельным non-testable
assertion, является жёсткой границей: reviewer не требует переносить перечисленные
в GAP неопределённые элементы в executable sibling той же строки.

Именованный verified fixture проецируется в condition/action/oracle точными query и
expected literals. Формулировки «соответствующее значение» и «значение из fixture»
без точного значения недостаточны. Typed-свойство ячейки не владеет BSR-кодом,
который определяет другое поведение; например, `О` владеет requiredness, а BSR про
visibility — отдельной assertion-chain.

| Claim | Evidence для `ready` |
| --- | --- |
| Literal UI action | Evidence содержит действие или однозначный locator; общий result text недостаточен. |
| Search/filter relational behavior | Pre-state fixture задаёт retained и excluded control rows; проверяются оба исхода. Допустимо непосредственно до поиска зафиксировать target/control rows в той же нефильтрованной таблице: это independent pre-state для сравнения состава после фильтра. Такой same-table pre-search capture доказывает только реляционное filter behavior (`retained`/`excluded`), но не correctness исходного mapping/type/value; mapping gate применяется отдельно. |
| Requiredness | Source задаёт validation trigger: blur, submit/save/search либо другое точное действие. |
| `always` / «всегда» | Два pre-state обязательны только когда эта же bounded source row явно называет оба состояния. Иначе достаточно одного прямого open-and-observe oracle; заимствовать несвязанный переключатель запрещено. |
| `O=Нет` / `optional` для action control (`Кнопка`, `виджет`) | Это структурная неприменимость required-value semantics, а не самостоятельное поведение: отдельные ASSERT/OBL/TC и UI-calibration candidate не создаются. Наблюдаемое действие покрывается явными click/add/delete требованиями; «не нажимать кнопку» не является отдельной проверкой. |
| `R=Нет` для action control (`Кнопка`, `виджет`) | Это структурная неприменимость value-editing, а не самостоятельное поведение: отдельные ASSERT/OBL/TC не создаются. Наблюдаемое действие кнопки/виджета покрывается его явными click/add/delete требованиями; попытка вводить текст в action control запрещена как неисполнимый шаг. |
| Negative partition | Invalid cause изолирована от valid и других invalid causes; один rejection oracle. |
| Pure declared metadata type without authorized manual interface | Если source только декларирует внутренний data type/metadata и не задаёт доступный manual UI/API/authorized artifact, assertion для manual UI scope получает `not-applicable` с source-backed rationale, без executable obligation и без GAP, созданного лишь из-за отсутствия интерфейса. |
| Visible mapping / rendered type / format | Если type, mapping или format наблюдаемы в UI/results/export/другом разрешённом интерфейсе, behavior остаётся `testable`. Expected entity/column/type/value берётся из названного hash-bound authoritative fixture/source. Capture ожидаемого mapping/type из того же наблюдаемого result state self-referential и mapping/type не доказывает; без независимого oracle source используется `dependency-blocked` + GAP, а не `not-applicable`. |

Exact-сверяй цепочку `canonical_statement entity/property → action
target → oracle entity/column`. Смена entity, колонки, code или data type —
blocking copy/paste-drift finding. Assertion/ledger/plan/будущий TC не являются
независимым evidence. Approved clarification допустим только через manifest-v4
typed clause binding. Descriptive determinacy ratio не ослабляет gate.
