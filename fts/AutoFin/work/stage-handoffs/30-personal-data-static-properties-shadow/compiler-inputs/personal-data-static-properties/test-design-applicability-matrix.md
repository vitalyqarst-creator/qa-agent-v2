# Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `field-property` | `yes` | XHTML rows 57–59; `BSR 47`; `BSR 50`; `BSR 53` | Проекция включает видимость, control type и value type трех полей. | `ATOM-001`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `ATOM-014`; `ATOM-015` | `TC-PDSP-001`; `TC-PDSP-004`; `TC-PDSP-005`; `TC-PDSP-006`; `TC-PDSP-009`; `TC-PDSP-010`; `TC-PDSP-011`; `TC-PDSP-014`; `TC-PDSP-015` |  |
| `requiredness` | `yes` | XHTML rows 57–59; DOCX table 6 rows 4–6 | Проекция включает обязательность или необязательность каждого поля. | `ATOM-002`; `ATOM-007`; `ATOM-012` | `TC-PDSP-002`; `TC-PDSP-007`; `TC-PDSP-012` |  |
| `editability` | `yes` | XHTML rows 57–59; DOCX table 6 rows 4–6 | Проекция включает редактируемость каждого поля. | `ATOM-003`; `ATOM-008`; `ATOM-013` | `TC-PDSP-003`; `TC-PDSP-008`; `TC-PDSP-013` |  |
| `format` | `no` | `BSR 48`; `BSR 51`; `BSR 54` | Ограничения символов остаются в полном parent scope. | `none_required:out_of_shadow` |  |  |
| `integration` | `no` | `BSR 49`; `BSR 52`; `BSR 55` | DaData остается в полном parent scope. | `none_required:out_of_shadow` |  |  |
| `dependency` | `no` | section 4.3 parent scope | Условные предыдущие ФИО не входят в эту статическую проекцию. | `none_required:out_of_shadow` |  |  |
| `scope` | `no` | `application-card-client-personal-data` | Eval-only projection не заменяет полный production scope. | `none_required:eval-only` |  |  |
