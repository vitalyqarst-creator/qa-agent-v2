# Source Table Normalization Regression

## Цель

Проверить, что writer не строит `Atomic Requirements Ledger` напрямую из загрязненного DOCX/PDF table extraction, а сначала нормализует исходные строки в отдельной секции `Source Table Normalization`.

## Regression Source

Writer-pass для `04-ui-main-info` в `fts/ft-2-OF_5` прошел формальную валидацию, но independent review нашел blocker-дефекты:

- ledger содержал следы исходной таблицы: соседние поля, заголовки колонок и склеенные свойства;
- `Package Test Design Plan` оказался сдвинутым, потому что опирался на загрязненный ledger;
- часть `ATOM-*` была помечена `covered`, хотя внутри atom были неподтвержденные или частичные утверждения;
- internal/API/RabbitMQ/model behavior снова попал в executable coverage без observable artifact.

Корневая причина: между extraction и ledger не было обязательного слоя нормализации источника.

## Must-pass Rules

1. Если scope основан на таблицах, DOCX/PDF extraction или смешанных source blocks, canonical test-case file содержит секцию `Source Table Normalization` до `Atomic Requirements Ledger`.
2. `Source Table Normalization` содержит таблицу с колонками: `source_row_id`, `source_property_id`, `package_id`, `field_or_block`, `property`, `condition`, `expected_behavior`, `requirement_code`, `source_ref`, `confidence`, `gap_id`, `linked_atoms`.
3. Одна строка normalization table описывает одно чистое свойство, условие или ожидаемое поведение.
4. Если одна source row содержит несколько `GSR`/`REQ`, canonical file содержит `Source Row Completeness Matrix`, где каждый код сопоставлен с отдельным `source_property_id`, `ATOM-*` или `GAP-*`.
5. Normalized row не содержит несколько independently checkable `GSR`/`REQ`; например `GSR 1` numeric-only, `GSR 2` max, `GSR 3` min и `GSR 4` amount tags должны стать отдельными rows.
6. Normalized row не смешивает разные semantic property classes: dictionary source, min boundary, max boundary, numeric format, visibility, requiredness, editability, default, integration prefill. Одна source row или один `GSR` могут породить несколько `source_property_id`.
7. В normalized row не должны попадать заголовки исходной таблицы, соседние поля, номера строк, page artifacts или unrelated source fragments.
8. Любая строка с `confidence = low` или `confidence = unclear` связана с `GAP-*`.
9. Каждая normalization row связана с `linked_atoms` или `gap_id`.
10. `Atomic Requirements Ledger` строится только из normalized rows, а не напрямую из грязного extracted text.
11. Low-confidence source rows не могут напрямую становиться `covered` без `GAP-*` и подтвержденного observable behavior.
12. Reviewer обязан считать dirty ledger или compressed normalization blocker-ом, даже если validator без semantic review не нашел ошибок покрытия.
13. Короткий diagnostic-only run должен создавать `source-normalization-diagnostic.md`; validator проверяет его как first-class artifact и не требует создания ledger/TC.
14. Если `source-normalization-diagnostic.md` находится рядом с `source-row-inventory.md` и используется как handoff input, diagnostic должен покрывать все `in_scope = yes/unclear` строки inventory и сохранять все их `GSR-*` / `REQ-*` коды в completeness matrix и normalization rows.

## Fail Examples

- `ATOM-*` содержит фрагмент `Название Видимость О Р Тип ввода поля Тип значения Примечание`.
- `ATOM-*` объединяет несколько полей из одной extracted table row.
- `Source Table Normalization` отсутствует при наличии table extraction residue в ledger.
- `SRC-003` / `Сумма на руки` содержит `GSR 1; GSR 2; GSR 3; GSR 4` в одной normalization row и одном `ATOM-*`.
- `SRC-005` / `Срок кредитования` содержит `property = term_dictionary_and_bounds`, а `expected_behavior` одновременно говорит про справочник, minimum и maximum. Правильно: отдельные rows для `dictionary-source`, `min-boundary`, `max-boundary`.
- В normalization нет `source_property_id` вида `SRC-003.P01`.
- Для source row с несколькими `GSR` нет `Source Row Completeness Matrix`.
- `confidence = low`, но `gap_id = -`.
- Normalization row не связана ни с `ATOM-*`, ни с `GAP-*`.
- `linked_atoms` ссылается на несуществующий `ATOM-*`.
- Internal/API/RabbitMQ/model assertion переносится из source row в `covered` без observable artifact.
- `source-normalization-diagnostic.md` отсутствует или содержит только `Source Table Normalization`, но не содержит `Source Row Completeness Matrix` и `Self-check`.
- `source-normalization-diagnostic.md` использует placeholder `GAP-900` вместо `diagnostic_atom_status = not-created`.
- `source-normalization-diagnostic.md` покрывает только high-risk/gap subset и теряет строки или `GSR-*` / `REQ-*` коды из соседнего `source-row-inventory.md`.
- Diagnostic normalization row не содержит `source_column` / `source_text_fragment`.
- `expected_behavior` в diagnostic row только ссылается на `GSR N`, но не фиксирует конкретное поведение из source text.
- Integration/internal diagnostic row не имеет ни observable behavior, ни реального `GAP-*`.

## Ожидаемый Итог

Новый writer-pass для table-heavy scope должен либо:

- создать нормализацию источника, чистый ledger, корректный package design plan и executable TC;
- либо зафиксировать `GAP-*`/`blocked-input`, если строку источника нельзя надежно нормализовать.

Формально валидный набор без `Source Table Normalization`, но с загрязненным ledger, считается failed regression.
