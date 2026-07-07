---
name: ft-source-locator
description: Находит нужный FT-пакет, основное ФТ, support-файлы и макеты перед анализом требований. Используй skill, когда нужно понять, с каким `fts/<ft-slug>/...` работать, какие файлы являются основными, а какие связанными, и куда потом должны сохраняться тест-кейсы.
---

# FT Source Locator

Используй этот skill, чтобы определить правильный FT-пакет и состав входных материалов до начала анализа.

## Входы

- запрос пользователя;
- текущая структура `fts/`;
- доступные `source/`, `support/`, `mockups/`, `test-cases/`.

## Выходы

- выбранный `ft-slug`;
- список основных документов ФТ;
- основной DOCX ФТ как authoritative source of truth;
- matching XHTML-версия основного ФТ в `source/` как обязательный machine-readable extraction source;
- `main_ft_xhtml` и `xhtml_available: yes | no`;
- список PDF-версий основного ФТ для сверки структуры, если они есть в FT-пакете;
- список support-файлов и макетов;
- package-specific `AGENT-NOTES.md`, если он есть в корне FT-пакета;
- `source-selection.md` в фактической stage-handoff папке; для новых handoff-папок это `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/`;
- структура `source-selection.md` определяется `source-selection-format.md`;
- `workflow-state.yaml` в фактической stage-handoff папке; для новых handoff-папок это `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/`;
- `source-locator-session-log.md` в той же stage-handoff папке, связанный из `workflow-state.yaml`;
- blocking reason `missing main-ft-xhtml`, если XHTML-версия основного ФТ отсутствует;
- явное указание, что результаты должны сохраняться в `fts/<ft-slug>/test-cases/`.

## Workflow

Перед завершением стадии создай или обнови `source-locator-session-log.md` по `session-log-format.md`: зафиксируй inputs read, inputs not used, key decisions, risks/fallbacks, validation и contamination check. Для clean eval/diagnostic run добавь audit-секции `Event Timeline`, `Quality Checkpoints`, `Technical Fallbacks`, `Handoff Notes For Next Session`; в `Inputs Not Used` и `Contamination Check` явно укажи соседние `fts/<ft-slug>*`, старые версии и baseline artifacts, которые были запрещены и не использовались. Свяжи лог из `workflow-state.yaml` через `latest_artifacts.session_log` или `latest_artifacts.source_locator_session_log`.
Параллельно веди `agent-decision-log.md` по `agent-decision-log-format.md`: фиксируй выбор FT package, источников, отклоненные соседние packages, ambiguity decisions и routing к scope analyzer; свяжи его через `latest_artifacts.decision_log`.
Для русскоязычных источников перед PowerShell-командами выставляй UTF-8 preamble из `session-log-format.md`; если вывод консоли искажает кириллицу, перечитай источник через явный UTF-8 file/script path, не используй mojibake stdout как evidence и зафиксируй это в `Technical Fallbacks`.

1. Просмотри `fts/` и карточки FT-пакетов.
2. Определи, к какому `ft-slug` относится запрос.
3. Зафиксируй, какие документы являются основным ФТ из `source/`, а какие относятся к support или mockups. Основной DOCX ФТ остается authoritative source of truth.
4. Найди matching XHTML-версию основного ФТ в `source/`. XHTML обязателен как основной машиночитаемый источник извлечения таблиц, строк, списков, вложенных списков, перечней значений и структуры разделов.
5. Отдельно найди PDF-версию основного ФТ для сверки структуры разделов. Ищи ее сначала в `source/`, затем в связанных материалах того же FT-пакета.
6. Если PDF-версия найдена, передай ее следующему skill-у как вход для structural/visual cross-check; PDF не заменяет DOCX или XHTML.
7. Если в корне FT-пакета есть `AGENT-NOTES.md`, передай его следующему skill-у как обязательный package-specific context.
8. Если PDF-версия не найдена, явно зафиксируй отсутствие PDF для сверки структуры, а не игнорируй это молча.
9. Если XHTML отсутствует, создай `source-selection.md` с секцией `Machine-Readable XHTML Source`, укажи `selection_status: blocked-input`, `xhtml_available: no`, `blocking_reason: missing main-ft-xhtml`, попроси добавить XHTML-версию основного ФТ в `source/` и не передавай задачу в `ft-scope-analyzer`.
10. Если выбор неоднозначен, сформулируй короткий список вариантов и чего именно не хватает для уверенного выбора.
11. Для новых handoff-папок используй numbered naming из `references/agent/stage-handoff-model.md`: `00-<container-slug>/` для предварительного контейнера выбора scope-ов и `NN-<scope-slug>/` для подтвержденного scope-level handoff. Логический `scope_slug` оставляй без числового префикса.
12. Сохрани `source-selection.md` и обнови `workflow-state.yaml` как handoff к `ft-scope-analyzer` только если `xhtml_available: yes`.
    - Если выбор источника неоднозначен, не запускай `ft-scope-analyzer`; зафиксируй `selection_status: ambiguous` или `blocked-input`.
    - Если XHTML отсутствует, не запускай `ft-scope-analyzer`, не создавай `scope-contract.md`, writer/reviewer/iteration prompt или downstream handoff.
    - Не создавай `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`: это ответственность `ft-scope-analyzer`.
13. При добавлении alias-копий source/support файлов или local-only evidence обнови `fts/artifact-manifest.json` по `references/agent/artifact-manifest-format.md`; binary alias не должен оставаться долгосрочной стратегией без manifest.
14. Не переходи к анализу секций или написанию тест-кейсов; передай управление следующему skill-у.

## Clean Diagnostic Isolation

Если запрос помечен как clean diagnostic/eval run или пользователь запретил использовать соседние пакеты:

- работай только внутри выбранного `fts/<ft-slug>`;
- не открывай, не сравнивай и не копируй артефакты из соседних `fts/<ft-slug>*`, старых версий и baseline packages;
- не используй готовые `00-scope-selection`, `scope-contract.md`, test-cases или review-cycle/legacy review artifacts из соседних пакетов как пример содержания;
- допустимо прочитать общие `skills/`, `references/`, `scripts/` и validator, потому что это правила агента, а не данные предыдущего FT run;
- если случайно был открыт соседний package artifact, зафиксируй contamination risk в `source-locator-session-log.md` и не выдавай run как clean.

## Канонические references

- Карта skill-ов: [../README.md](../README.md)
- Индекс контрактов инструкций: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Workflow state: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Session log format: [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md)
- Agent decision log format: [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md)
- Формат source selection: [../../references/agent/source-selection-format.md](../../references/agent/source-selection-format.md)
- Handoff-модель и numbered naming: [../../references/agent/stage-handoff-model.md](../../references/agent/stage-handoff-model.md)
- Границы skill-ов: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)
- Правила размещения знаний: [../../references/agent/content-placement.md](../../references/agent/content-placement.md)
- Artifact manifest: [../../references/agent/artifact-manifest-format.md](../../references/agent/artifact-manifest-format.md)
- Шаблон package-specific notes: [../../references/agent/ft-package-agent-notes-template.md](../../references/agent/ft-package-agent-notes-template.md)
- Source parsing quality: [../../references/agent/source-parsing-quality.md](../../references/agent/source-parsing-quality.md)
- Legacy strict source-quality warnings: [../../references/agent/source-quality-strict-warning-review-2026-05-25.md](../../references/agent/source-quality-strict-warning-review-2026-05-25.md)

## Ограничения

- Не формируй тест-кейсы.
- Не делай review существующих кейсов.
- Не проводи аудит архитектуры skill-слоя.
- Не считай source selection завершенным, если main FT XHTML отсутствует.
