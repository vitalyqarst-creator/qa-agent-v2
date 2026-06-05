# Scope Analyzer Handoff Regression

## Цель

Проверить, что `ft-scope-analyzer` не переводит workflow к writer/iteration без полного, воспроизводимого handoff-а по выбранному scope.

## Сценарий

После успешного `ft-source-locator` пользователь выбирает один scope. Агент запускает `ft-scope-analyzer` в режиме confirmed/manual scope.

## Pass Criteria

- `workflow-state.yaml` содержит `current_stage: ft-scope-analyzer`.
- Если `stage_status: ready-for-next-stage` и `next_skill: ft-test-case-writer`, workflow ссылается на:
  - `source-selection.md`;
  - `scope-contract.md`;
  - `scope-coverage-gaps.md`;
  - `prompt.scope-to-writer.md`;
  - `scope-analyzer-session-log.md`.
- Если `stage_status: ready-for-next-stage` и `next_skill: ft-test-case-iteration`, workflow ссылается на:
  - `source-selection.md`;
  - `scope-contract.md`;
  - `scope-coverage-gaps.md`;
  - `prompt.scope-to-iteration.md`;
  - `scope-analyzer-session-log.md`.
- Если `scope-coverage-gaps.md` содержит хотя бы один `GAP-*`, workflow также ссылается на `scope-clarification-requests.md`.
- Active `prompt.scope-to-writer.md` / `prompt.scope-to-iteration.md` input section lists resolving references to the same required scope handoff artifacts, including `source-selection.md`.
- Если доступны DOCX+PDF для подтвержденного scope, workflow и active prompt ссылаются на `source-parity-check.md`.
- Если `source-parity-check.md` содержит row-level/table parity, workflow и active prompt ссылаются на `source-row-inventory.md`.
- Если UI scope имеет mockup/source image, workflow и active prompt ссылаются на `mockup-visual-inventory.md`.
- Validator проходит:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy audit
```

## Fail Criteria

- `ready-for-next-stage` выставлен без `source-selection.md`.
- `ready-for-next-stage` выставлен без `scope-contract.md`.
- `ready-for-next-stage` выставлен без `scope-coverage-gaps.md`.
- Есть `GAP-*`, но нет `scope-clarification-requests.md`.
- `next_skill` указывает writer/iteration, но соответствующий `prompt.scope-to-*` отсутствует или не резолвится.
- Matching `prompt.scope-to-*` exists, but its input section omits `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`, or required conditional artifacts.
- `source-parity-check.md` contains `Table / Row Parity`, but handoff has no linked `source-row-inventory.md`.
- Active `prompt.scope-to-*` omits `source-row-inventory.md` when row-level parity exists.
- Session log относится к другому stage.

## Validator Findings

- `workflow-state-scope-analyzer-missing-handoff-artifacts`: missing `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md` or matching scope prompt.
- `workflow-state-scope-analyzer-missing-clarification-requests`: `scope-coverage-gaps.md` contains gaps, but no `scope-clarification-requests.md` is linked.
- `workflow-state-scope-analyzer-missing-source-row-inventory`: `source-parity-check.md` contains row-level parity, but no scope `source-row-inventory.md` is linked. This is an `error`, because routing writer/iteration without an independent source-row inventory can silently drop table rows.
- `prompt-format-missing-required-scope-inputs`: active scope transition prompt does not list required input artifacts for the next skill.

## Regression Lesson

Writer defects often start before writer: if scope-analyzer handoff is incomplete, writer has to infer boundaries, gaps and instructions from chat history. This regression keeps scope analysis as a real file-based contract instead of a loose transition message.
