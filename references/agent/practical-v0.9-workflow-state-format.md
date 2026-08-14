# Формат `workflow-state.json` practical v0.9

```json
{
  "schema_version": 1,
  "route_version": "practical-v0.9",
  "scope_id": "01",
  "scope_slug": "9.1-menu-upravleniya-partnerami",
  "phase": "scope",
  "next_action": "Создать матрицу тест-дизайна",
  "matrix_review_required": true,
  "contract_versions": {
    "route": "practical-v0.9",
    "source_package": "source-package-v4",
    "matrix": "practical-matrix-v3",
    "scenario_consolidation": "scenario-consolidation-v2",
    "controller_triage": "controller-triage-v1",
    "clarification_outcome": "clarification-outcome-v1",
    "execution_context": "execution-context-v1",
    "source_parity": "source-parity-v1",
    "exception_snapshot": "exception-snapshot-v1"
  },
  "artifacts": {
    "source_package_manifest": "work/practical-v0.9/source-package-manifest.json",
    "scope_obligations": "work/practical-v0.9/<scope>/scope-obligations.json",
    "scope_clarification_requests": "work/practical-v0.9/<scope>/scope-clarification-requests.md",
    "test_design_matrix": "not-created",
    "canonical_test_cases": "not-created",
    "validator_report": "not-created"
  },
  "reviews": [],
  "matrix_revision_count": 0,
  "tc_revision_count": 0,
  "final_verdict": "not-finalized",
  "decision_notes": [],
  "scenario_consolidation": [],
  "review_triage": []
}
```

`reviews` хранит только режим, вердикт и пути завершённых независимых review;
findings reviewer-а в него не дублируются. Matrix review обязателен для каждого
нового scope: scope не может перейти в `test-cases`, пока не появится запись
`matrix` с вердиктом `approved`. Scope не может перейти в `accepted`, пока не появится
запись `test-cases` с вердиктом `approved`.

`matrix_revision_count` и `tc_revision_count` — числа уже разрешённых
содержательных доработок соответствующей фазы; для каждого допустимы только
`0` и `1`. Второй принятый `changes-required` не запускает новый
repair-loop: scope получает честный `blocked` до решения пользователя.
`final_verdict`: `not-finalized`, `approved`, `changes-required` или
`blocked-input`.

`workflow-state.json` — единственный mutable control-plane artifact v0.9. Не копируй его поля в отдельный summary. Человекочитаемый статус формируется из него и `validator-report.json` в ответе агенту.

`scenario_consolidation` хранит только `CON-*` решения по кандидатам, а не
новый рабочий артефакт. Старый scope без его версии остаётся читаемым, новые
создаются с `scenario-consolidation-v1`.

`review_triage` хранит только controller-решения по immutable raw
`changes-required` verdict: SHA-256 результата, режим review и по одному
решению на content blocking finding. Raw JSON reviewer-а не переписывается.
Новый scope создаётся с `controller-triage-v1`; legacy scope без версии
остаётся читаемым без неявной миграции.

`clarification_outcome-v1` означает, что `scope_clarification_requests`
обязателен: это либо список карточек `CLR-*`, либо явная русскоязычная
отметка об отсутствии вопросов БА. Файл входит в snapshot независимого review.

`phase`: `scope`, `matrix`, `test-cases`, `review`, `accepted` или `blocked`.

Новый scope создаётся только командой `init_practical_v09_workflow.py`; не
копируй пример выше вручную. Регрессионный contract-sync test проверяет, что
результат команды содержит актуальные версии contracts.
