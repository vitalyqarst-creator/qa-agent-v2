# Requiredness Oracle Inventory: 07-4.3-client-addresses

## Summary

- `scope_slug`: `4-3-client-addresses`
- `status`: `candidate`
- `blocking_gap`: `GAP-003` for exact UI oracle

| obligation_id | source_ref | field | condition | known_oracle | decision |
|---|---|---|---|---|---|
| `SO-REQ-001` | `BSR 117` | Адрес регистрации | DaData/manual-off address input must include at least region and house | requiredness exists; exact empty-field oracle missing | candidate |
| `SO-REQ-002` | `BSR 117` | Квартира inside Адрес регистрации | address has no apartment and private-house flag is not set | red highlight and hint are source-backed for missing apartment in address field | candidate |
| `SO-REQ-003` | `BSR 125` | Регион / адрес регистрации | manual mode is `Да` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-004` | `BSR 127` | Населенный пункт / адрес регистрации | manual mode is `Да` and Город is empty | conditional mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-005` | `BSR 128` | Город / адрес регистрации | manual mode is `Да` and Населенный пункт is empty | conditional mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-006` | `BSR 130` | Дом / адрес регистрации | manual mode is `Да` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-007` | `BSR 133` | Квартира / адрес регистрации | `Клиент зарегистрирован в частном доме = Нет` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-008` | `BSR 142` | Адрес фактического места жительства | same-address flag is `Нет` and manual mode is off | requiredness exists; exact empty-field oracle missing | candidate |
| `SO-REQ-009` | `BSR 142` | Квартира inside Адрес фактического места жительства | factual address has no apartment and private-house flag is not set | red highlight and hint are source-backed for missing apartment in address field | candidate |
| `SO-REQ-010` | `BSR 150` | Регион / адрес фактического места жительства | factual manual mode is `Да` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-011` | `BSR 153` | Город / адрес фактического места жительства | factual manual mode is `Да` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-012` | `BSR 154` | Улица / адрес фактического места жительства | factual manual mode is `Да` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-013` | `BSR 155` | Дом / адрес фактического места жительства | factual manual mode is `Да` | field mandatory; exact empty-field oracle missing | candidate |
| `SO-REQ-014` | `BSR 157` | Квартира / адрес фактического места жительства | `Клиент проживает в частном доме = Нет` | field mandatory; exact empty-field oracle missing | candidate |

## Decision

Инвентарь фиксирует проверяемые обязанности scope, но не заменяет source assertions. Для тест-кейсов запрещено придумывать точные сообщения валидации там, где они не заданы.
