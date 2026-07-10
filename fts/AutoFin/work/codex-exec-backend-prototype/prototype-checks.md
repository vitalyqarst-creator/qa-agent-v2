# Проверки `codex exec` prototype

Дата: `2026-07-10`.

## Результаты

| Проверка | Результат |
|---|---|
| `tests/test_codex_exec_review_cycle_runner.py` | `23 passed` |
| Backend-independent v2 suites | `56 passed`: contract `26`, runtime `8`, SDK backend `5`, attempts `7`, metrics `4`, backend matrix `6` |
| `tests/test_codex_review_cycle_runner.py` | `96 passed` |
| `tests/test_diagnose_codex_sdk_turn.py` | `3 passed` |
| `scripts/run_tests.py --suite architecture` | pass: `59 checks`, `0 findings` |
| `scripts/run_tests.py --suite agent-layer-fast` | pass: `300 tests`, `1 skipped` |
| `scripts/run_tests.py --suite artifact-validator-sharded` | pass: `388/388`, `7/7` shards |
| `scripts/run_tests.py --suite agent-layer` | Phase 1 checkpoint: `266 tests`, `1 skipped`, затем `388/388`; после фаз 2–9 выполнен актуальный `agent-layer-fast` |
| Full instruction budget sweep через architecture audit `--fail-on warning` | pass: все `24` scenario budgets в пределах limits |
| Python compile и runner `--help` | pass |
| `git diff --check` | pass; только информационные LF/CRLF notices |

## Capability и live smoke

AppX `codex` из `PATH` по-прежнему возвращает `Access is denied`, но user-local `codex-cli 0.144.0-alpha.4` доступен и авторизован. Read-only auth probe прошёл, реальные flags и JSONL schema подтверждены.

Source-backed live writer получил отдельный `thread_id`, но завершился `blocked-timeout` через `600.453` секунды без draft. Reviewer не стартовал, automatic retry не выполнялся, production final TC не создан. Stage Contract v2 result и metrics сохранены; input hashes после процесса подтверждены.

## Root artifact validation blocker

Команда `python scripts/validate_agent_artifacts.py --root . --json --fail-on warning` выполнилась, но завершилась с exit code `1` на накопленном состоянии всего репозитория:

- `10 509` findings: `176 errors`, `8 396 warnings`, `1 937 info`;
- проверено `160` workflow states, `770` test-case files и тысячи исторических work/snapshot artifacts;
- representative errors: отсутствующие canonical/alias paths из `fts/artifact-manifest.json`, старые handoff prompts без актуального формата, legacy snapshot workflow states с отсутствующими полями.

Validator не поддерживает task-scoped path filter. Эти baseline findings не исправлялись: они не относятся к exec backend prototype и выходят за разрешённый scope. Task-scoped unit, architecture и sharded validator suites проходят.
