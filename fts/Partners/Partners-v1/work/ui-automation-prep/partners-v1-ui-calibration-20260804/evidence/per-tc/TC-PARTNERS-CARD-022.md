# TC-PARTNERS-CARD-022

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.2-kartochka-partnera.md`
- Source file SHA256: `EEEF0B13E130E3B4759B18D3FAC8C3051D922BEEBA82498CD5FF3CFF3F41723F`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `needs-test-data`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requires safe mutable unique partner/save/edit/file fixture and cleanup policy; not executed in this evidence-only pass.

## Data Used

Old TC uses PART-* fixtures; actual stand data was not safely mutated for this TC.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/9-3-1-9-3-2-requisites-and-partner-card-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.
