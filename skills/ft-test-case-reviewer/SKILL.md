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

Use `scope_gap_review` only after `ft-scope-analyzer` produced confirmed scope gaps and `prompt.scope-gaps-to-reviewer.md` is active. Inputs: `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`, `scope-clarification-requests.md`, `workflow-state.yaml`, plus source parity, row inventory, mockup inventory and `AGENT-NOTES.md` when applicable.

Review gap quality and routing only: concrete FT/source anchors, impact/blocking classification, downstream handling, matching clarification questions by `requirements-clarification-questioning-policy.md`, `xhtml_available: yes`, table/list coverage against XHTML and row inventory, no promotion of source-backed behavior to gap for convenience, no mockup-only/internal/unsupported expected result as covered. Weak questions use category `clarification-question-quality`.

Output `scope-gap-review.md` with verdict `passed | needs-scope-revision | blocked-input`, reviewer session/decision logs, and workflow routing either to writer (`ready-for-next-stage`, active `prompt.scope-to-writer.md`) or back to `ft-scope-analyzer` / `blocked-input`.

## Входы

- существующий набор тест-кейсов;
- split test-design artifacts из `work/test-design/<section-id>-<scope-slug>/`, если они есть;
- релевантный FT-пакет;
- подтвержденный scope;
- XHTML-версия основного ФТ как обязательный extraction source для таблиц, списков, вложенных списков и перечней значений;
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

Перед завершением review round создай или обнови `reviewer-session-log.round-N.md` по `session-log-format.md`: зафиксируй inputs read, inputs not used, key decisions, risks/fallbacks, validation и contamination check. Для clean eval/diagnostic run добавь audit-секции `Event Timeline`, `Quality Checkpoints`, `Technical Fallbacks`, `Handoff Notes For Next Session`; если был технический fallback или encoding issue, зафиксируй его как `TF-*`. Свяжи лог из `workflow-state.yaml` через `latest_artifacts.session_log` или `latest_artifacts.reviewer_round_N_session_log`.
Параллельно веди `agent-decision-log.md` или `agent-decision-log.round-N.md` по `agent-decision-log-format.md`: фиксируй review focus decisions, accepted/rejected sign-off reasons, finding severity decisions, residual-risk decisions и routing к writer/iteration/UI prep; свяжи его через `latest_artifacts.decision_log`.
Для русскоязычных источников перед PowerShell-командами выставляй UTF-8 preamble из `session-log-format.md`; если вывод консоли искажает кириллицу, перечитай источник через явный UTF-8 file/script path, не используй mojibake stdout как evidence.

1. Найди файл тест-кейсов и соответствующий FT-пакет с нужным scope.
2. Подтверди, что review выполняется только в пределах уже выбранного scope.
3. Определи `review_mode`. Если режим не указан явно, используй `full`.
4. Перед review проверь `source-selection.md`: если для нового workflow `xhtml_available != yes`, зафиксируй blocking finding и не подписывай набор.
5. Проверь, что writer использовал XHTML для таблиц, списков, вложенных списков, перечней значений, source rows и dictionary-source rows. Если writer ссылается только на DOCX/PDF и пропустил XHTML-only extracted list/table content, это traceability/test-design finding.
6. Если PDF-версия основного ФТ доступна, используй ее для сверки структуры разделов, заголовков и границ scope до начала review.
7. Если для основного ФТ доступны DOCX и PDF, прочитай `source-parity-check.md`. Если artifact отсутствует, зафиксируй blocking traceability finding и не подписывай набор.
7a. Если подтвержденный UI scope содержит mockup / screen image / `mockups/`, прочитай `mockup-visual-inventory.md`. Mockup помогает конкретизировать UI-шаги, но не является источником бизнес-правил, обязательности, validation, allowed values или expected results.
7b. Если source/support или `source-table-normalization.md` содержит `dictionary-source`, reference-list, tags или фиксированный перечень значений, прочитай `dictionary-inventory.md` и используй `DICT-*` в traceability/design checks.
8. В режиме `traceability` или `full` декомпозируй требования выбранного scope на атомарные утверждения.
9. Построй traceability matrix по каноническому формату из `traceability-matrix-format.md`; каждая строка должна иметь стабильный `atom_id`, который используется как `traceability_ref` в findings. Все mandatory requirement IDs из `source-parity-check.md`, включая PDF-only коды, должны присутствовать в `req_id`.
10. Создай рядом с Markdown matrix обязательный `.xlsx`-дубль по правилам `traceability-matrix-format.md`; строки, колонки и значения должны совпадать с Markdown matrix.
11. Для каждой строки матрицы проставь `coverage_status = covered | gap | unclear`.
12. Если утверждение не покрыто кейсами, но не может быть однозначно интерпретировано по ФТ, фиксируй `unclear`, а не придумывай поведение.
13. Выполни traceability diff против разрешенного baseline/revalidation context, если он есть в scope contract, handoff, review-cycle snapshots, eval run report или пользовательском prompt-е:
    - atom/code, ранее зафиксированный как `gap` / `unclear`, не должен внезапно стать `covered` без нового наблюдаемого artifact или утвержденного source;
    - буквенно-цифровые коды требований (`GSR`, `REQ`, `ID` и локальные коды ФТ) не должны исчезать из ledger/matrix/TC links;
    - `GAP-*` не должен менять смысл, affected atoms или blocking status без явного writer response;
    - lessons из revalidation findings должны переноситься как regression checks.
14. Если writer передал atomic requirements ledger или writer self-check, проверь, что ledger согласован с traceability matrix и source parity, а self-check не скрывает uncovered atoms, merged checks, over-splitting, package coverage, cross-package leakage, assumptions или unclear items.
15. В режиме `structure` или `full` проверь единый шаблон, обязательные секции, группировку, сквозную нумерацию `TC-*`, порядок кейсов, детерминированность шагов и отсутствие проверяемого действия в предусловиях. Смешанная схема одного `TC-*` является structure blocker: metadata table нельзя дублировать bold metadata fields, а runtime headings нельзя дублировать inline/bold-полями.
16. В режиме `test-design` или `full` проверь позитивные и негативные сценарии, границы, классы эквивалентности, условные зависимости, взаимное влияние полей, случаи где source fields дублируют друг друга, hallucinated assumptions, unsupported expected-result specificity и package-level design artifacts, если они применимы к scope. Применяй `test-design-review-rubric.md`, `test-design-defect-taxonomy.md`, `coverage-checklist.md`, `test-design-depth-policy.md`, `tc-set-optimization-format.md`, `test-case-format.md`, `test-case-runtime-format.md` и `review-findings-format.md`; не дублируй полный перечень defect classes в skill.
    - Проверь, что `coverage_depth_profile` и `artifact_mode` соответствуют complexity/risk: simple не перегружен full chain без причины, а deep/high-risk/table-heavy не прошел compact mode.
    - Проверь `TC Set Optimization Review`, если он обязателен; findings по этой зоне классифицируй как `test-design-depth`, `tc-set-optimization` или `over-testing`, если существующие категории недостаточны.
    - Ищи over-testing так же строго, как under-coverage: duplicate TC, low-value negatives, excessive fragmentation, several TC with same source_ref/input/oracle, и deep checks без маркировки отдельно от core.
    - Если TC, matrix или writer response закрывает unresolved `P0-blocker` / `P1-high` clarification question без accepted risk, это blocking finding. Категория зависит от дефекта: `clarification-question-quality`, `expected-result`, `traceability` или `test-design`.
    - Для table/list-heavy scope reviewer обязан сверять coverage against XHTML extraction, `source-row-inventory.md` and `source-table-normalization.md`. DOCX/PDF-only extraction is insufficient when XHTML is available.
    - Для table/PDF/DOCX/XHTML extraction scopes сначала проверь `source-row-inventory.md`, `source-row-completeness-matrix.md`, `source-table-normalization.md`, `dictionary-inventory.md` при наличии справочников, `test-design-decision-table.md` и `package-test-design-plan.md`.
    - Перед проверкой отдельных `TC-*` проверь split artifacts, matrix rows, package coverage, `DICT-*` links, mockup usage, coverage metrics and gaps together.
17. Обязательно прогони defect-class checklist из `test-design-review-rubric.md` и `test-design-defect-taxonomy.md`; не дублируй полный список классов в выводе, но явно фиксируй найденные blocking classes и evidence.
18. Для каждого спорного expected result примени evidence-first question: какой наблюдаемый artifact подтверждает pass/fail? Если artifact не указан для API/DB/RabbitMQ/model/internal state, создай `error` или требуй `GAP-*` / `unclear`.
19. Не требуй проверки, которых нет в ФТ. Например, не отмечай отсутствие проверки видимости, если ФТ не описывает видимость поля.
20. Для каждого finding укажи `review_mode` и `required_change`.
21. Для findings режима `traceability` обязательно ссылайся на строку матрицы через `traceability_ref = ATOM-*` или на `coverage_gap:<short-id>`, если строки matrix еще нет.
22. Для findings режима `structure` привязывай замечание к конкретному `test_case_id` или к месту в наборе.
23. Для findings режима `test-design` указывай, какой тип проверки отсутствует: `positive | negative | boundary | equivalence | dependency`. Если проблема в неподтвержденном expected result, используй категорию `expected-result`.
24. Если PDF для structural cross-check отсутствует, явно укажи это в human summary или findings как ограничение входных данных.
25. Во втором review сверяй не только обновленный набор тест-кейсов, но и writer response artifact. Если writer заявил `fixed`, проверь все affected artifacts: canonical TC, ledger, traceability matrix, Test-design Decision Table, Package Test Design Plan и coverage artifacts; рассинхрон current-scope ссылок `TC-*` / `ATOM-*` / `GAP-*` остается blocking finding.
26. Во втором review не переоткрывай закрытый finding без нового evidence.
27. Если findings artifact предыдущего раунда, writer response artifact или traceability matrix структурно невалидны, фиксируй это как blocking review finding.
28. Во втором review проверяй закрытие traceability findings по `traceability_ref`, а не по похожему тексту `source_path` или повторяющемуся `req_id`.
29. Если найдены unresolved findings, сохрани `prompt.reviewer-to-writer.round-N.md` для следующего writer round.
29a. Если review verdict = `not signed-off`, не записывай `stage_status: not-signed-off` в `workflow-state.yaml`: такого process-status нет. Для обычного следующего writer round используй `stage_status: ready-for-writer-revision` и `next_skill: ft-test-case-writer`; если достигнут round cap, используй `stage_status: round-cap-reached`; если нужен внешний input, используй `stage_status: blocked-input`.
30. Если набор подписан без unresolved findings, перед handoff проверь группировку, сквозную нумерацию `TC-*` и выполни `python scripts\validate_agent_artifacts.py --root <ft-package> --json` или runner validator gate по текущему scope. Final reviewer output должен содержать блок `Reviewer Sign-off Self-check` по `reviewer-output-format.md`; `validator_checked: yes`/`blocking_findings_absent: yes` допустимы только без scope `error`/`warning` либо с валидным `Validator Warning Waivers`. Затем сохрани `prompt.reviewer-to-ui-prep.md` и обнови handoff state.
31. Не выдавай handoff в `ft-ui-automation-prep`, если остаются `error`, `warning` или traceability `gap`, кроме явно допустимых `unclear`; для одиночного reviewer-pass без orchestrator-а не подменяй lifecycle sign-off, если sign-off должен фиксировать `ft-test-case-iteration`.

## Test-design Applicability Matrix Rule

In `test-design` and `full` modes, review the writer's `Test-design applicability matrix` before judging individual `TC-*`.

Rules:

- Use `coverage-checklist.md` as the canonical source for expected high-risk coverage dimensions.
- Verify that every visible FT dimension is represented in the matrix.
- For each `applicable = yes` row, require linked `ATOM-*` and either linked `TC-*` or linked `GAP-*`.
- For each linked `TC-*`, verify semantic coverage: the test steps, data, and final expected result must actually exercise that dimension. A generic positive case or a case for another dimension does not satisfy the matrix row.
- For each `applicable = unclear` row, require linked `GAP-*` and an analyst-facing question.
- If a row is missing, unsupported, silently skipped, linked to a non-covering `TC-*`, or contaminated by metadata-only atoms, return a finding with `coverage_dimension` from `review-findings-format.md`.
- For `test-design`, `coverage`, `expected-result`, and `scope` findings, never omit `coverage_dimension`.

## Канонические references

- Process/output: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md), [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md), [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md), [../../references/agent/next-step-prompt-format.md](../../references/agent/next-step-prompt-format.md), [../../references/agent/reviewer-output-format.md](../../references/agent/reviewer-output-format.md)
- Review method: [../../references/qa/review-findings-format.md](../../references/qa/review-findings-format.md), [../../references/qa/traceability-matrix-format.md](../../references/qa/traceability-matrix-format.md), [../../references/qa/test-design-review-rubric.md](../../references/qa/test-design-review-rubric.md), [../../references/agent/test-design-defect-taxonomy.md](../../references/agent/test-design-defect-taxonomy.md), [../../references/agent/requirements-clarification-questioning-policy.md](../../references/agent/requirements-clarification-questioning-policy.md)
- Scope/source/package artifacts: `scope-coverage-gaps-format.md`, `scope-clarification-requests-format.md`, `source-parity-check-format.md`, `source-row-inventory-format.md`, `source-table-normalization-format.md`, `dictionary-inventory-format.md`, `package-test-design-plan-format.md`, `test-design-depth-policy.md`, `tc-set-optimization-format.md`, `mockup-visual-inventory-format.md`.
- Scenario-specific deep references are loaded by [../../references/agent/instruction-loading-manifest.md](../../references/agent/instruction-loading-manifest.md).

## Ограничения

- Не используй этот skill для написания новых тест-кейсов вместо writer workflow.
- Не меняй FT-пакет и scope по ходу review, если это явно не требуется отдельной задачей.
- Не исправляй тест-кейсы сам. Возвращай remediation как findings artifact, human summary и traceability matrix при необходимости.
- Не расширяй scope на основании найденных пробелов. Out-of-scope замечания фиксируй как findings категории `scope`.
- Не дублируй общие правила из канонических references.
