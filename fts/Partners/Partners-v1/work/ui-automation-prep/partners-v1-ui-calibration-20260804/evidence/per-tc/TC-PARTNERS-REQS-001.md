# TC-PARTNERS-REQS-001

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.1-rekvizity-vnutri-partnera.md`
- Source file SHA256: `352C559EA300C75314EF08721FB821618D6F1BB4C30EC548E7AF73B79260D47D`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `confirmed`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Opening partner showed requisites for that partner.

## Data Used

Actual stand data: АО "СОГАЗ" requisites ID 5/6/7; old REQ-* fixture not present as visible fixture.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/partner-card-requisites-baseline.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-STRUCTURE-004-partner-card-requisites.png](../screenshots/TC-PARTNERS-STRUCTURE-004-partner-card-requisites.png)
