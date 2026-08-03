# Contributing

Этот файл фиксирует инженерные договоренности проекта, которые должны переживать отдельные сессии и не зависеть от памяти агента.

## Базовый workflow

Перед изменениями:

```powershell
uv sync
```

После изменений запускай тесты через каноническую точку входа:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py
```

## Запуск тестов

Основная команда:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py
```

Raw `unittest discover` не является каноническим full-run режимом: он запускает тяжелый artifact-validator suite монолитно. Helper script делает controlled discovery для быстрых test modules и отдельно запускает artifact-validator через sharded wrapper.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Для быстрого agent-layer прогона без тяжелого validator-а используй:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py --suite agent-layer-fast
```

Для тяжелого artifact-validator suite используй канонический sharded-режим:

```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py --suite artifact-validator-sharded
```

Он запускает полное покрытие через 7 shard-ов и заменяет монолитный запуск `.\.venv\Scripts\python.exe -m unittest tests.test_agent_artifact_validator`. Для CI fan-out запускай отдельные shard index: `.\.venv\Scripts\python.exe scripts/run_tests.py --suite artifact-validator --shard-count 7 --shard-index 1`.

## Поддержка test-layer

- если меняется repo-level contract, обновляй не только документы, но и соответствующие `unittest`-проверки;
- новые стабильные инженерные правила фиксируй в `README.md`, `CONTRIBUTING.md` или исполнимом script entrypoint;
- не записывай repo-level команды запуска тестов в `AGENTS.md`, если это не policy, а инженерный workflow.

## Versioning test-case artifacts

- Для каждого scope поддерживай один канонический текущий файл в `fts/<ft-slug>/test-cases/`.
- Промежуточные версии reviewer/writer loop не создают новый канонический файл, а сохраняются как snapshots в `fts/<ft-slug>/work/review-loops/<scope-slug>/snapshots/`.
- Канонический policy по versioning test-case artifacts см. в `references/qa/test-case-versioning-policy.md`.
