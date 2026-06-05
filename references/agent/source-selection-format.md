# Source Selection Format

Этот reference задает канонический формат `source-selection.md`: артефакта, который фиксирует выбранный FT-пакет, основной документ ФТ, PDF для structural cross-check и связанные материалы перед `ft-scope-analyzer`.

## Назначение

- сделать выбор источников воспроизводимым без истории чата;
- не смешивать выбор FT-пакета с определением scope;
- явно отделить main FT от support/mockups;
- зафиксировать source quality limitations до downstream writer/reviewer loop;
- предотвратить работу по неоднозначному или неподтвержденному источнику.

## Расположение

Для новых handoff-папок:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-or-container-slug>/source-selection.md
```

Если scope еще не выбран и создается предварительный контейнер для `agent-proposed-scope`, используй numbered directory вида:

```text
fts/<ft-slug>/work/stage-handoffs/00-<container-slug>/source-selection.md
```

`source-selection.md` не заменяет `workflow-state.yaml`: первый фиксирует содержательный выбор файлов, второй фиксирует process-status.

Не создавай `source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml` или session logs в корне FT-пакета `fts/<ft-slug>/`. Root-level workflow artifacts считаются contamination risk для clean runs. Используй только `work/stage-handoffs/NN-<scope-or-container-slug>/`.

## Validator Contract

- Для `current_stage: ft-source-locator` `workflow-state.yaml` обязан ссылаться на `source-selection.md` через `required_inputs` и/или `latest_artifacts.source_selection`.
- Source-locator handoff не должен содержать `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`. Эти файлы создаются только стадией `ft-scope-analyzer`.
- Если `source-selection.md` отсутствует или не связан из `workflow-state.yaml`, handoff считается неполным даже при наличии session log.
- Если source-locator создал scope-stage artifacts, это считается нарушением границы skill-а, а не допустимым ускорением workflow.
- Если FT-пакет содержит root-level handoff artifacts (`source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml`, session logs), validator должен вернуть `ft-package-root-level-handoff-artifacts`.

Additional validator content checks:

- `source-selection.md` must include all required sections: `Context`, `Main FT Documents`, `Structural Cross-Check PDF`, `Support Files And Mockups`, `Source Quality`, `Ambiguity And Decision Log`, `Handoff`.
- `Context` must include `selected_ft_slug` and `selection_status`; display labels such as `Selected FT slug` and `Selection status` are allowed because they normalize to the same field names.
- `selection_status` must be one of `selected`, `ambiguous`, `blocked-input`.
- If `selection_status` is not `selected`, workflow must remain blocked and must not route to `ft-scope-analyzer`, writer, iteration, or reviewer.

## Required Sections

### Context

Минимальные поля:

- `request_summary`;
- `selected_ft_slug`;
- `selection_status`;
- `created_at`;
- `created_by`.

Допустимые `selection_status`:

- `selected`;
- `ambiguous`;
- `blocked-input`.

Если статус не `selected`, downstream `ft-scope-analyzer` не должен стартовать без явного решения пользователя или обновленного `source-selection.md`.

### Main FT Documents

Перечисли все документы, которые считаются основным ФТ.

Для каждого документа фиксируй:

- `path`;
- `role`: `main-ft-docx | main-ft-pdf | main-ft-other`;
- `selection_reason`;
- `version_or_date`, если доступны;
- `source_quality_notes`, если есть parseability, section-id или oversized-block risks.

Основной `.docx` должен быть отделен от PDF-версии. PDF не должен становиться единственным source of truth, если доступен исходный main FT document.

### Structural Cross-Check PDF

Фиксируй:

- `pdf_available`: `yes | no`;
- `pdf_path`, если найден;
- `pdf_matches_main_ft`: `yes | no | not-checked`;
- `limitation`, если PDF отсутствует или не совпадает с main FT.

Если PDF отсутствует, это не всегда blocker, но limitation должен быть передан в `scope-coverage-gaps.md` или downstream notes, когда structural boundaries ненадежны.

### Support Files And Mockups

Раздели:

- support files;
- mockups;
- package notes;
- UI notes, если уже известны.

Для каждого файла укажи:

- `path`;
- `role`;
- `why_relevant`;
- `must_use_downstream`: `yes | no`;
- `limitations`.

Support/mockups не должны расширять FT scope без явного подтверждения.

### Source Quality

Фиксируй результаты первичной проверки источников:

- активные source documents для validator;
- parseability status;
- section-id confidence;
- oversized blocks или chunking limitations;
- strict source-quality warnings, если они уже известны.

Если есть strict warnings, не скрывай их. Либо документируй limitation, либо останавливай downstream работу через `blocked-input`, если section matching становится ненадежным.

### Ambiguity And Decision Log

Если выбор неоднозначен, перечисли candidate FT packages / files и причину:

- похожее имя;
- несколько версий;
- отсутствующий main FT;
- несоответствие PDF;
- непонятная роль файла.

Не выбирай источник по догадке. Для `selection_status: ambiguous` `workflow-state.yaml` должен использовать `stage_status: blocked-input` или другой явно неготовый статус.

### Handoff

Если `selection_status: selected`, подготовь handoff к `ft-scope-analyzer`:

```yaml
current_stage: ft-source-locator
stage_status: ready-for-next-stage
next_skill: ft-scope-analyzer
```

`latest_artifacts` в `workflow-state.yaml` должен ссылаться на:

- `source_selection`;
- active main FT document;
- structural cross-check PDF, если есть;
- package notes, если есть;
- artifact manifest, если aliases или local-only evidence значимы.

`source-selection.md` не должен создавать `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`: это ответственность `ft-scope-analyzer`.

Validator findings:

- `workflow-state-source-locator-missing-source-selection`: source-locator workflow не ссылается на `source-selection.md`.
- `workflow-state-source-locator-premature-scope-artifacts`: source-locator handoff содержит `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.

Additional validator findings:

- `source-selection-missing-required-sections`: `source-selection.md` misses one or more required handoff sections.
- `source-selection-missing-context-fields`: `Context` does not expose `selected_ft_slug` and/or `selection_status`.
- `source-selection-invalid-selection-status`: `selection_status` is outside `selected | ambiguous | blocked-input`.
- `workflow-state-source-selection-not-selected`: workflow routes downstream while `source-selection.md` is still `ambiguous` or `blocked-input`.

## Minimal Template

```md
# Source Selection

## Context

- Request summary:
- Selected FT slug:
- Selection status: `selected | ambiguous | blocked-input`
- Created at:
- Created by:

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |

## Structural Cross-Check PDF

- pdf_available: `yes | no`
- pdf_path:
- pdf_matches_main_ft: `yes | no | not-checked`
- limitation:

## Support Files And Mockups

| path | role | why_relevant | must_use_downstream | limitations |
| --- | --- | --- | --- | --- |

## Source Quality

- active source documents:
- parseability:
- section-id confidence:
- oversized blocks:
- strict warnings:

## Ambiguity And Decision Log

| candidate | issue | required_decision |
| --- | --- | --- |

## Handoff

- next_skill:
- required_inputs:
- latest_artifacts:
- blocked_reasons:
```
