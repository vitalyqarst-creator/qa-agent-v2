# TC-PASSPREV-010

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `12345` into previous-passport `Серия`, then blur.

Observed UI result: UI keeps `1234`, ignores the 5th digit, field state `valid`, no message.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/fresh-tc-passprev-010-series-12345.png`

Baseline expected result remains valid if interpreted as length enforcement by truncation/ignored extra input.
