# Package Test Design Plan Format

`Package Test Design Plan` — обязательная секция или split artifact между `Atomic Requirements Ledger` и `TC-*`.

Цель секции: зафиксировать test-design решение до написания тест-кейсов, чтобы writer не переходил от atoms сразу к generic или неатомарным `TC-*`. Если для `source_property_id` существует `Coverage Obligation Table`, строки плана строятся из obligation rows, а не напрямую из общего atom.

## Когда Создавать

- Для каждого `initial_draft`.
- Для каждого internal work package, включая простой scope с одним `WP-01`.
- В `revision_from_findings`, если findings касаются покрытия, атомарности, equivalence/boundary classes, action flows, dependency или expected results.

## Depth Metadata

Перед таблицей укажи `coverage_depth_profile`, `artifact_mode` и `depth_rationale`.

Допустимые значения:

- `coverage_depth_profile: simple | standard | deep`;
- `artifact_mode: compact | standard | full`;
- для plan, который наследует depth decision из `scope-contract.md`, используй explicit sentinel `inherited-from-scope-contract`, `inherited` или `scope-contract` и rationale со ссылкой на `scope-contract.md` / `Scope Complexity Assessment`.

Пустые значения, `-`, `n/a` и `todo` недопустимы. `simple` допускает compact plan только для малого low-risk scope; `deep` требует full plan и artifacts по `test-design-depth-policy.md`.

## Минимальный Формат

```md
## Package Test Design Plan

coverage_depth_profile: `standard`
artifact_mode: `standard`
depth_rationale: `Standard profile: source has validation rules, but no high-risk/table-heavy signals.`

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PD-001` | `WP-01` | `equivalence` | `GSR 12` | `ATOM-012` | `Поле X принимает допустимое числовое значение` | `positive` | `valid numeric` | `valid numeric` | `значение принято полем` | `FT` | `TC-...-001` | `planned` |
| `PD-002` | `WP-01` | `equivalence` | `GSR 12` | `ATOM-013` | `Поле X отклоняет буквы` | `negative` | `letters` | `letters` | `значение не принято полем` | `FT + coverage-checklist` | `TC-...-002` | `planned` |
```

## Колонки

- `design_item_id`: стабильный id строки плана, например `PD-001`.
- `package_id`: `WP-*` из `scope-contract.md`.
- `design_dimension`: coverage dimension, например `equivalence`, `boundary`, `dependency`, `conditional-visibility`, `decision-table`, `api-server-validation`, `integration`, `security`, `async`, `persistence`, `scenario-use-case`.
- `source_ref`: раздел, GSR/REQ/code, поле, таблица или строка ФТ.
- `linked_atoms`: один или несколько `ATOM-*`.
- `planned_check`: конкретная проверка, которую затем должен реализовать `TC-*`; не пересказ ФТ.
- `check_type`: `positive | negative | boundary | dependency | action-flow | scenario | gap`.
- `coverage_class`: класс эквивалентности, граница, ветка условия, action branch или причина gap.
- `input_class`: один входной класс или одна ветка, например `valid numeric`, `letters`, `N-1`, `N`, `N+1`, `condition=true`, `condition=false`.
- `single_expected_behavior`: один проверяемый oracle для expected result конкретного `TC-*`.
- `oracle_source`: `FT`, `PDF`, `approved clarification`, `coverage-checklist`, `GAP-*`; для internal/API/async без observable artifact указывай `GAP-*`, а не `FT`.
- `planned_tc_or_gap`: будущий/существующий `TC-*` или `GAP-*`.
- `status`: `planned | covered | gap | unclear | blocked`.

## Правила

- Один `design_item_id` описывает одну проверку или один gap.
- Одна executable строка плана обычно ведет к одному `TC-*` или `GAP-*`. Scenario grouping допустим только для одного business flow с общим setup, coherent observable oracle, явными ссылками на все `PD-*` и без скрытия independent pass/fail results.
- Не создавай low-value TC ради количества; source-backed class нельзя удалить ради экономии - используй `GAP-*`, accepted risk или `deep` classification.
- Не объединяй positive и negative checks в одной строке плана.
- Для field/input validation negative row должен иметь sibling positive acceptance row в том же source/atom context или `GAP-*`, если acceptance oracle не выводится из источника.
- `check_type`, `input_class` и `single_expected_behavior` не должны смешивать пары вроде `positive/negative`, `boundary/format`, `valid and invalid`, `не принимает X и принимает Y`.
- Для правил вида `только если`, `допустимы только`, `не допускается`, `обязателен при`, `отображается при` план должен содержать позитивную ветку и негативную/обратную ветку либо `GAP-*`.
- Validator ids: missing inverse branch -> `test-case-package-design-plan-missing-conditional-branch`; invalid/rejection row без positive sibling -> `test-case-package-design-plan-negative-without-positive-acceptance`. optional/no-blocking behavior dependency row не требует искусственной inverse branch при traceability evidence и без visibility/requiredness transition.
- Для length/mask/numeric/date rules перечисляй concrete valid/invalid/boundary classes; не используй общий класс `невалидное значение`, если можно выделить буквы, спецсимволы, пробелы, `N-1/N/N+1`, `min/max`, `start > end`. `numeric-format` строится из `Coverage Obligation Table`: valid digits, letters, spaces, special chars, decimal separator, sign или узкие `GAP-*`.
- Для `exact-length` plan должен содержать отдельные rows `N`, `N-1`, `N+1`; `N-1` и `N+1` нельзя объединять в один generic invalid-length row.
- Для action-created blocks plan должен отдельно фиксировать action branch, optional no-action branch и requiredness created-block fields, если эти ветки следуют из source.
- Для repeatable blocks покрой lifecycle rows: first add, second add, delete one/many/last, re-add after delete или `GAP-*` для reset/preserve behavior.
- Для checkbox/multi-select lists покрой list visibility, `DICT-*` values, no/single/multiple/clear selection. Generated documents разделяй на `print-form-generated` и `print-form-content-mapping`; missing mapping -> `GAP-*`.
- Для `dictionary-source`, tags и fixed-list rules план должен ссылаться на `DICT-*` из `dictionary-inventory.md`; `input_class` должен быть `active dictionary values`, `archived dictionary values`, `extra value` или другой конкретный класс, а не два случайных примера из ФТ.
- Для action/dependency rules перечисляй branches or `Dependency Matrix`; internal/API/RabbitMQ/model/database без observable artifact -> `GAP-*`, не `TC-*`.
- Writer не должен писать `TC-*`, пока для package нет полного `Package Test Design Plan`.
- После создания плана writer обязан выполнить `Test Design Review` по `test-design-review-format.md`: сверить `Test Design Decision Table`, `Coverage Obligation Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, `Coverage Gaps` и supporting matrices на полноту классов и веток.
- Для `deep` и large/high-risk `standard` scope после plan выполни `TC Set Optimization Review` по `tc-set-optimization-format.md`.
- Reviewer сначала проверяет этот план, затем сверяет каждый `TC-*` с соответствующей строкой `design_item_id`.
- Если запись полного файла упирается в лимит команды, не сокращай plan до merged rows. Продолжай chunked writing по одному `WP-*`; compact plan допустим только для `simple` или явно обоснованного small low-risk `standard`.

## Blocking Conditions

Не ставь `ready-for-review`, если:

- отсутствует `Package Test Design Plan`;
- не все `WP-*` из scope-contract представлены в плане;
- applicable atom не имеет строки плана;
- строка плана имеет `planned_tc_or_gap = -`;
- validation/action/dependency rule представлен только generic строкой без positive/negative/boundary/branch decomposition;
- dictionary/fixed-list rule представлен без `DICT-*` или `GAP-*`;
- один `TC-*` указан в нескольких executable строках плана без явного `scenario`/`recovery` обоснования;
- plan ссылается на `TC-*`, которого нет в canonical file после writer-pass.
- применимая dimension требует standalone `coverage-metrics.md` по depth policy, но metrics отсутствуют или показывают obligation без `TC-*`/`GAP-*`;
- reusable/generic baseline используется без `fixture-catalog.md` и без раскрытия конкретных данных в TC;
- high-risk atom отсутствует в `risk-priority-map.md` или risk row не использует `impact x likelihood` / residual risk fields;
- отсутствует `Test Design Review` или в нем есть blocking row по affected package.
- `coverage_depth_profile = deep`, но отсутствует `TC Set Optimization Review`.
