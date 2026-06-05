# Test Case Runtime Format

Этот reference задает минимальный runtime format для ручных `TC-*`. Полный формат и расширенные примеры остаются в `test-case-format.md` и `test-case-style-examples.md`.

## Required Structure

Каждый test case должен иметь:

- stable id `TC-<scope>-NNN` или локально принятый `TC-*` формат canonical file;
- `Название`;
- `Тип`: `Positive` или `Negative`;
- `Приоритет`;
- `Трассировка`: `ATOM-*`, `GSR-*` / `REQ-*` или source reference;
- `Предусловия`;
- `Тестовые данные`;
- numbered `Шаги`;
- один основной `Итоговый ожидаемый результат`;
- `Постусловия`.

Если специальных данных или cleanup нет, указывай `Не требуются`.

## Runtime Rules

- Один `TC-*` проверяет одну обязанность системы и один основной pass/fail результат.
- Не смешивай acceptance valid value и rejection invalid value в одном `TC-*`.
- Не помещай проверяемое действие в предусловия.
- В шагах описывай действие пользователя, а не внутреннюю реализацию.
- Expected result должен быть наблюдаемым: visible UI state, accepted/rejected value, saved/not saved state, navigation blocked/opened, generated document, message, API/log artifact only if source explicitly allows it.
- Не используй invisible oracle: `считается невалидным`, `корректно обрабатывается`, `соответствует ФТ`, `по системному правилу`.
- Не используй source-rule oracle: `по правилу из источника`, `по правилу видимости из источника`, `согласно источнику`, `согласно ФТ` вместо конкретного наблюдаемого результата.
- Не добавляй exact text, colors, sorting, normalization, status codes or backend effects unless they are source-backed.
- Если behavior unclear, создай `GAP-*` / `unclear`, а не executable TC.
- Каждый `TC-*` должен иметь traceability to source statement; gap-only notes не оформляются как `TC-*`.
- В `Трассировка` и `Ссылка на ФТ` не оставляй placeholder `-`, `N/A` или пустой элемент между разделителями. Если у source statement нет `GSR`/`REQ`, укажи `ATOM-*`, `SRC-*`, раздел/строку/страницу и цитату без фиктивного id.
- Editability TC должен называть конкретное исходное значение и новое значение. Запрещены шаги `Активировать элемент` + `Изменить значение на тестовое значение`, если expected result не содержит literal нового значения.
- Dictionary/list TC проверяет `все и только активные значения`, когда source/support задает закрытый справочник. Если закрытость не доказана, это `GAP-*` / `unclear`, а не молчаливая проверка только наличия значений.
- Test-design-derived checks (`v2 obligation`, exploratory/experience-based, risk-derived regression) должны быть помечены как derived coverage и не должны выглядеть как новая source-backed строка ФТ без `source_or_rule_ref`.
- Постусловия должны соответствовать действиям TC. Для read-only/list-composition/visibility checks используй `Не требуются`, а не шаблонное восстановление измененных данных.

## Field-Level Checks

Для конкретного поля держи порядок:

1. видимость/доступность, если описано;
2. default value, если описано;
3. обязательность, если описано;
4. справочник/list composition, если описано;
5. positive input;
6. negative input;
7. boundary/equivalence/dependency checks, если применимы и source-backed.

Для input restrictions проверяй состояние самого поля, если ФТ не задает отдельное validation action. Не подменяй mask/length/digits-only проверку переходом на следующий раздел без source-backed причины.

## When To Load Full Format

Подгружай `test-case-format.md`, если:

- validator/reviewer нашел defect формата или wording;
- нужен style remediation;
- требуется полный canonical example;
- есть сомнение в структуре expected result, приоритизации, списках/справочниках или запрещенных подменах покрытия.
