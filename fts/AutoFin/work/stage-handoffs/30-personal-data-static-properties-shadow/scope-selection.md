# Выбор реального shadow scope 4.3

## Контекст

- Родительский подтвержденный scope: `application-card-client-personal-data` из handoff `29`.
- Основные источники: `source/FT4AutoFinFinal.docx`, `source/FT4AutoFinFinal.xhtml`, `source/FT4AutoFinFinal.pdf`.
- Source selection: `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`, `xhtml_available: yes`.
- Режим: независимая eval-only проекция; старые и сгенерированные тест-кейсы не являются evidence.

## Граница shadow scope

Включены 15 независимо наблюдаемых статических обязанностей для полей `Фамилия`, `Имя`, `Отчество`:

- постоянная видимость;
- обязательность;
- редактируемость;
- тип элемента управления;
- тип значения.

Источники: XHTML rows `57–59`, DOCX table 6 rows `4–6`, PDF page `16`, `BSR 47`, `BSR 50`, `BSR 53`.

Исключены ограничения допустимых символов (`BSR 48`, `BSR 51`, `BSR 54`), DaData (`BSR 49`, `BSR 52`, `BSR 55`), conditional behavior, persistence и соседние поля. Они остаются в полном parent scope и не считаются покрытыми этой проекцией.

## Guardrails

- Compiler самостоятельно определяет execution profile; ручной override запрещен.
- Целевой путь `test-cases/4.3-prepared-shadow-personal-data-static-properties.md` используется только как отсутствующий production target.
- Promotion и production write запрещены.
- Сравнение со старым draft разрешено только после завершения независимой генерации.
