# Package Test Design Plan Format

`Package Test Design Plan` — обязательная секция canonical test-case file между `Atomic Requirements Ledger` и `TC-*`.

Цель секции: зафиксировать test-design решение до написания тест-кейсов, чтобы writer не переходил от atoms сразу к generic или неатомарным `TC-*`. Если для `source_property_id` существует `Coverage Obligation Table`, строки плана строятся из obligation rows, а не напрямую из общего atom.

## Когда Создавать

- Для каждого `initial_draft`.
- Для каждого internal work package, включая простой scope с одним `WP-01`.
- В `revision_from_findings`, если findings касаются покрытия, атомарности, equivalence/boundary classes, action flows, dependency или expected results.

## Минимальный Формат

```md
## Package Test Design Plan

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `PD-001` | `WP-01` | `equivalence` | `GSR 12` | `ATOM-012` | `Поле X принимает допустимое числовое значение` | `positive` | `valid numeric` | `valid numeric` | `значение принято полем` | `FT` | `TC-...-001` | `planned` |
| `PD-002` | `WP-01` | `equivalence` | `GSR 12` | `ATOM-013` | `Поле X отклоняет буквы` | `negative` | `letters` | `letters` | `значение не принято полем` | `FT + coverage-checklist` | `TC-...-002` | `planned` |
```

## Колонки

- `design_item_id`: стабильный id строки плана, например `PD-001`.
- `package_id`: `WP-*` из `scope-contract.md`.
- `design_dimension`: canonical coverage dimension, например `equivalence`, `boundary`, `dependency`, `conditional-visibility`, `decision-table`, `api-server-validation`, `integration`, `security`, `async`, `persistence`, `scenario-use-case`.
- `source_ref`: раздел, GSR/REQ/code, поле, таблица или строка ФТ.
- `linked_atoms`: один или несколько `ATOM-*`.
- `planned_check`: конкретная проверка, которую затем должен реализовать `TC-*`; не пересказ ФТ.
- `check_type`: `positive | negative | boundary | dependency | action-flow | scenario | gap`.
- `coverage_class`: класс эквивалентности, граница, ветка условия, action branch или причина gap.
- `input_class`: один входной класс или одна ветка, например `valid numeric`, `letters`, `N-1`, `N`, `N+1`, `condition=true`, `condition=false`.
- `single_expected_behavior`: один проверяемый oracle, который затем попадет в итоговый expected result конкретного `TC-*`.
- `oracle_source`: источник ожидаемого результата: `FT`, `PDF`, `approved clarification`, `coverage-checklist`, `GAP-*`. Для internal/API/async behavior без observable artifact указывай `GAP-*`, а не `FT`.
- `planned_tc_or_gap`: будущий/существующий `TC-*` или `GAP-*`.
- `status`: `planned | covered | gap | unclear | blocked`.

Для reset/state-transition строк поддерживается обязательное расширение таблицы:

- `initial_state_capture`: какое видимое исходное состояние фиксируется в начале этого же теста;
- `changed_state_setup`: как выбрать состояние относительно зафиксированного исходного;
- `pre_action_state_oracle`: наблюдаемая проверка отличия до целевого действия;
- `state_relation`: строго `different-from-captured-initial`.

Эти колонки обязательны для `coverage_class` / `property_type` вида `reset`, `*-reset` или `reset-*`. Нельзя считать `page 2`, первую строку, первый фильтр или первое нажатие на заголовок изменённым состоянием без сравнения с captured initial. Если отличающееся состояние недоступно, TC должен завершаться как fixture-blocked, а не продолжать reset-проверку с недоказанным setup.

## Правила

- Один `design_item_id` описывает одну проверку или один gap.
- Одна executable строка плана ведет к одному `TC-*`; один `TC-*` не должен закрывать несколько независимых строк плана ради экономии количества кейсов.
- Не объединяй positive и negative checks в одной строке плана.
- Для field/input validation negative row должен иметь sibling positive acceptance row в том же source/atom context или `GAP-*`, если acceptance oracle не выводится из источника.
- `check_type` должен быть одним значением. Slash-combinations вроде `positive/negative`, `boundary/format`, `dependency/integration`, `integration/gap`, `async/gap` запрещены, потому что скрывают несколько design decisions в одной строке.
- `input_class` не должен содержать пары вроде `valid and invalid`, `валидное/невалидное`, `допустимое и недопустимое`.
- `single_expected_behavior` не должен содержать пару независимых результатов вроде `не принимает X и принимает Y`.
- Для правил вида `только если`, `допустимы только`, `не допускается`, `обязателен при`, `отображается при` план должен содержать позитивную ветку и негативную/обратную ветку либо `GAP-*`.
- Validator ловит отсутствие обратной ветки для conditional/dependency rows как `test-case-package-design-plan-missing-conditional-branch`.
- Исключение: dependency row, которая явно описывает optional/no-blocking behavior (`может оставаться пустым`, `может оставаться без отдельного выбора`, `не блокирует переход/сохранение`), не требует искусственной inverse branch, если в этой же package/field context есть traceability evidence и row не заявляет visibility/requiredness transition.
- Validator ловит invalid/rejection row без positive acceptance sibling как `test-case-package-design-plan-negative-without-positive-acceptance`.
- Для length/mask/numeric/date rules план должен перечислять конкретные classes: valid class, invalid class, boundary class. Не используй общий класс `невалидное значение`, если можно выделить буквы, спецсимволы, пробелы, `N-1/N/N+1`, `min/max`, `start > end` и т.д.
- Для `numeric-format` plan должен строиться из `Coverage Obligation Table` и содержать отдельные rows для valid digits, letters, spaces, special chars, decimal separator и sign либо узкие `GAP-*`.
- Для `exact-length` plan должен содержать отдельные rows `N`, `N-1`, `N+1`; `N-1` и `N+1` нельзя объединять в один generic invalid-length row.
- Для action-created blocks plan должен отдельно фиксировать action branch, optional no-action branch и requiredness created-block fields, если эти ветки следуют из source.
- Для repeatable blocks plan должен содержать lifecycle rows: first add, second independent add, delete one of several, delete last, re-add after delete или `GAP-*` для неописанного reset/preserve behavior.
- Для checkbox/multi-select lists plan должен содержать rows для list visibility, `DICT-*` values, no selection, single selection, multiple selection и clear selection, когда они применимы.
- Для generated documents plan должен разделять `print-form-generated` и `print-form-content-mapping`; content mapping без source-backed маппинга должен быть `GAP-*`.
- Для `dictionary-source`, tags и fixed-list rules план должен ссылаться на `DICT-*` из `dictionary-inventory.md`; `input_class` должен быть `active dictionary values`, `archived dictionary values`, `extra value` или другой конкретный класс, а не два случайных примера из ФТ.
- Для action flows план должен перечислять branches: available action, unavailable/forbidden action, repeated action, cancel/back/refresh, если эти ветки следуют из scope.
- Для reset action flow до целевого действия план должен отдельно зафиксировать исходное состояние, подготовить состояние `different-from-captured-initial` и проверить видимое отличие. Проверка только post-reset результата не закрывает changed-prestate setup.
- Для dependency rules план должен ссылаться на `Dependency Matrix` или перечислять controlling value, dependent field и branch.
- Для internal/API/RabbitMQ/model/database behavior без подтвержденного observable artifact план должен ссылаться на `GAP-*`, а не на `TC-*`.
- Writer не должен писать `TC-*`, пока для package нет полного `Package Test Design Plan`.
- После создания плана writer обязан выполнить `Test Design Review` по `test-design-review-format.md`: сверить `Test Design Decision Table`, `Coverage Obligation Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, `Coverage Gaps` и supporting matrices на полноту классов и веток.
- Reviewer сначала проверяет этот план, затем сверяет каждый `TC-*` с соответствующей строкой `design_item_id`.
- Если запись полного файла упирается в лимит команды, patch или контекста, не сокращай план до merged rows. Продолжай chunked writing по одному `WP-*`; compact plan является blocking defect.

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
- применимая dimension отсутствует в `coverage-metrics.md` или metrics показывают obligation без `TC-*`/`GAP-*`;
- reusable/generic baseline используется без `fixture-catalog.md` и без раскрытия конкретных данных в TC;
- high-risk atom отсутствует в `risk-priority-map.md` или risk row не использует `impact x likelihood` / residual risk fields;
- отсутствует `Test Design Review` или в нем есть blocking row по affected package.
