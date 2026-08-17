---
name: ft-test-case-writer
description: Материализует тестовые данные, создаёт matrix и canonical TC.
---

# FT Test Case Writer

До работы прочитай `AGENTS.md`, `references/runtime/test-data-fixtures.md`, `references/runtime/test-design-profiles.md`, `references/runtime/test-design-matrix.md`, `references/runtime/test-case-runtime.md` и `references/runtime/review-record.md`.

## Fixture gate

1. Прочитай `test-data-plan.md`.
2. Найди локальные fixtures; при необходимости материализуй fixture фактического provider-а и запиши `work/test-data/<scope>/fixtures/fixture-catalog.json` с конкретными runtime literals. Если provider — DaData, используй `scripts/capture_dadata_fixture.py`, а не описание будущего запроса.
3. Если integration fixture нельзя получить, не заменяй её placeholder-текстом. Оставь обязанность в `coverage-gaps.md` и вопросе к БА.
4. Запусти `scripts/validate_fixture_catalog.py`.

## Matrix

Создай `work/practical/<scope>/test-design-matrix.md` и примени профиль к каждой строке. Неразрешённые обязанности сохрани как `coverage-gap`. Запусти `scripts/validate_runtime_matrix.py`. Не создавай canonical TC до независимого `matrix-accepted`, SHA-256 которого совпадает с текущей matrix по `scripts/validate_runtime_review.py`.

## Canonical TC

После проверки актуального `matrix-accepted` создай `test-cases/<section>-<scope>.md` по `references/runtime/test-case-runtime.md` и проверь его `scripts/validate_runtime_tc.py`. Перед передачей в review вручную сверь каждое интеграционное значение в TC с `runtime_data` соответствующей fixture: в TC идут литералы, не идентификатор fixture и не описание snapshot. После revision TC снова запускай validator; прежний TC review после изменения считается устаревшим.

Не создавай internal IDs, gaps, fixtures или просьбы о данных в production TC. Не выполняй больше одной revision без нового решения пользователя.
