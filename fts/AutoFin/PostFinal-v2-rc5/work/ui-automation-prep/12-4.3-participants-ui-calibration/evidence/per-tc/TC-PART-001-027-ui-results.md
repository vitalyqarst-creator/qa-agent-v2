# Per-TC UI results: 12-4.3-participants

## confirmed-ui-ready

- `TC-PART-001`: `Добавить созаемщика` visible.
- `TC-PART-003`: calculator widget absent inside embedded co-borrower section.
- `TC-PART-005`: `Добавить залогодателя` visible.
- `TC-PART-007`: pledgor exclusion list confirmed absent inside embedded pledgor section.
- `TC-PART-010`: `EDIT` visible.
- `TC-PART-011`: `EDIT` disabled without selected row.
- `TC-PART-014`: `DELETE` visible.
- `TC-PART-015`: `DELETE` disabled without selected row.
- `TC-PART-020`: `Тип участия` column visible.
- `TC-PART-022`: `ФИО` column visible.
- `TC-PART-024`: `Паспорт` column visible.
- `TC-PART-026`: `ID клиента` column visible.

## needs-test-case-update

- `TC-PART-002`: actual UI adds embedded same-page section `Добавление созаемщика`; no separate modal/window or route change observed.
- `TC-PART-006`: actual UI adds embedded same-page section `Добавление залогодателя`; no separate modal/window or route change observed.

## mismatch-ft-ui

- `TC-PART-004`: co-borrower role replacement is partial; `Клиент менял ФИО`, `ID Клиента`, `ИНН клиента`, and `...с клиентом...` remain.
- `TC-PART-008`: pledgor role replacement is partial; `Клиент менял ФИО`, `ID Клиента`, and `...с клиентом...` remain.

## blocked

- `TC-PART-009`: no concrete UI place/oracle for default borrower-as-pledgor was identified.
- `TC-PART-012`: requires an existing participant row; row setup blocked by required fields/documents.
- `TC-PART-013`: requires an existing participant row; row setup blocked.
- `TC-PART-016`: requires an existing participant row; row setup blocked.
- `TC-PART-017`: requires an existing participant row; row setup blocked.
- `TC-PART-018`: requires an existing participant row; row setup blocked.
- `TC-PART-019`: requires an existing participant row; row setup blocked.
- `TC-PART-021`: requires an existing participant row with type value; row setup blocked.
- `TC-PART-023`: requires an existing participant row with FIO value; row setup blocked.
- `TC-PART-025`: requires an existing participant row with passport value; row setup blocked.
- `TC-PART-027`: requires saved application and ABS ID oracle; also no participant row was available.

