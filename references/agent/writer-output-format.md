# Writer Output Format

Этот reference фиксирует, какие артефакты должен создавать `ft-test-case-writer` и где они должны храниться.

## Назначение

- отделить формат результата writer-а от процедурных инструкций skill-а;
- не создавать конкурирующие версии тест-кейсов вне canonical path;
- сделать handoff к reviewer воспроизводимым без истории чата;
- сохранить atomic-ledger-first подход для initial draft.

## Canonical Test-Case File

Основной результат writer-а хранится только здесь:

```text
fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md
```

Файл должен содержать:

- metadata по FT package, scope, source и режиму writer-а;
- границы покрытия выбранного scope;
- ссылки на canonical test-design artifacts из `work/test-design/<scope-slug>/`;
- краткий human summary по покрытию, gaps и готовности к review без дублирования полных таблиц;
- тест-кейсы в формате `references/qa/test-case-format.md`, сгруппированные по функциональности/блоку/элементу/операции с единой сквозной нумерацией `TC-*` в пределах файла;

Файл не должен содержать runtime/debug diagnostics: PowerShell/Bash/heredoc notes, stdout/stderr encoding dumps, mojibake samples, extractor debug logs или technical workaround narratives. Такие сведения храни только в session logs, debug artifacts или work folders.

Не вставляй в canonical test-case file полные таблицы `Source Row Inventory`, `Source Table Normalization`, `Test Design Decision Table`, `Coverage Obligation Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, `Coverage Map`, `Coverage Gaps`, `Writer Quality Gate` и другие table-heavy design artifacts, если для scope есть `work/test-design/<scope-slug>/`. Дублирование создает два источника истины и должно блокировать clean validation.

Не создавай второй canonical test-case file для того же scope. Если нужен snapshot, он хранится в `work/review-cycles/<scope-slug>/versions/<snapshot-id>/`, а не заменяет canonical file.

## Canonical Test-Design Artifacts

Для `initial_draft` writer хранит table-heavy design artifacts отдельно от набора `TC-*`:

```text
fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/
```

Имя папки должно совпадать со stem canonical test-case file: для `test-cases/2.3-osnovnaya-informaciya-ui.md` используй `work/test-design/2.3-osnovnaya-informaciya-ui/`.

Канонические файлы:

| artifact | purpose |
| --- | --- |
| `artifact-write-strategy.md` | preflight и способ записи больших/package-based artifacts |
| `mockup-usage.md` | как mockup использован для UI steps и где он не является source of truth |
| `source-row-inventory.md` | writer-side inventory всех source rows внутри scope |
| `source-row-completeness-matrix.md` | доказательство разложения source rows с несколькими кодами/свойствами |
| `source-table-normalization.md` | нормализованные `source_property_id`: одно свойство/условие/поведение на строку |
| `test-design-decision-table.md` | решение, как проверять каждый `source_property_id` или почему отдельный TC не нужен |
| `coverage-obligation-table.md` | обязательные классы покрытия для property types вроде `numeric-format` и `amount-tags` до plan/TC |
| `atomic-requirements-ledger.md` | стабильные `ATOM-*` id и статус coverage |
| `internal-work-package-coverage.md` | gates и статус по каждому `WP-*` |
| `package-ledger-self-check.md` | self-check атомарности ledger по package |
| `package-test-design-plan.md` | executable design rows, gaps and coverage classes before TC writing |
| `package-design-plan-self-check.md` | self-check полноты design plan |
| `test-design-review.md` | обязательная критика TDDT, Coverage Obligation Table, ledger и Package Test Design Plan перед финальным gate |
| `dependency-matrix.md` | условные ветки, controlling fields/actions и gaps |
| `test-design-applicability-matrix.md` | применимость coverage dimensions |
| `risk-priority-map.md` | risk/priority rationale and high-risk coverage |
| `combinatorial-coverage-table.md` | optional pairwise/combinatorial decisions when applicable |
| `coverage-map.md` | итоговая writer coverage map |
| `coverage-gaps.md` | все `GAP-*` и открытые вопросы writer-а |
| `writer-quality-gate.md` | admission control перед reviewer |
| `writer-self-check.md` | итоговый self-check writer-а |

Canonical test-case file должен ссылаться на эти файлы в секции `Canonical Artifact Links` и может содержать короткие summary tables, но не полные копии table-heavy artifacts.

## Test-Case Set Organization

Writer отвечает за финальную читаемость canonical test-case file до передачи на review:

- группируй `TC-*` по функциональности, блоку, элементу формы, бизнес-операции или внутреннему work package; для каждого scope packages обязательны;
- внутри группы сохраняй порядок проверок из `test-case-format.md`;
- не перезапускай нумерацию внутри групп: числовой суффикс `TC-*` должен быть сквозным в пределах файла без дублей и пропусков;
- после перенумерации обновляй все ссылки на `TC-*` в canonical file, split test-design artifacts, writer-created traceability artifacts и writer response artifact текущего round;
- не перенумеровывай signed-off набор без нового revision и повторного review.

## Внутренние Рабочие Пакеты Scope

Каждый подтвержденный scope должен иметь внутренние рабочие пакеты в `scope-contract.md`. Writer обязан использовать их как рабочий план перед созданием `TC-*`. Для простого scope это один пакет `WP-01`; отсутствие packages в новом `scope-contract.md` является blocking input issue, а не поводом писать плоский набор.

Правила:

- все человекочитаемые поля split artifacts и canonical test-case file пиши на русском языке, если пользователь явно не запросил другой язык; технические имена колонок, enum-значения, ids, имена файлов и traceability refs оставляй каноническими;
- не начинай писать тест-кейсы, пока для каждого `package_id` не понятны focus, source_refs, included_requirements и design_method;
- обрабатывай scope package-by-package, а не одним плоским списком атомов;
- для каждого package сначала создай normalization rows, `Test Design Decision Table` и `Coverage Obligation Table` только этого package, затем строки ledger только этого package и выполни package ledger self-check;
- не переходи к `TC-*` package, пока ledger package содержит generic atoms вроде `Требование GSR N выполняется`, `см. GSR/source row` или пересказ без проверяемого expected behavior;
- после ledger создай `Package Test Design Plan` для этого package из obligation rows и выполни package design-plan self-check;
- после `Package Test Design Plan` выполни `Test Design Review` по `test-design-review-format.md`: сверяй TDDT, ledger, plan, coverage gaps и supporting matrices, а не только строки плана;
- не переходи к `TC-*` package, пока plan не перечисляет positive checks, negative/equivalence classes, boundary classes, dependency/action branches и `GAP-*` для непроверяемого behavior, когда эти dimensions применимы;
- не переходи к `TC-*` package, пока `Test Design Review` не имеет blocking rows для этого package;
- после plan создай исполнимые `TC-*` только для этого package и выполни package TC self-check;
- не переходи к следующему package, пока текущий package не имеет явного результата: `covered`, `gap` или `unclear` по каждому atom;
- каждый `ATOM-*` должен относиться к одному основному `package_id`;
- каждый `TC-*` должен указывать `package_id` в источнике требования или в отдельной строке metadata;
- один `TC-*` не должен закрывать независимые проверки из разных packages, кроме явно разрешенного scenario/use-case package;
- если package требует отдельного метода test-design, например `dependency matrix`, `decision table`, `equivalence-boundary` или `integration artifact gate`, writer обязан создать соответствующую таблицу, `TC-*` или `GAP-*` до передачи на review;
- если рабочий пакет оказался слишком большим или блокирующим, не сжимай проверки внутри `TC-*`; зафиксируй `split_required = yes` / `coverage gap` и верни задачу на уточнение scope.

Split artifact `internal-work-package-coverage.md` должен содержать краткую секцию `Internal Work Package Coverage` для каждого initial draft. Canonical test-case file может держать только summary по packages.

Минимальная секция package gate:

| package_id | focus | ledger_gate | design_plan_gate | tc_gate | atoms | covered | gap | unclear | TC count | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | `...` | `pass | blocked` | `pass | blocked` | `pass | blocked` | `...` | `...` | `...` | `...` | `...` | `ready-for-review | blocked-input` |

## Artifact Write Strategy И Preflight

Для больших/package-based writer artifacts штатный путь записи - `scripts/write_artifact_sections.py --manifest <manifest.json>`. Это обязательный helper для больших generated files; он передает Markdown через UTF-8 файлы и manifest, а не через командную строку.

`scripts/update_markdown_section.py --content-file` / `--stdin` допустим для небольших точечных правок одной секции. Не используй его как основной writer большого canonical file, если файл собирается из многих секций.

Перед генерацией или записью canonical test-case file и split test-design artifacts writer обязан выбрать способ записи артефактов.

Если выполняется хотя бы одно условие, writer должен заранее выбрать file-based/chunked writing, не дожидаясь ошибки Windows command-line limit:

- ожидается больше `20` `TC-*`;
- ожидается больше `30` `ATOM-*`;
- ожидаемый Markdown больше `20 000` символов;
- scope имеет один или несколько `WP-*`;
- scope требует `Source Table Normalization`, `Package Test Design Plan` или других крупных split artifacts.

Для таких scope split artifact `artifact-write-strategy.md` должен содержать секцию:

```md
## Artifact Write Strategy

| item | value | evidence |
| --- | --- | --- |
| preflight_result | `large-file / package-based` | `TC count estimate: 98; ATOM estimate: 122; WP-01..WP-06` |
| write_method | `file-based manifest/chunked writing` | `scripts/write_artifact_sections.py --manifest <manifest.json>` |
| forbidden_methods_checked | `yes` | no one-shot PowerShell argument, no here-string, no inline giant command |
| chunk_plan | `WP-01 -> WP-02 -> ...` | one package at a time |
| helper_artifacts | `none` или committed `scripts/<helper>.py` | no ad-hoc `tmp/generate_*.py` as primary writer |
| validation_plan | `<when validation runs>` | after large chunk / after each WP / final |
```

Правила:

- большие Markdown artifacts записывай через manifest helper: `scripts/write_artifact_sections.py --manifest <manifest.json>`;
- небольшие одиночные section edits можно записывать через файл/stdin: `scripts/update_markdown_section.py --content-file <path>` или `--stdin`;
- не передавай большой Markdown через PowerShell argument, here-string, inline Python/Node command или одну длинную команду;
- не используй `tmp/generate_*.py` как основной writer больших test-case files; если нужен generator, он должен быть committed helper в `scripts/` с понятным входом/выходом и тестами;
- temp content files допустимы только как транспорт для `--content-file`; они не должны содержать hidden generation logic;
- если write strategy меняется во время работы, обнови `Artifact Write Strategy` и `writer-session-log.md` до передачи на review.
- если `writer-session-log.md` фиксирует, что первая попытка записи была one-shot PowerShell / here-string / inline giant command и только после ошибки произошел fallback на chunked writing, это считается нарушением preflight, даже если итоговый файл записан полностью.

Отсутствие `Artifact Write Strategy` у большого или package-based scope является validator warning и должно блокировать clean `--fail-on warning` прогон.
Выбор one-shot PowerShell / here-string / inline giant command в строке `write_method` также является validator warning `artifact-write-strategy-forbidden-initial-method`.

## Mockup Visual Inventory

Если подтвержденный UI scope содержит источник типа `mockup` или путь `mockups/*`, writer обязан использовать `mockup-visual-inventory.md` до написания `TC-*`.

Правила:

- `mockup-visual-inventory.md` создается по [mockup-visual-inventory-format.md](mockup-visual-inventory-format.md) и хранится в текущей handoff-папке scope;
- writer не должен начинать `Package Test Design Plan` и `TC-*`, пока не проверил, что inventory содержит `opened = yes`, `visible_blocks`, `visible_fields`, `visible_actions`, `interaction_hints`, `mockup_only_items`, `ft_conflicts`, `used_for_steps` и `not_used_as_requirement_source = yes`;
- макет используется для точности шагов: какой элемент нажать, где выбрать значение, где отметить чекбокс, где ожидать модальное окно, как называется UI alias;
- макет не используется как источник бизнес-правил, обязательности, allowed values, backend/API behavior или expected result, если это не подтверждено ФТ/support;
- если в макете есть элемент, которого нет в ФТ, writer фиксирует `mockup_only_items` / `GAP-*`, а не создает covered TC;
- если ФТ и макет конфликтуют, приоритет у ФТ; конфликт фиксируется в inventory и при необходимости в coverage gaps;
- если макет не удалось открыть визуально, writer должен оставить workflow в `blocked-input`, а не писать generic шаги.

В split artifact `mockup-usage.md` добавь короткую секцию:

```md
## Mockup Usage

| item | value | evidence |
| --- | --- | --- |
| inventory | `work/stage-handoffs/<scope>/mockup-visual-inventory.md` | `opened=yes` |
| used_for_steps | `yes/no` | `<WP/TC refs>` |
| not_used_as_requirement_source | `yes` | `FT/support define behavior` |
| mockup_only_items | `<GAP-* or ->` | `<handling>` |
```

Отсутствие inventory у UI scope с mockup должно блокировать `ready-for-review`.

## Chunked Artifact Writing И Запрет Compact Draft

Writer не должен снижать детализацию результата из-за технического ограничения записи файла, длины командной строки, размера patch, контекста или времени.

Для больших artifacts используй `scripts/write_artifact_sections.py --manifest <manifest.json>`. Для небольших одиночных section edits можно использовать `scripts/update_markdown_section.py` с `--content-file` или `--stdin`. Не передавай большой Markdown как аргумент PowerShell, here-string или одну длинную команду: это воспроизводит Windows command-line limit и провоцирует compact draft.

Для большого/package-based scope chunked artifact writing является штатным способом записи, а не fallback после ошибки:

1. создать или обновить каркас canonical file с metadata, coverage boundaries, ссылками на split artifacts и `TC-*` sections;
2. записывать строго по одному `WP-*` в split artifacts: Source Table Normalization rows, Test Design Decision Table rows, Coverage Obligation Table rows, ledger rows этого package, Package Test Design Plan rows этого package, затем `TC-*` этого package в canonical test-case file;
3. после каждого package обновлять split artifacts `internal-work-package-coverage.md`, `coverage-gaps.md` и `writer-self-check.md`;
4. запускать доступную валидацию после крупного chunk или после каждого package, если это дешево;
5. продолжать со следующего package без сжатия уже записанных строк;
6. ставить `ready-for-review` только после полной записи всех packages.

Запрещено:

- создавать `compact draft`, `summary draft`, `минимальный валидируемый draft` или аналогичный сокращенный результат;
- сначала пробовать one-shot запись большого Markdown и только после ошибки переходить к chunked writing;
- объединять несколько `GSR`/`REQ`/строк ФТ в один широкий `ATOM-*` только для уменьшения размера файла;
- пропускать `Test Design Decision Table` или `Coverage Obligation Table` и сразу превращать каждую строку `Source Table Normalization` в `TC-*`;
- объединять positive/negative/boundary/dependency/action checks в одну строку Package Test Design Plan ради компактности;
- сокращать `TC-*` до generic placeholders, если полноценная запись уперлась в технический лимит;
- проходить validator ценой потери атомарности.

Если writer не может продолжить chunked writing без риска потерять требования, он должен оставить `stage_status: blocked-input`, указать техническую причину в `blocking_reasons` и не передавать набор на review.

## Source Row Inventory

Если scope строится по таблицам полей, таблицам действий, PDF/DOCX extraction или другому табличному источнику, writer обязан создать `Source Row Inventory` перед `Source Table Normalization`.

Writer-side inventory хранится в split artifact `work/test-design/<scope-slug>/source-row-inventory.md`. Handoff inventory из stage-handoff остается отдельным input artifact и не заменяется writer-side версией.

Если handoff содержит отдельный `source-row-inventory.md`, writer-side inventory должен быть сверкой с ним, а не новой самостоятельной попыткой перечислить строки источника. Все in-scope rows из handoff inventory должны остаться в writer output как `ATOM-*`, `GAP-*` или явное out-of-scope решение.

Используй [source-row-inventory-format.md](source-row-inventory-format.md) как canonical format.

Минимальные колонки:

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |

Правила:

- каждая source row внутри подтвержденного scope должна быть перечислена до атомаризации;
- каждая in-scope source row из handoff `source-row-inventory.md` должна быть сохранена в writer-side inventory;
- `in_scope = yes` требует `mapped_atom_or_gap` с `ATOM-*` или `GAP-*`;
- строка источника не может исчезнуть между source/parity artifact, normalization и ledger;
- `Source Table Normalization` может делить одну source row на несколько атомарных свойств, но каждый `source_row_id` normalization должен существовать в inventory;
- отсутствие строки source в inventory является blocker-ом writer-pass, а не обычным reviewer finding.

## Source Table Normalization

Если scope строится по таблицам полей, таблицам действий, PDF/DOCX extraction или другому табличному источнику, writer обязан создать `Source Table Normalization` перед `Atomic Requirements Ledger`.

Canonical placement: `work/test-design/<scope-slug>/source-table-normalization.md`.

Используй [source-table-normalization-format.md](source-table-normalization-format.md) как canonical format.

Минимальные колонки:

| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Правила:

- одна строка normalization table = одно очищенное свойство поля, действие, условие или ожидаемое поведение;
- `source_property_id` обязателен для каждой строки normalization и должен иметь стабильный вид `<source_row_id>.P##`;
- если source row содержит несколько `GSR`/`REQ` или несколько самостоятельных свойств, writer обязан создать `Source Row Completeness Matrix` и доказать, что каждый код/свойство стал отдельным `source_property_id`, `ATOM-*` или `GAP-*`;
- normalization row не должна содержать несколько `GSR`/`REQ`, если эти коды могут pass/fail независимо; пример: `GSR 1` numeric-only, `GSR 2` max, `GSR 3` min и `GSR 4` amount tags должны быть четырьмя rows, а не одним `ATOM-*`;
- normalization row не должна смешивать разные semantic property classes. `dictionary-source`, `min-boundary`, `max-boundary`, `numeric-format`, `visibility`, `requiredness`, `editability`, `default-value`, `integration-prefill` — это разные строки с разными `source_property_id`, даже если они относятся к одному `GSR` или все временно идут в `GAP-*`;
- если строка источника говорит “значение берется из справочника; min/max берутся из продуктового каталога”, writer обязан создать отдельные rows для dictionary source, min boundary source и max boundary source;
- каждая normalization row должна быть связана с `linked_atoms` или `gap_id`; не оставляй нормализованное свойство без решения;
- не переноси в ledger заголовки таблиц, номера страниц, соседние поля или колонки вроде `Название / Видимость / О / Р / Тип ввода поля / Тип значения / Примечание`;
- если строка extraction загрязнена соседним полем или table-header residue, восстанови чистую строку по источнику либо поставь `confidence = low` и свяжи ее с `GAP-*`;
- `confidence = low` или `confidence = unclear` не может напрямую стать `covered` atom;
- не переходи к `Atomic Requirements Ledger`, пока normalization rows текущего `WP-*` не прошли self-check;
- если нормализовать строку без домысливания невозможно, оставь `stage_status: blocked-input` или `GAP-*`, а не создавай загрязненный `ATOM-*`.

## Test Design Decision Table

Если split artifact содержит `Source Table Normalization`, writer обязан создать `Test Design Decision Table` перед `Atomic Requirements Ledger`.

Canonical placement: `work/test-design/<scope-slug>/test-design-decision-table.md`.

Используй [test-design-decision-table-format.md](test-design-decision-table-format.md) как canonical format.

Минимальные колонки:

| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Правила:

- каждая `source_property_id` из `Source Table Normalization` должна иметь ровно одну decision row;
- `Source Table Normalization` отвечает на вопрос “что сказано в источнике”, а `Test Design Decision Table` отвечает на вопрос “как это проверять или почему это не отдельный TC”;
- допустимые `decision`: `standalone_tc`, `covered_by_existing_tc`, `gap_unclear`, `metadata_only`, `scenario_only`, `out_of_scope`;
- `standalone_tc` допустим только при наличии конкретного observable oracle и planned/existing `TC-*`;
- `covered_by_existing_tc` допустим только если указан реальный executable `TC-*` и объяснено, почему отдельный TC не нужен;
- `gap_unclear` должен ссылаться на объявленный `GAP-*` и пройти admissibility check: `blocked_part` содержит только реально непроверяемую часть, а `testable_part` пустой;
- если source row содержит наблюдаемый результат: подсказку, сообщение, красную подсветку, видимость, доступность действия, переход, маску, справочник/теги, подтверждение или другой pass/fail oracle, эта часть должна идти в `standalone_tc` / `covered_by_existing_tc`, а не в общий `gap_unclear`;
- `metadata_only` не должен ссылаться на executable `TC-*`; если старый `TC-*` id нужно сохранить только для совместимости review artifacts, он допустим только как `traceability-remap` section и не считается покрытием;
- dependency/conditional rows должны явно назвать controlling field, controlling value/action и branch; если этого нет в источнике или mockup/handoff, используй `gap_unclear`;
- internal/API/RabbitMQ/model/database behavior без подтвержденного observable artifact получает `gap_unclear`;
- отсутствие fixture, справочника, catalog value, backend artifact или test clock не отменяет проверяемую UI-часть требования; смешанные строки split-ятся на executable coverage и узкий `GAP-*`;
- решения `metadata_only`, `gap_unclear` и `scenario_only` должны быть синхронизированы с downstream sections: ledger, Package Test Design Plan, Risk / Priority Map и `TC-*` не могут объявлять executable coverage, если TDDT отправляет свойство в metadata/gap/remap route;
- не переходи к ledger, Package Test Design Plan или `TC-*`, пока decision table текущего `WP-*` не прошел self-check.

## Coverage Obligation Table

Если `Source Table Normalization` содержит property types с обязательными классами покрытия, writer обязан создать `Coverage Obligation Table` перед `Atomic Requirements Ledger` и `Package Test Design Plan`.

Canonical placement: `work/test-design/<scope-slug>/coverage-obligation-table.md`.

Используй [coverage-obligation-table-format.md](coverage-obligation-table-format.md) как canonical format.

Правила:

- `numeric-format` обязан раскладываться минимум на `valid-digits`, `reject-letters`, `reject-spaces`, `reject-special-chars`, `reject-decimal-separator`, `reject-sign`;
- `amount-tags` обязан раскладываться минимум на `dictionary-values-shown` и `tag-selection-fills-field`;
- `date-passport-validity` обязан раскладываться на окна до 14 лет, 14-20 + 45 дней, 20 + 1 день - 45 + 45 дней и 45+ бессрочно, если эти окна есть в source/PDF;
- `hint-behavior`, `validation-message`, `red-highlight`, `action-confirmation`, `action-navigation` и `address-required-components` раскладываются на видимые trigger/result obligations; отсутствие интеграционной фикстуры не должно убирать UI obligation;
- каждая obligation row должна ссылаться на `source_property_id`, `linked_atom_id`, `source_ref` и `TC-*` или `GAP-*`;
- если класс неприменим или непроверяем из-за отсутствия fixture/source/support data, строка все равно остается в таблице со ссылкой на конкретный `GAP-*`;
- `Package Test Design Plan` для таких свойств строится из obligation rows, а не напрямую из общего atom/requirement text.

## Atomic Requirements Ledger

В `initial_draft` ledger обязателен.

Canonical placement: `work/test-design/<scope-slug>/atomic-requirements-ledger.md`.

Одна строка ledger = одно атомарное утверждение ФТ или одно отдельное проверяемое правило.

Перед созданием ledger writer обязан прочитать `source-parity-check.md`, если для подтвержденного scope доступны основной DOCX и PDF. Все mandatory requirement IDs из этого artifact, включая PDF-only коды, должны быть сохранены в `req_id` или `source_reference`. Отсутствие обязательного parity artifact является blocking input issue: writer не должен ставить `stage_status: ready-for-review`.

Requirement code guardrail:

- если в подтвержденном scope есть буквенно-цифровой код требования, например `GSR 22`, `REQ-15` или иной локальный код ФТ, каждая связанная строка ledger должна сохранить этот код в `source_reference` или отдельном поле `req_id`;
- не заменяй код требования только номером раздела, названием поля или пересказом;
- сохранение кода требования означает semantic parity: `req_id` должен быть связан с тем же полем/действием, condition и expected behavior, что и в source/parity artifact; нельзя переносить `GSR` на соседнюю строку таблицы или другое утверждение ради формального присутствия кода;
- каждый код требования внутри scope должен иметь минимум один `ATOM-*` или строку traceability matrix;
- если код содержит несколько самостоятельных утверждений, раздели их на несколько `ATOM-*` с тем же кодом требования;
- если утверждение под кодом нельзя покрыть тест-кейсом, оставь его в ledger/matrix со статусом `gap` или `unclear`; не удаляй код из трассировки ради чистой coverage map.

Strict atom atomicity:

- одна строка `ATOM-*` не должна объединять независимые свойства поля или поведения, например видимость, обязательность, редактируемость, значение по умолчанию, формат, границы, persistence, API call, async event и downstream routing;
- если одно предложение ФТ содержит `A и B`, но `A` и `B` могут пройти/упасть независимо, это два атома. Примеры: `4 числовых символа` и `нет трех одинаковых цифр подряд`; `6 числовых символов` и `нет шести одинаковых цифр подряд`; `действие выполнено` и `RabbitMQ получил сообщение`;
- если FT строка или абзац содержит несколько проверяемых обязанностей системы, writer обязан разделить их на несколько `ATOM-*` или явно зафиксировать непроверяемую часть как `gap` / `unclear`;
- `coverage_status = covered` допустим только когда связанный `TC-*` проверяет condition и expected behavior именно этого атома;
- если часть составного требования покрыта, а часть не имеет наблюдаемого artifact или ожидаемого результата, не помечай весь атом `covered`; раздели атом либо оставь непроверяемую часть `gap` / `unclear`.
- `ATOM-*` с диапазоном кодов вроде `GSR 1`-`GSR 4` допустим только если все коды действительно описывают одно проверяемое правило с одним condition и одним expected behavior; если диапазон содержит видимость, обязательность, формат, границы, default, integration, persistence или action behavior, split обязателен.
- Широкий `ATOM-*`, появившийся после ошибки записи файла или лимита команды, считается compact draft defect, а не допустимой оптимизацией.

Правило разделения позитивных и негативных классов:

- один тест-кейс не должен одновременно доказывать, что недопустимое значение отклоняется, а допустимое значение принимается;
- если шаги, тестовые данные или итоговый ожидаемый результат содержат формулировки вида `не принимает X и принимает Y`, `валидное и невалидное значение`, `отклоняет X и принимает Y`, раздели проверку на отдельные `TC-*`;
- для ограничения ввода один `TC-*` проверяет один недопустимый класс, например буквы, спецсимволы, пробелы или смешанную строку, если такой класс следует из ФТ или допустим как проверка класса эквивалентности;
- отдельный позитивный `TC-*` нужен для допустимого класса, если он требуется для покрытия или как контроль работоспособности поля;
- не используй позитивный ввод как второй шаг негативного кейса, кроме отдельного сценария восстановления после ошибки; в таком сценарии итоговый ожидаемый результат должен проверять именно восстановление после ошибки, а не закрывать позитивный класс того же правила.
- не используй placeholder test data: `значение, нарушающее правило`, `значение из проверяемого класса`, `дата, соответствующая проверяемой ветке`, `тестовые данные не требуются` для format/validation. Укажи конкретное значение или именованный класс с примером: `abc`, `123`, `1111`, `12345`, `1234567`, `user@example.com`, `user1@example.com user2@example.com`, если такой пример не противоречит ФТ.
- `класс` в тестовых данных должен быть смысловым классом, а не вторым сырым значением. Правильно: `Допустимое значение: 123456; класс: 6 digits` или `класс: exact length N`. Неправильно: `Допустимое значение: 123456; класс: 12345`, потому что это выглядит как другой input и скрывает ошибку покрытия.

Правило для `тип значения`:

- `тип значения: Строка`, `тип значения: Дата`, `тип значения: Логическое Да/Нет` - это metadata/input type, а не доказательство, что поле открывает справочник или список;
- не закрывай такой `value-type` atom тест-кейсом вида `открыть контрол и выбрать значение из списка`, если source row не говорит `значение из списка`, `справочник`, `перечень`, `dropdown` или аналогичный источник значений;
- не закрывай `тип значения: Строка` отдельным TC вида `поле принимает и отображает введенное строковое значение`, если source row одновременно задает numeric/date/phone/email/length/format constraints или не задает отдельного наблюдаемого behavior для value type. В таком случае покрывай value-type через конкретные format/input/widget проверки или оставляй metadata-only row как `GAP-*` / `unclear`;
- для `Строка` покрытие должно быть через подтвержденный format/input rule, editable/input behavior или `GAP-*`, если из ФТ нельзя вывести наблюдаемую проверку;
- для `Дата` покрытие должно быть через date input/calendar behavior или date validation classes, если они заданы;
- для `Логическое Да/Нет` покрытие должно быть через toggle/checkbox/segmented control state или explicit allowed states, если это наблюдаемо в UI/source.

Правило для dependency setup:

- шаг `В форме задать данные, при которых ...` запрещен как executable step, если он не называет конкретное управляющее поле, точное значение и действие пользователя;
- правильно: `Установить переключатель "Клиент менял паспорт" в "Да"` / `Выбрать "Ввести вручную" = "Да"` / `Очистить поле "Тип занятости"`;
- неправильно: `В форме задать данные, при которых выполняется условие источника для "Номер"`;
- если controlling value или способ установки условия не описан в ФТ/mockup/handoff, создай `GAP-*` / `unclear`, а не executable TC.

Правило для oracle:

- expected result не должен быть generic rule-oracle вида `видимое состояние после действия соответствует одному наблюдаемому правилу этой строки` или `поле изменяет, отображает или ограничивает значение без утверждения внутренних эффектов`;
- expected result не должен быть source-dump oracle вида `Для <поле> наблюдается правило из GSR N: <сырой текст ФТ>`; raw `GSR`/source quote допустим в traceability/source quote, но не как итоговый ожидаемый результат;
- expected result не должен содержать extraction-мусор из DOCX/PDF: разорванные слова (`Д а`, `П о`, `Рефинансировани е`, `Переключат ель`), table headers (`Название Видимость О Р Тип ввода поля Тип значения Примечание`) или соседние строки таблицы;
- expected result должен назвать конкретное наблюдаемое состояние: поле отображается/скрыто, доступно/недоступно, значение принято/отклонено, маркер обязательности виден, переход выполнен/не выполнен, сообщение/подсказка отображается, либо ссылка на `GAP-*`, если oracle не выводится.

Минимальные поля ledger:

- `atom_id`;
- `req_id`, если в ФТ есть буквенно-цифровой код требования;
- `source_reference`;
- `atomic_statement`;
- `field_or_block`;
- `condition`;
- `expected_behavior`;
- `coverage_status`.

Допустимые значения `coverage_status`:

- `covered`;
- `gap`;
- `unclear`.

Если writer использует traceability matrix вместо отдельного ledger, matrix должна содержать те же атомарные утверждения и стабильные id. Для каждой создаваемой или обновляемой traceability matrix обязателен `.xlsx`-дубль traceability matrix.

`atom_id` является стабильным ключом между writer ledger, traceability matrix, reviewer findings и writer response. Не меняй `atom_id` при обычной правке текста тест-кейса. Если reviewer finding ссылается на `traceability_ref = ATOM-*`, revision response должен сохранить эту ссылку или явно описать split/merge атомарного утверждения.

## Package Test Design Plan

For `initial_draft`, split artifact `package-test-design-plan.md` must include `Package Test Design Plan` after `Atomic Requirements Ledger` and before finalizing `TC-*`.

Use [package-test-design-plan-format.md](package-test-design-plan-format.md) as the canonical format.

Minimum columns:

| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- one row = one planned check or one explicit `GAP-*`;
- one executable row = one `TC-*`; one `TC-*` must not be reused as a shortcut for several independent design rows;
- every `package_id` from `scope-contract.md` must appear in the plan;
- every applicable `ATOM-*` must appear in at least one plan row or be linked to `GAP-*`;
- do not use generic `planned_check` values like `проверить требование`, `проверить выполнение GSR`, `валидное/невалидное значение`, `установить условие`;
- `check_type` должен быть одним значением, например `positive`, `negative`, `boundary`, `dependency`, `action-flow`, `scenario` или `gap`; slash-combinations вроде `positive/negative`, `boundary/format`, `integration/gap` запрещены;
- `input_class` должен описывать ровно один класс входа/ветку: `valid numeric`, `letters`, `N-1`, `N`, `N+1`, `condition=true`, `condition=false`; значения вроде `valid and invalid`, `валидное/невалидное`, `любые данные` запрещены;
- `single_expected_behavior` должен содержать один проверяемый oracle, а не пару результатов вида `X отклоняется и Y принимается`;
- validation rules must split positive checks, negative equivalence classes and boundary classes before TC writing;
- `only if`, conditional visibility and action-flow rules must split allowed/forbidden or true/false branches before TC writing;
- internal/API/RabbitMQ/model/database behavior without observable artifact must map to `GAP-*`;
- each executable plan row must name exactly one `TC-*` in `planned_tc_or_gap`; if one manual scenario is needed to prove recovery or end-to-end flow, model it as a separate `scenario` / `recovery` row and keep atomic positive/negative rows separate;
- if the plan is incomplete, do not set `stage_status: ready-for-review`.

## Baseline And Revalidation Carry-Over

Before creating or revising a canonical test-case file, writer must check whether the current FT package, same scope, or explicitly supplied comparison package already contains an existing baseline, revalidation artifact, reviewer finding, traceability matrix, or writer-eval finding for the same scope.

Existing baseline conflict rule:

- if an existing baseline or revalidation artifact treats an assertion as `gap` / `unclear`, writer must not silently promote the same assertion to `covered`;
- if writer believes the newer scope has a source that resolves the gap, the canonical test-case file must name that source and explain why the older limitation no longer applies;
- if no resolving source exists, preserve the limitation as `gap` / `unclear` and carry it into the coverage map, applicability matrix, risk map and writer self-check;
- conflicts with an existing baseline are blocking for `ready-for-review` unless the conflict is explicitly explained and traceable.

Revalidation lesson carry-over:

- reviewer/writer-eval findings from prior `ui-main-info` or same-scope revalidation are mandatory regression inputs when they are explicitly supplied or located in the current FT package workflow;
- repeated lessons such as no fake coverage for internal/integration behavior must be applied before writer handoff;
- do not treat a newly generated from-scratch file as independent of known same-scope regression lessons.

## Internal And Integration Coverage

No internal/integration coverage without observable artifact:

- do not mark `kladr`, saved attributes, `esiaUserId`, `CorrelationId`, API calls, message sends, RabbitMQ events, async waiting/retry, DB/model persistence, absence of downstream calls, or internal routing as `covered` unless the scope defines a confirmed observable artifact for pass/fail verification;
- acceptable artifact sources include explicitly approved UI observation, API/log/DB/RabbitMQ evidence, mock/stub verification contract, or another package material that names how the result is observed;
- user-facing save/no-save behavior for fields visible in the same UI object is not automatically an internal persistence gap. If the source states that data is saved, not saved, restored, or discarded, and the object/section can be reopened through the in-scope UI flow, the displayed value after reopening is an acceptable UI observation. In that case create an executable `persistence` / `no-save` TC instead of requiring a DB/API/log artifact.
- only route persistence to `GAP-*` / `unclear` when the persisted effect is internal-only, cross-system, has no in-scope way to reopen or observe the value, or the source does not state the save/no-save outcome.
- vague steps such as `проверить модель данных`, `проверить бэк`, `проверить вызов`, `проверить сохранение`, or `проверить очередь` are not sufficient by themselves;
- if only the user-facing initiation is observable, split it from the internal result: the initiation may be covered, while persistence/API/async effects remain `gap` / `unclear`;
- action/async expected result вида `действие инициируется`, `запускается проверка`, `отправка инициирована` не является покрытием без конкретного наблюдаемого результата: UI message/state, navigation, enabled/disabled action state, approved log/API/mock/document artifact или другой явно разрешенный evidence source. Если такого artifact нет, action atom остается `gap` / `unclear`.
- `Test-design applicability matrix` and `Risk / Priority Map` must still mark `integration`, `async`, or `persistence` as applicable when present in FT, but link unobservable parts to `GAP-*` instead of fake `TC-*` coverage.

## Test-design Applicability Matrix

For `initial_draft`, split artifact `test-design-applicability-matrix.md` must include a `Test-design applicability matrix` before finalizing test cases and coverage.

The matrix is the writer's explicit decision record for which coverage dimensions apply to the confirmed scope. It prevents silent omission of roles, statuses, APIs, async behavior, integrations, security, tables, files, calculations, or other dimensions that are present in the FT.

Minimum columns:

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `<coverage_dimension>` | `yes | no | unclear` | `<FT section / GSR / table row / field>` | `<why applicable/not applicable/unclear>` | `ATOM-* | -` | `TC-* | -` | `GAP-* | -` |

Rules:

- `dimension` must use the coverage dimension vocabulary from `references/qa/review-findings-format.md`.
- `applicable = yes` requires at least one linked `ATOM-*` and either `linked_test_cases` or `gap_id`.
- `applicable = unclear` requires `gap_id`.
- `applicable = no` requires a concrete `source_ref` or reason proving absence/out-of-scope; do not use `no` to skip work silently.
- Если artifact содержит numeric-only / digits-only / min/max / length constraints, dimension `numeric` не может быть `no`; ставь `yes` с `TC-*`/`GAP-*` links или `unclear` с `GAP-*`.
- If any applicable dimension has no test case and no gap, writer must not set `stage_status: ready-for-review`; use `stage_status: blocked-input` or keep the handoff out of review until the gap is explicit.

## Coverage Metrics

For `initial_draft`, split artifact `coverage-metrics.md` must include `Test-design Coverage Metrics` by `test-design-coverage-metrics-format.md` before `Writer Quality Gate`.

Rules:

- every `applicable = yes` row from `Test-design applicability matrix` must have a metrics row or a linked split artifact with counted obligations/classes/branches/transitions;
- metrics count `TC-*`, `GAP-*` and `unclear` separately;
- combinatorial metrics must record selected `2-way | 3-way | t-way` strength and prove pair/triple coverage by generator output or manual table;
- writer must not set `ready-for-review` when an applicable dimension has no metric or has uncovered obligations without `TC-*`/`GAP-*`.

## Fixture Catalog

For `initial_draft` and `revision_from_findings`, split artifact `fixture-catalog.md` must follow `fixture-catalog-format.md` when reusable baseline data or negative transition fixtures are used.

Rules:

- generic phrases such as `валидные данные`, `валидная заявка` or `минимальный валидный набор` are allowed only when resolved to a fixture row or fully expanded inside the TC;
- negative transition checks must identify the valid baseline and the single invalid delta being tested;
- if a required fixture cannot be made reproducible from source/support materials, create `GAP-*` / `unclear` instead of executable TC.

## Risk / Priority Map

For `initial_draft`, split artifact `risk-priority-map.md` must include a `Risk / Priority Map` when the confirmed scope contains high-risk atoms or high-risk coverage dimensions.

Use `risk-priority-map-format.md` for the canonical `impact x likelihood`, `risk_score`, `risk_level`, `required_priority` and residual risk fields.

High-risk dimensions usually include `role-permission`, `status-lifecycle`, `api-server-validation`, `integration`, `security`, `file-upload`, `calculation`, and any atom involving money, access rights, data loss/corruption, irreversible state transitions, critical business validation, or external side effects.

Minimum columns:

| atom_id | coverage_dimension | impact | likelihood | risk_score | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | residual_risk_decision | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-*` | `<coverage_dimension>` | `1..5` | `1..5` | `<impact x likelihood>` | `high | medium | low` | `money | access-control | data-loss | irreversible-state | critical-calculation | server-side-rejection | security | integration | ...` | `<FT section / GSR / REQ>` | `High | Medium | Low` | `TC-* | -` | `GAP-* | -` | `none | accepted-with-gap | deferred-by-scope | blocked-input` | `<why this priority is justified>` |

Rules:

- `risk_level = high` requires `required_priority = High`.
- Each high-risk atom must link to at least one `TC-*` with `Priority: High` or to a blocking `GAP-*`.
- Low-frequency/high-impact atoms remain high risk when `impact = 5` even if `likelihood` is low.
- If the expected result for a high-risk atom cannot be derived from the FT, do not lower priority; create a blocking coverage gap.
- Accepted residual risk keeps the `GAP-*` visible and must not mark the atom as covered.
- Medium and low rows may link to `Medium` / `Low` test cases, but the rationale must explain why the risk is not high.
- Do not use priority to express execution order, convenience, or how easy the case is to automate.

## Combinatorial Coverage Table

Если `pairwise` применим, split artifact `combinatorial-coverage-table.md` должен содержать combinatorial coverage table до финализации тест-кейсов или coverage map.

Минимально зафиксируй:

- factors and values;
- source reference для каждого фактора;
- constraints и impossible combinations;
- selected combinations with explicit `coverage_strength = 2-way | 3-way | t-way`;
- high-risk combinations, добавленные сверх selected strength;
- generator output or manual proof that required pairs/triples are covered;
- excluded combinations и причину исключения;
- `TC-*` или `GAP-*` для каждой выбранной или проблемной комбинации.

Pairwise table не заменяет decision table для бизнес-правил с явными ветками результата. Если ФТ задает конкретную ветку, она должна быть покрыта напрямую, даже если pairwise уже выбрал похожую комбинацию.

## Coverage Map

Coverage map размещается в split artifact `coverage-map.md` после набора тест-кейсов или после ledger. Canonical test-case file может содержать только краткий coverage summary.

Минимально фиксируй:

- количество atomic statements;
- количество covered / gap / unclear;
- список uncovered atoms;
- список тест-кейсов, которые покрывают несколько atom id;
- известные ограничения покрытия.

Coverage map не заменяет reviewer traceability matrix. Это writer self-control artifact перед review.

## Coverage Gaps And Open Questions

Writer не должен закрывать gaps предположениями.

Если gap уже описан в `scope-coverage-gaps.md`, writer должен:

- сохранить его смысл;
- не менять scope без нового handoff;
- указать, как gap повлиял на test-case set;
- не превращать `working-assumption` в требование ФТ.

Если writer обнаружил новый gap внутри подтвержденного scope, он фиксирует его в split artifact `coverage-gaps.md` и, если результат нельзя честно передать на review, переводит `workflow-state.yaml` в `stage_status: blocked-input`.

Каждый `GAP-*`, который встречается в ledger, applicability/risk/dependency matrices, Package Test Design Plan, `TC-*`, coverage notes, Writer Quality Gate или self-check, должен быть объявлен в секции `Coverage Gaps`. Ссылка на `GAP-*` без строки в `Coverage Gaps` считается traceability defect.

`GAP-*` / `unclear` не является тест-кейсом. Не создавай `## TC-*` sections с `type = gap`, `status = unclear` и expected result вида `GAP-009: отдельный observable oracle не выводится...`. Такие строки должны жить в `Coverage Gaps`, ledger, matrix или design plan, но не увеличивать счетчик executable `TC-*`.

Если blocking gap явно принят как deferred risk, writer не закрывает gap и не меняет expected behavior. Вместо этого writer:

- добавляет `accepted_risks` в `workflow-state.yaml`;
- сохраняет ссылку на тот же `GAP-*`;
- указывает owner/role, rationale и revisit condition;
- отражает residual risk в coverage map / writer self-check.

## Writer Self-Check

## Writer Quality Gate

Split artifact heading policy: each split artifact must contain exactly one canonical section heading matching its section title. Accepted levels are `# Section` or `## Section`; missing/wrong headings and adjacent duplicates such as `# Section` plus `## Section` block writer-ready handoff.

Для `initial_draft` перед `Writer Self-Check` обязателен split artifact `writer-quality-gate.md` с секцией `Writer Quality Gate` по [writer-quality-gate-format.md](writer-quality-gate-format.md).


Gate является admission control перед review. Writer не должен ставить `stage_status: ready-for-review`, если gate содержит `status = fail` и `blocks_ready_for_review = yes`.

Перед финальным `Writer Quality Gate` writer обязан выполнить `artifact-shape-preflight`: split artifacts use exact canonical headings/tables, each split artifact has exactly one canonical section heading and must not contain adjacent wrapper headings like `# Source Row Inventory` followed by `## Source Row Inventory`, alias columns are invalid, and canonical TC file must not duplicate split artifact tables. Required table shapes: `| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |`; `| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |`; `| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision |`; `| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |`; `| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |`; `| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |`; `| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |`; `| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |`. `source-row-inventory.md` column `in_scope` accepts only `yes`, `no`, `unclear`, `out-of-scope`; fixture/residual context belongs in notes, `GAP-*`, or `mapped_atom_or_gap`, not in the enum. Details live in [writer-quality-gate-format.md](writer-quality-gate-format.md).

Перед handoff writer также выполняет `placeholder-sentinel-normalization`: в traceability-bearing колонках split artifacts и reviewer matrices нельзя оставлять placeholder `-` / `N/A`. Если значение неприменимо или покрытия нет, укажи явный sentinel с причиной: `not_applicable:covered`, `not_covered:<GAP-ID>`, `unclear:<GAP-ID>`, `no_requirement_code:<source_ref>`, `none_required:<reason>`. Это правило относится к колонкам связей и трассировки (`req_id`, `requirement_code(s)`, `covered_by_tc`, `linked_test_cases`, `planned_tc_or_gap`, `gap_id(s)`, `mapped_atom_or_gap`, `blocked_part`, `gap_admissibility`, `review_notes`, `gap_note`), а не к свободному тексту, где дефис является обычной пунктуацией.

Минимальные gate rows:

- `artifact-shape-preflight`;
- `artifact-write-strategy`;
- `mockup-visual-inventory`;
- `source-row-inventory`;
- `source-normalization-atomic`;
- `test-design-decision-table`;
- `ledger-atomicity`;
- `gsr-range-compression`;
- `design-plan-atomicity`;
- `test-design-review`;
- `gap-admissibility`;
- `scenario-does-not-replace-atomic`;
- `tc-atomicity`;
- `test-data-specificity`;
- `internal-observability`;
- `action-observability`;
- `semantic-req-id-parity`;
- `package-ready`.

Semantic compression является blocker-ом, если writer видит:

- broad `GSR N-M` в `covered` atom без split;
- combined source/atom/plan wording: `requiredness and format`, `visibility and format`, `conditional visibility and format`, `dependency and validation`, `length and repeated digits`, `condition=true/false`, `previous data branches`;
- missing or failed `Test Design Review`, including missing exact-length short/long numeric classes, missing repeated-digit checks, generic gap rows, or TDDT/ledger/plan conflicts;
- scenario/use-case TC, который заменяет атомарные positive/negative/boundary/dependency/action TC;
- one `TC-*` mapped to several independent executable design rows;
- placeholder validation data/steps вместо конкретных значений или классов;
- generic executable steps вроде `Подготовить ветку`, `Сравнить состояние поля с ожидаемым правилом ФТ`, `Проверить соответствие ФТ`;
- `value-type` atom (`тип значения: Строка/Дата/Логическое`) закрывается list-selection TC без source evidence, что поле действительно выбирает значение из списка/справочника;
- `value-type` atom закрывается standalone TC с generic string acceptance (`принимает и отображает введенное строковое значение`) вместо конкретного source-backed format/input/widget behavior;
- dependency TC содержит setup placeholder `В форме задать данные, при которых ...` вместо конкретного controlling field/value/action;
- expected result содержит generic rule-oracle `видимое состояние после действия соответствует одному наблюдаемому правилу ...` вместо конкретного observable state;
- expected result содержит source-dump oracle `наблюдается правило из GSR ...` или DOCX/PDF extraction artifacts вместо нормализованного observable oracle;
- expected result негативного кейса содержит альтернативы через `или`, например `значение очищено, не сохранено или поле подсвечено ошибкой`, вместо одного source-backed observable oracle;
- numeric test data содержит `класс`, записанный вторым сырым числом, например `Допустимое значение: 123456; класс: 12345`;
- `GAP-*` referenced in any canonical section is missing from `Coverage Gaps`;
- gap-only / metadata-only placeholder is represented as `## TC-*` instead of `Coverage Gaps` / matrix / ledger;
- `Test-design Applicability Matrix` marks `numeric = no` while the artifact contains numeric-only / digits-only / length / min/max behavior;
- `Type: Positive` для rejection/invalid/no-save oracle;
- requiredness coverage через заполненное значение вместо visible marker или empty-value validation;
- expected result, который только пересказывает ФТ и не дает observable oracle;
- action `covered` без named observable artifact;
- semantic mismatch между `req_id` и source/parity row;
- writer self-check phrases such as `possible merged checks = known risk`.

Если gate fail относится к одному package, writer обязан вернуться к этому package: пересобрать `Source Table Normalization`, `Test Design Decision Table`, `Coverage Obligation Table`, `Atomic Requirements Ledger`, `Package Test Design Plan` и `TC-*` только для affected package, затем повторить gate. Нельзя маскировать failed gate как residual risk и одновременно передавать файл на review.

## Writer Self-Check

Для `initial_draft` writer self-check обязателен и хранится в split artifact `writer-self-check.md` после `Writer Quality Gate`.

Минимальные пункты:

- source parity checked: `yes | not-applicable | blocked`;
- mandatory requirement IDs preserved: `yes | no | not-applicable`;
- uncovered atoms;
- possible merged checks;
- possible over-splitting;
- test-case grouping and continuous numbering;
- internal work package coverage;
- merged checks across packages;
- packages that require split or unresolved package gaps;
- scoped validator command/equivalent runner gate used after final artifact write;
- scoped validator findings summary with each current-scope `warning`/`error` listed as `fixed`, `false-positive`/waived with evidence, or `blocking`;
- current-scope filtering excludes historical `work/review-cycles/<scope>/versions/` snapshots and `_artifact_write/` scratch files even when the full validator report still lists warnings there; count only active canonical TC, active split test-design artifacts and current cycle outputs;
- post-write scoped validator must actually be executed before writer marks `ready-for-review`, `writer-draft-ready`, `semantic-review-ready` or terminal `blocked-input`; `Validator not run` is not a valid terminal blocker. If the validator cannot execute, record the attempted command, stderr/exception and concrete recovery action;
- assumptions;
- unclear items.
- high-risk atoms without `High` priority test case or blocking `coverage gap`;
- missing or incomplete `Risk / Priority Map` when high-risk dimensions are applicable;
- applicable `pairwise` / `calculation` dimensions without required supporting table or oracle.

Self-check не должен скрывать проблемы. Если self-check содержит blocking uncertainty или unresolved current-scope validator `warning`/`error`, не ставь `stage_status: ready-for-review` / `writer-draft-ready` / `semantic-review-ready`. Writer self-check не может писать `pass` по validator-sensitive gate item только на основании ручного просмотра; он должен ссылаться на scoped validator evidence или runner validator gate evidence.

Writer self-check не должен содержать пустые headings. Каждая секция, включая `Writer Self-Check` и `Artifact Write Evidence`, должна содержать хотя бы одно проверяемое утверждение, таблицу, список evidence, ссылку на `writer-session-log.md` / `artifact-write-strategy.md` или явное `not-applicable` с причиной. Пустая секция считается `writer-self-check-empty-section` и блокирует writer-ready handoff.

Статусы в writer-side review/gate artifacts должны использовать только закрытые enum-ы соответствующего format reference. Не заменяй `pass` на `ok`, `yes`, `passed`, `pass-with-gap` или `pass-with-gaps`; не используй `planned` как итоговый coverage status.

## Revision Output

В `revision_from_findings` writer обновляет существующий canonical test-case file, а не создает новый набор с нуля.

Writer response artifact хранится здесь:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/writer-rN-response.md
```

Legacy handoff aliases may call the same artifact `round-N-writer-response.md`; do not create a second file for that alias.

Он должен соответствовать `references/qa/review-findings-format.md` и содержать response block на каждый finding предыдущего round.

Допустимые resolution statuses:

- `fixed`;
- `not-fixed-scope`;
- `needs-clarification`.

Для response на traceability finding обязательно укажи `affected_traceability_refs` с теми же `ATOM-*` или `coverage_gap:<short-id>`, что были в finding, если только исправление не разделило или не объединило атомарные утверждения. В таком случае `change_summary` должен явно объяснить новое соответствие.

## Handoff To Reviewer

После успешного writer pass:

- canonical test-case file обновлен;
- `workflow-state.yaml` указывает `stage_status: ready-for-review`;
- `next_skill: ft-test-case-reviewer`;
- активный prompt сохранен как `prompt.writer-to-reviewer.round-N.md`;
- `latest_artifacts` содержит актуальные ссылки на writer outputs.

Если writer не может подготовить проверяемый результат без новых решений по scope, missing source, неразрешенных gaps или отсутствующего обязательного input artifact, используй:

```yaml
stage_status: blocked-input
```

и явно заполни `blocking_reasons`.
