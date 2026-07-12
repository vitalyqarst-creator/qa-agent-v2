# Prompt: UI prep blocker follow-up

## Цель этапа

Подготовить безопасные внешние условия для возобновления `ft-ui-automation-prep` без изменения FT-first baseline и без повторного UI-прогона до снятия blockers.

## Входные артефакты

- `work/stage-handoffs/28-calculator-summary-production-readiness/workflow-state.yaml`
- `test-cases/14-application-card-calculator-summary-entrypoints.md`
- `test-cases/automation-ready/14-application-card-calculator-summary-entrypoints.md`
- `work/ui-automation-prep/application-card-calculator-summary-entrypoints/ui-validation-report.md`
- `work/ui-automation-prep/application-card-calculator-summary-entrypoints/ui-evidence-index.md`
- `work/ui-automation-prep/application-card-calculator-summary-entrypoints/runtime-setup-profile.md`
- `work/stage-handoffs/28-calculator-summary-production-readiness/ui-prep-session-log.md`
- `work/stage-handoffs/28-calculator-summary-production-readiness/agent-decision-log.ui-prep.md`

## Обязательные действия

- Предоставить safe synthetic fixture с переносимым identifier и documented create/reset path.
- Подтвердить или восстановить normal UI entrypoints для calculator stage/window.
- Обеспечить sanitized screenshot/trace capture без PII, credentials, cookies, tokens и sensitive payloads.
- После снятия blockers явно запустить rerun только `TC-ACCS-001..005` через `ft-ui-automation-prep`.
- Сохранить `GAP-001` до появления внешнего FT `Калькулятор`.

## Не делать

- не изменять FT-first baseline;
- не использовать observed UI как source of truth;
- не публиковать текущие local restricted Playwright artifacts;
- не запускать writer/reviewer cycle;
- не начинать новый UI-прогон до выполнения gate.

## Ожидаемые выходы

- safe fixture/runbook;
- подтвержденный calculator entrypoint;
- sanitized evidence policy/path;
- явное решение владельца требований по двум FT/UI divergences;
- обновленный `workflow-state.yaml`, разрешающий controlled UI rerun.

## Gate завершения

Follow-up завершен только когда fixture воспроизводима, calculator stage/window наблюдаем normal UI path, evidence безопасно публикуется, а два divergence имеют product/FT-owner disposition. До этого `stage_status` остается `blocked-input`, `next_skill: none`.
