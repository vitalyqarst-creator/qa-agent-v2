# Writer Quality Gate Regression

## Цель

Проверить, что writer draft с формально валидным Markdown, но с семантической компрессией требований, не может пройти как `ready-for-review`.

Этот eval фиксирует урок из чистого запуска `fts/ft-2-OF_6` по scope `ui-main-info`: validator до усиления не выдавал warnings, хотя draft содержал broad `GSR` ranges, compressed atoms, merged TC и сценарные строки вместо атомарных проверок.

Дополнительный урок из diagnostic review `fts/ft-2-OF_10`: writer может формально сохранить `GSR` codes и пройти базовую валидацию, но потерять строку source (`Место рождения`), использовать generic steps, пересказывать ФТ в expected result, проверять обязательность заполнением поля и ставить `Type: Positive` на rejection/boundary oracle.

Урок из clean rerun `fts/ft-2-OF_13`: validator не должен полагаться только на человекочитаемые labels вроде `Expected Result`, `Test Data`, `Steps`. Если canonical file использует snake_case-поля `expected_result`, `test_data`, `steps`, все quality-smell checks должны применяться к ним так же строго. Иначе writer может формально пройти gate с generic steps, rule-restatement oracle, невалидным `valid` test data, semantic drift `GSR 116` и скрытым integration/API gap в applicability matrix.

Урок из round 2 review `fts/ft-2-OF_13`: после первой правки writer может заменить один generic-шаблон другим. Gate должен ловить не только конкретную старую фразу, но и новый класс дефектов: `Зафиксировать видимое состояние ... после выполненного действия`, expected result вида `целевой экран или раздел, указанный ... в ФТ`, `equivalence = no` при numeric-only rules, и противоречивую пару `Допустимое значение: 123; класс: ABC`.

Урок из post-signoff audit `fts/ft-2-OF_13`: даже reviewer `signed-off` не является доказательством качества, если validator не ловит повторяемые semantic smells. Gate должен блокировать ложное покрытие `value-type` atoms через list-selection TC, dependency setup placeholders, generic rule-oracles и numeric class labels, записанные как второе сырое число.

Дополнительный урок из focused repair того же `fts/ft-2-OF_13`: writer может закрыть точные warning phrases, но сохранить тот же дефект под новой формулировкой. Gate должен ловить не только старую строку, но и класс ошибки: source-dump oracle `наблюдается правило из GSR ...`, standalone metadata TC для `тип значения: Строка` через generic string acceptance, и DOCX/PDF extraction artifacts в expected results.

Урок из canary v3 `fts/ft-2-OF_16` / `ui-employment-canary-v3-compact`: даже компактный scope может получить `signed-off`, если writer и reviewer принимают слабые negative oracles и исполнимость поверх нерешенного механизма. Gate должен блокировать не размер набора, а конкретные классы дефектов: alternative oracle через `или`, executable TC over unresolved `GAP-*`, ambiguous UI alias steps и derived setup/recovery behavior как source-backed baseline.

## Входной Сценарий

- FT package: новый clean package без чтения соседних `fts/ft-2-OF*`.
- Scope: `ui-main-info`.
- Writer запускается только по handoff artifacts текущего package.
- Reviewer не запускается.
- Writer создает canonical test-case file и переводит `workflow-state.yaml` в `stage_status: ready-for-review`.

## Must-Catch Rules

Validator или pre-review gate должен находить хотя бы один blocking/warning signal, если в writer output есть:

- `covered` atom с широким диапазоном `GSR N-M`, где диапазон скрывает несколько независимых правил;
- `ATOM-*`, объединяющий видимость, обязательность, редактируемость, формат, boundary, dependency, persistence или integration behavior;
- `Package Test Design Plan` строка с объединенными классами проверки или одним `TC-*` для нескольких независимых executable rows;
- `Scenario` / use-case TC, который заменяет атомарные positive/negative/boundary/dependency/action TC;
- `TC-*`, объединяющий valid acceptance и invalid rejection;
- validation/equivalence/boundary `TC-*` с placeholder test data: `значение, нарушающее правило`, `значение из проверяемого класса`, `дата, соответствующая ветке ФТ`, `ввести или выбрать значение из тестовых данных`;
- boundary coverage, в котором есть только rejection для `min-1` / `max+1` / `P_min - Delta` / `P_max + Delta`, но нет отдельной acceptance-проверки exact `min` / `max` / `P_min` / `P_max`;
- правило вида `A и B`, где `A` и `B` могут pass/fail независимо, например length/format + repeated digits;
- action/async `TC-*`, который помечает `covered`, но expected result говорит только `действие инициируется` без observable artifact;
- source-backed save/no-save behavior для видимого UI-поля ошибочно отправлен в `GAP-*`, хотя его можно проверить повторным открытием объекта/раздела и отображаемым значением;
- UI scope с mockup, в котором writer не создал / не прочитал `mockup-visual-inventory.md`, не доказал `opened = yes` или использовал generic UI steps вместо visual interaction hints;
- semantic `GSR` mismatch: код требования присутствует, но привязан к другому полю, condition или expected behavior, чем в source/parity artifact;
- отсутствует `Source Row Inventory` или in-scope source row не связан с `ATOM-*` / `GAP-*`;
- `Source Table Normalization` содержит `source_row_id`, которого нет в `Source Row Inventory`;
- generic executable steps: `Подготовить ветку`, `Сравнить состояние поля с ожидаемым правилом ФТ`, `Проверить соответствие ФТ`, `Проверить поле согласно ФТ`, `Выполнить проверку значения`;
- `Type: Positive` используется для rejection/no-save/invalid oracle;
- `Type: Negative` используется для TC, который вводит только валидное значение и ожидает acceptance/display/save без rejection/invalid/no-save oracle;
- requiredness считается covered через заполнение поля вместо visible required marker или empty-value validation;
- expected result только пересказывает правило ФТ и не называет observable pass/fail oracle;
- snake_case `TC-*` fields (`title`, `test_data`, `steps`, `expected_result`) содержат те же дефекты, что и display-label fields, но обходят extractor;
- generic action/UI step: `Зафиксировать видимое состояние ... после выполненного действия`;
- generic action oracle: `целевой экран или раздел, указанный ... в ФТ`;
- numeric-only TC помечает нечисловое значение вроде `A-123` как `Допустимое значение` / `valid value`;
- positive test data содержит contradictory class label вроде `Допустимое значение: 123; класс: ABC`;
- `value-type` atom вроде `тип значения: Строка/Дата/Логическое` закрывается TC, который открывает список и выбирает значение из справочника;
- dependency TC использует setup placeholder `В форме задать данные, при которых ...` вместо конкретного controlling field/action/value;
- expected result или step использует generic rule-oracle `видимое состояние после действия соответствует одному наблюдаемому правилу ...`;
- expected result использует source-dump oracle `наблюдается правило из GSR N: ...` вместо конкретного observable result;
- negative/validation expected result допускает альтернативные реакции через `или`, включая `символ отклонен или значение остается незаполненным/предыдущим`, вместо одного deterministic oracle или `GAP-*`;
- executable `TC-*` ссылается на unresolved `GAP-*` по ключевому action/feedback/exact oracle, но все равно заявляет baseline pass/fail;
- шаг `TC-*` использует ambiguous UI alias/action через `/`, `alias` или `или`, например `Добавить дополнительный доход / Добавить источник дохода`;
- setup/recovery behavior вроде очистки checkbox/list state или снятия всех выборов представлен как source-backed baseline TC без source evidence;
- `тип значения: Строка/Дата/Логическое` закрывается standalone metadata TC, например `поле принимает и отображает введенное строковое значение`, без конкретного source-backed input/widget/format behavior;
- expected result содержит DOCX/PDF extraction artifacts, split words, table headers or neighboring table spillover, например `Д а`, `П о`, `Рефинансировани е`, `Переключат ель`, `Название Видимость О Р Тип ввода поля Тип значения Примечание`;
- numeric test data использует второй numeric literal как class label, например `Допустимое значение: 123456; класс: 12345`;
- action/button вроде `Следующий шаг` тестируется как обязательное поле, которое можно оставить пустым;
- `Test-design Applicability Matrix` помечает `integration`, `api-server-validation`, `async` или `persistence` как `no`, хотя в файле есть `GAP-*` про API/RabbitMQ/DaData/kladr/Connect/internal behavior;
- `Test-design Applicability Matrix` помечает `equivalence = no`, хотя в файле есть numeric-only / digits-only source rules;
- large/package-based canonical file без `Artifact Write Strategy`, либо strategy не использует `scripts/write_artifact_sections.py`, либо выбирает one-shot command-line write / here-string / inline giant command или ad-hoc `tmp/generate_*.py`;
- writer session log показывает, что первая попытка записи большого canonical file была one-shot PowerShell / here-string / inline giant command и только после ошибки произошел fallback на chunked writing;
- `writer-process-diagnostic*.md` сообщает `verdict: fail`, `process_readiness: contaminated` или `validator_gap_suspected: yes`, но `workflow-state.yaml` остается `ready-for-review`;
- при clean rerun рядом лежат historical и active writer-process diagnostics, но active diagnostic не помечен `active_for_current_workflow: yes` или его `diagnostic_target` не совпадает с active canonical file;
- writer self-check с формулировкой `possible merged checks = known risk`, но workflow все равно переведен в `ready-for-review`;
- internal/API/RabbitMQ/model/database behavior в `covered` без observable artifact;
- видимая UI persistence/no-save ветка в `gap_unclear`, когда ФТ задает outcome и повторное открытие объекта/раздела дает наблюдаемый oracle.

## Pass Criteria

Eval считается успешным, если:

- canonical test-case file содержит `Writer Quality Gate`;
- package-based file без `Writer Quality Gate` получает validator warning `writer-quality-gate-missing`;
- failed gate row дает warning `writer-quality-gate-failed`;
- writer `workflow-state.yaml` со статусом `ready-for-review` и отсутствующим/неполным/failed gate получает error `workflow-state-ready-for-review-without-passing-writer-quality-gate`;
- writer `workflow-state.yaml` со статусом `ready-for-review` получает error `workflow-state-ready-for-review-with-blocking-test-case-smells`, если canonical test-case file содержит blocking quality smells, даже когда `Writer Quality Gate` формально заполнен как `pass`;
- broad covered requirement range ловится как `covered-atom-gsr-range-compression-smell`;
- scenario TC вместо атомарного покрытия ловится как `scenario-tc-replaces-atomic-coverage-smell`;
- placeholder validation data ловится как `test-case-generic-executable-smell`;
- отсутствующий `Source Row Inventory` ловится как `source-row-inventory-missing`;
- in-scope source row без `ATOM-*` / `GAP-*` ловится как `source-row-inventory-in-scope-row-without-atom-or-gap`;
- normalization row без inventory source row ловится как `source-row-inventory-misses-normalized-source-row`;
- generic title ловится как `test-case-generic-title-smell`;
- `Type: Positive` с rejection/no-save oracle ловится как `test-case-positive-type-with-negative-oracle`;
- `Type: Negative` без negative oracle ловится как `test-case-negative-type-without-negative-oracle`;
- requiredness без empty-value или marker check ловится как `test-case-requiredness-without-empty-or-marker-check`;
- expected result как пересказ ФТ ловится как `test-case-generic-expected-result-smell`;
- snake_case `TC-*` fields проверяются теми же quality-smell rules, что и display-label fields;
- `Зафиксировать видимое состояние ... после выполненного действия` ловится как `test-case-generic-executable-smell`;
- `целевой экран или раздел, указанный ... в ФТ` ловится как `test-case-generic-expected-result-smell`;
- nonnumeric valid data в numeric-only TC ловится как `test-case-numeric-only-valid-data-invalid-smell`;
- contradictory valid data class label ловится как `test-case-valid-data-class-label-mismatch-smell`;
- non-list value-type atom through list-selection TC ловится как `test-case-value-type-list-selection-smell`;
- dependency setup placeholder ловится как `test-case-dependency-placeholder-setup-smell`;
- generic rule-oracle ловится как `test-case-generic-rule-oracle-smell`;
- source-dump oracle ловится как `test-case-source-dump-oracle-smell`;
- alternative negative oracle ловится как `test-case-nondeterministic-alternative-oracle-smell`, включая формулировки вида `символ отклонен или значение остается незаполненным/предыдущим`;
- value-type metadata as standalone behavior ловится как `test-case-value-type-metadata-as-behavior-smell`;
- DOCX/PDF extraction artifacts в expected result ловятся как `test-case-extraction-artifact-oracle-smell`;
- numeric raw literal class label ловится как `test-case-numeric-class-label-raw-literal-smell`;
- action/button-as-required-field drift ловится как `test-case-action-treated-as-required-field-smell`;
- hidden integration/API/internal gap в applicability matrix ловится как `test-design-applicability-matrix-hidden-integration-gap`;
- hidden numeric-only equivalence gap в applicability matrix ловится как `test-design-applicability-matrix-hidden-numeric-equivalence-gap`;
- off-boundary rejection без exact-boundary acceptance ловится как `test-case-boundary-rejection-without-on-boundary-acceptance`;
- action initiation without artifact ловится как `test-case-action-without-observable-artifact-smell`;
- generic UI steps при доступных mockup interaction hints ловятся как `test-case-mockup-interaction-hints-not-used`;
- conditional/dependency plan row без inverse branch или `GAP-*` ловится как `test-case-package-design-plan-missing-conditional-branch`;
- invalid/rejection plan row без positive acceptance sibling ловится как `test-case-package-design-plan-negative-without-positive-acceptance`;
- combined length/repeated-digits rows ловятся как combined behavior/class smells в source normalization, ledger или design plan;
- combined visibility/requiredness rows ловятся как combined behavior/class smells в source normalization, ledger или design plan;
- combined dictionary/min/max rows ловятся как `source-normalization-combined-property-class-smell`, даже если они используют один `GSR` и ведут в `GAP-*`;
- `Writer Quality Gate` требует rows `artifact-write-strategy`, `mockup-visual-inventory`, `source-row-inventory`, `test-data-specificity`, `action-observability`, `semantic-req-id-parity`;
- UI scope с mockup без linked/opened `mockup-visual-inventory.md` не проходит writer `ready-for-review`;
- large/package-based file без безопасной `Artifact Write Strategy` получает validator warning `artifact-write-strategy-*`;
- large/package-based file без `scripts/write_artifact_sections.py` получает warning `artifact-write-strategy-helper-missing`;
- forbidden initial one-shot method в `Artifact Write Strategy` ловится как `artifact-write-strategy-forbidden-initial-method`;
- forbidden initial one-shot fallback в `writer-session-log.md` ловится как `session-log-forbidden-initial-one-shot-write`;
- contaminated active `writer-process-diagnostic*.md` рядом с writer handoff ловится как `workflow-state-ready-for-review-with-contaminated-writer-process`;
- inactive historical `writer-process-diagnostic*.md` с `active_for_current_workflow: no` не блокирует clean rerun, если ровно один active diagnostic соответствует clean canonical file and reports `pass/clean/no`;
- запуск `validate_agent_artifacts.py --root <package> --fail-on warning` не проходит для bad draft, даже если базовые markdown-структуры валидны.

## Fail Criteria

Eval провален, если:

- bad draft проходит `--fail-on warning` без findings;
- writer может поставить `ready-for-review` без полного passing `Writer Quality Gate`;
- gate содержит failed/blocked/needs-rewrite строки, но workflow остается валидным для reviewer handoff;
- broad `GSR N-M` остается `covered` без атомарной декомпозиции или `GAP-*`.
- placeholder test data и action-without-artifact проходят как valid `ready-for-review`.
- snake_case test-case fields обходят generic step / expected-result / test-data checks.
- source-dump oracle или extraction artifact можно оставить в expected result и пройти `ready-for-review`.
- standalone `тип значения` TC можно переписать с list-selection на generic string acceptance и пройти gate.
- applicability matrix может ставить integration/API-like dimensions в `no`, несмотря на реальные `GAP-*` по unobservable internal/integration behavior.
- writer может начать с one-shot записи большого Markdown, упереться в command-line limit и затем считать fallback нормальным clean writer path.
- contaminated writer-process diagnostic может лежать рядом с writer handoff, но validator всё равно пропускает `ready-for-review`.
- active diagnostic может указывать не на тот canonical file, но validator всё равно пропускает reviewer routing.

## Regression Lesson

Package-by-package workflow снижает масштаб ошибки, но не заставляет writer остановиться, если он сам видит сжатие. Поэтому нужен отдельный pre-review quality gate: writer обязан отклонить собственный draft до reviewer-а, а validator должен блокировать `ready-for-review`, если gate отсутствует или провален.
