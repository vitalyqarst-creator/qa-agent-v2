# TC-PARTNERS-REQS-026

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.1-rekvizity-vnutri-partnera.md`
- Source file SHA256: `352C559EA300C75314EF08721FB821618D6F1BB4C30EC548E7AF73B79260D47D`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `needs-test-data`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requires mutable prepared requisite and allowed archive/restore or save path; not executed against current stand data.

## Data Used

Old TC uses REQ-* fixture; actual hidden/mutable requisite fixture was not available.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/9-3-1-9-3-2-requisites-and-partner-card-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

No screenshot added: the result depends on prepared external stand fixtures/application oracles/safe mutable PART-* or REQ-* data. The current PMS screen would not visually prove that missing data condition.
