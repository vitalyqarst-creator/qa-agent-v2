# Writer Quality Gate Format

`Writer Quality Gate` - обязательный split artifact `work/test-design/<scope-slug>/writer-quality-gate.md` перед `Writer Self-Check`.

Цель gate: не допустить явно слабый writer draft до full review. Это не заменяет reviewer, а отбраковывает draft, который нарушает базовую атомарность, декомпозицию или observability.

Человекочитаемые поля `evidence` и `required_action` пиши на русском языке, если пользователь явно не запросил другой язык. Технические имена колонок, gate items, enum-значения, ids и имена файлов остаются каноническими.

## Минимальный Формат

```md
## Writer Quality Gate

| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- |
| `artifact-write-strategy` | `pass` | Большой/package artifact использует `scripts/write_artifact_sections.py --manifest <manifest.json>`. | `all` | - | `no` |
| `mockup-visual-inventory` | `pass` | `mockup-visual-inventory.md` открыт и дал подсказки по взаимодействию. | `WP-01` | - | `no` |
| `source-row-inventory` | `pass` | Каждая in-scope строка handoff присутствует и сопоставлена с `ATOM-*` или `GAP-*`. | `WP-01` | - | `no` |
| `source-normalization-atomic` | `pass` | Source rows содержат по одному property/condition/behavior. | `WP-01` | - | `no` |
| `dictionary-inventory` | `pass` | `dictionary-source` rows используют `DICT-*` из `dictionary-inventory.md`. | `WP-01` | - | `no` |
| `test-design-decision-table` | `pass` | Каждый `source_property_id` имеет одно design decision до ledger/TC writing. | `WP-01` | - | `no` |
| `coverage-obligation-table` | `pass` | `numeric-format` и `amount-tags` разложены на обязательные coverage classes с `TC-*`/`GAP-*`. | `WP-01` | - | `no` |
| `test-design-review` | `pass` | `test-design-review.md` не содержит blocking rows. | `WP-01` | - | `no` |
| `gap-admissibility` | `pass` | Все `GAP-*` проверены: visible UI/API behavior не спрятан в gap, mixed rows split-нуты. | `WP-01` | - | `no` |
| `tc-regression-smells` | `pass` | В canonical TC отсутствуют placeholder traceability, source-rule oracle, generic editability steps и read-only template postconditions. | `all` | - | `no` |
| `semantic-compression` | `fail` | `ATOM-017` закрывает `GSR 34`-`GSR 58` одним scenario TC. | `WP-02` | Переписать package от Source Table Normalization до TC. | `yes` |
```

## Обязательные Gate Items

- `artifact-write-strategy`: большие/package-based writer outputs имеют preflight-стратегию записи и используют file-based/chunked writing до генерации контента.
- `mockup-visual-inventory`: UI scopes с макетами имеют `mockup-visual-inventory.md`; макет открыт, а подсказки по взаимодействию используются только для шагов без превращения mockup-only элементов в требования.
- `source-row-inventory`: каждая in-scope/unclear source row из handoff `source-row-inventory.md` присутствует в writer-side inventory до normalization и сопоставлена с `ATOM-*`, `GAP-*` или явным out-of-scope решением.
- `source-normalization-atomic`: normalized source rows содержат одно чистое property, condition или behavior; каждая строка имеет `source_property_id`; source rows с несколькими `GSR`/`REQ` имеют `Source Row Completeness Matrix`; normalization row не несет несколько independently checkable requirement codes и не смешивает semantic property classes, например dictionary source + min boundary + max boundary, visibility + requiredness или format + boundary.
- `test-design-decision-table`: каждый нормализованный `source_property_id` имеет ровно одно решение: `standalone_tc`, `covered_by_existing_tc`, `gap_unclear`, `metadata_only`, `scenario_only` или `out_of_scope`; metadata-only rows не создают executable `TC-*`; gap/metadata/scenario-only decisions согласованы с ledger, Package Test Design Plan, Risk / Priority Map и `TC-*`; standalone TC decisions имеют observable oracle.
- `coverage-obligation-table`: mandatory property types (`numeric-format`, `exact-length`, `action-created-optional-block`, `repeatable-block-lifecycle`, `checkbox-list`, `print-form-output`, `amount-tags`, `format-mask`, `default-mask`) разложены на обязательные classes с `TC-*`/`GAP-*`.
- `coverage-metrics`: каждая applicable dimension имеет counted obligations/classes/branches/transitions, covered count и gap/unclear count по `test-design-coverage-metrics-format.md`.
- `fixture-catalog`: reusable baselines и negative transition fixtures раскрыты в `fixture-catalog.md` или полностью в TC.
- `risk-priority-map`: high-risk atoms имеют `impact x likelihood`, priority и residual risk decision по `risk-priority-map-format.md`.
- `gap-admissibility`: `gap_unclear` и `GAP-*` не скрывают проверяемые подсказки, сообщения, красную подсветку, видимость, действия, переходы, маски, справочники/теги, date-window boundaries или другие source-backed observable outcomes; смешанные testable/blocked требования split-нуты.
- `test-design-review`: `test-design-review.md` существует для package-based `initial_draft`, совместно проверяет TDDT/ledger/plan/gaps и не содержит blocking failed rows.
- `ledger-atomicity`: `ATOM-*` rows не объединяют независимые visibility, requiredness, editability, format, boundary, dependency, persistence, integration или action behavior.
- `gsr-range-compression`: covered atoms не используют широкие диапазоны `GSR N-M` как замену декомпозиции.
- `design-plan-atomicity`: одна executable plan row имеет один `check_type`, один `input_class`, один `single_expected_behavior` и один `TC-*`/`GAP-*`.
- `scenario-does-not-replace-atomic`: scenario/use-case TC являются дополнительными и не заменяют atomic positive, negative, boundary, dependency или action TC.
- `tc-atomicity`: `TC-*` не объединяют независимые pass/fail decisions.
- `test-data-specificity`: validation/boundary/equivalence TC используют конкретные значения или именованные классы, а не placeholders вроде `значение, нарушающее правило`.
- `tc-regression-smells`: canonical TC file не содержит повторяющиеся canary-defects: placeholder `-` / `N/A` в traceability fields, expected result `по правилу из источника`, generic editability steps `Активировать элемент` + `Изменить значение на тестовое значение`, dictionary TC без `все и только активные значения`, test-design-derived checks без source/rule derivation (`derived-obligation-contamination`), шаблонное cleanup-постусловие в read-only TC.
- `internal-observability`: internal/API/RabbitMQ/model/database behavior без observable artifact остается `GAP-*`/`unclear`.
- `action-observability`: action/async TC со статусом `covered` называют конкретный observable result или artifact; `action initiated` без evidence остается `GAP-*`/`unclear`.
- `semantic-req-id-parity`: requirement codes связаны с тем же source statement/field/expected behavior, что и в source parity, а не просто присутствуют где-то в файле.
- `package-ready`: каждый `WP-*` прошел package ledger, design-plan и TC gates.

## Условные Gate Items

- `dictionary-inventory`: обязателен, если `source-table-normalization.md` содержит `dictionary-source`, `amount-tags`, `tag-values`, `table-list`, `checkbox-list` или аналогичный reference-list property; `dictionary-inventory.md` должен иметь matching `DICT-*`, а TDDT/plan/TC должны ссылаться на этот `DICT-*` или узкий `GAP-*`.

## Блокирующие Паттерны

Writer должен ставить `status = fail` и `blocks_ready_for_review = yes`, если есть:

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
- negative transition / submit-blocking TC использует generic valid baseline без `fixture-catalog.md` и без полного раскрытия baseline в TC;
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
- numeric `test_data` использует raw numeric value как class label, например `Допустимое значение: 123456; класс: 12345`, вместо semantic class вроде `6 digits`, `exact length N`, `N-1`, `N` или `N+1`;
- `GAP-*` появляется в ledger, matrices, TC notes или self-check, но отсутствует в split artifact `coverage-gaps.md`;
- gap-only / metadata-only / `unclear` placeholder представлен как `## TC-*` вместо `Coverage Gaps`, ledger, Package Test Design Plan или traceability matrix;
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
- каждая строка с `blocks_ready_for_review = yes` имеет `status = pass`;
- ни один package не имеет unresolved gate failure;
- required rewrite либо выполнен package-by-package, либо workflow переведен в `blocked-input`.

Если package не проходит gate, writer переписывает affected package начиная с `Source Table Normalization`, затем заново строит ledger, `Package Test Design Plan`, TC и gate rows до перехода к следующему package.
