# TC-PARTNERS-REQUISITE-CARD-008

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.3-kartochka-rekvizitov.md`
- Source file SHA256: `6BBF8416D7C403630E471CCA1411BBF12BEE833A8EFEC766B31EFDC52E0249A6`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `confirmed`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Empty Расчетный счет remained required and blocked completion.

## Data Used

Actual stand data: АО "СОГАЗ" add requisite dialog.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/requisite-add-dialog-baseline.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-REQUISITE-CARD-007-required-validation.png](../screenshots/TC-PARTNERS-REQUISITE-CARD-007-required-validation.png)
