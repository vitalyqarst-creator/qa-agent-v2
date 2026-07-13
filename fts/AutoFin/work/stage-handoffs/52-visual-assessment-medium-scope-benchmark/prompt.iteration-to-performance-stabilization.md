# Следующий этап: стабилизация writer latency

## Цель этапа

Уменьшить writer workload без потери V3 semantic acceptance: исключить двойное разворачивание exhaustive dictionary и заменить шумный single-run duration verdict на устойчивую метрику.

## Входные артефакты

- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/live-result.v1.json`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/live-result.v2.json`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/live-result.v3.json`
- `fts/AutoFin/work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/performance-analysis.v3.md`
- `fts/AutoFin/work/review-cycles/visual-assessment-medium-scope-benchmark-v3-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `fts/AutoFin/work/review-cycles/visual-assessment-medium-scope-benchmark-v3-20260713/attempts/writer-r1/attempt-001/runner-output/dictionary-projection.json`
- `scripts/codex_exec_review_cycle_runner.py`
- `references/agent/prepared-writer-runtime-profile.md`

## Обязательные действия

- Начать с `agent-architecture-auditor` и проверить, где должен жить contract runner-owned dictionary projection.
- Доказать byte/token duplication между writer-rendered dictionary list и projection block.
- Спроектировать writer contract, при котором writer задаёт исполнимую проверку, а exhaustive values материализует ровно один runner-owned слой.
- Добавить positive/negative regression: reviewer-visible draft остаётся полным, но writer output не дублирует values.
- Определить latency verdict по median нескольких сопоставимых runs либо явно классифицировать single-run duration как observation.

## Ограничения

- Не менять DOCX/XHTML/PDF, FT-first baseline или принятый V3 draft.
- Не ослаблять dictionary completeness, action/path unambiguity или calibration lifecycle gates.
- Не запускать live до отдельного плана, checkpoint и user authorization.
- Не оптимизировать Python orchestration: его доля доказанно составляет только 1.48%.

## Ожидаемые выходы

- bounded architecture decision и regression-backed implementation candidate;
- before/after writer payload byte/token estimate;
- revised benchmark protocol with stable latency statistic;
- explicit pre-live stop gate for any later benchmark.

## Gate завершения

Offline tests and architecture audit pass, dictionary completeness remains exact, and no live invocation is performed in this stage.
