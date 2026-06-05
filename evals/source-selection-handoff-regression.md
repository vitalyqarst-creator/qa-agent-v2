# Source Selection Handoff Regression

## Цель

Проверить, что `ft-source-locator` завершает только выбор источников и передает downstream stage воспроизводимый `source-selection.md`, а не начинает scope/writer работу преждевременно.

## Сценарий

Запустить `ft-source-locator` на чистом FT-пакете, где есть основной DOCX/PDF и нет ранее созданного handoff.

Ожидаемый результат стадии:

- создан `source-selection.md`;
- создан `source-locator-session-log.md`;
- создан `workflow-state.yaml`;
- `workflow-state.yaml` ссылается на `source-selection.md` через `required_inputs` и/или `latest_artifacts.source_selection`;
- `current_stage: ft-source-locator`;
- `next_skill: ft-scope-analyzer` или `stage_status: blocked-input`, если выбор источника неоднозначен.

## Pass Criteria

- Content-level gate:
  - `source-selection.md` includes required sections: `Context`, `Main FT Documents`, `Structural Cross-Check PDF`, `Support Files And Mockups`, `Source Quality`, `Ambiguity And Decision Log`, `Handoff`.
  - `Context` includes `selected_ft_slug` and `selection_status`.
  - If workflow routes to `ft-scope-analyzer` or downstream writer/reviewer stages, `selection_status` is `selected`.

- `source-selection.md` существует в текущей source-locator handoff-папке.
- В корне FT-пакета нет root-level workflow artifacts: `source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml`, `source-locator-session-log.md`, `scope-analyzer-session-log.md`.
- `workflow-state.yaml` содержит разрешающуюся ссылку на `source-selection.md`.
- В source-locator handoff-папке нет `scope-contract.md`, `prompt.scope-to-writer.md`, `prompt.scope-to-iteration.md`.
- Session log соответствует `ft-source-locator` stage и фиксирует clean package boundary.
- Validator проходит:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy audit
```

## Fail Criteria

- Content-level failures:
  - `source-selection.md` is a placeholder without required sections.
  - `source-selection.md` lacks `selected_ft_slug` or `selection_status`.
  - `selection_status` is outside `selected | ambiguous | blocked-input`.
  - `selection_status` is `ambiguous` or `blocked-input`, but workflow routes downstream anyway.

- `workflow-state.yaml` есть, но `source-selection.md` отсутствует или не связан из workflow.
- `source-selection.md` создан, но downstream должен искать его по догадке, а не по `workflow-state.yaml`.
- `source-selection.md`, `scope-options.md`, session logs или `workflow-state.yaml` созданы в корне `fts/<ft-slug>/`, а не в `work/stage-handoffs/NN-<scope-or-container>/`.
- Source-locator одновременно создает `scope-contract.md` или writer prompts.
- Агент утверждает, что source selection готов, но не зафиксировал active main DOCX/PDF и source-quality limitations.

## Validator Findings

- `source-selection-missing-required-sections` должен появляться для placeholder `source-selection.md`.
- `source-selection-missing-context-fields` должен появляться, если нет `selected_ft_slug` или `selection_status`.
- `source-selection-invalid-selection-status` должен появляться для неканонического status.
- `workflow-state-source-selection-not-selected` должен появляться, если workflow идет downstream при `selection_status != selected`.

- `workflow-state-source-locator-missing-source-selection` должен появляться, если source-locator workflow не ссылается на `source-selection.md`.
- `workflow-state-source-locator-premature-scope-artifacts` должен появляться, если source-locator handoff содержит scope-stage artifacts.
- `ft-package-root-level-handoff-artifacts` должен появляться, если clean FT package содержит root-level workflow handoff artifacts.

## Regression Lesson

Source selection - это отдельная стадия, а не неформальное вступление к scope analysis. Если ее результат не связан из `workflow-state.yaml`, следующая сессия может стартовать от неверного или неполного источника. Если source-locator начинает создавать scope artifacts, чистая диагностика теряет границы ответственности stage.
