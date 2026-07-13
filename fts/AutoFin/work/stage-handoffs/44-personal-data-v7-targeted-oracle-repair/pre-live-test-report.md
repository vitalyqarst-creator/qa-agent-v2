# V7 Pre-Live Test Report

## Целевые проверки

- `tests/test_prepared_workflow_compiler.py` + `tests/test_codex_exec_review_cycle_runner.py`: `137 passed`; вместе с instruction-context headroom regression: `138 passed`.
- Prepared oracle bad eval блокируется до attempt; corrected evidence-record oracle проходит.
- Targeted repair regression доказывает exact target set, runner-owned splice, byte preservation нецелевой секции и две fresh sessions.
- Extra TC в replacement блокирует reviewer; repair-input hash drift отклоняется.
- `reviewer.session_prepared_semantic` instruction budget regression после компактизации references: `pass`, headroom `20.0 KiB`.

## Полный suite

Полный запуск: `958 passed, 1 skipped, 3 failed`. Один внесённый failure по instruction-context headroom исправлен и прошёл focused regression. Два оставшихся failures — унаследованный инфраструктурный долг: отсутствует tracked fixture directory `tests/fixtures/agent-artifacts/ui-evidence-policy`; они не исполняют V7 runner/compiler и не затрагивают Personal Data package.

## V7 package и границы

- Package: `42 atoms / 65 obligations / 47 TC`, `GAP-001..003`, `DICT-001`.
- Oracle preflight: `65 checked / 0 findings`.
- Repair: `4 target TC / 43 preserved TC`; одна writer session вместо четырёх full-set shards.
- Reviewer: `65` obligations; output/context estimates ниже limits.
- Dispatcher dry-run выбрал verified `exec`, contract v2, без SDK fallback.
- Artifact validator для активной H44-области: `0 errors / 0 warnings / 3 inherited source-quality info`.
- V7 attempts и `cycle-state.yaml` отсутствуют; production shadow отсутствует.
- FT-first baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.

Решение: V7 готов к checkpoint-коммиту. Live разрешается только после push и повторной проверки production boundaries.
