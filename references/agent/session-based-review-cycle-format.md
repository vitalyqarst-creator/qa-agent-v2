# Session-Based Review Cycle Format

This reference defines the new writer/reviewer lifecycle that runs each stage in a separate Codex SDK session. It is the target process for new automated review-cycle orchestration.

The existing pre-SDK `iteration.full_loop` flow is compatibility-only for historical artifacts. Do not make the old full-loop the source of truth for this process.

New session-based runs must not create or update `fts/<ft-slug>/work/review-loops/<scope-slug>/`. That path is legacy-only historical evidence. Active prompts, outputs, state, session metadata and snapshots for this process live under `fts/<ft-slug>/work/review-cycles/<scope-slug>/`.

## Core Rule

The writer never starts the reviewer directly. The SDK runner reads state, verifies gates, starts the next Codex session, writes session metadata, and creates snapshots. For unattended execution, the runner may repeat this one-session operation with `run-until-terminal`, reloading `cycle-state.yaml` after each completed stage until a terminal or non-runnable status is reached.

Each stage receives only the active prompt, resolved instruction-loading scenario context and required artifacts for that stage. It must not rely on previous chat history. The runner injects the selected instruction files from `resolve_instruction_context.py`; the stage must read them before writer/reviewer decisions and record the resolver command, budget status and selected files in its session log.

## Stage Contract Versions

The existing SDK runner remains a `v1` compatibility path: each v1 stage updates `cycle-state.yaml` before ending. If such a session completes without advancing `current_stage`, `stage_status`, `semantic_round` or `active_transition_prompt`, the v1 runner must stop instead of starting another copy of the same stage.

`contract_version: 2` is defined in `review-cycle-stage-contract-v2.md`. A v2 stage must not edit `cycle-state.yaml` or production test cases; it returns a strict artifact-backed outcome, and the runner applies runner-owned transitions. It must never report `signed-off`. Introducing v2 does not silently change v1 recovery behavior.

For v1, SDK `turn_status = interrupted` is not automatically a failed stage. If the stage already advanced `cycle-state.yaml` and the updated state validates, the runner may classify it as `completed-with-progress`. Without state advancement and validation, interruption remains a failed stage and the chain stops. V2 completion is classified from the runner-owned manifest/result/artifact evidence instead of a stage-written state transition.

The runner writes process evidence separately from writer/reviewer artifacts:

- `runner-events.ndjson`: append-only lifecycle events for locks, thread start, turn finish and stage completion.
- `outputs/<stage>-completion.yaml`: runner-owned completion manifest with thread/turn ids, raw turn status, classified session status, before/after progress markers and snapshot references.

These files support diagnosis and recovery only. They do not contain reviewer verdicts and must not override `cycle-state.yaml`.

## Lifecycle

The default stage order is:

Default chain: `scope-gap-review -> writer-r1 -> structure-preflight-r1 -> writer-structure-r1 if blocked -> structure-preflight-r1 -> semantic-review-r1 -> writer-r2 -> semantic-review-r2 -> format-review-final -> writer-format-final -> semantic-regression-final -> signed-off|round-cap-reached`.

0. `scope-gap-review`: optional reviewer session after scope analysis, required when `scope-coverage-gaps.md` contains any `GAP-*`.
1. `writer-r1`: initial draft in a writer session.
2. `structure-preflight-r1`: reviewer structure preflight in a reviewer session.
3. `writer-structure-r1`: structure-only writer remediation when preflight blocks parseability or canonical schema review.
4. `semantic-review-r1`: traceability and test-design review in a reviewer session.
5. `writer-r2`: semantic revision in a writer session, only when round 1 has semantic findings.
6. `semantic-review-r2`: final semantic review in a reviewer session.
7. `format-review-final`: structure/format review after semantic closure.
8. `writer-format-final`: format-only writer revision, only when format findings exist.
9. `semantic-regression-final`: final check that format-only changes did not alter semantic coverage.
10. `signed-off` or `round-cap-reached`.

Max two semantic rounds: semantic review is limited to two rounds. A third semantic review round is not allowed by default.

## Cycle State

The process state lives in:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/cycle-state.yaml
```

`workflow-state.yaml` may point to this state for compatibility, but `cycle-state.yaml` is the source of truth for the session-based cycle.

When a matching `cycle-state.yaml` exists for the same `ft_slug` and `scope_slug`, and it is newer than the legacy `workflow-state.yaml`, validators and downstream routing must treat `cycle-state.yaml` as authoritative for active process status. The legacy `workflow-state.yaml` may still be checked for readability and artifact links, but its `ready-for-review` / `next_skill` routing gates must not create active writer/reviewer errors after the session-based cycle has taken over.

Required fields:

```yaml
ft_slug: <ft-slug>
scope_slug: <scope-slug>
section_id: <section-id>
current_stage: <stage-id>
stage_status: <status>
semantic_round: <0|1|2>
max_semantic_rounds: 2
canonical_test_cases: test-cases/<section-id>-<scope-slug>.md
test_design_dir: work/test-design/<section-id>-<scope-slug>
active_snapshot: work/review-cycles/<scope-slug>/versions/<snapshot-id>
active_transition_prompt: work/review-cycles/<scope-slug>/prompts/<prompt-file>.md
sessions: []
latest_artifacts: []
blocking_reasons: []
blocking_findings: []
open_questions: []
accepted_risks: []
```

Before `writer-r1`, `canonical_test_cases` is the intended canonical path and may not exist yet. The runner must still reject snapshot paths under `work/review-cycles/.../versions/`, but it must not require the file to exist for `scope-ready-for-gap-review`, `scope-gap-review-passed` or `scope-ready-for-writer`.

`cycle-state.yaml` must stay in runner simple-YAML form: top-level scalar fields plus top-level string lists only. Do not write nested maps under `latest_artifacts`, `blocking_reasons`, `blocking_findings`, `open_questions`, `accepted_risks` or `sessions`; put rich details in sidecar artifacts and list those artifact paths. The runner may tolerate and normalize simple accidental nested map leaves for recovery, but that is not the canonical format.

Allowed `stage_status` values:

- `scope-ready-for-gap-review`
- `scope-gap-review-passed`
- `scope-ready-for-writer`
- `writer-draft-ready`
- `structure-preflight-blocked`
- `semantic-review-ready`
- `semantic-revision-needed`
- `semantic-review-passed`
- `format-review-ready`
- `format-revision-needed`
- `final-regression-ready`
- `signed-off`
- `round-cap-reached`
- `blocked-input`

## Post-Session Transition Matrix

The runner and reviewer/writer prompts must stay aligned with this matrix. A session may also produce a terminal status: `signed-off`, `round-cap-reached` or `blocked-input`.

| scenario | allowed non-terminal post-session `stage_status` |
| --- | --- |
| `reviewer.scope_gap_review` | `scope-gap-review-passed`; `scope-ready-for-writer` |
| `writer.session_initial_draft` | `writer-draft-ready` |
| `writer.remediation.structure_preflight` | `writer-draft-ready` |
| `writer.session_semantic_revision` | `semantic-review-ready` |
| `writer.session_format_revision` | `final-regression-ready` |
| `reviewer.structure_preflight` | `semantic-review-ready`; `structure-preflight-blocked` |
| `reviewer.semantic_traceability_test_design` | `format-review-ready`; `semantic-review-passed`; `semantic-revision-needed` |
| `reviewer.semantic_regression` | |
| `reviewer.structure_format_final` | `final-regression-ready`; `format-revision-needed` |

## Reviewer Passes

The session-based cycle uses reviewer modes as separate sessions:

- `scope_gap_review`: pre-writer review of scope gaps, clarification requests and source anchors.
- `structure_preflight`: parseability and blocking format prerequisites only.
- `semantic_traceability_test_design`: traceability, coverage, test-design and expected-result review.
- `structure_format_final`: final template, numbering, grouping and wording review after semantic closure.
- `semantic_regression`: final check that formatting changes did not alter coverage or meaning.

`structure_preflight` must not spend work polishing the set. It only blocks cases that cannot be reviewed reliably.

When `structure_preflight` blocks the cycle and creates an active writer prompt, `structure-preflight-blocked` is recoverable by `writer-structure-r1`. This writer stage must perform structure-only remediation and route back to `writer-draft-ready` / `reviewer.structure_preflight`; it must not perform semantic redesign.

`scope_gap_review` must not review test cases or create coverage matrices for test cases. Its output is `scope-gap-review.md` and a routing decision: writer-ready, scope revision needed, or blocked input.

`structure_format_final` must not require new semantic checks. If it finds missing behavior, non-atomic semantic coverage or unsupported expected results, the cycle returns to semantic review, subject to the two-round cap.

## Versioned Snapshots

The canonical test-case file stays in:

```text
fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md
```

Do not create competing canonical versions under `test-cases/`.

Snapshots live in:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/versions/<snapshot-id>/
```

Recommended snapshot ids:

- `r0-baseline`
- `r1-writer-draft`
- `r1-structure-preflight`
- `r1-semantic-review`
- `r2-writer-revision`
- `r2-semantic-review`
- `final-format-review`
- `final-format-revision`
- `final-semantic-regression`
- `signed-off`
- `round-cap-reached`

Each snapshot should include a `snapshot-manifest.yaml` with file path, size and SHA-256 for every copied artifact.

Snapshot candidates:

- canonical test-case file;
- `work/test-design/<section-id>-<scope-slug>/` artifacts;
- reviewer outputs from `work/review-cycles/<scope-slug>/outputs/`;
- writer response artifacts from `work/review-cycles/<scope-slug>/outputs/`;
- active prompts from `work/review-cycles/<scope-slug>/prompts/`;
- `cycle-state.yaml`;
- `codex-session-map.yaml`;
- `runner-events.ndjson`;
- `outputs/<stage>-completion.yaml` files.

Snapshot exclusions:

- never copy `work/test-design/<scope-slug>/_artifact_write/` scratch directories into `versions/<snapshot-id>/`;
- never re-snapshot existing `work/review-cycles/<scope-slug>/versions/` contents into a new snapshot;
- snapshot manifests should list only canonical/current artifacts, prompts, outputs and runner evidence needed for diagnosis/replay.

If the canonical test-case file does not exist yet in pre-writer statuses, snapshots include state, prompts and scope/test-design artifacts only.

## Gates

The runner must not start semantic review when structure preflight has blocking findings.

The runner must not start format review until semantic review has passed.

In other words, format review must not run before semantic review passes.

The runner must not start semantic round 3. After round 2, unresolved `error`, `warning` or traceability `gap` means `round-cap-reached`.

The runner must not mark `signed-off` unless the latest evidence proves:

- semantic review passed;
- format review passed or format-only writer revision was followed by semantic regression;
- no findings with `severity = error` or `severity = warning` remain;
- traceability matrix has no `coverage_status = gap`, except explicitly accepted residual `unclear`;
- snapshots and session metadata exist for the stages that ran.

UI automation prep can start only after `signed-off`; `round-cap-reached`, `blocked-input` and unresolved semantic findings are not valid UI-prep inputs.

## Required Separation

Writer sessions may create or modify test cases and writer artifacts.

Reviewer sessions are read-only SDK turns or deterministic runner-owned checks. They return findings, matrices, summaries and routing decisions; the runner persists reviewer artifacts, prompts and state updates. Reviewer sessions must not edit the canonical test-case file.

The v1 SDK runner may update `cycle-state.yaml`, `codex-session-map.yaml` and snapshots, but must not invent review decisions. Under v2, only the runner updates those orchestration artifacts; stage sessions return structured outcomes and cannot write orchestration state.

The SDK runner may also start the next session automatically after a completed v1 stage, but only after it reloads and validates the stage-updated `cycle-state.yaml`. A future v2 backend adapter may start the next session only after validating `stage-result.json`, required output hashes and the runner-applied next state.
