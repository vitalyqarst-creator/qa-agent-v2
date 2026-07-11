# Prepared fast path vs standard control: widget selection

## Решение

Prepared fast path подтверждён для `simple-field-property` scope и не должен расширяться на stateful/action-flow задачи. Для выбранного widget-selection scope fast path одновременно быстрее и качественнее matched standard control: он сохраняет неподтверждённые утверждения как gaps вместо формального покрытия через незаполненные fixtures.

## Матрица запусков

| run | route | writer | reviewer | terminal result | production write |
| --- | --- | ---: | ---: | --- | --- |
| prepared v13 | fast | 72.813 s | 20.797 s | `accepted-not-promoted` | no |
| prepared v14 | fast + package notes | 74.375 s | 23.422 s | `accepted-not-promoted` | no |
| prepared v15 | fast + promotion dry-run | 88.500 s | 19.500 s | `accepted-promotion-dry-run` | no |
| standard v1 | standard control | 97.329 s | not started | writer command budget, no draft | no |
| standard v2 | standard control | 284.422 s | not started | non-canonical `### TC-*`, validator block | no |
| standard v3 | standard + resolved instructions | 900.094 s | 115.500 s | reviewer command budget before verdict | no |
| standard v4 | standard + production defaults | 816.719 s | 398.312 s | `changes-required`, 6 errors | no |

Fast cycle median for v13-v15 is `97.797 s`. Standard v4 required `1215.031 s` and did not reach acceptance. The observed end-to-end speed ratio is about `12.4x` in favor of fast path, without treating a failed standard result as quality-equivalent.

## Quality comparison

| quality signal | prepared v13-v15 | standard v4 |
| --- | --- | --- |
| reviewer outcome | 3/3 accepted | changes required |
| testable obligations | `OBL-002`, `OBL-004`, `OBL-005` covered | draft claimed 5/6 atoms covered |
| non-testable obligations | dictionary provenance/composition and internal `NULL` semantics preserved as gaps | source-less dictionary snapshots and unbound fixtures used as coverage |
| executable coverage | 3 atomic TC | reviewer assessed 0/6 execution-ready |
| invented UI behavior | none accepted | `last-selected-wins` required without source evidence |
| package context | `AGENT-NOTES.md` embedded in v14/v15 | omitted in v4; runner contract subsequently fixed |

The standard structural validator passed v4, but the semantic reviewer found six blocking errors. Structural Markdown validity is therefore necessary but not a proxy for execution-ready coverage.

## Context and token cost

| metric | prepared v14 | prepared v15 | standard v4 |
| --- | ---: | ---: | ---: |
| writer input artifact bytes | 68,062 | 68,062 | 38,923,210 |
| reviewer input artifact bytes | 81,597 | 79,235 | 39,071,903 |
| total reported tokens | 117,054 | 142,203 | at least 2,907,926 reviewer tokens; writer count unavailable after interruption |
| writer commands | 2 | 6 | 65 |
| reviewer commands | 0 | 0 | 41 |

Standard input bytes are dominated by full binary sources. Prepared context stays scoped and source-backed; full sources remain only in the verified targeted fallback registry.

## Routing proof

- Widget selection compiles as `simple-field-property`, package v5, with no unsupported dimensions.
- Universal application common actions compiles as `standard-required` with `state-transition-or-navigation`.
- The prepared runner rejects the common-actions package during configuration, before `cycle-state.yaml`, attempt folders or an LLM session are created.
- A terminal v14 cycle cannot be replayed: the repeated command is rejected and the state hash remains unchanged.

### Cross-scope compiler matrix

| scope | compiler result | route / blocker |
| --- | --- | --- |
| widget selection | built | `simple-field-property` |
| calculator summary | built | `standard-required`: state transition/navigation |
| common actions | built | `standard-required`: state transition/navigation |
| search clear | built | `standard-required`: limited default oracle + navigation |
| visual assessment | built | `standard-required`: dependency state |
| print form | built after routing-budget fix | `standard-required`: dependency, generated document, repeatable lifecycle |
| client addresses | blocked | 27 ledger atoms have no coverage obligation |
| document files | blocked | 47 ledger atoms have no coverage obligation |
| document recognition | blocked | invalid obligation id `OBL-N/A-001` |

The three blocked scopes expose upstream design-artifact defects and must not be forced into either route. The print-form failure was a technical regression caused by mandatory package notes crossing the fast-only 32 KiB evidence cap; standard-required diagnostic packages now allow 48 KiB while fast eligibility remains capped at 32 KiB.

## Failure taxonomy

| failure class | observed signal | guard/result |
| --- | --- | --- |
| `prepared-runtime-contract-drift` | stale package/profile/attempt binding | exact package v5 + attempt/output preflight |
| `obligation-atom-mapping-loss` | OBL ids compared with ATOM traceability | explicit `obligation_id` and `atom_id` in package/gates/reviewer |
| `standard-instruction-context-omission` | v2 writer skipped canonical runtime format | scenario resolver and budget pass required before LLM |
| `standard-runtime-budget-underfit` | v3 reviewer exhausted budget while loading 33 inputs | role-specific standard defaults and preflight input floor |
| `semantic-false-coverage` | v4 used unbound fixtures as covered TC | structured prepared obligations keep unsupported claims as gaps |
| `route-misclassification` | stateful common-actions candidate | compiler emits `standard-required`; runner rejects fast path |
| `package-context-omission` | v4 omitted mandatory package notes | standard auto-routes notes; prepared compiler embeds them |
| `stale-cycle-replay` | repeated v14 command | rejected before LLM; state and production unchanged |
| `upstream-obligation-closure` | ledger atoms without OBL rows or invalid OBL ids | compiler blocks before package/LLM; remediation stays upstream |
| `routing-package-budget` | standard-required evidence plus mandatory notes exceeded fast cap | 32 KiB fast cap retained; standard routing package cap 48 KiB |

## Promotion and recovery guards

- v15 promotion dry-run recorded the exact draft hash and absent destination.
- `write_performed: false`; no production or temporary promotion file exists.
- Writer interruption is accepted only as `completed-with-progress` when a draft exists and deterministic gates pass.
- Partial reviewer output is never terminal evidence.
- Recovery uses a new immutable cycle; prepared recovery recompiles a package bound to the new attempt.

## Fast-path boundary

Keep fast eligibility limited to compact, independently observable field-property obligations with explicit gaps. Route numeric/boundary, dependency/state, integration/persistence, file/upload, generated-document, repeatable lifecycle, table-parity and navigation/action transitions to the standard workflow.

The evidence does not justify replacing the standard workflow. It justifies avoiding it when an upstream canonical design package already contains all machine-checkable obligations for a simple scope.
