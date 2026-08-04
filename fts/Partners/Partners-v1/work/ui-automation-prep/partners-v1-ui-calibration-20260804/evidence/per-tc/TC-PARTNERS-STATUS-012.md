# TC-PARTNERS-STATUS-012

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.2-statusnaya-model-partnerov.md`
- Source file SHA256: `C6E21AA5163E42FD7BFAD9DE6D6AED8C278DA154318E1A22CB0C26510030A1E2`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `blocked-observability`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

No visible archive action for requisite rows was observed in the checked UI state.

## Data Used

Actual stand requisites under АО "СОГАЗ"; old REQ-* fixture IDs were not present as visible IDs.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/novaya-papka-pms-ui-pass/evidence/partner-card-requisites-baseline.json

## Reproducibility Notes

No baseline rewrite was made. If old TC fixture names such as PART-* / REQ-* / Поставщик Скрытый 9.3.1 are present, this evidence records whether they matched actual stand data instead of correcting them.
