# Writer Runtime Contract

Этот reference задает короткий runtime contract для `ft-test-case-writer`. Он используется resolver-ом как default writer context. Полные форматы и deep rules остаются в связанных references и подгружаются условно.

## Когда использовать

Используй этот contract для:

- `writer.initial_draft.simple`;
- `writer.initial_draft.ui`, если scope не table-heavy;
- `writer.revision_from_findings`;
- предварительной проверки, можно ли запускать writer без возврата на locator/scope.

Если scope содержит таблицы полей/действий, row-level parity, package-heavy decomposition или validator finding по design artifacts, дополнительно читай `writer-output-format.md` и table/deep references из manifest.

## Required Inputs

Writer может стартовать только если уже определены:

- FT-пакет;
- подтвержденный scope и его границы;
- основной источник ФТ;
- `scope-contract.md`;
- `scope-coverage-gaps.md`;
- `workflow-state.yaml` или эквивалентный handoff с `next_skill = ft-test-case-writer`;
- package-specific `AGENT-NOTES.md`, если он есть в корне FT-пакета.

Conditional inputs:

- `source-parity-check.md` обязателен, если основной ФТ доступен в DOCX и PDF;
- `source-row-inventory.md` обязателен для row-level/table parity;
- `mockup-visual-inventory.md` обязателен для UI scope с mockup/screen image;
- `negative-oracle-inventory.md` / `requiredness-oracle-inventory.md` обязательны, если scope handoff содержит validation/format restrictions или requiredness obligations;
- structured findings и traceability matrix обязательны для `revision_from_findings`, если они были переданы reviewer-ом.

## Hard Stops

Не ставь `stage_status: ready-for-review`, если:

- FT-пакет или scope не выбран;
- отсутствует обязательный input из handoff;
- есть blocking `coverage gaps` без accepted-risk решения;
- expected behavior нельзя вывести из ФТ или разрешенных материалов, и obligation нельзя честно оформить как `ui-calibration-required` candidate TC;
- writer обнаружил новый gap, который блокирует исполнимый результат;
- simple runtime context оказался недостаточным: нужен table/UI/revision/validator deep context из manifest;
- технический fallback привел к compact draft, потере детализации, one-shot giant write или непроверенному mojibake output.

В этих случаях используй `stage_status: blocked-input`, заполни `blocking_reasons` и маршрутизируй задачу в нужный skill или пользователю через handoff prompt.

## Runtime Workflow

1. Объяви выбранный writer scenario и resolved instruction context.
2. Прочитай required inputs и зафиксируй missing inputs до генерации `TC-*`.
3. Подтверди границы scope; не расширяй scope самостоятельно.
4. Разложи требования на coverage obligations, atomic statements или explicit gaps.
5. Построй coverage plan и metrics по `coverage-runtime-checklist.md`; для mandatory classes используй `Coverage Obligation Table`.
6. Напиши `TC-*` по `test-case-runtime-format.md`.
6a. Для `oracle_status = ui-calibration-required` создай candidate TC по `negative-ui-calibration-policy.md`; не заменяй его общим `GAP-*` и не выдумывай точную UI-реакцию без source-backed oracle.
6b. В каждом `TC-*` пиши `Предусловия` как воспроизводимый setup: numbered action setup steps, fixture/API setup или reusable setup profile. Не оставляй magic/passive UI states без действия, которое их создает; `Дождаться` / `Убедиться` допустимы только после setup action.
6b.1. Production files under `fts/**/test-cases/*.md` are self-contained runtime artifacts: no setup profile references, stand/environment wording or package-name leakage; dynamically created fields must include the reveal/create action in preconditions, for contact-person fields - `Добавить контактное лицо`.
6c. Для source-backed input restriction всегда разложи allowed classes и invalid classes; напиши positive TC на allowed representative values и negative/candidate-negative TC на invalid representative values. Candidate negative TC не заменяет positive allowed-class TC.
6d. If one TC references more than two independent source-backed obligations, split it unless one visible source-backed workflow justifies grouping. Grouped TC must include `Scenario rationale` and must not hide missing atomic TC/GAP coverage.
6e. For similar fields/classes with shared restrictions, representative or pairwise coverage is allowed only when the artifact states selected combinations, omitted combinations and residual risk. Otherwise write the missing TC/GAP items.
7. Проверь traceability: каждый `TC-*` связан с `ATOM-*` / requirement code / source reference.
8. Выполни writer self-check и применимые quality gates.
9. Обнови `workflow-state.yaml` и создай `prompt.writer-to-reviewer.round-N.md`, если draft готов к review.

## Output Contract

Default writer output:

- canonical test-case file в `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`;
- краткий coverage summary;
- explicit `Coverage Gaps`, если есть `GAP-*`;
- writer self-check;
- updated `workflow-state.yaml`;
- next-step prompt для reviewer.

Для table-heavy/package-based scope используй full output contract из `writer-output-format.md`: split artifacts, Source Row Inventory, normalization, TDDT, Coverage Obligation Table, Package Test Design Plan, coverage metrics, Fixture Catalog при применимости, Risk / Priority Map, Test Design Review, Writer Quality Gate и coverage maps.

## Logging

Для writer-pass сохраняй session log и decision log по каноническим форматам. Runtime contract не заменяет:

- `workflow-state-format.md`;
- `session-log-format.md`;
- `agent-decision-log-format.md`;
- `next-step-prompt-format.md`.

Эти references подгружаются как deep/process context, если нужно создавать или проверять соответствующие artifacts подробно.

## Deep References

- Full writer output: `writer-output-format.md`
- Writer Quality Gate details: `writer-quality-gate-format.md`
- Coverage obligations: `references/agent/coverage-obligation-table-format.md`
- Negative UI calibration: `references/agent/negative-ui-calibration-policy.md`
- Coverage metrics: `references/agent/test-design-coverage-metrics-format.md`
- Fixture catalog: `references/agent/fixture-catalog-format.md`
- Risk / Priority Map: `references/agent/risk-priority-map-format.md`
- Test-case full format: `references/qa/test-case-format.md`
- Coverage deep checklist: `references/qa/coverage-checklist.md`
- Review findings/writer response: `references/qa/review-findings-format.md`
- Traceability matrix: `references/qa/traceability-matrix-format.md`
