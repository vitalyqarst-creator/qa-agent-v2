# Prepared-standard calculator-summary runtime report

## Решение

`prepared-standard` доказал, что compact prepared transport совместим с полными standard writer/reviewer instruction scenarios и semantic gates. Fast eligibility не расширялась: calculator-summary остаётся `standard-required` из-за `state-transition-or-navigation`.

Quality acceptance получен в v7 после исправления source traceability и test-design obligations. Production baseline не изменялся и promotion не выполнялся.

## Целевые semantic cycles

| run | writer | reviewer | total | result | quality |
| --- | ---: | ---: | ---: | --- | --- |
| v5 | 312.719 s | 210.422 s | 523.141 s | `changes-required` | 2 source-backed findings |
| v7 | 282.797 s | 221.359 s | 504.156 s | `accepted-not-promoted` | 5/5 testable obligations covered; OBL-006 gap preserved |

- Median total: `513.648 s` / `8.561 min`.
- Raw standard v4: `1215.031 s`; median speedup: `2.37x`.
- Required target `<= 8 min` was missed by `33.648 s` at the median.
- Desired target `<= 5 min` was not reached.
- v7 reviewer time `221.359 s` also exceeded the desired `<= 3 min` reviewer target.

## Primary context

| run | writer primary context | reviewer primary context | raw standard v4 writer/reviewer reduction |
| --- | ---: | ---: | --- |
| v5 | 187,820 bytes | 306,601 bytes | 99.517% / 99.215% |
| v7 | 192,696 bytes | 313,358 bytes | 99.505% / 99.198% |

Raw standard v4 supplied 38,923,210 writer bytes and 39,071,903 reviewer bytes. Registered DOCX/XHTML/PDF remained hashed fallback evidence and were excluded from the primary context.

## Commands and reported token usage

| run | writer/reviewer commands | writer input/cached/output tokens | reviewer input/cached/output tokens |
| --- | --- | --- | --- |
| v5 | 15 / 31 | 1,085,948 / 1,002,496 / 11,810 | 743,943 / 653,824 / 6,242 |
| v7 | 19 / 17 | 1,059,579 / 973,568 / 9,772 | 1,022,325 / 920,320 / 6,391 |

Context bytes decreased by more than 99%, but standard sessions still reread 17 writer and 19 reviewer instruction files. Most reported input tokens were cached; instruction loading remains the main runtime optimization target.

## Session separation

| run | writer backend session | reviewer backend session |
| --- | --- | --- |
| v5 | `019f5169-9866-73a0-bcc3-a86dfc213264` | `019f516e-6047-75a3-9446-766a5dd4e6d6` |
| v7 | `019f5184-f524-7070-9e30-5ab6ad69ad1b` | `019f5189-4761-7783-84da-f5c32c1dcfac` |

All four IDs are distinct.

## Quality progression

### v5

- `OBL-001`: visibility fixture incorrectly depended on calculator data.
- `OBL-002`: names were checked, but recorded values were not compared.
- `OBL-003` and `OBL-004`: covered.
- The then-current prefill mapping gap was preserved.

### v7

- Active requirement IDs corrected from stale `BSR 35-38` to registered-source `BSR 43-46`.
- Five testable obligations are covered by five atomic TCs.
- `OBL-006 / ATOM-006` preserves only exhaustive prefill field set and exact mapping as `GAP-001`.
- No blocking findings.
- No registered full-source access was needed in the accepted reviewer turn.

## Diagnostic cycles retained

| run | stopped at | defect exposed |
| --- | --- | --- |
| v1 | reviewer evidence/idle gate | fast-only instruction roots and idle policy leaked into prepared-standard |
| v2 | writer evidence gate | read-only production status check misclassified as content access |
| v3 | reviewer contract | composite prefill obligation and unresolved `<ID заявки>` fixture |
| v4 | writer evidence gate | exact `rg --files scripts` inventory misclassified as FT evidence scan |
| v6 | reviewer contract | stale BSR mapping and source-backed prefill-presence obligation; schema allowed incompatible verdict |

Each recovery used a new cycle and newly compiled attempt-bound package. No terminal/blocked cycle was replayed.

## Guards

- V7 terminal replay was rejected before LLM launch; `cycle-state.yaml` SHA-256 remained unchanged.
- V5 and v7 writer/reviewer evidence-access reports passed.
- Production `test-cases/**` diff remained empty.
- Promotion remained disabled. A dry-run was not represented as passed because the canonical destination already exists and overwrite is forbidden.

## Remaining boundary

The active prepared package is corrected against `FT4AutoFinFinal`, but handoff 05 still names `AutoFinPreFinal` and its parity inventory predates the discovered `BSR 43-46` mapping. Broader reuse must first rebase that canonical scope handoff and audit the generated AutoFin BSR source inventory; historical snapshots must remain immutable.
