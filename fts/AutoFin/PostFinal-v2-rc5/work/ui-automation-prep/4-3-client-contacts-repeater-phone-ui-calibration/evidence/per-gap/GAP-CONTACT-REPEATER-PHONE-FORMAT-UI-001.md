# GAP-CONTACT-REPEATER-PHONE-FORMAT-UI-001

## Scenario

Added phone row exists. `Тип телефона` is selected as `Мобильный`. `Номер телефона` is checked with multiple input values.

## Observed UI facts

| Exact input | Displayed value after blur | Field state | Message | Filtering / truncation |
| --- | --- | --- | --- | --- |
| `9999999999` | `+7 (999) 999–99–99` | `valid` | none | Accepted as masked phone. |
| `999123456` | empty | `invalid required empty` | `Обязательно к заполнению` | Short value clears/rejects on blur. |
| `99912345678` | `+7 (999) 123–45–67` | `valid` | none | Extra digit is ignored/truncated by mask. |
| `99912A4567` | empty | `invalid required empty` | `Обязательно к заполнению` | Letter-containing value clears/rejects on blur. |
| `99912 4567` | empty | `invalid required empty` | `Обязательно к заполнению` | Space-containing value clears/rejects on blur. |

## Status

`confirmed`

## Evidence

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-repeater-phone-format-9999999999.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-repeater-phone-format-999123456.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-repeater-phone-format-99912345678.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-repeater-phone-format-99912A4567.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-contacts-repeater-phone-ui-calibration/evidence/screenshots/gap-repeater-phone-format-99912-space-4567.png`
