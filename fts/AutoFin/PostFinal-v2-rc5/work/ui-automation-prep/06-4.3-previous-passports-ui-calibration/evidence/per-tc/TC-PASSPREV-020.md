# TC-PASSPREV-020

Status: `blocked-observability`

Setup: `Клиент менял паспорт = Да`; previous-passport row visible.

Action: inspect behavior of empty previous-passport `Дата выдачи`.

Observed UI result: UI shows date requiredness/format behavior only. The field is required, focus displays `__.__.____`, and validation trigger can show `Введена неверная дата`. No behavior was observed that can be tied specifically to empty BSR 114.

Evidence: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/evidence/screenshots/tc-passprev-021-date-empty-after-ctrl-enter.png`

Blocked reason: source row has BSR 114 code but no normative text; UI does not reveal a separate BSR-114-specific rule.
