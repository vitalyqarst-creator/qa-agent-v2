# UI evidence index: 13-4.3-employment-info

## Artifacts

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/ui-validation-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/employment-second-pass-observations.md`

## Second-pass Evidence Files

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-employment-status-work-for-hire.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-011-org-dadata-attempts.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-011-clean-dadata-address-blur.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-011-clean-dadata-address-blur-type.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-011-clean-dadata-address-blur-cua-click.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-027-date-valid-manual.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-027-date-invalid-paste.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-date-invalid-manual-gap.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-033-036-period-valid-manual.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-period-invalid-paste.png`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/evidence/tc-emp-period-invalid-manual-gap.png`

## Evidence Notes

- Browser screenshots were captured during the pass in the Codex session output for key states:
  - employment block default paper mode;
  - DaData organization dropdown and selected Sberbank organization;
  - OPF dropdown;
  - social status visibility matrix;
  - additional income add/duplicate/delete;
  - valid PDF upload with eye/trash/download icons;
  - unsupported file and over-40MB upload errors;
  - Gosuslugi explanatory text.
- Large and small upload fixtures were generated only as transient local test data and are not retained as evidence files in this repo.
- Manual user recheck was incorporated for `TC-EMP-066`, `TC-EMP-067`, `TC-EMP-075`, and for current not-implemented status of `TC-EMP-002`, `TC-EMP-004`, `TC-EMP-028`.
- Second pass observations were incorporated for DaData organization, date mask, period mask, and work phone mask. Some phone second-pass evidence is recorded as structured DOM observations in `employment-second-pass-observations.md`; screenshot capture for later phone-only clean tabs timed out in the browser control surface.
- No source DOCX/XHTML/PDF/support/mockups were changed.
- No baseline `fts/AutoFin/PostFinal-v2-rc5/test-cases/*.md` files were edited.

## Key Repo-relative Result

Use the report as the canonical UI pass output:

`fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-employment-info-ui-pass/ui-validation-report.md`
