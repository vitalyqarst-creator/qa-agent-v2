# TC-PARTNERS-SCREEN-013

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.1-ekran-partnery.md`
- Source file SHA256: `432D6B36559EA2A62FC8071A61560A8AC5F6D45F53AD5AF1B73BBAA5A7356D95`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `blocked-observability`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Requires exact credit-conveyor selection place/oracle for hidden partner availability; not observable from PMS list only.

## Data Used

Hidden partner existed in PMS list for admin; credit-conveyor place was not checked.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-SCREEN-001-partners-list-visible.png](../screenshots/TC-PARTNERS-SCREEN-001-partners-list-visible.png)
