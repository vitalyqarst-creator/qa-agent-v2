# Source assertion semantic rule card

Единый gate автора/reviewer. Нет evidence — не `ready`: неизвестный смысл =
`ambiguous`, известный без исполнимого evidence = `dependency-blocked` + GAP.

| Claim | Evidence для `ready` |
| --- | --- |
| Literal UI action | Evidence содержит действие или однозначный locator; общий result text недостаточен. |
| Search/filter relational behavior | Pre-state fixture задаёт retained и excluded control rows; проверяются оба исхода. Допустимо непосредственно до поиска зафиксировать target/control rows в той же нефильтрованной таблице: это independent pre-state для сравнения состава после фильтра. Такой same-table pre-search capture доказывает только реляционное filter behavior (`retained`/`excluded`), но не correctness исходного mapping/type/value; mapping gate применяется отдельно. |
| Requiredness | Source задаёт validation trigger: blur, submit/save/search либо другое точное действие. |
| `always` / «всегда» | Один oracle подтверждён минимум в двух разных релевантных pre-state. |
| Negative partition | Invalid cause изолирована от valid и других invalid causes; один rejection oracle. |
| Pure declared metadata type without authorized manual interface | Если source только декларирует внутренний data type/metadata и не задаёт доступный manual UI/API/authorized artifact, assertion для manual UI scope получает `not-applicable` с source-backed rationale, без executable obligation и без GAP, созданного лишь из-за отсутствия интерфейса. |
| Visible mapping / rendered type / format | Если type, mapping или format наблюдаемы в UI/results/export/другом разрешённом интерфейсе, behavior остаётся `testable`. Expected entity/column/type/value берётся из названного hash-bound authoritative fixture/source. Capture ожидаемого mapping/type из того же наблюдаемого result state self-referential и mapping/type не доказывает; без независимого oracle source используется `dependency-blocked` + GAP, а не `not-applicable`. |

Exact-сверяй цепочку `canonical_statement entity/property → action
target → oracle entity/column`. Смена entity, колонки, code или data type —
blocking copy/paste-drift finding. Assertion/ledger/plan/будущий TC не являются
независимым evidence. Approved clarification допустим только через manifest-v4
typed clause binding. Descriptive determinacy ratio не ослабляет gate.
