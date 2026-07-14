# Architecture Decision: exact reference fixtures

## Решение

В package v8 `reference-only` dictionary requirement может хранить ограниченный точный набор `fixture_values`. Compiler извлекает только значения, явно названные в design plan, runner один раз материализует их в draft и deterministic gate проверяет сохранение до reviewer.

Package v1-v7 остаются читаемыми с прежней семантикой. Формат v7 не меняется задним числом.

## Границы ответственности

- Compiler: связывает точные plan values с `DICT-*` и сохраняет group path.
- Prepared package: immutable source-backed transport `fixture_values`.
- Writer: пишет действия и oracle; не заменяет exact fixture обобщением.
- Runner: добавляет canonical fixture block из package после writer response.
- Gate: останавливает draft при отсутствии или неполной проекции.
- Reviewer: получает уже проверенный materialized draft.

## Неизменённые контракты

- Exhaustive `full-hierarchy`/`all-leaf-values` остаются runner-owned через `required_values`.
- `reference-only` не становится exhaustive coverage.
- FT-first production baseline не переписывается.
- Generic plan без явно названных source-backed values не превращается в выдуманную fixture.

## Trade-off

Canonical block ограничивает свободу форматирования test data, но устраняет зависимость от prompt adherence. Это оправдано только для bounded exact fixtures; переносить тем же способом произвольный prose intent нельзя.
