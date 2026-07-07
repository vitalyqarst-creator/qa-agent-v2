# Source Selection Format

`source-selection.md` фиксирует выбранный FT-пакет и источники до scope analysis. Он не заменяет `workflow-state.yaml`: первый описывает выбор файлов, второй хранит process-status и routing.

## Purpose

- сделать выбор источников воспроизводимым без истории чата;
- не смешивать выбор FT-пакета с определением scope;
- явно отделить main FT от support/mockups;
- зафиксировать `main-ft-xhtml` как mandatory primary machine-readable extraction source;
- передать source-quality limitations до `ft-scope-analyzer`, writer и reviewer;
- остановить downstream workflow, если источник неоднозначен или отсутствует обязательный XHTML.

## Location

Новый handoff хранится только внутри numbered stage handoff:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-or-container-slug>/source-selection.md
```

Для предварительного контейнера без выбранного scope используй `00-<container-slug>`. Не создавай handoff artifacts в корне `fts/<ft-slug>/`: это contamination risk для clean runs.

## Source Priority

1. DOCX remains the authoritative main FT source of truth.
2. XHTML is mandatory as the primary machine-readable extraction source.
3. PDF is a structural/visual cross-check source.
4. Support files clarify only within confirmed scope.
5. Mockups provide UI interaction hints but do not define business rules.

DOCX остается главным исходным документом ФТ / source of truth. XHTML обязателен как основной машиночитаемый источник извлечения требований: текст, таблицы, списки, вложенные списки, перечни значений, структура разделов и строки таблиц извлекаются из XHTML первыми. PDF используется для structural/visual cross-check и не заменяет ни DOCX, ни XHTML. Если XHTML противоречит DOCX/PDF, фиксируй discrepancy / `coverage gap`, а не выбирай по догадке.

## Validator Contract

- `current_stage: ft-source-locator` в `workflow-state.yaml` обязан ссылаться на `source-selection.md` через `required_inputs` и/или `latest_artifacts.source_selection`.
- `source-selection.md` должен содержать required sections: `Context`, `Main FT Documents`, `Machine-Readable XHTML Source`, `Structural Cross-Check PDF`, `Support Files And Mockups`, `Source Quality`, `Ambiguity And Decision Log`, `Handoff`.
- `Context` должен содержать `selected_ft_slug` и `selection_status`; display labels such as `Selected FT slug` and `Selection status` are allowed because they normalize to the same field names.
- `selection_status` must be one of `selected | ambiguous | blocked-input`.
- If `selection_status` is not `selected`, workflow must remain blocked and must not route downstream.
- `Machine-Readable XHTML Source` must include `xhtml_available: yes | no`.
- If `selection_status = selected`, then `xhtml_available` must be `yes`.
- If `xhtml_available != yes`, workflow must remain `blocked-input` and must not route downstream.
- If `xhtml_available = yes`, `xhtml_path` must resolve to the main FT XHTML under `source/` or another valid relative path inside the FT package.
- Source-locator handoff не должен создавать `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.

## Required Sections

### Context

Минимальные поля:

- `request_summary`;
- `selected_ft_slug`;
- `selection_status`: `selected | ambiguous | blocked-input`;
- `created_at`;
- `created_by`.

Если статус не `selected`, downstream stages не стартуют без явного решения пользователя или обновленного `source-selection.md`.

### Main FT Documents

Перечисли все документы, которые считаются основным ФТ.

Required columns:

- `path`;
- `role`: `main-ft-docx | main-ft-xhtml | main-ft-pdf | main-ft-other`;
- `selection_reason`;
- `version_or_date`;
- `source_quality_notes`.

`main-ft-docx` является source of truth. `main-ft-xhtml` обязателен для extraction. `main-ft-pdf` используется только как structural/visual cross-check.

### Machine-Readable XHTML Source

Минимальные поля:

- `xhtml_available`: `yes | no`;
- `xhtml_path`;
- `xhtml_matches_main_ft`: `yes | no | not-checked`;
- `xhtml_extraction_priority`: `primary`;
- `xhtml_required_for_downstream`: `yes`;
- `limitation`;
- `blocking_reason`.

Если XHTML отсутствует, укажи `selection_status: blocked-input`, `xhtml_available: no`, `blocking_reason: missing main-ft-xhtml`, попроси добавить XHTML-версию основного ФТ в `source/` и не создавай downstream handoff как будто источник выбран корректно.

### Structural Cross-Check PDF

Минимальные поля:

- `pdf_available`: `yes | no`;
- `pdf_path`;
- `pdf_matches_main_ft`: `yes | no | not-checked`;
- `limitation`.

Отсутствие PDF не всегда blocker, но limitation должен быть передан downstream.

### Support Files And Mockups

Required columns:

- `path`;
- `role`;
- `why_relevant`;
- `must_use_downstream`: `yes | no`;
- `limitations`.

Support files and mockups do not expand scope without explicit DOCX/source-context confirmation.

### Source Quality

Зафиксируй:

- active source documents for validator;
- parseability status;
- section-id confidence;
- oversized blocks or chunking limitations;
- strict source-quality warnings.

Не скрывай strict warnings; документируй limitation или останавливай downstream через `blocked-input`.

### Ambiguity And Decision Log

Если выбор неоднозначен, перечисли candidate FT packages/files и причину: похожее имя, несколько версий, missing main FT, missing main-ft-xhtml, PDF mismatch или unclear file role.

Для `selection_status: ambiguous` workflow must use `stage_status: blocked-input` or another explicit non-ready status.

### Handoff

Handoff к `ft-scope-analyzer` разрешен только при `selection_status: selected` and `xhtml_available: yes`:

```yaml
current_stage: ft-source-locator
stage_status: ready-for-next-stage
next_skill: ft-scope-analyzer
```

`latest_artifacts` должен ссылаться на `source_selection`, active main FT DOCX, `main_ft_xhtml`, PDF/package notes if available, and artifact manifest if aliases or local-only evidence matter.

## Validator Findings

- `workflow-state-source-locator-missing-source-selection`: source-locator workflow does not link `source-selection.md`.
- `workflow-state-source-locator-premature-scope-artifacts`: source-locator handoff contains `scope-contract.md`, `prompt.scope-to-writer.md` or `prompt.scope-to-iteration.md`.
- `ft-package-root-level-handoff-artifacts`: FT package root contains root-level handoff artifacts.
- `source-selection-missing-required-sections`: `source-selection.md` misses one or more required handoff sections.
- `source-selection-missing-context-fields`: `Context` does not expose `selected_ft_slug` and/or `selection_status`.
- `source-selection-invalid-selection-status`: `selection_status` is outside `selected | ambiguous | blocked-input`.
- `workflow-state-source-selection-not-selected`: workflow routes downstream while `source-selection.md` is still `ambiguous` or `blocked-input`.
- `source-selection-missing-xhtml-section`: `source-selection.md` misses `Machine-Readable XHTML Source`.
- `source-selection-invalid-xhtml-availability`: `xhtml_available` is outside `yes | no`.
- `workflow-state-source-selection-missing-required-xhtml`: `selection_status = selected`, but `xhtml_available != yes`.
- `workflow-state-source-selection-xhtml-missing-routes-downstream`: workflow routes to scope/writer/reviewer/iteration while XHTML is missing.
- `source-selection-xhtml-path-missing`: `xhtml_available = yes`, but `xhtml_path` is empty or does not resolve.

## Minimal Template

```md
# Source Selection

## Context

- request_summary:
- selected_ft_slug:
- selection_status: `selected | ambiguous | blocked-input`
- created_at:
- created_by:

## Main FT Documents

| path | role | selection_reason | version_or_date | source_quality_notes |
| --- | --- | --- | --- | --- |

## Machine-Readable XHTML Source

- xhtml_available: `yes | no`
- xhtml_path:
- xhtml_matches_main_ft: `yes | no | not-checked`
- xhtml_extraction_priority: `primary`
- xhtml_required_for_downstream: `yes`
- limitation:
- blocking_reason:

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
