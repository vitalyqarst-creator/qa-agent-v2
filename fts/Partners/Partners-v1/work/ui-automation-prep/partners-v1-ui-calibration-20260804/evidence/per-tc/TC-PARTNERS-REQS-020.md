# TC-PARTNERS-REQS-020

- Source test-case file: `fts/AutoFin/Partners1/Новая папка/9.3.1-rekvizity-vnutri-partnera.md`
- Source file SHA256: `352C559EA300C75314EF08721FB821618D6F1BB4C30EC548E7AF73B79260D47D`
- Git HEAD during evidence packaging: `dfc3f4f5f954b293de87a2d58b6c3200402554b3`
- Result: `blocked-observability`
- Note: test-cases were from the older version, before the latest test-data corrections. Baseline test-cases were not edited.

## Actual UI Behavior

Admin return-from-archive action for a requisite was not executable: no visible Вернуть из архива/unarchive action was observed for requisite rows in the checked UI state.

## Data Used

Actual stand requisites under АО "СОГАЗ"; old REQ-* hidden requisite fixture was not available as a visible mutable object.

## Evidence / Confirmation

fts/AutoFin/Partners1/work/ui-automation-prep/9-3-1-9-3-2-requisites-and-partner-card-pms-ui-pass/ui-validation-report.md

## Reproducibility Notes

Do not add a confirmation-dialog step. The blocker here is that the requisite-level unarchive control was not visible/observable in the checked UI state.
