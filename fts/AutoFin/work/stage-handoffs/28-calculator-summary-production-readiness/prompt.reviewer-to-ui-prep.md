# Handoff Prompt

## Цель этапа

Подготовить signed-off calculator-summary baseline к `ft-ui-automation-prep` без перезаписи FT-first production-файла.

## Входные артефакты

- `test-cases/14-application-card-calculator-summary-entrypoints.md`
- `work/test-design/14-application-card-calculator-summary-entrypoints/`
- `work/stage-handoffs/28-calculator-summary-production-readiness/promotion-receipt.json`
- `work/stage-handoffs/28-calculator-summary-production-readiness/iteration-summary.md`
- `work/review-cycles/codex-exec-prepared-standard-calculator-summary-production-v12-20260712/attempts/reviewer-r1/attempt-001/runner-output/findings.md`
- `work/stage-handoffs/27-calculator-summary-final-source-rebase/mockup-visual-inventory.md`
- `AGENT-NOTES.md`

## Обязательные действия

- Использовать skill `ft-ui-automation-prep` только от signed-off baseline.
- Если automation-ready файл отсутствует, создать initial automation-ready copy по lifecycle skill-а.
- Проверить виджет, переход на этап, кнопку, открытие окна и observable prefill presence.
- Сохранить `GAP-001` для полного состава и exact mapping prefill.

## Не делать

- Не изменять FT-first production baseline.
- Не использовать UI как источник новых бизнес-правил, расчётов или точного mapping.
- Не расширять scope на соседние разделы карточки заявки.

## Ожидаемые выходы

- Automation-ready версия или explicit UI blocker.
- Playwright/UI evidence и validation report.
- Обновлённый UI-prep workflow без изменения signed-off baseline.
