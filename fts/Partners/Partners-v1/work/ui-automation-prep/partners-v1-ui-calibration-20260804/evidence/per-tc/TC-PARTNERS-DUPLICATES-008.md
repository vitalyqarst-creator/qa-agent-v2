# TC-PARTNERS-DUPLICATES-008

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3-struktura-i-dubli-partnerov.md`
- Source file SHA256: `DEE5A75FD188F593D691A54B9D950C5627F9B2124FD6D0DBC2DFCD70236073F1`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `blocked-observability`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Navigation from duplicate hint could not be executed because duplicate hint was not observed.

## Data Used

Old TC data uses ООО "РОМАШКА" / PART-* fixtures; not all were actually present as stable stand records.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/9-3-struktura-i-dubli-partnerov-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-CARD-001-add-partner-fields.png](../screenshots/TC-PARTNERS-CARD-001-add-partner-fields.png)
- [TC-PARTNERS-CARD-008-inn-dadata-options.png](../screenshots/TC-PARTNERS-CARD-008-inn-dadata-options.png)
