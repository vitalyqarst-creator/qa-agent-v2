# TC-PASSPREV-004

Status: `confirmed`

Setup: `Клиент менял паспорт = Да`; one previous-passport row is already visible.

Action: click `ДОБАВИТЬ ПАСПОРТ`.

Observed UI result: a second `Предыдущий паспорт` row is added. Each row contains `Серия`, `Номер`, `Дата выдачи`, and a delete/trash control. `ДОБАВИТЬ ПАСПОРТ` remains visible.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/previous-passports-after-add-second-row.png`

Baseline needs clarification: initial row appears on flag enable; `Добавить паспорт` adds an additional row.
