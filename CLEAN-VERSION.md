# FT Test Case Agent clean-version

## Текущий маршрут

Новые scope ФТ используют **compact practical route v0.9**: одноразовую
dependency-closed валидацию scope, явного владельца blocker, условный review
матрицы и неизменяемый manifest каждого независимого review. `practical-v0.8`
сохранён только для уже начатой legacy-работы.

## Базовая сборка

- source worktree: `C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2-practical-route-v0.8-partners-v1-clean`
- source branch: `codex/practical-route-v0.8-partners-v1-clean`
- source commit: `16443799858c6c9680379256e4b63cec454525f1`

Назначение:

- чистая рабочая версия агента для написания тест-кейсов по compact practical route v0.9;
- без исходных ФТ, рабочих артефактов, benchmark/eval-наборов и старых release bundle.

Включено:

- `AGENTS.md`
- `README.md`, `CONTRIBUTING.md`
- `pyproject.toml`, `uv.lock`
- `skills/`
- `references/`
- `scripts/`
- `test_case_agent/`
- минимальные regression tests для practical-route governance

`scripts/` в clean-version намеренно сокращён: оставлены только общие runtime/helper scripts для environment probe, instruction resolving, markdown/artifact writing, source JSON utilities, DaData fixture verification, validation and controlled review-cycle orchestration. AutoFin-specific, benchmark, canary, replay and historical debug helper scripts исключены.

Исключено:

- `fts/`
- `evals/`
- `release/`
- `work/`
- `output/`
- untracked локальные материалы, включая `_delayed-ba-answers/`

Маршрут по умолчанию для нового scope:

1. пакетный source manifest, связывающий DOCX, XHTML и доступный PDF;
2. обязательства, нормализованные из источников;
3. компактная русскоязычная матрица тест-дизайна;
4. review матрицы только для детерминированно сложного scope;
5. canonical test cases;
6. финальный независимый review в отдельной верхнеуровневой Codex-сессии;
7. не более одной целевой revision writer-а и одного нового финального review.

Не используется по умолчанию:

- benchmark
- sharding
- semantic bridge
- source_assertion_review
- immutable `ft-agent run`
- source-qualified iteration
