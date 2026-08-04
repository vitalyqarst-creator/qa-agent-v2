# TC-PARTNERS-MENU-003

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.1-menu-partnerov.md`
- Source file SHA256: `2C671436388F6FBEBA6996C823B71190AFCAFF42CF2A1629DFD02B9E0F39640F`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `mismatch-ft-ui`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Clicking Группы компаний opened group list; exact label Группы компаний (ГК) was not displayed.

## Data Used

No special data.

## Evidence / Confirmation

fts/Partners/Partners-v1/work/ui-automation-prep/partners-v1-ui-calibration-20260804/evidence/per-tc/TC-PARTNERS-MENU-003.md; fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/9-1-menu-navigation.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.

## Screenshots

- [TC-PARTNERS-MENU-003-groups-companies-label.png](../screenshots/TC-PARTNERS-MENU-003-groups-companies-label.png)
