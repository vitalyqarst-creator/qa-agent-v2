# Automation-ready draft: PostFinal-v2-rc5 UI-calibrated scopes

## Scope

- Package: `fts/AutoFin/PostFinal-v2-rc5`
- Created from baseline files in `test-cases/` without overwriting them.
- Evidence sources:
  - `work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-validation-report.md`
  - `work/ui-automation-prep/postfinal-v2-rc5-ui-calibration/ui-evidence-index.md`
  - `work/ui-automation-prep/passcur-dadata-fms-772-053/ui-validation-report.md`
  - `work/ui-automation-prep/passcur-dadata-fms-772-053/ui-evidence-index.md`

## Files

| File | Status |
| --- | --- |
| `automation-ready/4-3-contact-persons.md` | Draft automation-ready with one expected-fail product defect: `TC-CP-B78F72E22B`. |
| `automation-ready/4-3-current-passport-data.md` | Draft automation-ready; DaData/FMS `TC-PASSCUR-003/005/018` confirmed with fixture `FX-DADATA-FMS-POS-001`. |
| `automation-ready/11-4.3-application-documents-and-recognition.md` | Draft automation-ready; manual/mobile-only cases explicitly excluded, `TC-DOC-036` updated to blob-tab viewer behavior. |

## Excluded / not run in automation-ready

| TC-ID | Status | Reason |
| --- | --- | --- |
| `TC-DOC-019` | `excluded-manual-only` | Drag-and-drop upload was not reliably reproduced in available browser automation path. |
| `TC-DOC-020` | `excluded-manual-mobile-only` | QR/mobile upload requires external phone/QR flow. |
| `TC-DOC-025` | `excluded-manual-only` | Drag-and-drop upload was not reliably reproduced in available browser automation path. |
| `TC-DOC-026` | `excluded-manual-mobile-only` | QR/mobile upload requires external phone/QR flow. |
| `TC-DOC-031` | `excluded-manual-only` | Drag-and-drop upload was not reliably reproduced in available browser automation path. |
| `TC-DOC-040` | `blocked-observability` | `?????????? ? ????????` did not open reproducible QR dialog in checked session. |
| `TC-CP-B78F72E22B` | `expected-fail-product-defect` | Product decision: FT requires additional text field for `????`; current UI evidence shows it is missing. |

## DaData/FMS automation contract

Use fixture `FX-DADATA-FMS-POS-001`:

- Query / code: `772-053`.
- Dropdown item: `??? ?????? ?. ?????? 772-053`.
- Resulting field value: `??? ?????? ?. ??????`.
- Required trigger: fill `??? ?????????????`, then click/focus `??? ?????`; do not assert auto-fill after input/blur/Enter.
- Snapshot SHA-256: `5575e4fbb9e28df33d8826a00580594eccde839bb6d625bfa84a6bf53d2bf90e`.

## Notes

- Runtime API calls to DaData are not part of automation TC execution.
- Baseline `test-cases/*.md` remains the FT-first baseline; this folder is a UI-calibrated automation draft.
- Exact screenshots are linked from the evidence indexes above.
