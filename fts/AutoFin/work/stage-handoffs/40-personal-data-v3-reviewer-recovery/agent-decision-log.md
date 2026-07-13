# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| stage | `ft-test-case-iteration` |
| started_from | `work/stage-handoffs/39-personal-data-full-scope-recovery-rollout/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `routing` | V2 reviewer did not start; transport fix exists at `15889ad` | Create a new immutable V3 cycle | V2 is quarantined and cannot prove the patched live path | V3 cycle; handoff 40 | high | applied |
| `DEC-002` | 2 | `source-boundary` | Handoff 38 compiler inputs are verified and unchanged | Compile them directly without generic AI preparation | Avoids the measured 2.306M-token preparation defect without changing evidence | V3 prepared package | high | applied |
| `DEC-003` | 3 | `artifact-write` | New generated cycle and audit handoff are required | Limit writes to V3 cycle and handoff 40; keep production/V1/V2 read-only | Preserves evidence and prevents contamination | iteration session log | high | applied |
| `DEC-004` | 4 | `execution` | V3 is allowed only after deterministic preflight | Authorize exactly one dispatcher live conditionally | Prevents wasting a live run on a known configuration defect | pre-live stop gate | high | applied |
| `DEC-005` | 5 | `fallback` | Compiler rejected an output root that stopped at parent `prepared-input` | Repeat compile with the package-id directory as exact output root | Compiler contract requires `<cycle>/prepared-input/<package-id>` and no package was written | V3 prepared package; `TF-001` | high | applied |
| `DEC-006` | 6 | `execution` | Package, seed, 118 tests, both context budgets, exec capability and contamination boundary pass | Authorize exactly one V3 dispatcher live | Every condition in the pre-live stop gate is satisfied | `pre-live-authorization.md` | high | applied |
| `DEC-007` | 7 | `stop` | Reviewer live returned `changes-required` with four blocking findings | Stop V3 without retry, mutation or promotion | The one-live authorization is exhausted and an immutable failed review is useful evidence | `stop-gate.md`; V3 cycle state | high | applied |
| `DEC-008` | 8 | `root-cause` | Nine TC are non-executable although every deterministic writer gate passed | Classify the failure as an upstream design/package plus deterministic-gate gap, not only a draft wording defect | Prepared obligations already contain undefined continuation intents and insufficient ABS/DaData fixtures | `reviewer-outcome-analysis.md` | high | applied |
| `DEC-009` | 9 | `quality-feedback` | The defect blocks sign-off, has precise reviewer evidence and escaped deterministic checks | Create a bounded eval candidate | The quality loop explicitly requires a candidate for a sign-off blocker with clear pass/fail criteria | `evals/candidates/2026-07-13-action-without-observable-oracle-personal-data.md` | high | applied |
| `DEC-010` | 10 | `routing` | Transport/state recovery is proven, semantic quality is not | Route the next session to design/gate remediation followed by a fresh immutable V4 only after deterministic regression passes | Blind V3 retry would reproduce the same input defect and waste another live run | next-stage prompt; `workflow-state.yaml` | high | applied |
