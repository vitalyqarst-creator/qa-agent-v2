## Fixture Catalog

| fixture_id | purpose | fixture_data | used_by | cleanup |
| --- | --- | --- | --- | --- |
| `FIX-ACPD-001` | Current FIO positive values | `Иванов-Петров`; `Анна-Мария`; `Сергеевич` | `TC-ACPD-003`; `TC-ACPD-005`; `TC-ACPD-007` | Discard unsaved changes. |
| `FIX-ACPD-002` | Date boundaries | `D-18y`; `D-100y`; invalid `D-18y+1d`; `D+1`; `D-100y-1d` | `TC-ACPD-014`; `TC-ACPD-015`; `TC-ACPD-026`..`TC-ACPD-028` | Discard unsaved changes. |
| `FIX-ACPD-003` | Previous FIO positive values | `Сидорова-Петрова`; `Мария-Анна`; `Игоревна` | `TC-ACPD-033`; `TC-ACPD-034`; `TC-ACPD-037`; `TC-ACPD-038`; `TC-ACPD-042`; `TC-ACPD-043`; `TC-ACPD-046` | Set `Клиент менял ФИО=Нет` or discard changes. |
| `FIX-ACPD-004` | Gender dictionary | `Мужчина`; `Женщина` | `TC-ACPD-011`; `TC-ACPD-012` | Discard unsaved changes. |
