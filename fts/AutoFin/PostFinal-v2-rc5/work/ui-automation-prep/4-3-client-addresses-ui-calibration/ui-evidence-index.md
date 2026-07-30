# UI Evidence Index: 4.3 Client Addresses

All paths are repo-relative.

| TC-ID | Status | What was checked | Trigger | Primary evidence |
|---|---|---|---|---|
| `TC-ADDR-005` | confirmed | Registration `Регион` and `Дом` required in manual mode | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-005.md` |
| `TC-ADDR-013` | confirmed | Registration `Почтовый индекс` mask: 6 numeric chars | input, blur, `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-013.md` |
| `TC-ADDR-021` | mismatch-ft-ui | Registration `Корпус` format | input, blur, `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-021.md` |
| `TC-ADDR-023` | mismatch-ft-ui | Registration `Квартира` format | input, blur, `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-023.md` |
| `TC-ADDR-031` | confirmed | Actual `Регион` and `Дом` required in manual mode | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-031.md` |
| `TC-ADDR-047` | confirmed | Actual `Квартира` required when private-house checkbox is unchecked | checkbox, `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-047.md` |
| `TC-ADDR-049` | mismatch-ft-ui | Actual `Квартира` format | input, blur, `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-049.md` |
| `TC-ADDR-051` | confirmed | Actual postal index rejects nonnumeric input by mask/clear | input, blur | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-051.md` |
| `TC-ADDR-052` | confirmed | Actual postal index shorter than 6 digits clears on blur | input, blur | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-052.md` |
| `TC-ADDR-053` | mismatch-ft-ui | Actual postal index longer than 6 digits | input, blur | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-053.md` |
| `TC-ADDR-056` | confirmed | Registration `Населенный пункт` conditional requiredness | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-056.md` |
| `TC-ADDR-057` | confirmed | Registration `Город` conditional requiredness | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-057.md` |
| `TC-ADDR-058` | confirmed | Registration `Дом` required | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-058.md` |
| `TC-ADDR-059` | confirmed | Registration `Квартира` required when private-house checkbox is unchecked | checkbox, `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-059.md` |
| `TC-ADDR-060` | confirmed | Actual `Город` required | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-060.md` |
| `TC-ADDR-061` | mismatch-ft-ui | Actual `Улица` requiredness | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-061.md` |
| `TC-ADDR-062` | confirmed | Actual `Дом` required | `ДАЛЕЕ` | `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/TC-ADDR-062.md` |

## Screenshot Inventory

Setup:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-clean-card-before-manual.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-manual-enabled.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-clean-card-before-toggles.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-address-manual-enabled.png`

Required:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-required-empty-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-required-empty-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-city-only-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-locality-only-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-private-house-no-flat-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-private-house-no-flat-after-next.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-private-house-yes-after-toggle.png`

Format probes:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-443017-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-44301-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-4430179-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-postal-44301A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-building-hyphen-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/registration-flat-hyphen-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-443017-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-44301-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-4430179-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-postal-44301A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-12A-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-space-after-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/actual-flat-hyphen-after-blur.png`
