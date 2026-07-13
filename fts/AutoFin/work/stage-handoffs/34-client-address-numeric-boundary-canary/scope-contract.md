# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`.
- Основной FT: `source/FT4AutoFinFinal.docx`.
- Машиночитаемый источник: `source/FT4AutoFinFinal.xhtml`.
- PDF cross-check: `source/FT4AutoFinFinal.pdf`.
- Родительский подтверждённый scope: `application-card-client-addresses-contacts`.
- Текущий canary является внутренним рабочим пакетом родительского scope, а не новым внешним scope.

## Scope Identity

- `scope_slug`: `application-card-client-address-numeric-boundaries-shadow`.
- Раздел: `4.3`, Table 4, блок адресов клиента.
- Цель: проверить standard structured pipeline на пяти однородных numeric-format obligations.

## Что Входит В Scope

- `Адрес регистрации / Почтовый индекс`, `SRC-004.P02`, `BSR 116`.
- `Адрес регистрации / Корпус`, `SRC-011.P02`, `BSR 124`.
- `Адрес регистрации / Квартира`, `SRC-012.P02`, `BSR 126`.
- `Фактический адрес / Квартира`, `SRC-025.P03`, `BSR 151`.
- `Фактический адрес / Почтовый индекс`, `SRC-026.P02`, `BSR 153`.
- Только source-backed положительный oracle: допустимое числовое значение; для индекса — ровно шесть цифр.

## Что Не Входит В Scope

- Тексты ошибок, фильтрация, блокировка перехода и иное поведение для невалидного ввода.
- Видимость, обязательность, DaData, сохранение `kladr`, контакты и прочие поля адреса.
- Production promotion и изменение существующих тест-кейсов.

## Разрешённые Источники

- Только выбранный комплект `FT4AutoFinFinal.*`, package notes и канонические source/design artifacts, перечисленные в prepared package.
- Старые `AutoFinPreFinal.*`, production test cases и предыдущие generated drafts запрещены как requirement evidence.

## Условие Старта

- Новый immutable package содержит 5 testable obligations и один non-blocking constraint gap.
- Validate-only и dispatcher preflight проходят до live-запуска.
- Запускается ровно один writer/reviewer cycle без SDK fallback.
