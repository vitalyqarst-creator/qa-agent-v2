# TC-PARTNERS-STRUCTURE-005

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3-struktura-i-dubli-partnerov.md`
- Source file SHA256: `DEE5A75FD188F593D691A54B9D950C5627F9B2124FD6D0DBC2DFCD70236073F1`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `confirmed`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requisites are displayed as second level inside partner card.

## Data Used

Actual stand partners/requisites; old РОМАШКА/PART-* fixtures were not the actual records used for all checks.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/partner-card-requisites-baseline.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.
