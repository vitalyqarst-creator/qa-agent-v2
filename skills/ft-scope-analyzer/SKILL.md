---
name: ft-scope-analyzer
description: Выделяет релевантные разделы ФТ, сужает границы анализа и фиксирует coverage gaps до написания тест-кейсов. Используй skill, когда FT-пакет уже выбран и нужно определить точный фрагмент требований, с которым дальше будет работать writer или reviewer.
---

# FT Scope Analyzer

## Bounded lean-production path

Если scope удовлетворяет eligibility из
`references/agent/lean-production-workflow.md`, используй этот профиль по
умолчанию. Его цель — пройти scope → source review → writer → reviewer →
promotion в одной пользовательской задаче, сохранив независимые модельные
сессии и все source/compiler/quality gates.

Для lean-run:

- загружай instruction scenario `scope.bounded_production`, а не полный
  `scope.manual` pack;
- материализуй все scope/compiler inputs одним patch и проверь их одним
  aggregate validation; допускается не более одного correction patch;
- не создавай успешные session logs, decision logs, `scope-agent-final.md`,
  `scope-execution-options.md`, N/A-only oracle inventories, `artifact-write/*`,
  schema canary и сохранённый dispatcher config;
- сохраняй один active prompt только для независимого source assertion review;
  после accepted receipt runner строит writer/reviewer input из prepared package;
- измеряй полный пользовательский wall-clock, включая orchestration и file work,
  по time budget канонического lean profile.

Если eligibility не выполнена или aggregate validation обнаружил semantic defect,
не маскируй это fast path: перейди на полный маршрут либо заверши `blocked-input`.
После deterministic dependency gate и до detailed v1 model call обязательно
примени scope execution profile assessment из `lean-production-workflow.md`.
Неизвестный eligibility-критерий или превышение лимита маршрутизирует scope в
`standard-production`; не используй количество BSR/GSR как оценку assertions/TC
и не запускай монолитный detailed v1 для standard scope. Сохрани внешний
scope целиком и передай его в standard semantic-design bridge; внутренние
`WP-*` не заменяют внешний scope и не создаются ради lean-лимита.
До assessment проверь обязательный hash binding prepared context; не принимай
ручные или изменённые после подготовки eligibility facts без совпадающего digest.

## Standard-production semantic-design bridge

Для `standard-production` следуй `lean-production-workflow.md`: boundary-v2 →
semantic author → materialization → независимый source review. Boundary
immutable; defect блокирует writer; retry/fallback/synthesis запрещены.
Materialization связывает обязательные compact session/decision logs.

## Source-first contract for new production cycles

For every new promotion-capable workflow, produce `source-assertions.json` from the
complete selected `source-row-inventory.md` before writer routing. Follow
`source-assertions-format.md` and `source-assertion-semantic-rule-card.md` for
hash binding, source row -> assertion -> `ATOM-*` -> `OBL-*` lineage,
condition/action/oracle clauses, `primary_gap_id`, dependency gaps, document-global constraints
and approved clarifications. Do not create or self-approve
`source-assertion-review.json` in this skill.

Create `prompt.scope-assertions-to-reviewer.md` and route one independent
`source_assertion_review` before writer. That review also challenges gap
classification, so do not run a second `scope_gap_review` over the same manifest-v4 source
model. A rejected assertion or receipt routes back to this skill; only an accepted
receipt with the exact manifest digest may route to writer/iteration. Compiler v2
remains diagnostic-only and cannot be promoted.

## Rules for `prompt.scope-gaps-to-reviewer.md`

If confirmed scope analysis creates at least one `GAP-*` in `scope-coverage-gaps.md`, create `prompt.scope-gaps-to-reviewer.md` and make it the active transition before writer starts.

Minimum for `prompt.scope-gaps-to-reviewer.md`:

- list `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`, `scope-clarification-requests.md` and `workflow-state.yaml`;
- list `source-parity-check.md`, `source-row-inventory.md`, `mockup-visual-inventory.md` and package `AGENT-NOTES.md` when they exist;
- require `source-selection.md` to confirm `xhtml_available: yes`; missing XHTML keeps the workflow at `blocked-input` before writer/reviewer routing;
- explicitly request reviewer mode `scope_gap_review`;
- require reviewer to check source anchors, blocking classification, clarification requests and downstream handling for every `GAP-*`;
- forbid reviewer from writing or reviewing test cases in this mode;
- define completion routing: passed review routes to `prompt.scope-to-writer.md`; failed review routes back to `ft-scope-analyzer` or `blocked-input`.

## Правила Формирования `prompt.scope-to-writer.md`

При создании `prompt.scope-to-writer.md` применяй специальный контракт из `next-step-prompt-format.md`. Prompt обязан быть самодостаточным для writer-сессии и явно переносить критичные правила из `scope-contract.md`, `scope-coverage-gaps.md`, `source-parity-check.md` и regression artifacts.

Минимум для каждого `prompt.scope-to-writer.md`:

- перечислить `scope-contract.md`, `scope-coverage-gaps.md`, `workflow-state.yaml`;
- перечислить `source-selection.md` с `xhtml_available: yes`; если XHTML отсутствует или не подтвержден, не запускай writer и зафиксируй blocking input issue;
- перечислить `source-parity-check.md`, если доступны DOCX+PDF; если artifact должен быть, но отсутствует, не запускай writer и зафиксируй blocking input issue;
- перечислить `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий; если artifact должен быть, но отсутствует, не запускай writer и зафиксируй blocking input issue;
- перечислить `negative-oracle-inventory.md` / `requiredness-oracle-inventory.md`, если scope содержит validation/format ограничения или обязательность; candidate rows с `decision = candidate_tc_required` и `oracle_status = ui-calibration-required` передавай writer-у, не скрывай их только в parent `GAP-*`; если нужный artifact отсутствует, не запускай writer и зафиксируй blocking input issue;
- перечислить `mockup-visual-inventory.md`, если подтвержденный UI scope имеет источник `mockup` / `mockups/` / изображение макета; если mockup есть, но visual inventory отсутствует или `opened != yes`, не запускай writer и зафиксируй blocking input issue;
- перечислить `AGENT-NOTES.md`, если он есть;
- перечислить regression/baseline artifacts, если они есть для того же scope или явно указаны в `scope-contract.md`;
- явно указать режим writer-а: `continue-current-workflow`, `revision-from-findings`, `rebuild-from-scope` или `fresh-eval-run`;
- требовать package-by-package writer-pass для каждого scope: `scope-contract.md` обязан содержать минимум один internal work package, а каждый `ATOM-*` и `TC-*` обязан иметь `package_id`;
- требовать три внутренних gate для каждого package: сначала package ledger self-check, затем Package Test Design Plan self-check, затем package TC self-check; переход к следующему package разрешен только после фиксации этих проверок;
- если scope строится по таблицам полей/действий или PDF/DOCX extraction, требовать `Source Table Normalization` до `Atomic Requirements Ledger`; table-header residue, соседние поля и low-confidence extraction rows должны идти в `GAP-*`, а не в `covered`;
- требовать `Artifact Write Strategy` preflight до записи больших generated artifacts и canonical file: если ожидается больше `20` `TC-*`, больше `30` `ATOM-*`, Markdown больше `20 000` символов, scope содержит `WP-*` или создаются `source-row-inventory.md` / `source-normalization-diagnostic.md`, stage должен сразу использовать `scripts/write_artifact_sections.py --manifest <manifest.json>`; one-shot PowerShell/here-string/inline giant command, compact draft, summary draft, ad-hoc `tmp/generate_*.py` и объединение требований ради сокращения canonical file запрещены;
- если есть previous `gap` / `unclear` lessons, запретить silently promote to `covered` без нового источника или observable artifact;
- если scope содержит internal/API/RabbitMQ/DB/model/persistence/async effects, требовать observable artifact gate: без artifact такие assertions остаются `gap` / `unclear`;
- явно указать writer outputs и gate: canonical test-case file, ledger, applicability/dependency/risk matrices, writer self-check, `prompt.writer-to-reviewer.round-1.md`, `stage_status: ready-for-review`; writer не ставит `signed-off`.

Используй этот skill после выбора FT-пакета и до написания или review тест-кейсов.

## Входы

- выбранный FT-пакет;
- package-specific `AGENT-NOTES.md`, если он есть в корне FT-пакета;
- основной DOCX ФТ как authoritative source of truth;
- XHTML-версия основного ФТ из `source/` как обязательный машиночитаемый extraction source;
- PDF-версия основного ФТ для сверки структуры, если она есть;
- запрос пользователя на конкретную область или функцию.

## Выходы

- карта внешних candidate scope-ов, если FT или запрос слишком широкий;
- релевантный раздел, подраздел или набор узких фрагментов для подтвержденного внешнего scope;
- краткое резюме границ анализа;
- список `coverage gaps` и открытых вопросов;
- выбранный режим scope: `manual-scope` или `agent-proposed-scope`;
- `scope-options.md` и `scope-selection-prompts.md`, если агент предлагает несколько вариантов scope;
- `scope-contract.md` с подтвержденными границами анализа;
- `source-parity-check.md`, если для основного ФТ доступны DOCX и PDF;
- `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий;
- `source-assertions.json` для нового production/promotion-capable workflow;
- `prompt.scope-assertions-to-reviewer.md` для независимой проверки source model;
- `mockup-visual-inventory.md`, если подтвержденный UI scope включает mockup / screen image / `mockups/`;
- `scope-coverage-gaps.md` с неоднозначностями и отсутствующими данными;
- `scope-clarification-requests.md`, если в `scope-coverage-gaps.md` есть хотя бы один gap;
- `scope-execution-options.md` с рекомендуемым следующим шагом;
- `prompt.scope-gaps-to-reviewer.md`, если в `scope-coverage-gaps.md` есть хотя бы один `GAP-*`;
- `prompt.scope-to-writer.md`, только если scope подтвержден и следующий этап действительно writer;
- `prompt.scope-to-iteration.md`, если scope подтвержден и доступен полный writer-reviewer loop;
- при необходимости результаты `resolve_sections()` или `preview_chunks()`.

## Workflow

Для полного, eval или diagnostic route перед завершением стадии создай или обнови `scope-analyzer-session-log.md` по `session-log-format.md`: зафиксируй inputs read, inputs not used, key decisions, risks/fallbacks, validation и contamination check. Для clean eval/diagnostic run добавь audit-секции `Event Timeline`, `Quality Checkpoints`, `Artifact Write Strategy`, `Technical Fallbacks`, `Handoff Notes For Next Session`. Chunked writer включай только по size/count thresholds из `lean-production-workflow.md`, а не из-за самого наличия `WP-*` или row inventory. Если был лимит команды, failed patch, chunked writing, helper script, temp content file или encoding fallback, заполни `Technical Fallbacks` строкой `TF-*`. Свяжи лог из `workflow-state.yaml` через `latest_artifacts.session_log` или `latest_artifacts.scope_analyzer_session_log`.
Для полного/eval/diagnostic route параллельно веди `agent-decision-log.md` по `agent-decision-log-format.md`. Успешный `lean-production` run не создает оба лога: typed receipts, workflow state и общий performance record являются audit trail; при failure создай один `failure-diagnostic.json`.
Для русскоязычных источников перед PowerShell-командами выставляй UTF-8 preamble из `session-log-format.md`; если вывод консоли искажает кириллицу, перечитай источник через явный UTF-8 file/script path, не используй mojibake stdout как evidence и зафиксируй это в `Technical Fallbacks`.

1. Перед `resolve_sections()` или любым scope narrowing проверь `source-selection.md`: если `xhtml_available != yes`, останови workflow как `blocked-input`, зафиксируй отсутствие обязательного `main-ft-xhtml` и не создавай `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.
1a. Используй `test_case_agent.resolve_sections()` для первичного сужения области.
1b. Используй XHTML в первую очередь для машинного извлечения текста, таблиц, строк, списков, вложенных списков, перечней значений, `source-row-inventory.md` и `dictionary-source` rows.
1c. Используй DOCX как authoritative source for meaning: если XHTML и DOCX расходятся, фиксируй discrepancy / `coverage gap`, а не выбирай по догадке.
2. Если для FT-пакета есть `AGENT-NOTES.md`, учти его как обязательный package-specific context.
3. Если PDF-версия основного ФТ доступна, используй ее для сверки структуры разделов, заголовков и границ выбранного scope; PDF не заменяет DOCX или XHTML.
4. Примени `scope-decomposition-policy.md`: если пользователь просит большое ФТ, весь документ или несколько разнородных разделов, сначала создай карту внешних candidate scope-ов по разделам/подразделам ФТ в режиме `agent-proposed-scope`.
5. При `agent-proposed-scope` сохрани `scope-options.md` и `scope-selection-prompts.md` в контейнере `00-<container-slug>/`; не создавай handoff к writer и не создавай `scope-contract.md`, `source-parity-check.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`, пока пользователь не выбрал один candidate scope.
5a. Все source/scope handoff artifacts сохраняй только в numbered-папке `fts/<ft-slug>/work/stage-handoffs/NN-<scope-or-container-slug>/`. Не создавай `source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml` или session logs в корне FT-пакета.
6. Если пользователь уже выбрал конкретный внешний scope, зафиксируй режим `manual-scope`.
7. Если раздел большой, используй `preview_chunks()` и выдели только нужные фрагменты внутри выбранного внешнего scope.
8. Зафиксируй, какие требования входят в scope, а какие не входят.
9. Если для основного ФТ доступны DOCX и PDF, создай `source-parity-check.md` по `source-parity-check-format.md`: сверяй коды требований, таблицы, строки, примечания и границы только выбранного scope.
   Если подтвержденный UI scope содержит mockup / screen image / `mockups/`, открой изображение визуально и создай `mockup-visual-inventory.md` по `mockup-visual-inventory-format.md` до handoff к writer. Инвентарь должен фиксировать видимые блоки, поля, действия, interaction hints, mockup-only элементы, конфликты с ФТ и решение `not_used_as_requirement_source = yes`. Если макет нельзя открыть или проверить визуально, переведи workflow в `blocked-input`, а не передавай writer-у задачу с догадками по UI-шагам.
9a. Если `source-parity-check.md` содержит секцию `Table / Row Parity` или подтвержденный scope основан на таблице полей/действий, создай отдельный `source-row-inventory.md` по `source-row-inventory-format.md` до handoff к writer. В inventory должны попасть все source rows выбранного scope, включая `in_scope = no`, применимые document-global/ancestor/cross-referenced constraints, rows/list values из XHTML, строки с PDF-only requirement codes и строки, которые могут стать `GAP-*`. Для compiler v3 заполни exact `source_path`, `source_locator`, `bounded_source_text`, `source_context_class` и `requirement_codes`; downstream manifest обязан совпасть с этим registry полностью. Не передавай writer-у табличный scope только с `source-parity-check.md`: writer должен получить независимый row inventory.
9b. Для табличного scope проверь расшифровку колонок, сокращений и локальных кодов; неподтвержденное значение, влияющее на test design, фиксируй как `GAP-*` типа `missing-source-definition`, а не как догадку.
10. Перед handoff к writer выполни `Scope Complexity Assessment`: оцени количество полей/блоков, условных зависимостей, validation domains, action flows, integrations/API/async, lifecycle/status rules и ожидаемых gaps.
10a. Если complexity/source rows выявляют validation/format/date/email/length/numeric/allowed-values ограничения или обязательность, создай `negative-oracle-inventory.md` / `requiredness-oracle-inventory.md` до handoff. Для каждого invalid/requiredness item проверь observable oracle: сообщение, подсветка, blocked transition, input filtering, save rejection, API response, visible marker или другой source-backed pass/fail artifact.
10b. Если source задает restriction/requiredness, но exact UI oracle отсутствует, не теряй obligation: укажи `decision = candidate_tc_required`, `oracle_status = ui-calibration-required`, stable `scope_obligation_id` (`SO-NEG-*` / `SO-REQ-*`) и передай writer-у как candidate TC по `negative-ui-calibration-policy.md`. Parent `GAP-*` используй только для общего неизвестного oracle, но child obligations перечисляй отдельно. `gap_required` оставляй для случаев, когда нельзя сформировать даже candidate TC.
10c. Если scope содержит буквальный UI-текст/сообщение или неоднозначное преобразование единиц, создай `source-to-package-fidelity.json` по canonical format и зарегистрируй его в `latest_artifacts`. Не преобразуй `МБ` в точные байты без source-backed policy; неизвестную точную boundary fixture сохрани как отдельный `GAP-*` obligation.
10d. Для нового production/promotion-capable workflow создай `source-assertions.json` по `source-assertions-format.md`, примени `source-assertion-semantic-rule-card.md` и покрой ровно все строки `source-row-inventory.md`. Если manifest не готов к независимому source review, оставь workflow в `blocked-input`.
11. Добавь в `scope-contract.md` секцию `Внутренние Рабочие Пакеты` для каждого подтвержденного scope. Если scope простой, создай один `WP-01`; если неоднородный, раздели работу на несколько `WP-*`. Не используй внутренние рабочие пакеты как замену внешнему split для всего ФТ.
12. Каждый внутренний рабочий пакет должен иметь focus, source_refs, included_requirements, design_method, expected_outputs и split_required. Это рабочий план writer-а, а не новый внешний scope. `prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md` должны явно требовать `package_id`, package ledger gate, Package Test Design Plan gate и package TC gate.
13. Если PDF для structural cross-check отсутствует, явно укажи это в промежуточных заметках или `coverage gaps`, а не оставляй неявным.
14. Отдельно перечисли отсутствующие данные и неоднозначности как `coverage gaps`; для каждого gap укажи точное утверждение ФТ, к которому он относится: раздел, GSR/код, таблицу/строку, поле/условие, цитату или `ATOM-*`, если атом уже создан.
15. Для новых handoff-папок используй numbered naming из `references/agent/stage-handoff-model.md`: `00-<container-slug>/` для контейнера выбора и `NN-<scope-slug>/` для подтвержденного scope-level handoff. Логический `scope_slug` оставляй без числового префикса.
16. После подтверждения scope сохрани `scope-contract.md`, `scope-coverage-gaps.md` и один активный downstream prompt; условно добавь `source-parity-check.md`, `source-row-inventory.md`, oracle inventories, `scope-clarification-requests.md` и `prompt.scope-gaps-to-reviewer.md`, когда их требуют правила выше. `scope-execution-options.md` создавай только для неоднозначного выбора следующего действия; в однозначном lean-run он запрещён как дубликат active route.
17. В `workflow-state.yaml` укажи один активный downstream `next_skill`, но сохраняй второй prompt в `latest_artifacts` как альтернативный user-facing entrypoint, если он применим. Для compiler contract v3 активный downstream до writer всегда `ft-test-case-reviewer` в режиме `source_assertion_review`, а `latest_artifacts` содержит `source_assertions` и `active_transition_prompt: prompt.scope-assertions-to-reviewer.md`; наличие gaps не создаёт дублирующий gap-review. Legacy workflow с gaps сохраняет маршрут через `prompt.scope-gaps-to-reviewer.md`, но не допускается к production promotion.
18. Передай выбранный scope дальше в `ft-test-case-writer`, `ft-test-case-reviewer` или `ft-test-case-iteration` вместе с информацией о XHTML extraction notes, source parity, PDF cross-check, package-specific notes, scope complexity assessment и обязательными внутренними рабочими пакетами.

## Канонические references

- Индекс контрактов инструкций: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Workflow state: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Session log format: [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md)
- Agent decision log format: [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md)
- Artifact write strategy: [../../references/agent/artifact-write-strategy-format.md](../../references/agent/artifact-write-strategy-format.md)
- Формат next-step prompt: [../../references/agent/next-step-prompt-format.md](../../references/agent/next-step-prompt-format.md)
- Формат Package Test Design Plan: [../../references/agent/package-test-design-plan-format.md](../../references/agent/package-test-design-plan-format.md)
- Coverage checklist: [../../references/qa/coverage-checklist.md](../../references/qa/coverage-checklist.md)
- Правила трассировки: [../../references/qa/traceability-rules.md](../../references/qa/traceability-rules.md)
- Формат scope contract: [../../references/agent/scope-contract-format.md](../../references/agent/scope-contract-format.md)
- Формат scope options: [../../references/agent/scope-options-format.md](../../references/agent/scope-options-format.md)
- Формат scope selection prompts: [../../references/agent/scope-selection-prompts-format.md](../../references/agent/scope-selection-prompts-format.md)
- Формат scope coverage gaps: [../../references/agent/scope-coverage-gaps-format.md](../../references/agent/scope-coverage-gaps-format.md)
- Формат scope clarification requests: [../../references/agent/scope-clarification-requests-format.md](../../references/agent/scope-clarification-requests-format.md)
- Формат scope execution options: [../../references/agent/scope-execution-options-format.md](../../references/agent/scope-execution-options-format.md)
- Правило декомпозиции scope-ов: [../../references/agent/scope-decomposition-policy.md](../../references/agent/scope-decomposition-policy.md)
- Формат source parity check: [../../references/agent/source-parity-check-format.md](../../references/agent/source-parity-check-format.md)
- Формат Source Row Inventory: [../../references/agent/source-row-inventory-format.md](../../references/agent/source-row-inventory-format.md)
- Формат Source-To-Package Fidelity: [../../references/agent/source-to-package-fidelity-format.md](../../references/agent/source-to-package-fidelity-format.md)
- Source-first assertion contract: [../../references/agent/source-assertions-format.md](../../references/agent/source-assertions-format.md)
- Source assertion semantic rule card: [../../references/agent/source-assertion-semantic-rule-card.md](../../references/agent/source-assertion-semantic-rule-card.md)
- Deterministic Source Row Baseline: [../../references/agent/source-row-baseline-format.md](../../references/agent/source-row-baseline-format.md)
- Формат Negative Oracle Inventory: [../../references/agent/negative-oracle-inventory-format.md](../../references/agent/negative-oracle-inventory-format.md)
- Формат Requiredness Oracle Inventory: [../../references/agent/requiredness-oracle-inventory-format.md](../../references/agent/requiredness-oracle-inventory-format.md)
- Negative UI calibration policy: [../../references/agent/negative-ui-calibration-policy.md](../../references/agent/negative-ui-calibration-policy.md)
- Формат mockup visual inventory: [../../references/agent/mockup-visual-inventory-format.md](../../references/agent/mockup-visual-inventory-format.md)
- Handoff-модель и numbered naming: [../../references/agent/stage-handoff-model.md](../../references/agent/stage-handoff-model.md)
- Границы skill-ов: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)
- Source parsing quality: [../../references/agent/source-parsing-quality.md](../../references/agent/source-parsing-quality.md)
- Lean production workflow: [../../references/agent/lean-production-workflow.md](../../references/agent/lean-production-workflow.md)

## Ограничения

- Не создавай финальные тест-кейсы как основной результат.
- Не ищи FT-пакет с нуля, если он еще не выбран.
- Не проводи архитектурный аудит agent-layer.
