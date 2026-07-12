---
name: ft-ui-automation-prep
description: Проводит post-iteration UI-проверку уже signed-off набора через Playwright CLI, собирает evidence, фиксирует расхождения FT vs UI и выпускает отдельную automation-ready версию тест-кейсов с актуализированными предусловиями, шагами и ожидаемыми результатами там, где это нужно для воспроизводимого прохождения и дальнейшей автоматизации.
---

# FT UI Automation Prep

Используй этот skill только после `ft-test-case-iteration`, когда набор уже получил статус `signed-off`.

Skill не пересматривает scope, не заменяет session-based review-cycle и не делает UI новым source of truth. Его задача — проверить готовые ручные кейсы в реальном интерфейсе, собрать evidence и подготовить отдельную automation-ready версию под дальнейшее написание автотестов. Эта версия должна быть не просто копией baseline со статусами, а practically executable handoff: по итогам UI-прохождения она уточняет реальные предусловия, тестовые данные, шаги и ожидаемые результаты там, где это требуется для воспроизводимого прохождения.

## Входы

- путь к FT-пакету `fts/<ft-slug>/...`;
- package-specific `AGENT-NOTES.md`, если он есть;
- package-level UI notes `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`, если они есть;
- signed-off набор тест-кейсов;
- `cycle-state.yaml` со статусом `signed-off`;
- `prompt.reviewer-to-ui-prep.md` из фактической stage-handoff папки; для новых handoff-папок это `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/`;
- `workflow-state.yaml` со значениями `stage_status: ready-for-next-stage` и `next_skill: ft-ui-automation-prep`;
- подтвержденный `scope-slug`;
- runtime URL или route entrypoint приложения;
- доступ к приложению: учетные данные, тестовая сессия или другой согласованный способ входа;
- при необходимости support-файлы и mockups из того же FT-пакета для интерпретации расхождений;
- рабочий Playwright CLI через wrapper script.

Если набор содержит `**Статус тест-кейса:** candidate-ui-calibration` или `**Статус oracle:** ui-calibration-required`, UI-stage должен выполнить calibration: найти фактический trigger валидации, зафиксировать observed UI behavior, предложить regression-ready expected result и перевести oracle только в `observed-ui-backed` после evidence.

Если `automation-ready` файл для нужного scope отсутствует, но baseline файл в `fts/<ft-slug>/test-cases/` уже существует, skill должен сначала создать initial `automation-ready` версию на основе baseline и только потом использовать ее как вход для UI-прогона. Подробный lifecycle см. в [../../references/qa/automation-ready-lifecycle.md](../../references/qa/automation-ready-lifecycle.md).

## Выходы

- `ui-validation-report.md` в `fts/<ft-slug>/work/ui-automation-prep/<scope-slug>/`;
- `ui-evidence-index.md` в `fts/<ft-slug>/work/ui-automation-prep/<scope-slug>/`;
- Playwright artifacts в `output/playwright/<scope-slug>/`;
- отдельная automation-ready версия тест-кейсов в `fts/<ft-slug>/test-cases/automation-ready/<section-id>-<scope-slug>.md`, уточненная по фактически наблюдаемому UI в пределах signed-off intent;
- список blockers и limitations, если UI недоступен или шаги не наблюдаемы.

## Workflow

1. Подтверди, что входной набор уже имеет статус `signed-off`. Если статус `round-cap-reached` или другой unresolved, зафиксируй blocked input и не выпускай automation-ready версию.
2. Проверь, существует ли `fts/<ft-slug>/test-cases/automation-ready/<section-id>-<scope-slug>.md`.
   - Если файл уже есть, используй его как входной артефакт для UI-прогона.
   - Если файла нет, но существует baseline файл `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`, сначала создай initial `automation-ready` версию из baseline без смены UI-статусов.
   - Если нет ни `automation-ready`, ни baseline файла, зафиксируй отсутствие входного артефакта и остановись.
3. Если в корне FT-пакета есть `AGENT-NOTES.md`, используй его как обязательный package-specific context.
4. Если для FT-пакета есть `work/ui-automation-prep/UI-AGENT-NOTES.md`, используй его как обязательный phase-specific context для UI-прогонов: runtime entrypoints, credentials, flow создания тестовых данных и другие устойчивые operational notes должны браться оттуда, а не из памяти прошлых сессий.
5. Возьми только уже утвержденный набор тест-кейсов и не расширяй scope самостоятельно.
6. Если создаешь initial `automation-ready`, делай это как отдельную фазу:
   - сохрани трассируемость к baseline;
   - не меняй baseline файл;
   - не ставь `confirmed`, `mismatch-ft-ui` или `blocked-*` только потому, что файл подготовлен;
   - не переписывай expected result под предполагаемое UI behavior до реального прогона.
   - если `Предусловия` требуют UI state, но дают только passive state без action setup steps, fixture/API setup или reusable setup profile, пометь кейс как not automation-ready до уточнения setup path; не додумывай путь подготовки.
7. Используй Playwright CLI в CLI-first режиме. Перед обращением к element refs всегда делай свежий `snapshot`.
8. Делай повторный `snapshot` после навигации, открытия модалок, крупных UI changes и смены вкладок.
9. Для каждого кейса проставь один `ui_verification_status`:
   - `confirmed`
   - `mismatch-ft-ui`
   - `blocked-ui-unavailable`
   - `blocked-access`
   - `blocked-observability`
   - `not-automatable-manual-only`
   A test case is not automation-ready when `Предусловия` require a UI state but provide only passive state wording without action setup steps, fixture, API setup, or reusable setup profile.
10. Для каждого кейса со статусом `confirmed` или `mismatch-ft-ui` сохраняй screenshot. Если шаг падает, происходит неожиданная навигация или найден mismatch, дополнительно сохраняй trace.
11. Индексируй все screenshots, snapshots, traces и logs в `ui-evidence-index.md`.
    - Evidence quality, DOM-seeded observations, local `output/` paths и trace limitations оценивай по [../../references/agent/ui-evidence-policy.md](../../references/agent/ui-evidence-policy.md).
    - Каждому artifact назначай уникальный стабильный `evidence_id`; automation-ready кейсы ссылаются на этот ID, а не используют локальный path как идентичность evidence.
    - Не публикуй raw artifact с PII/session data ради переносимости: оставь его restricted и опубликуй только безопасный индекс без чувствительных значений.
    - Не ставь `confirmed` или `mismatch-ft-ui` на основании DOM-seeded observation, пользовательского комментария или старого screenshot без normal UI path.
12. Если UI расходится с ФТ, не переписывай baseline-набор. Зафиксируй `FT vs UI` divergence в report и в automation-ready версии.
13. В automation-ready версии сохраняй все обязательные поля ручного тест-кейса из `test-case-format.md` и добавляй:
    - `UI Verification Status`
    - `UI Evidence`
    - `Automation Notes`
    - `FT/UI Divergence`, если есть расхождение
14. Если после прогона пользователь дает комментарий с уточнением воспроизведения, ожидаемого поведения или недостающего шага, используй этот комментарий как вход для повторной UI-проверки нужного кейса, а не как прямое основание для смены статуса.
15. Перед актуализацией статуса, evidence или automation-ready кейса перепройди затронутый кейс в UI с учетом пользовательского комментария и заново подтверди либо не подтверди воспроизводимость ожидаемого поведения.
16. Для `confirmed` кейсов разрешено дополнять и конкретизировать предусловия, тестовые данные, шаги и ожидаемый результат под реально наблюдаемый UI, если трассировка к ФТ сохраняется.
16a. Для `candidate-ui-calibration` кейсов зафиксируй observed UI behavior в `ui-validation-report.md` и `ui-evidence-index.md`, обнови automation-ready expected result на один конкретный observed oracle, измени `Статус oracle` на `observed-ui-backed` и сохрани связь с исходным candidate/baseline. Baseline FT-first файл не переписывай без evidence.
17. Для `mismatch-ft-ui` кейсов разрешено отражать фактический executable flow UI, включая дополнительные действия, нужные для прохождения ветки в интерфейсе, но расхождение с ФТ должно оставаться отдельной явной пометкой `FT/UI Divergence`.
18. Если прохождение кейса требует дополнительного действия, неочевидного из baseline, фиксируй это действие в самом automation-ready кейсе, а не оставляй его только в `Automation Notes`.
19. Для `blocked-*` и `not-automatable-manual-only` кейсов не удаляй кейс из automation-ready версии: оставляй blocker или limitation как часть результата и не додумывай недостающий executable path.
20. Если утверждение из ФТ не имеет наблюдаемого UI-критерия, используй `blocked-observability`, а не домысливай поведение интерфейса.
21. Закрой `workflow-state.yaml` по каноническому terminal contract из `workflow-state-format.md`:
    - `stage_status: completed`, `next_skill: none`, пустые `blocking_reasons` и успешный `closeout_status`, если этап действительно завершен;
    - `stage_status: blocked-input`, `next_skill: none`, `closeout_status: ui-prep-blocked` и конкретные `blocking_reasons`, если повторный UI-доступ, fixture или наблюдаемость еще нужны.

## Канонические references

- Карта skill-ов: [../README.md](../README.md)
- Индекс контрактов инструкций: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Политика UI evidence: [../../references/agent/ui-evidence-policy.md](../../references/agent/ui-evidence-policy.md)
- Negative UI calibration policy: [../../references/agent/negative-ui-calibration-policy.md](../../references/agent/negative-ui-calibration-policy.md)
- Workflow state: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Формат next-step prompt: [../../references/agent/next-step-prompt-format.md](../../references/agent/next-step-prompt-format.md)
- Формат ручного тест-кейса: [../../references/qa/test-case-format.md](../../references/qa/test-case-format.md)
- Правила трассировки: [../../references/qa/traceability-rules.md](../../references/qa/traceability-rules.md)
- Lifecycle automation-ready: [../../references/qa/automation-ready-lifecycle.md](../../references/qa/automation-ready-lifecycle.md)
- Формат UI automation prep: [../../references/qa/ui-automation-prep-format.md](../../references/qa/ui-automation-prep-format.md)
- Handoff-модель и numbered naming: [../../references/agent/stage-handoff-model.md](../../references/agent/stage-handoff-model.md)
- Границы skill-ов: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)
- Шаблон UI agent notes: [../../references/agent/ft-ui-agent-notes-template.md](../../references/agent/ft-ui-agent-notes-template.md)

## Ограничения

- Не используй этот skill до завершения `ft-test-case-iteration` со статусом `signed-off`.
- Не выбирай FT-пакет и не определяй scope с нуля.
- Не перезаписывай baseline signed-off набор тест-кейсов.
- Не считай UI канонической заменой текста ФТ.
- Не генерируй Playwright test specs вместо подготовки automation-ready тест-кейсов.
- Не подменяй молча FT-смысл: можно уточнять executable flow и условия прохождения в UI, но нельзя менять бизнес-ожидание без явной пометки `FT/UI Divergence`.
- Не меняй статус кейса и не актуализируй automation-ready версию только на основании комментария пользователя без повторной проверки этого кейса в UI.
- Не скрывай проблемы доступа, нестабильности среды или ненаблюдаемости шага: фиксируй их в report как blockers или limitations.

## UI Access Stop Condition

Если во время `ft-ui-automation-prep` агент не может получить доступ к рабочему UI после 2 последовательных попыток входа, включая не менее 1 fallback-способа, он должен остановить UI-прогон и зафиксировать блокировку в результатах. Продолжать попытки, менять runtime URL или использовать launcher/workaround-разработки можно только после явного подтверждения.
