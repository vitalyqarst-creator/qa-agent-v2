# Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `format` | `yes` | `BSR 48`; `BSR 51`; `BSR 54` | Scope состоит из allowed и disallowed character classes для трех независимых полей. | `ATOM-001..ATOM-012` | `TC-PDCR-001..TC-PDCR-012` | `GAP-001` |
| `equivalence-partitioning` | `yes` | `BSR 48`; `BSR 51`; `BSR 54` | Отдельные классы: текст, дефис, цифра, иной специальный символ. | `ATOM-001..ATOM-012` | `TC-PDCR-001..TC-PDCR-012` | `GAP-001` |
| `negative-oracle` | `yes` | `SO-NEG-001..SO-NEG-006` | Шесть invalid-class candidates требуют UI calibration без выдумывания точного механизма. | `ATOM-003`; `ATOM-004`; `ATOM-007`; `ATOM-008`; `ATOM-011`; `ATOM-012` | `TC-PDCR-003`; `TC-PDCR-004`; `TC-PDCR-007`; `TC-PDCR-008`; `TC-PDCR-011`; `TC-PDCR-012` | `GAP-001` |
| `integration` | `no` | `BSR 49`; `BSR 52`; `BSR 55` | DaData исключена из projection. | `none_required:out_of_shadow` |  |  |
| `requiredness` | `no` | XHTML rows 57–59 | Уже проверяется отдельным static-properties shadow scope. | `none_required:out_of_shadow` |  |  |
| `dependency` | `no` | section 4.3 parent scope | Условные предыдущие ФИО не входят в projection. | `none_required:out_of_shadow` |  |  |
| `scope` | `no` | `application-card-client-personal-data` | Eval-only projection не заменяет полный production scope. | `none_required:eval-only` |  |  |
