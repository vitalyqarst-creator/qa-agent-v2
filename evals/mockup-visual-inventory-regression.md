# Mockup Visual Inventory Regression

## Цель

Проверить, что UI scope с макетами не передается writer-у как текстовая задача без визуального анализа макета.

Регрессия, которую ловит eval: агент видел `mockups/Основная информация.png`, но не открыл изображение и написал generic UI steps. Это ухудшило точность шагов и позволило подменить реальные элементы экрана пересказом ФТ.

## Входной сценарий

- FT package содержит основной ФТ, PDF и папку `mockups/`.
- Пользователь выбирает UI scope, например `ui-main-info`.
- `scope-contract.md` или package context ссылается на mockup / screen image / `mockups/`.
- Writer запускается без дополнительных пользовательских подсказок.

## Must-Catch Rules

- `ft-scope-analyzer` обязан открыть mockup визуально и создать `mockup-visual-inventory.md` до handoff к writer.
- `mockup-visual-inventory.md` обязан фиксировать `mockup_path`, `opened`, `method`, `screen_name`, `visible_blocks`, `visible_fields`, `visible_actions`, `interaction_hints`, `mockup_only_items`, `ft_conflicts`, `used_for_steps`, `not_used_as_requirement_source`.
- Если `opened != yes`, workflow должен быть `blocked-input`, а не `ready-for-next-stage` / `ready-for-review`.
- Writer обязан использовать inventory для конкретизации UI steps и не должен использовать generic steps вида `перейти к нужному элементу`, `ввести или выбрать значение`, `привести данные к состоянию`.
- Mockup не является источником бизнес-правил: allowed values, обязательность, validation и expected result должны ссылаться на ФТ/source artifacts. Mockup-only элементы идут в `GAP-*` / conflict.
- Reviewer обязан считать отсутствие inventory, generic steps при доступных interaction hints или mockup-derived requirements blocking finding.

## Pass Criteria

Eval считается успешным, если:

- `validate_agent_artifacts.py --root <package> --fail-on warning` не пропускает writer `ready-for-review` для UI scope с mockup, если нет linked `mockup-visual-inventory.md`;
- generic UI steps при `used_for_steps = yes` ловятся как `test-case-mockup-interaction-hints-not-used`;
- валидный `mockup-visual-inventory.md` проходит проверку и учитывается в summary как `mockup_visual_inventories_checked`;
- `Writer Quality Gate` содержит row `mockup-visual-inventory`;
- reviewer findings используют category `test-design`, `expected-result` или `coverage` для нарушений mockup usage.

## Fail Criteria

Eval провален, если:

- writer может поставить `ready-for-review`, хотя mockup указан в scope, но inventory отсутствует;
- inventory содержит `opened = no`, но workflow не блокируется;
- test cases содержат generic UI steps при наличии visual interaction hints;
- mockup-only элемент становится `covered` requirement без подтверждения ФТ.

## Regression Lesson

Макет нужен не как дополнительный источник требований, а как evidence для точности ручных действий. Если агент не открывает макет, он продолжает писать исполнимые только формально шаги. Поэтому visual inventory должен быть отдельным артефактом и отдельным gate, а не фразой в session log.
