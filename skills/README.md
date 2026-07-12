# Skills Map

Канонический список активных skill-ов:

- `ft-source-locator` - найти нужный FT-пакет и связанные материалы.
- `ft-scope-analyzer` - предложить внешние scope-ы по разделам/подразделам ФТ, подтвердить границы выбранного scope и зафиксировать `coverage gaps`.
- `ft-test-case-iteration` - оркестрировать writer-reviewer loop и довести набор до reviewer sign-off или зафиксировать unresolved findings.
- `ft-test-case-writer` - написать новые тест-кейсы по уже выбранному scope.
- `ft-test-case-reviewer` - review существующих тест-кейсов.
- `ft-ui-automation-prep` - post-iteration проверка signed-off кейсов в реальном UI и подготовка automation-ready версии.
- `agent-architecture-auditor` - аудит структуры `AGENTS.md`, `skills/`, `references/` и scripts.

## Когда какой skill использовать

- Если сначала нужно понять, с каким ФТ работать: `ft-source-locator`.
- Если FT-пакет уже выбран, но еще не определен точный фрагмент требований или нужно разбить большое ФТ на scope-ы: `ft-scope-analyzer`.
- Если scope уже зафиксирован и нужно написать новые кейсы одним writer-pass без review-cycle: `ft-test-case-writer`.
- Если scope уже зафиксирован и нужно пройти writer-reviewer iteration: `ft-test-case-iteration`.
- Если нужен новый session-based writer/reviewer cycle в отдельных Codex sessions: `ft-test-case-iteration` через `scripts/review_cycle_backend_dispatcher.py --backend auto`; SDK используется только как явно выбранный fallback.
- Если кейсы уже существуют и нужен review: `ft-test-case-reviewer`.
  По умолчанию он работает в режиме `full` и последовательно выполняет `traceability` -> `structure` -> `test-design`.
- Если набор уже получил `signed-off` и нужно сверить его с реальным UI перед подготовкой к автотестам: `ft-ui-automation-prep`.
- Если запрос про архитектуру агента, дублирование, хранение знаний и границы skill-ов: `agent-architecture-auditor`.

## Типовые цепочки

- Новый набор тест-кейсов: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-writer`
- Новый набор тест-кейсов с session-based review-cycle: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-iteration`
- Новый session-based review cycle: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-iteration` через `scripts/review_cycle_backend_dispatcher.py --backend auto`
- Подготовка automation-ready версии после sign-off: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-iteration` -> `ft-ui-automation-prep`
- Review существующих кейсов: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-reviewer`
- Аудит agent-layer: `agent-architecture-auditor` со script-first workflow (`skills/agent-architecture-auditor/scripts/audit_agent_architecture.py` -> manual interpretation)

## Instruction context

Для задач, где важно контролировать объем подгружаемых инструкций, используй resolver:

```powershell
python scripts/resolve_instruction_context.py --phase writer --mode initial_draft --scope-profile table --budget-report
```

Канонический manifest загрузки хранится в `references/agent/instruction-loading-manifest.md`. Он определяет только набор instruction files для сценария; workflow и QA-правила остаются в `SKILL.md` и `references/`.

## Канонические references

- Agent governance: [../references/agent](../references/agent)
- QA rules and formats: [../references/qa](../references/qa)
- Instruction contracts: [../references/agent/instruction-contract-index.md](../references/agent/instruction-contract-index.md)
- Instruction loading manifest: [../references/agent/instruction-loading-manifest.md](../references/agent/instruction-loading-manifest.md)
- Task-start skill routing: [../references/agent/task-start-skill-routing-format.md](../references/agent/task-start-skill-routing-format.md)
- Session-based review cycle: [../references/agent/session-based-review-cycle-format.md](../references/agent/session-based-review-cycle-format.md)
- Codex SDK orchestration: [../references/agent/codex-sdk-orchestration-format.md](../references/agent/codex-sdk-orchestration-format.md)
- Writer runtime contract: [../references/agent/writer-runtime-contract.md](../references/agent/writer-runtime-contract.md)
- Writer runtime workflow: [../references/agent/writer-runtime-workflow.md](../references/agent/writer-runtime-workflow.md)
- Writer process workflow: [../references/agent/writer-process-workflow.md](../references/agent/writer-process-workflow.md)
- Writer table workflow: [../references/agent/writer-table-workflow.md](../references/agent/writer-table-workflow.md)
- Writer revision workflow: [../references/agent/writer-revision-workflow.md](../references/agent/writer-revision-workflow.md)
- Writer remediation workflow: [../references/agent/writer-remediation-workflow.md](../references/agent/writer-remediation-workflow.md)
- Writer table artifacts format: [../references/agent/writer-table-artifacts-format.md](../references/agent/writer-table-artifacts-format.md)
- Writer handoff format: [../references/agent/writer-handoff-format.md](../references/agent/writer-handoff-format.md)
- Writer revision output format: [../references/agent/writer-revision-output-format.md](../references/agent/writer-revision-output-format.md)
- Intermediate decision log format: [../references/agent/agent-decision-log-format.md](../references/agent/agent-decision-log-format.md)
- Scope decomposition policy: [../references/agent/scope-decomposition-policy.md](../references/agent/scope-decomposition-policy.md)
- Source parity check format: [../references/agent/source-parity-check-format.md](../references/agent/source-parity-check-format.md)
- Negative Oracle Inventory: [../references/agent/negative-oracle-inventory-format.md](../references/agent/negative-oracle-inventory-format.md)
- Requiredness Oracle Inventory: [../references/agent/requiredness-oracle-inventory-format.md](../references/agent/requiredness-oracle-inventory-format.md)
- Quality feedback loop: [../references/agent/quality-feedback-loop.md](../references/agent/quality-feedback-loop.md)
- Test-design defect taxonomy: [../references/agent/test-design-defect-taxonomy.md](../references/agent/test-design-defect-taxonomy.md)
- Test case style examples: [../references/qa/test-case-style-examples.md](../references/qa/test-case-style-examples.md)
- Test case runtime format: [../references/qa/test-case-runtime-format.md](../references/qa/test-case-runtime-format.md)
- Coverage runtime checklist: [../references/qa/coverage-runtime-checklist.md](../references/qa/coverage-runtime-checklist.md)
- Coverage input boundaries: [../references/qa/coverage-input-boundaries.md](../references/qa/coverage-input-boundaries.md)
- Coverage integration and async: [../references/qa/coverage-integration-async.md](../references/qa/coverage-integration-async.md)
- Coverage obligation table: [../references/agent/coverage-obligation-table-format.md](../references/agent/coverage-obligation-table-format.md)
- Test-design coverage metrics: [../references/agent/test-design-coverage-metrics-format.md](../references/agent/test-design-coverage-metrics-format.md)
- Fixture catalog: [../references/agent/fixture-catalog-format.md](../references/agent/fixture-catalog-format.md)
- Risk / Priority Map: [../references/agent/risk-priority-map-format.md](../references/agent/risk-priority-map-format.md)
- User interaction guide: [../references/agent/user-interaction-guide.md](../references/agent/user-interaction-guide.md)
- Full user manual: [../references/agent/user-manual.md](../references/agent/user-manual.md)
- End-to-end use case: [../references/agent/test-case-writing-use-case.md](../references/agent/test-case-writing-use-case.md)
