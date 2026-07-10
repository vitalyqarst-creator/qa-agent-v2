# Review Cycle Stage Contract v2

This reference is the canonical backend-independent contract for one writer or reviewer stage. It defines process/artifact boundaries, not QA or reviewer semantics.

Fresh sessions may use the compact prepared-input capsule defined in `prepared-stage-package-format.md`. The capsule keeps full binary sources in a verified fallback registry instead of declaring them as default stage inputs.

The optimized prepared writer and reviewer are allowlisted only for package version 3 with `execution_profile = simple-field-property`, no unsupported dimensions and no blocking coverage gaps. Versions 1 and 2 remain readable as immutable legacy evidence but route out of the fast path. All table-parity, numeric-boundary, integration/persistence and dependency/state packages route to the standard writer/reviewer contracts. Prepared execution uses the compact technical projections in `prepared-writer-runtime-profile.md` and `prepared-reviewer-runtime-profile.md`; the full skills and deep reviewer rubric remain authoritative outside this narrow allowlist.

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

Prepared writer attempts may include a runner-owned draft seed under `runner-input/`. The seed is an immutable template artifact outside allowed write roots; it is not pre-created at the declared stage output path. The output file is absent at stage start and remains stage-owned, so the writer must create it on the first file write rather than issue an update-only patch. A non-blocked result requires a distinct draft, no seed sentinels, a recorded first meaningful write, and the normal structure/obligation gates.

Prepared obligation gate version `2` scopes traceability to Markdown TC sections. A TC ends at the next `TC-*` heading or the next heading of the same/higher level; nested headings remain inside the case and fenced code blocks are ignored. Set-level coverage gaps and other sections after the last TC must not be attributed to that TC. Bulleted and unbulleted bold traceability fields are equivalent inside the scoped case.

Prepared reviewer attempts receive a runner-built inline projection containing eligible package metadata, the compact reviewer profile, selected evidence, atomic obligations, deterministic gate summaries, the immutable draft and its SHA-256. The prompt must not direct the stage to reread package/reference/source files, and its UTF-8 size is capped at `64 KiB`; oversized handoffs route out of the fast path instead of silently expanding context. Artifact paths and hashes remain in `stage-input.json` for auditability even when their verified contents are embedded.

The prepared reviewer has a `90 s` terminal deadline and a one-command budget separate from the standard reviewer. It has no shorter idle cutoff: with `--output-schema`, the first semantic output may be the final structured object, so transport-only `thread.started` and `turn.started` events cannot distinguish valid silent inference from a hang. The hard terminal deadline remains mandatory and bounds the process. Standard reviewers and writers retain their idle protection. The only allowlisted command is the environment probe when no confirmed probe is available. Its JSONL stream is audited after execution; any other command, skill/reference/package/source reread or broad scan is a blocking evidence-access violation even when the model returned a syntactically valid review contract.

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

An eligible prepared reviewer returns structured review contract version `2`: the exact reviewed draft SHA-256, one verdict for every supplied atomic obligation, referenced `TC-*`, structured findings and a summary. The runner rejects missing/duplicate/unknown atoms, unknown test-case ids, hash mismatch, verdicts incompatible with `coverage_status`, blocking verdicts without an `error` finding, and `accepted` with an error or incomplete obligation result. The runner, not the read-only reviewer, renders `findings.md`. Standard reviewer scenarios retain their existing compatibility contract.

The API response-format schema intentionally uses only the verified transport-compatible subset and does not rely on `uniqueItems`. Array uniqueness and all semantic cross-field invariants remain mandatory runner-side checks after transport parsing; removing an unsupported transport keyword must not weaken sign-off integrity.

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
- `test_case_agent/review_cycle/evidence_access.py`: deterministic JSONL command audit for forbidden evidence roots, broad scans, exact targeted fallback authorization and optional prepared-stage command allowlists.
- `test_case_agent/review_cycle/orchestration.py`: one completion path from backend evidence to immutable result and metrics.
- `tests/test_review_cycle_stage_contract.py`: focused contract, failure and transition coverage.

The exec prototype persists this contract for each writer/reviewer process. The SDK runner remains on v1 until its dedicated adapter is enabled. Attempt recovery and metrics use the common runtime; live execution remains capability-gated.
