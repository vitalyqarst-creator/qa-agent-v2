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
3. `scope-obligations.json` — нормализованные `OBL-*` с точной source-привязкой, формулировкой ФТ и рисками. Это не test design.
4. `scope-clarification-requests.md` — только если один или несколько gaps требуют продуктового ответа БА; companion к `scope-obligations.json`, а не второй workflow state.
5. `test-design-matrix.md` — человекочитаемый дизайн будущих проверок на русском.
6. `validator-report.json` — output единственного scoped validator run для замороженного набора входов.
7. `<mode>-review-manifest.json` — неизменяемый snapshot входов отдельного review.
8. `<mode>-review-result.json` — независимый verdict и findings reviewer.
9. `fts/<domain>/<ft>/test-cases/<section>-<scope>.md` — canonical test cases.

Не создавай для v0.9 `writer-self-check.md`, `tc-self-check.md`, Writer Quality Gate, отдельный stage summary, launch/dispatch receipts, parking prompts или вспомогательные coverage tables. Если нужно пояснить недетерминированное решение, добавь короткую запись `decision_notes` в `workflow-state.json` рядом с решением.

## Обязательные свойства качества

- DOCX — источник смысла; XHTML — обязательное машиночитаемое представление. PDF, если он доступен в FT-пакете, связывается в manifest и используется для structural/visual cross-check; отсутствие PDF само по себе не блокирует downstream stage.
- Если существует `AGENT-NOTES.md`, он включается в source manifest и является обязательным контекстом. Его отсутствие само по себе не блокирует работу.
- Один `OBL-*` описывает одно самостоятельное утверждение ФТ. Один matrix row и один TC покрывают ровно один `OBL-*` и один основной ожидаемый результат.
- При нормализации `OBL-*` и независимом восстановлении требований не теряй ограничители исходной фразы: контекст выполнения (например, создание и редактирование), кванторы (`все`, `каждый`, `только`), граничные значения, условия и исключения. Если один ограничитель задаёт самостоятельный поток или результат, разложи его на отдельные OBL/matrix/TC.
- Конечный перечень элементов не становится автоматически одним TC: если выбор разных элементов запускает разные переходы или результаты, разложи их на отдельные `OBL-*`, строки matrix и TC. Единый TC допустим только для однотипной проверки состава или значений, выполняемой одним действием и не запускающей отдельную бизнес-логику.
- Не выдумывай статусы, роли, данные, экраны, поля, UI-реакции или интеграционные ответы. Неизвестное оформляй статусом `needs-test-data`, `candidate-ui-calibration`, `blocked-observability` или `needs-future-clarification`.
- `needs-test-data` используй, когда утверждение ФТ наблюдаемо, но отсутствует подготовленный актор, объект, исходный статус или значение. `blocked-observability` используй, когда в доступных источниках не названа точка наблюдения, действие или признак, по которому утверждение можно честно проверить. Не подменяй второй случай подготовкой произвольных данных.
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

`ft-scope-analyzer` читает DOCX/XHTML/PDF, support и доступный Figma только как visual reference. Он создаёт `scope-obligations.json`, не матрицу и не тест-кейсы. Каждое обязательство содержит `id`, `source_anchor`, русскоязычный `statement` и при необходимости `risk_flags`.

На этом же этапе агент фиксирует gaps в `clarifications`. Если gap требует продуктового ответа, он обязан сразу создать `scope-clarification-requests.md` с карточкой `CLR-* — GAP-*`; вопрос нельзя оставлять только в JSON. Терминологическое расхождение между заголовком раздела и ближайшими таблицами/утверждениями — отдельный `source-terminology-discrepancy`. Рабочий объект выбирается по содержательным требованиям, а не по заголовку. Если содержательные требования однозначны, расхождение остаётся редакционным non-blocking gap без вопроса БА; `CLR-*` нужен только при конкурирующих правилах, меняющих состав TC.

До `workflow-state.json` агент может запустить только `validate_practical_obligations.py`. Это проверка структуры source manifest, OBL и GAP; она не заменяет scoped validator и не подтверждает готовность маршрута целиком. В итоговом сообщении этапа агент обязан назвать вид выполненной проверки точно.

### 2. Матрица и условный matrix review

Writer создаёт русскоязычный `test-design-matrix.md` с таблицей:

| Проверка | Обязательство ФТ | Сценарий | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |
| --- | --- | --- | --- | --- | --- | --- |

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

Reviewer запускается в новой верхнеуровневой Codex-сессии (`codex-thread`), read-only для matrix/TC. Если механизм создания отдельной Codex-сессии доступен, controller использует его напрямую: не ищет внешнюю документацию и не заменяет отдельную сессию subagent-ом. До чтения matrix и TC reviewer самостоятельно формирует в `<mode>-review-result.json` массив `independent_obligations`: для каждого восстановленного утверждения указывает `source_anchor`, русскоязычный `statement` и связанные `obligation_ids`. Формулировка обязана сохранять все применимые ограничители первичного источника: контекст создания/редактирования, кванторы, границы, условия и исключения. Не передавай writer self-check: такого артефакта в v0.9 нет.

Результат review содержит `review_manifest_sha256`, `reviewer_thread_id`, `execution_surface: codex-thread`, `review_mode`, `independent_obligations`, `verdict` и findings. Перед созданием manifest controller обязан иметь свежий чистый `validator-report.json`, чьи content hashes совпадают с текущими входами scope. Controller проверяет неизменность snapshot и обновляет только `workflow-state.json` командой `finalize_practical_review.py`.

### 4. TC, final review и revision

После matrix acceptance либо пропуска matrix review writer создаёт canonical TC и повторно запускает scoped validator один раз для нового замороженного набора входов. Затем всегда запускается отдельный final TC review.

При `changes-required` разрешена ровно одна целевая writer revision и один свежий final independent TC review. `revision_count` в `workflow-state.json` расходуется только для blocking content finding; второй такой вердикт переводит scope в `blocked`, а не запускает repair-loop. Process/transport/validator finding с `remediation_owner: controller` или `validator` исправляется без расходования writer revision. Наблюдаемое требование с неизвестным UI-признаком получает `blocked-observability`; это допустимый статус matrix/TC и не является external blocker само по себе. Противоречие источников или непредставимое требование — честный `blocked-input`.

## Scoped validator и блокеры

`validate_practical_scope.py` читает только artifacts, явно связанные из `workflow-state.json`; он не сканирует исторические attempts/sibling scopes и не читает создаваемый report. Finding имеет независимые поля:

- `severity`: важность сообщения;
- `blocking`: разрешено ли продолжение;
- `blocking_reason`: причина остановки, если `blocking: true`;
- `remediation_owner`: `scope-analyzer`, `writer`, `reviewer`, `controller` или `validator`.

`source-integrity`, `unresolved-requirement`, `semantic-completeness`, `traceability`, `execution-readiness`, `review-integrity` и `artifact-tampering` блокируют. `format`, `style`, `transport` и `advisory-risk` не блокируют сами по себе; они остаются видимыми и могут быть подняты до blocker только явным правилом с `blocking_reason`.

## Compatibility

Workflow хранит `route_version`, а validator/report manifests — `tool_version`, contract digest и SHA-256 содержательных входов. Git commit фиксируется в review manifest только для аудита: нерелевантное изменение agent-layer кода не инвалидирует scope, если route/tool contract и content input hashes не изменились. Изменение поведения route требует явного повышения `tool_version` или соответствующей версии контракта.
