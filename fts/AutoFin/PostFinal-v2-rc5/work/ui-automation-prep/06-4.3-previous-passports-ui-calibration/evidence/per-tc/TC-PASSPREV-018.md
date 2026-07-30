# TC-PASSPREV-018

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `111111` into previous-passport `Номер`.

Observed UI result: value remains `111111`; field state `invalid`; exact message `Не должно быть шести одинаковых цифр подряд`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/tab-tc-passprev-018-number-111111.png`

Baseline expected result remains valid; add exact message to automation-ready version.
