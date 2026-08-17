---
name: ft-test-case-writer
description: Материализует тестовые данные, создаёт matrix и canonical TC.
---

# FT Test Case Writer

До работы прочитай `AGENTS.md`, `references/runtime/session-topology.md`, `references/runtime/test-data-fixtures.md`, `references/runtime/test-design-profiles.md`, `references/runtime/test-design-matrix.md`, `references/runtime/test-case-runtime.md` и `references/runtime/review-record.md`. До чтения handoff проверь, что текущая сессия зарегистрирована writer-ом выбранного scope: `runtime_session_registry.py verify --through writer --scope <scope> --expected-role writer --expected-thread-id <own-threadId>`. Matrix, TC и обе разрешённые revision выполняй только в этой writer-сессии.

## Fixture gate

1. Прочитай `test-data-plan.md`.
2. Найди локальные fixtures; при необходимости материализуй fixture фактического provider-а и запиши `work/test-data/<scope>/fixtures/fixture-catalog.json` с конкретными runtime literals. Если provider — DaData, используй `scripts/capture_dadata_fixture.py`, а не описание будущего запроса.
3. Если integration fixture нельзя получить, не заменяй её placeholder-текстом. Оставь обязанность в `coverage-gaps.md` и вопросе к БА.
4. Запусти `scripts/validate_fixture_catalog.py`.

## Matrix

Создай `work/practical/<scope>/test-design-matrix.md` и примени профиль к каждой строке. В `Источник требования` сохрани `SR-*` каждой покрываемой строки инвентаря и её первичные коды/строки ФТ. Неразрешённые обязанности сохрани отдельными строками: их `ID` совпадает с `GAP-*` из `coverage-gaps.md`, а решение равно `coverage-gap`. Запусти `python scripts/validate_runtime_matrix.py <matrix> --source-inventory <source-row-inventory.md> --coverage-gaps <coverage-gaps.md>`. Не создавай canonical TC до независимого `matrix-accepted`, SHA-256 которого совпадает с текущей matrix по `scripts/validate_runtime_review.py`.

## Canonical TC

После проверки актуального `matrix-accepted` создай `test-cases/<section>-<scope>.md` по `references/runtime/test-case-runtime.md`. В `Трассировка` каждого TC укажи исполнимую `M-*` строку принятой матрицы и повтори её первичные коды/строки ФТ. Проверь файл командой `python scripts/validate_runtime_tc.py <test-cases.md> --matrix <test-design-matrix.md>`. Перед передачей в review вручную сверь каждое интеграционное значение в TC с `runtime_data` соответствующей fixture: в TC идут литералы, не идентификатор fixture и не описание snapshot. После revision TC снова запускай validator; прежний TC review после изменения считается устаревшим.

Не создавай internal IDs, gaps, fixtures или просьбы о данных в production TC. Не выполняй больше одной revision без нового решения пользователя и не создавай для revision новую writer-сессию.
