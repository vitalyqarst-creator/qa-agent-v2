# Contributing

Этот файл фиксирует инженерные договоренности проекта, которые должны переживать отдельные сессии и не зависеть от памяти агента.

## Базовый workflow

Перед изменениями:

```powershell
uv sync
```

После изменений запускай тесты через каноническую точку входа:

```powershell
python scripts/run_tests.py
```

## Запуск тестов

Основная команда:

```powershell
python scripts/run_tests.py
```

Raw-эквивалент для полного suite:

```powershell
python -m unittest discover -s tests
```

Почему не `python -m unittest`:

- в этом репозитории обычный вызов может показать `Ran 0 tests`;
- `discover -s tests` гарантирует реальный прогон suite;
- helper script делает этот запуск каноническим и не заставляет помнить детали руками.

## Поддержка test-layer

- если меняется repo-level contract, обновляй не только документы, но и соответствующие `unittest`-проверки;
- новые стабильные инженерные правила фиксируй в `README.md`, `CONTRIBUTING.md` или исполнимом script entrypoint;
- не записывай repo-level команды запуска тестов в `AGENTS.md`, если это не policy, а инженерный workflow.

## Versioning test-case artifacts

- Для каждого scope поддерживай один канонический текущий файл в `fts/<ft-slug>/test-cases/`.
- Промежуточные версии reviewer/writer loop не создают новый канонический файл, а сохраняются как snapshots в `fts/<ft-slug>/work/review-loops/<scope-slug>/snapshots/`.
- Канонический policy по versioning test-case artifacts см. в `references/qa/test-case-versioning-policy.md`.
