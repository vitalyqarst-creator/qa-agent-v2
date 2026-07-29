# Scope Clarification Requests: 07-4.3-client-addresses

## Контекст

- `ft_slug`: `AutoFin/PostFinal-v2-rc5`
- `scope_slug`: `4-3-client-addresses`
- `stage`: `ft-scope-analyzer`
- Coverage gaps: `scope-coverage-gaps.md`
- Workflow status: `blocked-input-resolved-rerun-required`

Этот файл фиксирует вопросы по `GAP-*` и место для ответа БА. Ответы из этого файла не являются утвержденным evidence, пока агент не переведет запись в `response_status: answered` с согласованными `authority` и `response_type`.

## Как Заполнять

- БА заполняет только блок `Ответ БА`.
- `response_status`, `response_type` и `updated_at` заполняет агент после получения ответа.
- Не удаляйте `clarification_id`, `gap_id`, scope, ссылки и вопрос.
- Если ответ заменен более новым, агент установит старой карточке `response_status = superseded` и добавит новую карточку с тем же `gap_id`.

## Clarification Requests

### CLR-001 — GAP-001

```yaml
clarification_id: CLR-001
gap_id: GAP-001
scope_slug: 4-3-client-addresses
requirement_codes: BSR 116; BSR 118; BSR 119; BSR 125; BSR 141; BSR 143; BSR 144; BSR 150; BSR 324
related_ft_reference: AGENT-NOTES.md, "Условный Контекст DaData"; Таблица 4, строки 34/37/47/50; связанное BSR 324
source_quote: Если подтверждённый scope содержит поле, для которого ФТ прямо задаёт интеграцию с DaData, используй `work/vendor-references/dadata-reference.md` как внешний vendor reference.
question: Нужно ли добавить в rc5-пакет файл `work/vendor-references/dadata-reference.md`, либо можно выполнять анализ блока адресов клиента без отдельного vendor reference по DaData?
needed_for: Разблокировать анализ DaData-полей адреса регистрации и фактического адреса, справочника регионов и раскладки адреса по BSR 324.
blocking: yes
requested_from: user
authority: user
response_status: answered
response_type: user-confirmed
updated_at: 2026-07-26
```

**Текст из ФТ/source:** AGENT-NOTES.md: если подтвержденный scope содержит поле с интеграцией DaData, должен использоваться `work/vendor-references/dadata-reference.md` как внешний vendor reference.

**Вопрос:** Нужно ли добавить в rc5-пакет файл `work/vendor-references/dadata-reference.md`, либо можно выполнять анализ блока адресов клиента без отдельного vendor reference по DaData?

**Что станет возможно после ответа:** Разблокировать анализ DaData-полей адреса регистрации и фактического адреса, справочника регионов и раскладки адреса по `BSR 324`.

#### Ответ БА (`user_response`)

```text
Файл `work/vendor-references/dadata-reference.md` добавлен в rc5-пакет. Анализ блока адресов клиента должен выполняться с этим package-local vendor reference.
```

### CLR-002 — GAP-002

```yaml
clarification_id: CLR-002
gap_id: GAP-002
scope_slug: 4-3-client-addresses
requirement_codes: BSR 115-161; BSR 324
related_ft_reference: support/client-addresses-approved-clarifications-v3.md, Context and CLR-ADDR-001..005
source_quote: "support v3: scope_slug = application-card-client-addresses; Основной ФТ = source/PostFinal-v2/PostFinal-v2.docx. Current rc5 handoff: scope_slug = 4-3-client-addresses; source = source/PostFinal-v2.docx."
question: Подтверждает ли БА, что `support/client-addresses-approved-clarifications-v3.md` применим к текущему rc5 scope `4-3-client-addresses`, несмотря на отличающиеся metadata по scope и пути основного ФТ?
needed_for: Использовать `CLR-ADDR-001..005` как утвержденные уточнения для текущего rc5 handoff и связать их с source assertions.
blocking: yes
requested_from: user
authority: user
response_status: answered
response_type: user-confirmed
updated_at: 2026-07-26
```

**Текст из ФТ/source:** В `support/client-addresses-approved-clarifications-v3.md` указано `scope_slug: application-card-client-addresses` и основной ФТ `source/PostFinal-v2/PostFinal-v2.docx`, а текущий rc5 handoff использует `scope_slug: 4-3-client-addresses` и `source/PostFinal-v2.docx`.

**Вопрос:** Подтверждает ли БА, что `support/client-addresses-approved-clarifications-v3.md` применим к текущему rc5 scope `4-3-client-addresses`, несмотря на отличающиеся metadata по scope и пути основного ФТ?

**Что станет возможно после ответа:** Использовать `CLR-ADDR-001..005` как утвержденные уточнения для текущего rc5 handoff и связать их с source assertions.

#### Ответ БА (`user_response`)

```text
Подтверждаю, что `support/client-addresses-approved-clarifications-v3.md` можно применять к текущему rc5 scope `4-3-client-addresses`.
```

### CLR-003 — GAP-003

```yaml
clarification_id: CLR-003
gap_id: GAP-003
scope_slug: 4-3-client-addresses
requirement_codes: BSR 117; BSR 124; BSR 125; BSR 127; BSR 128; BSR 130; BSR 132; BSR 134; BSR 142; BSR 150; BSR 153; BSR 154; BSR 155; BSR 159; BSR 161
related_ft_reference: Таблица 4, строки 34/36/37/39/40/42/43/44/47/50/53/54/55/57/58; negative-oracle-inventory.md; requiredness-oracle-inventory.md
source_quote: "BSR 124/161: Ограничение на формат: только 6 числовых символов. BSR 132/134/159: Возможен ввод только числовых символов. BSR 117/142: обязательно должны быть введены регион и номер дома."
question: Какой утвержденный результат проверки должен ожидаться для ошибок ручного ввода адреса: формат почтового индекса, ввод только цифр в корпус/квартиру и незаполненные обязательные ручные поля?
needed_for: Сформулировать точные expected results для негативных и requiredness тест-кейсов без домысливания текста ошибки, подсветки или момента срабатывания проверки.
blocking: no
requested_from: analyst
authority: analyst
response_status: unanswered
response_type: not-provided
updated_at: -
```

**Текст из ФТ/source:** `BSR 124`/`BSR 161`: почтовый индекс ограничен форматом "только 6 числовых символов"; `BSR 132`/`BSR 134`/`BSR 159`: для корпуса/квартиры возможен ввод только числовых символов; `BSR 117`/`BSR 142`: обязательно должны быть введены регион и номер дома.

**Вопрос:** Какой утвержденный результат проверки должен ожидаться для ошибок ручного ввода адреса: формат почтового индекса, ввод только цифр в корпус/квартиру и незаполненные обязательные ручные поля?

**Что станет возможно после ответа:** Сформулировать точные expected results для негативных и requiredness тест-кейсов без домысливания текста ошибки, подсветки или момента срабатывания проверки.

#### Ответ БА (`user_response`)

```text
-
```

## Gaps Without Requests

| gap_id | related_ft_reference | reason |
| --- | --- | --- |
| - | - | Для всех текущих `GAP-*` создана карточка в `Clarification Requests`. |

## Правила Использования Ответов

- Ответы в этом файле не заменяют основной ФТ.
- Ответ из блока `Ответ БА` можно использовать downstream только после обновления служебных полей `response_status`, `response_type`, `authority` и `updated_at`.
- Production-ready semantics разрешено строить только из записи со `response_status = answered` и согласованной парой authority/type: `user/user-confirmed`, `analyst/analyst-confirmed` или `product-owner/product-confirmed`.
- `working-assumption`, `rejected`, `superseded`, `unanswered` и `not-provided` не являются утвержденным evidence.
- После утвержденного ответа соответствующий `GAP-*` остается в `scope-coverage-gaps.md` со статусом/resolution, а не исчезает без трассировки.
- Если ответ противоречит основному ФТ, приоритет остается у основного ФТ; противоречие фиксируется как gap.
