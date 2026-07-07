# Review Findings Format

Канонический structured findings artifact хранится в Markdown и используется для handoff от `ft-test-case-reviewer` к `ft-test-case-writer`.

Все человекочитаемые поля findings artifact и writer response artifact должны быть заполнены на русском языке. Служебные имена полей и допустимые enum-значения сохраняются в каноническом виде, как указано в этом формате.

## Findings Artifact

Каждый finding должен быть отдельным блоком и включать:

- `finding_id`
- `review_mode`
- `severity`
- `category`
- `coverage_dimension`
- `test_case_id` или `coverage_gap`
- `traceability_ref`, если `review_mode = traceability`
- `title`
- `problem`
- `evidence`
- `required_change`
- `source_reference`
- `status`

### Допустимые значения

- `review_mode` = `traceability | structure | test-design`
- `severity` = `error | warning | info`
- `category` = `coverage | atomarity | traceability | expected-result | scope | duplication | format | structure | test-design | clarification-question-quality`
- `coverage_dimension` = `role-permission | status-lifecycle | decision-table | pairwise | boundary | equivalence | dependency | conditional-visibility | api-server-validation | integration | security | async | persistence | table-list | file-upload | calculation | numeric | date-time | length | scenario-use-case | performance | reliability | compatibility | usability | accessibility-ui | traceability | expected-result | atomarity | format | scope | other`
- `status` = `open`

## Дополнительные требования по режимам

- Для `traceability` finding обязательно указывать `traceability_ref`: `ATOM-*` из traceability matrix или `coverage_gap:<short-id>`, если строки матрицы еще нет. Не используй `req_id` как единственный ключ: один requirement id может соответствовать нескольким atomic statements.
- Для `structure` finding обязательно привязывать замечание к `test_case_id` или к месту в наборе. Нарушения группировки по функциональности/блоку/элементу и несквозная нумерация `TC-*` оформляются как blocking structure finding до sign-off.
- Для `test-design` finding обязательно указывать пропущенный тип проверки в `required_change` или `evidence`:
  - `positive`
  - `negative`
  - `boundary`
  - `equivalence`
  - `dependency`
- Для `test-design` finding и для категорий `coverage`, `test-design`, `expected-result`, `scope` обязательно указывать `coverage_dimension`. Используй `other` только если применимая dimension отсутствует в словаре, и объясни это в `problem`.

## Рекомендуемый шаблон findings artifact

```md
## Review Findings

### FINDING-001
**Review Mode:** structure
**Severity:** error
**Category:** atomarity
**Coverage Dimension:** atomarity
**Test Case ID:** TC-DEMO-001
**Traceability Ref:** -
**Title:** Невалидная комбинация двух проверок в одном тест-кейсе

**Problem:** Один тест-кейс одновременно проверяет обязательность поля и ограничение по допустимым символам.

**Evidence:**
- В кейсе объединены две независимые проверки.
- Нарушено правило `Один тест-кейс = одна проверка`.

**Required Change:** Разделить комбинированный тест-кейс на два отдельных атомарных кейса.

**Source Reference:** `ФТ 2`; `2.1.1.1.1.1.2`; `Поле «ФИО клиента»`

**Status:** open
```

## Writer Response Artifact

Writer response artifact фиксирует, как `ft-test-case-writer` обработал findings reviewer-а.

Каждый response block должен включать:

- `finding_id`
- `resolution_status`
- `change_summary`
- `affected_test_case_ids`
- `affected_traceability_refs`, если исходный finding содержит `traceability_ref`

### Допустимые значения

- `resolution_status` = `fixed | not-fixed-scope | needs-clarification`

Writer response должен использовать именно эти служебные поля и enum-значения. Таблицы, свободный summary, русскоязычные аналоги служебных полей вроде `Статус`, а также нестандартные значения наподобие `fixed_with_gap_retained` не заменяют канонический response block и считаются структурной ошибкой во втором review.

Если writer закрывает traceability finding, response должен ссылаться на те же `ATOM-*` или `coverage_gap:<short-id>`, что и исходный finding, либо явно объяснить, почему ссылка изменилась из-за split/merge атомарного утверждения.

## Рекомендуемый шаблон writer response artifact

```md
## Writer Response

### FINDING-001
**Resolution Status:** fixed
**Change Summary:** Комбинированный кейс разделен на два отдельных кейса по обязательности и по допустимым символам.

**Affected Test Case IDs:**
- `TC-DEMO-001`
- `TC-DEMO-002`

**Affected Traceability Refs:**
- `-`
```

## Правила использования

- Reviewer обязан сортировать findings по severity: сначала `error`, затем `warning`, затем `info`.
- Reviewer не должен возвращать finding без `review_mode`.
- Reviewer не должен возвращать finding без `required_change`. Если проблему нельзя свести к конкретному проверяемому исправлению, не оформляй ее как finding.
- Reviewer не должен возвращать finding без `test_case_id` или `coverage_gap`.
- Reviewer не должен возвращать `test-design`, `coverage`, `expected-result` или `scope` finding без `coverage_dimension`.
- Reviewer не должен возвращать `traceability` finding без `traceability_ref`.
- Writer обязан дать response на каждый finding предыдущего раунда.
- Writer response на `traceability` finding должен сохранять связь с исходным `traceability_ref`, чтобы второй review мог проверить закрытие gap по матрице, а не по текстовому описанию.
- Если writer не исправляет finding, он обязан выбрать только один статус: `not-fixed-scope` или `needs-clarification`.
- Во втором review reviewer должен сверять не только обновленные тест-кейсы, но и writer response artifact.
- Если writer response artifact не содержит обязательные canonical fields или использует недопустимые enum-значения, reviewer фиксирует blocking `structure` / `format` finding.
