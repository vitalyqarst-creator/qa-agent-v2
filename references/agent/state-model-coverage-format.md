# State Model Coverage Format

`state-model.md` - split artifact для сложных lifecycle/status/form-state требований. Используй его, когда scope содержит несколько состояний, событий, разрешенных/запрещенных переходов, повторные действия или side effects переходов.

## State Catalog

| state_id | state_name | source_ref | entry_condition | observable_marker | notes |
| --- | --- | --- | --- | --- | --- |
| `ST-001` | `Черновик` | `GSR 10` | `Заявка создана, не отправлена` | `Статус = Черновик` | `-` |

## Event Catalog

| event_id | event_name | source_ref | actor_or_trigger | preconditions | observable_artifact |
| --- | --- | --- | --- | --- | --- |
| `EV-001` | `Следующий шаг` | `GSR 142` | `Пользователь` | `Обязательные поля валидны` | `Открыт следующий раздел` |

## Transition Table

| transition_id | from_state | event | to_state | expected_behavior | allowed | source_ref | linked_tc_or_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TR-001` | `ST-001` | `EV-001` | `ST-002` | `Открывается следующий раздел` | `yes` | `GSR 142` | `TC-...` |
| `TR-002` | `ST-002` | `EV-001` | `-` | `Повторное действие не описано` | `unclear` | `GSR 142` | `GAP-...` |

## Rules

- Покрывай source-backed allowed transitions, forbidden transitions, repeated actions и irreversible transitions.
- Не создавай states/events по UX-догадке. Если state marker или expected state не наблюдаемы, фиксируй `GAP-*`.
- State model не заменяет decision table: если результат зависит от комбинации условий внутри transition, нужна decision table или ссылка на нее.
- Каждый transition с `allowed = yes | no` должен иметь `TC-*` или `GAP-*`; `allowed = unclear` всегда требует `GAP-*`.

