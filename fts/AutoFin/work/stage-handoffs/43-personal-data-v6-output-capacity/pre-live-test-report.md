# V6 Pre-Live Test Report

## Целевые проверки

- `tests/test_prepared_workflow_compiler.py` + `tests/test_codex_exec_review_cycle_runner.py`: `132 passed`.
- Runner/output-schema/instruction-context regression после исправлений: `110 passed`.
- Bad output-capacity eval: sharding выключен, набор `47 TC / 65 OBL` блокируется до live; `attempts/` не создан.
- Corrected eval: `4` fresh-session shards `12/12/12/11`, union полный, пересечений нет, deterministic merge предшествует одному reviewer.

## Полный suite

Полный запуск завершился как `951 passed, 1 skipped, 4 failed`. Два failures, внесённые текущей правкой (output-schema probe и instruction-context headroom), исправлены и вошли в последующий зелёный focused run `110 passed`. Два оставшихся failures относятся к известному инфраструктурному долгу: отсутствует tracked fixture directory `tests/fixtures/agent-artifacts/ui-evidence-policy`; они не исполняют V6 runner, compiler или Personal Data package.

## V6 package и границы

- Package: 42 atoms, 65 obligations, 47 уникальных TC, `GAP-001..003`, `DICT-001`.
- Writer prompt budgets: `53 329`, `52 412`, `56 593`, `48 571` из `131 072` bytes.
- Reviewer conservative context estimate: `115 831 / 196 608` bytes.
- Reviewer output estimate: `18 688 / 65 536` bytes; bounded schema: `1 690` bytes.
- Dispatcher dry-run выбрал verified `exec`, contract v2, без SDK fallback.
- V6 attempts отсутствуют; live не запускался.
- V5 stage package SHA-256 сохранён: `668d906f8ae31e74d95b9a43a01e2824aae432a5fa9af8e2598b343d2ebc330c`.
- FT-first baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.
- Production shadow отсутствует.

Решение: V6 готов к checkpoint-коммиту. Live разрешается только после существования checkpoint и повторной проверки чистоты целевой области.
