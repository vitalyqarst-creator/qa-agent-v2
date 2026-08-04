# TC-PARTNERS-STATUS-004

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.2-statusnaya-model-partnerov.md`
- Source file SHA256: `C6E21AA5163E42FD7BFAD9DE6D6AED8C278DA154318E1A22CB0C26510030A1E2`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `needs-test-data`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requires non-final application with selected requisite and safe edit/restore oracle.

## Data Used

Old TC data references PART-* / REQ-* and non-admin user; those were not available as actual stand-prepared fixtures in this pass.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/9-2-statusnaya-model-partnerov-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

No screenshot added: the result depends on prepared external stand fixtures/application oracles/safe mutable PART-* or REQ-* data. The current PMS screen would not visually prove that missing data condition.
