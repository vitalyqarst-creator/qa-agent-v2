# Review AutoFin test cases against agent instructions

**Branch:** `codex/agent-layer-iteration-1-ft-test-case-reviewer`

**Scope:** `fts/AutoFin/test-cases`, excluding aggregate `14-application-card.md` to avoid duplicate review of the same canonical/narrow cases.

**Review mode:** `ft-test-case-reviewer / full` — structure, traceability, runtime executability and test-design quality.

## Verdict scale

- `PASS`: no blocking issue found in the published file; minor editorial improvements may still be useful.
- `WARN`: non-blocking issue or reproducibility risk; should be fixed before sign-off if the case must be executable without hidden artifacts.
- `ERROR`: blocker against agent instructions/runtime contract; fix required before sign-off.

## Applied rules

- Test cases must not invent behavior, statuses, fields, buttons, integrations or exact UI reactions not supported by source material.
- One test case should cover one check and one primary expected result.
- Runtime format requires `## TC-*`, `Тип: Positive|Negative`, `Приоритет`, `package_id`, `Трассировка`, `Предусловия`, `Тестовые данные`, numbered `Шаги`, `Итоговый ожидаемый результат`, `Постусловия`.
- Expected result must be observable and deterministic; no vague `корректно`, no `или`, no unsupported exact colors/messages/filtering/rounding.
- If `DICT-*` or `FIX-*` is used, the manual executor must have concrete values or a linked accessible fixture artifact.
- AutoFin `AGENT-NOTES.md`: DaData notes are supporting context only, not a source of new requirements; `kladr`/model/API effects need concrete observable evidence.

## Summary

- Reviewed source files: `15`.
- Reviewed test-case rows: `316`.
- `PASS`: `135`.
- `WARN`: `109`.
- `ERROR`: `72`.

## Most important blocking patterns

1. **Invalid runtime format / enum:** `section-16-print-form-generation.md` uses `### TC-*`; several files use invalid `Тип` values such as `Validation`, `Business`, `Integration`, `Configuration`, `Decision table`.
2. **Scope drift:** e.g. recognition success/mapping in `TC-AFDRP-008`, `Далее` scenarios inside files whose scope excludes `Далее`, and integration/archive checks without concrete evidence artifacts.
3. **Fixture opacity:** `fixture-catalog.md` is an index of usages, not a definition of fixture values. Many `FIX-*`, `DICT-*`, `FX-*` cases are not reproducible from published files alone.
4. **Non-deterministic oracles/steps:** examples include `если постраничность доступна`, `если кнопка доступна`, `видимый признак или инструкция`, and conditional expected results.
5. **Input restriction overreach:** several negative input cases assert field filtering or generic validation for multiple invalid classes without a source-backed observable mechanism.
6. **Numbering/organization drift:** out-of-order TC IDs, missing `TC-ACPCP-012`, duplicate empty-date passport cases, and `### Ожидаемый результат` instead of required `### Итоговый ожидаемый результат`.

## `14-application-card-calculator-summary-entrypoints.md`

**Rows reviewed:** `4`. **PASS:** `1`, **WARN:** `2`, **ERROR:** `1`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACCS-001` | `PASS` | `—` | Узкая проверка видимости виджета; есть traceability и наблюдаемый UI-oracle. |  |
| `TC-ACCS-002` | `WARN` | `warning` | Проверка состава виджета исполнима, но предусловие «значения параметров зафиксированы» зависит от внешней подготовки без ссылки на детальный fixture. | Добавить ссылку/описание fixture для значений калькулятора или раскрыть путь подготовки. |
| `TC-ACCS-003` | `WARN` | `warning` | Переход на этап калькулятора проверяется узко, но `GAP-001` в trace может быть ошибочно прочитан как покрытие поведения самого калькулятора. | Явно оставить expected только про открытие этапа; не заявлять покрытие внутренней логики калькулятора. |
| `TC-ACCS-004` | `ERROR` | `error` | Expected result «с предзаполненными данными» слишком общий; сам файл выносит точные правила prefill в `GAP-001`. | Либо проверить только открытие окна, либо указать source-backed поля и значения prefill; остальное оставить `GAP-*`. |

## `14-application-card-document-recognition-popup.md`

**Rows reviewed:** `8`. **PASS:** `6`, **WARN:** `1`, **ERROR:** `1`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-AFDRP-001` | `PASS` | `—` | Узкая проверка видимости кнопки; формат и traceability приемлемы. |  |
| `TC-AFDRP-002` | `PASS` | `—` | Узкая проверка открытия popup; наблюдаемый expected result. |  |
| `TC-AFDRP-003` | `PASS` | `—` | Состав списка проверяется через `DICT-001`; trace включает DICT, default не проверяется — корректно. |  |
| `TC-AFDRP-004` | `PASS` | `—` | Контейнер файлов с drag&drop проверяется в пределах scope. |  |
| `TC-AFDRP-005` | `PASS` | `—` | Проверка состава кнопок popup узкая и наблюдаемая. |  |
| `TC-AFDRP-006` | `PASS` | `—` | Закрытие popup по `Отменить` проверяется корректно. |  |
| `TC-AFDRP-007` | `WARN` | `warning` | Negative case с предупреждением без файлов корректен при условии, что точный текст подтвержден source. | Для TC-007 сохранить source evidence точного текста предупреждения. |
| `TC-AFDRP-008` | `ERROR` | `error` | Кейс проверяет успешное распознавание, запрос в систему распознавания и заполнение полей заявки, но scope прямо исключает successful/failed recognition outcomes, mapping и backend/API effects; это также открытый `GAP-002`. | Удалить executable TC из baseline или заменить на `GAP-* / unclear`; успешное распознавание покрывать отдельным scope/UI-evidence набором. |

## `14-application-card-task-title-and-common-actions.md`

**Rows reviewed:** `5`. **PASS:** `2`, **WARN:** `2`, **ERROR:** `1`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-AF-CARD-001` | `PASS` | `—` | Проверка заголовка новой карточки конкретна и наблюдаема. |  |
| `TC-AF-CARD-002` | `WARN` | `warning` | Проверка заголовка существующей заявки приемлема, но fixture «номер выбранной заявки» не раскрыт. | Добавить конкретный номер/fixture или ссылку на fixture catalog с данными. |
| `TC-AF-CARD-003` | `ERROR` | `error` | `Тип: Business` не входит в allowed enum; кейс выходит за заявленные coverage boundaries, использует generic baseline обязательных полей/документов и expected «следующий этап» без конкретного oracle. | Заменить `Тип` на Positive/Negative; вынести `Далее` в отдельный scope или раскрыть полный fixture и конкретный следующий этап. |
| `TC-AF-CARD-004` | `PASS` | `—` | Ветка отказа от возврата в общий список описана исполнимо; один action-flow с наблюдаемым итогом. |  |
| `TC-AF-CARD-005` | `WARN` | `warning` | Ветка подтверждения исполнима, но expected «видима и доступна другим сотрудникам» требует роли/fixture другого сотрудника. | Добавить fixture второго сотрудника или сузить expected до отвязки/возврата в общий список, если это единственный source-backed oracle. |

## `section-17-universal-application-common-actions.md`

**Rows reviewed:** `1`. **PASS:** `1`, **WARN:** `0`, **ERROR:** `0`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-UACA-001` | `PASS` | `—` | Хороший узкий кейс: проверяется только открытие окна истории, без расширения на содержимое окна. |  |

## `section-16-print-form-generation.md`

**Rows reviewed:** `16`. **PASS:** `0`, **WARN:** `0`, **ERROR:** `16`.

**File-level blocker:** all `TC-AF-PFG-*` headings use `###` instead of required `##`; many `Тип` values are outside `Positive|Negative`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-AF-PFG-001` | `ERROR` | `error` | Глобальный structural defect: заголовок `### TC-*` вместо требуемого `## TC-*`; сам сценарий после форматного исправления приемлем. | Заменить на `## TC-AF-PFG-001` и нормализовать runtime sections. |
| `TC-AF-PFG-002` | `ERROR` | `error` | Неверный заголовок `### TC-*` и `Тип: Configuration`; allowed enum только Positive/Negative. Плюс требуется конкретный доступный артефакт настройки шаблона. | Сделать `Тип: Positive`, раскрыть проверяемый configuration artifact или оформить недоступность как gap. |
| `TC-AF-PFG-003` | `ERROR` | `error` | Неверный уровень заголовка `### TC-*`; содержательно кейс зависит от `FIX-PFG-BASE` с данными кредита/авто. | Исправить заголовок; добавить/связать fixture values для expected PDF. |
| `TC-AF-PFG-004` | `ERROR` | `error` | Неверный уровень заголовка; expected содержит много независимых полей в одном PDF-блоке, но это допустимо как проверка одного generated block при наличии fixture. | Исправить формат; убедиться, что fixture раскрывает все expected values. |
| `TC-AF-PFG-005` | `ERROR` | `error` | Неверный заголовок и `Тип: Decision table`; allowed enum нарушен. Таблица из двух состояний допустима только если это один decision-rule oracle. | Переименовать тип в Positive или разделить состояния, если они исполняются разными fixture runs. |
| `TC-AF-PFG-006` | `ERROR` | `error` | Неверный заголовок и `Тип: Decision table`; цикл по всем статусам требует явной параметризации/fixture rows. | Нормализовать тип; при необходимости оформить как list/decision-table check с конкретными rows. |
| `TC-AF-PFG-007` | `ERROR` | `error` | Неверный уровень заголовка; содержательно проверяет два адресных состояния в одном TC. | Исправить формат; разделить same/different, если нужны разные подготовки и pass/fail. |
| `TC-AF-PFG-008` | `ERROR` | `error` | Неверный уровень заголовка; expected по рабочему телефону для пенсионера зависит от source-backed условия. | Исправить формат; оставить условие как отдельную строку/fixture или split. |
| `TC-AF-PFG-009` | `ERROR` | `error` | Неверный заголовок и `Тип: Decision table`; проверка отношения к заявителю параметризована, но enum нарушен. | Нормализовать тип; убедиться, что все значения DICT-PFG-004 указаны в trace/source. |
| `TC-AF-PFG-010` | `ERROR` | `error` | Неверный заголовок и `Тип: Decision table`; проверка ОПФ содержит длинный closed-set without full fixture details. | Нормализовать тип; добавить DICT/source или split, если нужны отдельные заявки. |
| `TC-AF-PFG-011` | `ERROR` | `error` | Неверный уровень заголовка; content acceptable при раскрытом fixture адреса работодателя. | Исправить `### TC-*` -> `## TC-*`. |
| `TC-AF-PFG-012` | `ERROR` | `error` | Неверный заголовок; кейс содержит условие «если расчетный oracle недоступен» в постусловиях, то есть baseline не полностью executable. | Исправить формат; для `<job_start>` либо предоставить oracle, либо оставить эту часть gap/unclear. |
| `TC-AF-PFG-013` | `ERROR` | `error` | Неверный заголовок и `Тип: Decision table`; проверка типов дохода параметризована. | Нормализовать тип; убедиться, что для каждого типа есть fixture row или оформить как composition check. |
| `TC-AF-PFG-014` | `ERROR` | `error` | Неверный заголовок и `Тип: Decision table`; ветки выбора адреса регистрации требуют двух fixture states. | Нормализовать тип; split same/different if needed. |
| `TC-AF-PFG-015` | `ERROR` | `error` | Неверный уровень заголовка; content acceptable при наличии fixture с пятью предыдущими паспортами. | Исправить формат и связать fixture details. |
| `TC-AF-PFG-016` | `ERROR` | `error` | Неверный уровень заголовка; negative check отсутствия незаполненных тегов полезен, но trace содержит `GAP-PFG-002`. | Исправить формат; подтвердить, что GAP не используется как covered source-backed behavior. |

## `14-application-card-client-addresses.md`

**Rows reviewed:** `27`. **PASS:** `9`, **WARN:** `7`, **ERROR:** `11`.

**File-level issue:** `TC-ACCA-026` appears before `TC-ACCA-020`; `TC-ACCA-001A` is a non-standard sequence suffix.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACCA-001` | `WARN` | `warning` | Видимость блока/поля проверяется, но `Тестовые данные: Заявка с доступной анкетой клиента` слишком общие. | Сослаться на fixture или заменить на `Не требуются`, если состояние задается предусловием. |
| `TC-ACCA-001A` | `ERROR` | `error` | Нестандартный суффикс `001A` ломает сквозную numeric sequence; кейс смешивает две ветки обязательности DaData/manual в одном TC. | Перенумеровать; разделить DaData branch и manual branch или оформить как decision table artifact. |
| `TC-ACCA-002` | `ERROR` | `error` | DaData-адрес задан не literal, expected про компоненты адреса не проверяем без fixture values. | Указать конкретный адрес и ожидаемые компоненты или сослаться на детальный fixture. |
| `TC-ACCA-003` | `ERROR` | `error` | Negative DaData case без конкретной адресной строки; исполнитель не сможет воспроизвести «не найдено». | Добавить literal non-found address/source fixture. |
| `TC-ACCA-004` | `ERROR` | `error` | Адрес без квартиры не раскрыт; точная красная подсветка и текст должны быть source-backed. `GAP-001` в trace показывает риск. | Указать конкретный адрес и evidence текста/подсветки либо оставить feedback mechanism as gap. |
| `TC-ACCA-005` | `PASS` | `—` | Default переключателя ручного ввода проверяется узко и наблюдаемо. |  |
| `TC-ACCA-006` | `PASS` | `—` | Автосборка адреса имеет конкретные входные значения и наблюдаемый expected порядок. |  |
| `TC-ACCA-007` | `PASS` | `—` | Состав ручных полей проверяется одним list/visibility oracle. |  |
| `TC-ACCA-008` | `WARN` | `warning` | Кейс смешивает обязательность двух полей и list-source региона в одном expected result. | Разделить requiredness markers и справочник региона. |
| `TC-ACCA-009` | `WARN` | `warning` | Две условные ветки обязательности города/населенного пункта объединены в один TC. | Разделить на два branch TC, если нужны отдельные pass/fail. |
| `TC-ACCA-010` | `PASS` | `—` | Positive numeric input с конкретными значениями; invalid feedback явно не проверяется — корректно для `GAP-002`. |  |
| `TC-ACCA-011` | `ERROR` | `error` | Generic manual address without apartment; exact text/highlight need concrete source/fixture. | Добавить literal address and source-backed expected reaction. |
| `TC-ACCA-012` | `WARN` | `warning` | Default checkbox case исполним, но адрес без квартиры задан generic. | Добавить конкретный адрес без квартиры. |
| `TC-ACCA-013` | `WARN` | `warning` | Предусловие зависит от ранее вызванной подсказки; не раскрыт путь подготовки полностью. | Добавить setup steps or link TC-ACCA-011 as prerequisite fixture. |
| `TC-ACCA-014` | `PASS` | `—` | Default совпадения фактического адреса с регистрацией проверяется узко. |  |
| `TC-ACCA-015` | `PASS` | `—` | Visibility branch при несовпадении адресов исполним и наблюдаем. |  |
| `TC-ACCA-016` | `ERROR` | `error` | DaData фактический адрес задан generic; expected components not verifiable. | Указать конкретный address fixture and expected components. |
| `TC-ACCA-017` | `ERROR` | `error` | Non-found DaData address задан generic; нет literal input. | Добавить literal non-found address. |
| `TC-ACCA-018` | `ERROR` | `error` | Фактический адрес без квартиры не раскрыт; exact warning/highlight depends on source. | Добавить concrete address and evidence. |
| `TC-ACCA-019` | `PASS` | `—` | Состав ручных полей фактического адреса проверяется наблюдаемо. |  |
| `TC-ACCA-020` | `PASS` | `—` | Автосборка фактического адреса имеет конкретные values и expected order. |  |
| `TC-ACCA-021` | `WARN` | `warning` | Requiredness и region dictionary смешаны в одном TC. | Разделить required marker check и list-source check. |
| `TC-ACCA-022` | `PASS` | `—` | Positive numeric input; invalid feedback intentionally out of scope. |  |
| `TC-ACCA-023` | `ERROR` | `error` | Generic manual фактический адрес без квартиры; exact expected needs concrete data. | Добавить fixture literal. |
| `TC-ACCA-024` | `WARN` | `warning` | Default checkbox pass, но фактический адрес без квартиры не конкретизирован. | Добавить concrete address fixture. |
| `TC-ACCA-025` | `ERROR` | `error` | Смешаны две ветки обязательности фактического адреса; one TC contains two pass/fail states. | Split into DaData branch and manual branch. |
| `TC-ACCA-026` | `ERROR` | `error` | `Тип: Integration` invalid; `kladr`/model assertion uses generic API/DB/log evidence and no concrete КЛАДР value. | Change to Positive only with named evidence artifact and exact expected `kladr`, or move to GAP/integration scope. |

## `14-application-card-client-contacts-and-extra-info.md`

**Rows reviewed:** `27`. **PASS:** `17`, **WARN:** `7`, **ERROR:** `3`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACCEI-001` | `WARN` | `warning` | `package_id` WP-01 but trace includes WP-02 and expected spans contacts + additional info. | Split or use scenario package; align package_id/trace. |
| `TC-ACCEI-002` | `WARN` | `warning` | Marker check spans WP-01 and WP-02 fields with `package_id` WP-02; otherwise observable. | Split contacts vs additional info or justify scenario package. |
| `TC-ACCEI-003` | `WARN` | `warning` | Editability check spans multiple packages and many fields in one TC; trace includes WP-01/WP-02. | Split by package or provide explicit scenario rationale. |
| `TC-ACCEI-004` | `PASS` | `—` | Visibility absence of additional phone before add is narrow and observable. |  |
| `TC-ACCEI-005` | `PASS` | `—` | Mobile phone positive mask check has literal input; keep source evidence for exact mask. |  |
| `TC-ACCEI-006` | `PASS` | `—` | E-mail positive input has literal value and observable field-state. |  |
| `TC-ACCEI-007` | `PASS` | `—` | Adding additional phone block is a single observable action-created block; cleanup present. |  |
| `TC-ACCEI-008` | `WARN` | `warning` | Mutual requiredness проверяется двумя branch states в одном TC. | Split branch `номер заполнен` and branch `тип выбран`, if strict one-result required. |
| `TC-ACCEI-009` | `PASS` | `—` | Closed list check includes all active values and DICT trace. |  |
| `TC-ACCEI-010` | `PASS` | `—` | Additional phone positive mask check has concrete literal. |  |
| `TC-ACCEI-011` | `PASS` | `—` | Deletion of created additional-phone block has clear observable result. |  |
| `TC-ACCEI-012` | `PASS` | `—` | Adding contact person row is one action-created block with cleanup. |  |
| `TC-ACCEI-013` | `PASS` | `—` | Requiredness marker check for created contact row is coherent one field group. |  |
| `TC-ACCEI-014` | `PASS` | `—` | FIO text input has concrete values and observable field-state. |  |
| `TC-ACCEI-015` | `PASS` | `—` | Closed list check for relationship values is concrete and traceable. |  |
| `TC-ACCEI-016` | `PASS` | `—` | Selecting `иное` and displaying extra text field is a narrow dependency check. |  |
| `TC-ACCEI-017` | `PASS` | `—` | Contact phone positive mask check has literal input. |  |
| `TC-ACCEI-018` | `WARN` | `warning` | Uses absolute current stand date; acceptable only if stand date is controllable/known. | Use relative current date or declare controlled business date setup. |
| `TC-ACCEI-019` | `PASS` | `—` | Deletion of contact-person row is observable. |  |
| `TC-ACCEI-020` | `WARN` | `warning` | Successful INN verification expected combines checkbox state plus read-only state of many other fields; fixture `FX-001` is not in fixture-catalog. | Provide detailed fixture/evidence or split verification result and read-only lock checks. |
| `TC-ACCEI-021` | `ERROR` | `error` | Uses `Далее`, while file scope excludes standalone action `Далее`; expected depends on broader workflow. | Move to `Далее`/common-action scope or reduce to INN field state only. |
| `TC-ACCEI-022` | `PASS` | `—` | Visibility of `ИНН проверен` checkbox is narrow. |  |
| `TC-ACCEI-023` | `PASS` | `—` | Closed list check for marital status is concrete and traceable. |  |
| `TC-ACCEI-024` | `WARN` | `warning` | Combines numeric value input and spinner/buttons presence in one TC. | Split value input and control availability if each is separately sourced. |
| `TC-ACCEI-025` | `PASS` | `—` | Additional information field visibility check is narrow. |  |
| `TC-ACCEI-026` | `ERROR` | `error` | Expected contains conditional `Если интеграция вернула ИНН`; test data says generic valid date and no exact expected INN/status. | Use deterministic stub/fixture with exact INN/status or mark integration outcome gap. |
| `TC-ACCEI-027` | `ERROR` | `error` | Step `Подготовить состояние...` is generic; TC combines auto-fill state and manual-input fallback branch. | Split into two deterministic TCs with explicit setup/evidence. |

## `14-application-card-client-personal-data.md`

**Rows reviewed:** `15`. **PASS:** `8`, **WARN:** `4`, **ERROR:** `3`.

**File-level issue:** TC order is non-monotonic (`014`, `015` appear before `003`) and coverage summary count does not match the visible 15 TC rows.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACPD-001` | `PASS` | `—` | Block/field visibility check is narrow and observable. |  |
| `TC-ACPD-002` | `ERROR` | `error` | Combines required markers, conditional visibility, and conditional group requiredness in one TC. | Split base requiredness, visibility of previous-FIO fields, and at-least-one required rule. |
| `TC-ACPD-014` | `WARN` | `warning` | DaData test data literals are not actually used in steps; DaData behavior must be source-backed and not inferred from package notes. | Use literal values in steps and cite source evidence that DaData suggestions are required for these fields. |
| `TC-ACPD-015` | `ERROR` | `error` | Negative date expected says form cannot proceed, but no transition/save action or full valid fixture is provided; current date is fixed example. | Add deterministic validation action and valid baseline, or use field/message oracle confirmed by source. |
| `TC-ACPD-003` | `ERROR` | `error` | Editability check for `Пол` lacks concrete new value; combines editability of many fields and read-only ID. | Provide literal `Пол` value and split read-only ID if needed. |
| `TC-ACPD-004` | `PASS` | `—` | Positive FIO format with hyphen has concrete values and observable field-state. |  |
| `TC-ACPD-005` | `WARN` | `warning` | Saving relies on generic baseline `all fields from signed-off scope` and ABS-generated ID; not reproducible from this file alone. | Link detailed fixture/setup or keep as integration/persistence gap. |
| `TC-ACPD-006` | `PASS` | `—` | Closed list `Пол` check includes active values and DICT trace. |  |
| `TC-ACPD-007` | `WARN` | `warning` | DaData-driven gender update is integration-dependent and traced to GAP; exact outcome requires source/stub evidence. | Provide deterministic DaData fixture or mark unresolved behavior as gap. |
| `TC-ACPD-008` | `WARN` | `warning` | Boundary date uses fixed stand date example; expected only field display, not acceptance through validation. | Use relative date or controlled date setup; add validation action if acceptance is intended. |
| `TC-ACPD-009` | `PASS` | `—` | Default `Клиент менял ФИО = Нет` is narrow. |  |
| `TC-ACPD-010` | `PASS` | `—` | Toggle between `Да/Нет` is simple and observable. |  |
| `TC-ACPD-011` | `PASS` | `—` | Visibility when `Клиент менял ФИО = Да` is narrow. |  |
| `TC-ACPD-012` | `PASS` | `—` | Negative visibility branch when `Нет` is narrow. |  |
| `TC-ACPD-013` | `PASS` | `—` | Previous FIO hyphen input has concrete values and observable field-state. |  |

## `14-application-card-documents-and-questionnaire-files.md`

**Rows reviewed:** `31`. **PASS:** `16`, **WARN:** `5`, **ERROR:** `10`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-AF-DOC-001` | `PASS` | `—` | Visibility/instruction field check is clear and observable. |  |
| `TC-AF-DOC-002` | `WARN` | `warning` | Combines three file formats and two upload mechanisms in one TC with intermediate deletions. | Split by upload mechanism or make it explicit parameterized list-composition check. |
| `TC-AF-DOC-003` | `PASS` | `—` | Drag&drop upload check is narrow and has concrete file. |  |
| `TC-AF-DOC-004` | `PASS` | `—` | File size positive boundary has concrete file name and observable result. |  |
| `TC-AF-DOC-005` | `ERROR` | `error` | `Тип: Validation` invalid; should be Negative. Otherwise expected has exact source-like error text. | Set `Тип: Negative`. |
| `TC-AF-DOC-006` | `WARN` | `warning` | Combines three formats in one TC; same issue as DOC-002. | Split or explicitly treat as one accepted-formats list check. |
| `TC-AF-DOC-007` | `PASS` | `—` | Drag&drop passport upload is narrow. |  |
| `TC-AF-DOC-008` | `PASS` | `—` | Positive size check is narrow. |  |
| `TC-AF-DOC-009` | `ERROR` | `error` | `Тип: Validation` invalid; should be Negative. | Set `Тип: Negative`. |
| `TC-AF-DOC-010` | `WARN` | `warning` | Combines default empty value and list composition in one TC. | Split default check and list composition check. |
| `TC-AF-DOC-011` | `PASS` | `—` | Upload disabled before type selection is clear and observable. |  |
| `TC-AF-DOC-012` | `PASS` | `—` | Second document upload after type selection is narrow. |  |
| `TC-AF-DOC-013` | `PASS` | `—` | Second document drag&drop is narrow. |  |
| `TC-AF-DOC-014` | `ERROR` | `error` | `Тип: Validation` invalid; should be Negative. | Set `Тип: Negative`. |
| `TC-AF-DOC-015` | `PASS` | `—` | Visibility for two source-backed document types can be one composition check. |  |
| `TC-AF-DOC-016` | `PASS` | `—` | SNILS negative visibility branch is narrow. |  |
| `TC-AF-DOC-017` | `WARN` | `warning` | Uses current calendar date without explicit controlled date setup. | Use relative current date or controlled date precondition. |
| `TC-AF-DOC-018` | `ERROR` | `error` | `Тип: Validation` invalid; test data has generic future date, not literal. | Set `Тип: Negative`; use concrete relative/literal date. |
| `TC-AF-DOC-019` | `PASS` | `—` | Preview through eye icon is observable. |  |
| `TC-AF-DOC-020` | `PASS` | `—` | Hide/delete via trash icon is observable; persistence not claimed. |  |
| `TC-AF-DOC-021` | `PASS` | `—` | QR code popup opening is narrow. |  |
| `TC-AF-DOC-022` | `WARN` | `warning` | Download check is observable but requires local download evidence path/filename convention. | Add expected filename or evidence criterion if source defines it. |
| `TC-AF-DOC-023` | `PASS` | `—` | Multiple questionnaire files comma display is concrete. |  |
| `TC-AF-DOC-024` | `PASS` | `—` | Multiple passport files comma display is concrete. |  |
| `TC-AF-DOC-025` | `PASS` | `—` | Multiple second-document files comma display is concrete. |  |
| `TC-AF-DOC-026` | `ERROR` | `error` | `Тип: Validation` invalid; should be Negative. | Set `Тип: Negative`. |
| `TC-AF-DOC-027` | `ERROR` | `error` | `Тип: Validation` invalid; should be Negative. | Set `Тип: Negative`. |
| `TC-AF-DOC-028` | `ERROR` | `error` | `Тип: Business` invalid; combines three program variants/branches in one TC. | Set valid type and split by program type. |
| `TC-AF-DOC-029` | `ERROR` | `error` | `Тип: Integration` invalid; archive evidence source is generic (`archive UI, API, БД или лог`). | Set `Тип: Positive` only with concrete evidence artifact, otherwise move to gap/integration scope. |
| `TC-AF-DOC-030` | `ERROR` | `error` | Same integration-type and generic evidence problem as DOC-029. | Use concrete archive evidence or gap. |
| `TC-AF-DOC-031` | `ERROR` | `error` | Same integration-type and generic evidence problem as DOC-029. | Use concrete archive evidence or gap. |

## `14-application-card-employment-income-gosuslugi.md`

**Rows reviewed:** `44`. **PASS:** `27`, **WARN:** `10`, **ERROR:** `7`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-AFEIG-001` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-002` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-003` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-004` | `WARN` | `warning` | Два значения (`пенсионер`, `самозанятый`) проверяются в одном TC; expected одинаковый, поэтому допустимо как composition check, но split повысит атомарность. | При необходимости разделить на два branch TC. |
| `TC-AFEIG-005` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-006` | `ERROR` | `error` | Использует `Далее` при scope exclusion generic `Далее`; DaData organization fixture не конкретизирован; exact warning/source must be proven. | Move transition to action scope or provide full valid fixture and concrete DaData stub. |
| `TC-AFEIG-007` | `ERROR` | `error` | DaData organization described generically with “known values”; expected fields have no literal expected values. | Provide concrete organization fixture and expected filled fields. |
| `TC-AFEIG-008` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-009` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-010` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-011` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-012` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-013` | `WARN` | `warning` | Exact phone template must be source-backed; otherwise expected over-specific. | Confirm source for `+7(xxx)-xxx-xx-xx`. |
| `TC-AFEIG-014` | `WARN` | `warning` | Expected asserts absence of red highlight/message; acceptable only if source confirms validation reaction at X boundary. | Keep source evidence or reduce to field accepts value. |
| `TC-AFEIG-015` | `WARN` | `warning` | Exact red highlight/message must be source-backed. | Confirm source evidence. |
| `TC-AFEIG-016` | `WARN` | `warning` | Exact warning/highlight must be source-backed. | Confirm source evidence. |
| `TC-AFEIG-017` | `WARN` | `warning` | Precondition `fields filled with test values` lacks literal values for all fields. | Add fixture values or setup steps. |
| `TC-AFEIG-018` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-019` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-020` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-021` | `WARN` | `warning` | Uniqueness rule iterates several income types but one expected; acceptable if same behavior, otherwise split. | Consider parameterized table with rows. |
| `TC-AFEIG-022` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-023` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-024` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-025` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-026` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-027` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-028` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-029` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-030` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-031` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-032` | `WARN` | `warning` | Expected starts with conditional `Если вложен документ`, while precondition already says document is attached; wording can be deterministic. | Remove conditional wording. |
| `TC-AFEIG-033` | `WARN` | `warning` | Expected uses conditional wording and includes GAP-007; ensure only UI hiding, not persistence deletion, is covered. | Make expected deterministic and keep persistence as gap. |
| `TC-AFEIG-034` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-035` | `ERROR` | `error` | Unsupported field-filter oracle for input restriction: `abc` not entered. Source class does not prove UI filtering mechanism. | Use source-backed message/transition with full fixture, or mark enforcement as `GAP-*`. |
| `TC-AFEIG-036` | `ERROR` | `error` | Unsupported field-filter oracle for negative value `-2000`; exact filtering not proven. | Use source-backed oracle or gap. |
| `TC-AFEIG-037` | `ERROR` | `error` | Exact rounding/format `66 660.98` from `66660.981` is not safe unless source explicitly defines precision/rounding/space separator. | Provide source for rounding/format or move to gap. |
| `TC-AFEIG-038` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-039` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-040` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-041` | `WARN` | `warning` | Two social-status values in one TC with same expected; acceptable but split may improve atomicity. | Split if reviewer requires strict branch isolation. |
| `TC-AFEIG-042` | `PASS` | `—` | Проверка в целом соответствует runtime-формату; замечаний уровня blocker не найдено. |  |
| `TC-AFEIG-043` | `ERROR` | `error` | `Тип: Integration` invalid; uses `Далее` save/request and generic service-log/stub evidence. | Set valid type only with concrete evidence, or move integration request to separate scope/gap. |
| `TC-AFEIG-044` | `ERROR` | `error` | `Тип: Integration` invalid; archive evidence generic. | Set `Тип: Positive` with concrete archive evidence artifact or mark gap. |

## `14-application-card-participants-coborrower-pledger.md`

**Rows reviewed:** `28`. **PASS:** `5`, **WARN:** `19`, **ERROR:** `4`.

**File-level issue:** many TC rows have `package_id: WP-01` while trace includes `WP-02/03/04`; `TC-ACP-025..028` use a non-canonical expected-result heading.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACP-001` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACP-002` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-003` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-004` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-005` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-006` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-007` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-008` | `WARN` | `warning` | Кроме package mismatch, проверка исключений содержит длинный список элементов в одном TC; допустимо как composition check, но сложна для исполнения. | Сохранить как list-composition или split по группам исключений. |
| `TC-ACP-009` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-010` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-011` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-012` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-013` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-014` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-015` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-016` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-017` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-018` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-019` | `WARN` | `warning` | Deletion UI covered, but scope excludes persistence after deletion; expected should remain UI-only. | Do not assert backend/persistence deletion. |
| `TC-ACP-020` | `WARN` | `warning` | `package_id` указан как WP-01, но trace содержит другой work package (`WP-02/03/04`); content может быть валиден, но package trace несогласован. | Align `package_id` with trace or use justified scenario package. |
| `TC-ACP-021` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACP-022` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACP-023` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACP-024` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACP-025` | `ERROR` | `error` | Runtime section named `### Ожидаемый результат`, not required `### Итоговый ожидаемый результат`; parser/contract may treat expected as missing. | Rename section to `### Итоговый ожидаемый результат`. |
| `TC-ACP-026` | `ERROR` | `error` | Runtime section named `### Ожидаемый результат`, not required `### Итоговый ожидаемый результат`; parser/contract may treat expected as missing. | Rename section to `### Итоговый ожидаемый результат`. |
| `TC-ACP-027` | `ERROR` | `error` | Runtime section named `### Ожидаемый результат`, not required `### Итоговый ожидаемый результат`; parser/contract may treat expected as missing. | Rename section to `### Итоговый ожидаемый результат`. |
| `TC-ACP-028` | `ERROR` | `error` | Runtime section named `### Ожидаемый результат`, not required `### Итоговый ожидаемый результат`; parser/contract may treat expected as missing. | Rename section to `### Итоговый ожидаемый результат`. |

## `14-application-card-passport-current-and-previous.md`

**Rows reviewed:** `54`. **PASS:** `25`, **WARN:** `21`, **ERROR:** `8`.

**File-level issue:** `TC-ACPCP-012` is missing; `TC-ACPCP-019` and `TC-ACPCP-031` duplicate the empty date issue scenario.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACPCP-001` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-002` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-003` | `WARN` | `warning` | Editability many fields in one TC; acceptable but broad. | Split if each field has separate source property. |
| `TC-ACPCP-004` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-005` | `WARN` | `warning` | Negative validation expected is generic `отображается валидация`; exact field/message not specified. | Use source-backed message/marker or a deterministic save-block oracle with full fixture. |
| `TC-ACPCP-006` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-007` | `WARN` | `warning` | Same generic validation wording as series negative. | Specify source-backed message/marker. |
| `TC-ACPCP-008` | `WARN` | `warning` | Expected says `принимает` rather than exact displayed value; still observable enough, but better use field-state wording. | Use `отображает значение 770001`. |
| `TC-ACPCP-009` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-010` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-011` | `ERROR` | `error` | DaData `Кем выдан` prefill expected has no exact expected value; only code is given. | Add concrete expected issuing authority from stub/source. |
| `TC-ACPCP-013` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-014` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-015` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-016` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-017` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-018` | `WARN` | `warning` | Uses fixed stand date; acceptable only with controlled date setup. | Use relative date or controlled business date. |
| `TC-ACPCP-019` | `ERROR` | `error` | Duplicate of TC-ACPCP-031 and uses generic valid baseline. | Remove duplicate or merge with TC-ACPCP-031; keep one canonical case. |
| `TC-ACPCP-020` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-021` | `WARN` | `warning` | Positive boundary expected only absence of one message; ensure no other invalid state matters. | Consider field-state/save oracle if source requires. |
| `TC-ACPCP-022` | `WARN` | `warning` | Relies on controlled future current date; okay only with date control fixture. | Explicitly set/verify business date. |
| `TC-ACPCP-023` | `WARN` | `warning` | Relies on controlled date logic and exact range naming; okay if source-backed. | Keep source evidence. |
| `TC-ACPCP-024` | `WARN` | `warning` | Relies on controlled future current date; save-block expected okay if fixture valid. | Add date-control setup. |
| `TC-ACPCP-025` | `WARN` | `warning` | Uses far-future current date; requires controlled business date. | Add date-control setup. |
| `TC-ACPCP-026` | `WARN` | `warning` | Uses far-future current date; requires controlled date setup. | Add date-control setup. |
| `TC-ACPCP-027` | `WARN` | `warning` | Uses far-future current date; requires controlled date setup. | Add date-control setup. |
| `TC-ACPCP-028` | `WARN` | `warning` | Uses far-future current date; save-block expected okay only with fixture. | Add date-control setup. |
| `TC-ACPCP-029` | `WARN` | `warning` | Uses far-future current date; requires controlled date setup. | Add date-control setup. |
| `TC-ACPCP-030` | `WARN` | `warning` | Fixed current date; okay with controlled date setup. | Add/verify date-control setup. |
| `TC-ACPCP-031` | `ERROR` | `error` | Duplicate of TC-ACPCP-019; same empty-date validation scenario. | Remove duplicate or merge. |
| `TC-ACPCP-032` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-033` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-034` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-035` | `WARN` | `warning` | Auto-setting `Клиент менял паспорт` depends on current date; use controlled date setup. | Add business date fixture. |
| `TC-ACPCP-036` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-037` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-038` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-039` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-040` | `WARN` | `warning` | Step contains `При необходимости`, which is nondeterministic in runtime steps. | Make setup deterministic: ensure previous passport block exists before checking trash. |
| `TC-ACPCP-041` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-042` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-043` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-044` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-045` | `WARN` | `warning` | Generic validation wording; no exact message/marker. | Specify source-backed oracle. |
| `TC-ACPCP-046` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-047` | `WARN` | `warning` | Generic validation wording; no exact message/marker. | Specify source-backed oracle. |
| `TC-ACPCP-048` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACPCP-049` | `WARN` | `warning` | Combines numeric class checks for three fields in one TC; acceptable as class check but broad. | Split if strict one field per TC is required. |
| `TC-ACPCP-050` | `WARN` | `warning` | Combines numeric class checks for two previous-passport fields in one TC. | Split if strict. |
| `TC-ACPCP-051` | `ERROR` | `error` | Combines multiple invalid classes (length, letters, spaces, plus, dot) under one negative expected; runtime requires distinct invalid classes when distinguishable. | Split invalid length and invalid character classes, or prove identical source-backed reaction for all rows. |
| `TC-ACPCP-052` | `ERROR` | `error` | Combines multiple invalid classes (length, letters, spaces, plus, dot) under one negative expected; runtime requires distinct invalid classes when distinguishable. | Split invalid length and invalid character classes, or prove identical source-backed reaction for all rows. |
| `TC-ACPCP-053` | `ERROR` | `error` | Combines multiple invalid classes (length, letters, spaces, plus, dot) under one negative expected; runtime requires distinct invalid classes when distinguishable. | Split invalid length and invalid character classes, or prove identical source-backed reaction for all rows. |
| `TC-ACPCP-054` | `ERROR` | `error` | Combines multiple invalid classes (length, letters, spaces, plus, dot) under one negative expected; runtime requires distinct invalid classes when distinguishable. | Split invalid length and invalid character classes, or prove identical source-backed reaction for all rows. |
| `TC-ACPCP-055` | `ERROR` | `error` | Combines multiple invalid classes (length, letters, spaces, plus, dot) under one negative expected; runtime requires distinct invalid classes when distinguishable. | Split invalid length and invalid character classes, or prove identical source-backed reaction for all rows. |

## `14-application-card-visual-assessment-consents-checks.md`

**Rows reviewed:** `19`. **PASS:** `12`, **WARN:** `7`, **ERROR:** `0`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-ACVCC-001` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-002` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-003` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-004` | `WARN` | `warning` | References appendix file for full dictionary; if hidden work artifact is unavailable, manual executor lacks full list. | Publish/inline dictionary values or link accessible artifact. |
| `TC-ACVCC-005` | `WARN` | `warning` | Uses `Любое значение`; less reproducible than a concrete representative value. | Use a concrete criterion value from DICT-001. |
| `TC-ACVCC-006` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-007` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-008` | `WARN` | `warning` | Uses external appendix reference; ensure it is available in branch/review package. | Publish reference list or inline needed text. |
| `TC-ACVCC-009` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-010` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-011` | `WARN` | `warning` | Combines display and default value in one TC; acceptable but can split. | Split if strict. |
| `TC-ACVCC-012` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-013` | `WARN` | `warning` | Expected `all fields APP2-CHECK-003` depends on external reference; not self-contained. | Publish/inline APP2 list. |
| `TC-ACVCC-014` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-015` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-016` | `WARN` | `warning` | Uses `любой отображенный блок 1-7`; pick a concrete block/value for reproducibility. | Use a concrete group, e.g. same as section-18 TC-VAC-009. |
| `TC-ACVCC-017` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-018` | `PASS` | `—` | Проверка в целом исполнима; blocker не найден. |  |
| `TC-ACVCC-019` | `WARN` | `warning` | Out of numeric order and uses transition `Далее`; file claims this is BSR316 coverage, but expected message is generic. | Move to numeric order and use source-backed validation oracle/full valid fixture. |

## `section-18-visual-assessment-criteria.md`

**Rows reviewed:** `13`. **PASS:** `6`, **WARN:** `6`, **ERROR:** `1`.

**File-level issue:** the file says it is reference/dictionary coverage, while several TC rows duplicate executable UI behavior from the canonical section-14 visual/consents file.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-VAC-001` | `WARN` | `warning` | Duplicative with canonical 14-card visual coverage; file itself says it should be reference/dictionary, not competing UI behavior. | Either keep only as reference or mark duplicate/non-canonical. |
| `TC-VAC-002` | `WARN` | `warning` | Duplicative default-value UI behavior with canonical 14-card file. | Avoid maintaining two competing baseline TCs. |
| `TC-VAC-003` | `WARN` | `warning` | Duplicative UI behavior for `Визуальная информация=Да`. | Keep canonical behavior in 14-card file only. |
| `TC-VAC-004` | `WARN` | `warning` | Duplicative display check for `Параметры визуальной оценки`. | Keep as dictionary reference or remove duplicate UI TC. |
| `TC-VAC-005` | `WARN` | `warning` | Duplicative negative visibility branch. | Keep canonical behavior in 14-card file. |
| `TC-VAC-006` | `PASS` | `—` | Dictionary/list composition check matches reference purpose, but relies on published dictionary-inventory availability. |  |
| `TC-VAC-007` | `PASS` | `—` | Checkbox controls for reference list are acceptable reference/dictionary coverage. |  |
| `TC-VAC-008` | `ERROR` | `error` | Expected `видимый признак или инструкция` is alternative/non-deterministic and not a single concrete observable oracle. | Choose one source-backed observable marker/message or move ambiguity to gap. |
| `TC-VAC-009` | `PASS` | `—` | Concrete `Другое` value in one group; observable text field display. |  |
| `TC-VAC-010` | `WARN` | `warning` | Requiredness marker for comment field must be source-backed; otherwise exact marker is unsupported. | Keep only if BSR/clarification confirms visible marker. |
| `TC-VAC-011` | `PASS` | `—` | Closed clarification for standalone `Комментарий` is reflected with concrete groups. |  |
| `TC-VAC-012` | `PASS` | `—` | Concrete standalone comment input value and field-state expected. |  |
| `TC-VAC-013` | `PASS` | `—` | Multiple checkbox selection uses concrete values and observable selected state. |  |

## `section-4.2-applications-menu-search.md`

**Rows reviewed:** `24`. **PASS:** `0`, **WARN:** `18`, **ERROR:** `6`.

| TC | Verdict | Severity | Feedback | Required change |
| --- | --- | --- | --- | --- |
| `TC-AMSR-001` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-002` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-003` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-004` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-005` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-006` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-007` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-008` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-009` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-010` | `ERROR` | `error` | Depends on `DICT-STATUS-01` and non-final status model, but status values/defaults are residual gap; fixture values are not published. | Provide status fixture/list or keep default non-final status behavior as gap. |
| `TC-AMSR-011` | `ERROR` | `error` | `DICT-POS-01` values and first-symbol fixture not published; expected cannot be manually reproduced. | Publish DICT-POS values and expected filtered list. |
| `TC-AMSR-012` | `ERROR` | `error` | Employee dictionary and role model are residual dependencies; `DICT-EMP-01`/role fixture not defined. | Publish role+employee fixture or mark as gap until role model available. |
| `TC-AMSR-013` | `WARN` | `warning` | Step says `Нажать Очистить, если фильтры были изменены`; conditional step is nondeterministic. | Make setup deterministic: start from clean state or always clear first. |
| `TC-AMSR-014` | `WARN` | `warning` | Large column composition/read-only check is acceptable, but trace ranges `ATOM-022..ATOM-034` may be parser-hostile. | Expand ranges if validator requires exact tokens. |
| `TC-AMSR-015` | `ERROR` | `error` | Uses one unspecified invalid format and expected offers three alternative messages (`телефон/паспорт/VIN`); not one deterministic negative class. | Split by invalid class with concrete input and single expected message. |
| `TC-AMSR-016` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-017` | `ERROR` | `error` | Step `если постраничность доступна` is nondeterministic; expected combines filters, sort, pagination and selection reset. | Split reset dimensions or provide fixture guaranteeing pagination. |
| `TC-AMSR-018` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-019` | `WARN` | `warning` | Checks no selection, one selection and two selections in one TC; acceptable state matrix but broad. | Consider three atomic availability TCs. |
| `TC-AMSR-020` | `ERROR` | `error` | Step `Нажать Продолжить, если кнопка доступна` is nondeterministic; expected has generic message text. | Define exact pre-state and either disabled-state or source-backed message. |
| `TC-AMSR-021` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-022` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-023` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
| `TC-AMSR-024` | `WARN` | `warning` | Uses `FIX-*` fixture IDs, while published fixture-catalog is only an index and does not define fixture values. | Publish fixture details or inline key literals. |
