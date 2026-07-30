# TC-PASSPREV-016

Status: `confirmed`

Setup: fresh new application card; `Клиент менял паспорт = Да`.

Action: manually enter `1234567` into previous-passport `Номер`.

Observed UI result: UI keeps `123456`, ignores the 7th digit, field state `valid`, no message.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/tab-tc-passprev-016-number-1234567.png`

Baseline expected result remains valid if interpreted as length enforcement by truncation/ignored extra input.
