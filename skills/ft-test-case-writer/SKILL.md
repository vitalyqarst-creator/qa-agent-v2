---
name: ft-test-case-writer
description: Материализует тестовые данные, создаёт matrix и canonical TC.
---

# FT Test Case Writer

До работы прочитай `AGENTS.md`, `references/runtime/test-data-fixtures.md`, `references/runtime/test-design-matrix.md` и `references/runtime/test-case-runtime.md`.

## Fixture gate

1. Прочитай `test-data-plan.md`.
2. Найди локальные fixtures; при необходимости материализуй provider fixture и запиши `work/test-data/<scope>/fixtures/fixture-catalog.json` с конкретными runtime literals. Для DaData используй `scripts/capture_dadata_fixture.py`, а не описание будущего запроса.
3. Если integration fixture нельзя получить, не заменяй её placeholder-текстом. Оставь обязанность в `coverage-gaps.md` и вопросе к БА.
4. Запусти `scripts/validate_fixture_catalog.py`.

## Matrix

Создай `work/practical/<scope>/test-design-matrix.md` только для обязанностей с данными и наблюдаемым результатом. Не создавай canonical TC до независимого matrix verdict `matrix-accepted`.

## Canonical TC

После `matrix-accepted` создай `test-cases/<section>-<scope>.md` по `references/runtime/test-case-runtime.md` и проверь его `scripts/validate_runtime_tc.py`. Перед выпуском вручную сверь каждое интеграционное значение в TC с `runtime_data` соответствующей fixture: в TC идут литералы, не идентификатор fixture и не описание snapshot.

Не создавай internal IDs, gaps, fixtures или просьбы о данных в production TC. Не выполняй больше одной revision без нового решения пользователя.
