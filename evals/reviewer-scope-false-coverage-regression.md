# Regression eval: reviewer must reject false coverage through excluded scope artifacts

## Цель

Этот eval проверяет, что `ft-test-case-reviewer` не принимает test-case set как покрытый, если writer закрывает integration atom через артефакт, явно исключенный из scope.

Практический источник regression: набор по разделу `Сведения о занятости`, где `job:*` значения сначала были ошибочно покрыты через `Анкету клиента`, хотя `Анкета клиента` была исключена границами набора.

## Как использовать

1. Передать reviewer-у блок `Writer Artifacts Under Review`.
2. Запустить review в режиме `test-design`.
3. Сравнить ответ с `Expected Reviewer Output`.
4. Считать regression, если reviewer подписывает `ATOM-013B` как covered или предлагает молча расширить текущий scope.

## Eval Case 13 - integration atom falsely covered through excluded scope artifact

**Requirement Source:**

- `REQ-013`: Поле `Организация` интегрировано с DaData: пользователь может выбрать найденную организацию из списка.
- `REQ-013.1`: После выбора организации система предзаполняет `job: orgName`, `job: orgINN` и `job: orgAddress` в `Анкете клиента` и контракте СПР.
- `SCOPE-013`: Текущий набор покрывает только раздел `Сведения о занятости`. Раздел `Анкета клиента` и контракт СПР исключены из scope.

**Writer Artifacts Under Review:**

```md
## Scope boundaries

В набор входят только поля раздела `Сведения о занятости`.
В набор не входят раздел `Анкета клиента`, печатные формы и контракт СПР.

## Atomic Requirements Ledger

| atom_id | req_id | field_or_block | condition | atomic_statement | expected_behavior | coverage_status | gap_note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-013A` | `REQ-013` | `Организация` | `при поиске организации` | Поле интегрировано с DaData | Пользователь может выбрать найденную организацию из списка DaData. | `covered` | - |
| `ATOM-013B` | `REQ-013.1` | `Анкета клиента / контракт СПР` | `после выбора организации` | Выбор организации предзаполняет `job: orgName`, `job: orgINN`, `job: orgAddress` | Значения `job:*` предзаполнены в Анкете клиента и контракте СПР. | `covered` | - |

## Test-design applicability matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| integration | yes | REQ-013, REQ-013.1 | DaData affects organization selection and `job:*` values | ATOM-013A, ATOM-013B | TC-EVAL-013A, TC-EVAL-013B | - |

## TC-EVAL-013A
**Название:** Выбор организации из списка DaData
**Приоритет:** High
**Тип:** UI
**Шаги:**
1. Открыть раздел `Сведения о занятости`.
2. Ввести часть наименования организации в поле `Организация`.
3. Выбрать найденную организацию из списка DaData.
**Итоговый ожидаемый результат:** Выбранная организация отображается в поле `Организация`.
**Ссылка на ФТ:** `REQ-013`; `ATOM-013A`

## TC-EVAL-013B
**Название:** Предзаполнение job-полей после выбора организации
**Приоритет:** High
**Тип:** Integration
**Шаги:**
1. Открыть раздел `Сведения о занятости`.
2. Выбрать организацию из списка DaData.
3. Открыть раздел `Анкета клиента`.
4. Проверить значения `job: orgName`, `job: orgINN`, `job: orgAddress`.
**Итоговый ожидаемый результат:** В `Анкете клиента` значения `job:*` предзаполнены данными выбранной организации.
**Ссылка на ФТ:** `REQ-013.1`; `ATOM-013B`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `scope`
- `coverage_dimension`: `integration`
- `test_case_id`: `TC-EVAL-013B` или set-level finding
- Finding должен указать, что `TC-EVAL-013B` проверяет `Анкету клиента`, хотя `SCOPE-013` явно исключает этот раздел.
- Finding должен указать false coverage: `ATOM-013B` не должен иметь `coverage_status=covered` в текущем наборе, если единственный pass/fail artifact находится вне scope.
- Required change должен требовать оставить `TC-EVAL-013A` как исполнимую проверку текущего поля, а `ATOM-013B` перевести в `unclear` / `GAP-*` либо вынести в отдельный scope по `Анкете клиента` / контракту СПР.
- Reviewer не должен предлагать расширить текущий scope молча, добавлять неподтвержденный ручной артефакт контракта СПР или считать `job:*` covered через проверку выбора организации в текущем поле.

## Pass criteria

- Reviewer выдает blocking/error finding по `scope` или `coverage`.
- Finding явно связывает проблему с `SCOPE-013`.
- `ATOM-013B` требует перевода в `unclear` / `GAP-*` или вынесения в отдельный scope.
- `TC-EVAL-013A` не помечается дефектным только из-за того, что `job:*` остается вне scope.

## Fail criteria

- Reviewer считает `ATOM-013B` covered.
- Reviewer принимает `TC-EVAL-013B` без замечаний.
- Reviewer предлагает просто добавить шаги по `Анкете клиента` в текущий набор, не отметив нарушение scope.
- Reviewer не различает наблюдаемую проверку выбора организации в текущем поле и ненаблюдаемое в текущем scope предзаполнение `job:*`.
