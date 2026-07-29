# Negative Oracle Inventory: 07-4.3-client-addresses

## Summary

- `scope_slug`: `4-3-client-addresses`
- `status`: `candidate`
- `blocking_gap`: `GAP-003` for exact UI oracle

| obligation_id | source_ref | field | invalid_class | representative_value | known_oracle | decision |
|---|---|---|---|---|---|---|
| `SO-NEG-001` | `BSR 124` | Почтовый индекс / адрес регистрации | fewer than 6 digits | `12345` | numeric length requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-002` | `BSR 124` | Почтовый индекс / адрес регистрации | more than 6 digits | `1234567` | numeric length requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-003` | `BSR 124` | Почтовый индекс / адрес регистрации | non-numeric character | `12345A` | numeric-only requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-004` | `BSR 132` | Корпус / адрес регистрации | non-numeric character | `12A` | numeric-only requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-005` | `BSR 134` | Квартира / адрес регистрации | non-numeric character | `12A` | numeric-only requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-006` | `BSR 159` | Квартира / адрес фактического места жительства | non-numeric character | `12A` | numeric-only requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-007` | `BSR 161` | Почтовый индекс / адрес фактического места жительства | fewer than 6 digits | `12345` | numeric length requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-008` | `BSR 161` | Почтовый индекс / адрес фактического места жительства | more than 6 digits | `1234567` | numeric length requirement exists; exact message/trigger missing | candidate |
| `SO-NEG-009` | `BSR 161` | Почтовый индекс / адрес фактического места жительства | non-numeric character | `12345A` | numeric-only requirement exists; exact message/trigger missing | candidate |

## Decision

Не использовать эти строки для точных expected results, пока не закрыт `GAP-003`. Допустимая будущая формулировка без уточнения: система не должна принимать значение, нарушающее требование формата; точный текст ошибки не утвержден.
