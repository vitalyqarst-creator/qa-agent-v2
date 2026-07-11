# Handoff Prompt

## Цель этапа

Провести первое контролируемое боевое испытание принятого v9 candidate: проверить точный diff, явно продвинуть только подтверждённый SHA и повторно доказать валидность production-результата.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/scope-contract.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/source-parity-check.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/source-row-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/mockup-visual-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/negative-oracle-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/requiredness-oracle-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/scope-coverage-gaps.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/scope-clarification-requests.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/iteration-summary.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/workflow-state.yaml`
- `work/review-cycles/codex-exec-prepared-standard-calculator-summary-final-v9-20260711/cycle-state.yaml`
- `work/review-cycles/codex-exec-prepared-standard-calculator-summary-final-v9-20260711/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `work/review-cycles/codex-exec-prepared-standard-calculator-summary-final-v9-20260711/attempts/reviewer-r1/attempt-001/runner-output/findings.md`
- `test-cases/14-application-card-calculator-summary-entrypoints.md`

## Обязательные действия

- Убедиться, что candidate SHA равен `7f7e076abf1faca3e4bf58e8aab62f2b7beec6ffd1e63ef4a05be4cc29c0bc00`.
- Показать и проверить semantic diff candidate против production baseline.
- Сохранить пять атомарных TC и `GAP-001`; не добавлять детали экрана калькулятора без нового источника.
- Продвигать только после явного подтверждения diff и повторно выполнить strict validator/reviewer gate.
- Проверить, что итоговый git diff ограничен ожидаемым calculator-summary production-файлом и handoff/runtime evidence.

## Не делать

- Не replay terminal v8/v9.
- Не использовать PreFinal или соседние test cases как requirement evidence.
- Не объявлять production signed-off до фактического продвижения и повторной проверки.

## Ожидаемые выходы

- Production calculator-summary содержит принятый набор из пяти TC.
- GAP-001 остаётся явным.
- Повторная проверка проходит без findings.
- Scope diff не содержит соседних production-файлов.
