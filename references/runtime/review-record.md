# Controller-owned запуск и актуальность независимого review

Matrix и canonical TC проверяются в разных верхнеуровневых Codex-сессиях, зарегистрированных по `session-topology.md`. Reviewer не создаёт собственную сессию и не формирует dispatch evidence: запуском и регистрацией владеет controller.

## Двухфазный dispatch

1. Controller создаёт operational prompt в `work/reviews/<scope>/<matrix|tc>-review-prompt.md`.
2. Через встроенный Codex Desktop API controller вызывает `list_projects`, затем `create_thread` в local environment текущего проекта. Начальный bootstrap prompt запрещает читать artifacts и выполнять review до operational follow-up.
3. Полученный от `create_thread` `threadId` controller регистрирует командой `scripts/runtime_review_dispatch.py create`. Команда одновременно закрепляет reviewer за scope в `runtime-session-registry.json`. Для первого review `--previous-review` не передаётся и режим всегда `full`. После ограниченной revision controller передаёт прежний `changes-required` record через `--previous-review`; команда сама создаёт revision manifest и выбирает `delta` либо безопасный `full` fallback. Receipt имеет имя `<kind>-review-dispatch-<artifact-hash-prefix>-<reviewer-thread-prefix>.json`.
4. Только после успешной регистрации controller отправляет в созданную сессию operational prompt через `send_message_to_thread`, включая путь receipt.
5. Reviewer первым действием запускает `scripts/runtime_review_dispatch.py verify`. При успехе команда возвращает путь и SHA-256 `skills/ft-test-case-reviewer/SKILL.md`; reviewer полностью читает этот файл до review inputs. При ошибке или несовпадении skill contract он останавливается без verdict.
6. Controller ожидает завершения через `wait_threads`, сверяет фактические thread/host ID, проверяет неизменность SHA-256 receipt относительно значения, возвращённого командой `create`, и валидирует итоговый review-record.

Controller не меняет review inputs между созданием receipt и завершением reviewer. Reviewer изменяет только `<matrix|tc>-review.md` и `<matrix|tc>-review.json`. При вызове `create_thread` controller не переопределяет model/thinking, если пользователь явно этого не запросил.

Controller не использует subagent, fork, analyzer, другой reviewer или текущую writer-сессию как независимый reviewer. После revision controller возвращает re-review в уже зарегистрированную reviewer-сессию того же вида только при неизменном commit agent-layer. Если runtime commit изменился, новый receipt создаётся для новой верхнеуровневой reviewer-сессии, чтобы она заново загрузила текущие инструкции. Если thread API недоступен или пользователь ещё не разрешил создание отдельных сессий, route останавливается до получения возможности/разрешения. Разрешение запрашивается один раз на текущий practical route.

Bootstrap prompt:

```text
Ты создан как независимый reviewer. Не читай файлы проекта, не выполняй review и не изменяй artifacts до отдельного operational prompt controller-а с путём controller-owned dispatch receipt.
```

После получения реального `threadId` controller выполняет:

```text
python scripts/runtime_review_dispatch.py create --package-root <FT-package> --artifact <matrix-or-TC> --review-prompt <prompt.md> --review-dir <work/reviews/scope> --kind <matrix|tc> --reviewer-thread-id <threadId> --reviewer-host-id <hostId>
```

После revision к команде добавляется:

```text
--previous-review <work/reviews/scope/matrix-or-tc-review.json>
```

До перезаписи прежнего record dispatch встраивает его в controller-owned manifest. `delta` разрешён только когда source/support/mockup, scope handoff, ответы БА, materialization/fixtures и принятая matrix для TC не изменились; структура/порядок artifact прежние; изменены только элементы, перечисленные в `affected_items` findings. Writer-owned `matrix-data-plan.md` является companion-проекцией matrix: его изменение вместе с заявленными строками matrix сохраняет `delta`, но весь изменённый plan обязателен для чтения reviewer-ом и остаётся перечисленным в `changed_semantic_inputs`. Иные изменения semantic inputs автоматически требуют `full`. No-op revision отклоняется.

Reviewer проверяет receipt:

```text
python scripts/runtime_review_dispatch.py verify --package-root <FT-package> --artifact <matrix-or-TC> --review-prompt <prompt.md> --dispatch <dispatch.json> --kind <matrix|tc> --reviewer-thread-id <own-threadId>
```

## Итог review

Человекочитаемый итог хранится в `work/reviews/<scope>/<matrix|tc>-review.md`, а рядом создаётся машиночитаемая запись `<matrix|tc>-review.json`.

## Формат записи

```json
{
  "schema_version": 2,
  "review_kind": "matrix",
  "artifact_path": "work/practical/<scope>/test-design-matrix.md",
  "artifact_sha256": "<64 hex>",
  "dispatch_path": "work/reviews/<scope>/matrix-review-dispatch-<hash-prefix>-<thread-prefix>.json",
  "dispatch_sha256": "<64 hex>",
  "reviewer_session_type": "codex-thread",
  "reviewer_session_id": "<top-level thread id>",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "review_mode": "full",
  "artifact_index": {
    "items": {"M-001": "<64 hex>"},
    "order": ["M-001"],
    "structure_sha256": "<64 hex>"
  },
  "semantic_input_hashes": {"source/requirements.docx": "<64 hex>"},
  "reviewed_items": ["M-001"],
  "review_scope_complete": true,
  "matrix_review_checklist": {
    "source-coverage": {"status": "checked", "evidence": ["SR-001 -> M-001"]},
    "formal-techniques": {"status": "not-applicable", "evidence": ["Не применимо: формальные профили отсутствуют."]},
    "uniqueness-lifecycle": {"status": "not-applicable", "evidence": ["Не применимо: правило уникальности отсутствует."]},
    "save-data-closure": {"status": "checked", "evidence": ["M-001"]},
    "identity-provenance": {"status": "checked", "evidence": ["TD-PARTNER-A -> внешний сервис: Provider"]},
    "reachability-oracles": {"status": "checked", "evidence": ["M-001"]},
    "duplication-parameterization": {"status": "checked", "evidence": ["Дубли отсутствуют."]}
  },
  "verdict": "matrix-accepted",
  "findings": []
}
```

- `review_kind`: `matrix` или `tc`.
- Допустимые verdict: `matrix-accepted`, `matrix-changes-required`, `tc-accepted`, `tc-changes-required`.
- Accepted verdict требует пустой `findings`; changes-required требует непустой конечный список findings.
- Schema v2 обязательна для новых review. Schema v1 принимается только как историческое evidence и не может служить основанием для delta re-review.
- Перед validator reviewer запускает `runtime_review_delta.py enrich-review`: helper рассчитывает hashes элементов и semantic inputs из текущих файлов и переносит controller-owned режим/manifest из dispatch. Эти поля нельзя заполнять оценочно.
- `full` означает полный независимый semantic review всех элементов ограниченного artifact. Source slice для первого review включает целиком выбранный раздел scope и точные зарегистрированные anchors; нерелевантные разделы FT-пакета повторно не читаются. Выход за границы фиксируется в Markdown review и допускается только по явной внешней ссылке либо для проверки противоречия. `delta` означает полный запуск дешёвых validator-ов и semantic re-review только `changed_items`, прежних findings и их source/dependency slices; для matrix delta reviewer дополнительно полностью читает изменённый `matrix-data-plan.md`, не перечитывая из-за этого весь source slice. Reviewer вправе повысить `delta` до `full` только при обнаруженной зависимости за пределами manifest, но не понизить controller-owned `full`.
- Schema v2 `full` matrix review содержит `matrix_review_checklist` с категориями `source-coverage`, `formal-techniques`, `uniqueness-lifecycle`, `save-data-closure`, `identity-provenance`, `reachability-oracles`, `duplication-parameterization`. В `identity-provenance` перечисляются все целевые и prerequisite/родительские сущности и источник их tester-facing идентичности; сам стенд, будущая подготовка или стендовая привязка источником литерала не являются. Каждая clause с упоминанием стенда должна в той же clause назвать подтверждённую привязку либо другой источник идентичности. Статус каждой категории — `checked` либо `not-applicable`; evidence непустое, а неприменимость содержит `Не применимо: <причина>`.
- Любое изменение проверенного artifact меняет SHA-256 и делает review устаревшим. После правки нужен новый review-record из отдельной сессии.
- Обновление agent-layer само по себе не отменяет уже принятый review неизменного artifact. Проверка исторического review-record сверяет его собственные immutable receipt, thread ID и hashes, но не требует, чтобы та reviewer-сессия оставалась текущей ролью registry. Свежая сессия обязательна только при фактическом новом review.
- `dispatch_path` указывает на controller-owned receipt текущего artifact; thread ID и hashes в receipt и review-record должны совпадать.
- Writer не создаёт TC без успешной проверки принятой matrix. Набор TC не считается выпущенным без успешной проверки `tc-accepted` для текущих байтов файла.

Для `review_kind: tc` запись дополнительно обязана содержать:

```json
{
  "total_tc_count": 34,
  "reviewed_tc_count": 34,
  "review_scope_complete": true
}
```

Каждый finding при `tc-changes-required` дополнительно содержит `origin_stage`:

```json
{
  "id": "TC-R-001",
  "severity": "material",
  "affected_items": ["TC-001"],
  "origin_stage": "matrix",
  "description": "Принятая matrix не содержит обязательную ветку покрытия.",
  "required_correction": "Добавить ветку в matrix и заново спроецировать TC."
}
```

`affected_items` обязателен для каждого schema v2 finding обоих видов review. Для matrix перечисляй `M-*`, `GAP-*` и затронутые элементы модели `EP-*`/`BVA-*`/`DT-R*`/`ST-T*`/`CT-C*`; для TC — `TC-*`. Используй `GLOBAL` только для действительно глобального дефекта: он принудительно включает полный re-review.

При manifest-backed matrix re-review после writer revision каждый finding дополнительно содержит `discovery_status` и непустое `discovery_evidence`. Fresh full review, заменяющий record, который стал невалиден после изменения runtime-контракта, не сравнивает свою полноту с таким невалидным predecessor и возвращает обычный полный набор текущих findings:

- `carried-forward` — прежний finding не закрыт; обязателен `previous_finding_id`;
- `introduced-by-revision` — дефект действительно возник в одном из `changed_items` manifest;
- `semantic-input-change` — дефект стал применим из-за изменённого semantic input;
- `prior-review-omission` — дефект неизменённого материала должен был войти в предыдущее полное review, но был пропущен.

Manifest-backed re-review record с хотя бы одним `prior-review-omission` получает `review_quality_status: failed-prior-review-incomplete`; иначе — `complete`. Это не скрывает найденный дефект, но запрещает controller-у выдавать finding drift за нормальную следующую matrix revision. Для маршрутизации controller использует только машинное поле `review_quality_blocking` из `validate_runtime_review.py`; raw `review_quality_status` без `revision_manifest_path` route не блокирует.

- `matrix` — дефект присутствует в принятой matrix, но проверенный TC уже корректен относительно источника и после исправления matrix не требует изменения. Сначала исправляется matrix.
- `tc` — matrix достаточна, а дефект возник только при её проекции в canonical TC. Исправляются TC.
- `both` — содержательная ошибка есть и в matrix, и в TC либо отсутствие matrix-ветки уже привело к отсутствию/ошибке соответствующего покрытия в TC. Сначала исправляется matrix, затем TC.

Reviewer классифицирует происхождение, а не только место проявления. Если любой finding имеет `origin_stage: matrix|both`, validator возвращает `repair_stage: matrix`; только набор из `origin_stage: tc` возвращает `repair_stage: tc`. Controller использует это поле как исполнимую маршрутизацию и не трактует findings самостоятельно.

После принятия исправленной matrix controller передаёт writer-у путь исходного `tc-changes-required` review-record. Writer применяет все findings с `origin_stage: tc|both` и заново проецирует matrix-изменения. Если при наличии `tc|both` findings SHA-256 canonical TC остался равен проверенному review artifact, `validate_runtime_tc.py` отклоняет no-op repair.

Для полного TC review оба счётчика совпадают с фактическим числом заголовков `## TC-...`, а отчёт содержит `Проверено TC: 34/34`. Для delta re-review `total_tc_count` сохраняет общий размер, `reviewed_tc_count` равен числу `changed_items`, а отчёт содержит `Проверено изменённых TC: 2/34`. Во всех режимах `reviewed_items` и `review_scope_complete: true` обязательны.

Проверка:

```text
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind matrix --require-accepted
python scripts/validate_runtime_review.py <artifact.md> <review.json> --kind tc --require-accepted
```

Review-record подтверждает актуальность и форму независимого review, но не заменяет содержательную проверку источников.
