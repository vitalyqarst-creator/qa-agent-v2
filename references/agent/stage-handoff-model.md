# Stage Handoff Model

В проекте используется `Design A / Hybrid Handoff` как каноническая модель межэтапной передачи контекста для FT pipeline.

## Цель

- отделить стабильные handoff-артефакты от session-based review-cycle артефактов;
- сохранить один явный источник process-status;
- сделать переход между этапами воспроизводимым без истории чата.

## Базовая структура

```text
fts/<ft-slug>/
  test-cases/
    <section-id>-<scope-slug>.md
  work/
    stage-handoffs/
      <ordered-scope-dir>/
        workflow-state.yaml
        agent-decision-log.md
        source-selection.md
        scope-options.md
        scope-selection-prompts.md
        scope-contract.md
        source-parity-check.md
        source-row-inventory.md
        source-row-extraction-spec.json
        source-row-baseline.json
        source-assertions.json
        scope-coverage-gaps.md
        scope-clarification-requests.md
        scope-execution-options.md
        prompt.scope-assertions-to-reviewer.md
        prompt.scope-gaps-to-reviewer.md
        prompt.scope-to-writer.md
        prompt.scope-to-iteration.md
        source-assertion-review.json
        prompt.writer-to-reviewer.round-1.md
        prompt.reviewer-to-writer.round-1.md
        prompt.writer-to-reviewer.round-2.md
        prompt.reviewer-to-ui-prep.md
    review-cycles/
      <scope-slug>/
        cycle-state.yaml
        codex-session-map.yaml
        prompts/
        outputs/
        versions/
```

## Именование Handoff-Папок

Для новых handoff-папок в `fts/<ft-slug>/work/stage-handoffs/` используй числовой префикс, чтобы каталог было удобно читать в порядке выполнения:

```text
NN-<scope-slug>/
```

Примеры:

```text
00-general-requirements-to-before-ui/
01-status-model-universal-application/
02-status-model-product-application/
03-application-interruption-cancellation-expiry/
04-bp-initiation-client-offers/
```

Правила:

- `NN` — двухзначный порядковый номер в рекомендуемом порядке работы: `00`, `01`, `02`, ...
- Для контейнеров с картой scope-ов и prompt templates использовать `00-<container-slug>`, если это предварительный `agent-proposed-scope` handoff, а не подтвержденный рабочий scope.
- Для большого ФТ или запроса на весь документ `00-<container-slug>` должен хранить карту внешних candidate scope-ов по разделам/подразделам ФТ; не используй подтвержденную папку вида `NN-all-sections...` как стандартный старт вместо scope selection.
- `scope_slug` остается логическим идентификатором без числового префикса, например `bp-initiation-client-offers`.
- Канонический файл тест-кейсов остается без `NN-`, но должен начинаться с номера раздела ФТ: `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`.
- Session-based review-cycle папка остается `fts/<ft-slug>/work/review-cycles/<scope-slug>/`, без `NN-`.
- В `workflow-state.yaml` и prompt-файлах все пути к stage handoff должны указывать на фактическую numbered-папку.
- Не переименовывай существующие handoff-папки задним числом без отдельного явного запроса: переименование ломает сохраненные ссылки в уже созданных prompt-файлах и workflow-state.

## Обязательные handoff-артефакты по этапам

### `ft-source-locator`

- `source-selection.md`
- структура `source-selection.md` определяется `references/agent/source-selection-format.md`
- `agent-decision-log.md`
- обновленный `workflow-state.yaml`

### `ft-scope-analyzer`

- в режиме `agent-proposed-scope`: `scope-options.md`
- в режиме `agent-proposed-scope`: `scope-selection-prompts.md`
- после подтверждения одного scope: `scope-contract.md`
- после подтверждения одного scope и при наличии DOCX+PDF основного ФТ: `source-parity-check.md`
- после подтверждения одного scope и при наличии row-level/table parity: `source-row-inventory.md`
- для нового production/promotion-capable workflow: `source-row-extraction-spec.json`, `source-row-baseline.json`, `source-assertions.json`
- для нового production/promotion-capable workflow: `prompt.scope-assertions-to-reviewer.md`
- после подтверждения одного scope: `scope-coverage-gaps.md`
- после подтверждения одного scope: `scope-clarification-requests.md`, если в `scope-coverage-gaps.md` есть хотя бы один gap
- опционально после подтверждения одного scope: `scope-execution-options.md`
- `prompt.scope-gaps-to-reviewer.md`, если в `scope-coverage-gaps.md` есть хотя бы один `GAP-*`
- `prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md` только после accepted source assertion review либо для явно legacy/non-promotion route
- `agent-decision-log.md`
- обновленный `workflow-state.yaml`

### `ft-test-case-writer`

- канонический `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`
- структура writer output определяется `references/agent/writer-output-format.md`
- `prompt.writer-to-reviewer.round-N.md`
- в revision mode: `round-N-writer-response.md`
- `agent-decision-log.md`
- обновленный `workflow-state.yaml`

### `ft-test-case-reviewer`

- структура reviewer output определяется `references/agent/reviewer-output-format.md`
- `round-N-findings.md`
- при `traceability` и `full`: `round-N-traceability-matrix.md` и соседний `round-N-traceability-matrix.xlsx`
- если нужен revision: `prompt.reviewer-to-writer.round-N.md`
- если набор signed-off: `prompt.reviewer-to-ui-prep.md`
- `agent-decision-log.md` или round-specific `agent-decision-log.round-N.md`
- обновленный `workflow-state.yaml`

### `ft-test-case-iteration`

- валидирует обязательные handoff-артефакты;
- lifecycle, session transitions, snapshots и terminal statuses определяются `references/agent/session-based-review-cycle-format.md`;
- обновляет `agent-decision-log.md` для routing/sign-off/round-cap decisions;
- обновляет `workflow-state.yaml`;
- не создает собственный параллельный набор доменных артефактов поверх `cycle-state.yaml`, `outputs/` и `versions/`.

### `ft-ui-automation-prep`

- стартует только при `stage_status = ready-for-next-stage` и `next_skill = ft-ui-automation-prep`;
- использует `prompt.reviewer-to-ui-prep.md` как человекочитаемый handoff.

## Правила использования

- `stage-handoffs/` хранит межэтапный handoff; новые handoff-папки должны использовать формат `NN-<scope-slug>/`.
- Не создавай workflow handoff artifacts в корне FT-пакета `fts/<ft-slug>/`: `source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml`, `source-locator-session-log.md` и `scope-analyzer-session-log.md` должны лежать в фактической numbered-папке внутри `work/stage-handoffs/`.
- `review-cycles/` хранит session-based writer/reviewer cycle state, prompts, outputs and snapshots. `review-loops/` является legacy-only historical storage и не используется для новых прогонов.
- Канонический набор тест-кейсов остается в `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`.
- `agent-decision-log.md` хранит промежуточные решения стадии по `agent-decision-log-format.md` и должен быть связан из `workflow-state.yaml` через `latest_artifacts.decision_log`.
- `scope-options.md` используется только до выбора одного подтвержденного scope и не заменяет `scope-contract.md`.
- `scope-selection-prompts.md` используется только для подтверждения одного candidate scope и не является handoff к writer.
- `scope-contract.md` создается только для подтвержденного scope и должен соответствовать `scope-contract-format.md`.
- `source-parity-check.md` создается только для подтвержденного scope, если для основного ФТ доступны DOCX и PDF; он должен соответствовать `source-parity-check-format.md` и не заменяет `scope-contract.md` или traceability matrix.
- `source-row-inventory.md` создается только для подтвержденного scope, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий; он должен соответствовать `source-row-inventory-format.md` и не заменяет writer-side `work/test-design/<scope-slug>/source-row-inventory.md`.
- `scope-coverage-gaps.md` создается как отдельный companion-артефакт к `scope-contract.md` и должен соответствовать `scope-coverage-gaps-format.md`.
- `scope-clarification-requests.md` создается как conditional companion к `scope-coverage-gaps.md`, если в gaps есть хотя бы один `GAP-*`; он должен соответствовать `scope-clarification-requests-format.md`.
- `scope-clarification-requests.md` не заменяет `scope-coverage-gaps.md` и не является источником process-status.
- `scope-execution-options.md` — optional helper artifact для пользователя; он не заменяет `workflow-state.yaml` и не является обязательным входом downstream этапов.
- `prompt.scope-gaps-to-reviewer.md` является legacy entrypoint после scope analysis, если найдены `GAP-*` и требуется отдельная reviewer-сессия до writer. Для compiler contract v3 gap challenge входит в source assertion review.
- `prompt.scope-assertions-to-reviewer.md` является активным pre-writer entrypoint для нового production/promotion-capable workflow.
- `prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md` являются user-facing entrypoints только после accepted source assertion review либо для явно legacy/non-promotion route: первый запускает один writer-pass, второй запускает полный writer-reviewer loop.
- Каждый новый `*-traceability-matrix.md` в `review-cycles/<scope-slug>/outputs/` должен иметь соседний XLSX companion-файл с тем же basename.
- Для новых или обновленных traceability matrices каждая строка должна иметь `atom_id`; findings и writer response связываются с matrix через `traceability_ref`, а не через text-only `req_id` / `source_path`.
- После завершения session-based cycle `cycle-state.yaml` должен иметь terminal status `signed-off`, `round-cap-reached` или `blocked-input`, а `latest_artifacts` должен ссылаться на final outputs and terminal snapshot.
- После завершения session-based cycle используй final aliases в `latest_artifacts`: `final_findings`, `final_traceability_matrix`, `final_traceability_matrix_xlsx`, `final_writer_response`, `signed_off_snapshot` или `round_cap_snapshot`.
- Для новых или обновленных traceability matrices findings и writer response связываются с matrix через `traceability_ref`; это основной key для closure, а не `req_id`.
- Не создавай несколько конкурирующих `workflow-state.yaml` для одного `scope-slug`.
- Не используй prompt-файлы как замену findings, traceability matrix, writer response, final output summary или `cycle-state.yaml`.
