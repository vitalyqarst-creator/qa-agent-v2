# Prompt: UI prep blocker follow-up

## Цель этапа

Подготовить безопасные внешние условия для возобновления `ft-ui-automation-prep` без изменения FT-first baseline и без повторного UI-прогона до снятия blockers.

Проверка gate от `2026-07-12` на remediation HEAD `b0f1108cc2ded7cc9313938cabd2f7f79425cd15` не разрешила controlled rerun: новые evidence IDs и уточненная portability policy не заменяют отсутствующие fixture, entrypoint, observability path и product/FT-owner disposition.

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
- Документировать способ наблюдения independent calculator-stage values для `TC-ACCS-002` и prefill до пользовательского ввода для `TC-ACCS-005`.
- Настроить безопасный evidence path: sanitized screenshot/trace без PII/session data либо restricted local storage с публикуемым безопасным индексом и новыми стабильными `evidence_id`.
- Предоставить явное product/FT-owner disposition для divergences `TC-ACCS-003` и `TC-ACCS-004` либо явно подтвердить, что они остаются unresolved и не блокируют продуктовый closeout.
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
- безопасный evidence policy/path и индекс со стабильными `evidence_id`; raw restricted artifacts публиковать не требуется;
- явное решение владельца требований по двум FT/UI divergences;
- обновленный `workflow-state.yaml`, разрешающий controlled UI rerun.

## Gate завершения

Follow-up завершен только когда fixture воспроизводима, calculator stage/window наблюдаем normal UI path, для `TC-ACCS-002` и `TC-ACCS-005` определены независимые oracles, evidence можно безопасно проверить через sanitized artifacts либо restricted-local индекс, а два divergence имеют product/FT-owner disposition. Публикация raw trace с PII/session data не является gate. До снятия функциональных blockers `stage_status` остается `blocked-input`, `next_skill: none`; успешный rerun закрывается через канонический `stage_status: completed`.
