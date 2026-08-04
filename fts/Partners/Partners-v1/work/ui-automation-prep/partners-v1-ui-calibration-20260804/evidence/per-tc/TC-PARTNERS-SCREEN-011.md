# TC-PARTNERS-SCREEN-011

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.1-ekran-partnery.md`
- Source file SHA256: `432D6B36559EA2A62FC8071A61560A8AC5F6D45F53AD5AF1B73BBAA5A7356D95`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `needs-test-data`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requires non-admin account to check hidden partner invisibility.

## Data Used

Old TC references non-admin user and hidden fixture; non-admin account was not available.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

No screenshot added: the result depends on prepared external stand fixtures/application oracles/safe mutable PART-* or REQ-* data. The current PMS screen would not visually prove that missing data condition.
