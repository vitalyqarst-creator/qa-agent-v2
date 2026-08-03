# Review Cycle Stage Contract v2

This reference is the canonical backend-independent contract for one writer or reviewer stage. It defines process/artifact boundaries, not QA or reviewer semantics.

Fresh sessions may use the compact prepared-input capsule defined in `prepared-stage-package-format.md`. The capsule keeps full binary sources in a verified fallback registry instead of declaring them as default stage inputs.

The optimized prepared writer and reviewer are allowlisted only for package version 9 with `execution_profile = simple-field-property` and no unsupported dimensions. The default `release` mode additionally requires no blocking coverage gaps or execution dependencies. An explicit source-first `draft-with-blocking-gaps` package may run writer/reviewer only for the executable ready subset after the compiler has retained every other guard, proved at least one ready testable obligation and isolated blocked obligations from every ready TC/design-plan group; it remains unsigned and ineligible for promotion. Versions 1 through 8 remain readable as immutable diagnostic evidence but are not runnable as the current prepared contract. Package version 9 retains the v8 machine-readable `OBL-* -> ATOM-* -> TC/GAP`, exhaustive dictionary, calibration, exact `reference-only` fixture values and input-fingerprint contracts and adds digest-bound structured release/dependency status. All table-parity, numeric-boundary, integration/persistence and dependency/state packages route to the standard writer/reviewer contracts. Prepared execution uses the compact technical projections in `prepared-writer-runtime-profile.md` and `prepared-reviewer-runtime-profile.md`; the full skills and deep reviewer rubric remain authoritative outside this narrow allowlist.

## Operational Run Profiles

`review_cycle_backend_dispatcher.py` uses a separate `--run-profile` contract; this is not the prepared package `execution_profile`:

- `production` is the default real-work route. It keeps capability preflight, fresh writer/reviewer sessions and every deterministic/semantic gate, but never scans detailed event/context attribution. Its optional performance output contains compact stage metrics and the dispatcher timing breakdown.
- `benchmark` keeps the same quality gates and additionally requires `--performance-output`, detailed event/context attribution and benchmark metrics.

Performance output version 2 separates capability probe, runner preflight, runner wall time, summed stage execution, runner orchestration overhead and reporting time. Profile selection must never weaken writer/reviewer acceptance gates.

## Compatibility

The existing SDK runner remains on the v1 stage-updated-state contract until a dedicated adapter is implemented. V2 is additive: introducing its models must not change v1 execution, timeout recovery or session routing.

## Ownership

- `cycle-state.yaml`, session maps, runner events, snapshots and promotion receipts are runner-owned.
- A v2 stage must not edit runner-owned orchestration state.
- Workspace writer stages may write only declared stage-produced outputs under an allowed attempt root. A structured prepared writer is read-only and returns a schema-constrained draft contract that the runner materializes.
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

Writer stage-produced outputs must stay under both `attempt_root` and an allowed write root. Read-only writer and reviewer manifests declare no allowed write roots and no stage-produced files; their outputs are persisted by the runner. All expected outputs, including runner-produced captures/status, stay under the attempt root. The canonical test-case path must be under a forbidden write root.

Prepared writer attempts may include a runner-owned draft seed under `runner-input/`. In the default structured fast mode, the writer uses a read-only sandbox and zero-command budget, returns `contract_version`, `status`, `draft_markdown` and `blocking_reasons`, and never chooses an output path. The runner validates the exact contract, atomically materializes the declared draft and applies the normal seed, structure and obligation gates. Malformed, partial, timed-out or command-using results block without workspace fallback. The legacy workspace mode remains explicit and keeps the first-write rules for recovery experiments.

For exhaustive dictionary obligations, the structured writer receives dictionary identity, coverage mode and value count but does not own the full leaf payload. It keeps the executable check symbolic through the exact `DICT-*` id. The runner rejects writer output that enumerates two or more values from a runner-owned exhaustive set, then materializes the complete immutable hierarchy exactly once before the ordinary dictionary-completeness gate and reviewer handoff. For bounded `reference-only` scenarios, package v9 transports only the exact group/value/path fixtures explicitly named by the design plan. The runner places that small projection in the draft seed, canonicalizes it before gates and requires the linked TC to retain it; a generic substitute cannot reach reviewer.

Before any structured writer process starts, the runner must apply an output-capacity preflight based on complete `planned_test_case_id` groups. If the full set exceeds the single-session limit, one-shot execution is forbidden. The runner creates an immutable shard plan whose ordered union equals the full test-case and obligation sets and whose shards are pairwise disjoint. One TC group must never be split. Every shard runs in a fresh read-only backend session, returns only its assigned `## TC-*` sections and passes an exact ID/order/traceability gate. A failed shard blocks the cycle without retry or transport switching. Only the runner merges passed shards in canonical order, and the full seed, structure, obligation, quality and production-boundary gates run against that merge before one fresh full-set reviewer session.

Prepared execution also applies observable-oracle and state-change preflights before attempt creation. Known non-observable or empty prepared oracles block the package. A reset obligation is runnable only when its immutable package proves capture of the initial visible state, setup of a state explicitly different from that capture, and an observable inequality check before the target action. A new immutable cycle may perform a bounded targeted repair only when prior deterministic findings use an allowlisted repairable quality class and reference known TC ids. The prior complete draft and findings are hash-bound handoff artifacts, not requirement evidence. The read-only writer returns exactly the assigned replacement sections; the runner validates their ordered TC/OBL/ATOM set and splices them into the prior draft. For a new package, the runner may update only the exact per-TC `package_id` line in preserved sections; it records byte preservation separately and proves preservation after normalizing that one metadata field. Any other non-target change, input drift, extra/missing TC or unsupported finding class blocks before reviewer. A package-metadata gate then requires exactly one current `package_id` in every TC. The merged full set follows the ordinary deterministic gates and fresh reviewer contract.

The runner is the single numeric source for current prepared package eligibility. Compact runtime profiles must not hard-code a package version. Before attempt creation, the runner validates the immutable package and its digest, rejects stale numeric profile allowlists, and projects the same `package_version`, `package_id` and `package_digest` identity into both writer and reviewer metadata.

Prepared obligation gate version `2` scopes traceability to Markdown TC sections. A TC ends at the next `TC-*` heading or the next heading of the same/higher level; nested headings remain inside the case and fenced code blocks are ignored. Set-level coverage gaps and other sections after the last TC must not be attributed to that TC. Bulleted and unbulleted bold traceability fields are equivalent inside the scoped case.

Prepared reviewer attempts receive a runner-built inline projection containing eligible package metadata, the compact reviewer profile, selected evidence, atomic obligations, structured evidence for every referenced `DICT-*`, deterministic gate summaries, the immutable draft and its SHA-256. Missing or malformed referenced dictionary evidence blocks before launch. The prompt must not direct the stage to reread package/reference/source files, and its UTF-8 size is capped at `64 KiB`; oversized handoffs route out of the fast path instead of silently expanding context. Artifact paths and hashes remain in `stage-input.json` for auditability even when their verified contents are embedded.

For a current source-first package, the complete source assertion manifest and accepted independent receipt remain immutable only in hash-bound `source-evidence.md`; they are not copied wholesale into writer or reviewer prompts. Before projection the runner rechecks the package-declared source-evidence and obligation-artifact SHA-256 values. The deterministic `prepared-digest-bound-source-evidence-projection-v1` carries the full artifact SHA-256, manifest digest, canonical receipt SHA-256, extraction/baseline digests and accepted decision. Its selected assertion rows contain only assertion id, source-row id, reviewed canonical statement, polarity/disposition/readiness/risk, typed condition/action/oracle clauses, requirement codes and exact OBL/DICT/GAP/calibration bindings. It excludes bounded row text, source fragments, scope-boundary details and independent-review notes. A writer shard receives only assertions mapped to that shard's exact obligation set; an unknown, duplicate, non-testable or assertion-less selected obligation blocks before launch. The reviewer additionally receives exact routed dimension bindings and a digest-bound semantic projection of every compiled obligation, coverage gap and referenced dictionary value. Every draft TC must carry a traceability field with at least one known testable OBL; unknown OBL/ATOM/SRC/DICT/GAP ids or BSR/GSR/DIT codes block projection and name the offending TC. Default source-projection caps are `256 KiB` for writer and `256 KiB` for reviewer (the smaller overall fast-prompt cap still wins); the deterministic byte/digest report is embedded in the stage context-budget report. Reviewer capacity accounting measures the compiled semantic projection separately and adds it to source-projection bytes before applying the overall reviewer context cap. Exceeding a cap blocks instead of falling back to the full receipt. The full immutable source basis uses a separate storage cap and is never substituted for a role projection.

The inline metadata also carries compiler `output_mode`, `release_eligible` and
exact blocking source-gap ids. An accepted source assertion receipt proves the
source model was independently checked; it does not override these release
fields.

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

An eligible prepared writer returns structured writer contract version `1`: `draft-ready` requires non-empty Markdown and no blocking reasons; `blocked-input` requires an empty draft and at least one reason. An eligible prepared reviewer returns structured review contract version `2`: the exact reviewed draft SHA-256, one verdict for every supplied atomic obligation, referenced `TC-*`, structured findings and a summary. Both exact and generic bounded reviewer schemas restrict verdicts by `coverage_status`; the generic schema groups exact obligation ids by status instead of exposing one permissive verdict enum. The runner rejects missing/duplicate/unknown atoms, unknown test-case ids, hash mismatch, verdicts incompatible with `coverage_status`, blocking verdicts without an `error` finding, and `accepted` with an error or incomplete obligation result. The runner, not either read-only stage, persists draft/findings artifacts. Standard scenarios retain their compatibility contracts.

For a sharded writer route, each shard is a distinct v2 stage attempt with a distinct backend session id. `writer-r1` also acts as the runner-owned merge anchor; later shard attempts may complete first, but reviewer routing is forbidden until the anchor draft and all full-set gates are complete. Shard completion is not semantic sign-off.

For a targeted-repair route, the replacement writer is likewise a new backend session and the reviewer must receive another fresh session. A successful splice is only `draft-ready`; it does not inherit a prior verdict and cannot bypass reviewer sign-off.

The API response-format schemas intentionally use only the verified transport-compatible subset and do not rely on root `oneOf` or `uniqueItems`. Array uniqueness and all semantic cross-field invariants remain mandatory runner-side checks after transport parsing; removing an unsupported transport keyword must not weaken sign-off integrity.

A stage must never return `signed-off`. Required outputs must exist for non-blocked results, undeclared outputs are rejected, output kinds must match the manifest, and a backend session id must not have been used by an earlier stage.

## Runner-Owned Transitions

The runner maps `(current stage_status, scenario, outcome, semantic_round)` through an allowlist. Unknown combinations block. Reviewer `changes-required` after semantic round 2 maps to `round-cap-reached`. `blocked` maps to `blocked-input`.

Only the runner may produce `signed-off`, and only after the reviewer returns `accepted` for a terminal review stage and deterministic terminal gates pass. Mapping an accepted outcome is not permission to invent or override reviewer findings.

When a reviewer accepts a `draft-with-blocking-gaps` candidate, the semantic
review evidence is valid but the lifecycle terminates as
`workflow_status = blocked-source-gaps` for primary source gaps or
`blocked-execution-dependencies` for a typed execution-dependency registry, and
`stage_status = blocked-input`, with
`reviewer_stage_status = accepted`, `draft_or_unsigned = true` and
the matching blocking `promotion_status`. The runner must not create a promotion
seed, canonical publication or signed-off snapshot. After clarification, source
assertions and coverage gaps are rematerialized into a fresh immutable cycle;
the blocked draft is not resumed or promoted.

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
