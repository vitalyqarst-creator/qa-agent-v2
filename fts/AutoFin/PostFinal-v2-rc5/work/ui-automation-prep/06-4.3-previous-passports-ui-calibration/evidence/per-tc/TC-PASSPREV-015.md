# TC-PASSPREV-015

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `12345` into previous-passport `Номер`.

Observed UI result: value is `12345_`; field state `invalid`; message `Обязательно к заполнению`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/tab-tc-passprev-015-number-12345.png`

Baseline expected result remains valid; exact UI mechanism should be added to automation-ready version.
