# Рубрика review test-design

Этот reference определяет, как `ft-test-case-reviewer` должен оценивать смысловое качество test-design. Он дополняет `test-case-format.md`, `coverage-checklist.md`, `traceability-rules.md` и `review-findings-format.md`.

Канонический список повторяющихся классов дефектов хранится в `../agent/test-design-defect-taxonomy.md`. Новые классы ошибок добавляй туда, а здесь держи только reviewer-правила и severity.

Reviewer обязан критически проверять заявления writer-а о покрытии. Нельзя считать тест-кейс достаточным только потому, что он ссылается на требование или `ATOM-*`. Тест-кейс приемлем только тогда, когда его шаги и ожидаемый результат позволяют ручному исполнителю принять однозначное решение pass/fail относительно требования.

## Позиция reviewer-а

- Считай каждый тест-кейс writer-а неподтвержденным, пока он не докажет трассируемость, наблюдаемость и атомарность.
- Предпочитай точный blocking finding расплывчатому sign-off.
- Не требуй поведение, которого нет в ФТ, PDF, принятом уточнении или утвержденных материалах пакета.
- Не снижай severity только потому, что дефект часто повторяется в наборе.
- Не создавай findings из-за стилистических предпочтений, если кейс исполним, трассируем и семантически достаточен.

## Минимальный split reviewer roles

Для сложных или high-risk scope review должен состоять минимум из двух независимых passes:

1. `traceability reviewer`: проверяет полноту source/code/atom/TC/gap трассировки и regression diff против baseline/revalidation lessons.
2. `test-design/TC-quality reviewer`: проверяет применимость dimensions, матрицы, атомарность, исполнимость шагов и evidence-first expected results.

Эти passes могут выполняться одним `ft-test-case-reviewer`, но reviewer не должен смешивать критерии. Формальная трассировка не доказывает качество test-design; хороший test-design не компенсирует потерянный `GSR`/`REQ`/`ATOM-*`.

## Рубрика severity

| Severity | Когда использовать | Обязательное действие reviewer-а |
| --- | --- | --- |
| `error` | Тест-кейс не может надежно доказать требование, содержит неподтвержденное поведение, скрывает независимую проверку или блокирует trustworthy sign-off. | Создать blocking finding. Набор нельзя подписывать, пока дефект не исправлен, не вынесен как out-of-scope или не переведен в `unclear` с трассируемой причиной. |
| `warning` | Тест-кейс, вероятно, исполним, но имеет значимую слабость test-design, неполное покрытие веток, слабую наблюдаемость или устранимую неоднозначность. | Создать finding, который writer должен исправить до sign-off, если риск явно не принят как остаточный. |
| `info` | Замечание является неблокирующим улучшением, legacy-заметкой или низкорисковым уточнением, которое не ослабляет pass/fail judgment. | Фиксировать только если это помогает следующей итерации; не раздувать список findings. |

## Non-negotiable дефекты

Эти дефекты являются `error`, если finding явно не относится к out-of-scope:

- Ожидаемый результат недостаточно наблюдаем для pass/fail.
- Ожидаемый результат только повторяет название или цель тест-кейса.
- Ожидаемый результат содержит неподтвержденные точные значения, статусы, сообщения, UI-реакции, порядок нормализации или форматирование.
- Ожидаемый результат использует размытые формулировки вроде `корректно`, `как ожидается`, `согласно системным правилам`, `не ломается`, `должно быть уточнено`.
- Ожидаемый результат использует source-rule oracle вроде `по правилу из источника`, `по правилу видимости из источника`, `согласно источнику`, `согласно ФТ` вместо конкретного наблюдаемого pass/fail состояния.
- Шаг негативного сценария выполняет запрещенное действие так, будто оно успешно, вместо попытки действия и проверки отказа/no-change.
- Проверяемое действие спрятано в предусловиях или тестовых данных вместо шагов.
- Один тест-кейс объединяет независимые бизнес-проверки, которые могут pass/fail отдельно.
- Positive и negative сценарии смешаны в одном тест-кейсе.
- Тест-кейс на ограничение ввода одновременно проверяет, что недопустимое значение отклоняется, а допустимое значение принимается, вместо разделения на отдельные `TC-*` или отдельный восстановительный сценарий.
- Тест-кейс заявляет покрытие `ATOM-*`, но не проверяет condition и expected behavior этого атома.
- Буквенно-цифровой код требования из подтвержденного scope отсутствует в ledger, traceability matrix или ссылках тест-кейсов без явного `gap` / `unclear`.
- Writer создал compact draft / summary draft после технического лимита или свернул несколько `GSR`/`REQ`/строк ФТ в широкий `ATOM-*`, чтобы получить короткий валидируемый файл.
- `ATOM-*` объединяет диапазон кодов требований и несколько независимых свойств поведения: видимость, обязательность, редактируемость, default, формат, границы, integration, persistence, async или action flow.
- `Atomic Requirements Ledger` построен из загрязненного table extraction: в atom/expected behavior попали заголовки колонок, соседние поля, номера страниц или фрагменты следующей строки; при этом нет `Source Table Normalization` с `source_property_id`, `confidence` и `GAP-*`.
- `Source Table Normalization` схлопывает несколько `GSR`/`REQ` или несколько самостоятельных свойств source row в одну строку/один `ATOM-*`; для строк с несколькими кодами нет `Source Row Completeness Matrix`.
- `Source Table Normalization` оставляет разные semantic property classes в одной строке, например dictionary source + min boundary + max boundary, visibility + requiredness, requiredness + editability или format + boundary. Это blocking defect даже если строка ведет в `GAP-*`, потому что reviewer теряет отдельные test-design решения.
- Тест-кейс проверяет детали реализации или UI-механику, которые не указаны в ФТ или утвержденных материалах пакета.
- Тест-кейс по numeric-only ожидает конкретную фильтрацию ввода (`буква не появляется`, `значение очищается`, `отображаются только цифры`) без source evidence.
- Маска формата (`format-mask`, `default-mask`) считается покрытой numeric-only проверкой без отдельного oracle по видимому шаблону/маске.
- Numeric-only правило считается покрытым одним смешанным вводом вроде `12A00` без отдельных классов букв, пробелов, спецсимволов, десятичного разделителя и знака.
- Exact-length правило считается покрытым без отдельных классов `N`, `N-1` и `N+1`.
- Action-created block считается покрытым обязательностью внутренних полей без проверки optional no-action branch или `GAP-*`.
- Repeatable block считается покрытым одним добавлением и одним удалением, хотя source разрешает несколько блоков и не проверена независимость/удаление одного из нескольких.
- Checkbox-list считается покрытым только проверкой состава справочника без выбора одного/нескольких значений, обязательности или снятия выбора, когда эти ветки source-backed.
- Формирование печатной формы считается покрытием корректности данных внутри формы без source-backed content mapping.
- Справочник или фиксированный перечень из ФТ/support workbook не проверен как closed-set и не оформлен как `GAP-*` / `unclear`.
- Негативная проверка перехода/кнопки не задает valid fixture для остальных обязательных полей, поэтому нельзя доказать, что отказ вызван проверяемым условием.
- Исполнимый `TC-*` использует generic fixture/test data вроде `Минимальный валидный набор данных`, `валидные данные`, `валидная заявка` без раскрытого воспроизводимого baseline или linked fixture artifact.
- Expected result использует oracle вида `значение из тестовых данных принято/не принимается`, хотя сами test data не содержат конкретный literal, параметр или строку fixture.
- Строка `Test-design Applicability Matrix` с `applicable = yes` засчитывает metadata-only/source-property atoms как покрытие dimension: например `table-list` содержит atoms про источник значения, технический тип, table extraction residue или другие свойства, не проверяемые этой dimension.
- Строка `Test-design Applicability Matrix` с `applicable = yes` ссылается на `TC-*`, который по шагам, данным и expected result проверяет другую dimension.
- Обязательная зависимость, переход состояния, ветка условной видимости или правило закрытого списка из ФТ не покрыты и не зафиксированы как `gap` / `unclear`.
- `GAP-*` или `gap_unclear` скрывает source-backed observable behavior: подсказку, сообщение, красную подсветку, подтверждение, переход, маску, справочник/теги, date-window boundary, отображаемое сохраненное/несохраненное значение после повторного открытия объекта/раздела или другой pass/fail oracle.
- Один gap смешивает проверяемую UI-часть и недостающий blocker: fixture, справочник, catalog value, backend artifact, статус, test clock или boundary convention.
- Расчетный тест-кейс не содержит formula/source reference, входные значения и вручную вычисленный expected result, хотя расчет является предметом проверки.
- High-risk atom не имеет `High` priority test case и не оформлен как blocking `coverage gap`.
- Applicable dimension не имеет строки в `coverage-metrics.md` или metrics показывают uncovered obligation без `TC-*`/`GAP-*`.
- Reusable baseline / valid fixture используется в TC без `fixture-catalog.md` или полного раскрытия конкретных данных.
- Traceability fields contain placeholder elements such as `; \`-\`;`, `N/A`, empty id slots or fake ids instead of real `ATOM-*`, requirement code, source row, section/table/page or `DICT-*` references.
- Editability TC does not name concrete old/new values, uses generic steps `Активировать элемент` + `Изменить значение на тестовое значение`, or has no expected result with the literal new displayed value.
- Closed dictionary/list TC checks active values but does not verify absence of extra values and does not record closed-set ambiguity as `GAP-*` / `unclear`.
- Test-design-derived check (`v2 obligation`, exploratory, risk-derived, regression-derived) is presented as a direct FT/source atom without source/rule derivation.

## Обязательный defect-class checklist

Reviewer обязан явно попытаться найти следующие классы дефектов до sign-off:

1. `fake internal coverage`: `kladr`, `esiaUserId`, `CorrelationId`, API/DB/RabbitMQ/model/internal state, async waiting/retry или absence of downstream calls помечены `covered` без наблюдаемого artifact.
2. `TC atomarity`: один `TC-*` объединяет независимые проверки или несколько pass/fail решений.
3. `positive+negative merge`: один `TC-*` одновременно проверяет отклонение невалидного значения и прием валидного значения, если это не отдельный recovery scenario.
4. `action in preconditions`: проверяемое действие спрятано в предусловиях или тестовых данных.
5. `lost requirement code`: буквенно-цифровой код требования из scope отсутствует в ledger, matrix или TC links.
6. `missing matrices`: отсутствуют обязательные `Test-design Applicability Matrix`, `Dependency Matrix`, `Decision Table`, `Risk / Priority Map` или package coverage, когда scope/dimension этого требует.
7. `unsupported expected result`: expected result содержит неподтвержденные UI/API/status/message/format details или не дает наблюдаемого pass/fail.
7a. `unsupported-ui-mechanism`: TC/plan требуют конкретную UI-механику без source evidence, особенно фильтрацию numeric-only ввода.
7b. `format-mask-not-covered-by-numeric`: маска формата закрыта только проверкой цифр или общим форматом без видимого шаблона.
7c. `dictionary-closed-set-missing`: справочник/support workbook не превращен в проверку состава отображаемых значений и отсутствия лишних значений либо в `GAP-*`.
7d. `negative-transition-without-valid-fixture`: негативный переход проверяется без валидного baseline состояния остальных обязательных полей.
7e. `applicability-linked-tc-drift`: matrix row linked TC не упражняет указанную dimension.
7f. `false-gap`: проверяемое source-backed behavior целиком отправлено в `GAP-*` / `gap_unclear`.
7g. `overbroad-gap`: gap смешивает проверяемую часть и реально заблокированную часть вместо split.
7h. `metadata-only-behavior`: visible behavior помечено как `metadata_only`.
7i. `date-window-gap`: source-backed date/age windows и точные подсказки не разложены на boundary/equivalence obligations.
7j. `generic-valid-fixture-placeholder`: исполнимый TC зависит от generic valid baseline, который не раскрыт в предусловиях, шагах, test data или linked artifact.
7k. `generic-test-data-oracle`: expected result ссылается на `значение из тестовых данных`, но test data не дают конкретного проверяемого значения.
7l. `applicability-atom-contamination`: строка applicability matrix засчитывает atoms, которые не относятся к указанной dimension или являются metadata-only/non-executable для этой dimension.
7m. `numeric-only-class-gap`: `numeric-format` не разложен на обязательные equivalence classes.
7n. `exact-length-class-gap`: `exact-length` не разложен на `N`, `N-1`, `N+1`.
7o. `repeatable-block-lifecycle-gap`: repeatable block не покрывает независимость нескольких блоков и lifecycle удаления.
7p. `action-created-optionality-gap`: блок, создаваемый действием, не имеет no-action optional branch или `GAP-*`.
7q. `checkbox-list-obligation-gap`: checkbox/multi-select list не покрывает обязательность, single/multiple selection или снятие выбора.
7r. `print-form-content-mapping-gap`: generated document проверяет только факт формирования без source-backed content mapping или gap.
7s. `coverage-metrics-missing`: applicable dimension не имеет измеримого coverage count.
7t. `traceability-placeholder`: `Ссылка на ФТ`, `Трассировка`, ledger или matrix содержит placeholder `-` / `N/A` / fake id.
7u. `source-rule-oracle`: expected result ссылается на `по правилу из источника` / `согласно ФТ` вместо observable oracle.
7v. `generic-editability`: editability TC не раскрывает old/new literal и concrete control action.
7w. `derived-obligation-contamination`: derived coverage check выглядит как новая source-backed строка ФТ.
8. `covered without TC`: atom/requirement имеет `coverage_status = covered`, но не связан ни с одним исполнимым `TC-*`.
9. `package leakage`: `TC-*` смешивает независимые проверки из разных internal work packages.
10. `set organization drift`: набор не сгруппирован по функциональности/блоку/элементу/операции или `TC-*` нумерация перезапускается внутри групп, содержит пропуски либо дубли.
11. `gap drift`: существующий `GAP-*` изменил смысл, affected atoms, blocking status или temporary handling без явного writer response.
12. `compact draft fallback`: writer сообщает о лимите команды/patch/контекста и после этого создает сокращенный ledger, merged design-plan rows или generic TC вместо chunked writing.
13. `source table pollution`: ledger или TC quotes содержат table-header residue вроде `Название / Видимость / О / Р / Тип ввода поля / Тип значения / Примечание`, соседние поля или extraction-мусор, но writer пометил atoms как `covered`.

Если reviewer не нашел дефект класса, это не нужно оформлять отдельным finding; но перед sign-off `Reviewer Sign-off Self-check` должен быть совместим с тем, что эти классы проверены.

## Evidence-first review expected results

Для каждого expected result reviewer задает вопрос:

`Какой наблюдаемый artifact позволяет исполнителю принять pass/fail решение?`

Допустимые artifact-и: UI-состояние, отображаемое значение, доступность действия, отображаемое значение после повторного открытия объекта/раздела, сохраненная запись в разрешенном источнике, API/log/DB/RabbitMQ/mock artifact, явно утвержденный в scope или support material.

Правила:

- Если expected result проверяет внутреннее состояние, API/DB/RabbitMQ/model/persistence/async behavior, но artifact не указан, это `error`.
- Если FT описывает внутренний результат, а scope не дает artifact для его проверки, writer должен оставить `coverage_status = gap | unclear`, а не создавать `TC-*`.
- Если artifact доступен только на UI-automation этапе, baseline manual `TC-*` должен ссылаться на `GAP-*` / `unclear` или явно ограничить expected result пользовательски наблюдаемой частью.
- Формулировки `проверить в модели данных`, `проверить в логах`, `проверить API-вызов` допустимы только если source/handoff называет конкретный разрешенный artifact и способ доступа.

## Traceability diff против baseline/revalidation lessons

Если scope имеет предыдущий signed-off snapshot, revalidation artifact, writer eval report, round findings или пользователь явно дал baseline, reviewer обязан сравнить новый набор с этим baseline.

Проверки:

1. `gap` / `unclear` atoms не должны стать `covered` без нового source или observable artifact.
2. Requirement codes (`GSR`, `REQ`, `ID`, локальные коды ФТ) не должны исчезнуть из ledger/matrix/TC links.
3. Requirement codes должны сохраняться семантически: `GSR`/`REQ` должен указывать на то же поле/действие, condition и expected behavior, что и source/parity row. Формальное присутствие кода при сдвинутом смысле является traceability error.
4. Для UI scope с mockup reviewer обязан проверить `mockup-visual-inventory.md`: макет должен быть визуально открыт, inventory должен фиксировать видимые blocks/fields/actions/interaction hints и guard `not_used_as_requirement_source = yes`. Отсутствие inventory, generic UI steps при доступных interaction hints или использование mockup-only элемента как `covered` requirement без ФТ/source подтверждения является blocking finding.
4. Старые blocking lessons не должны повториться под новыми `ATOM-*` / `TC-*`.
5. `GAP-*` не должен менять смысл, affected dimension, affected atoms или blocking status без writer response.
6. Новый набор не должен противоречить revalidation sign-off rationale.

Если baseline artifact найден, но reviewer не может проверить diff из-за отсутствия ссылок или snapshots, это как минимум `warning`; если новый набор явно противоречит зафиксированному blocker lesson, это `error`.

## Warning-level дефекты

Используй `warning`, когда:

- Отсутствует полезная boundary, equivalence, dependency или negative ветка, но основное требование уже имеет базовый исполнимый кейс.
- Предусловия зашумлены или содержат нерелевантную настройку, которая может запутать исполнение.
- Тестовые данные недоопределены, но недостающая деталь восстановима из шагов или источника требования.
- Кейс атомарен, но название, цель или ссылка на источник замедляют трассировку.
- Проверка списка/справочника покрывает значения, но явно не говорит об отсутствии лишних значений, когда ФТ задает закрытый список.
- Похожие кейсы указывают на over-splitting или under-grouping, но текущая форма все еще исполнима.

## Info-level дефекты

Используй `info` только когда:

- Замечание является legacy-заметкой, а compatible mode валидатора уже трактует его как неблокирующее.
- Кейс приемлем, но небольшая правка формулировки улучшит сопровождаемость.
- Finding документирует ограничение входных данных, например отсутствие PDF cross-check, без изменения решения о sign-off.

## Ревью Test-design applicability matrix

До проверки отдельных `TC-*` reviewer обязан проверить `Test-design applicability matrix` writer-а из canonical test-case file.

Reviewer проверяет:

1. Каждая dimension, видимая в ФТ, scope contract, ledger или coverage map, представлена в matrix.
2. Каждая строка с `applicable = yes` содержит связанные `ATOM-*` и либо связанные `TC-*`, либо связанные `GAP-*`.
3. Каждая строка с `applicable = unclear` содержит связанный `GAP-*` с конкретным вопросом аналитику.
4. Строка с `applicable = no` подтверждена `source_ref` или ясной причиной; reviewer не должен принимать молчаливое отсутствие проверки.
5. Если применимая dimension отсутствует в matrix или не имеет ни `TC-*`, ни `GAP-*`, создай `test-design` / `coverage` finding с `coverage_dimension`.
6. Для каждой строки с `applicable = yes` reviewer обязан открыть связанные `TC-*` и проверить, что шаги, данные и итоговый expected result реально проверяют именно эту dimension. Формальная ссылка на `TC-*` не является покрытием, если кейс проверяет только общий positive flow или другую dimension.
7. Для каждой строки с `applicable = yes` reviewer обязан проверить, что linked `ATOM-*` относятся именно к указанной dimension. Metadata-only atoms, source-table properties, value-source rows, technical type rows и extraction residue не должны засчитываться как coverage dimension; они должны быть вынесены в отдельное решение, `GAP-*`, `metadata_only` или исключены из linked atoms строки.
8. Если связанный `TC-*` не доказывает dimension или linked atoms загрязняют строку другой semantic class, reviewer должен требовать либо доработать/добавить `TC-*`, либо оформить `GAP-*`/исправить matrix; до этого строка matrix считается непокрытой.
9. Reviewer не может подписать набор, пока каждая применимая строка matrix не имеет одного из двух состояний: `covered-by-TC` с проверяемым TC или `covered-by-gap` с явным `GAP-*`, а linked atoms не содержат metadata contamination.

Используй словарь `coverage_dimension` из `review-findings-format.md`. Типовые dimensions включают `role-permission`, `status-lifecycle`, `decision-table`, `pairwise`, `boundary`, `equivalence`, `dependency`, `numeric`, `date-time`, `length`, `persistence`, `scenario-use-case`, `api-server-validation`, `integration`, `security`, `async`, `table-list`, `file-upload`, `calculation`, `performance`, `reliability`, `compatibility`, `usability` и `accessibility-ui`.

## Ревью Risk / Priority Map

Если scope содержит high-risk dimensions или high-risk atoms, reviewer обязан проверить `Risk / Priority Map` из canonical test-case file.

Reviewer проверяет:

1. High-risk atoms присутствуют в map и имеют `impact`, `likelihood`, `risk_score`, `risk_level`, `required_priority` по `risk-priority-map-format.md`.
2. Каждая строка с `risk_level = high` имеет `required_priority = High`.
3. High-risk atom связан хотя бы с одним `TC-*` с `Priority: High` или с blocking `GAP-*`.
4. `risk_factors` объясняют риск конкретно: money, access-control, data-loss, irreversible-state, critical-calculation, server-side-rejection, security, integration или другой явно названный фактор.
5. Low-frequency/high-impact atom не понижен только из-за `likelihood`: `impact = 5` должен оставаться high.
6. Если writer понизил priority для access, money, security, server-side rejection, critical calculation или irreversible transition, reviewer создает `test-design` finding с соответствующей `coverage_dimension`.
7. `residual_risk_decision` не скрывает `GAP-*` и не превращает gap в covered requirement.
8. Priority не должен использоваться как порядок исполнения, сложность automation или субъективная важность раздела.

## Ревью Coverage Metrics

Если `Test-design applicability matrix` содержит applicable dimensions, reviewer обязан проверить `coverage-metrics.md`.

Reviewer проверяет:

1. Каждая строка с `applicable = yes` имеет строку metrics или linked artifact.
2. Metrics считают найденные obligations/classes/branches/transitions, covered by TC и `GAP-*` / `unclear` отдельно.
3. `numeric-format`, `exact-length`, dependency, repeatable-block, checkbox-list, print-form-output и generated document rules имеют разложение на обязательные классы.
4. Combinatorial coverage указывает `coverage_strength = 2-way | 3-way | t-way` и доказывает coverage выбранной силы.
5. Metrics не засчитывают generic TC или scenario TC как покрытие атомарных obligations без plan-row correspondence.

## Checklist review test-design

Перед проверкой отдельных `TC-*` проверь обязательный package workflow:

1. `scope-contract.md` содержит минимум один internal work package; отсутствие packages для подтвержденного scope является finding категории `scope`.
2. Каждый package из scope-contract представлен в ledger, coverage map или отдельной секции `Internal Work Package Coverage`.
3. Если source является таблицей полей/действий или PDF/DOCX extraction, перед ledger есть `Source Table Normalization`; reviewer сначала проверяет `Source Row Completeness Matrix` для multi-`GSR` rows, затем чистоту normalization rows, наличие `source_property_id`, `confidence`, `gap_id`, отсутствие multi-code compression, mixed property classes и table-header residue.
4. `Package Test Design Plan` присутствует и содержит строки для каждого package и применимого atom.
5. Для каждого package применен указанный `design_method`: например `dependency matrix`, `decision table`, `equivalence-boundary` или `integration artifact gate`.
5a. `Coverage Obligation Table` и `coverage-metrics.md` присутствуют, когда source содержит mandatory coverage classes; отсутствующие обязательные classes оформлены как `GAP-*`, а не пропущены.
5b. `fixture-catalog.md` присутствует или TC полностью раскрывают baseline, если negative checks требуют валидного состояния остальных полей.
6. `TC-*` не смешивают независимые проверки из разных packages, кроме явно выделенного scenario/use-case package.
7. Если package не может быть покрыт без новых источников или решений по scope, это оформлено как `GAP-*` / `unclear`, а не скрыто в общем `covered`.
8. Если набор обработан плоским списком atoms без packages, создай finding категории `test-design` или `scope`.
9. Если package ledger содержит generic atoms вроде `Требование GSR N выполняется`, `см. GSR/source row` или “поведение соответствует ФТ” без проверяемого expected behavior, создай finding категории `traceability` или `test-design`.
10. Если package ledger содержит широкие `ATOM-*` с диапазонами `GSR`/`REQ` и несколькими независимыми свойствами поведения, создай finding категории `atomarity`.
11. Если `Package Test Design Plan` содержит generic checks вроде `проверить требование`, `валидное/невалидное значение`, `установить условие`, slash-combinations в `check_type` или не раскладывает validation/action/dependency rules на positive/negative/boundary/branch checks, создай finding категории `test-design`.
12. Если один `TC-*` используется как `planned_tc_or_gap` для нескольких независимых executable строк плана, создай finding категории `atomarity`: writer экономит кейсы за счет объединения проверок.
13. Если writer явно сообщает о техническом лимите записи файла, reviewer обязан проверить, что применен chunked artifact writing. Если вместо этого файл стал компактнее за счет merged atoms/plan/TC, это blocking finding категории `atomarity` или `test-design`.

Для каждого проверяемого `TC-*` проверь:

1. У кейса есть одна основная проверка и один основной ожидаемый результат.
2. `TC-*` не является shortcut-ом для нескольких строк `Package Test Design Plan`, кроме отдельного scenario/recovery case, который не заменяет атомарные проверки.
3. Ожидаемый результат наблюдаем и достаточен для pass/fail.
4. Ожидаемый результат подтвержден ФТ, PDF, принятым уточнением или утвержденным материалом пакета.
5. Предусловия описывают состояние до выполнения, а не действие, которое проверяет тест.
6. Шаги детерминированы и исполнимы ручным тестировщиком.
7. Негативные сценарии сформулированы как попытки и проверяют отказ, no-change или отсутствие доступного действия.
8. Кейс не объединяет positive и negative ветки.
9. `Тестовые данные` не повторяют шаги и не содержат значения, которые полностью создаются шагами и не влияют на pass/fail. Если нарушение есть, фиксируй `format` / `structure` finding по `test-case-format.md`.
10. Ссылки трассировки указывают на точный requirement atom или фрагмент источника, который проверяется.
11. Boundary, equivalence, dependency и conditional-visibility проверки присутствуют, когда ФТ дает достаточно информации, чтобы их требовать.
12. Недостающее поведение зафиксировано как `coverage gap` / `unclear`, а не заполнено предположением.
13. Если применим `pairwise` / combinatorial coverage, есть factors/values, constraints, selected combinations, `coverage_strength`, proof of selected strength, high-risk additions и `TC-*` / `GAP-*` на выбранные комбинации.
14. `Приоритет` соответствует риску атома: деньги, доступы, потеря данных, необратимые статусы, расчеты, security и server-side rejection не должны быть ниже `High` без трассируемого `impact x likelihood` обоснования.
15. Расчетные кейсы содержат oracle: source/formula, входные значения, вручную вычисленный expected result, rounding/precision/currency/unit, если они влияют на pass/fail.
16. Для ограничений ввода кейс не смешивает недопустимый класс и допустимый контрольный ввод; если допустимый ввод используется после ошибки, кейс явно оформлен как восстановительный сценарий.
17. Если в scope есть внутренние рабочие пакеты, кейс не закрывает независимые проверки из разных packages одним expected result.
18. Кейс соответствует одной строке `Package Test Design Plan`; если строка plan обещает отдельный positive/negative/boundary class, TC реально проверяет только этот class. Scenario/recovery TC может ссылаться на несколько atoms, но не заменяет атомарные TC.
19. Набор сгруппирован по функциональности/блоку/элементу/операции, а `TC-*` ids идут сквозной последовательностью в пределах canonical file.
20. Validation/equivalence/boundary TC не используют placeholder data вроде `значение, нарушающее правило`, `значение из проверяемого класса`, `дата, соответствующая ветке ФТ`. Если конкретный ввод не может быть выбран из ФТ/разрешенного источника, reviewer требует `GAP-*` или параметризованный oracle.
20a. UI TC по экрану с mockup не используют generic steps вместо visible action / control / block hints из `mockup-visual-inventory.md`. Если mockup не открыт или inventory отсутствует, reviewer не подписывает набор.
20b. TC не использует unresolved generic valid baseline/test data и не строит expected result на `значении из тестовых данных`, если concrete input не задан. Если конкретика недоступна из источников, это `GAP-*` / `unclear`, а не executable TC.
20c. TC не использует placeholder traceability, source-rule oracle, generic editability steps, closed-list oracle without absence-of-extra-values, or derived-obligation contamination. These smells are blocking for semantic sign-off unless the affected TC is explicitly out-of-scope or non-baseline exploratory evidence.
21. Если atom/TC содержит правило вида `A и B`, reviewer проверяет, могут ли `A` и `B` pass/fail независимо. Если да, объединение является `atomarity` error.
22. Action/async TC с expected result `действие инициируется` допустим только при named observable artifact. Без artifact это `expected-result` / `async` error или `GAP-*`.

## Требования к finding

Для каждого `test-design` finding:

- `review_mode` должен быть `test-design`.
- `category` должен быть одним из: `test-design`, `expected-result`, `coverage`, `atomarity`, `duplication`, `scope`.
- `coverage_dimension` должен указывать конкретную test-design dimension из `review-findings-format.md`; `other` допустим только с объяснением в `problem`.
- `test_case_id` должен указывать затронутый `TC-*`, кроме случаев set-level coverage gap.
- `evidence` должен цитировать или кратко пересказывать слабое место тест-кейса и релевантное ожидание из ФТ/источника.
- `required_change` должен точно говорить, что writer должен добавить, разделить, удалить или пометить как `unclear`.
- Если дефект блокирует sign-off, severity должен быть `error`.

## Примеры

### Blocking expected result

Используй `error`, если кейс говорит:

> Система корректно обрабатывает заявку.

Это не наблюдаемо для pass/fail. Required change должен требовать заменить такую формулировку на конкретное наблюдаемое состояние, результат валидации, созданную запись, доступное действие или сохраненное значение, подтвержденное источником.

### Unsupported specificity

Используй `error`, если кейс ожидает точный текст ошибки, disabled-состояние контрола, status code, порядок сортировки или правило форматирования, которого нет в разрешенных источниках.

Required change должен требовать удалить неподтвержденную деталь или пометить поведение как `unclear`.

### Missing negative branch

Используй `warning`, если ФТ задает класс допустимых и недопустимых значений, но набор проверяет только допустимый класс и при этом уже имеет базовый positive case.

Используй `error`, если недопустимое значение является центральным требованием проверяемого правила.

### Over-splitting

Используй `warning`, если несколько тест-кейсов отличаются только отдельными значениями одного списка, а все значения проверяются одним действием и одним ожидаемым результатом.

Required change должен требовать объединить их в один list-composition case, если отдельные значения не запускают разную бизнес-логику.
