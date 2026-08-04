# TC-PARTNERS-REQUISITE-CARD-019

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.3-kartochka-rekvizitov.md`
- Source file SHA256: `6BBF8416D7C403630E471CCA1411BBF12BEE833A8EFEC766B31EFDC52E0249A6`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `needs-test-data`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requires prepared mutable requisite/save/edit/duplicate/date fixture and cleanup policy; not executed in this evidence-only pass.

## Data Used

Old TC uses REQ-* fixtures; actual stand data was not safely mutated for this TC.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.
