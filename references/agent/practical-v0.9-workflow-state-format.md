# Формат `workflow-state.json` practical v0.9

Создавай новый `workflow-state.json` только командой
`scripts/init_practical_v09_workflow.py`. Канонический пример с актуальными
версиями contracts генерируется тем же runtime builder-ом и хранится в
[practical-v0.9-workflow-state.json](examples/practical-v0.9-workflow-state.json).
Не копируй JSON из Markdown вручную.

`workflow-state.json` — единственный mutable control-plane artifact v0.9.
Он хранит scope, фазу, пути artifacts, историю review, независимые budgets
`matrix_revision_count` и `tc_revision_count`, `final_verdict`, краткие
`decision_notes` и `review_triage`. Человекочитаемый статус формируется из
него и `validator-report.json` в ответе агента.

Матрица — владелец test-design truth: `SCN-*` и решения `CON-*` находятся в
`test-design-matrix.md`, а не в workflow state. Если сценарии объединяются
или один ненаблюдаемый сценарий покрывается наблюдаемым результатом, добавь
раздел `## Решения о консолидации сценариев` с одним JSON-массивом решений.
При отсутствии таких решений раздел не требуется.

`reviews` хранит только режим, verdict и пути завершённых независимых review;
findings reviewer-а в него не дублируются. Matrix review обязателен для
каждого нового scope до test cases; final TC review обязателен до acceptance.

`clarification_outcome-v1` сохраняет обязательный
`scope_clarification_requests`: либо карточки `CLR-*`, либо явную русскую
отметку об отсутствии вопросов БА. Файл входит в immutable review snapshot.

`phase`: `scope`, `matrix`, `test-cases`, `review`, `accepted` или `blocked`.
