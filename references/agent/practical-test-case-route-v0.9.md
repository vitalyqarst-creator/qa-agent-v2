# Practical route v0.9 — компактный production-маршрут

## Назначение

Это default macro-stage маршрут для обычной задачи «написать тест-кейсы по подтвержденному scope ФТ». Его цель — выпускать качественные ручные и пригодные для автоматизации тест-кейсы до accepted baseline или честного external blocker, без повторения одного и того же coverage state в self-check, summary, receipt и нескольких таблицах.

`practical-v0.8` сохранён только для незавершённых legacy-запусков. Новый scope не начинает v0.8 без явного запроса пользователя.

## Канонические артефакты scope

Пакетный `source-package-manifest.json` размещается в
`fts/<domain>/<ft>/work/practical-v0.9/`. Остальные артефакты scope размещаются в
`fts/<domain>/<ft>/work/practical-v0.9/<scope-slug>/`, кроме production тест-кейсов.

1. `workflow-state.json` — единственный mutable источник статуса и следующего действия.
2. `../source-package-manifest.json` — DOCX, XHTML, доступный PDF, package notes, package-level утверждённые решения БА и их SHA-256;
   единый неизменяемый manifest для всех scope данного ФТ-пакета.
3. `scope-obligations.json` — нормализованные `OBL-*` с точной source-привязкой, формулировкой ФТ, контекстами исполнения и рисками. Это не test design.
4. `scope-clarification-requests.md` — только если один или несколько gaps требуют продуктового ответа БА; companion к `scope-obligations.json`, а не второй workflow state.
5. `test-design-matrix.md` — человекочитаемый дизайн будущих проверок на русском.
6. `validator-report.json` — output единственного scoped validator run для замороженного набора входов.
7. `<mode>-review-manifest.json` — неизменяемый snapshot состава входов отдельного review.
8. `<mode>-review-input-snapshot/` — создаётся только если отдельная сессия не получает тот же checkout; read-only копия hash-bound входов reviewer-а.
9. `<mode>-review-result.json` — дословно сохранённый независимый verdict и findings reviewer.
9. `fts/<domain>/<ft>/test-cases/<section>-<scope>.md` — canonical test cases.

Не создавай для v0.9 `writer-self-check.md`, `tc-self-check.md`, Writer Quality Gate, отдельный stage summary, launch/dispatch receipts, parking prompts или вспомогательные coverage tables. Если нужно пояснить недетерминированное решение, добавь короткую запись `decision_notes` в `workflow-state.json` рядом с решением.

## Обязательные свойства качества

- DOCX — источник смысла; XHTML — обязательное машиночитаемое представление. PDF, если он доступен в FT-пакете, связывается в manifest и используется для structural/visual cross-check; отсутствие PDF само по себе не блокирует downstream stage.
- Если существует `AGENT-NOTES.md`, он включается в source manifest и является обязательным контекстом. Его отсутствие само по себе не блокирует работу.
- Один `OBL-*` описывает одно самостоятельное утверждение ФТ. Каждый атомарный
  `SCN-*` matrix покрывает ровно один `OBL-*`, один `CTX-*` и один основной
  ожидаемый результат; ему соответствует ровно один TC. Один `OBL/CTX` может
  иметь несколько `SCN-*` только если ФТ требует независимые классы, границы
  или исходные состояния с разными primary oracle. Не создавай несколько TC
  только ради повторения одной и той же проверки.
- При нормализации `OBL-*` и независимом восстановлении требований не теряй ограничители исходной фразы: контекст выполнения (например, создание и редактирование), кванторы (`все`, `каждый`, `только`), граничные значения, условия и исключения. Если один ограничитель задаёт самостоятельный поток или результат, разложи его на отдельные OBL/matrix/TC.
- Конечный перечень элементов не становится автоматически одним TC: если выбор разных элементов запускает разные переходы или результаты, разложи их на отдельные `OBL-*`, строки matrix и TC. Единый TC допустим только для однотипной проверки состава или значений, выполняемой одним действием и не запускающей отдельную бизнес-логику.
- Не выдумывай статусы, роли, данные, экраны, поля, UI-реакции или интеграционные ответы. Неизвестное оформляй статусом `needs-test-data`, `candidate-ui-calibration`, `blocked-observability` или `needs-future-clarification`.
- Перед тем как отнести название, идентичность или расположение UI-контрола к `candidate-ui-calibration`, проверь относящиеся к экрану рисунки внутри ФТ, PDF и зарегистрированные visual-only макеты. Если они снимают эту неопределённость, зафиксируй `visual_binding` в `OBL-*` и используй её в matrix/TC; визуальный материал уточняет шаг, но не создаёт бизнес-правило. Открытый `ui-calibration` обязан содержать `visual_evidence_check` с проверенными источниками и только остаточным runtime-вопросом.
- `needs-test-data` используй, когда утверждение ФТ наблюдаемо, но отсутствует подготовленный актор, объект, исходный статус или действительно недоступный набор данных. Не назначай этот статус потому, что writer ещё не выбрал literal: сначала используй значение из ФТ, утверждённого решения БА, закрытого справочника, сохранённого DaData-fixture или синтетического fixture по его политике. `blocked-observability` используй, когда в доступных источниках не названа точка наблюдения, действие или признак, по которому утверждение можно честно проверить. Не подменяй второй случай подготовкой произвольных данных.
- Проза в пользовательских полях, matrix и обязательствах — на русском. Английский допустим только для согласованных enum и идентификаторов.

## Этапы

### 1. Источники и обязательства

`ft-source-locator` создаёт `source-package-manifest.json` командой:

```text
python scripts/create_practical_source_manifest.py --ft-package-root <package> --docx <docx> --xhtml <xhtml> [--pdf <pdf>] [--support <stable-support>] [--visual <mockup-or-figma-index>] [--ba-decisions <approved-ba-decisions>] --output work/practical-v0.9/source-package-manifest.json
```

В `support_inputs` включай только стабильные нормативные или справочные материалы. Макеты,
изображения экранов и Figma-index передавай только через `--visual`: они попадают в
`visual_inputs` с ролью `visual-only` и не могут стать источником бизнес-правила.

Если в `support/` есть `*-approved-ba-decisions.md`, передавай его только через
`--ba-decisions`. Утверждённое решение БА, прямо отменяющее или изменяющее ФТ,
имеет операционный приоритет в своей явно указанной области действия во всём
текущем FT-пакете. Формат, границы распространения и materialization задаёт
`practical-v0.9-ba-decision-registry-format.md`.

Для первичного извлечения выбранного scope используй штатный read-only helper
`scripts/inspect_practical_scope_sources.py` с XHTML, DOCX, PDF, section ID и при
необходимости fallback title. Он не создаёт артефактов в `work/`. Не создавай и не
итеративно не исправляй source-specific парсер в `work/debug`, пока штатный helper не
зафиксировал конкретное ограничение. Если для structural cross-check достаточно текста
PDF, не рендери его; визуальный рендер используй только при существенном для scope
layout-вопросе.

Обычный scope-local утверждённый ответ БА сохрани в
`support/<scope>-approved-clarifications.md` и запиши путь с SHA-256 в
связанном `GAP-*` внутри `scope-obligations.json`. Если ответ прямо отменяет
или меняет ФТ, оформи его package-level реестром решений БА, а не локальным
исключением. При противоречии без утверждённого решения обязательно создай
`scope-clarification-requests.md`.

`ft-scope-analyzer` читает DOCX/XHTML/PDF, support и доступный Figma только как visual reference. Он создаёт `scope-obligations.json`, не матрицу и не тест-кейсы. Каждое активное обязательство содержит `id`, `source_anchor`, русскоязычный `statement`, один или несколько `execution_contexts` и при необходимости `risk_flags`. Контекст связывает требование с одним пользовательским потоком и с каталогом `execution_setups`: актор, fixture, интеграция, исходное состояние и другие действительно нужные предпосылки. У одного OBL с разными потоками создания/редактирования — отдельный `CTX-*` для каждого потока. Для видимого контрола, однозначно определённого в рисунке ФТ или visual-only макете, запиши `visual_binding`; не оставляй его название или положение в UI-калибровке.

До фиксации обязательств анализатор обязан проверить применимые
**общедокументные правила**. Если строка scope задаёт поле с типом данных,
форматом, общим справочником или иной ссылкой на правило вне ближайшей
таблицы, нужно найти определение этого правила в DOCX/XHTML и перенести все
проверяемые подправила в OBL/scenario: диапазоны, границы, допустимые классы,
календарную корректность, правила сохранения и иные явно заданные условия.
Например, строка поля типа «Дата» не покрывается одним валидным примером, если
общая таблица «Дата» определяет формат, границы и сохранение значения. Если
применимость общего правила неясна, это `GAP-*`, а не молчаливое исключение.

На этом же этапе агент фиксирует gaps в `clarifications`. Если gap требует продуктового ответа, он обязан сразу создать `scope-clarification-requests.md` с карточкой `CLR-* — GAP-*`; вопрос нельзя оставлять только в JSON. Терминологическое расхождение между заголовком раздела и ближайшими таблицами/утверждениями — отдельный `source-terminology-discrepancy`. Рабочий объект выбирается по содержательным требованиям, а не по заголовку. Если содержательные требования однозначны, расхождение остаётся редакционным non-blocking gap без вопроса БА; `CLR-*` нужен только при конкурирующих правилах, меняющих состав TC.

До `workflow-state.json` агент может запустить только `validate_practical_obligations.py`. Это проверка структуры source manifest, OBL и GAP; она не заменяет scoped validator и не подтверждает готовность маршрута целиком. В итоговом сообщении этапа агент обязан назвать вид выполненной проверки точно.

### 2. Матрица и условный matrix review

Writer создаёт русскоязычный `test-design-matrix.md` с таблицей:

| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

В каждой строке указывай уникальный `SCN-*`. Один `OBL/CTX` имеет хотя бы
один сценарий; несколько сценариев допустимы только для независимых классов,
границ или состояний. В `Исходном состоянии` опиши, что уже существует до
действий исполнителя. В `Формировании состояния` укажи отдельное действие,
которое создаёт trigger, либо честно запиши, что оно задано предусловием и
действие не требуется. В `Проверяемом действии` опиши действие, вызывающее
результат. В «Нужных предпосылках» перечисляй все связанные `SETUP-*`.
Статус исполнения обычно вычисляется из их доступности: если не подготовлен
актор, fixture, интеграция или исходное состояние, строка не может быть
`ready`. При нескольких недоступных предпосылках указывай один первичный
статус в порядке: `needs-future-clarification`, `blocked-observability`,
`needs-test-data`, `candidate-ui-calibration`. Поэтому отсутствующий актор,
fixture, интеграция или исходное состояние всегда даёт `needs-test-data`, а не
маскируется `candidate-ui-calibration`; все причины сохраняются в поле
«Нужные предпосылки». Исключение: если само утверждение ФТ описывает только
внутреннюю проверку и не задаёт наблюдаемый oracle, строка получает
`blocked-observability` независимо от отсутствующих fixture или актора. В
ожидаемом результате явно зафиксируй эту причину со ссылкой на источник.

До передачи матрицы на review writer сверяет каждое поле scope с обнаруженными
для него общедокументными правилами. Independent reviewer делает ту же
проверку самостоятельно: он не считает покрытой строку поля, пока не проверил
все применимые правила её типа вне локальной таблицы. Отдельные классы и
границы, имеющие разные primary oracle, должны быть отдельными `SCN-*`.

Один раз выполни scoped validator:

```text
python scripts/validate_practical_scope.py --ft-package-root <package> --workflow-state <scope-dir>/workflow-state.json --output-profile <scope-dir>/validator-report.json --exclude-output <scope-dir>/validator-report.json --require-clean
```

Matrix review обязателен только если в `scope-obligations.json` не менее 8 обязательств или есть `risk_flags`: `status-transition`, `cross-field-rule`, `closed-dictionary`, `integration`, `authorization`, `exception-over-general-rule`, `mapping-table`, `temporal-rule`, `high-fan-out`, `high-risk`. Для простого scope matrix review не запускается: после чистой валидации writer переходит к TC.

### 3. Separate-session review

Для обязательного matrix review и для любого final TC review controller создаёт один immutable manifest:

```text
python scripts/create_practical_review_manifest.py --repo-root <repo> --ft-package-root <package> --workflow-state <scope-dir>/workflow-state.json --review-mode <matrix|test-cases> --controller-thread-id <current-top-level-thread-id> --contract-file references/agent/practical-test-case-route-v0.9.md --output <scope-dir>/<mode>-review-manifest.json
```

Reviewer запускается в новой верхнеуровневой Codex-сессии (`codex-thread`), read-only для matrix/TC. Если механизм создания отдельной Codex-сессии доступен, controller использует его напрямую: не ищет внешнюю документацию и не заменяет отдельную сессию subagent-ом. До чтения matrix и TC reviewer самостоятельно восстанавливает требования. Для обычного scope он возвращает `independent_obligations`: указывает `source_anchor`, русскоязычный `statement` и связанные `obligation_ids`. Если manifest содержит `reviewer_receipt_contract`, reviewer возвращает один `independent_obligation_set`, связанный с digest полного набора `OBL-*`; это не освобождает его от самостоятельного чтения источников. Формулировка обязана сохранять все применимые ограничители первичного источника: контекст создания/редактирования, кванторы, границы, условия и исключения. Для каждого открытого `ui-calibration` reviewer сам проверяет связанные изображения ФТ и visual-only inputs: если они уже определяют контрол или его расположение, требует удалить gap и использовать `visual_binding`; если нет, проверяет узость остаточного runtime-вопроса. Не передавай writer self-check: такого артефакта в v0.9 нет.

До dispatch controller обязан проверить доступность каждого hash-bound входа в
целевом checkout:

```text
python scripts/practical_review_input_snapshot.py --manifest <scope-dir>/<mode>-review-manifest.json --verify-target <target-package-root>
```

Если target checkout не содержит текущие незакоммиченные артефакты, не запускай
review на неполном наборе. Сначала создай разрешённый snapshot, передай его
абсолютный путь reviewer-у и потребуй `--verify-snapshot` до чтения входов:

```text
python scripts/practical_review_input_snapshot.py --manifest <scope-dir>/<mode>-review-manifest.json --ft-package-root <package> --create-snapshot <scope-dir>/<mode>-review-input-snapshot
python scripts/practical_review_input_snapshot.py --manifest <scope-dir>/<mode>-review-manifest.json --verify-snapshot <scope-dir>/<mode>-review-input-snapshot
```

Reviewer возвращает один JSON-object без нормализации семантики, сразу в
лимите `reviewer_receipt_contract` при его наличии. Controller сохраняет
первый валидный raw response byte-for-byte, а не переписывает anchor или
формулировки и не делает follow-up для сжатия уже вынесенного verdict:

```text
python scripts/capture_practical_review_result.py --submission <raw-reviewer-json> --output <scope-dir>/<mode>-review-result.json
```

Результат review содержит `review_manifest_sha256`, `reviewer_thread_id`, `execution_surface: codex-thread`, `review_mode`, `independent_obligations` либо digest-bound `independent_obligation_set`, `verdict` и findings. Перед созданием manifest controller обязан иметь свежий чистый `validator-report.json`, чьи content hashes совпадают с текущими входами scope. Controller проверяет неизменность snapshot и обновляет только `workflow-state.json` командой `finalize_practical_review.py`, которая сохраняет SHA-256 raw receipt в history review.

### 4. TC, final review и revision

После matrix acceptance либо пропуска matrix review writer создаёт canonical TC и повторно запускает scoped validator один раз для нового замороженного набора входов. Затем переводит `workflow-state.json` в `phase: review`, устанавливает следующее действие «Провести независимое final TC review» и сохраняет `final_verdict: not-finalized`. Затем всегда запускается отдельный final TC review. `final_verdict` относится только к final TC review; matrix verdict хранится в `reviews`.

При `changes-required` для каждой фазы разрешена ровно одна целевая writer revision: одна целевая writer revision матрицы и один свежий matrix re-review, а также отдельно одна целевая writer revision canonical TC и один свежий final independent TC review. `matrix_revision_count` и `tc_revision_count` в `workflow-state.json` расходуются только для blocking content finding своей фазы; второй такой вердикт той же фазы переводит scope в `blocked`, а не запускает repair-loop. Process/transport/validator finding с `remediation_owner: controller` или `validator` исправляется без расходования writer revision. Наблюдаемое требование с неизвестным UI-признаком получает `blocked-observability`; это допустимый статус matrix/TC и не является external blocker само по себе. Противоречие источников или непредставимое требование — честный `blocked-input`.

В canonical TC тестовые данные — это либо конкретные значения/файлы, либо
точные свойства действительно недостающего набора и способ его подготовки.
Нельзя пересказывать проверяемое правило вместо данных или писать
«подготовлена строка запроса», «доступны указанные предпосылки», «параметры,
указанные в тестовых данных». Если literal можно получить из ФТ, support,
справочника, сохранённого DaData-fixture или синтетического fixture, укажи его
прямо в TC. Шаги «Сформировать исходное состояние», «Выполнить подготовку
состояния» и аналогичные мета-действия запрещены: вместо них указывай
конкретное действие пользователя с экраном, полем и значением, либо точный
внешний fixture в предусловиях. В трассировке указывай один
`OBL-*` и один `SCN-*`. Если `source_anchor` связанного обязательства содержит
формальный код требования (`AS.*`, `BSR`, `GSR` или `DIT`), перенеси каждый
такой код в трассировку TC; ссылка только на таблицу, без её кода, не заменяет
код. Если в source-привязке кода нет, не выдумывай его. Каждое действие,
которое создаёт состояние для проверки, указывается отдельным нумерованным
шагом: ввод поискового запроса —
до выбора подсказки; создание дубля — до сохранения; несохранённое изменение —
до отмены/закрытия; повторное открытие/поиск — после действия, для которого
проверяется отсутствие сохранения. Для ограничения «не более одного файла»
сначала прикрепляется первый допустимый файл, затем отдельным шагом выполняется
попытка прикрепить второй. Если ФТ задаёт дословное сообщение, это сообщение
переносится в итоговый ожидаемый результат без перефразирования. Внутреннее
действие без самостоятельного наблюдаемого результата получает
`blocked-observability`; не выдавай его за наблюдаемую проверку и явно
укажи в ожидаемом результате, что источник не задаёт наблюдаемый признак.

### Явная миграция активного matrix-контракта

Новая схема `practical-matrix-v2` несовместима с прежней matrix: в ней есть
обязательные `SCN-*` и поля состояния/действия. Если активный scope был
начат с `practical-matrix-v1`, controller не исправляет его частично и не
сбрасывает `matrix_revision_count` или `tc_revision_count`.

Сначала он выполняет только read-only план:

```text
python scripts/migrate_practical_matrix_contract.py --ft-package-root <package> --workflow-state <scope-dir>/workflow-state.json --action plan
```

После явного разрешения пользователя допустим только такой структурный
переход:

```text
python scripts/migrate_practical_matrix_contract.py --ft-package-root <package> --workflow-state <scope-dir>/workflow-state.json --action start --snapshot-dir <scope-dir>/contract-migration-v1-to-v2-snapshot --explicit-user-authorization
```

Команда сохраняет хешированный snapshot прежних workflow/matrix/TC,
переводит workflow в `matrix-migration` и фиксирует неизменённые бюджеты. Она
не изменяет содержательную matrix или TC. Затем writer переводит matrix в
новую схему, controller отмечает только структурную готовность:

```text
python scripts/migrate_practical_matrix_contract.py --ft-package-root <package> --workflow-state <scope-dir>/workflow-state.json --action mark-matrix-ready
```

После чистой валидации и нового независимого matrix review прежние TC ещё не
являются валидным входом. Writer синхронизирует их с SCN/matrix и existing
findings в рамках прежнего TC-бюджета; затем controller завершает только
contract migration:

```text
python scripts/migrate_practical_matrix_contract.py --ft-package-root <package> --workflow-state <scope-dir>/workflow-state.json --action complete-tc-sync
```

Лишь после новой scoped validation допустимо final TC review. Второй
content-verdict той же фазы остаётся blocker: migration не создаёт новый
repair-loop и не отменяет уже полученные reviewer findings.

## Scoped validator и блокеры

`validate_practical_scope.py` читает только artifacts, явно связанные из `workflow-state.json`; он не сканирует исторические attempts/sibling scopes и не читает создаваемый report. Finding имеет независимые поля:

- `severity`: важность сообщения;
- `blocking`: разрешено ли продолжение;
- `blocking_reason`: причина остановки, если `blocking: true`;
- `remediation_owner`: `scope-analyzer`, `writer`, `reviewer`, `controller` или `validator`.

`source-integrity`, `unresolved-requirement`, `semantic-completeness`, `traceability`, `execution-readiness`, `review-integrity` и `artifact-tampering` блокируют. `format`, `style`, `transport` и `advisory-risk` не блокируют сами по себе; они остаются видимыми и могут быть подняты до blocker только явным правилом с `blocking_reason`.

## Compatibility

Workflow хранит `route_version` и `contract_versions.matrix`, а validator/report manifests — `tool_version`, contract digest и SHA-256 содержательных входов. Git commit фиксируется в review manifest только для аудита: нерелевантное изменение agent-layer кода не инвалидирует scope, если route/tool contract и content input hashes не изменились. Изменение поведения route требует явного повышения `tool_version` или соответствующей версии контракта.
