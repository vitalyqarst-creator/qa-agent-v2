# Source Row Inventory

| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-004` | `WP-NUM` | `Адрес регистрации / Почтовый индекс`: только 6 числовых символов | `SRC-004.P02`; `DOCX row 035`; `PDF page 19` | `BSR 116` | `yes` | canonical `ATOM-011`; canary `ATOM-NUM-001`; `GAP-002`; `GAP-NUM-001` |
| `SRC-011` | `WP-NUM` | `Адрес регистрации / Корпус`: только числовые символы | `SRC-011.P02`; `DOCX row 042`; `PDF page 20` | `BSR 124` | `yes` | canonical `ATOM-011`; canary `ATOM-NUM-002`; `GAP-002`; `GAP-NUM-001` |
| `SRC-012` | `WP-NUM` | `Адрес регистрации / Квартира`: только числовые символы | `SRC-012.P02`; `DOCX row 043`; `PDF page 20` | `BSR 126` | `yes` | canonical `ATOM-011`; canary `ATOM-NUM-003`; `GAP-002`; `GAP-NUM-001` |
| `SRC-025` | `WP-NUM` | `Фактический адрес / Квартира`: только числовые символы | `SRC-025.P03`; `DOCX row 056`; `PDF page 22` | `BSR 151` | `yes` | canonical `ATOM-032`; canary `ATOM-NUM-004`; `GAP-002`; `GAP-NUM-001` |
| `SRC-026` | `WP-NUM` | `Фактический адрес / Почтовый индекс`: только 6 числовых символов | `SRC-026.P02`; `DOCX row 057`; `PDF page 22` | `BSR 153` | `yes` | canonical `ATOM-032`; canary `ATOM-NUM-005`; `GAP-002`; `GAP-NUM-001` |
