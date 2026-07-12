# Следующая итерация: оптимизация standard prepared route

Используй `agent-architecture-auditor`, затем `ft-test-case-iteration`. Не изменяй FT-first baseline и не запускай новый live cycle до прохождения unit tests.

## Цель

Снизить стоимость `standard-required` writer/reviewer без потери 12/12 coverage и без ослабления GAP-001.

## Обязательные работы

1. Добавить preflight dispatcher config validation для profile-specific writer/reviewer command-budget floors до создания cycle-owned outputs.
2. Исследовать V3 `stage-input.json`, metrics и events; отделить обязательный context от повторно переданных/прочитанных файлов.
3. Ввести bounded prepared-standard resolver manifest: writer получает compiled evidence и минимальный instruction set; reviewer — immutable package, draft, deterministic reports и только необходимые canonical rules.
4. Запретить нерелевантные repo-wide diagnostics (`git status` и аналогичные) внутри prepared stages, если они не нужны контракту результата.
5. Покрыть изменения unit tests и validate-only replay.
6. Только после этого создать новый immutable cycle для того же scope. Acceptance: reviewer accepted, 12/12 obligations, clean overlap, baseline absent; uncached tokens и command executions должны существенно снизиться относительно V3.

## Baseline метрик

- V3: 386.907 с; 1 690 384 total tokens; 208 136 uncached input tokens; 74 commands.
- Draft SHA-256: `4794e6168bea183b7d40b8fc03d7736c87580a20c05dde6f4efd637c5c615fe9`.
