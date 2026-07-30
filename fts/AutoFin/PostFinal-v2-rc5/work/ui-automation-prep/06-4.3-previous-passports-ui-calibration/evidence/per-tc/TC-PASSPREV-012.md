# TC-PASSPREV-012

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `1112` into previous-passport `Серия`, then blur.

Observed UI result: value remains `1112`; field state `invalid`; exact message `Не должно быть трех одинаковых цифр подряд`.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/fresh-tc-passprev-012-series-1112.png`

Baseline expected result remains valid; add exact message to automation-ready version.
