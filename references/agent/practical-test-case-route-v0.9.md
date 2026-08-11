# Practical route v0.9 — компактный production-маршрут

## Назначение

Это default macro-stage маршрут для обычной задачи «написать тест-кейсы по подтвержденному scope ФТ». Его цель — выпускать качественные ручные и пригодные для автоматизации тест-кейсы до accepted baseline или честного external blocker, без повторения одного и того же coverage state в self-check, summary, receipt и нескольких таблицах.

`practical-v0.8` сохранён только для незавершённых legacy-запусков. Новый scope не начинает v0.8 без явного запроса пользователя.

## Канонические артефакты scope

Пакетный `source-package-manifest.json` размещается в
`fts/<domain>/<ft>/work/practical-v0.9/`. Остальные артефакты scope размещаются в
`fts/<domain>/<ft>/work/practical-v0.9/<scope-slug>/`, кроме production тест-кейсов.

1. `workflow-state.json` — единственный mutable источник статуса и следующего действия.
2. `../source-package-manifest.json` — DOCX, XHTML, доступный PDF, package notes и их SHA-256;
   единый неизменяемый manifest для всех scope данного ФТ-пакета.
3. `scope-obligations.json` — нормализованные `OBL-*` с точной source-привязкой, формулировкой ФТ и рисками. Это не test design.
4. `test-design-matrix.md` — человекочитаемый дизайн будущих проверок на русском.
5. `validator-report.json` — output единственного scoped validator run для замороженного набора входов.
6. `<mode>-review-manifest.json` — неизменяемый snapshot входов отдельного review.
7. `<mode>-review-result.json` — независимый verdict и findings reviewer.
8. `fts/<domain>/<ft>/test-cases/<section>-<scope>.md` — canonical test cases.

Не создавай для v0.9 `writer-self-check.md`, `tc-self-check.md`, Writer Quality Gate, отдельный stage summary, launch/dispatch receipts, parking prompts или вспомогательные coverage tables. Если нужно пояснить недетерминированное решение, добавь короткую запись `decision_notes` в `workflow-state.json` рядом с решением.

## Обязательные свойства качества

- DOCX — источник смысла; XHTML — обязательное машиночитаемое представление. PDF, если он доступен в FT-пакете, связывается в manifest и используется для structural/visual cross-check; отсутствие PDF само по себе не блокирует downstream stage.
- Если существует `AGENT-NOTES.md`, он включается в source manifest и является обязательным контекстом. Его отсутствие само по себе не блокирует работу.
- Один `OBL-*` описывает одно самостоятельное утверждение ФТ. Один matrix row и один TC покрывают ровно один `OBL-*` и один основной ожидаемый результат.
- Конечный перечень элементов не становится автоматически одним TC: если выбор разных элементов запускает разные переходы или результаты, разложи их на отдельные `OBL-*`, строки matrix и TC. Единый TC допустим только для однотипной проверки состава или значений, выполняемой одним действием и не запускающей отдельную бизнес-логику.
- Не выдумывай статусы, роли, данные, экраны, поля, UI-реакции или интеграционные ответы. Неизвестное оформляй статусом `needs-test-data`, `candidate-ui-calibration`, `blocked-observability` или `needs-future-clarification`.
- `needs-test-data` используй, когда утверждение ФТ наблюдаемо, но отсутствует подготовленный актор, объект, исходный статус или значение. `blocked-observability` используй, когда в доступных источниках не названа точка наблюдения, действие или признак, по которому утверждение можно честно проверить. Не подменяй второй случай подготовкой произвольных данных.
- Проза в пользовательских полях, matrix и обязательствах — на русском. Английский допустим только для согласованных enum и идентификаторов.

## Этапы

### 1. Источники и обязательства

`ft-source-locator` создаёт `source-package-manifest.json` командой:

```text
python scripts/create_practical_source_manifest.py --ft-package-root <package> --docx <docx> --xhtml <xhtml> [--pdf <pdf>] --output work/practical-v0.9/source-package-manifest.json
```

`ft-scope-analyzer` читает DOCX/XHTML/PDF, support и доступный Figma только как visual reference. Он создаёт `scope-obligations.json`, не матрицу и не тест-кейсы. Каждое обязательство содержит `id`, `source_anchor`, русскоязычный `statement` и при необходимости `risk_flags`.

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

Reviewer запускается в новой верхнеуровневой Codex-сессии (`codex-thread`), read-only для matrix/TC. До чтения matrix и TC он самостоятельно формирует в `<mode>-review-result.json` массив `independent_obligations`: для каждого восстановленного утверждения указывает `source_anchor`, русскоязычный `statement` и связанные `obligation_ids`. Не передавай writer self-check: такого артефакта в v0.9 нет.

Результат review содержит `review_manifest_sha256`, `reviewer_thread_id`, `execution_surface: codex-thread`, `review_mode`, `independent_obligations`, `verdict` и findings. Controller проверяет неизменность snapshot и обновляет только `workflow-state.json` командой `finalize_practical_review.py`.

### 4. TC, final review и revision

После matrix acceptance либо пропуска matrix review writer создаёт canonical TC и повторно запускает scoped validator один раз для нового замороженного набора входов. Затем всегда запускается отдельный final TC review.

При `changes-required` разрешена ровно одна целевая writer revision и один свежий final independent TC review. `revision_count` в `workflow-state.json` расходуется при первом `changes-required`; второй такой вердикт переводит scope в `blocked`, а не запускает repair-loop. Process/transport/validator finding с `remediation_owner: controller` или `validator` исправляется без расходования writer revision. Противоречие источников или непредставимое требование — честный `blocked-input`.

## Scoped validator и блокеры

`validate_practical_scope.py` читает только artifacts, явно связанные из `workflow-state.json`; он не сканирует исторические attempts/sibling scopes и не читает создаваемый report. Finding имеет независимые поля:

- `severity`: важность сообщения;
- `blocking`: разрешено ли продолжение;
- `blocking_reason`: причина остановки, если `blocking: true`;
- `remediation_owner`: `scope-analyzer`, `writer`, `reviewer`, `controller` или `validator`.

`source-integrity`, `unresolved-requirement`, `semantic-completeness`, `traceability`, `execution-readiness`, `review-integrity` и `artifact-tampering` блокируют. `format`, `style`, `transport` и `advisory-risk` не блокируют сами по себе; они остаются видимыми и могут быть подняты до blocker только явным правилом с `blocking_reason`.

## Compatibility

Workflow хранит `route_version`, а validator/report manifests — `tool_version`, contract digest и SHA-256 содержательных входов. Git commit фиксируется в review manifest только для аудита: нерелевантное изменение agent-layer кода не инвалидирует scope, если route/tool contract и content input hashes не изменились. Изменение поведения route требует явного повышения `tool_version` или соответствующей версии контракта.
