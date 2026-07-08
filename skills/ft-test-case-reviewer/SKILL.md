---
name: ft-test-case-reviewer
description: Делает review существующих тест-кейсов по подтвержденному FT-пакету и scope. Работает как umbrella-skill с режимами `full`, `traceability`, `structure`, `test-design`, возвращает structured findings artifact и при необходимости отдельную traceability matrix.
---

# FT Test Case Reviewer

Используй этот skill для review уже существующих тест-кейсов. Skill не пишет и не исправляет тест-кейсы сам: он только анализирует набор и возвращает findings.

## Когда использовать

- нужно проверить готовый набор тест-кейсов;
- нужно сверить кейсы с FT-пакетом и выбранным scope;
- нужно найти пробелы покрытия по утверждениям ФТ;
- нужно проверить единый формат и организацию набора;
- нужно проверить качество test design;
- нужно подготовить замечания для writer workflow.

## Reviewer roles и режимы review

Минимальный полезный split reviewer-а состоит из двух независимых ролей:

- `traceability reviewer` — отвечает только за полноту и стабильность трассировки: ФТ/code/source -> `ATOM-*` / traceability matrix -> `TC-*` или `GAP-*` / `unclear`.
- `test-design/TC-quality reviewer` — отвечает за смысловую достаточность test-design и качество самих `TC-*`: атомарность, исполнимость, наблюдаемость expected results, матрицы покрытия, gaps и приоритеты.

Эти роли могут выполняться одним skill-ом, но reviewer обязан мыслить их как разные passes. Test-design не доказывает traceability, а traceability не доказывает покрытие риска.

## Режимы review

- `full` — канонический режим по умолчанию для direct review. Выполняет `traceability`, затем `structure`, затем `test-design`; возвращает findings и traceability matrix при необходимости. Direct `full` не заменяет session-based sign-off: для `signed-off` используй `ft-test-case-iteration`.
- `traceability` — строит traceability matrix по атомарным утверждениям ФТ и проверяет, что каждое утверждение покрыто тест-кейсом или зафиксировано как `gap` / `unclear`.
- `structure` — проверяет формат тест-кейса, группировку набора, сквозную нумерацию `TC-*`, порядок позитивных и негативных кейсов, наличие базовых проверок по полю, если такие свойства явно описаны в ФТ.
- `test-design` — проверяет полноту позитивных и негативных сценариев, граничные значения, классы эквивалентности, зависимости и комбинации условий, а также неподтвержденные expected results в пределах подтвержденного scope; severity назначается по `test-design-review-rubric.md`.

## Session-based reviewer modes

Для нового Codex SDK process split reviewer запускается отдельными сессиями, но физически остается этим umbrella-skill:

- `scope_gap_review` - pre-writer review of `scope-coverage-gaps.md`, `scope-clarification-requests.md`, source anchors and handoff routing. This mode does not review or edit test cases because the canonical TC file may not exist yet.
- `structure_preflight` — только parseability, handoff completeness, обязательные секции и blockers, которые мешают semantic review; не выполняет polishing.
- `semantic_traceability_test_design` — объединяет traceability и test-design review, строит или обновляет reviewer traceability matrix и возвращает semantic findings.
- `structure_format_final` — финальная проверка оформления после semantic closure: шаблон, группировка, сквозная нумерация, wording, format smells и обязательный validator gate по текущему scope.
- `semantic_regression` — финальная проверка, что format-only revision не изменила смысл, coverage, `ATOM-*` links, traceability matrix и expected results.

Порядок нового session-based cycle: optional `scope_gap_review` after scope analysis and before writer, then `structure_preflight -> semantic_traceability_test_design` до двух semantic rounds, затем `structure_format_final`, optional format-only writer revision и `semantic_regression`. Если final format review находит semantic problem, это не format finding: routing возвращается в semantic loop или фиксирует `round-cap-reached` при исчерпанном лимите.

### `scope_gap_review` contract

Use `scope_gap_review` only after `ft-scope-analyzer` has produced a confirmed scope and at least one `GAP-*` in `scope-coverage-gaps.md`. The active prompt is `prompt.scope-gaps-to-reviewer.md`.

Required inputs:

- `source-selection.md`
- `scope-contract.md`
- `scope-coverage-gaps.md`
- `scope-clarification-requests.md`
- `source-parity-check.md`, when DOCX+PDF are available
- `source-row-inventory.md`, when row-level/table parity is required
- `mockup-visual-inventory.md`, when the scope uses mockups
- package `AGENT-NOTES.md`, when present
- `workflow-state.yaml`

Review only gap quality and routing readiness:

- every `GAP-*` has a concrete FT/source anchor: section, requirement code, table/row, field/condition, quote or atomic statement;
- each gap has a clear impact, blocking classification and downstream handling rule;
- each gap with an unresolved decision has a matching analyst-facing item in `scope-clarification-requests.md`;
- no source-backed requirement was converted into a gap just because writing it is inconvenient;
- unknown negative/requiredness UI mechanisms are listed as child inventory obligations, not hidden only in parent `GAP-*`;
- source extraction relied on XHTML when `source-selection.md` requires it;
- table/list rows present in XHTML were not lost before ledger/TC coverage;
- no mockup-only detail, internal effect or unsupported expected result is promoted to covered behavior;
- source parity, row inventory and mockup inventory limitations are carried into gaps or blocking reasons;
- routing after review is either writer-ready or back to `ft-scope-analyzer`; do not route to UI prep or sign-off from this mode.

Expected outputs:

- `scope-gap-review.md` with verdict `passed | needs-scope-revision | blocked-input`;
- reviewer session log and decision log in the current stage-handoff folder;
- if passed: `workflow-state.yaml` routes to writer with `stage_status: ready-for-next-stage`, `next_skill: ft-test-case-writer`, and active prompt `prompt.scope-to-writer.md`;
- if not passed: `workflow-state.yaml` routes back to `ft-scope-analyzer` or `blocked-input` with explicit findings and blocking reasons.

## Входы

- существующий набор тест-кейсов;
- split test-design artifacts из `work/test-design/<section-id>-<scope-slug>/`, если они есть;
- релевантный FT-пакет;
- подтвержденный scope;
- `source-selection.md` с `xhtml_available: yes`;
- XHTML-версия основного ФТ как обязательный extraction source для таблиц, строк, списков, вложенных списков и перечней значений;
- PDF-версия основного ФТ для сверки структуры, если она есть;
- `source-parity-check.md`, если для основного ФТ доступны DOCX и PDF;
- `dictionary-inventory.md`, если source/support или split artifacts содержат `dictionary-source` / reference-list rows;
- `mockup-visual-inventory.md`, если подтвержденный UI scope содержит mockup / screen image / `mockups/`;
- `review_mode = full | traceability | structure | test-design`;
- при необходимости связанные материалы FT-пакета для уточнения трассировки;
- при second review:
  - structured findings artifact предыдущего раунда;
  - writer response artifact;
  - при наличии traceability matrix предыдущего раунда.

## Выходы

- findings по severity в порядке `error -> warning -> info`;
- structured findings artifact;
- human summary;
- при `traceability` и `full`:
  - отдельный traceability matrix artifact;
  - обязательный `.xlsx`-дубль traceability matrix artifact с теми же строками и колонками;
- при необходимости:
  - карта coverage gaps;
  - список неоднозначностей и противоречий по ФТ;
  - `prompt.reviewer-to-writer.round-N.md`, если findings требуют writer revision;
  - `prompt.reviewer-to-ui-prep.md`, если reviewer подписал набор и следующий этап `ft-ui-automation-prep`.
- расположение и обязательные поля reviewer outputs определяются `reviewer-output-format.md`.

## Workflow

Перед завершением review round создай или обнови `reviewer-session-log.round-N.md` по `session-log-format.md`: зафиксируй inputs read, inputs not used, key decisions, risks/fallbacks, validation и contamination check. Для clean eval/diagnostic run добавь audit-секции `Event Timeline`, `Quality Checkpoints`, `Technical Fallbacks`, `Handoff Notes For Next Session`; в них отдельно фиксируй reviewer passes, rejected sign-off reasons, semantic checks beyond validator, technical fallbacks и recommended writer focus. Если был лимит команды, failed patch, chunked writing, helper script, temp content file или encoding fallback, обязательно заполни `Technical Fallbacks` структурированной строкой `TF-*`; не пиши `none`. Свяжи лог из `workflow-state.yaml` через `latest_artifacts.session_log` или `latest_artifacts.reviewer_round_N_session_log`.
Параллельно веди `agent-decision-log.md` или `agent-decision-log.round-N.md` по `agent-decision-log-format.md`: фиксируй review focus decisions, accepted/rejected sign-off reasons, finding severity decisions, residual-risk decisions и routing к writer/iteration/UI prep; свяжи его через `latest_artifacts.decision_log`.
Для русскоязычных источников перед PowerShell-командами выставляй UTF-8 preamble из `session-log-format.md`; если вывод консоли искажает кириллицу, перечитай источник через явный UTF-8 file/script path, не используй mojibake stdout как evidence и зафиксируй это в `Technical Fallbacks`.

1. Найди файл тест-кейсов и соответствующий FT-пакет с нужным scope.
2. Подтверди, что review выполняется только в пределах уже выбранного scope.
3. Определи `review_mode`. Если режим не указан явно, используй `full`.
4. Перед review проверь `source-selection.md`: если для нового workflow `xhtml_available != yes`, зафиксируй blocking finding и не подписывай набор.
5. Проверь, что writer использовал XHTML для таблиц, строк, списков, вложенных списков, перечней значений, source rows и dictionary-source rows. Потеря строк/списков, которые присутствуют в XHTML, является traceability/test-design finding.
6. Если PDF-версия основного ФТ доступна, используй ее для сверки структуры разделов, заголовков и границ scope до начала review.
7. Если для основного ФТ доступны DOCX и PDF, прочитай `source-parity-check.md`. Если artifact отсутствует, зафиксируй blocking traceability finding и не подписывай набор.
5a. Если подтвержденный UI scope содержит mockup / screen image / `mockups/`, прочитай `mockup-visual-inventory.md`. Если inventory отсутствует, не открыт (`opened != yes`) или не содержит guard `not_used_as_requirement_source = yes`, создай blocking finding. В `structure`/`test-design` pass проверь, что writer использовал mockup для конкретизации UI-шагов, но не вывел из него бизнес-правила, обязательность, validation, allowed values или expected results. Mockup-only элементы без подтверждения ФТ должны быть `GAP-*` / conflict, а не `covered`.
5b. Если source/support или `source-table-normalization.md` содержит `dictionary-source`, reference-list, tags или фиксированный перечень значений, прочитай `dictionary-inventory.md`. Если inventory отсутствует, неполный, не содержит `DICT-*` для referenced dictionary/list или plan/TC используют только примерные значения вместо inventory, создай finding по `dictionary-closed-set-missing`.
6. В режиме `traceability` или `full` декомпозируй требования выбранного scope на атомарные утверждения.
7. Построй traceability matrix по каноническому формату из `traceability-matrix-format.md`; каждая строка должна иметь стабильный `atom_id`, который используется как `traceability_ref` в findings. Все mandatory requirement IDs из `source-parity-check.md`, включая PDF-only коды, должны присутствовать в `req_id`.
8. Создай рядом с Markdown matrix обязательный `.xlsx`-дубль по правилам `traceability-matrix-format.md`; строки, колонки и значения должны совпадать с Markdown matrix.
9. Для каждой строки матрицы проставь `coverage_status = covered | gap | unclear`.
10. Если утверждение не покрыто кейсами, но не может быть однозначно интерпретировано по ФТ, фиксируй `unclear`, а не придумывай поведение.
11. Выполни traceability diff против разрешенного baseline/revalidation context, если он есть в scope contract, handoff, review-cycle snapshots, eval run report или пользовательском prompt-е:
    - atom/code, ранее зафиксированный как `gap` / `unclear`, не должен внезапно стать `covered` без нового наблюдаемого artifact или утвержденного source;
    - буквенно-цифровые коды требований (`GSR`, `REQ`, `ID` и локальные коды ФТ) не должны исчезать из ledger/matrix/TC links;
    - `GAP-*` не должен менять смысл, affected atoms или blocking status без явного writer response;
    - lessons из revalidation findings должны переноситься как regression checks.
12. Если writer передал atomic requirements ledger или writer self-check, проверь, что ledger согласован с traceability matrix и source parity, а self-check не скрывает uncovered atoms, merged checks, over-splitting, package coverage, cross-package leakage, assumptions или unclear items.
13. В режиме `structure` или `full` проверь единый шаблон, обязательные секции, группировку, сквозную нумерацию `TC-*`, порядок кейсов, детерминированность шагов и отсутствие проверяемого действия в предусловиях. Смешанная схема одного `TC-*` является structure blocker: metadata table нельзя дублировать bold metadata fields, а runtime headings нельзя дублировать inline/bold-полями.
14. В режиме `test-design` или `full` проверь позитивные и негативные сценарии, границы, классы эквивалентности, условные зависимости и взаимное влияние полей, если они описаны в требованиях. Применяй `test-design-review-rubric.md`: reviewer должен пытаться опровергнуть coverage claim writer-а, а не подтверждать его по умолчанию.
    - Применяй эвристики `coverage-checklist.md`: переходы состояния, зависимости между элементами, около-граничные значения, расчетные классы, повторяющиеся блоки и восстановление после ошибки. Не требуй baseline-кейс, если ожидаемая реакция не следует из ФТ или разрешенного уточнения; фиксируй `coverage gap` / `unclear`.
    - Проверяй избыточную атомаризацию: несколько кейсов, которые отличаются только одним значением одного и того же списка/справочника и выполняют одну и ту же проверку, должны быть объединены в один кейс на состав списка, если значения не запускают отдельную бизнес-логику.
    - Если ФТ задает закрытый перечень значений, проверяй, что тест-кейс покрывает и наличие ожидаемых значений, и отсутствие лишних значений. Если закрытость перечня не следует из ФТ, не требуй такую проверку и фиксируй неоднозначность только при необходимости.
    - Для правил вида `допустимы только ...` проверяй, что набор не ограничился одним общим кейсом `недопустимые символы`, а содержит отдельные атомарные негативные `equivalence`-проверки по различимым классам невалидного ввода, если такие классы следуют из текста ФТ без домысливания.
    - Для `ui-calibration-required` / `candidate-ui-calibration` не требуй точный UI-oracle; требуй calibration note, `scope_obligation_id` traceability и отсутствие выдуманной UI-реакции.
    - Для условной видимости проверяй позитивную и негативную ветку по `coverage-checklist.md` и `traceability-rules.md`, если обратная ветка явно следует из ФТ.
    - Для `numeric-format`, `exact-length`, action-created blocks, repeatable blocks, checkbox-list и generated documents проверь наличие соответствующих obligation rows, plan rows, metrics и `TC-*`/`GAP-*`; один общий positive/negative case не доказывает эти classes.
    - Если negative transition или submit-blocking TC ссылается на generic valid baseline, проверь `fixture-catalog.md` или полное раскрытие baseline в TC.
    - Если применимы high-risk atoms или combinatorial coverage, проверь `risk-priority-map.md` с `impact x likelihood` и `coverage-metrics.md` с выбранной `2-way | 3-way | t-way` strength.
    - Проверь обязательный package-by-package workflow для каждого scope: `scope-contract.md` должен содержать минимум один internal work package, split artifact `internal-work-package-coverage.md` должен содержать `Internal Work Package Coverage`, каждый `ATOM-*` и каждый `TC-*` должен иметь `package_id`.
    - Если source является таблицей полей/действий или PDF/DOCX/XHTML extraction, сначала проверь split artifacts `source-row-inventory.md`, `source-row-completeness-matrix.md`, `source-table-normalization.md`, `dictionary-inventory.md` при наличии справочников и `test-design-decision-table.md`: каждая source row внутри подтвержденного scope должна присутствовать и быть связана с `ATOM-*`, `GAP-*` или out-of-scope решением; строки normalization должны иметь `source_property_id`, быть очищены от table-header residue, соседних полей и extraction-мусора, не объединять несколько independently checkable `GSR`/`REQ` и не смешивать разные semantic property classes в одной строке. `dictionary-source`, `min-boundary`, `max-boundary`, `format`, `visibility`, `requiredness`, `editability`, `integration-prefill` должны быть отдельными normalization rows; `dictionary-source` rows должны ссылаться на `DICT-*` или узкий `GAP-*`; `confidence = low | unclear` требует `GAP-*` и не может быть `covered`; каждая `source_property_id` должна иметь ровно одно решение в `Test Design Decision Table`.
    - Проверь `gap-admissibility`: `gap_unclear` и `metadata_only` не должны скрывать source-backed observable behavior. Если в source/PDF/support указаны подсказка, сообщение, красная подсветка, подтверждение, переход, маска, справочник/теги, date-window boundary, отображаемое сохраненное/несохраненное значение после повторного открытия объекта/раздела или другой pass/fail oracle, reviewer должен требовать `TC-*`/obligation coverage для этой части и узкий `GAP-*` только для реально заблокированной части.
    - Перед проверкой отдельных `TC-*` проверь split artifact `package-test-design-plan.md`: каждый `WP-*` и применимый `ATOM-*` должен иметь planned check или `GAP-*`, validation rules должны быть разложены на positive/negative/equivalence/boundary classes, action/dependency rules — на branches.
    - Проверь, что writer обработал scope package-by-package, не смешал независимые проверки из разных packages в одном `TC-*`, не пометил package покрытым без применения указанного `design_method`, и зафиксировал package ledger gate / package design-plan gate / package TC gate.
    - Ставь `error`, если ledger содержит generic atoms вроде `Требование GSR N выполняется`, `см. GSR/source row`, “поведение соответствует ФТ” без проверяемого expected behavior, или если TC использует generic steps вместо исполнимых действий. Generic steps включают `Подготовить ветку`, `Сравнить состояние поля с ожидаемым правилом ФТ`, `Проверить соответствие ФТ`, `Проверить поле согласно ФТ`, `Выполнить проверку значения`.
    - Ставь `error`, если `Type: Positive` используется для rejection/invalid/no-save oracle, requiredness проверяется заполнением поля вместо visible marker или empty-value validation, либо expected result только пересказывает ФТ без observable oracle.
    - Ставь `error`, если expected result содержит source-dump oracle вида `наблюдается правило из GSR ...`, сырую строку normalization/source quote вместо наблюдаемого результата, или DOCX/PDF extraction-мусор (`Д а`, `П о`, разорванные слова, table-header residue).
    - Ставь `error`, если source fields дублируют друг друга без новой evidence, `DICT-*` используется в body TC, но отсутствует в `Трассировка`, synthetic statement выдан за source quote, action-created block имеет `Постусловия: Не требуются` без cleanup/закрытия без сохранения, branch choices имеют одинаковый oracle без source-backed rationale или negative input TC объединяет несколько invalid classes под generic oracle.
    - Ставь `error`, если исполнимый TC использует unresolved generic fixture/test data вроде `Минимальный валидный набор данных`, `валидные данные`, `валидная заявка`, `значение из тестовых данных`, но не раскрывает конкретный baseline, literal/параметр или linked fixture artifact.
    - Ставь `error`, если expected result использует oracle `значение из тестовых данных принято/не принимается`, а test data не содержат конкретное проверяемое значение.
    - Ставь `error`, если `тип значения: Строка/Дата/Логическое` закрыт standalone TC как generic metadata behavior, например `поле принимает и отображает введенное строковое значение`, вместо конкретного source-backed input/widget/format behavior или `GAP-*`.
    - Ставь `error`, если строка `Test-design Applicability Matrix` засчитывает metadata-only/source-property atoms как покрытие dimension, например links для `table-list` включают atoms про источник значения, technical type или table extraction residue, не проверяемые этой dimension.
    - Ставь `error`, если ledger выглядит как compact draft: один `ATOM-*` с диапазоном `GSR`/`REQ` закрывает несколько независимых свойств поведения, особенно после сообщения writer-а о лимите команды, patch или контекста.
    - Ставь `error`, если `Package Test Design Plan` содержит generic planned checks вроде `проверить требование`, `валидное/невалидное значение`, `установить условие`, или если TC не соответствует строкам plan.
    - Ставь `error`, если `Package Test Design Plan` использует slash-combinations вроде `positive/negative`, `boundary/format`, `integration/gap` вместо отдельных строк плана.
    - Ставь `error`, если один `TC-*` закрывает чрезмерное количество независимых `ATOM-*` без явного scenario/use-case rationale.
    - Ставь `error`, если writer-side artifacts используют неканонические status aliases: `pass-with-gap`, `pass-with-gaps`, `planned` как итоговый coverage status, `ok`, `yes`, `passed`, `failed` или локальные варианты вместо enum-ов из format references.
    - Проверяй hallucinated assumptions, unsupported expected-result specificity и размытые expected results по `test-case-format.md`: точные значения, разделители, статусы, тексты ошибок, порядок нормализации или UI-реакции должны быть подтверждены ФТ или разрешенными материалами; отображаемые значения должны сохранять точное написание из ФТ.
    - Ставь `error`, если expected result не дает наблюдаемого pass/fail, проверяемое действие спрятано в предусловиях, один TC смешивает независимые бизнес-проверки, positive/negative ветки объединены, или TC заявляет покрытие `ATOM-*`, но не проверяет его condition и expected behavior.
    - Ставь `error`, если UI scope имеет mockup, но canonical file не ссылается на `mockup-visual-inventory.md`, использует generic UI steps вместо доступных interaction hints из inventory, или превращает mockup-only элемент в covered requirement без ФТ/source подтверждения.
15. Обязательно прогони defect-class checklist из `test-design-review-rubric.md` и `test-design-defect-taxonomy.md`; не дублируй полный список классов в выводе, но явно фиксируй найденные blocking classes и evidence.
16. Для каждого спорного expected result примени evidence-first question: какой наблюдаемый artifact подтверждает pass/fail? Если artifact не указан для API/DB/RabbitMQ/model/internal state, создай `error` или требуй `GAP-*` / `unclear`.
17. Не требуй проверки, которых нет в ФТ. Например, не отмечай отсутствие проверки видимости, если ФТ не описывает видимость поля.
18. Для каждого finding укажи `review_mode` и `required_change`.
19. Для findings режима `traceability` обязательно ссылайся на строку матрицы через `traceability_ref = ATOM-*` или на `coverage_gap:<short-id>`, если строки matrix еще нет.
20. Для findings режима `structure` привязывай замечание к конкретному `test_case_id` или к месту в наборе.
21. Для findings режима `test-design` указывай, какой тип проверки отсутствует: `positive | negative | boundary | equivalence | dependency`. Если проблема в неподтвержденном expected result, используй категорию `expected-result`.
22. Если PDF для structural cross-check отсутствует, явно укажи это в human summary или findings как ограничение входных данных.
23. Во втором review сверяй не только обновленный набор тест-кейсов, но и writer response artifact. Если writer заявил `fixed`, проверь все affected artifacts: canonical TC, ledger, traceability matrix, Test-design Decision Table, Package Test Design Plan и coverage artifacts; рассинхрон current-scope ссылок `TC-*` / `ATOM-*` / `GAP-*` остается blocking finding.
24. Во втором review не переоткрывай закрытый finding без нового evidence.
25. Если findings artifact предыдущего раунда, writer response artifact или traceability matrix структурно невалидны, фиксируй это как blocking review finding.
26. Во втором review проверяй закрытие traceability findings по `traceability_ref`, а не по похожему тексту `source_path` или повторяющемуся `req_id`.
27. Если найдены unresolved findings, сохрани `prompt.reviewer-to-writer.round-N.md` для следующего writer round.
27a. Если review verdict = `not signed-off`, не записывай `stage_status: not-signed-off` в `workflow-state.yaml`: такого process-status нет. Для обычного следующего writer round используй `stage_status: ready-for-writer-revision` и `next_skill: ft-test-case-writer`; если достигнут round cap, используй `stage_status: round-cap-reached`; если нужен внешний input, используй `stage_status: blocked-input`.
28. Если набор подписан без unresolved findings, перед handoff проверь группировку, сквозную нумерацию `TC-*` и выполни `python scripts\validate_agent_artifacts.py --root <ft-package> --json` или runner validator gate по текущему scope. Final reviewer output должен содержать блок `Reviewer Sign-off Self-check` по `reviewer-output-format.md`; `validator_checked: yes`/`blocking_findings_absent: yes` допустимы только без scope `error`/`warning` либо с валидным `Validator Warning Waivers`. Затем сохрани `prompt.reviewer-to-ui-prep.md` и обнови handoff state.
29. Не выдавай handoff в `ft-ui-automation-prep`, если остаются `error`, `warning` или traceability `gap`, кроме явно допустимых `unclear`; для одиночного reviewer-pass без orchestrator-а не подменяй lifecycle sign-off, если sign-off должен фиксировать `ft-test-case-iteration`.

## Test-design Applicability Matrix Rule

In `test-design` and `full` modes, review the writer's `Test-design applicability matrix` before judging individual `TC-*`.

Rules:

- Use `coverage-checklist.md` as the canonical source for expected high-risk coverage dimensions.
- Verify that every visible FT dimension is represented in the matrix.
- For each `applicable = yes` row, require linked `ATOM-*` and either linked `TC-*` or linked `GAP-*`.
- For each linked `TC-*`, verify semantic coverage: the test steps, data, and final expected result must actually exercise that dimension. A generic positive case or a case for another dimension does not satisfy the matrix row.
- For each `applicable = unclear` row, require linked `GAP-*` and an analyst-facing question.
- If a row is missing, unsupported, silently skipped, or linked to a non-covering `TC-*`, return a finding with `coverage_dimension` from `review-findings-format.md`.
- For `test-design`, `coverage`, `expected-result`, and `scope` findings, never omit `coverage_dimension`.

## Канонические references

- Индекс контрактов инструкций: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Workflow state: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Session log format: [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md)
- Agent decision log format: [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md)
- Формат next-step prompt: [../../references/agent/next-step-prompt-format.md](../../references/agent/next-step-prompt-format.md)
- Формат reviewer output: [../../references/agent/reviewer-output-format.md](../../references/agent/reviewer-output-format.md)
- Формат Package Test Design Plan: [../../references/agent/package-test-design-plan-format.md](../../references/agent/package-test-design-plan-format.md)
- Формат Source Table Normalization: [../../references/agent/source-table-normalization-format.md](../../references/agent/source-table-normalization-format.md)
- Формат Source Row Inventory: [../../references/agent/source-row-inventory-format.md](../../references/agent/source-row-inventory-format.md)
- Формат Dictionary Inventory: [../../references/agent/dictionary-inventory-format.md](../../references/agent/dictionary-inventory-format.md)
- Формат тест-кейса: [../../references/qa/test-case-format.md](../../references/qa/test-case-format.md)
- Test-design review rubric: [../../references/qa/test-design-review-rubric.md](../../references/qa/test-design-review-rubric.md)
- Test-design defect taxonomy: [../../references/agent/test-design-defect-taxonomy.md](../../references/agent/test-design-defect-taxonomy.md)
- Coverage obligation table format: [../../references/agent/coverage-obligation-table-format.md](../../references/agent/coverage-obligation-table-format.md)
- Test-design coverage metrics format: [../../references/agent/test-design-coverage-metrics-format.md](../../references/agent/test-design-coverage-metrics-format.md)
- Fixture catalog format: [../../references/agent/fixture-catalog-format.md](../../references/agent/fixture-catalog-format.md)
- Risk / Priority Map format: [../../references/agent/risk-priority-map-format.md](../../references/agent/risk-priority-map-format.md)
- Формат review findings и writer response: [../../references/qa/review-findings-format.md](../../references/qa/review-findings-format.md)
- Формат traceability matrix: [../../references/qa/traceability-matrix-format.md](../../references/qa/traceability-matrix-format.md)
- Формат source parity check: [../../references/agent/source-parity-check-format.md](../../references/agent/source-parity-check-format.md)
- Формат mockup visual inventory: [../../references/agent/mockup-visual-inventory-format.md](../../references/agent/mockup-visual-inventory-format.md)
- Negative UI calibration policy: [../../references/agent/negative-ui-calibration-policy.md](../../references/agent/negative-ui-calibration-policy.md)
- Legacy traceability matrix report: [../../references/agent/traceability-legacy-matrix-report-2026-05-25.md](../../references/agent/traceability-legacy-matrix-report-2026-05-25.md)
- Strict validator debt report: [../../references/agent/strict-debt-report-2026-05-25.md](../../references/agent/strict-debt-report-2026-05-25.md)
- Reviewer sign-off migration report: [../../references/agent/reviewer-signoff-migration-report-2026-05-25.md](../../references/agent/reviewer-signoff-migration-report-2026-05-25.md)
- Eval run report format: [../../references/agent/eval-run-report-format.md](../../references/agent/eval-run-report-format.md)
- Coverage checklist: [../../references/qa/coverage-checklist.md](../../references/qa/coverage-checklist.md)
- Правила трассировки: [../../references/qa/traceability-rules.md](../../references/qa/traceability-rules.md)
- Границы skill-ов: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)
- Source parsing quality: [../../references/agent/source-parsing-quality.md](../../references/agent/source-parsing-quality.md)

## Ограничения

- Не используй этот skill для написания новых тест-кейсов вместо writer workflow.
- Не меняй FT-пакет и scope по ходу review, если это явно не требуется отдельной задачей.
- Не исправляй тест-кейсы сам. Возвращай remediation как findings artifact, human summary и traceability matrix при необходимости.
- Не расширяй scope на основании найденных пробелов. Out-of-scope замечания фиксируй как findings категории `scope`.
- Не дублируй общие правила из канонических references.
