# Prepared Fast Canary: Client Address Static Properties

## Решение

Второй независимый fast-path canary подтверждён на шести статических свойствах section 14. Оба immutable cycle приняты отдельными reviewer sessions. Canary является eval-only проекцией и не заменяет полный `application-card-client-addresses` scope, который остаётся `standard-required`.

## Live runs

| run | writer | reviewer | total | result | promotion |
| --- | ---: | ---: | ---: | --- | --- |
| `client-address-static v1` | 84.797 s | 35.203 s | 120.768 s | `accepted-not-promoted` | disabled |
| `client-address-static v2` | 88.719 s | 31.297 s | 120.741 s | `accepted-promotion-dry-run` | dry-run passed |

- Median total for two runs: `120.755 s`.
- Both runs stayed below the 3-minute target.
- Writer command count: `2` in each cycle.
- Reviewer command count: `0` in each cycle.

## Quality

| signal | v1 | v2 |
| --- | --- | --- |
| obligations | 6/6 covered | 6/6 covered |
| reviewer verdict | accepted | accepted |
| blocking findings | 0 | 0 |
| unsupported behavior | none accepted | none accepted |
| draft SHA-256 | `8c6737d39040ad7aaa425ae62963d423f094cc483939e41155ae7dcafecb321d` | `a6847f6d0bc2d6bf0f3f3591bc579df431961589959a03de55fac068a1a0a0ac` |

Draft hashes differ, but both reviewers mapped the same six exact `OBL -> ATOM -> TC` obligations and accepted the observable outcomes.

## Session separation

| run | writer backend session | reviewer backend session |
| --- | --- | --- |
| v1 | `019f5118-baef-7191-ac1e-e7bfcfaf9481` | `019f5119-fb75-75d0-a3ed-37fe7e07b8d9` |
| v2 | `019f511b-18a4-7fe0-ac41-65a52c0a70d0` | `019f511c-748b-7231-8efd-3d1feff4034f` |

All four backend session IDs are distinct.

## Context cost

| metric | v1 | v2 |
| --- | ---: | ---: |
| writer input artifact bytes | 65,239 | 65,239 |
| reviewer input artifact bytes | 78,855 | 76,826 |
| writer total tokens | 94,605 | 97,658 |
| reviewer total tokens | 22,046 | 22,424 |
| prepared `source-evidence.md` | 10,610 bytes | 10,610 bytes |

## Promotion and replay guards

- v2 dry-run recorded exact draft hash and destination.
- `destination_exists: false`.
- `production_changes: []`.
- `write_performed: false`.
- Replaying terminal v2 was rejected before a new LLM session.
- `cycle-state.yaml` hash remained unchanged after the replay attempt.
- Target `test-cases/14-prepared-canary-client-address-static-properties.md` remained absent.

## Evidence paths

- v1 state: `fts/AutoFin/work/review-cycles/codex-exec-prepared-client-address-static-live-v1-20260711/cycle-state.yaml`.
- v2 state: `fts/AutoFin/work/review-cycles/codex-exec-prepared-client-address-static-live-v2-20260711/cycle-state.yaml`.
- v2 promotion dry-run: `fts/AutoFin/work/review-cycles/codex-exec-prepared-client-address-static-live-v2-20260711/promotion-dry-run.json`.
- Compiler matrix: `evals/prepared-obligation-rollout/20260711/compiler-matrix.md`.

## Remaining boundary

This result does not justify routing the full client-addresses scope to fast execution. Conditional visibility, numeric/length checks, DaData, address composition and model persistence remain in the full standard package.
