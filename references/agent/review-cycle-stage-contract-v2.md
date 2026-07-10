# Review Cycle Stage Contract v2

This reference is the canonical backend-independent contract for one writer or reviewer stage. It defines process/artifact boundaries, not QA or reviewer semantics.

## Compatibility

The existing SDK runner remains on the v1 stage-updated-state contract until a dedicated adapter is implemented. V2 is additive: introducing its models must not change v1 execution, timeout recovery or session routing.

## Ownership

- `cycle-state.yaml`, session maps, runner events, snapshots and promotion receipts are runner-owned.
- A v2 stage must not edit runner-owned orchestration state.
- Writer stages may write only declared stage-produced outputs under an allowed attempt root.
- Reviewer stages are read-only; the runner persists their findings, stream captures and status artifacts.
- Production `test-cases/` is always a forbidden write root for a stage.
- A stage returns a semantic outcome; the runner validates it and applies an allowlisted transition.

## Attempt Layout

Every execution uses a fresh attempt directory:

```text
work/review-cycles/<scope-slug>/attempts/<stage-id>/<attempt-id>/
  stage-input.json
  stage-result.json
  stdout.txt
  stderr.txt
  events.ndjson
  metrics.json
  <declared stage artifacts>
```

An attempt must not reuse runner-owned outputs from an earlier attempt. `StageAttemptLedger` classifies prior attempts from immutable evidence. Incomplete or corrupt attempts require manual reconciliation; a blocked attempt may create a new numbered root only after an explicit `retry_blocked` decision; successful or changes-required attempts cannot be repeated.

## Stage Input Manifest

`stage-input.json` uses `contract_version: 2` and contains:

- stable cycle, stage, attempt and runner-issued session ids;
- role and instruction-loading scenario;
- semantic round, sandbox policy and timeout;
- canonical production test-case path;
- one canonical attempt root;
- prompt, instruction, source and handoff artifacts with repository-relative paths, kinds and SHA-256 values;
- declared expected outputs with `producer = stage|runner` and requiredness;
- allowed and forbidden write roots;
- SHA-256 `input_digest` over the canonical manifest payload excluding the digest field.

The schema is strict. Unknown fields, absolute/traversing paths, duplicate paths, overlapping input/output paths, invalid hashes, role/sandbox mismatches and digest mismatches are blocking contract errors. It intentionally has no previous-thread or resume-context field: each LLM stage must receive a fresh session.

Writer stage-produced outputs must stay under both `attempt_root` and an allowed write root. Reviewer manifests declare no allowed write roots and no stage-produced files. All expected outputs, including runner-produced captures/status, stay under the attempt root. The canonical test-case path must be under a forbidden write root.

## Stage Result

`stage-result.json` contains:

- the manifest identity and `input_digest`;
- actual backend session/thread identity;
- role, scenario, process status and semantic outcome;
- output artifacts with SHA-256;
- timestamps, duration, exit code and timeout flag;
- blocking reasons when blocked.

Allowed outcomes:

- writer: `draft-ready`, `blocked`;
- reviewer: `accepted`, `changes-required`, `blocked`.

A stage must never return `signed-off`. Required outputs must exist for non-blocked results, undeclared outputs are rejected, output kinds must match the manifest, and a backend session id must not have been used by an earlier stage.

## Runner-Owned Transitions

The runner maps `(current stage_status, scenario, outcome, semantic_round)` through an allowlist. Unknown combinations block. Reviewer `changes-required` after semantic round 2 maps to `round-cap-reached`. `blocked` maps to `blocked-input`.

Only the runner may produce `signed-off`, and only after the reviewer returns `accepted` for a terminal review stage and deterministic terminal gates pass. Mapping an accepted outcome is not permission to invent or override reviewer findings.

## Technical Implementation

- `test_case_agent/review_cycle/contracts.py`: strict manifest/result models, digests, path/write boundaries and fresh-session checks.
- `test_case_agent/review_cycle/transitions.py`: allowlisted runner-owned transition decisions.
- `test_case_agent/review_cycle/runtime.py`: shared backend protocol, immutable attempt persistence and filesystem evidence verification.
- `test_case_agent/review_cycle/backends.py`: fresh-thread SDK boundary and backend adapter without resume context.
- `test_case_agent/review_cycle/attempts.py`: deterministic attempt inspection, retry gating and fresh attempt allocation.
- `test_case_agent/review_cycle/metrics.py`: attempt/cycle latency, artifact-volume, outcome and optional token evidence.
- `test_case_agent/review_cycle/orchestration.py`: one completion path from backend evidence to immutable result and metrics.
- `tests/test_review_cycle_stage_contract.py`: focused contract, failure and transition coverage.

The exec prototype persists this contract for each writer/reviewer process. The SDK runner remains on v1 until its dedicated adapter is enabled. Attempt recovery and metrics use the common runtime; live execution remains capability-gated.
