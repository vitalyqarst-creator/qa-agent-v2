# Regression eval: split reviewer roles и evidence-first review

## Цель

Проверить, что reviewer не выполняет общий “мягкий” review, а разделяет минимум две роли:

1. `traceability reviewer` — проверяет source/code/atom/TC/gap трассировку и regression diff против baseline/revalidation lessons.
2. `test-design/TC-quality reviewer` — проверяет test-design, atomarity, матрицы, expected result observability и mandatory defect classes.

## Входные артефакты

- ФТ содержит требования `GSR 126`, `GSR 127`.
- Previous revalidation artifact фиксирует:
  - `GSR 126` / `ATOM-009` был `gap`, потому что `kladr` не имеет observable artifact;
  - `GSR 127` / `ATOM-010` был `unclear`, потому что точный источник проверки `CorrelationId` не указан.
- Writer создает новый canonical test-case file:
  - теряет код `GSR 126`, оставляя только `section-19`;
  - переводит `ATOM-009` из `gap` в `covered`;
  - добавляет TC с expected result `в модели данных заполнено kladr`;
  - объединяет negative+positive ввод в одном TC: “ввести нечисловое значение, затем ввести допустимое числовое значение”;
  - не добавляет `Dependency Matrix`, хотя `Test-design Applicability Matrix` содержит `dependency = yes`;
  - в package-based scope оставляет часть `TC-*` без `package_id`.

## Ожидаемое поведение reviewer-а

Reviewer должен вернуть `not signed-off` и минимум такие findings:

1. `traceability` / `error`: потерян requirement code `GSR 126`.
2. `traceability` или `expected-result` / `error`: baseline/revalidation diff нарушен — `kladr` был `gap`, но стал `covered` без нового artifact.
3. `expected-result` / `error`: internal/model expected result не имеет наблюдаемого artifact.
4. `atomarity` / `error`: positive+negative input checks объединены в одном `TC-*`.
5. `test-design` / `error|warning`: missing `Dependency Matrix` при `dependency = yes`.
6. `test-design` / `error|warning`: package-based `TC-*` без `package_id`.

## Pass criteria

Eval считается passed, если:

- findings содержат минимум один блок от `traceability reviewer` и минимум один блок от `test-design/TC-quality reviewer`;
- ни один internal/API/model atom не подписан как `covered` без observable artifact;
- reviewer явно ссылается на baseline/revalidation lesson или на отсутствие такого diff как blocking limitation;
- итоговый статус не `signed-off`.

## Failure modes

Eval failed, если reviewer:

- подписывает набор;
- ловит только formatting issues и пропускает fake coverage;
- не замечает потерянный `GSR`;
- принимает `в модели данных заполнено ...` без artifact;
- считает наличие `ATOM-*` ссылки достаточным покрытием без проверки шагов и expected result.

## Regression lesson

Traceability review и test-design review решают разные задачи. Их можно выполнять одним skill-ом, но нельзя смешивать в один общий “quality review”: иначе formal links маскируют плохие expected results, а красивые тест-кейсы маскируют потерянные requirement codes.
