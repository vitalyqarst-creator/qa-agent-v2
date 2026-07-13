# Visual Assessment Medium-Scope Prepared Iteration

## Цель этапа

Собрать current-source immutable package на 13 obligations / 12 planned TC и выполнить один promotion-off exec writer-reviewer benchmark после всех pre-live gates.

## Входные артефакты

- `fts/AutoFin/AGENT-NOTES.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/negative-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/requiredness-oracle-inventory.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/mockup-visual-inventory.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/workflow-state.yaml`
- `fts/AutoFin/open-scope-coverage-gaps_ответы Соболева.md`

## Обязательные действия

- Работать в режиме `fresh-eval-run`; baseline не читать как requirement evidence и не перезаписывать.
- Сохранить `WP-01`, все `SRC-001`-`SRC-052`, `BSR 311`-`BSR 317`, 13 obligations и полный `DICT-001/101-108`.
- Назначить `package_id` каждому ATOM/TC; выполнить ledger, Package Test Design Plan и TC self-check gates.
- Планировать ровно 12 TC: BSR 313/314 покрываются одним visibility case с одним expected result; остальные obligations остаются атомарными.
- Для `SO-REQ-001/002` создать candidate UI-calibration TC без выдуманного точного механизма.
- До live пройти compile, runtime identity, dictionary/oracle/state/capacity gates, artifact validator, exec dry-run, pushed checkpoint and separate pushed authorization.
- Выполнить один dispatcher и сравнить duration/tokens/uncached tokens per obligation с V4.

## Не делать

- Не использовать PreFinal, production TC, review-cycle outputs или user-owned untracked 4.3 draft как requirements.
- Не использовать SDK fallback, sharding, retry, resume/rebind или promotion.
- Не урезать dictionary evidence ради token target.

## Ожидаемые выходы

- New review cycle and immutable package.
- Fresh writer draft and fresh reviewer findings.
- Performance/quality report and terminal stop gate.
- Production target remains absent.

## Gate завершения

Этап завершён после единственного terminal dispatcher outcome, performance comparison, protected-hash recheck, artifact validation and pushed terminal commit. Any pre-live blocker stops before LLM.
