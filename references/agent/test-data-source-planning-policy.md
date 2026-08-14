# Планирование и материализация тестовых данных

Этот provider-neutral контракт действует между принятием матрицы тест-дизайна
и написанием canonical test cases, если матрица требует отсутствующих данных.

## Выбор источника

Выбирай первый источник, который доказывает требуемое свойство:

1. точное значение из ФТ или утверждённого ответа БА;
2. значение из закрытого package-справочника;
3. уже сохранённый проверенный fixture;
4. внешний provider, семантически связанный с проверяемой интеграцией;
5. synthetic provider для нейтральных данных свободного ввода или формата;
6. подготовка тестовой среды для ролей, объектов и статусов.

DaData — один профиль внешнего provider-а, а не общий источник для любого ФТ.
`api.randomdatatools.ru` — один synthetic profile. Другой FT может использовать
иной provider, если зарегистрированы его adapter и проверяемый evidence contract.
Synthetic provider не доказывает существование объекта, бизнес-валидность
реквизита или результат интеграции.

## Артефакт и gate

Controller создаёт рядом с принятой matrix `test-data-source-plan.json` с:

- `contract_version: test-data-source-plan-v1`, `scope_slug`, `matrix_sha256`;
- массивом `items` с `TDP-*`, `linked_scenarios`, `required_evidence`,
  `required_properties`, `selected_source` и русским `selection_reason`;
- `materialization_status`: `not-required`, `pending`, `materialized` или
  `blocked`; для `blocked` обязателен точный `blocker`;
- для `materialized`: `fixture_id`, `snapshot_path`, `receipt_path` и
  `snapshot_sha256`.

Допустимые `required_evidence`: `source-literal`, `closed-dictionary-value`,
`integration-response`, `neutral-format-value`, `business-valid-entity`,
`environment-state`.

- План охватывает только используемые `SCN-*`; одинаковые зависимости
  переиспользуют один fixture.
- При зарегистрированном adapter-е и доступных credentials controller сам
  запускает adapter. Credentials читаются только из environment.
- `materialized` требует snapshot/receipt, SHA-256 и literals в fixture catalog.
- При недоступном provider-е/credentials зависимые сценарии получают
  `needs-test-data` с точным blocker, а не выдуманные значения.
- Ответ provider-а не доказывает состояние продукта: create, duplicate, role и
  status отдельно требуют `environment-state`.
- Новый provider подключается профилем и adapter-ом без изменения маршрута.

Writer использует только готовый план и fixtures, но не материализует их.
Reviewer проверяет соответствие источника требуемому evidence. Live-вызовы API
в предусловиях, шагах и ожидаемом результате TC запрещены.

