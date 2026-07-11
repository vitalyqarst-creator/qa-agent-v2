# Cross-scope prepared pipeline: blocker report

## Статус

`blocked-input`; live writer/reviewer validation не запускалась, promotion выключена.

## Реальный блокер

Первый обязательный scope матрицы — numeric/validation — был выбран из реального пакета `fts/ft-2-OF_17`:

- scope: `2-1-1-1-1-2-ui-employment-canary-v25-numeric-taxonomy-clean`;
- atomic ledger: `fts/ft-2-OF_17/work/test-design/2-1-1-1-1-2-ui-employment-canary-v25-numeric-taxonomy-clean/atomic-requirements-ledger.md`;
- design plan: `fts/ft-2-OF_17/work/test-design/2-1-1-1-1-2-ui-employment-canary-v25-numeric-taxonomy-clean/package-test-design-plan.md`;
- dictionary inventory: `fts/ft-2-OF_17/work/test-design/2-1-1-1-1-2-ui-employment-canary-v25-numeric-taxonomy-clean/dictionary-inventory.md`.

В `fts/ft-2-OF_17/source/` найдены:

- `ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.docx`;
- `ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.pdf`.

Обязательный `.xhtml`/`.html` для основного ФТ отсутствует. Это нарушает глобальный source contract: DOCX остаётся source of truth, но XHTML обязателен как machine-readable extraction source; PDF не может его заменить.

## Почему continuation запрещён

- Prepared package v3 требует одновременно зарегистрированные DOCX `source-of-truth` и XHTML/HTML `machine-readable`.
- Compiler обязан блокировать неоднозначный или неполный source registry.
- Запуск writer/reviewer только по DOCX/PDF нарушил бы source fidelity и сделал бы сравнение трёх scope несопоставимым.
- Автоматический retry, выбор случайного HTML или незаявленная замена numeric scope маскировали бы обязательный missing input.

## Состояние матрицы

| scope class | candidate | preflight result | live run |
| --- | --- | --- | --- |
| numeric/validation | `ft-2-OF_17/.../ui-employment-canary-v25-numeric-taxonomy-clean` | `blocked-input`: mandatory XHTML missing | not started |
| dictionary/fixed values | `AutoFin/.../section-18-visual-assessment-criteria` | not evaluated after blocker | not started |
| multi-obligation with gaps | `AutoFin/.../3-iteration-smoke-widget-selection-types` | not evaluated after blocker | not started |

## Выполненный checkpoint до обнаружения блокера

- Добавлен dependency-free compiler `workflow-state.yaml -> immutable prepared package`.
- Compiler строит obligations из canonical atomic ledger + design plan и блокирует testable atom без observable plan oracle.
- Добавлены gates для linked gaps, dictionary inventory, exact source refs и DOCX/XHTML source registry.
- Добавлен promotion dry-run, который проверяет production drift, draft hash, destination и overwrite guard без записи в `test-cases/`.
- Production promotion не включалась; production test cases не изменялись.

## Обязательный missing input для продолжения

Добавить в `fts/ft-2-OF_17/source/` XHTML/HTML-экспорт того же основного ФТ и подтвердить его соответствие выбранному DOCX в source-selection/source-parity artifacts. После этого создать новый immutable benchmark cycle; текущий blocker report не переписывать.
