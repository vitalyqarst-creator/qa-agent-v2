# TC-PARTNERS-CARD-011

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.2-kartochka-partnera.md`
- Source file SHA256: `EEEF0B13E130E3B4759B18D3FAC8C3051D922BEEBA82498CD5FF3CFF3F41723F`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `confirmed`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Manual fields КПП/ОГРН were visible and fillable in dialog.

## Data Used

Actual stand add/edit partner dialog; Sberbank INN data used for DaData recheck where available.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/add-partner-dialog-baseline.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.
