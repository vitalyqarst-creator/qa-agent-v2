# TC-PASSPREV-017

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `12345A` into previous-passport `Номер`.

Observed UI result: `A` is filtered; value remains `12345_`; field state `invalid`; message `Обязательно к заполнению`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/tab-tc-passprev-017-number-12345A.png`

Baseline expected result remains valid; exact UI mechanism should be added to automation-ready version.
