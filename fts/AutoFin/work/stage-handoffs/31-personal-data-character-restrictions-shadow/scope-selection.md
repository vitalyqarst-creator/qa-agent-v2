# Выбор shadow scope: ограничения символов ФИО

## Контекст

- Родительский подтвержденный scope: `application-card-client-personal-data` из handoff `29`.
- Источники: `source/FT4AutoFinFinal.docx`, обязательный XHTML и PDF cross-check.
- Режим: независимая eval-only проекция; production baseline и ранее созданные тест-кейсы не являются evidence.

## Граница scope

Включены только `BSR 48`, `BSR 51`, `BSR 54` для полей `Фамилия`, `Имя`, `Отчество`:

- допустимый текст;
- допустимый дефис `-` внутри текстового значения;
- недопустимая цифра как отдельный negative class;
- недопустимый специальный символ `@` как отдельный negative class.

Источник: XHTML rows `57–59`, DOCX table 6 rows `4–6`, PDF page `16`.

Исключены DaData (`BSR 49`, `BSR 52`, `BSR 55`), обязательность, видимость, редактируемость, persistence и соседние поля. Точный UI-механизм отклонения invalid value отсутствует в ФТ и сохраняется как `GAP-001`; negative checks являются UI-calibration candidates.

## Guardrails

- Compiler выбирает профиль автоматически; ожидается `standard-required` из-за `format` и UI calibration.
- Целевой путь `test-cases/4.3-prepared-shadow-personal-data-character-restrictions.md` не должен создаваться или изменяться.
- Promotion запрещен.
- Invalid classes не объединяются между собой или между полями.
