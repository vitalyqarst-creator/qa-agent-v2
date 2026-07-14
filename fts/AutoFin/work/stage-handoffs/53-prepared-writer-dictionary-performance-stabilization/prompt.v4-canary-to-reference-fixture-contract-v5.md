# Prompt: V4 Canary -> Reference Fixture Contract V5

Продолжи улучшение агента после terminal V4 canary blocker.

Обязательные inputs:

- `workflow-state.yaml`
- `live-result.v4-r1.json`
- `performance-analysis.v4.md`
- `terminal-stop-gate.v4.md`
- r1 writer draft, reviewer findings и immutable prepared package

Задача:

1. Не повторять V4 и не исправлять benchmark draft вручную.
2. Разобрать transport `test_intent`, `dictionary_requirements` и runner-generated draft seed для OBL-013.
3. Спроектировать first-class exact fixture contract для `reference-only` сценариев. Предпочтительный вариант: compiler переносит конкретные plan values в структурное obligation field, runner seed материализует их один раз в test data/action, deterministic gate проверяет сохранение до reviewer.
4. Не переносить в writer exhaustive payload OBL-006/OBL-007 и не ослаблять новый ownership gate.
5. Добавить negative regression на обобщение «два обычных значения», positive regression на exact values и offline replay V4-r1 draft.
6. Провести full offline suite и architecture audit.
7. Создать новый immutable V5 package/cycle и отдельный pre-live checkpoint. Live запрещён без новой hash-bound authorization.

Критерий готовности: generic reference-only fixture не проходит deterministic gate; exact fixture проходит; exhaustive dictionary остаётся runner-owned; production baseline не изменён.
