# FT Test Case Agent clean-version

Источник сборки:

- source worktree: `C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2-practical-route-v0.8-partners-v1-clean`
- source branch: `codex/practical-route-v0.8-partners-v1-clean`
- source commit: `16443799858c6c9680379256e4b63cec454525f1`

Назначение:

- чистая рабочая версия агента для написания тест-кейсов по practical route v0.8;
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

Исключено:

- `fts/`
- `evals/`
- `release/`
- `work/`
- `output/`
- untracked локальные материалы, включая `_delayed-ba-answers/`

Default route:

1. source locator
2. scope analyzer
3. test-design matrix
4. writer
5. independent reviewer
6. one bounded revision when needed
7. final baseline

Не default:

- benchmark
- sharding
- semantic bridge
- source_assertion_review
- immutable `ft-agent run`
- source-qualified iteration
