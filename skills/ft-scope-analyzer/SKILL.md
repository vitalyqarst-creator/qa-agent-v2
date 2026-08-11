---
name: ft-scope-analyzer
description: Выделяет релевантные разделы ФТ, сужает границы анализа и фиксирует coverage gaps до написания тест-кейсов. Используй skill, когда FT-пакет уже выбран и нужно определить точный фрагмент требований, с которым дальше будет работать writer или reviewer.
---

# FT Scope Analyzer

## Default practical route

For ordinary work where the user wants test cases, use practical route v0.8 from
[../../references/agent/practical-test-case-route-v0.8.md](../../references/agent/practical-test-case-route-v0.8.md).

In this route, scope analysis prepares only the next writer input:

- confirm external scope boundaries by FT section/subsection;
- create one compact `scope-brief.md` under
  `fts/<ft-slug>/work/practical/<scope-slug>/`;
- create `source-parity-check.md` before writer handoff when the main FT has
  both DOCX and PDF;
- create a compact `source-row-inventory.md` before writer handoff when the
  selected scope is driven by FT table rows, action rows, field rows, status
  rows, document mappings or fixed value lists;
- keep FT context, gaps, dictionary values and candidate UI calibration concise
  in `scope-brief.md`; create `scope-clarification-requests.md` only for a
  concrete BA question;
- route next to `ft-test-case-writer` in `practical_v0_8_matrix` mode, not to `source_assertion_review` or `ft-test-case-iteration`.

Do not create `scope-contract.md`, a separate `scope-coverage-gaps.md`, oracle
inventories, session/decision logs or heavy/source-first artifacts in
`practical_v0_8`; those belong to legacy, diagnostic or explicitly selected routes.

Все актуальные practical artifacts scope — brief, matrix, prompts, summary и
review receipts — хранятся в этой единственной директории. Не создавай второй
параллельный каталог с повторным section id.

### Mandatory route gate

Choose the route once, before creating any scope-local artifact. For
`practical_v0_8`, a `GAP-*`, a cross-FT reference or an unresolved UI oracle
does **not** authorize a pre-writer `scope_gap_review`. Keep the uncertainty
compactly in `scope-brief.md` and, only when a concrete product decision is
missing, in `scope-clarification-requests.md`. Route directly to the
matrix-only writer.

The legacy/session instructions below are available only when that route was
explicitly selected. Do not borrow its artifacts, statuses or reviewer stages
into a practical handoff.

## Bounded lean-production path

Если scope удовлетворяет eligibility из
`references/agent/lean-production-workflow.md`, используй этот профиль только
когда пользователь явно запросил lean/source-qualified/immutable production
route. Его цель — пройти scope → source review → writer → reviewer → promotion
в одной пользовательской задаче, сохранив независимые модельные сессии и все
source/compiler/quality gates.

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

## Standard-production source-first route

For new `standard-production` work, use boundary-v2/source-first routing by
default only when the user explicitly selected the standard production route.
For ordinary test-case writing, use `practical_v0_8` instead. Do not materialize
the semantic-design bridge merely because a scope is large or not lean-eligible.
The bridge route remains available only when the user or a recovery procedure
explicitly requests it.

The default standard path is: boundary/source inventory -> source assertions ->
independent source assertion review -> production input finalization ->
`ft-agent run` schema v2. When no semantic bridge projection is embedded, the
runner builds typed derivations from the accepted source-first contract.

Legacy explicit semantic-design bridge behavior:

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
remains diagnostic-only and cannot be promoted. This contract is not part of
`practical_v0_8`.

## Legacy/session route only: Rules for `prompt.scope-gaps-to-reviewer.md`

Only if the user explicitly selected the legacy/session route and confirmed
scope analysis creates at least one `GAP-*` in `scope-coverage-gaps.md`, create
`prompt.scope-gaps-to-reviewer.md` and make it the active transition before
writer starts. This section never applies to `practical_v0_8`.

Minimum for `prompt.scope-gaps-to-reviewer.md`:

- list `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`, `scope-clarification-requests.md` and `workflow-state.yaml`;
- list `source-parity-check.md`, `source-row-inventory.md`, `mockup-visual-inventory.md` and package `AGENT-NOTES.md` when they exist;
- require `source-selection.md` to confirm `xhtml_available: yes`; missing XHTML keeps the workflow at `blocked-input` before writer/reviewer routing;
- explicitly request reviewer mode `scope_gap_review`;
- require reviewer to check source anchors, blocking classification, clarification requests and downstream handling for every `GAP-*`;
- forbid reviewer from writing or reviewing test cases in this mode;
- define completion routing: passed review routes to `prompt.scope-to-writer.md`; failed review routes back to `ft-scope-analyzer` or `blocked-input`.

## Правила Формирования `prompt.scope-to-writer.md`

Для `practical_v0_8` prompt содержит только путь к `scope-brief.md` и к
присутствующим parity/row/mockup/BA artifacts; не дублирует правила и не
ссылается на `scope-contract.md`, full gaps или oracle inventories.
Полный legacy/session contract хранится в `next-step-prompt-format.md`.

При создании `prompt.scope-to-writer.md` сначала выбери route, затем применяй соответствующий раздел `next-step-prompt-format.md`.

Для `practical_v0_8` prompt обязан быть коротким и содержать только:

- `source-selection.md`, `scope-brief.md` и `workflow-state.yaml`;
- существующие для scope `source-parity-check.md`, `source-row-inventory.md`, `mockup-visual-inventory.md`, `scope-clarification-requests.md`, `AGENT-NOTES.md` и разрешенные source/support файлы;
- первый writer pass `practical_v0_8_matrix`;
- output только `test-design-matrix.md`, self-check матрицы и `prompt.matrix-to-reviewer.md`;
- явный запрет создавать или обновлять `fts/**/test-cases/*.md` до отдельного `matrix-accepted` review.

Не добавляй в practical prompt `scope-contract.md`, отдельный `scope-coverage-gaps.md`, oracle inventories, `scope-gap-review.md`, package gates или legacy writer outputs. Они не являются входами compact route и создают ложный blocking contract.

Для legacy/session route используй его полный контракт из `next-step-prompt-format.md`; не смешивай его с practical handoff.

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
- при `agent-proposed-scope`: только options/prompts и `awaiting-user-scope-selection`;
- `scope-contract.md` с подтвержденными границами анализа — только legacy/session route;
- `source-parity-check.md`, если для основного ФТ доступны DOCX и PDF;
- `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий;
- `mockup-visual-inventory.md`, если подтвержденный UI scope включает mockup / screen image / `mockups/` или агент визуально открыл относящийся Figma-узел;
- `scope-coverage-gaps.md` с неоднозначностями и отсутствующими данными — только legacy/session route;
- для practical scope: `scope-brief.md`, обязательные source-parity/row/mockup artifacts и `scope-clarification-requests.md` только при вопросе к БА;
- один активный handoff к matrix-only writer, если scope готов к следующей стадии;
- при необходимости результаты `resolve_sections()` или `preview_chunks()`.

## Workflow

Для полного, eval или diagnostic route перед завершением стадии создай или обнови `scope-analyzer-session-log.md` по `session-log-format.md`: зафиксируй inputs read, inputs not used, key decisions, risks/fallbacks, validation и contamination check. Для clean eval/diagnostic run добавь audit-секции `Event Timeline`, `Quality Checkpoints`, `Artifact Write Strategy`, `Technical Fallbacks`, `Handoff Notes For Next Session`. Chunked writer включай только по size/count thresholds из `lean-production-workflow.md`, а не из-за самого наличия `WP-*` или row inventory. Если был лимит команды, failed patch, chunked writing, helper script, temp content file или encoding fallback, заполни `Technical Fallbacks` строкой `TF-*`. Свяжи лог из `workflow-state.yaml` через `latest_artifacts.session_log` или `latest_artifacts.scope_analyzer_session_log`.
Для полного/eval/diagnostic route параллельно веди `agent-decision-log.md` по `agent-decision-log-format.md`. Успешный `lean-production` run не создает оба лога: typed receipts, workflow state и общий performance record являются audit trail; при failure создай один `failure-diagnostic.json`.
Для русскоязычных источников перед PowerShell-командами выставляй UTF-8 preamble из `session-log-format.md`; если вывод консоли искажает кириллицу, перечитай источник через явный UTF-8 file/script path, не используй mojibake stdout как evidence и зафиксируй это в `Technical Fallbacks`.

1. Перед `resolve_sections()` или любым scope narrowing разреши канонический `source-selection.md`: сначала прочитай `work/stage-handoffs/00-scope-selection/workflow-state.yaml` и его `latest_artifacts.source_selection`, затем используй fallback `work/stage-handoffs/00-scope-selection/source-selection.md`. Если валидный selection найден, переиспользуй его и не объявляй его отсутствующим, не запускай `ft-source-locator` и не создавай замену. Если оба пути не разрешаются, останови workflow как `blocked-input` и создай только transition к `ft-source-locator`. При возобновлении после смены code gate перечитай этот skill и practical route, затем запиши `instruction_context.loaded_skill` и совпадающий commit. После разрешения selection: если `xhtml_available != yes`, зафиксируй отсутствие обязательного `main-ft-xhtml` и не создавай `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.
1a. Используй `test_case_agent.resolve_sections()` для первичного сужения области.
1b. Используй XHTML в первую очередь для машинного извлечения текста, таблиц, строк, списков, вложенных списков, перечней значений, `source-row-inventory.md` и `dictionary-source` rows.
1c. Используй DOCX как authoritative source for meaning: если XHTML и DOCX расходятся, фиксируй discrepancy / `coverage gap`, а не выбирай по догадке.
2. Если для FT-пакета есть `AGENT-NOTES.md`, учти его как обязательный package-specific context.
3. Если PDF-версия основного ФТ доступна, используй ее для сверки структуры разделов, заголовков и границ выбранного scope; PDF не заменяет DOCX или XHTML.
4. Примени `scope-decomposition-policy.md`: если пользователь просит большое ФТ, весь документ или несколько разнородных разделов, сначала создай карту внешних candidate scope-ов по разделам/подразделам ФТ в режиме `agent-proposed-scope`.
5. При `agent-proposed-scope` сохрани options/prompts в `00-<container-slug>/`; установи `awaiting-user-scope-selection`, `next_skill: ft-scope-analyzer` и пустой `blocking_reasons`. В `scope-options.md` добавь компактное `Распределение требований ФТ` строго по канонической таблице: каждый формальный код требования назначен одному владельцу проектирования тестов, перечислены все затронутые `scope_slug`, а `cross-scope` или `out-of-scope` имеют обоснование. До выбора не создавай writer/scope-local/BA artifacts или `scope-contract.md`; scope-зависимую неизвестность укажи только как риск option. Исключение — source contradiction, исключающее безопасное разбиение.
5a. Все source/scope handoff artifacts сохраняй только в numbered-папке `fts/<ft-slug>/work/stage-handoffs/NN-<scope-or-container-slug>/`. Не создавай `source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml` или session logs в корне FT-пакета. Видимые заголовки и проза handoff-ов — на русском; английский допустим только в IDs, путях и metadata enums.

5b. Не удаляй артефакты завершенного `ft-source-locator` из контейнера выбора: `source-selection.md`, `source-locator-session-log.md` и `agent-decision-log.md` остаются audit trail, если на них есть ссылка. Для practical scope запрет на session/decision logs означает «не создавать новый scope-local лог», а не «удалить receipt предыдущей стадии».
6. Если пользователь уже выбрал конкретный внешний scope, зафиксируй режим `manual-scope`.
7. Если раздел большой, используй `preview_chunks()` и выдели только нужные фрагменты внутри выбранного внешнего scope.
8. Зафиксируй, какие требования входят в scope, а какие не входят.
9. Если для основного ФТ доступны DOCX и PDF, создай `source-parity-check.md` по `source-parity-check-format.md`: сверяй коды требований, таблицы, строки, примечания и границы только выбранного scope.
   Если подтвержденный UI scope содержит mockup / screen image / `mockups/`, открой изображение визуально и создай `mockup-visual-inventory.md` по `mockup-visual-inventory-format.md` до handoff к writer. Инвентарь должен фиксировать видимые блоки, поля, действия, interaction hints, mockup-only элементы, конфликты с ФТ и решение `not_used_as_requirement_source = yes`. Если макет нельзя открыть или проверить визуально, переведи workflow в `blocked-input`, а не передавай writer-у задачу с догадками по UI-шагам. Если source-selection регистрирует Figma-узел, относящийся к scope, внеси его index в `required_inputs`, brief и prompt; доступный узел — в inventory, недоступный `optional_visual_reference` — как limitation в brief.
9a. Если `source-parity-check.md` содержит секцию `Table / Row Parity` или подтвержденный scope основан на таблице полей/действий, создай отдельный `source-row-inventory.md` по `source-row-inventory-format.md` до handoff к writer. В inventory должны попасть все source rows выбранного scope, включая `in_scope = no`, применимые document-global/ancestor/cross-referenced constraints, rows/list values из XHTML, строки с PDF-only requirement codes и строки, которые могут стать `GAP-*`. Для compiler v3 заполни exact `source_path`, `source_locator`, `bounded_source_text`, `source_context_class` и `requirement_codes`; downstream manifest обязан совпасть с этим registry полностью. Не передавай writer-у табличный scope только с `source-parity-check.md`: writer должен получить независимый row inventory.
9b. Для табличного scope проверь расшифровку колонок, сокращений и локальных кодов; неподтвержденное значение, влияющее на test design, фиксируй как `GAP-*` типа `missing-source-definition`, а не как догадку.
9c. Для каждого поля из таблицы перенеси в `source-row-inventory.md` все применимые document-global ограничения его типа: например, длину текста, формат/диапазон/календарную корректность даты, границы числового значения и timezone-поведение. Каждое независимое ограничение получит собственную source row и отдельный `ATOM-*` либо `SO-NEG-*`; не заменяй их фразой «и т. п.».
9d. Если ФТ/AS задаёт автозаполнение нескольких полей, в `scope-brief.md` назови все целевые поля дословно и создай отдельный `ATOM-*` на каждое поле, даже при общем триггере. Не используй «базовые», «перечисленные» или «все» атрибуты без точного списка. Для одного поля разделяй автозаполнение и ручной ввод; независимые UI-контролы с одним результатом (например, `Отмена` и закрытие окна) также получают разные `ATOM-*`. Объединять допустимо только значения одного фиксированного перечня одного поля, если действие и ожидаемый результат совпадают.
10. Перед handoff к writer выполни `Scope Complexity Assessment`: оцени количество полей/блоков, условных зависимостей, validation domains, action flows, integrations/API/async, lifecycle/status rules и ожидаемых gaps.
10a. Для legacy/session route при validation/format/date/email/length/numeric/allowed-values ограничениях или обязательности создай `negative-oracle-inventory.md` / `requiredness-oracle-inventory.md`. В `practical_v0_8` таблица `Кандидаты отрицательных проверок` содержит `Связанный ATOM`: один `SO-NEG-*` на одно поле/ATOM.
10b. Если source задает restriction/requiredness, но exact UI oracle отсутствует, не теряй obligation: укажи `decision = candidate_tc_required`, `oracle_status = ui-calibration-required`, stable `scope_obligation_id` (`SO-NEG-*` / `SO-REQ-*`) и передай writer-у как candidate TC по `negative-ui-calibration-policy.md`. Parent `GAP-*` используй только для общего неизвестного oracle, но child obligations перечисляй отдельно. `gap_required` оставляй для случаев, когда нельзя сформировать даже candidate TC.
10c. Если scope содержит буквальный UI-текст/сообщение или неоднозначное преобразование единиц, создай `source-to-package-fidelity.json` по canonical format и зарегистрируй его в `latest_artifacts`. Каждый `FID-*` укажи в одной inventory-строке с тем же `ATOM-*`, что в JSON binding. Не преобразуй `МБ` в точные байты без source-backed policy; неизвестную точную boundary fixture сохрани как отдельный `GAP-*` obligation.
10d. `source-assertions.json` допустим только для явно выбранного production/promotion route по его canonical format; никогда не создавай его в `practical_v0_8`.
11. В legacy/session route используй `scope-contract.md` и `WP-*` по canonical format; в `practical_v0_8` достаточно `scope-brief.md` без package gates.
13. Если PDF для structural cross-check отсутствует, явно укажи это в промежуточных заметках или `coverage gaps`, а не оставляй неявным.
14. Отдельно перечисли отсутствующие данные и неоднозначности как `coverage gaps`; для каждого gap укажи точное утверждение ФТ, к которому он относится: раздел, GSR/код, таблицу/строку, поле/условие, цитату или `ATOM-*`, если атом уже создан.
14a. В practical route ставь `blocking: yes` только когда gap не позволяет построить даже статусный candidate TC для затронутого `ATOM-*` или есть source contradiction. Частичный вопрос об обязательности, редактируемости или UI oracle не блокирует остальные проверки: он остаётся в `scope-clarification-requests.md`, а затронутый `ATOM-*` получает корректный статус (`candidate-ui-calibration`, `needs-test-data` или `blocked-observability`).
14a.1. Ссылка ФТ на будущий или внешний документ сама по себе не является вопросом к БА: зафиксируй соответствующую проверку как out-of-scope, пока этот документ не предоставлен. Вопрос допустим только если для уже входящего в scope утверждения не хватает конкретного продуктового правила.
14a.2. Если source подтверждает действие, но не задаёт детальный UI-признак результата, не проси БА проектировать интерфейс. Сформируй узкий `candidate-ui-calibration` TC с явно ограниченным source-backed ожиданием; вопрос к БА нужен только при реальной неоднозначности бизнес-правила.
14a.3. Перед handoff отнеси каждую неизвестность ровно к одному типу: `ba-business-ambiguity`, `ui-calibration`, `external-scope-boundary` или `test-data-setup`. Вопрос `CLR-*` создавай только для первого типа и укажи в нём `request_kind: ba-business-ambiguity`. Будущий/внешний ФТ оставь вне границ текущего scope; экран, UI-индикатор и сообщение оставь кандидатом UI-калибровки; роль, объект, статус и fixture — зависимостью от тестовых данных.
14b. До `CLR-*` проверь DOCX/XHTML/PDF/support. Спрашивай БА только о
неразрешенном продуктовом правиле; account/object/fixture и роль с заданными
source правами — `needs-test-data`, не вопрос к БА. В предпосылках укажи для
каждого атома исполнителя, состояние, `SETUP-*`, статус и `FX-*`, шаги ФТ с
`поле=значение` или отсутствующую предпосылку. Повторяй общий `SETUP-*` только
у атомов с одинаковыми исполнителем, объектом и исходным состоянием; не
распространяй полный перечень ролей на проверки только администратора. Таблица
отображения / действий и «создать или выбрать» не доказывают подготовку.
Если действие одного исполнителя только создаёт состояние для проверки другой
роли, вынеси его в `SETUP-*`: формула «администратор, затем пользователь» не
является одним исполнителем атомарной проверки. Перед rematerialization сам
сравни source/support inputs, границы scope, source rows, словарь и `GAP-*` с
активным handoff. Если они не изменились, а задача затрагивает только
версию/маршрутизацию/summary/validator, используй `metadata-only`: не меняй
содержательные brief, matrix, dictionary и self-check. Иначе используй
`bounded-content`. Сначала собери все scope-local findings validator и внеси
их одним patch.
Широкий gap по нескольким
obligations/полям/validation classes разложи на отдельные `CLR-*` или
нумерованный checklist. Не задавай БА umbrella-вопрос; при intake закрывай
только подтверждённые подпункты, остаток оставляй residual gap.
14c. Если одно действие навигации называет два разных пункта меню, кнопки или назначения, создай отдельный `ATOM-*` для каждого назначения. Параметризованная строка допустима только когда явно записано одинаковое стартовое состояние, пользовательское действие и наблюдаемый результат для каждого значения.
14c.1. До handoff к matrix writer раздели `ATOM-*` по разным объектам/UI-уровням и по комбинациям роли или состояния с разными действием либо ожидаемым результатом. Каждая строка `Планируемые проверки` содержит ровно один `ATOM-*` и один `Основной ожидаемый результат`; каждая строка `Предпосылки исполнения` содержит одного исполнителя. Объединение значений или ролей допустимо только при секции `Обоснование параметризации ATOM` в `scope-brief.md`: для каждого `ATOM-*` она доказывает одинаковые стартовый экран, UI-уровень, навигацию, действие, триггер и наблюдаемый результат. Для practical route также соблюдай canonical rule о reciprocal `SRC-*` ↔ `ATOM-*` и покрытии всех ролей из `practical-test-case-route-v0.8.md`. Не оставляй решение об этой декомпозиции writer-у.
15. Для новых handoff-папок используй numbered naming из `references/agent/stage-handoff-model.md`: `00-<container-slug>/` для контейнера выбора и `NN-<scope-slug>/` для подтвержденного scope-level handoff. Логический `scope_slug` оставляй без числового префикса.
16. После подтверждения scope сохрани `workflow-state.yaml` и один active downstream prompt. Для `practical_v0_8` за один проход создавай только `scope-brief.md`, обязательные parity/row/mockup artifacts и route к writer; не создавай legacy artifacts с последующим удалением. `scope-contract.md`, logs, full gaps/oracle artifacts и reviewer prompts не создавай. В финальной handoff-папке не оставляй unlinked промежуточные `chunks/`, `tmp/`, `_artifact-write/` и partial-файлы: временные фрагменты держи вне handoff и удаляй до валидации. То же правило применяется к одноразовым scripts/renders/manifests в `work/debug/`: сохраняй их только как явно linked evidence, а перед финализацией удаляй лишь созданные в текущем run временные файлы, не затрагивая pre-existing user artifacts. Для legacy/session/production route сохрани `scope-contract.md`, `scope-coverage-gaps.md` и условно добавь остальные artifacts. `scope-execution-options.md` создавай только для неоднозначного выбора.
16a. Для `practical_v0_8` отсутствие `scope-contract.md` не отменяет обязательные source checks: если DOCX+PDF доступны, `scope-brief.md` обязан ссылаться на актуальный `source-parity-check.md`; если scope табличный/строковый, `scope-brief.md` обязан ссылаться на актуальный `source-row-inventory.md`. Если любой обязательный artifact отсутствует или не открывается, остановись с `blocked-input` и не создавай writer prompt.
17. В legacy/session route `workflow-state.yaml` задает один active downstream по его canonical contract. `practical_v0_8` всегда идет к writer, не в `source_assertion_review`.
18. Передай выбранный scope дальше в `ft-test-case-writer`, `ft-test-case-reviewer` или `ft-test-case-iteration` вместе с информацией о XHTML extraction notes, source parity, PDF cross-check, package-specific notes, scope complexity assessment и обязательными внутренними рабочими пакетами.
19. Перед финальным сообщением перечитай созданный `workflow-state.yaml`, `practical-stage-summary.md`, `## Действия текущего этапа` и существующие receipt. Отрази только подтвержденные ими фактические `current_stage`, `stage_status`, `next_skill`, blocker-ы и active prompt. Не заявляй о commit/push/reviewer session/dispatch/review artifact, если он не существует в этих evidence текущего этапа; отсутствие обозначай `not-created`. Не сообщай о legacy review или следующем этапе, которого нет в этих артефактах.

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
