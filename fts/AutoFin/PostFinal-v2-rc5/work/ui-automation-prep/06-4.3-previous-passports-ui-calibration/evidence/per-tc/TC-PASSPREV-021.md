# TC-PASSPREV-021

Status: `confirmed`

Setup: `Клиент менял паспорт = Да`; previous-passport row visible; `Дата выдачи` left empty.

Action: focus previous-passport `Дата выдачи`, then trigger validation by `Ctrl+Enter` / top UI action `Следующее (Ctrl + Enter)`.

Observed UI result: focused value is `__.__.____`; after validation trigger the field state becomes `required ... invalid`; exact message in previous-passport block: `Введена неверная дата`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/tc-passprev-021-date-empty-after-ctrl-enter.png`

Baseline expected result can be promoted with trigger `Ctrl+Enter` / `Следующее` and exact message `Введена неверная дата`.
