# Search Clear Context Fresh Writer Benchmark

## Цель этапа

Создать fresh-eval draft по BSR 32 без использования старых generated тест-кейсов.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/19-iteration-smoke-search-clear-context/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/negative-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/requiredness-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/mockup-visual-inventory.md`
- `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/workflow-state.yaml`
- `fts/AutoFin/AGENT-NOTES.md`

## Обязательные действия

- Режим `fresh-eval-run`; работать только с `WP-01`.
- Создать writer-side row inventory/completeness, normalization, ledger, design plan and four atomic TC.
- Указать `package_id = WP-01` для каждого ATOM/TC; выполнить package ledger, design-plan и TC self-check gates.
- Использовать mockup interaction hints только для шагов; не выводить defaults из макета.
- Для generated/canonical artifacts использовать declared manifest strategy.

## Не делать

- Не читать H19 writer draft, старый production testcase или review outputs.
- Не объединять четыре reset dimensions в один multi-oracle TC.
- Не ставить signed-off и не выполнять production write.

## Ожидаемые выходы

- Fresh unsigned draft, split test-design artifacts, deterministic gate evidence and reviewer handoff.

## Gate завершения

Writer pass готов только после 4/4 obligation coverage, unique titles, structure/metadata/oracle gates and `ready-for-review`.
