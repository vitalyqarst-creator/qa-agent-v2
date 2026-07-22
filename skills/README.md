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
- Если scope уже атомаризирован в hash-bound source packet и нужен короткий
  deterministic-first маршрут без benchmark/history: условный режим
  `ft-test-case-iteration` `lean_v2` через `scripts/run_lean_v2_iteration.py`.
- Если новая версия ФТ должна актуализировать signed-off набор: условный режим
  `ft-test-case-iteration` `incremental-update` через
  `scripts/run_incremental_update_iteration.py`; обычный full-loop его инструкции не загружает.
- Если явно передан checked-in full-process config с `schema_version = 2`:
  напрямую `ft-test-case-iteration` через `scripts/start_full_process_observation.py --execute`;
  generic цепочки discovery/scope остаются для запусков без такого config.
- Если нужен новый session-based writer/reviewer cycle в отдельных Codex sessions: `ft-test-case-iteration` через `scripts/review_cycle_backend_dispatcher.py --backend auto`; SDK используется только как явно выбранный fallback.
- Если кейсы уже существуют и нужен review: `ft-test-case-reviewer`.
  По умолчанию он работает в режиме `full` и последовательно выполняет `traceability` -> `structure` -> `test-design`.
- Если набор уже получил `signed-off` и нужно сверить его с реальным UI перед подготовкой к автотестам: `ft-ui-automation-prep`.
- Если запрос про архитектуру агента, дублирование, хранение знаний и границы skill-ов: `agent-architecture-auditor`.

## Типовые цепочки

- Новый набор тест-кейсов: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-writer`
- Новый набор тест-кейсов с session-based review-cycle: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-iteration`
- Новый session-based review cycle: `ft-source-locator` -> `ft-scope-analyzer` -> `ft-test-case-iteration` через `scripts/review_cycle_backend_dispatcher.py --backend auto`
- Новый deterministic-first cycle: `ft-source-locator` -> `ft-scope-analyzer` ->
  `ft-test-case-iteration` в режиме `lean_v2` после подготовки atomic source packet.
- Актуализация новой версии ФТ: `ft-test-case-iteration` в режиме
  `incremental-update` после явного выбора обеих версий и target scope.
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
- Lean-v2 iteration: [../references/agent/lean-v2-iteration.md](../references/agent/lean-v2-iteration.md)
- Session-based review cycle: [../references/agent/session-based-review-cycle-format.md](../references/agent/session-based-review-cycle-format.md)
- Codex SDK orchestration: [../references/agent/codex-sdk-orchestration-format.md](../references/agent/codex-sdk-orchestration-format.md)
- Quality feedback loop: [../references/agent/quality-feedback-loop.md](../references/agent/quality-feedback-loop.md)
- User interaction guide: [../references/agent/user-interaction-guide.md](../references/agent/user-interaction-guide.md)
- End-to-end use case: [../references/agent/test-case-writing-use-case.md](../references/agent/test-case-writing-use-case.md)
