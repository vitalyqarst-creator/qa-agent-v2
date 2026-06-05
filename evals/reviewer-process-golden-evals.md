# Reviewer Process Golden Evals

## Назначение

Этот eval-набор проверяет не стиль ответа reviewer-а, а способность процесса `ft-test-case-reviewer` находить blocking defects в наборе тест-кейсов. Используй его для A/B проверки изменений в `reviewer.full_existing_cases` и `reviewer.semantic_traceability_test_design`.

Каждый case должен выполняться как замороженный input fixture: reviewer получает source excerpt, writer artifacts и canonical TC excerpt, затем возвращает structured findings. Eval считается failed, если reviewer подписывает набор с blocking defect или возвращает только formatting/style findings.

## Метрики

| metric | pass rule |
| --- | --- |
| `known_defect_recall` | Все listed blocking defects обнаружены. |
| `blocking_miss_count` | `0` для каждого case. |
| `incorrect_signoff` | `no` для каждого case с `severity = error`. |
| `finding_actionability` | Каждый expected finding содержит `required_change`, `source_reference`, `coverage_dimension` и `traceability_ref`, когда применимо. |
| `false_positive_control` | Reviewer не требует поведения, которого нет в source. |

## Eval Case GP-001 - Lost Requirement Code

**Failure Class:** `lost-requirement-code`

**Source Excerpt:**

- `GSR 126`: Поле `kladr` передается во внутреннюю модель после выбора адреса.

**Writer Artifacts Under Review:**

```md
| atom_id | req_id | atomic_statement | covered_by_tc | coverage_status |
| --- | --- | --- | --- | --- |
| ATOM-009 | section-19 | `kladr` заполнен в модели данных | TC-GP-001 | covered |
```

```md
## TC-GP-001
**Название:** Заполнение адреса
**Итоговый ожидаемый результат:** В модели данных заполнено поле `kladr`.
**Ссылка на ФТ:** section-19
```

**Expected Reviewer Output:**

- `review_mode`: `traceability`
- `severity`: `error`
- `category`: `traceability`
- `coverage_dimension`: `traceability`
- `traceability_ref`: `ATOM-009`
- Finding указывает, что source-backed code `GSR 126` потерян в `req_id` / TC links.
- Required change требует восстановить `GSR 126` или оформить конкретный `GAP-*` / `unclear`, если поведение невозможно проверить вручную.

## Eval Case GP-002 - Gap Promoted To Covered Without Artifact

**Failure Class:** `fake-internal-coverage`

**Source Excerpt:**

- Previous revalidation: `ATOM-010` / `CorrelationId` был `gap`, потому что разрешенный observable artifact не указан.

**Writer Artifacts Under Review:**

```md
| atom_id | req_id | atomic_statement | covered_by_tc | coverage_status | gap_note |
| --- | --- | --- | --- | --- | --- |
| ATOM-010 | GSR 127 | `CorrelationId` передан во внешний сервис | TC-GP-002 | covered | - |
```

```md
## TC-GP-002
**Название:** Передача CorrelationId
**Шаги:** 1. Сохранить заявку.
**Итоговый ожидаемый результат:** `CorrelationId` передан во внешний сервис.
```

**Expected Reviewer Output:**

- `review_mode`: `traceability`
- `severity`: `error`
- `category`: `expected-result`
- `coverage_dimension`: `integration`
- `traceability_ref`: `ATOM-010`
- Finding указывает, что prior `gap` стал `covered` без нового source / observable artifact.
- Required change требует вернуть `gap` / `unclear` или указать разрешенный artifact проверки.

## Eval Case GP-003 - Applicability Matrix Linked To Non-Covering TC

**Failure Class:** `applicability-linked-tc-drift`

**Source Excerpt:**

- `REQ-301`: Backend должен отклонять прямой payload без `ИНН`.

**Writer Artifacts Under Review:**

```md
| dimension | applicable | source_ref | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- |
| api-server-validation | yes | REQ-301 | ATOM-301 | TC-GP-003 | - |
```

```md
## TC-GP-003
**Название:** ИНН обязателен в UI
**Шаги:** 1. Оставить поле `ИНН` пустым. 2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Сохранение через UI не происходит.
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `coverage`
- `coverage_dimension`: `api-server-validation`
- Finding указывает, что linked TC проверяет UI-flow, а не direct/API payload bypass.
- Required change требует отдельный backend/API bypass TC или `GAP-*`, если artifact проверки недоступен.

## Eval Case GP-004 - Unsupported UI Mechanism

**Failure Class:** `unsupported-ui-mechanism`

**Source Excerpt:**

- `REQ-402`: При недопустимом ИНН значение не сохраняется.

**Test Case Under Review:**

```md
## TC-GP-004
**Шаги:** 1. Ввести `123`. 2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Поле подсвечено красным, отображается ошибка `Некорректный ИНН`, кнопка `Сохранить` становится disabled.
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `expected-result`
- `coverage_dimension`: `expected-result`
- Finding указывает, что цвет, точный текст ошибки и disabled-state не подтверждены source.
- Required change оставляет только source-backed no-save oracle или переводит UI reaction в `unclear`.

## Eval Case GP-005 - Dictionary Closed Set Not Covered

**Failure Class:** `dictionary-closed-set-missing`

**Source Excerpt:**

- `REQ-501`: Поле `Тип документа` содержит значения `Паспорт`, `ВНЖ`, `Военный билет`.

**Writer Artifacts Under Review:**

```md
## TC-GP-005
**Название:** Выбор паспорта
**Шаги:** 1. Открыть список `Тип документа`. 2. Выбрать `Паспорт`.
**Итоговый ожидаемый результат:** Значение `Паспорт` выбрано.
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `warning` или `error`, если source явно задает closed set.
- `category`: `coverage`
- `coverage_dimension`: `table-list`
- Finding указывает, что набор не проверяет полный состав списка и отсутствие лишних значений.
- Required change требует list-composition TC со всеми source values или `GAP-*` по закрытости перечня.

## Eval Case GP-006 - Positive And Negative Branches Merged

**Failure Class:** `positive-negative-merge`

**Source Excerpt:**

- `REQ-601`: Поле `Сумма` обязательно и должно быть больше `0`.

**Test Case Under Review:**

```md
## TC-GP-006
**Шаги:** 1. Оставить `Сумма` пустой и нажать `Сохранить`. 2. Ввести `1000` и нажать `Сохранить`.
**Итоговый ожидаемый результат:** Пустое значение не сохраняется, а `1000` сохраняется.
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `atomarity`
- `coverage_dimension`: `atomarity`
- Finding указывает, что negative и positive branches объединены в одном TC.
- Required change требует разделить на отдельный negative TC и positive TC либо явно оформить recovery scenario, который не заменяет атомарные проверки.

## Eval Case GP-007 - False Gap Hiding Source-Backed Behavior

**Failure Class:** `false-gap`

**Source Excerpt:**

- `REQ-701`: После удаления черновик отсутствует в списке черновиков.

**Writer Artifacts Under Review:**

```md
| gap_id | source_ref | blocked_part | handling |
| --- | --- | --- | --- |
| GAP-701 | REQ-701 | Поведение удаления не определено | Оставить весь сценарий как gap |
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `coverage`
- `coverage_dimension`: `scenario-use-case`
- Finding указывает, что source уже задает observable oracle: черновик отсутствует в списке.
- Required change требует покрыть проверяемую UI-часть TC и оставить `GAP-*` только на реально недостающую fixture/mechanism часть, если она есть.

## Run Report Template

```md
## Reviewer Golden Eval Run

- `eval_suite`: `evals/reviewer-process-golden-evals.md`
- `process_under_test`: `reviewer.full_existing_cases | reviewer.semantic_traceability_test_design`
- `artifact_version`: `<git/tree/snapshot id>`
- `known_defects_found`: `<N/M>`
- `blocking_misses`: `<N>`
- `incorrect_signoff`: `yes|no`
- `false_positives`: `<N + short ids>`
- `verdict`: `pass | partial | fail`
```
