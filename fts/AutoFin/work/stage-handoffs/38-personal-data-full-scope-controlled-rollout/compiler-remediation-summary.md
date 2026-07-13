# Результат подготовки full-scope пакета

## Итог

- Исправлены `SEM-001` и `SEM-002` во входах компилятора.
- Все четыре mapping-артефакта согласованы: 42 атома, 65 обязательств и 47 planned TC.
- Компилятор теперь блокирует расхождение точных множеств TC между ledger, obligation table, design plan и optional decision table.
- Prepared package собран с digest `ccdd820518c583507f769df81834dcbf60265f8c8e0f10236b2272bf3f5b6155`.
- `GAP-001..GAP-003` и `DICT-001` сохранены без придумывания UI-oracle.

## Исправления pipeline

1. Повторяющиеся obligation/plan evidence в source projection устранены; итоговый `source-evidence.md` занимает 45 871 байт и проходит лимит 49 152 байта.
2. Structured writer больше не получает второй полный экземпляр `atomic-obligations.json`. Полная семантика остаётся в source evidence, mapping — в seed, а исходный JSON потребляют gates и reviewer.
3. Реальный writer context уменьшен с 157 908 до 96 886 байт при лимите 131 072.
4. После live-блокера генератор seed исправлен: planned TC groups сортируются по числовому суффиксу до передачи модели.

## Проверки

- 44 compiler/migration теста до live: pass.
- 116 runner/compiler тестов перед live: pass.
- 117 runner/compiler тестов после исправления seed order: pass.
- `agent-layer-fast`: 419 pass, 1 skip.
- `architecture`: 61 checks, 0 findings.
- Реальный post-fix seed: точная последовательность `TC-ACPD-001..TC-ACPD-047`.

## Ограничение результата

Исправление seed order сделано после единственного live-запуска. Оно покрыто тестами и проверено на реальном пакете, но ещё не подтверждено новым writer/reviewer live cycle.
