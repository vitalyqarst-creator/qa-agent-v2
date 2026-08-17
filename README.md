# QA Test Case Runtime v1

Отдельная минимальная среда для подготовки тест-кейсов по ФТ. Открывайте в Codex именно эту папку:

`C:\Users\Пользователь\Documents\Виталя\GitProjects\qa-agent-v2-runtime-v1`

## Что здесь есть

- четыре runtime skill-а: source locator, scope analyzer, writer, independent reviewer;
- обязательная подготовка конкретных тестовых данных до matrix и TC;
- валидаторы fixture catalog и production TC;
- FT-пакеты в `fts/`.

Каждый FT-пакет создаётся пустым: в него попадают только собственные источники, support, mockups, work и test-cases. Он не наследует содержимое репозитория разработки.

## Чего здесь нет

- `evals`, benchmark, historical canary и release-артефактов;
- legacy iteration, sharding и автоматических бесконечных review-циклов;
- UI-prep как автоматического продолжения после выпуска TC.

## Обычная работа

1. Создайте пустой пакет: `python scripts/create_ft_package.py fts/<проект>/<FT>`.
2. Поместите в него только исходные материалы данного ФТ: DOCX/XHTML/PDF в `source/`, нужные справочники и утверждённые ответы БА в `support/`, приложенные макеты в `mockups/`.
3. Откройте эту runtime-папку в Codex.
4. Дайте короткую задачу: «Начни practical route для FT-пакета `<полный путь>`. Сначала выполни `ft-source-locator`».
5. После scope analysis агент обязан подготовить конкретные данные или честно оставить неполные обязанности в `coverage-gaps.md` и вопросах к БА.
6. В `test-cases/` попадают только исполнимые TC.

Перед каждым выпуском используйте:

```powershell
python scripts/validate_runtime_scope.py <FT-пакет> <scope-handoff>
python scripts/validate_fixture_catalog.py <путь-к-fixture-catalog.json>
python scripts/validate_runtime_matrix.py <путь-к-matrix.md> --source-inventory <путь-к-source-row-inventory.md> --coverage-gaps <путь-к-coverage-gaps.md>
python scripts/validate_runtime_tc.py <путь-к-test-cases.md> --matrix <путь-к-matrix.md>
python scripts/validate_runtime_tree.py
```
