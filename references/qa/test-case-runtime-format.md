# Test Case Runtime Format

Этот reference задает минимальный runtime format для ручных `TC-*`. Полный формат и расширенные примеры остаются в `test-case-format.md` и `test-case-style-examples.md`.

## Required Structure

Каждый test case должен иметь:

- stable id `TC-<scope>-NNN` или локально принятый `TC-*` формат canonical file;
- use `## TC-*`; `### TC-*` is invalid;
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

- A slim runtime `TC-*` is canonical-valid when it has all parser-supported bold metadata fields (`Название`, `Тип`, `Приоритет`, `package_id`, `Трассировка`), all required runtime sections (`Предусловия`, `Тестовые данные`, numbered `Шаги`, `Итоговый ожидаемый результат`, `Постусловия`), and no duplicate metadata table. Full source fields from `test-case-format.md` are optional, not required, when traceability and split artifacts already provide source navigation/evidence.

- Canonical writer output must use parser-supported bold metadata fields from `test-case-format.md`: `**Название:**`, `**Тип:**`, `**Приоритет:**`, `**package_id:**`, `**Трассировка:**`. A table-only metadata block such as `| Поле | Значение |` / `| package_id | WP-01 |` is not acceptable for canonical `TC-*`, because validator parsing of required fields and `package_id` relies on the bold-field/runtime-field contract. Do not mix table metadata with the same bold fields either; use bold fields only.

- Один `TC-*` проверяет одну обязанность системы и один основной pass/fail результат.
- Не смешивай acceptance valid value и rejection invalid value в одном `TC-*`.
- Не помещай проверяемое действие в предусловия. Для созданного/выбранного/настроенного UI-state укажи путь: шаг пользователя с кнопкой/полем/значением/блоком или fixture/setup artifact; если путь неизвестен, используй `GAP-*` / `unclear`.
- В шагах описывай действие пользователя, а не внутреннюю реализацию.
- Expected result должен быть наблюдаемым: visible UI state, accepted/rejected value, saved/not saved state, navigation blocked/opened, generated document, message, API/log artifact only if source explicitly allows it.
- Не используй invisible oracle: `считается невалидным`, `корректно обрабатывается`, `соответствует ФТ`, `по системному правилу`.
- Не используй альтернативные negative oracles через `или`: `значение очищено, не сохранено или поле подсвечено`, `символ отклонен или значение осталось пустым/предыдущим`. Выбери один подтвержденный observable oracle или оформи `GAP-*` / `unclear`.
- Не используй source-rule oracle: `по правилу из источника`, `по правилу видимости из источника`, `согласно источнику`, `согласно ФТ` вместо конкретного наблюдаемого результата.
- Не добавляй exact text, colors, sorting, normalization, status codes or backend effects unless they are source-backed.
- Если behavior unclear, создай `GAP-*` / `unclear`, а не executable TC.
- Каждый `TC-*` должен иметь traceability to source statement; gap-only notes не оформляются как `TC-*`.
- `Трассировка` является обязательным source-link полем. `Ссылка на ФТ`, `Источник требования` и `Источник / цитата требования` допустимы только если добавляют недублирующую навигацию, иерархию источника или короткую реальную цитату. Не заполняй эти поля тем же набором `ATOM-*`/`SRC-*`, который уже указан в `Трассировка`.
- В `Трассировка` и optional source fields не оставляй placeholder `-`, `N/A` или пустой элемент между разделителями. Если у source statement нет `GSR`/`REQ`, укажи `ATOM-*`, `SRC-*`, раздел/строку/страницу и цитату без фиктивного id.
- Если `TC-*` использует `DICT-*` в тестовых данных, шагах или expected result, тот же `DICT-*` должен быть в `Трассировка`.
- `Источник / цитата требования` должен быть реальной краткой цитатой или явно помеченной нормализацией/derived rationale. Не выдавай synthetic statement вроде `поле использует все и только активные значения DICT-*` за цитату ФТ.
- Не смешивай две схемы описания одного `TC-*`: не дублируй metadata table `| Поле | Значение |` bold-полями `**Название:**`, `**Тип:**`, `**Приоритет:**`, `**Трассировка:**`, `**package_id:**`; не дублируй `### Тестовые данные`, `### Шаги`, `### Итоговый ожидаемый результат` inline/bold-полями с теми же названиями.
- Editability TC должен называть конкретное исходное значение и новое значение. Запрещены шаги `Активировать элемент` + `Изменить значение на тестовое значение`, если expected result не содержит literal нового значения.
- Dictionary/list TC проверяет `все и только активные значения`, когда source/support задает закрытый справочник. Если закрытость не доказана, это `GAP-*` / `unclear`, а не молчаливая проверка только наличия значений.
- Test-design-derived checks (`v2 obligation`, exploratory/experience-based, risk-derived regression) должны быть помечены как derived coverage и не должны выглядеть как новая source-backed строка ФТ без `source_or_rule_ref`.
- Постусловия должны соответствовать действиям TC. Для read-only/list-composition/visibility checks используй `Не требуются`, а не шаблонное восстановление измененных данных. Если TC создает repeatable/action-created block, постусловия должны удалять созданный блок, закрывать без сохранения или явно объяснять, почему созданное состояние не сохраняется.
- Для branch choices (`Да`/`Нет`, confirm/cancel, save/discard, back/stay) expected result должен различать выбранную ветку. Две ветки с одинаковым oracle допустимы только если source прямо задает одинаковое поведение или оформлен `GAP-*`.
- Negative input TC не должен объединять несколько независимых invalid classes под одним generic oracle. Разделяй классы или используй параметризованный набор только когда реакция на каждый класс source-backed и наблюдаемо одинаковая.

## Field-Level Checks

Для конкретного поля держи порядок:

1. видимость/доступность, если описано;
2. default value, если описано;
3. обязательность, если описано;
4. справочник/list composition, если описано;
5. positive input;
6. negative input;
7. boundary/equivalence/dependency checks, если применимы и source-backed.

Для input restrictions не додумывай механизм enforcement. `Только цифры`, length или mask задают класс допустимых значений, но не доказывают, что UI фильтрует ввод, очищает поле, показывает marker или блокирует переход. Используй field-state только с evidence, transition-state только с полным valid fixture остальных обязательных полей, иначе `GAP-*` / `unclear`.

Для numeric/input rejection не заменяй один unsupported oracle другим. Если validator или reviewer отклонил `значение не отображается`, `значение очищено`, `символы отфильтрованы` или `значение не принято` как неподтвержденный UI-механизм, writer не должен исправлять это на `поле подсвечено красным`, `появляется ошибка`, `Следующий шаг заблокирован` или `раздел не открыт`, если source прямо не задает такую реакцию именно для invalid numeric/input class. Разрешены только:

- source-backed `field-state`, если источник/макет/support подтверждает конкретное состояние поля после действия;
- source-backed `message-marker`, если подтвержден конкретный marker/message;
- source-backed `transition-state`, если источник связывает этот invalid class с блокировкой перехода и TC раскрывает full-valid fixture всех остальных обязательных полей;
- narrow `GAP-*` / `unclear` для неподтвержденного enforcement mechanism, при сохранении source-backed invalid class в design artifacts.

## When To Load Full Format

Подгружай `test-case-format.md`, если:

- validator/reviewer нашел defect формата или wording;
- нужен style remediation;
- требуется полный canonical example;
- есть сомнение в структуре expected result, приоритизации, списках/справочниках или запрещенных подменах покрытия.
