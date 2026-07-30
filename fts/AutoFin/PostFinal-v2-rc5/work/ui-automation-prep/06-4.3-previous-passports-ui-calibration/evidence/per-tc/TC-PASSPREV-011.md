# TC-PASSPREV-011

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `12A4` into previous-passport `Серия`, then blur.

Observed UI result: `A` is filtered; while focused value is `124_`; after blur the field clears, state becomes `invalid empty required`, message `Обязательно к заполнению`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/fresh-tc-passprev-011-series-12A4.png`

Baseline expected result remains valid; exact UI mechanism should be added to automation-ready version.
