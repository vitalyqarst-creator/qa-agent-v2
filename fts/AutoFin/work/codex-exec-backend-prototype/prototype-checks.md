# Проверки `codex exec` prototype

Дата: `2026-07-10`.

## Результаты

| Проверка | Результат |
|---|---|
| `tests/test_codex_exec_review_cycle_runner.py` | `19 passed` |
| `tests/test_codex_review_cycle_runner.py` | `96 passed` |
| `tests/test_diagnose_codex_sdk_turn.py` | `3 passed` |
| `scripts/run_tests.py --suite architecture` | pass: `59 checks`, `0 findings` |
| `scripts/run_tests.py --suite agent-layer-fast` | pass: `240 tests`, `1 skipped` |
| `scripts/run_tests.py --suite artifact-validator-sharded` | pass: `388/388`, `7/7` shards |
| `scripts/run_tests.py --suite agent-layer` | pass: `240 tests`, `1 skipped`, затем `388/388` artifact-validator tests |
| Full instruction budget sweep через architecture audit `--fail-on warning` | pass: все `24` scenario budgets в пределах limits |
| Python compile и runner `--help` | pass |
| `git diff --check` | pass; только информационные LF/CRLF notices |

## Capability и live smoke

`codex`, `codex.exe` обнаружены в packaged build `OpenAI.Codex_26.707.3748.0`, но `codex --version`, `codex --help` и `codex exec --help` завершаются с exit code `1` и `Access is denied`. Auth, sandbox flags и event schema недостижимы. Live smoke имеет статус `blocked-codex-exec-unavailable`; writer/reviewer live processes и final TC не создавались.

## Root artifact validation blocker

Команда `python scripts/validate_agent_artifacts.py --root . --json --fail-on warning` выполнилась, но завершилась с exit code `1` на накопленном состоянии всего репозитория:

- `10 509` findings: `176 errors`, `8 396 warnings`, `1 937 info`;
- проверено `160` workflow states, `770` test-case files и тысячи исторических work/snapshot artifacts;
- representative errors: отсутствующие canonical/alias paths из `fts/artifact-manifest.json`, старые handoff prompts без актуального формата, legacy snapshot workflow states с отсутствующими полями.

Validator не поддерживает task-scoped path filter. Эти baseline findings не исправлялись: они не относятся к exec backend prototype и выходят за разрешённый scope. Task-scoped unit, architecture и sharded validator suites проходят.
