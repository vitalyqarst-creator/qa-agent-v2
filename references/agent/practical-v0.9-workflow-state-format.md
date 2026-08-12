# Формат `workflow-state.json` practical v0.9

```json
{
  "schema_version": 1,
  "route_version": "practical-v0.9",
  "scope_id": "01",
  "scope_slug": "9.1-menu-upravleniya-partnerami",
  "phase": "scope",
  "next_action": "Создать матрицу тест-дизайна",
  "matrix_review_required": false,
  "contract_versions": {
    "route": "practical-v0.9",
    "source_package": "source-package-v2"
  },
  "artifacts": {
    "source_package_manifest": "work/practical-v0.9/source-package-manifest.json",
    "scope_obligations": "work/practical-v0.9/<scope>/scope-obligations.json",
    "test_design_matrix": "not-created",
    "canonical_test_cases": "not-created",
    "validator_report": "not-created"
  },
  "reviews": [],
  "revision_count": 0,
  "final_verdict": "not-finalized",
  "decision_notes": []
}
```

`reviews` хранит только режим, вердикт и пути завершённых независимых review;
findings reviewer-а в него не дублируются. Если правило сложности требует review
матрицы, scope не может перейти в `test-cases`, пока не появится запись `matrix`
с вердиктом `approved`. Scope не может перейти в `accepted`, пока не появится
запись `test-cases` с вердиктом `approved`.

`revision_count` — число уже разрешённых содержательных доработок после review;
для v0.9 допустимы только `0` и `1`. Второй `changes-required` не запускает
новый repair-loop: scope получает честный `blocked` до решения пользователя.
`final_verdict`: `not-finalized`, `approved`, `changes-required` или
`blocked-input`.

`workflow-state.json` — единственный mutable control-plane artifact v0.9. Не копируй его поля в отдельный summary. Человекочитаемый статус формируется из него и `validator-report.json` в ответе агенту.

`phase`: `scope`, `matrix`, `test-cases`, `review`, `accepted` или `blocked`.
