# Source Row Inventory And Oracle Regression

## Цель

Проверить, что writer не может передать на review формально валидный canonical test-case file, если source rows потеряны или TC не дают исполнимого pass/fail oracle.

Eval фиксирует diagnostic review `fts/ft-2-OF_10 / 05-ui-main-info`, где writer-pass прошел базовый validator, но review нашел пропущенную source row `Место рождения`, generic steps, expected results как пересказ ФТ, requiredness через заполнение поля и `Type: Positive` для rejection/boundary проверок.

## Must-Catch Rules

- Scope-analyzer handoff содержит `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity.
- Package-based writer output содержит `Source Row Inventory` и сверяет его с handoff `source-row-inventory.md`.
- Writer `ready-for-review` блокируется, если writer-side inventory потерял in-scope/unclear `source_row_id` из handoff `source-row-inventory.md`.
- Каждая in-scope source row связана с `ATOM-*` или `GAP-*`.
- Каждый `source_row_id` в `Source Table Normalization` существует в `Source Row Inventory`.
- TC не используют generic steps: `Подготовить ветку`, `Сравнить состояние поля с ожидаемым правилом ФТ`, `Проверить соответствие ФТ`, `Проверить поле согласно ФТ`, `Выполнить проверку значения`.
- `Type: Positive` не используется для rejection, invalid, no-save, below-min или above-max oracle.
- Requiredness marker и requiredness enforcement разделены: marker TC наблюдает visible required indicator, enforcement TC оставляет поле пустым и запускает подтвержденную validation action; если action вне scope, ставится `GAP-*`.
- Expected result описывает observable state, а не только `соответствует ФТ` / `поле принимает только ...` / `поле обязательно к заполнению`.
- TC title называет конкретную проверку, а не шаблон вида `Поле: проверяет Поле ...`.

## Pass Criteria

Validator или pre-review gate создает findings:

- `source-row-inventory-missing`;
- `workflow-state-scope-analyzer-missing-source-row-inventory` с severity `error`, потому что writer не должен стартовать по табличному scope без независимого handoff inventory;
- `workflow-state-ready-for-review-missing-handoff-source-rows`;
- `prompt-format-missing-required-scope-inputs` для отсутствующего `source-row-inventory.md` в `prompt.scope-to-writer.md` / `prompt.scope-to-iteration.md`;
- `source-row-inventory-in-scope-row-without-atom-or-gap`;
- `source-row-inventory-misses-normalized-source-row`;
- `test-case-generic-executable-smell`;
- `test-case-generic-title-smell`;
- `test-case-positive-type-with-negative-oracle`;
- `test-case-generic-expected-result-smell`;
- `test-case-requiredness-without-empty-or-marker-check`.

`validate_agent_artifacts.py --root <package> --fail-on warning` не должен проходить для такого writer draft.

## Fail Criteria

Eval провален, если writer может поставить `ready-for-review`, а validator не показывает warning/error при:

- отсутствующем source-row inventory;
- отсутствующем handoff `source-row-inventory.md` при row-level source parity; для confirmed scope handoff это должен быть `error`, не информационное замечание;
- `prompt.scope-to-writer.md` без ссылки на обязательный `source-row-inventory.md`;
- writer-side `Source Row Inventory` без in-scope/unclear source rows из handoff inventory;
- source row без `ATOM-*` / `GAP-*`;
- generic executable steps;
- expected result как пересказ ФТ;
- `Type: Positive` для rejection/no-save oracle;
- requiredness check без empty-value или visible marker проверки.
