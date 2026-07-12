# Production Readiness Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `production canonicalization and controlled promotion` |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| started_from | `work/stage-handoffs/27-calculator-summary-final-source-rebase/workflow-state.yaml` |
| status_after | `signed-off` |

## Inputs Read

- Handoff 27 Final-source scope and accepted v9 candidate.
- Production-before calculator-summary baseline.
- v10, v11 and v12 immutable cycle state, gates and reviewer results.
- Active calculator test-design artifacts linked by production Metadata.

## Inputs Not Used

- PreFinal sources and historical handoff 05 as active evidence.
- Neighbor production test cases and unrelated untracked diagnostics.

## Key Decisions

- Reject direct v9 promotion because diagnostic IDs and structure were not production-ready.
- Preserve v10 timeout as terminal evidence and use a new capacity-adjusted cycle.
- Consume one correction round after v11 manual gate found Metadata/Priority drift.
- Promote only byte-equivalent accepted v12 content.

## Risks And Fallbacks

- Local default model remained incompatible; live cycles pinned `gpt-5.5`.
- v10 reviewer hard-timed out; v11 used 900 s hard / 600 s idle budgets.
- DOCX was temporarily locked by another process during hash recheck; pinned handoff hash remained unchanged and XHTML/PDF plus tracked source state were verified.

## Validation

- 72 focused tests passed after promotion/validator changes.
- Production strict validator passed 37/37 with zero findings.
- Full regression passed: 511 tests (`1` skipped) and artifact-validator shards `7/7`.
- Agent-layer suite passed: 400 tests (`1` skipped) and artifact-validator shards `7/7`.
- Architecture audit passed 59 checks with zero findings.
- Production hash equals accepted v12 hash.

## Contamination Check

- Only calculator-summary production file changed under `fts/AutoFin/test-cases/**`.
- Terminal v8–v12 cycle artifacts were not rewritten or replayed.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Locked baseline and v9 SHA | stable | promotion findings |
| 2 | Added promotion contract/gate | focused tests pass | commits `cb1108a`, `b1c49be` |
| 3 | Ran v10 | reviewer hard-timeout, no promotion | v10 cycle state |
| 4 | Ran v11 with capacity budget | accepted; manual format gate found two gaps | v11 cycle state |
| 5 | Ran single correction v12 | accepted promotion-ready, zero findings | v12 cycle state |
| 6 | Promoted exact v12 bytes | one production file changed | promotion receipt |
| 7 | Ran production strict validator | 37 checks, zero findings | validator output |
| 8 | Replaced downstream ignored runtime references with tracked portable evidence | handoff resolves after clone | accepted-v12 portable artifacts |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Semantic closure | pass | v12 reviewer accepted | none |
| Production readiness | pass | machine gate zero findings | none |
| Gap preservation | pass | GAP-001 in production and traceability | UI prep must preserve |
| Production scope diff | pass | only section-14 calculator file | none |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `work/review-cycles/...v10-v12/` | `machine runtime evidence` | `canonical runner writes` | `yes` | `codex_exec_review_cycle_runner.py` | `yes` |
| `test-cases/14-application-card-calculator-summary-entrypoints.md` | `bounded production Markdown` | `reviewable apply_patch after SHA gate` | `yes` | `n/a` | `yes` |
| `work/stage-handoffs/28-*` | `bounded handoff artifacts` | `reviewable apply_patch` | `yes` | `n/a` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | v10 reviewer hard-timeout | 450 s reviewer budget | fresh immutable v11 with 900/600 s budgets | v10 cycle | `yes` | `partial review never accepted` | use capacity-adjusted budgets for comparable live reviews |
| `TF-002` | writer sandbox git safe-directory rejection | read-only scoped git status | runner-owned production hash guard and root-session git diff | v11 stdout | `yes` | `low: the root session independently verified the production diff` | keep the runner hash guard as the sandbox-independent invariant |
| `TF-003` | DOCX locked during repeated hash command | direct Get-FileHash read | retained pinned Final hash plus XHTML/PDF and tracked-state verification | handoff 27 evidence | `yes` | `no new DOCX evidence used` | recheck when lock clears |
| `TF-004` | clean Windows clone failed on historical snapshot paths | default Windows checkout path handling | `git -c core.longpaths=true clone` into a short root path | portable clone validation | `yes` | `low: checkout behavior only; committed bytes are unchanged` | use the verified longpaths clone command on the second PC |

## Handoff Notes For Next Session

- Start `ft-ui-automation-prep` only from this signed-off baseline.
- Preserve GAP-001; UI evidence may calibrate interactions but cannot invent exact prefill mapping.
