# Handoff Prompt

## Цель этапа

Провести pre-writer review scope gaps в режиме `scope_gap_review`. Не писать и не review-ить тест-кейсы.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md` — должен подтверждать `xhtml_available: yes`.
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/scope-contract.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/source-parity-check.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/source-row-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/mockup-visual-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/negative-oracle-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/requiredness-oracle-inventory.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/scope-coverage-gaps.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/scope-clarification-requests.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/workflow-state.yaml`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/final-bsr-evidence.json`
- `AGENT-NOTES.md`

## Обязательные действия

- Проверь источники и anchors для `BSR 43–46`.
- Подтверди, что `BSR 35–38` исключены обоснованно.
- Проверь non-blocking классификацию `GAP-001` и отсутствие скрытого повышения exact mapping до covered.
- Проверь, что clarification request не нужен для ограниченного downstream покрытия.
- Проверь обязательные правила для writer/reviewer и package `WP-01`.
- Запрещено использовать production test cases, old PreFinal handoff или historical cycles как requirement evidence.

## Не делать

- Не писать и не review-ить тест-кейсы.
- Не расширять scope до внешнего ФТ `Калькулятор`.
- Не использовать макеты как источник бизнес-правил.

## Ожидаемые выходы

- Passed: создать `scope-gap-review.md`, обновить cycle state на `scope-gap-review-passed`/`scope-ready-for-writer`, затем активировать `prompt.scope-to-iteration.md`.
- Failed: вернуть в `ft-scope-analyzer` либо `blocked-input` с конкретными source-backed причинами.
