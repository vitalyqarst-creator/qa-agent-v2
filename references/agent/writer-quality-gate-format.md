# Writer Quality Gate Format

`Writer Quality Gate` - обязательный split artifact `work/test-design/<scope-slug>/writer-quality-gate.md` перед `Writer Self-Check`.

Цель gate: не допустить явно слабый writer draft до full review. Это не заменяет reviewer, а отбраковывает draft, который нарушает базовую атомарность, декомпозицию или observability.

Человекочитаемые поля `evidence` и `required_action` пиши на русском языке, если пользователь явно не запросил другой язык. Технические имена колонок, gate items, enum-значения, ids и имена файлов остаются каноническими.

## Семантика статусов

`Writer Quality Gate` фиксирует результат именно writer-этапа. `pass` означает,
что writer на момент передачи в review проверил условие прямым evidence и не
оставил действий для исправления: `required_action` должен быть
`none_required:pass`.

Reviewer finding не является evidence для задним числом поставленного `pass`.
Нельзя дописывать в уже пройденный gate строку `pass` с формулировкой вроде
`tracked_in_tc_review_findings`: это скрывает дефект writer draft. Такой finding
остается в `review-findings.md` до writer revision. После фактического исправления
writer запускает gate для новой revision и только тогда может зафиксировать `pass`.

Если writer сам обнаружил дефект до review, используй `needs-rewrite` или `fail`
с `blocks_ready_for_review = yes`; не заменяй этот статус ссылкой на будущий review.

## Версия контракта и migration policy

Перед таблицей укажи текущую строку:

```md
**Версия контракта:** `writer-quality-gate-v4`
```

Если validator требует новую версию или новый обязательный gate item, старый
draft становится `blocked-quality-gate`. Нельзя добавлять в старую таблицу
строки `pass` только ради migration. Writer сначала повторно проверяет текущие
matrix и canonical TC, собирает evidence и только после этого обновляет версию
контракта. Пока revalidation не выполнена, reviewer не запускается.

В одном `writer-quality-gate.md` для каждого `gate_item` допускается ровно одна
актуальная строка. После повторной проверки замени evidence/status этой строки;
историю предыдущей проверки фиксируй в writer session/decision log, а не во
второй таблице `recheck` внутри gate. Это не позволяет одновременно хранить
противоречивые `pass` и `fail` для одного условия.

## Минимальный Формат

```md
## Writer Quality Gate

**Версия контракта:** `writer-quality-gate-v4`

| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- |
| `artifact-shape-preflight` | `pass` | Split artifacts have exactly one canonical `#` or `##` section heading matching the section title, use exact canonical tables, and canonical TC links summaries only. | `all` | none_required:pass | `no` |
| `artifact-write-strategy` | `pass` | Большой/package artifact использует `scripts/write_artifact_sections.py --manifest <manifest.json>`. | `all` | none_required:pass | `no` |
| `mockup-visual-inventory` | `pass` | `mockup-visual-inventory.md` открыт и дал подсказки по взаимодействию. | `WP-01` | none_required:pass | `no` |
| `source-row-inventory` | `pass` | Каждая in-scope строка handoff присутствует и сопоставлена с `ATOM-*` или `GAP-*`. | `WP-01` | none_required:pass | `no` |
| `source-normalization-atomic` | `pass` | Source rows содержат по одному property/condition/behavior. | `WP-01` | none_required:pass | `no` |
| `matrix-atomarity` | `pass` | `test-design-matrix.md`: все строки с несколькими атрибутами/значениями имеют `Обоснование параметризации` с едиными экраном, UI-уровнем, действием, триггером и наблюдаемым результатом; остальные строки разделены. | `WP-01` | none_required:pass | `no` |
| `dictionary-inventory` | `pass` | `dictionary-source` rows используют `DICT-*` из `dictionary-inventory.md`. | `WP-01` | none_required:pass | `no` |
| `test-design-decision-table` | `pass` | Каждый `source_property_id` имеет одно design decision до ledger/TC writing. | `WP-01` | none_required:pass | `no` |
| `coverage-obligation-table` | `pass` | `numeric-format` и `amount-tags` разложены на обязательные coverage classes с `TC-*`/`GAP-*`. | `WP-01` | none_required:pass | `no` |
| `test-design-review` | `pass` | `test-design-review.md` не содержит blocking rows. | `WP-01` | none_required:pass | `no` |
| `gap-admissibility` | `pass` | Все `GAP-*` проверены: visible UI/API behavior не спрятан в gap, mixed rows split-нуты. | `WP-01` | none_required:pass | `no` |
| `runtime-language-style` | `pass` | Runtime-поля TC написаны по-русски и не содержат agent-process фраз вроде `source-backed`, `runtime-prose`, `semantic projection`. | `all` | none_required:pass | `no` |
| `tc-regression-smells` | `pass` | В canonical TC отсутствуют placeholder traceability, source-rule oracle, duplicate-positive, downstream-local rejection, injected requiredness, optional-as-required, post-save input, generic editability, nondeterministic negative oracle, executable unresolved GAP, ambiguous UI alias и read-only cleanup smells. | `all` | none_required:pass | `no` |
| `tc-metadata-integrity` | `pass` | У каждого `TC-*` заполнены канонические metadata-поля, указан только `Статус исполнения`, тип соответствует полярности проверки. | `all` | none_required:pass | `no` |
| `lifecycle-execution-ownership` | `pass` | Каждый TC по статусу/жизненному циклу привязан к одному конкретному объекту, месту выполнения (экрану, карточке, списку или блоку), действию пользователя и наблюдаемому результату; разные акторы с разными outcome разложены в отдельные TC; определение статуса без такого сценария остается трассировкой или `GAP-*`. | `all` | none_required:pass | `no` |
| `step-executability` | `pass` | Шаги пронумерованы, не ссылаются на шаги другого TC и не содержат условных альтернатив выполнения. | `all` | none_required:pass | `no` |
| `fixture-resolution` | `pass` | Каждый упомянутый fixture существует в каталоге либо полностью раскрыт в текущем TC. | `all` | none_required:pass | `no` |
| `closed-dictionary-completeness` | `pass` | Для закрытого справочника проверено «все и только» значения из `dictionary-inventory.md`. | `WP-01` | none_required:pass | `no` |
| `boundary-class-completeness` | `pass` | Для применимых ограничений описаны границы, допустимые и недопустимые эквивалентные значения. | `WP-01` | none_required:pass | `no` |
| `creation-form-isolation-coverage` | `pass` | `test-design-matrix.md`: `TC-EXAMPLE-014`; проверяемые поля: `Наименование`, `Расчетный счет`; после создания A новая форма B не содержит значения A. | `WP-01` | none_required:pass | `no` |
| `runtime-execution-semantics` | `pass` | `test-cases/9.1-example.md`: `TC-EXAMPLE-015`–`TC-EXAMPLE-019`; проверены одна точка входа, source-backed границы автозаполнения, cardinality upload-поля, конкретная отмена и persistence дочерних записей. | `WP-01` | none_required:pass | `no` |
| `semantic-compression` | `fail` | `ATOM-017` закрывает `GSR 34`-`GSR 58` одним scenario TC. | `WP-02` | Переписать package от Source Table Normalization до TC. | `yes` |
```

## Обязательные Gate Items

- `artifact-shape-preflight`: split artifacts use exact canonical headings/table columns, each split artifact has exactly one canonical section heading matching the section title, accepted heading levels are `# Section` or `## Section`, missing/wrong headings are invalid, adjacent wrapper headings like `# Source Row Inventory` followed by `## Source Row Inventory` are invalid, canonical TC file must not duplicate split artifact tables, and alias columns such as `item` instead of `gate_item` are invalid. Required shapes: `| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |`; `| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |`; `| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision |`; `| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |`; `| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |`; `| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |`; `| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |`; `| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |`. `source-row-inventory.md` column `in_scope` accepts only `yes`, `no`, `unclear`, `out-of-scope`.
- `placeholder-sentinel-normalization`: traceability-bearing split artifacts and review matrices must not use placeholder `-` / `N/A` in source/coverage/link columns such as `req_id`, `requirement_code(s)`, `covered_by_tc`, `linked_test_cases`, `planned_tc_or_gap`, `gap_id(s)`, `mapped_atom_or_gap`, `blocked_part`, `gap_admissibility`, `review_notes`, or `gap_note`. Use explicit values such as `not_applicable:covered`, `not_covered:<GAP-ID>`, `unclear:<GAP-ID>`, `no_requirement_code:<source_ref>`, or `none_required:<reason>` so reviewers can distinguish absent data from an unfilled placeholder.
- `artifact-write-strategy`: большие/package-based writer outputs имеют preflight-стратегию записи и используют file-based/chunked writing до генерации контента.
- `mockup-visual-inventory`: UI scopes с макетами имеют `mockup-visual-inventory.md`; макет открыт, а подсказки по взаимодействию используются только для шагов без превращения mockup-only элементов в требования.
- `source-row-inventory`: каждая in-scope/unclear source row из handoff `source-row-inventory.md` присутствует в writer-side inventory до normalization и сопоставлена с `ATOM-*`, `GAP-*` или явным out-of-scope решением.
- `source-normalization-atomic`: normalized source rows содержат одно чистое property, condition или behavior; каждая строка имеет `source_property_id`; source rows с несколькими `GSR`/`REQ` имеют `Source Row Completeness Matrix`; normalization row не несет несколько independently checkable requirement codes и не смешивает semantic property classes, например dictionary source + min boundary + max boundary, visibility + requiredness или format + boundary.
- `matrix-atomarity`: до reviewer проверены все строки `test-design-matrix.md`: одна строка — один объект/UI-уровень, одна проверка и один основной ожидаемый результат. Несколько независимых отображаемых атрибутов, разные объекты, роли с разными outcome, позитивная и негативная ветви или несколько самостоятельных действий разделяются. Параметризация значений допустима только при явном `Обоснование параметризации`, которое доказывает одинаковые стартовый экран, UI-уровень, навигацию, действие, триггер и наблюдаемый результат.
- `test-design-decision-table`: каждый нормализованный `source_property_id` имеет ровно одно решение: `standalone_tc`, `covered_by_existing_tc`, `gap_unclear`, `metadata_only`, `scenario_only` или `out_of_scope`; metadata-only rows не создают executable `TC-*`; gap/metadata/scenario-only decisions согласованы с ledger, Package Test Design Plan, Risk / Priority Map и `TC-*`; standalone TC decisions имеют observable oracle.
- `scoped-validator-findings`: writer после финальной записи canonical TC и split artifacts запускает scoped validator или runner validator gate; текущий scope не имеет unresolved `warning`/`error`, либо каждая finding оформлена как валидный `false-positive`/waiver с id, path, evidence и rationale.
  Для `status = pass` evidence должно ссылаться только на runner-generated `outputs/scoped-validator-profile.<stage>.json` с `generated_by: codex_review_cycle_runner` либо на runner validator gate output. Generic `validator.json`, в том числе с `passed: true`, и self-reported JSON без `generated_by` не являются валидным scoped validator evidence.
  Для отдельного writer-stage без запуска полного review-cycle используй `python scripts/write_scoped_validator_profile.py --workflow-state <путь-к-workflow-state.yaml> --require-clean`: helper запускает validator и записывает текущий stage profile. Не создавай JSON profile вручную.
  Writer gate must reference the current writer-stage profile, for example `outputs/scoped-validator-profile.writer-r1.json`; reviewer/future profiles such as `outputs/scoped-validator-profile.structure-preflight-r1.json` do not prove that writer output was validator-clean at handoff time.
  Current-scope filtering includes only the active canonical TC file, active `work/test-design/<scope>/` directory and current cycle `outputs/`. Full validator reports may still contain historical findings under `work/review-cycles/<scope>/versions/` or scratch files under `_artifact_write/`; those paths are evidence history, not current-scope blockers, and must not be counted in `unresolved_warning_error_count`.
- `coverage-obligation-table`: mandatory property types (`numeric-format`, `exact-length`, `action-created-optional-block`, `repeatable-block-lifecycle`, `checkbox-list`, `print-form-output`, `amount-tags`, `format-mask`, `default-mask`) разложены на обязательные classes с `TC-*`/`GAP-*`.
- `coverage-metrics`: каждая applicable dimension имеет counted obligations/classes/branches/transitions, covered count и gap/unclear count по `test-design-coverage-metrics-format.md`.
- `fixture-catalog`: reusable baselines и negative transition fixtures раскрыты в `fixture-catalog.md` или полностью в TC.
- `risk-priority-map`: high-risk atoms имеют `impact x likelihood`, priority и residual risk decision по `risk-priority-map-format.md`.
- `gap-admissibility`: `gap_unclear` и `GAP-*` не скрывают проверяемые подсказки, сообщения, красную подсветку, видимость, действия, переходы, маски, справочники/теги, date-window boundaries или другие source-backed observable outcomes; смешанные testable/blocked требования split-нуты.
- `runtime-language-style`: canonical TC runtime-поля (`Название`, `Цель`, `Предусловия`, `Тестовые данные`, `Шаги`, `Итоговый ожидаемый результат`, `Постусловия`, `Требуется подтверждение`) написаны как пользовательский русский текст и не содержат agent-process английские фразы: `source-backed`, `source qualified`, `registered-card`, `runtime-prose`, `model-runtime-prose`, `semantic projection`, `hash-bound`, `manifest digest`, `runner-owned`, `agent-process`, `exact credit-conveyor screen`. Английские значения разрешены только для metadata enum (`Positive`, `Negative`, `High`, `Medium`, `Low`) и технических ID/fixture_id. Видимые названия вкладок, полей, кнопок и действий берутся из макета или approved UI evidence; заголовок раздела ФТ не заменяет UI label.
- `test-design-review`: `test-design-review.md` существует для package-based `initial_draft`, совместно проверяет TDDT/ledger/plan/gaps и не содержит blocking failed rows.
- `ledger-atomicity`: `ATOM-*` rows не объединяют независимые visibility, requiredness, editability, format, boundary, dependency, persistence, integration или action behavior.
- `gsr-range-compression`: covered atoms не используют широкие диапазоны `GSR N-M` как замену декомпозиции.
- `design-plan-atomicity`: одна executable plan row имеет один `check_type`, один `input_class`, один `single_expected_behavior` и один `TC-*`/`GAP-*`.
- `scenario-does-not-replace-atomic`: scenario/use-case TC являются дополнительными и не заменяют atomic positive, negative, boundary, dependency или action TC.
- `tc-atomicity`: `TC-*` не объединяют независимые pass/fail decisions.
- `tc-metadata-integrity`: у каждого `TC-*` есть канонические поля `Название`, `Тип`, `Приоритет`, `package_id`, `Трассировка`; `Positive` не используется для проверки отказа, а `Negative` не скрывает позитивную приемку.
- `lifecycle-execution-ownership`: TC по статусу, архивированию, разархивированию или доступности объекта не смешивает разные уровни UI (например, партнера и реквизит); у него есть один объект, точка исполнения, действие и наблюдаемый результат. Если ФТ задает только словарное определение статуса, это не самостоятельный executable TC.
- `step-executability`: шаги имеют непрерывную нумерацию внутри TC, содержат конкретное действие или проверку, не ссылаются на другой TC и не предлагают альтернативы вида «если действие доступно».
- `test-data-specificity`: validation/boundary/equivalence TC используют конкретные значения или именованные классы, а не placeholders вроде `значение, нарушающее правило`.
- `fixture-resolution`: ссылка на `FX-*` допустима только на существующий fixture catalog или на полностью раскрытые данные в самом TC. Нельзя подменять реальную интеграционную/DaData запись выдуманным названием организации.
- `closed-dictionary-completeness`: если source/support определяет закрытый перечень, план и TC проверяют присутствие всех разрешенных значений и отсутствие дополнительных; два случайных примера не являются покрытием перечня.
- `boundary-class-completeness`: для digits-only отдельно представлены допустимые цифры и недопустимые классы (латиница, кириллица, пробел, знак/дефис, точка/десятичный разделитель, спецсимвол) в применимом объеме; для exact/min/max length есть границы и соседние значения.
- `creation-form-isolation-coverage`: если действие `Создать` / `Добавить` открывает форму нового независимого объекта, дочерней записи или строки, matrix/TC проверяют: после создания A с отличительными пользовательскими значениями новая форма B не предзаполнена значениями A. TC явно перечисляет `Проверяемые поля` и наблюдает их сразу после открытия B, до несвязанного перевода фокуса, ввода или сохранения. Evidence `pass` содержит `test-design-matrix.md`, affected `TC-*` и набор проверяемых полей; при неприменимости используй `not_applicable:` с source reference. Не требуй пустоты для source-defined default, context/inherited value, clone/import или документированного draft restoration.
- `runtime-execution-semantics`: evidence `pass` ссылается на canonical `test-cases/...` и проверенные `TC-*`. До handoff writer обязан проверить сами runtime-поля, а не только matrix: один TC не смешивает создание и редактирование через `или`; автозаполнение не используется как доказательство ручного изменения/очистки без source/UI evidence; ограничение «не более одного файла» проверяется второй допустимой загрузкой в том же поле, а не «файлом того же типа документа»; отмена изменяет одно конкретное поле на конкретное значение; TC про первый дочерний объект задаёт родителя без дочерних записей, а TC про второй после сохранения повторно открывает родителя и подтверждает оба объекта. Если один из этих сценариев не подтверждён источником, writer создаёт узкий `GAP-*` или ставит честный execution status, но не имитирует исполнимость.
- `source-obligation-completeness`: evidence `pass` ссылается на `test-design-matrix.md` и на источник полноты: `source-row-inventory.md` для табличного/строчного scope либо `scope-brief.md` для компактного scope. Общий текст «сопоставлено» не является evidence.
- `expected-result-singularity`: evidence `pass` ссылается на canonical `test-cases/...` и affected `TC-*`, а не на общий текст «у каждого TC один результат».
- `tc-regression-smells`: canonical TC file не содержит повторяющиеся canary-defects: placeholder `-` / `N/A`, source-rule oracle, duplicate modeled as positive save, downstream local rejection, injected requiredness, optional-as-required, field input after save, generic editability steps, dictionary TC без `все и только активные значения`, nondeterministic negative oracle через `или`, executable unresolved `GAP-*`, ambiguous UI alias/action, derived checks без source/rule derivation, шаблонное cleanup-постусловие в read-only TC.
- TC смешивает добавление/создание и редактирование, делает неявный вывод о ручном изменении автозаполненного поля, подменяет cardinality upload-поля проверкой расширения/типа документа, использует альтернативные изменяемые поля в TC `Отменить`, объявляет первый дочерний объект без пустого родителя или второй дочерний объект без проверки сохранения обоих после повторного открытия.
- `internal-observability`: internal/API/RabbitMQ/model/database behavior без observable artifact остается `GAP-*`/`unclear`.
- `action-observability`: action/async TC со статусом `covered` называют конкретный observable result или artifact; `action initiated` без evidence остается `GAP-*`/`unclear`.
- `semantic-req-id-parity`: requirement codes связаны с тем же source statement/field/expected behavior, что и в source parity, а не просто присутствуют где-то в файле.
- `package-ready`: каждый `WP-*` прошел package ledger, design-plan и TC gates.

## Условные Gate Items

- `dictionary-inventory`: обязателен, если `source-table-normalization.md` содержит `dictionary-source`, `amount-tags`, `tag-values`, `table-list`, `checkbox-list` или аналогичный reference-list property; `dictionary-inventory.md` должен иметь matching `DICT-*`, а TDDT/plan/TC должны ссылаться на этот `DICT-*` или узкий `GAP-*`.

## Блокирующие Паттерны

Writer должен ставить `status = fail` и `blocks_ready_for_review = yes`, если есть:

- `artifact-shape-preflight` failed: required table missing/unparseable, missing/wrong canonical split artifact heading, noncanonical or alias columns, adjacent duplicate split artifact headings such as `# X` followed by `## X`, invalid status/blocks values, invalid `in_scope` enum values, missing `Source Row Completeness Matrix` for multi-code rows, table-only TC metadata that hides parser-required fields such as `package_id`, or canonical TC duplicates full split artifact sections instead of linking summaries to `work/test-design/<scope-slug>/...`;
- large/package-based writer output без `Artifact Write Strategy`;
- large/package-based writer output, где `Artifact Write Strategy` не использует `scripts/write_artifact_sections.py`;
- UI scope с mockup source, но без `mockup-visual-inventory.md`;
- `mockup-visual-inventory.md` содержит `opened = no`, не содержит interaction hints или не содержит `not_used_as_requirement_source = yes`;
- package-based writer output без split artifact `source-row-inventory.md`, in-scope source row без `ATOM-*` / `GAP-*` mapping или writer-side inventory потерял source row из handoff `source-row-inventory.md`;
- package/table-based writer output имеет `Source Table Normalization`, но не имеет `Test Design Decision Table`;
- `Source Table Normalization` содержит `dictionary-source` / reference-list property, но рядом нет `dictionary-inventory.md`, нет строки `DICT-*` для referenced dictionary/list или downstream plan/TC используют только примерные значения вместо inventory;
- `Test Design Decision Table` пропускает normalized `source_property_id` rows, содержит duplicate decisions, связывает `metadata_only` rows с executable `TC-*`, использует `gap_unclear` без `GAP-*`, отправляет atom в `metadata_only` / `gap_unclear`, хотя downstream sections помечают его как `covered`, сохраняет scenario-only compatibility anchors как executable `scenario-use-case` sections или помечает `value-type` / `тип значения` как standalone TC без конкретного observable input/widget/format behavior;
- `Test Design Decision Table` отправляет в `gap_unclear` или `metadata_only` source-backed observable behavior: подсказку, сообщение, красную подсветку, подтверждение, переход, маску, справочник/теги, date-window boundary или другой visible pass/fail oracle; отсутствие fixture/catalog/backend/test clock допускает только узкий `GAP-*` на заблокированную часть;
- `Test Design Decision Table` отправляет в `gap_unclear` source-backed save/no-save behavior для видимого UI-поля, хотя значение можно проверить повторным открытием того же объекта/раздела;
- package/table-based writer output имеет `numeric-format` или `amount-tags` в `Source Table Normalization`, но не имеет `Coverage Obligation Table` либо пропускает обязательные classes `valid-digits`, `reject-letters`, `reject-spaces`, `reject-special-chars`, `reject-decimal-separator`, `reject-sign`, `dictionary-values-shown`, `tag-selection-fills-field`;
- source или plan содержит `exact-length`, но нет `exact-length-accepted`, `shorter-rejected`, `longer-rejected` rows или узких `GAP-*`;
- source или plan содержит action-created block, но нет optional no-action branch или `GAP-*` для обязательности добавления;
- source или plan содержит repeatable block, но нет lifecycle rows для второго независимого блока и удаления одного из нескольких или `GAP-*`;
- source или plan содержит checkbox/multi-select list, но нет rows для обязательности, single/multiple selection и снятия выбора, когда они применимы;
- source или plan содержит generated document / print form, но `print-form-generated` и `print-form-content-mapping` смешаны в одной проверке или content mapping объявлен covered без source-backed mapping;
- applicable dimension из `Test-design Applicability Matrix` отсутствует в `coverage-metrics.md` или metrics показывают uncovered obligation без `TC-*`/`GAP-*`;
- negative transition / submit-blocking TC нажимает `Следующий шаг` или аналогичный transition action без named full-valid fixture, где все unrelated required fields для выбранной ветки раскрыты конкретными значениями; generic формула `все остальные поля заполнены валидно` недостаточна без linked `fixture-catalog.md`;
- high-risk atom отсутствует в `risk-priority-map.md`, не имеет `impact`, `likelihood`, `risk_score`, `risk_level`, или high-impact atom понижен без residual risk decision;
- package-based writer output имеет `Package Test Design Plan`, но не имеет `test-design-review.md`, пропускает required review items или содержит любую строку `Test Design Review` со `status = fail | blocked | needs-rewrite` и `blocks_ready_for_review = yes`;
- шаги TC остаются общими (`ввести или выбрать`, `привести данные к состоянию`, `нажать действие при необходимости`), хотя доступны mockup interaction hints;
- `Mockup Usage` содержит `used_for_steps = yes`, но шаги TC игнорируют mechanics элемента из inventory и используют общий текст вроде `в поле <...> ввести значение из тестовых данных`, `найти область` или `найти элемент`;
- шаги TC остаются общими (`Подготовить ветку`, `Сравнить состояние поля с ожидаемым правилом ФТ`, `Проверить соответствие ФТ`, `Проверить поле согласно ФТ`, `Выполнить проверку значения`);
- non-list `value-type` atom закрыт list-selection TC: например источник говорит `тип значения: Строка`, `Дата` или `Логическое Да/Нет`, но TC открывает list/reference selector и выбирает значение без source evidence, что поле действительно list-backed;
- non-list `value-type` atom закрыт standalone generic acceptance вроде `поле принимает и отображает введенное строковое значение`, а не конкретным source-backed format/input/widget behavior или `GAP-*`;
- dependency TC содержит setup placeholder `В форме задать данные, при которых ...` вместо конкретного controlling field, точного значения и действия пользователя;
- `Type: Positive` используется для rejection/invalid/no-save oracle, включая значения выше max или ниже min;
- `Type: Negative` используется для TC, чей expected result только принимает/отображает/сохраняет валидное значение и не содержит rejection, invalid, no-save или error oracle;
- requiredness считается покрытым через заполнение поля; marker checks должны наблюдать видимый required indicator, а enforcement checks должны оставлять поле пустым и запускать подтвержденное validation action;
- expected result только пересказывает правило ФТ (`соответствует ФТ`, `поле принимает только ...`, `поле обязательно к заполнению`) без observable pass/fail oracle;
- expected result использует source-rule oracle (`по правилу из источника`, `по правилу видимости из источника`, `согласно источнику`, `согласно ФТ`) вместо конкретного observable state;
- expected result использует generic rule-oracle вроде `видимое состояние после действия соответствует одному наблюдаемому правилу этой строки` или `поле изменяет, отображает или ограничивает значение без утверждения внутренних эффектов` вместо точного observable state;
- expected result вставляет raw source text как oracle, например `наблюдается правило из GSR N: ...`;
- expected result содержит DOCX/PDF extraction artifacts: split words, table-header residue, соседние строки таблицы, `Д а`, `П о`, `Рефинансировани е`, `Переключат ель`;
- expected result для negative/validation TC допускает альтернативные реакции через `или`, например `значение очищено, не сохранено или поле подсвечено ошибкой`, вместо одного deterministic observable oracle;
- expected result для negative/validation TC использует вариант `символ отклонен или значение остается незаполненным/предыдущим`; source-backed input restriction сам по себе не доказывает конкретный UI enforcement mechanism;
- runtime-поля canonical TC содержат agent-process английские формулировки, например `source-backed`, `runtime-prose`, `semantic projection`, `manifest digest`, `runner-owned` или `exact credit-conveyor screen`;
- numeric/input-restriction rejection TC ожидает очистку поля, неотображение введенного значения, отфильтрованные символы, красную подсветку, сообщение об ошибке, blocked transition или неоткрытие следующего раздела без прямого source evidence именно на этот UI feedback; правило `не принимает значение`, `только цифры` или `ниже минимума не принимается` доказывает только класс недопустимого значения, а не способ UI-реакции;
- writer заменяет один unsupported numeric/input oracle другим unsupported oracle: например после запрета `значение не отображается` или `значение очищено` переписывает TC на `поле подсвечено красным` / `Следующий шаг заблокирован` / `Анкета клиента не открыта` без нового source/UI/support evidence для invalid class. Это остается blocking `tc-regression-smells`, а не remediation.
- executable `TC-*` ссылается на `GAP-*` как на unresolved механизм действия, feedback или exact oracle, но при этом заявляет baseline pass/fail вместо split на проверяемую инвариантную часть и отдельный gap;
- шаг `TC-*` содержит несколько возможных UI labels/actions через `/`, `alias` или `или`, например `Добавить дополнительный доход / Добавить источник дохода`, вместо одного наблюдаемого action label;
- setup/recovery behavior вроде очистки checkbox/list state или снятия всех выборов представлен как source-backed baseline TC без source evidence;
- numeric `test_data` использует raw numeric value как class label, например `Допустимое значение: 123456; класс: 12345`, вместо semantic class вроде `6 digits`, `exact length N`, `N-1`, `N` или `N+1`;
- `GAP-*` появляется в ledger, matrices, TC notes или self-check, но отсутствует в split artifact `coverage-gaps.md`;
- gap-only / metadata-only / `unclear` placeholder представлен как `## TC-*` вместо `Coverage Gaps`, ledger, Package Test Design Plan или traceability matrix;
- gap-only / fixture-context source row включена в executable routing текущего scope: для таких строк допустимы только `out_of_scope`, narrow `GAP-*`, fixture note или явное решение `not executable in this scope`, но не `standalone_tc`, covered ledger row или planned executable TC;
- `Test-design Applicability Matrix` помечает `numeric = no`, хотя тот же artifact содержит numeric-only / digits-only / length / min/max source rules;
- mockup-only UI elements повышаются до `covered` requirements вместо фиксации как `mockup_only_items`, `FT conflicts`, `GAP-*` или out-of-scope;
- one-shot PowerShell argument, here-string, inline giant command или другой command-line transport выбран для большого Markdown artifact, включая случаи, где это отражено в `writer-session-log.md` как первый failed write method before fallback;
- ad-hoc `tmp/generate_*.py` или local generator используется как primary writer для canonical test cases вместо file-based/chunked writing или committed helper under `scripts/`;
- `GSR N-M` указан в `covered` atom, когда диапазон содержит больше трех requirement codes и atom не разбит на отдельные atomic rows;
- combined source/atom/plan wording вроде `requiredness and format`, `visibility and requiredness`, `visibility and format`, `conditional visibility and format`, `dependency and validation`, `length and repeated digits`, `condition=true/false`, `previous data branches`;
- combined normalization property classes вроде `term_dictionary_and_bounds`, dictionary source + min/max boundary, requiredness + editability или format + boundary в одном `source_property_id`;
- conditional/dependency rows имеют только true/applicable ветку и не имеют inverse negative branch или `GAP-*`;
- field/input validation rows покрывают rejection/invalid input, но не имеют positive acceptance sibling или `GAP-*`;
- expected behavior вроде `validate by FT rules`, `same constraints`, `соответствует GSR N-M` или другие ссылки откладывают фактический oracle на диапазон вместо одной проверки;
- validation TC содержит placeholder data или steps вроде `значение, нарушающее указанное правило`, `значение из проверяемого класса по ФТ`, `дата, соответствующая проверяемой ветке ФТ`, `ввести или выбрать значение из тестовых данных`;
- traceability fields contain placeholder elements such as `; \`-\`;`, `N/A`, empty id slots, or fake ids instead of real `ATOM-*`, requirement code, source row, section/table/page or `DICT-*` references;
- editability TC uses generic steps like `Активировать элемент` and `Изменить значение на тестовое значение` without concrete old/new literal values and an expected result naming the new displayed value;
- dictionary/list TC checks only presence of expected active values when the source/support inventory defines a closed list and the expected result does not state absence of extra values;
- `v2 obligation`, exploratory, risk-derived or other test-design-derived checks are presented as direct FT atoms without `source_or_rule_ref` / defect-class / coverage-dimension derivation;
- read-only/list-composition/visibility TC uses template postcondition `Вернуть измененные данные...` even though the steps do not change data;
- boundary design проверяет только off-boundary rejection (`min-1`, `max+1`, `P_min - Delta`, `P_max + Delta`) без отдельных exact-boundary acceptance checks (`min`, `max`, `P_min`, `P_max`);
- `scenario` TC покрывает широкий requirement range, пока atomic TC для базовых проверок отсутствуют;
- один `TC-*` используется как `planned_tc_or_gap` для нескольких independent executable design rows;
- `covered` action/async TC в expected result только говорит, что действие инициировано/начато, без named observable UI/API/log/mock/document artifact;
- requirement code parity mismatch: `GSR`/`REQ` появляется в ledger/TC, но указывает на другое field, condition или expected behavior, чем source/parity artifact;
- writer self-check содержит фразы вроде `possible merged checks = known risk`, если нет соответствующей blocking gate row и workflow переведен в `ready-for-review`.

## Правило Workflow

Writer не должен ставить `stage_status: ready-for-review`, пока не выполнено:

- `Writer Quality Gate` существует;
- `Test Design Review` существует и проходит, если существует `Package Test Design Plan`;
- `Source Row Inventory` существует, если используется package/source-table flow;
- `Dictionary Inventory` существует и связан с downstream `DICT-*`, если source/support содержит справочники или fixed lists;
- scoped validator run выполнен после финальной записи canonical TC и split artifacts;
- `scoped-validator-findings = pass` подтвержден runner-generated `outputs/scoped-validator-profile.<stage>.json` с `generated_by: codex_review_cycle_runner` либо runner validator gate output; generic `validator.json` не принимается;
- profile stage is the current writer stage, not a future reviewer/preflight/regression stage;
- отсутствие запуска scoped validator после финальной записи не является валидной причиной для `stage_status: blocked-input`; это procedural failure writer-а. Если validator технически не смог выполниться, writer должен зафиксировать attempted command, stderr/exception, affected path и concrete follow-up, а не писать `Validator not run`;
- current-scope validator `warning`/`error` либо отсутствуют, либо каждая finding строка явно зафиксирована как валидный `false-positive`/waiver с id, path, evidence и rationale; process-only формулировки вроде `pre-existing`, `unchanged`, `not introduced` не являются достаточным waiver для writer-ready handoff;
- каждая строка с `blocks_ready_for_review = yes` имеет `status = pass`;
- ни один package не имеет unresolved gate failure;
- required rewrite либо выполнен package-by-package, либо workflow переведен в `blocked-input`.

Если package не проходит gate, writer переписывает affected package начиная с `Source Table Normalization`, затем заново строит ledger, `Package Test Design Plan`, TC и gate rows до перехода к следующему package.

`Writer Quality Gate` не может иметь общий итог `pass`, если `scoped-validator-findings` содержит unresolved current-scope `warning`/`error`. В этом случае writer обязан исправить affected artifacts или перевести workflow в `blocked-input`; передача на reviewer с расчетом на последующий разбор validator blockers запрещена.
