# Fixture Catalog Format

`fixture-catalog.md` - split artifact в `work/test-design/<scope-slug>/`, который хранит воспроизводимые baseline-состояния и тестовые сущности, используемые несколькими `TC-*` или критичные для negative transition checks.

Artifact обязателен, если writer использует именованные baseline-данные вроде `валидная заявка`, `валидный работодатель`, `валидный пользователь`, `валидное состояние раздела`, либо если negative case проверяет отказ перехода/сохранения и должен доказать, что остальные обязательные условия валидны.

## Fixture Catalog

| fixture_id | purpose | source_ref | setup_state | concrete_data | valid_for | invalid_for | dependencies | cleanup | linked_tcs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FX-EMP-BASE-001` | Валидный baseline раздела занятости для негативных проверок одного поля | `section 2.1.1.1.1.2` | `Открыта карточка УЗ, пользователь может редактировать раздел` | `Тип занятости = Работа по найму; ...` | `TC-EMP-...` | `-` | `F-DADATA-ORG-001` | `Откатить изменения заявки` | `TC-EMP-006; TC-EMP-013` |

## External-dynamic fixture

Для внешнего динамического справочника, например DaData, строка каталога должна
иметь связанный блок со следующими обязательными полями:

```yaml
fixture_id: FX-DADATA-ADDR-001
provider: DaData
request:
  method: POST
  endpoint: <официальный endpoint>
  parameters: <точные параметры>
  query: <точная строка запроса>
expected_response:
  outcome: suggestions-found | suggestions-empty
  exact_suggestion: <точный value либо not_applicable>
  exact_components: <проверяемые компоненты либо not_applicable>
verification:
  source: <официальная документация или сохранённый live response>
  checked_at: YYYY-MM-DDThh:mm:ssZ
  response_snapshot: <repo-relative path>
  response_sha256: <64 hex>
  status: verified | blocked-verification
lifecycle:
  policy: verified-once / revalidate-on-failure
  revalidation_triggers:
    - linked-test-failure
    - confirmed-provider-contract-change
    - explicit-user-request
```

## Rules

- `concrete_data` должен содержать literals, параметры с source (`min`, `N`, `DICT-*`) или ссылки на другие fixtures; фразы `валидные данные`, `минимальный валидный набор`, `корректная заявка` без раскрытия недопустимы.
- Negative TC должен задавать только один invalid delta поверх valid fixture. Если несколько полей невалидны, failure attribution ненадежен.
- Если fixture зависит от внешнего справочника, mock/stub или системного состояния, укажи это в `dependencies`; если зависимость недоступна, используй `GAP-*`, а не generic fixture.
- Если fixture используется только в одном TC и полностью раскрыта в `Тестовые данные` / `Предусловия`, отдельная строка catalog не обязательна.
- Fixture catalog не является источником новых требований. Если baseline требует поведения, которого нет в source, добавь `coverage gap` / `unclear`.
- External-dynamic fixture создаётся и проверяется до writer; writer и runtime TC
  не обращаются к внешнему API для поиска тестового значения.
- Позитивный external-dynamic fixture хранит точный запрос, предложение и нужные
  компоненты. Негативный считается воспроизводимым только при сохранённом ответе
  `suggestions=[]` и совпадающем SHA-256; вымышленная «несуществующая» строка не
  доказывает отсутствие подсказок.
- TC содержит `FX-DADATA-*`, точный запрос и ожидаемые литералы, поэтому остаётся
  исполнимым без чтения каталога во время выполнения.
- Успешно проверенный external-dynamic fixture считается замороженными тестовыми
  данными по правилу `verified-once / revalidate-on-failure`. Дата проверки и
  SHA-256 фиксируют исходное evidence, но не задают срок годности fixture.
- Release-preflight, writer и reviewer используют сохранённые snapshot/literals и
  не выполняют автоматические live-вызовы внешнего provider-а.
- Повторная live-проверка допускается только после фактического падения связанного
  теста, подтверждённого изменения API/контракта provider-а или явного запроса
  пользователя. Изменение ответа сначала требует reconciliation fixture; дефект
  продукта создаётся только после подтверждения расхождения с ФТ на новом
  валидном fixture.

