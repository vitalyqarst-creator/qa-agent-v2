# Common Application Fields Automation-Ready Setup Plan - 2026-06-17

## Context

| field | value |
| --- | --- |
| FT package | `fts/ft-2-OF_17` |
| Scope | `common-application-fields` |
| Baseline status | `signed-off` |
| Baseline TC | `fts/ft-2-OF_17/test-cases/section-34-common-application-fields.md` |
| Local setup artifact | `fts/ft-2-OF_17/work/ui-automation-prep/common-application-fields/setup-readiness.md` |

## Decision

Do not start UI automation prep yet. The baseline is signed off, but the UI run is not reproducible until environment access and fixtures are explicit.

## Required Setup Before UI Run

| item | required detail |
| --- | --- |
| UI entrypoint | Stable test environment URL. |
| Credentials | User allowed to open and view the Universal Application card. |
| Navigation | Exact path to create/open the card and reach common fields. |
| Primary-save state | Exact action or prepared record that puts the card into "after primary save" state. |
| Fixture data | Concrete records for `FIX-CAF-001`..`FIX-CAF-004`. |
| Cleanup | Rule for creating a fresh card per run or resetting prepared records. |

## Fixture Summary

| fixture_id | purpose | unresolved part |
| --- | --- | --- |
| `FIX-CAF-001` | Current session user for `Ответственный менеджер`. | Need actual user/account and displayed naming format. |
| `FIX-CAF-002` | Primary-saved card with client/product/amount values. | Need UI path or prepared record; exact status text remains intentionally unspecified. |
| `FIX-CAF-003` | CDI DBO/DKBO prefill values. | Need fixture injection/prepared record; no API payload assertions. |
| `FIX-CAF-004` | Gosuslugi `Статус ЦП` prefill value. | Need fixture injection/prepared record; no API payload assertions. |

## Expected Automation-Ready Output

When `ft-ui-automation-prep` starts:

- create `fts/ft-2-OF_17/test-cases/automation-ready/section-34-common-application-fields.md` from baseline if absent;
- preserve baseline traceability and expected-result intent;
- add concrete setup/navigation/fixture details;
- mark cases blocked where fixtures are unavailable;
- collect `ui-validation-report.md` and `ui-evidence-index.md` under `work/ui-automation-prep/common-application-fields/`.

## Non-Goals

- Do not rewrite the signed-off FT-first baseline.
- Do not infer exact generated application number, exact application status, CDI value sets, Gosuslugi value sets, API payloads, retries, or errors without source/UI evidence.
- Do not treat this plan as UI evidence.
