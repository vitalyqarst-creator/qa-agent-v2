# Планирование и материализация тестовых данных

Этот provider-neutral контракт действует после черновика матрицы и до её
независимого review, если матрица требует данных, которых нет буквально в ФТ
или package-справочнике. Это позволяет reviewer-у проверить не абстрактное
обещание данных, а их доказуемое происхождение до написания тест-кейсов.

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

Controller создаёт рядом с черновиком matrix `test-data-source-plan.json` с:

- `contract_version: test-data-source-plan-v2`, `scope_slug`, `matrix_sha256`;
- массивом `items` с `TDP-*`, `linked_scenarios`, `required_evidence`,
  `required_properties`, `selected_source` и русским `selection_reason`;
- `materialization_status`: `not-required`, `pending`, `materialized` или
  `blocked`; для `blocked` обязателен точный `blocker`;
- для `materialized`: `fixture_id`, `snapshot_path`, `receipt_path` и
  `snapshot_sha256`, а также `evidence_bindings`: одно доказательство для
  каждого требуемого свойства;
- для provider-а с заявленными семантическими возможностями —
  `provider_context` и `required_capabilities`.

Допустимые `required_evidence`: `source-literal`, `closed-dictionary-value`,
`integration-response`, `neutral-format-value`, `business-valid-entity`,
`binary-file-artifact`, `environment-state`.

`evidence_bindings` использует компактный формат:

```json
{
  "required_property": "data.inn=7707083893",
  "evidence_path": "receipt:/expected_response/exact_components/data.inn",
  "verified_value": "7707083893"
}
```

Путь начинается с `receipt:` или `snapshot:` и далее использует JSON Pointer.
Validator сверяет путь, literal, SHA-256 snapshot и `fixture_id` receipt-а;
пути всегда относительны папке scope.

- План охватывает только используемые `SCN-*`; одинаковые зависимости
  переиспользуют один fixture.
- При зарегистрированном adapter-е и доступных credentials controller сам
  запускает adapter. Credentials читаются только из environment.
- `materialized` требует snapshot/receipt, SHA-256, literals в fixture catalog
  и `evidence_bindings` для всех использованных свойств. Утверждение
  «подсказка DaData содержит нужные данные» без точного component path и
  verified value не является доказательством.
- При недоступном provider-е/credentials зависимые сценарии получают
  `needs-test-data` с точным blocker, а не выдуманные значения.
- Ответ provider-а не доказывает состояние продукта: create, duplicate, role и
  status отдельно требуют `environment-state`.
- Новый provider подключается профилем и adapter-ом без изменения маршрута.

## Семантическая совместимость provider-а

До materialization controller сверяет каждое требуемое свойство с
`required_capabilities` выбранного provider-а. Если provider возвращает
смежное, но не то же свойство, это не допускает подмены. Например, юридический
адрес организации из DaData не доказывает наличие отдельного фактического
адреса. В таком случае controller создаёт или дополняет один корневой
`BAQ-*`/`GAP-*`, связывает его с затронутыми matrix-строками и оставляет
соответствующий `TDP-*` `blocked` с этой ссылкой. Он не изобретает mapping и
не ожидает, пока writer обнаружит проблему.

## Локальные бинарные fixtures

Для файловых проверок используй профиль `local-binary-fixture` и adapter
`scripts/create_binary_file_fixture.py`. Он создаёт `jpg`, `png`, `pdf` или
`txt` указанного размера **в байтах**, сохраняет файл и token-free receipt с
SHA-256. Формулировки ФТ вроде «40 МБ» сначала нормализуй в точное число байт
по исходнику или утверждённому ответу БА. Если единица неоднозначна, создай
`BAQ-*`; не выбирай между `40_000_000` и `40 * 1024 * 1024` самостоятельно.

После matrix revision plan обновляется только если revision изменила
`linked_scenarios`, свойства или источники данных. Это ограниченное обновление
данных не является второй design-revision; reviewer повторно проверяет лишь
изменённые data-зависимости вместе с закрытием своих findings.

Writer использует только готовый план и fixtures, но не материализует их.
Matrix reviewer проверяет соответствие источника требуемому evidence и
семантическую совместимость provider-а до verdict. TC reviewer сверяет каждый
provider-backed literal с fixture catalog и plan. Live-вызовы API в
предусловиях, шагах и ожидаемом результате TC запрещены.
