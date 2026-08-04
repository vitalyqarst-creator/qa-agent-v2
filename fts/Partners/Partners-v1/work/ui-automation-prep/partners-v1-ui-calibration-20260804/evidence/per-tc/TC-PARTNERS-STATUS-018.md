# TC-PARTNERS-STATUS-018

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.2-statusnaya-model-partnerov.md`
- Source file SHA256: `C6E21AA5163E42FD7BFAD9DE6D6AED8C278DA154318E1A22CB0C26510030A1E2`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `confirmed`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Hidden partner is visible for the current admin-like user in PMS list.

## Data Used

Actual stand data: АО "СОГАЗ", ООО "ЛЕНТА", ООО "РЕНЕСАНС", ООО "СБЕРОБРАЗОВАНИЕ"; fixture names like PART-* were not actually used as seeded IDs.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/partner-archive-unarchive-transition.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-SCREEN-001-partners-list-visible.png](../screenshots/TC-PARTNERS-SCREEN-001-partners-list-visible.png)
