# Test Design Decision Table Format

`Test Design Decision Table` - обязательный split artifact `work/test-design/<scope-slug>/test-design-decision-table.md` для table/extraction/package-based scope между `Source Table Normalization` и `Atomic Requirements Ledger`.

Цель таблицы - не дать writer-у механически превращать каждое свойство источника в отдельный `TC-*`. Одна строка `Source Table Normalization` описывает свойство источника, но не доказывает, что нужен самостоятельный исполнимый тест-кейс.

## Placement

Порядок для writer-pass:

1. `Source Row Inventory`
2. `Source Row Completeness Matrix`, если одна source row содержит несколько самостоятельных требований
3. `Source Table Normalization`
4. `Dictionary Inventory`, если есть `dictionary-source` / reference-list rows
5. `Test Design Decision Table`
6. `Atomic Requirements Ledger`
7. `Package Test Design Plan`
8. `TC-*`

Writer не должен создавать `Atomic Requirements Ledger`, `Package Test Design Plan` или `TC-*`, пока каждая строка `Source Table Normalization` не получила решение в `Test Design Decision Table`.

## Minimum Columns

| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TDD-001` | `WP-01` | `SRC-003.P01` | `ATOM-002` | `format` | `standalone_tc` | Numeric-only input is observable in UI. | `TC-UI-MAIN-002` | `DOCX table 9 row 3; UI field accepts/rejects input` | `yes` | `UI принимает/отклоняет класс ввода` | `Проверить ввод цифр и нецифровых классов` | `-` | `not-a-gap` | `none` |

## Allowed Decisions

- `standalone_tc`: свойство требует отдельного исполнимого `TC-*`.
- `covered_by_existing_tc`: свойство покрывается уже запланированным исполнимым `TC-*`; отдельный TC не нужен.
- `gap_unclear`: ожидаемое поведение, oracle или artifact не выводится из источников.
- `metadata_only`: строка является metadata/input classification и сама по себе не задает observable behavior.
- `scenario_only`: свойство проверяется только как часть допустимого scenario/use-case, при этом atomic coverage не заменяется сценарием.
- `out_of_scope`: свойство вне подтвержденных границ scope.

## Rules

- Каждая `source_property_id` из `Source Table Normalization` должна иметь ровно одну строку в `Test Design Decision Table`.
- `metadata_only` не должен ссылаться на `TC-*`. Если metadata важна для traceability, используй `GAP-*` или объясни, каким конкретным format/input/widget TC она покрывается через `covered_by_existing_tc`.
- `gap_unclear` должен ссылаться на объявленный `GAP-*`.
- `gap_unclear` допустим только для реально заблокированной части. Если source row содержит наблюдаемый UI/API artifact: подсказку, сообщение, красную подсветку, видимость/скрытие, доступность действия, переход, маску, справочник/теги, подтверждение или другой pass/fail oracle, эту часть нельзя отправлять в общий gap.
- Для `gap_unclear` обязательно заполняй:
  - `observable_oracle`: что наблюдаемо по источнику или `none`, если ничего наблюдаемого нет;
  - `testable_part`: какая часть требования проверяема сейчас или `-`;
  - `blocked_part`: какая конкретная часть непроверяема;
  - `gap_admissibility`: почему именно эта непроверяемая часть имеет право остаться `GAP-*`.
- Если `testable_part` не пустой, решение всей строки не может быть `gap_unclear`: split row на executable decision и узкий `GAP-*`.
- `standalone_tc` должен ссылаться на один planned/existing `TC-*` и иметь source-backed observable `oracle_source`.
- `covered_by_existing_tc` должен ссылаться на planned/existing executable `TC-*` и объяснять, почему отдельный TC не нужен.
- `scenario_only` должен ссылаться на scenario TC и объяснять, почему сценарий не заменяет atomic checks.
- `out_of_scope` должен ссылаться на scope/source decision.
- Решение в `Test Design Decision Table` должно быть синхронизировано со всеми downstream sections:
  - если `decision = metadata_only`, связанный `ATOM-*` не может быть `covered` в `Atomic Requirements Ledger`, не может иметь executable `TC-*` в `Package Test Design Plan`, `Risk / Priority Map` или обычных `TC-*` секциях; допустимы только `GAP/unclear` или `traceability-remap`;
  - если `decision = gap_unclear`, тот же `GAP-*` должен быть виден в `Coverage Gaps`, ledger, design plan и risk map, а executable `TC-*` coverage по этому atom запрещен;
  - если `decision = scenario_only`, строка должна ссылаться на retained executable scenario TC; compatibility/remap anchors не должны выглядеть как executable `scenario-use-case` TC.
- `value-type` / `тип значения` строки не становятся standalone TC без конкретного observable behavior. Допустимые решения: `metadata_only`, `gap_unclear` или `covered_by_existing_tc` через source-backed format/input/widget behavior.
- `dictionary-source` / reference-list строки должны ссылаться на `DICT-*` из `dictionary-inventory.md` в `decision_reason` или `oracle_source`; если inventory отсутствует или неполон, решение должно ссылаться на узкий `GAP-*`, а не на примерные значения.
- Dependency/conditional rows должны называть controlling field, controlling value/action и expected branch. Если source не дает этих данных, решение должно быть `gap_unclear`.
- Internal/API/RabbitMQ/model/database behavior без подтвержденного observable artifact получает `gap_unclear`, а не `standalone_tc`.
- UI persistence/no-save для видимых полей не считается internal-only, если источник прямо задает save/no-save outcome и в scope есть путь повторно открыть тот же объект/раздел. В этом случае `observable_oracle` должен быть отображаемым значением после повторного открытия, а decision должен быть `standalone_tc` или `covered_by_existing_tc`, не `gap_unclear`.
- Отсутствие fixture, справочника, product catalog, backend artifact или test clock не отменяет проверяемые UI-части требования. Такие случаи split-ятся: UI oracle -> `standalone_tc` / `covered_by_existing_tc`, недостающая внутренняя или data-dependent часть -> `GAP-*`.
- Для date/window rules, включая паспортные окна 14/20/45 лет и точные подсказки, нельзя использовать общий `gap_unclear`, если границы и тексты ошибок есть в ФТ/PDF. Допустим только узкий gap на тестовые часы, точку отсчета или недостающую фикстуру.
- Решение не должно использоваться для экономии количества TC. Если два свойства могут pass/fail независимо, они требуют разных decisions и разных `TC-*` или `GAP-*`.

## Self-check

Перед переходом к ledger writer обязан проверить:

- `source_property_id` coverage: нет пропущенных или дублирующихся source properties;
- `metadata_only` rows не имеют `TC-*`;
- `gap_unclear` rows имеют `GAP-*`;
- `gap_unclear` rows прошли admissibility: нет source-backed visible behavior, спрятанного в gap; mixed testable/blocked rows split-нуты;
- `metadata_only` / `gap_unclear` rows не конфликтуют с ledger, Package Test Design Plan, Risk / Priority Map и `TC-*`;
- scenario-only remap anchors, если они оставлены для совместимости, имеют тип `traceability-remap` и не считаются executable coverage;
- `standalone_tc` rows имеют конкретный oracle source;
- `covered_by_existing_tc` rows не маскируют независимую проверку;
- `value-type`, `тип контрола`, `тип значения` и structural-context rows не превращены в pseudo-TC без наблюдаемого поведения.
- `dictionary-source` rows имеют `DICT-*` или `GAP-*`; branch-driver examples из ФТ не используются как замена `dictionary-inventory.md`.
