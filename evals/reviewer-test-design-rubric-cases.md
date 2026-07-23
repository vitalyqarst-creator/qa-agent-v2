# Evals рубрики review test-design

## Цель

Этот eval-набор проверяет, что `ft-test-case-reviewer` применяет `references/qa/test-design-review-rubric.md` достаточно жестко и предсказуемо.

Reviewer должен оценивать не стиль текста, а способность тест-кейса доказать требование. Для каждого кейса ниже ожидается structured finding или явное отсутствие finding.

## Как использовать

1. Передай reviewer-у один eval case как мини-набор входных данных.
2. Запусти review в режиме `test-design`.
3. Сравни результат с `Expected Reviewer Output`.
4. Если reviewer снижает severity или подписывает blocking defect, это regression в strictness.

## Eval Case 1 - ненаблюдаемый expected result

**Requirement Source:**

- `REQ-001`: После успешного сохранения заявки система отображает статус `Сохранена`.

**Test Case Under Review:**

```md
## TC-EVAL-001
**Название:** Сохранение заявки
**Цель:** Проверить сохранение заявки.
**Шаги:**
1. Заполнить обязательные поля заявки.
2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Система корректно обрабатывает заявку.
**Ссылка на ФТ:** `REQ-001`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `expected-result`
- `test_case_id`: `TC-EVAL-001`
- Finding должен указать, что expected result недостаточно наблюдаем для pass/fail.
- Required change должен требовать конкретный наблюдаемый статус `Сохранена`.

## Eval Case 2 - неподтвержденная точная UI-реакция

**Requirement Source:**

- `REQ-002`: При вводе недопустимого ИНН значение не должно сохраняться.

**Test Case Under Review:**

```md
## TC-EVAL-002
**Название:** Ошибка при недопустимом ИНН
**Шаги:**
1. Ввести `123` в поле `ИНН`.
2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Поле подсвечено красным, отображается текст ошибки `Некорректный ИНН`, кнопка `Сохранить` становится disabled.
**Ссылка на ФТ:** `REQ-002`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `expected-result`
- `test_case_id`: `TC-EVAL-002`
- Finding должен указать, что точный текст ошибки, цвет и disabled-state не подтверждены требованием.
- Concrete false-fail witness: реализация отклоняет сохранение недопустимого ИНН,
  но не показывает красную подсветку, точный текст и disabled-state. Такая
  реализация соответствует `REQ-002`, однако текущий TC ошибочно провалит её.
- Required change должен оставить только подтвержденное наблюдаемое поведение: недопустимое значение не сохраняется, либо пометить UI-реакцию как `unclear`.

## Eval Case 3 - проверяемое действие спрятано в предусловиях

**Requirement Source:**

- `REQ-003`: Пользователь может отменить черновик заявки.

**Test Case Under Review:**

```md
## TC-EVAL-003
**Название:** Отмена черновика
**Предусловия:**
- Открыт черновик заявки.
- Пользователь отменил черновик.
**Шаги:**
1. Открыть список заявок.
**Итоговый ожидаемый результат:** Черновик отсутствует в списке активных заявок.
**Ссылка на ФТ:** `REQ-003`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `test-design`
- `test_case_id`: `TC-EVAL-003`
- Finding должен указать, что проверяемое действие спрятано в предусловиях вместо шагов.
- Finding должен явно указать нарушение trigger fidelity: ни один шаг TC не
  выполняет проверяемое действие отмены.
- Concrete false-pass witness: операция отмены в продукте не работает, но
  fixture уже содержит отменённую заявку; единственный шаг просмотра списка
  проходит, хотя возможность пользователя отменить черновик не проверена.
- Required change должен требовать перенести отмену черновика в детерминированные шаги.

## Eval Case 4 - positive и negative ветки смешаны

**Requirement Source:**

- `REQ-004`: Поле `Сумма кредита` обязательно. Значение должно быть больше нуля.

**Test Case Under Review:**

```md
## TC-EVAL-004
**Название:** Проверка суммы кредита
**Шаги:**
1. Оставить поле `Сумма кредита` пустым и нажать `Сохранить`.
2. Ввести `100000` и нажать `Сохранить`.
**Итоговый ожидаемый результат:** Пустое значение не сохраняется, а значение `100000` сохраняется.
**Ссылка на ФТ:** `REQ-004`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `atomarity`
- `test_case_id`: `TC-EVAL-004`
- Finding должен указать, что positive и negative ветки смешаны в одном тест-кейсе.
- Required change должен требовать разделить кейс на отдельный negative case и отдельный positive case.

## Eval Case 5 - отсутствует negative branch, но основной positive case есть

**Requirement Source:**

- `REQ-005`: Поле `Код подразделения` принимает только цифры.

**Test Case Under Review:**

```md
## TC-EVAL-005
**Название:** Ввод цифрового кода подразделения
**Шаги:**
1. Ввести `123456` в поле `Код подразделения`.
2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Значение `123456` сохраняется.
**Ссылка на ФТ:** `REQ-005`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `warning`
- `category`: `coverage`
- `test_case_id`: `TC-EVAL-005`
- Finding должен указать, что отсутствует negative equivalence check для нецифрового ввода.
- Required change должен требовать добавить invalid non-digit input case.

## Eval Case 6 - over-splitting эквивалентных значений списка

**Requirement Source:**

- `REQ-006`: Поле `Тип документа` содержит значения `Паспорт`, `ВНЖ`, `Военный билет`.

**Test Case Under Review:**

```md
## TC-EVAL-006A
**Название:** Значение Паспорт в списке типов документа
**Шаги:** 1. Открыть список `Тип документа`.
**Итоговый ожидаемый результат:** В списке есть значение `Паспорт`.

## TC-EVAL-006B
**Название:** Значение ВНЖ в списке типов документа
**Шаги:** 1. Открыть список `Тип документа`.
**Итоговый ожидаемый результат:** В списке есть значение `ВНЖ`.

## TC-EVAL-006C
**Название:** Значение Военный билет в списке типов документа
**Шаги:** 1. Открыть список `Тип документа`.
**Итоговый ожидаемый результат:** В списке есть значение `Военный билет`.
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `warning`
- `category`: `duplication`
- `test_case_id`: `TC-EVAL-006A`, `TC-EVAL-006B`, `TC-EVAL-006C` или set-level finding
- Finding должен указать, что кейсы отличаются только значением списка и должны быть объединены в один list-composition case.
- Required change должен требовать сохранить все ожидаемые значения в одном кейсе, если отдельное значение не запускает отдельную бизнес-логику.

## Eval Case 7 - неподтвержденное missing behavior должно стать `unclear`

**Requirement Source:**

- `REQ-007`: При закрытии заявки пользователь указывает причину закрытия.

**Test Case Under Review:**

```md
## TC-EVAL-007
**Название:** Закрытие заявки без причины
**Шаги:**
1. Открыть заявку.
2. Очистить поле `Причина закрытия`.
3. Нажать `Закрыть заявку`.
**Итоговый ожидаемый результат:** Отображается ошибка `Укажите причину закрытия`.
**Ссылка на ФТ:** `REQ-007`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `expected-result`
- `test_case_id`: `TC-EVAL-007`
- Finding должен указать, что требование не задает точный текст ошибки и даже negative behavior недостаточно явно.
- Required change должен требовать либо сослаться на утвержденный источник negative behavior, либо пометить missing behavior как `unclear`.

## Eval Case 8 - приемлемый кейс без finding

**Requirement Source:**

- `REQ-008`: Если заявка имеет статус `Черновик`, пользователь может удалить ее. После удаления заявка отсутствует в списке черновиков.

**Test Case Under Review:**

```md
## TC-EVAL-008
**Название:** Удаление заявки в статусе Черновик
**Предусловия:**
- Есть заявка в статусе `Черновик`.
**Шаги:**
1. Открыть список черновиков.
2. Выбрать заявку в статусе `Черновик`.
3. Выполнить доступное действие удаления.
**Итоговый ожидаемый результат:** Удаленная заявка отсутствует в списке черновиков.
**Ссылка на ФТ:** `REQ-008`
```

**Expected Reviewer Output:**

- Нет `test-design` finding.
- Reviewer может не добавлять finding или добавить `info` input-limitation note только если отсутствует обязательный source artifact.
- Reviewer не должен требовать точное название кнопки, текст модального окна, анимацию удаления или audit log, если этих деталей нет в источнике.
- Falsification gate не является основанием придумать finding: TC выполняет
  source-backed trigger и наблюдает точный source-backed postcondition.
- Adversarial clean control: дефект удаления, при котором черновик остаётся в
  списке, будет обнаружен текущим oracle; реализация с любым source-consistent
  названием действия удаления пройдёт TC.
- Поскольку supplied evidence не даёт конкретного false-pass, false-fail или
  alternative-cause witness, reviewer не должен создавать finding.

## Eval Case 9 - отсутствует pairwise table при 3+ факторах

**Requirement Source:**

- `REQ-009`: Доступность действия `Отправить на согласование` зависит от роли пользователя (`Автор`, `Руководитель`, `Наблюдатель`), статуса заявки (`Черновик`, `На доработке`, `Согласована`) и канала создания (`Web`, `Mobile`).
- `REQ-009.1`: `Автор` может отправить заявку только в статусах `Черновик` и `На доработке`.
- `REQ-009.2`: `Руководитель` и `Наблюдатель` не могут отправлять заявку.

**Writer Artifacts Under Review:**

```md
## Test-design applicability matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| pairwise | yes | REQ-009 | 3 independent factors: role, status, channel | ATOM-009 | TC-EVAL-009A, TC-EVAL-009B | - |
| role-permission | yes | REQ-009.1-009.2 | Role-based access | ATOM-009 | TC-EVAL-009A, TC-EVAL-009B | - |

## TC-EVAL-009A
**Название:** Автор отправляет черновик из Web
**Приоритет:** Medium
**Шаги:** 1. Автор открывает заявку в статусе `Черновик`, созданную через `Web`. 2. Выполняет действие `Отправить на согласование`.
**Итоговый ожидаемый результат:** Заявка отправлена на согласование.

## TC-EVAL-009B
**Название:** Руководитель не отправляет согласованную заявку из Mobile
**Приоритет:** Medium
**Шаги:** 1. Руководитель открывает заявку в статусе `Согласована`, созданную через `Mobile`. 2. Пытается выполнить действие `Отправить на согласование`.
**Итоговый ожидаемый результат:** Операция отклоняется, статус заявки не меняется.
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `coverage`
- `coverage_dimension`: `pairwise`
- `test_case_id`: set-level finding или `TC-EVAL-009A`, `TC-EVAL-009B`
- Finding должен указать, что при 3 независимых факторах с несколькими значениями отсутствует `Combinatorial Coverage Table` с factors/values, constraints, selected combinations и high-risk additions.
- Required change должен требовать добавить pairwise table или зафиксировать `GAP-*`, если невозможно вывести expected behavior для комбинаций.

## Eval Case 10 - high-risk access case имеет заниженный priority

**Requirement Source:**

- `REQ-010`: Пользователь без роли `Администратор` не может изменять лимит сделки.
- `REQ-010.1`: Попытка изменения лимита пользователем без права не должна сохранять новое значение.

**Test Case Under Review:**

```md
## TC-EVAL-010
**Название:** Менеджер не изменяет лимит сделки
**Приоритет:** Low
**Тип:** Negative
**Предусловия:**
- Открыта сделка с лимитом `1 000 000`.
- Пользователь имеет роль `Менеджер`.
**Шаги:**
1. Попытаться изменить лимит сделки на `2 000 000`.
2. Попытаться сохранить изменение.
**Итоговый ожидаемый результат:** Значение лимита не меняется и остается `1 000 000`.
**Ссылка на ФТ:** `REQ-010`; `REQ-010.1`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `test-design`
- `coverage_dimension`: `role-permission`
- `test_case_id`: `TC-EVAL-010`
- Finding должен указать, что access-control / money-impact atom является high-risk и не должен иметь `Low` priority.
- Required change должен требовать поднять `Приоритет` до `High` или явно оформить blocking `coverage gap`, если риск/ожидаемое поведение не подтверждены.

## Eval Case 11 - расчетный кейс без calculation oracle

**Requirement Source:**

- `REQ-011`: Комиссия рассчитывается как `Сумма операции x 1.5%`.
- `REQ-011.1`: Комиссия округляется до двух знаков после запятой по математическим правилам.

**Test Case Under Review:**

```md
## TC-EVAL-011
**Название:** Расчет комиссии
**Приоритет:** High
**Тип:** Calculation
**Тестовые данные:**
- Сумма операции заполнена.
**Шаги:**
1. Ввести сумму операции.
2. Сохранить операцию.
**Итоговый ожидаемый результат:** Комиссия рассчитана корректно согласно формуле.
**Ссылка на ФТ:** `REQ-011`; `REQ-011.1`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `expected-result`
- `coverage_dimension`: `calculation`
- `test_case_id`: `TC-EVAL-011`
- Finding должен указать, что расчетный case не содержит calculation oracle: formula/source reference, конкретные входные значения, вручную вычисленный expected result и rounding rule.
- Required change должен требовать указать, например, вход `1000.00`, формулу `1000.00 x 1.5%`, ожидаемую комиссию `15.00` и ссылку на правило округления. Если rounding/precision не подтверждены источником, поведение должно быть вынесено в `coverage gap` / `unclear`.

## Eval Case 12 - applicability matrix ссылается на TC, который не покрывает dimension

**Requirement Source:**

- `REQ-012`: Обязательное поле `ИНН` должно проверяться на клиенте и на сервере.
- `REQ-012.1`: При прямой отправке payload без `ИНН` изменение не сохраняется.

**Writer Artifacts Under Review:**

```md
## Test-design applicability matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| api-server-validation | yes | REQ-012.1 | Backend must reject direct payload without INN | ATOM-012 | TC-EVAL-012 | - |
| boundary | yes | REQ-012 | Required-field validation | ATOM-012 | TC-EVAL-012 | - |

## TC-EVAL-012
**Название:** Поле ИНН обязательно в UI
**Приоритет:** Medium
**Тип:** Negative
**Предусловия:**
- Открыта форма редактирования клиента.
**Шаги:**
1. Оставить поле `ИНН` пустым.
2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Сохранение не происходит, поле считается невалидным.
**Ссылка на ФТ:** `REQ-012`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `coverage`
- `coverage_dimension`: `api-server-validation`
- `test_case_id`: `TC-EVAL-012` или set-level finding
- Finding должен указать, что matrix заявляет покрытие `api-server-validation`, но связанный `TC-*` проверяет только UI-flow и не выполняет direct/API payload bypass из `REQ-012.1`.
- Required change должен требовать добавить отдельный server-side/API bypass TC или оформить `GAP-*`, если backend/API проверка не входит в доступный scope или ожидаемая реакция не выводится из источника.

## Eval Case 13 - false pass: persistence не проверяется

**Requirement Source:**

- `REQ-013`: После сохранения изменённый контактный email отображается после
  повторного открытия заявки.

**Test Case Under Review:**

```md
## TC-EVAL-013
**Название:** Изменение контактного email
**Предусловия:**
- Открыта заявка с контактным email `old@example.org`.
**Шаги:**
1. Ввести `new@example.org`.
2. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** В открытой форме отображается `new@example.org`.
**Ссылка на ФТ:** `REQ-013`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `expected-result`
- `coverage_dimension`: `persistence`
- `test_case_id`: `TC-EVAL-013`
- Finding должен указать, что проверка текущего UI-state не доказывает
  persistence после повторного открытия.
- Concrete false-pass witness: UI хранит `new@example.org` только в локальном
  состоянии формы, запись остаётся `old@example.org`; TC проходит, но `REQ-013`
  нарушено.
- Required change должен требовать закрыть и повторно открыть ту же заявку и
  проверить literal `new@example.org`.

## Eval Case 14 - failure attribution нарушен невалидным fixture

**Requirement Source:**

- `REQ-014`: Поле `ИНН` обязательно; заявка без `ИНН` не сохраняется.
- `REQ-014.1`: Поле `Наименование` обязательно; заявка без `Наименования` не
  сохраняется.

**Test Case Under Review:**

```md
## TC-EVAL-014
**Название:** Сохранение без ИНН
**Предусловия:**
- Открыта новая заявка.
- Поля `ИНН` и `Наименование` пусты.
**Шаги:**
1. Нажать `Сохранить`.
**Итоговый ожидаемый результат:** Заявка не сохраняется.
**Ссылка на ФТ:** `REQ-014`
```

**Expected Reviewer Output:**

- `review_mode`: `test-design`
- `severity`: `error`
- `category`: `test-design`
- `coverage_dimension`: `dependency`
- `test_case_id`: `TC-EVAL-014`
- Finding должен указать, что отказ нельзя надёжно связать с отсутствием `ИНН`,
  потому что fixture содержит второй независимый blocker.
- Concrete alternative-cause witness: продукт ошибочно принимает пустой `ИНН`,
  но корректно блокирует сохранение из-за пустого `Наименования`; TC проходит,
  хотя `REQ-014` нарушено.
- Required change должен требовать valid fixture для всех остальных обязательных
  полей и оставить пустым только `ИНН`.
