# Risk / Priority Map

## Risk / Priority Map

| risk_id | package_id | linked_atom_id | risk_statement | impact | likelihood | risk_score | risk_level | required_priority | residual_risk_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RISK-BSR32-001 | WP-BSR32 | ATOM-001 | Filters remain applied after `Очистить`, causing a user to see a narrowed result context while expecting a cleared context. | high | medium | 6 | high | High | Covered by TC-BSR32-001. |
| RISK-BSR32-002 | WP-BSR32 | ATOM-002 | Sorting remains applied after `Очистить`, causing result ordering context to remain stale. | medium | medium | 4 | medium | High | Covered by TC-BSR32-002. |
| RISK-BSR32-003 | WP-BSR32 | ATOM-003 | Pagination remains away from initial/default page after `Очистить`, hiding first-page/default results from the user. | medium | medium | 4 | medium | High | Covered by TC-BSR32-003; fixture must expose pagination. |
| RISK-BSR32-004 | WP-BSR32 | ATOM-004 | Row selection remains after `Очистить`, allowing stale row context to remain visible. | medium | medium | 4 | medium | High | Covered by TC-BSR32-004. |

## Scoring

- `risk_score = impact x likelihood`, using low=1, medium=2, high=3.

## Rules

- High-priority tests are assigned because `BSR 32` clears visible search context used before further user actions.
