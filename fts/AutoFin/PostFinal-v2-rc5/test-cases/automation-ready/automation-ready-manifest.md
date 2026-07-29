# Automation-ready handoff: PostFinal-v2-rc5 UI-calibrated scopes

## Scope

- Package: `fts/AutoFin/PostFinal-v2-rc5`.
- Baseline files in `test-cases/*.md` are not overwritten.
- This folder contains all TC-ID from the three UI-calibrated scopes; no TC is removed.
- UI status vocabulary is intentionally limited to `confirmed` and `blocked-observability`.

## Files

| File | TC count | Notes |
| --- | ---: | --- |
| `automation-ready/4-3-contact-persons.md` | 38 | Includes product-defect note for `TC-CP-B78F72E22B`; TC remains confirmed because the UI path was observed. |
| `automation-ready/4-3-current-passport-data.md` | 44 | Includes DaData/FMS fixture `FX-DADATA-FMS-POS-001` and dynamic date-boundary cases. |
| `automation-ready/11-4.3-application-documents-and-recognition.md` | 42 | Includes all document TC; unavailable drag-and-drop/QR/mobile paths are marked `blocked-observability`. |

## Status semantics

| UI status | Meaning for automation |
| --- | --- |
| `confirmed` | UI path and observed behavior are sufficiently confirmed for automation. If the product currently differs from FT, the TC note says so; the TC remains in scope. |
| `blocked-observability` | TC remains in the suite, but current evidence lacks a reproducible UI path/oracle or requires unavailable external/manual/mobile behavior. Automator should create skip/stub/mock or request a prepared environment. |

## DaData/FMS automation contract

Use fixture `FX-DADATA-FMS-POS-001`:

- Query / code: `772-053`.
- Dropdown item: `ОВД ЗЮЗИНО Г. МОСКВЫ 772-053`.
- Resulting field value: `ОВД ЗЮЗИНО Г. МОСКВЫ`.
- Required trigger: fill `Код подразделения`, then click/focus `Кем выдан`; do not assert auto-fill immediately after input, blur, or Enter.
- Snapshot SHA-256: `5575e4fbb9e28df33d8826a00580594eccde839bb6d625bfa84a6bf53d2bf90e`.

## Evidence sources

- `work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md`
- `work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-evidence-index.md`
- `work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/post-ui-product-decisions.md`
- `work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md`
- `work/ui-automation-prep/passcur-dadata-fms-772-053/ui-evidence-index.md`
