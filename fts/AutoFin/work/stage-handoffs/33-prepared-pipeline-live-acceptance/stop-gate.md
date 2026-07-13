# V4 live acceptance stop-gate

## Pre-launch

- Package loader/digest: `pass`.
- Package version/profile: `5 / standard-required`.
- Context profile: `character-restriction-calibration`.
- Validate-only: `pass`; writer context 44338 bytes, one instruction artifact.
- Writer sandbox/budget: `read_only / 0`.
- Cycle directory contains only `prepared-input/`.
- SDK fallback: forbidden.
- Promotion: disabled.
- Production target exists: `no`.

## Required terminal quality

- reviewer decision `accepted`;
- obligation gate 12/12;
- exactly 12 unique test cases and titles;
- semantic overlap `clean`;
- quality gate `pass`;
- six lifecycle entries `awaiting-ui-calibration`;
- `GAP-001` retained in each constrained TC;
- production target remains absent.

## Performance thresholds

| metric | threshold |
| --- | ---: |
| duration writer + reviewer | `< 180000 ms` |
| uncached input tokens | `< 100000` |
| command executions | `<= 2` |
| writer command executions | `0` |
| primary context bytes total | `< 150000` |

Any failed quality requirement stops later live scopes. A performance miss with correct quality is recorded as `quality-pass-performance-fail` and also stops later live scopes pending analysis.

## Result

| gate | result | evidence |
| --- | --- | --- |
| reviewer | `pass` | `accepted`, 12 obligation reviews |
| obligation coverage | `pass` | 12/12 |
| unique TC/title | `pass` | quality bundle, 12 cases, 0 findings |
| semantic overlap | `pass` | `clean` |
| GAP/calibration | `pass` | six `awaiting-ui-calibration`, `GAP-001` |
| writer/reviewer commands | `pass` | 0 / 0 |
| duration | `pass` | 84469 ms |
| uncached input | `pass` | 52374 tokens |
| primary context | `pass` | 95302 bytes |
| production isolation | `pass` | target absent, promotion disabled |

Terminal classification: `quality-pass-performance-pass`.
