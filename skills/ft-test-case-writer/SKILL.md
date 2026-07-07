---
name: ft-test-case-writer
description: Пишет новые ручные тест-кейсы по уже выбранному и ограниченному фрагменту требований или корректирует существующий набор по structured findings. В revision mode обязан учитывать `review_mode` reviewer-а и при необходимости использовать traceability matrix.
---

# FT Test Case Writer

Используй этот skill только когда уже определены:

- нужный FT-пакет;
- границы scope;
- основной источник ФТ и связанные материалы;
- режим работы: `initial_draft`, `revision_from_findings` или remediation.

Если пакет, источник или scope еще не выбраны, сначала используй `ft-source-locator` и `ft-scope-analyzer`.

## Входы

- путь к FT-пакету `fts/<ft-slug>/...`;
- основной документ ФТ;
- `source-selection.md` с `xhtml_available: yes` и main FT XHTML;
- PDF-версия основного ФТ для сверки структуры, если она есть;
- `source-parity-check.md`, если основной ФТ доступен в DOCX и PDF;
- `source-row-inventory.md`, если handoff требует row-level/table parity;
- `dictionary-inventory.md`, если source/support уже ссылается на справочник или фиксированный перечень значений;
- `mockup-visual-inventory.md`, если подтвержденный UI scope содержит mockup / screen image / `mockups/`;
- выбранный раздел, подраздел или узкий фрагмент требований;
- package-specific `AGENT-NOTES.md`, если он есть;
- mode: `initial_draft`, `revision_from_findings` или remediation;
- при `revision_from_findings`: существующий набор тест-кейсов, structured findings artifact, номер review round, `review_mode` и traceability matrix при наличии.

## Выходы

- canonical test-case file: `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`;
- при `initial_draft`: split test-design artifacts в `fts/<ft-slug>/work/test-design/<section-id>-<scope-slug>/`;
- при наличии `dictionary-source` / reference-list rows: `dictionary-inventory.md` рядом со split test-design artifacts до TDDT/plan/TC;
- при revision в session-based cycle: `fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/writer-rN-response.md`;
- traceability matrix и обязательный `.xlsx`-дубль, если writer создает или обновляет matrix;
- `coverage-obligation-table.md`, `coverage-metrics.md`, `fixture-catalog.md` при применимости, `coverage gaps`, открытые вопросы, `test-design-review.md`, Writer Quality Gate и writer self-check в соответствующих split artifacts;
- `writer-session-log.md` и `agent-decision-log.md`, когда это требуется stage workflow;
- `workflow-state.yaml` со статусом `ready-for-review` только после успешных gates;
- `prompt.writer-to-reviewer.round-N.md` в текущей handoff-папке.

## Runtime Contract Anchors

- Если доступна PDF-версия основного ФТ для сверки структуры, сверяй по ней структуру разделов, коды требований и порядок источника; не используй PDF как замену тексту основного ФТ.
- Перед `initial_draft` проверь `source-selection.md`: без `xhtml_available: yes` верни `blocked-input`; tables/lists бери из XHTML, DOCX - source of truth, PDF/mockups не заменяют main FT.
- Если источники не задают поведение, не придумывай поведение, а выноси это в `coverage gaps`.
- В `revision_from_findings` используй structured findings artifact и traceability matrix artifact; Обрабатывай findings с учетом `review_mode`.
- Для traceability findings и writer response сохраняй связь `traceability_ref = ATOM-*`.
- Handoff по review mode: `traceability` — закрывай gaps покрытия; `structure` — выравнивай шаблон, порядок, группировку и сквозную нумерацию; `test-design` — добавляй или корректируй проверки и expected results.
- В `initial_draft` writer строит atomic requirements ledger, затем тест-кейсы с canonical fields и writer self-check.
- Если writer создает или обновляет matrix, обязателен `.xlsx`-дубль traceability matrix.
- Проверяй smell markers из canonical QA references: test-case-forbidden-formulation-smell, test-case-abstract-oracle-smell, test-case-input-restriction-transition-oracle-smell, test-case-mechanical-field-step-smell.

## Workflow

Следуй runtime workflow: [../../references/agent/writer-runtime-workflow.md](../../references/agent/writer-runtime-workflow.md).

Подключай deep workflow только по фактическому сценарию:

- process artifacts, logs, artifact-write strategy: [../../references/agent/writer-process-workflow.md](../../references/agent/writer-process-workflow.md);
- table-heavy / row-level parity writing: [../../references/agent/writer-table-workflow.md](../../references/agent/writer-table-workflow.md);
- revision by findings: [../../references/agent/writer-revision-workflow.md](../../references/agent/writer-revision-workflow.md);
- validator, Writer Quality Gate or style remediation: [../../references/agent/writer-remediation-workflow.md](../../references/agent/writer-remediation-workflow.md).

Minimum runtime rules:

1. Не расширяй scope во время writing.
2. Не выдумывай системное поведение, поля, статусы, кнопки, интеграции или expected results.
3. Один `TC-*` покрывает одну проверку и один основной expected result.
4. Requirement codes, например `GSR 22`, сохраняй буквально.
5. Не превращай gaps или unclear notes в `TC-*`.
6. Если source/support задает справочник, создай/обнови `dictionary-inventory.md` и ссылайся на `DICT-*`; branch examples из ФТ не заменяют полный справочник.
7. Не ставь `stage_status: ready-for-review`, пока source/parity/mockup/table/dictionary inputs, Writer Quality Gate и validator blockers не закрыты.
8. Перед `ready-for-review` проверь canonical TC на unresolved generic fixture/test-data/oracle smells: `Минимальный валидный набор данных`, `валидные данные`, `валидная заявка`, `значение из тестовых данных принято/не принимается`. Такие формулировки допустимы только если рядом есть конкретный воспроизводимый baseline, literal/параметр или linked fixture artifact; иначе исправь TC или оформи `GAP-*` / `unclear`.
9. Перед `ready-for-review`, `semantic-review-ready` и финальным handoff проверь каждый `TC-*` по [../../references/qa/test-case-runtime-format.md](../../references/qa/test-case-runtime-format.md): `Трассировка` обязательна, optional source fields допустимы только если добавляют недублирующую навигацию или реальную source evidence. Если `TC-*` использует `DICT-*`, тот же id должен быть в `Трассировка`; synthetic quote нельзя выдавать за цитату ФТ.
10. Не смешивай схемы TC: один `TC-*` не должен одновременно содержать metadata table и bold metadata fields, либо runtime heading `### Тестовые данные` / `### Шаги` / `### Итоговый ожидаемый результат` и дублирующее inline/bold поле с тем же смыслом. Canonical writer output должен использовать parser-supported bold metadata fields из `test-case-format.md`: `**Название:**`, `**Тип:**`, `**Приоритет:**`, `**package_id:**`, `**Трассировка:**`. table-only metadata `| Поле | Значение |` / `| package_id | WP-01 |` не является валидной заменой, потому что `package_id` и required fields должны быть parseable validator-ом.
11. После любого изменения `TC-*`, `ATOM-*`, `GAP-*`, `DICT-*` или `package_id` синхронизируй canonical TC, ledger, traceability matrix, Test-design Decision Table, Package Test Design Plan, coverage artifacts и writer response. Статус `fixed` допустим только после проверки всех affected artifacts, а не только canonical file.
12. Writer-ready handoff (`ready-for-review`, `writer-draft-ready`, `semantic-review-ready`) допустим только если current-scope validator warning/error из canonical TC, active test-design dir и cycle outputs либо исправлен, либо оформлен как валидный `false-positive`/waiver с id, path, evidence и rationale, либо не относится к текущему scope. Writer self-check и Writer Quality Gate должны ссылаться на scoped validator evidence или runner validator gate evidence; не рассчитывай, что reviewer разберет очевидный current-scope validator blocker после передачи.
12a. Для validator findings `test-case-unsupported-input-filtering-oracle-smell` и `test-case-unsupported-numeric-validation-feedback-smell` remediation не может быть простой заменой одного неподтвержденного UI-механизма другим. Если source говорит только `не принимает`, `только цифры`, `ниже минимума не принимается`, writer не должен менять `значение не отображается/очищено` на `красная подсветка`, `сообщение`, `blocked transition` или `Анкета клиента не открыта` без прямого source/UI/support evidence. Если deterministic observable oracle не выводится, сохрани invalid class в design artifacts и оставь narrow `GAP-*` / `unclear` на enforcement mechanism.
13. Если applicable dimension требует обязательные coverage classes (`numeric-format`, `exact-length`, dependency transitions, repeatable blocks, checkbox-list, generated document mapping), разложи их в `Coverage Obligation Table`, `Package Test Design Plan` и `coverage-metrics.md` до `TC-*`.
14. Если writer не может подготовить проверяемый результат без новых решений по scope или source, используй `blocked-input`.
15. Перед writer-ready handoff выполни `artifact-shape-preflight` из `writer-output-format.md` и `writer-quality-gate-format.md`: split artifacts должны использовать точные canonical headings/table columns без alias columns и без соседних дублей вида `# X` + `## X`, `writer-quality-gate.md` должен иметь `gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review`, а canonical TC file must not duplicate split artifact tables. При любом таком дефекте ставь `blocked-input` или исправляй артефакты до передачи на review.
16. Не используй неканонические status aliases в writer-side artifacts: `Writer Quality Gate` и `Test Design Review` принимают только `pass | fail | blocked | needs-rewrite`; `Coverage Obligation Table` принимает только `covered | gap | unclear | blocked | not-applicable | n/a`. `pass-with-gap`, `pass-with-gaps`, `planned`, `ok`, `yes`, `passed`, `failed` и локальные варианты являются validator defects.
17. `writer-self-check.md` не должен содержать пустые секции. Каждая heading-секция, включая `Artifact Write Evidence`, должна иметь evidence, таблицу/список, ссылку на session log / split artifact или явное `not-applicable` с причиной.
18. `placeholder-sentinel-normalization`: в traceability-bearing таблицах split artifacts и reviewer matrices не используй placeholder `-` / `N/A` в колонках связей и трассировки. Пиши явный sentinel: `not_applicable:covered`, `not_covered:<GAP-ID>`, `unclear:<GAP-ID>`, `no_requirement_code:<source_ref>` или `none_required:<reason>`.

## Runtime Format Clarifications

- Slim runtime `TC-*` is valid when `Название`, `Тип`, `Приоритет`, `package_id`, `Трассировка`, `Предусловия`, `Тестовые данные`, numbered `Шаги`, `Итоговый ожидаемый результат`, and `Постусловия` are present and parseable. Do not force optional source fields when `Трассировка` plus split artifacts already provide source evidence.
- `artifact-shape-preflight` accepts one split artifact heading at `# Section` or `## Section`. Missing/wrong headings and adjacent duplicates like `# Section` + `## Section` must be fixed or block writer-ready handoff.

## Test-design Applicability Matrix Rule

В `initial_draft` построй `Test-design applicability matrix` после atomic requirements ledger и до финализации тест-кейсов. Короткие runtime-правила смотри в [../../references/qa/coverage-runtime-checklist.md](../../references/qa/coverage-runtime-checklist.md); deep remediation использует [../../references/qa/coverage-checklist.md](../../references/qa/coverage-checklist.md).

Правила:

- каждая applicable coverage dimension должна иметь linked `ATOM-*` и linked `TC-*` или `GAP-*`;
- `applicable = unclear` всегда требует linked `GAP-*`;
- `applicable = no` требует source-based reason;
- linked `TC-*` должен реально покрывать dimension, а не просто выглядеть похожим.

## Канонические references

- Skill map: [../README.md](../README.md)
- Instruction contract index: [../../references/agent/instruction-contract-index.md](../../references/agent/instruction-contract-index.md)
- Task-start routing: [../../references/agent/task-start-skill-routing-format.md](../../references/agent/task-start-skill-routing-format.md)
- Writer runtime workflow: [../../references/agent/writer-runtime-workflow.md](../../references/agent/writer-runtime-workflow.md)
- Writer runtime contract: [../../references/agent/writer-runtime-contract.md](../../references/agent/writer-runtime-contract.md)
- Writer process workflow: [../../references/agent/writer-process-workflow.md](../../references/agent/writer-process-workflow.md)
- Writer table workflow: [../../references/agent/writer-table-workflow.md](../../references/agent/writer-table-workflow.md)
- Writer revision workflow: [../../references/agent/writer-revision-workflow.md](../../references/agent/writer-revision-workflow.md)
- Writer remediation workflow: [../../references/agent/writer-remediation-workflow.md](../../references/agent/writer-remediation-workflow.md)
- Workflow state: [../../references/agent/workflow-state-format.md](../../references/agent/workflow-state-format.md)
- Session log format: [../../references/agent/session-log-format.md](../../references/agent/session-log-format.md)
- Agent decision log format: [../../references/agent/agent-decision-log-format.md](../../references/agent/agent-decision-log-format.md)
- Artifact write strategy: [../../references/agent/artifact-write-strategy-format.md](../../references/agent/artifact-write-strategy-format.md)
- Writer output format: [../../references/agent/writer-output-format.md](../../references/agent/writer-output-format.md)
- Writer table artifacts format: [../../references/agent/writer-table-artifacts-format.md](../../references/agent/writer-table-artifacts-format.md)
- Dictionary inventory format: [../../references/agent/dictionary-inventory-format.md](../../references/agent/dictionary-inventory-format.md)
- Writer handoff format: [../../references/agent/writer-handoff-format.md](../../references/agent/writer-handoff-format.md)
- Writer revision output format: [../../references/agent/writer-revision-output-format.md](../../references/agent/writer-revision-output-format.md)
- Source parity check format: [../../references/agent/source-parity-check-format.md](../../references/agent/source-parity-check-format.md)
- Mockup visual inventory format: [../../references/agent/mockup-visual-inventory-format.md](../../references/agent/mockup-visual-inventory-format.md)
- Test case runtime format: [../../references/qa/test-case-runtime-format.md](../../references/qa/test-case-runtime-format.md)
- Test case format: [../../references/qa/test-case-format.md](../../references/qa/test-case-format.md)
- Review findings format: [../../references/qa/review-findings-format.md](../../references/qa/review-findings-format.md)
- Traceability matrix format: [../../references/qa/traceability-matrix-format.md](../../references/qa/traceability-matrix-format.md)
- Coverage runtime checklist: [../../references/qa/coverage-runtime-checklist.md](../../references/qa/coverage-runtime-checklist.md)
- Coverage checklist: [../../references/qa/coverage-checklist.md](../../references/qa/coverage-checklist.md)
- Coverage obligation table format: [../../references/agent/coverage-obligation-table-format.md](../../references/agent/coverage-obligation-table-format.md)
- Test-design coverage metrics format: [../../references/agent/test-design-coverage-metrics-format.md](../../references/agent/test-design-coverage-metrics-format.md)
- Fixture catalog format: [../../references/agent/fixture-catalog-format.md](../../references/agent/fixture-catalog-format.md)
- Risk / Priority Map format: [../../references/agent/risk-priority-map-format.md](../../references/agent/risk-priority-map-format.md)
- Experience-based coverage format: [../../references/agent/experience-based-coverage-format.md](../../references/agent/experience-based-coverage-format.md)
- State model coverage format: [../../references/agent/state-model-coverage-format.md](../../references/agent/state-model-coverage-format.md)
- Traceability rules: [../../references/qa/traceability-rules.md](../../references/qa/traceability-rules.md)
- Skill boundaries: [../../references/agent/skill-boundaries.md](../../references/agent/skill-boundaries.md)

## Ограничения

- Не выбирай новый FT-пакет и не отвечай на вопрос «что брать» вместо `ft-source-locator`.
- Не определяй scope с нуля вместо `ft-scope-analyzer`.
- Не делай review существующего набора вместо `ft-test-case-reviewer`.
- Не запускай writer-reviewer orchestration вместо `ft-test-case-iteration`.
- Не проводи аудит agent-layer вместо `agent-architecture-auditor`.
- Не дублируй общие QA-правила в этом skill-е: добавляй или меняй canonical references.
