# Prompt: Continue Questionnaire Upload V7

## Intent

Продолжить только после независимого review source-fidelity gate.

## Required Inputs

- активный `workflow-state.yaml` H56;
- `scope-coverage-gaps.md` и `scope-clarification-requests.md`;
- immutable prepared package V7 и offline validation report.

## Required Actions

Если `GAP-QUT-001` остается open, выполнить только gap review. Если получена source-backed convention, создать новую immutable revision, обновить binding policy и заново скомпилировать package.

## Forbidden Actions

Не запускать live и не менять baseline без отдельного нового authorization.

## Expected Output

Проверяемое reviewer decision и следующий numbered handoff.

## Stop Conditions

Любая попытка вывести byte convention из `МБ` без source-backed policy блокирует продолжение.
