# TC-PASSPREV-008

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `1234` into previous-passport `Серия`, then blur.

Observed UI result: value remains `1234`; field state `valid`; no message.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/fresh-tc-passprev-008-series-1234.png`

Baseline expected result remains valid.
