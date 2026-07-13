# Source Row Inventory

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-002` | `WP-COND` | Поле `Визуальная информация`: default и multiple-selection trigger | `SRC-002.P02`; `SRC-002.P04`; DOCX Table 4 | `BSR 312`; `BSR 313` | `yes` | canonical `ATOM-002`; `ATOM-013`; canary `ATOM-COND-001`; `ATOM-COND-005` |
| `SRC-003` | `WP-COND` | Список `Параметры визуальной оценки`: show/hide, `Другое`, requiredness | `SRC-003.P01`; `SRC-003.P02`; `SRC-003.P05`..`SRC-003.P08`; DOCX Table 4 | `BSR 314`; `BSR 315`; `BSR 316`; `BSR 317` | `yes` | canonical `ATOM-004`; `ATOM-005`; `ATOM-008`; `ATOM-009`; `ATOM-010`; `ATOM-013`; canary `ATOM-COND-002`..`ATOM-COND-006`; `GAP-COND-001` |
| `SRC-005` | `WP-COND` | Fixture: `Запах алкоголя / перегара / сильный запах духов, перебивающий перегар` | Appendix 1; `DICT-101` | `no_requirement_code:SRC-005` | `yes` | canonical `ATOM-006`; `ATOM-007`; canary `ATOM-COND-005` |
| `SRC-006` | `WP-COND` | Fixture: `Отечность, нездоровый цвет лица, синяки под глазами` | Appendix 1; `DICT-101` | `no_requirement_code:SRC-006` | `yes` | canonical `ATOM-006`; `ATOM-007`; canary `ATOM-COND-005` |
| `SRC-009` | `WP-COND` | Fixture: `Другое (комментарий обязателен)` | Appendix 1; `DICT-101` | `no_requirement_code:SRC-009` | `yes` | canonical `ATOM-006`; `ATOM-009`; canary `ATOM-COND-004`; `GAP-COND-001` |
