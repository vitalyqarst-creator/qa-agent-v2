# TC-PARTNERS-STRUCTURE-002

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3-struktura-i-dubli-partnerov.md`
- Source file SHA256: `DEE5A75FD188F593D691A54B9D950C5627F9B2124FD6D0DBC2DFCD70236073F1`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `mismatch-ft-ui`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Insurance company type is displayed as СК, not full text Страховые компании.

## Data Used

Actual partner list data, e.g. АО "СОГАЗ" and СПАО "ИНГОССТРАХ". 

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/partners-list-baseline.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-SCREEN-001-partners-list-visible.png](../screenshots/TC-PARTNERS-SCREEN-001-partners-list-visible.png)
