# Package Test Design Plan Regression

## Цель

Проверить, что writer не переходит от ledger сразу к `TC-*`, а сначала фиксирует test-design plan по каждому internal work package.

## Regression Source

Fresh writing check для `04-ui-main-info` показал, что package workflow улучшил traceability, но writer все еще создал слабые TC: псевдошаги `Установить условие`, неполные positive/negative ветки, слабое length/equivalence coverage и неполное action-flow coverage.

## Must-pass Rules

1. Canonical test-case file содержит `Package Test Design Plan`.
2. Каждый `WP-*` представлен в plan.
3. Каждый применимый `ATOM-*` связан с `design_item_id`.
4. Validation rules имеют отдельные plan rows для positive, negative/equivalence и boundary classes.
5. `only if`, dependency и action-flow rules имеют отдельные branches или `GAP-*`.
6. Internal/API/RabbitMQ/model/database behavior без observable artifact связан с `GAP-*`, а не с executable `TC-*`.
7. Каждый executable plan row ссылается на существующий `TC-*`.
8. Один `TC-*` не используется как `planned_tc_or_gap` для нескольких независимых executable rows.
9. `input_class` и `single_expected_behavior` фиксируют один класс входа и один oracle, без объединения valid/invalid.
8. Reviewer не ставит `signed-off`, если plan отсутствует, generic или не покрывает применимые atoms/classes.

## Fail Examples

- `planned_check = Проверить требование GSR 12`.
- `planned_check = Установить условие и проверить результат`.
- Один plan row: `валидное/невалидное значение`.
- Две строки plan: `positive` и `negative`, но обе ссылаются на один `TC-*`.
- `planned_tc_or_gap = -` для применимого atom.
- `GSR 121` / `GSR 122` internal behavior помечены `TC-*` без observable artifact.

## Ожидаемый Итог

Новый writer-pass должен либо дать полноценный plan и executable TC, либо остановиться в `blocked-input`/`gap`. Формально валидный набор без plan считается failed regression.
