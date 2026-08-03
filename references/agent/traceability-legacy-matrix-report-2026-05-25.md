# Traceability Legacy Matrix Report — 2026-05-25

## Summary

Validator scan results:

- Traceability matrices checked: `23`
- Matrices with canonical `atom_id` column: `3`
- Legacy matrices without `atom_id`: `20`
- Matrices with canonical `ATOM-*` ids only: `2`
- Matrices with legacy `UNCLEAR-*` ids inside `atom_id`: `1`
- Completed workflow states missing canonical `final_*` aliases: `13`

This report is intentionally read-only. Do not mechanically add `ATOM-*` ids to historical matrices: that would create false traceability unless a reviewer re-validates the atomic decomposition.

## Legacy Matrices Without `atom_id`

| FT package | Scope | Round |
| --- | --- | --- |
| FT-5 | `formirovanie-kod-pechatnye-formy-i-tegi` | `round-1` |
| FT-5 | `pdd-detalizaciya-dohodov-obshchaya-logika` | `round-1` |
| FT-5 | `pdd-detalizaciya-dohodov-obshchaya-logika` | `round-2` |
| FT-5 | `pdd-dokumenty-klienta` | `round-1` |
| FT-5 | `pdd-dokumenty-klienta` | `round-2` |
| FT-5 | `pdd-ostalnye-tipy-dpd` | `round-1` |
| FT-5 | `pdd-ostalnye-tipy-dpd` | `round-2` |
| FT-5 | `podgotovka-k-sdelke` | `round-1` |
| FT-5 | `podgotovka-k-sdelke` | `round-2` |
| FT-5 | `podpisanie-kod` | `round-1` |
| FT-5 | `postobsluzhivanie-kredita` | `round-1` |
| FT-2 | `application-interruption-cancellation-expiry` | `round-1` |
| FT-2 | `application-interruption-deal-issue-exceptions` | `round-1` |
| FT-2 | `bp-checks-predecision-pdn` | `round-1` |
| FT-2 | `bp-collateral-deal-issue` | `round-1` |
| FT-2 | `bp-initiation-client-offers` | `round-1` |
| FT-2 | `bp-offer-selection-application-update` | `round-1` |
| FT-2 | `status-model-product-application` | `round-1` |
| FT-2 | `status-model-universal-application` | `round-1` |
| FT-2 | `ui-main-info` | `round-1` |

## Matrices With `atom_id`

| FT package | Scope | Round | Status |
| --- | --- | --- | --- |
| FT-5 | `pdd-detalizaciya-2-ndfl` | `round-1` | canonical `ATOM-*` ids |
| FT-5 | `pdd-detalizaciya-2-ndfl` | `round-2` | canonical `ATOM-*` ids |
| FT-2 | `ui-employment-core-fields` | `round-1` | mixed: canonical `ATOM-*` plus legacy `UNCLEAR-*` ids |

## Completed Workflow States Missing Final Aliases

These states are valid legacy states, but future completed reviewer-loop states should expose `final_findings`, `final_traceability_matrix`, `final_traceability_matrix_xlsx`, `final_writer_response` when applicable, and `loop_summary`.

| FT package | Handoff scope |
| --- | --- |
| FT-5 | `02-podpisanie-kod` |
| FT-5 | `03-postobsluzhivanie-kredita` |
| FT-5 | `04-pdd-dokumenty-klienta` |
| FT-5 | `05-pdd-detalizaciya-dohodov-obshchaya-logika` |
| FT-5 | `06-pdd-detalizaciya-2-ndfl` |
| FT-5 | `07-pdd-ostalnye-tipy-dpd` |
| FT-5 | `08-formirovanie-kod-pechatnye-formy-i-tegi` |
| FT-2 | `01-status-model-universal-application` |
| FT-2 | `02-status-model-product-application` |
| FT-2 | `03-bp-offer-selection-application-update` |
| FT-2 | `05-application-interruption-cancellation-expiry` |
| FT-2 | `07-application-interruption-deal-issue-exceptions` |
| FT-2 | `bp-checks-predecision-pdn` |

## Recommended Migration Policy

1. Do not rewrite legacy matrices in bulk.
2. When a scope enters a new reviewer round, create the new matrix with `atom_id`.
3. If a legacy matrix is used as baseline, record `legacy traceability baseline` in human summary.
4. For signed-off or round-cap states created from now on, write canonical `final_*` aliases to `workflow-state.yaml`.
5. Prioritize re-review for scopes that are both signed-off and legacy-only, because their downstream UI automation has the weakest machine-checkable traceability.

