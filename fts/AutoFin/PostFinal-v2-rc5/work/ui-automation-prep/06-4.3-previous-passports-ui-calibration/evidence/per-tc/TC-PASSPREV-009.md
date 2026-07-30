# TC-PASSPREV-009

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `123` into previous-passport `Серия`, then blur.

Observed UI result: while focused value is `123_`; after blur the field clears, state becomes `invalid empty required`, message `Обязательно к заполнению`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/fresh-tc-passprev-009-series-123.png`

Baseline expected result remains valid; exact UI mechanism should be added to automation-ready version.
