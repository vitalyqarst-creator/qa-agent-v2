# UI Automation Prep Format

Канонический формат UI-проверки и automation-ready версии хранится в Markdown и используется для handoff после `ft-test-case-iteration`.

Все человекочитаемые поля `ui-validation-report.md`, `ui-evidence-index.md` и automation-ready версии должны быть заполнены на русском языке. Служебные имена полей, статусы и другие канонические enum-значения сохраняются в виде, заданном этим форматом.

## Closeout Status

Успешно завершенный UI-prep фиксируется в `workflow-state.yaml` так:

- `stage_status: completed`;
- `next_skill: none`;
- `blocking_reasons: []`;
- `closeout_status: ui-prep-complete` без UI findings либо `ui-prep-complete-with-findings`, если наблюдаемые неблокирующие расхождения сохранены;
- `latest_artifacts` связывает automation-ready test cases, UI validation report и UI evidence index.

Если доступ, fixture или наблюдаемость не позволяют закончить проверки, используй `stage_status: blocked-input`, `closeout_status: ui-prep-blocked` и конкретные `blocking_reasons`. Наличие FT/UI findings само по себе не блокирует closeout, если они наблюдаемы, классифицированы и не требуют повторного прогона для определения результата.

## Общие правила

- UI-проверка запускается только на наборе со статусом `signed-off`.
- Базовый signed-off набор остается FT-first и не перезаписывается.
- Если UI расходится с ФТ, это фиксируется как расхождение `FT vs UI`, а не как новый source of truth.
- UI-проверка не заменяет session-based review-cycle и не генерирует Playwright test specs.
- Automation-ready версия предназначена для practically executable handoff в автоматизацию: по итогам UI-прохождения она может уточнять фактически необходимые предусловия, тестовые данные, шаги и наблюдаемый результат, если это не ломает signed-off intent и не подменяет FT смыслом UI.
- Если после прогона пользователь дает комментарий, уточняющий воспроизведение или ожидаемое поведение, этот комментарий используется как вход для повторной UI-проверки, а не как самостоятельное evidence для смены статуса или актуализации кейса.
- Подробный lifecycle `baseline -> initial automation-ready -> UI rerun -> updated automation-ready` хранится в [automation-ready-lifecycle.md](./automation-ready-lifecycle.md).
- Evidence trust levels, DOM-seeded ограничения, local `output/` portability и trace policy определяются в [../agent/ui-evidence-policy.md](../agent/ui-evidence-policy.md).
- Если `automation-ready` файла еще нет, но baseline файл уже существует, допускается сначала создать initial `automation-ready` версию на основе baseline, а затем использовать ее как вход для UI-прогона.

## UI Validation Report

`ui-validation-report.md` хранится в `fts/<ft-slug>/work/ui-automation-prep/<scope-slug>/`.

Каждый проверенный тест-кейс должен быть отдельным блоком и включать:

- `test_case_id`
- `ui_verification_status`
- `result_summary`
- `ui_steps_checked`
- `evidence`
- `ft_reference`
- `automation_notes`
- опционально `ft_ui_divergence`

### Допустимые статусы

- `confirmed`
- `mismatch-ft-ui`
- `blocked-ui-unavailable`
- `blocked-access`
- `blocked-observability`
- `not-automatable-manual-only`

### Рекомендуемый шаблон

```md
## UI Validation Report

### TC-DEMO-001
**UI Verification Status:** confirmed
**Result Summary:** Шаги кейса подтверждены в реальном UI.

**UI Steps Checked:**
1. Открыт экран `Анкета клиента`.
2. Поле `ФИО клиента` оставлено пустым.
3. Выполнена попытка сохранения.

**Evidence:**
- `output/playwright/demo-scope/TC-DEMO-001/screenshot-01.png`
- `output/playwright/demo-scope/TC-DEMO-001/trace.zip`

**FT Reference:** `GSR 11`; `2.1.1.1.1.1.2`

**Automation Notes:** Для автотеста нужен стабильный селектор кнопки сохранения.
```

## UI Evidence Index

`ui-evidence-index.md` хранится рядом с report и индексирует все артефакты Playwright.

Если evidence-артефакты намеренно остаются локальными, индекс должен явно объявить это до таблицы evidence:

- `evidence_export_policy`: `local-output-index-only`
- `artifact_availability`: пути `output/` являются локальными Playwright-артефактами и не переносимы в чистый checkout.
- `dom_seeded_policy`: `non-canonical-observation`, если присутствуют DOM-seeded наблюдения.
- `trace_policy`: `not-collected`, если Playwright traces намеренно не собирались.
- `downstream_rule`: `dom-seeded-not-confirmed`, если DOM-seeded наблюдения не должны считаться `confirmed`.

DOM-seeded observations не являются normal UI path и не могут самостоятельно подтверждать `confirmed` или `mismatch-ft-ui`.

Каждая запись должна включать:

- `evidence_id` — уникальный стабильный ID по `references/agent/ui-evidence-policy.md`;
- `test_case_id`
- `artifact_type`
- `path`
- `note`

### Допустимые `artifact_type`

- `snapshot`
- `screenshot`
- `trace`
- `log`

## Automation-Ready Test Cases

Automation-ready версия хранится в `fts/<ft-slug>/test-cases/automation-ready/<section-id>-<scope-slug>.md`.

Она сохраняет все обязательные поля из `test-case-format.md` и добавляет:

- `UI Verification Status`
- `UI Evidence`
- `Automation Notes`
- опционально `FT/UI Divergence`

`UI Evidence` ссылается прежде всего на стабильные `evidence_id` из `ui-evidence-index.md`. Локальный path можно оставить рядом как диагностический locator, но он не заменяет ID и не обязан переноситься в другой checkout.

При необходимости automation-ready версия может и должна уточнять существующие поля кейса по данным UI-прохождения:

- предусловия;
- тестовые данные;
- шаги;
- итоговый ожидаемый результат.

Такая актуализация нужна для того, чтобы кейс стал воспроизводимым и пригодным для дальнейшей автоматизации. Она допустима только в пределах already signed-off intent. Если уточнение меняет бизнес-ожидание относительно ФТ, это оформляется не как тихая правка кейса, а как явное расхождение `FT/UI Divergence`.

Если основанием для уточнения служит комментарий пользователя после прогона, перед изменением `ui_verification_status`, evidence или automation-ready кейса нужно перепроверить этот кейс в UI с учетом комментария и только после этого вносить актуализацию.

### Поведение по статусам

- `confirmed` — предусловия, тестовые данные, шаги и ожидаемый результат можно уточнить под реально наблюдаемый UI, если кейс становится точнее и воспроизводимее без потери трассировки к ФТ.
- `mismatch-ft-ui` — baseline не меняется; в automation-ready версии можно отразить фактический путь прохождения UI, включая дополнительные шаги и условия, но явная пометка `FT/UI Divergence` остается обязательной.
- `blocked-ui-unavailable`, `blocked-access`, `blocked-observability`, `not-automatable-manual-only` — кейс не удаляется, а сохраняется с blocker или limitation; недостающий executable path не додумывается.

### Рекомендуемый шаблон automation-ready кейса

```md
## TC-DEMO-001
**Название:** Обязательность поля «ФИО клиента» при пустом значении
**Приоритет:** High
**Тип:** Validation

**Цель:** Проверить обязательность поля `ФИО клиента`.

**Предусловия:**
- Открыт раздел `Основная информация`.

**Тестовые данные:**
- Поле `ФИО клиента` оставлено пустым.

**Шаги:**
1. Оставить поле `ФИО клиента` пустым.
2. Нажать кнопку сохранения.

**Итоговый ожидаемый результат:** Система не сохраняет форму и показывает реакцию на обязательность поля.

**Постусловия:**
- -

**Ссылка на ФТ:** `GSR 11`; `2.1.1.1.1.1.2`

**Источник требования:**
- `2.1.1.1.1.1 Раздел «Основная информация»`

**Источник / цитата требования:** Поле обязательно, если ручной ввод не включен.

**UI Verification Status:** confirmed
**UI Evidence:**
- `output/playwright/demo-scope/TC-DEMO-001/screenshot-01.png`

**Automation Notes:** Для автотеста нужен стабильный селектор поля и кнопки сохранения.
```

Если в ходе UI-прохождения выяснилось, что для успешного воспроизведения кейса нужен дополнительный шаг, неочевидный из baseline, этот шаг должен быть отражен в самом automation-ready кейсе, а не только в `Automation Notes`.
