# TC-PARTNERS-REQS-009

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.1-rekvizity-vnutri-partnera.md`
- Source file SHA256: `352C559EA300C75314EF08721FB821618D6F1BB4C30EC548E7AF73B79260D47D`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `blocked-observability`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Edit requisite dialog could not be opened from widget; prefill not checked.

## Data Used

No stable visible requisite edit/status action.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/9-3-1-9-3-2-requisites-and-partner-card-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-STRUCTURE-004-partner-card-requisites.png](../screenshots/TC-PARTNERS-STRUCTURE-004-partner-card-requisites.png)
