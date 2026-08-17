---
name: ft-test-case-writer
description: Проектирует тестовые данные и готовность исполнения, создаёт matrix и canonical TC.
---

# FT Test Case Writer

До работы прочитай `AGENTS.md`, `references/runtime/session-topology.md`, `references/runtime/test-data-fixtures.md`, `references/runtime/test-design-profiles.md`, `references/runtime/test-design-matrix.md`, `references/runtime/test-case-runtime.md` и `references/runtime/review-record.md`. До чтения handoff проверь, что текущая сессия зарегистрирована writer-ом выбранного scope: `runtime_session_registry.py verify --through writer --scope <scope> --expected-role writer --expected-thread-id <own-threadId>`. Matrix, TC и обе разрешённые revision выполняй только в этой writer-сессии.

## Подготовка данных

1. Прочитай `test-data-plan.md`. Артефакты analyzer-а в `work/stage-handoffs/<scope>/` доступны writer-у только для чтения: не изменяй inventory, scope brief, gaps, вопросы, план данных, prompt или их workflow state.
2. Для обычной стендовой сущности опиши конкретные значения и воспроизводимые действия создания/перевода в состояние. Отсутствие уже созданной записи, логина, URL или доступа к стенду означает `needs-test-data`, а не `coverage-gap`.
3. Для внешней интеграции найди или материализуй ответ фактического provider-а и запиши `work/test-data/<scope>/fixtures/fixture-catalog.json`. Если provider — DaData, используй `scripts/capture_dadata_fixture.py`, а не описание будущего запроса.
4. Если необходимые интеграционные литералы получить нельзя, не выдумывай их и не редактируй analyzer-owned gaps/questions. Останови передачу в TC-stage и сообщи controller `blocked-data-preparation` с точной причиной. Новый смысловой дефект источника возвращается controller-у для исходной analyzer-сессии.
5. Если catalog создан, запусти `scripts/validate_fixture_catalog.py`. Отсутствующий catalog не является ошибкой для scope без внешних ответов.

## Matrix

Создай `work/practical/<scope>/test-design-matrix.md` и соседний `workflow-state.yaml` по `references/runtime/test-design-matrix.md`; не сохраняй matrix в `stage-handoffs`. Примени профиль к каждой строке и отдельно укажи решение по покрытию и готовность исполнения. В `Источник требования` сохрани `SR-*` каждой покрываемой строки инвентаря и её первичные коды/строки ФТ. Неразрешённые из-за недостатка источника обязанности сохрани отдельными строками: их `ID` совпадает с `GAP-*` из `coverage-gaps.md`, решение равно `coverage-gap`, готовность — `blocked-observability`. Отсутствие стендовой привязки сохраняет решение `TC` и получает `needs-test-data`. Запусти `python scripts/validate_runtime_matrix.py <matrix> --source-inventory <source-row-inventory.md> --coverage-gaps <coverage-gaps.md>`. Не создавай canonical TC до независимого `matrix-accepted`, SHA-256 которого совпадает с текущей matrix по `scripts/validate_runtime_review.py`.

## Canonical TC

После проверки актуального `matrix-accepted` создай `test-cases/<section>-<scope>.md` по `references/runtime/test-case-runtime.md`. В `Трассировка` каждого TC укажи исполнимую `M-*` строку принятой матрицы и повтори её первичные коды/строки ФТ. Для `needs-test-data` всё равно укажи конкретные литералы и воспроизводимую подготовку; статус означает только отсутствие стендовой привязки. Проверь файл командой `python scripts/validate_runtime_tc.py <test-cases.md> --matrix <test-design-matrix.md>`. Перед передачей в review вручную сверь каждое интеграционное значение в TC с `runtime_data` соответствующей fixture: в TC идут литералы, не идентификатор fixture и не описание snapshot. Обнови writer-owned `workflow-state.yaml`. После revision TC снова запускай validator; прежний TC review после изменения считается устаревшим.

Не создавай internal IDs, gaps, fixtures или просьбы о данных в production TC. Не выполняй больше одной revision без нового решения пользователя и не создавай для revision новую writer-сессию.
