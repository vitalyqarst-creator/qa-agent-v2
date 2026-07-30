# TC-PASSPREV-006

Status: `confirmed`

Setup: `Клиент менял паспорт = Да`; two previous-passport rows are present.

Action: click delete/trash on the second row.

Observed UI result: the whole second previous-passport row is removed immediately. The first row remains. No JavaScript confirmation dialog appeared.

Observed delete set: one row containing `Серия`, `Номер`, `Дата выдачи`. Controls `Код подразделения`, `Кем выдан`, and `Ввести вручную подразделение` are not present in previous-passport rows.

Evidence:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/previous-passports-after-add-second-row.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/previous-passports-after-delete-second-row.png`

Baseline can be promoted from blocked-observability using this observed delete set.
