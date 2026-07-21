# DaData FMS Unit Reference Для AutoFin

## Статус И Назначение

- `reference_kind`: `external-vendor-reference`
- `package`: `AutoFin`
- `scope_slug`: `application-card-passport-current-and-previous`
- `checked_at`: `2026-07-21`
- `authority_for_autofin_requirements`: `limited-user-confirmed`
- `authority_ref`: `CLR-PASS-002`
- `governed_by`: `fts/AutoFin/source/PostFinal-v2/PostFinal-v2.docx` и passport approved clarifications

Документ является узкой неизменяемой привязкой публичного контракта DaData к
справочнику подразделений, выдавших паспорт. Он не изменяет общий адресный
`dadata-reference.md` и не инвалидирует старые immutable address benchmark.

## Официальный Контракт

- Документация: `https://dadata.ru/api/suggest/fms_unit/`.
- Endpoint: `POST https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/fms_unit`.
- Тело запроса: UTF-8 JSON с обязательным `query`.
- Поиск выполняется по коду и наименованию подразделения.
- Результат содержит `value`, `unrestricted_value`, `data.code`, `data.name`,
  `data.region_code` и `data.type`.
- Публичный vendor contract не задаёт trigger length, debounce, сортировку,
  точное число строк dropdown или тексты ошибок AutoFin.

По `CLR-PASS-002` этот контракт является `external-dynamic-dictionary` для поля
«Кем выдан» в `BSR 94–95` и заменяет отсутствующий статический проектный
справочник только в этой роли.

## Verified-Once Fixture

- fixture: `FX-DADATA-FMS-POS-001`;
- query: `772-053`;
- минимально подтверждённое число вариантов: `2`;
- конкретный выбираемый вариант: `ОВД ЗЮЗИНО Г. МОСКВЫ`;
- компоненты: `code=772-053`, `name=ОВД ЗЮЗИНО Г. МОСКВЫ`,
  `region_code=77`, `type=2`;
- response SHA-256:
  `5575e4fbb9e28df33d8826a00580594eccde839bb6d625bfa84a6bf53d2bf90e`;
- lifecycle: `verified-once / revalidate-on-failure`;
- evidence:
  `dadata-fixtures/FX-DADATA-FMS-POS-001/FX-DADATA-FMS-POS-001.response.json`
  и соответствующий verification receipt.

Fixture подтверждает воспроизводимый пример ветки `BSR 95` с несколькими
вариантами. Ручной тест-кейс использует сохранённые concrete values и не делает
runtime API-вызов. Fixture не требует от AutoFin показывать все vendor results
или сохранять их vendor-порядок.

## Запреты Для Test Design

- Не превращать vendor defaults в продуктовые обязанности AutoFin.
- Не писать в тест-кейсе динамические формулировки «получить значение во время
  выполнения».
- Не проверять HTTPS-запрос или внутреннюю интеграцию вместо наблюдаемого UI.
- Не придумывать отрицательный FMS fixture без сохранённого live response.
