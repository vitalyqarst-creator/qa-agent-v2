# Prepared Stage Package Format

This reference defines the compact, source-backed input used by fresh writer and reviewer sessions. It is a transport and verification format, not a replacement for DOCX as the authoritative FT source or XHTML as the mandatory machine-readable source.

## Ownership And Trust Chain

- The runner or an upstream source/scope preparation step builds the package before the LLM stage starts.
- A writer or reviewer must not rewrite its package.
- Full DOCX/XHTML/PDF files stay in the source registry with repository-relative paths and SHA-256 values; they are fallback evidence, not default stage inputs.
- The package contains scoped evidence already checked against DOCX/XHTML and, when available, source parity evidence for PDF.
- Every package artifact is immutable and covered by one digest. The runner verifies artifact and registered-source hashes before and after each stage.
- Existing generated test cases, previous cycle outputs and canary artifacts must never enter the package as requirement evidence.
- Workflow compilation requires an expected FT slug; state, sources, output and attempt root stay inside that package. Neighboring `fts/*` packages are never substitutes.
- Registry entries come only from the linked `source-selection.md`. DOCX and XHTML/HTML use the same base name; selected PDF is structural cross-check evidence.
- The canonical applicability matrix decides routing. Numeric/boundary, dependency/state, integration/persistence, table-parity and unclassified applicable dimensions produce `standard-required` plus explicit `unsupported_dimensions`; flags and prompts cannot force the fast path.
- Compiler contract v3 preserves the exact inventory-bound source-row registry,
  registered extraction-source, binary/auxiliary `evidence_sources` and mockup
  hashes, an independently accepted source assertion receipt and explicit
  source-row -> assertion -> `ATOM-*` -> `OBL-*` -> TC/GAP. Primary evidence is
  row-local; cross-row evidence requires a typed supporting binding. For
  DOCX+XHTML+PDF FT packages, the embedded source contract binds XHTML as
  extraction source, DOCX as semantic source of truth and PDF as
  structural/visual parity evidence; support used for an oracle is also
  hash-bound. Compiler v2 remains readable diagnostic evidence but cannot be
  promoted. Package v9 retains the v8 exhaustive dictionary, calibration,
  input-fingerprint and bounded `reference-only` fixture contracts; evidence
  prose cannot replace typed fields and adds a digest-bound structured release
  status.
- Compiler output mode is explicit. `release` is the fail-closed default;
  `draft-with-blocking-gaps` is a source-first unsigned-draft route, not a
  release or promotion waiver.
- Testable `execution_readiness = dependency-blocked` blocks `release`. Explicit
  `draft-with-blocking-gaps` compiles only the ready subset and carries the exact
  blocked assertion/source-row/ATOM/OBL/GAP/risk/rationale registry in package
  v9 `release_status`. Blocked and ready obligations may not share one TC or
  design-plan group. The accepted result remains unsigned
  `blocked-execution-dependencies`; do not reinterpret the dependency as a
  semantic coverage gap.
- When workflow-state declares `source_to_package_fidelity`, compilation must pass its literal/unit bindings before the package is built; normalized bindings are compiler evidence covered by the package fingerprint.
- When the FT package contains `AGENT-NOTES.md`, workflow compilation embeds it as mandatory package context in `source-evidence.md`. Package notes remain context/guardrails, not a replacement requirement source.
- Every input-based design-plan row binds a concrete synthetic/source-backed value or stable fixture. Abstract classes such as `valid-text` fail with `input-fixture-required`.
- Before live, empty or known non-observable prepared oracles block as `blocked-prepared-oracle-quality`.
- Reset obligations must declare `execution_semantics = reset-to-captured-initial` plus the captured-initial setup, changed-state setup and observable pre-action inequality check. Missing classification or metadata blocks before LLM as `blocked-prepared-state-change-quality`.

## Layout

```text
work/review-cycles/<cycle-id>/prepared-input/<package-id>/
  stage-package.json
  source-evidence.md
  atomic-obligations.json
  stage-instructions.md
```

The four files are the default writer/reviewer input capsule. Package-local paths are repository-relative POSIX paths. Unknown fields, missing files, stale hashes, duplicate ids and path traversal are blocking errors.

`stage-instructions.md` is attempt-bound: its `attempt_root` and `output_path` must exactly match the target writer attempt selected by the runner. A compiled package may be reused as source material for a new compilation, but its immutable manifest must not be passed directly to a different cycle. The runner rejects binding drift before starting an LLM session.

## `stage-package.json`

Required fields:

- `package_version`: currently `9`; versions `1` through `8` remain readable as diagnostic legacy evidence but are not eligible for a new prepared writer run;
- stable `package_id`, `ft_slug`, `scope_slug` and `section_id`;
- `created_at` with timezone;
- `input_fingerprint`: SHA-256 over source registry hashes, compiler evidence, obligations, attempt-bound instructions and routing inputs; it intentionally excludes `created_at`;
- `source_registry`: full source path, role, SHA-256 and scope locator;
- `package_artifacts`: the other three package files with path, kind, SHA-256 and byte size;
- `execution_profile`: `simple-field-property` selects the optimized fast path; `standard-required` selects compact prepared transport with the full standard writer/reviewer instruction scenarios;
- `unsupported_dimensions`: explicit dimensions that require the standard writer, for example table parity, numeric boundaries, integration/persistence or dependency/state design;
- `forbidden_evidence_roots`: generated TC, old cycle and canary roots that must not be read as source evidence;
- `fallback_policy`: `targeted-only`;
- `release_status`: required structured
  `prepared-package-release-status-v1`, included in the package digest. It owns
  `output_mode`, `release_eligible`, exact `blocking_gap_ids`, the complete
  `execution_dependency_registry`, exact excluded OBL ids, unsigned lifecycle
  status and release-blocking finding codes;
- `package_digest`: SHA-256 over the canonical payload without this field.

The package is rejected when registered full sources changed after preparation. Full source files are not copied into `prepared-input/`.

Version `9` fast-path packages must register both the authoritative `.docx` as `source-of-truth` and the mandatory `.xhtml`/`.html` extraction source as `machine-readable`. A package with only one representation is ineligible even when its selected evidence is otherwise well formed.

`release_status` is reconciled against `atomic-obligations.json`: its blocking
gap ids equal the union of compiled blocking gaps and execution-dependency GAPs;
excluded OBL ids equal the registry exactly; blocked ATOM/OBL ids are absent
from the ready subset. A release-eligible package has no blocker, no unsigned
status and no blocking finding code. A draft cannot be release-eligible.

The runner must route `standard-required` packages with explicit `unsupported_dimensions` through the prepared-standard writer/reviewer path. Legacy/unclassified profiles remain blocked. Fast-path rejection is a quality guard, not a reason to weaken the source package.

## `atomic-obligations.json`

Required top-level fields are `package_version`, `package_id`, `obligations`, `coverage_gaps` and `digest`.

Each obligation contains:

- unique `obligation_id` using `OBL-*`; legacy packages may still contain atom ids in this field;
- unique `atom_id` using `ATOM-*` in current package version 9, preserving the machine-readable obligation-to-atom relation used by writer, gate and reviewer;
- non-empty `source_refs` using exact requirement codes and/or `SRC-*` anchors;
- one independently checkable `atomic_statement`;
- `observable_oracle` or an explicit linked gap;
- `test_intent`;
- `coverage_status`: `testable | gap | unclear | not-applicable`;
- optional `dictionary_refs`, `constraint_gap_ids`, `notes` and `planned_test_case_id`;
- v7 `execution_semantics` and nullable `state_change`: `direct` requires null; `reset-to-captured-initial` requires captured/changed setup, a pre-action oracle and `different-from-captured-initial`;
- v8 `dictionary_requirements`: exactly one per `dictionary_ref`, with `coverage_mode = reference-only | all-leaf-values | full-hierarchy`. Exhaustive modes carry `required_values`; bounded reference-only scenarios carry only exact plan-named `fixture_values`. Both preserve group/leaf hierarchy paths and are runner-materialized before obligation gate v4;
- v8 `calibration_status`; `ui-calibration-required` remains active without a `constraint_gap_id`;
- `planned_test_case_id` from the Coverage Obligation Table. A shared TC requires one design-plan row that links all grouped atoms to one action, fixture and oracle. Conflicts or unjustified cross-field/package groups fail as `invalid-planned-test-case-group`.

Versions 1–8 remain readable with their original digests. Every gap must be token-exact and linked as executable or non-blocking. Compiler-v3 gaps require an explicit blocking classification; no implicit `blocking: false` is allowed. In default `release`, a primary blocking gap blocks both fast and standard packages. The explicit `draft-with-blocking-gaps` builder escape hatch is disabled by default and may carry only primary blocking gaps and/or typed execution-dependency blockers alongside at least one ready testable obligation. A constraint gap must remain explicitly non-blocking; blocking constraint gaps and all broad/nonblocking/high-risk guard failures are rejected in either mode. Legacy fast packages also cannot contain blocking gaps.

Each gap contains a stable `GAP-*` id, source refs, problem, handling and blocking flag. One source row may map to multiple obligations; the builder must not assume that one row equals one atom.

Prepared execution profiles, the derived artifact graph, structured/assisted modes, context rule cards, deterministic gate bundle and UI-calibration lifecycle are defined in `references/agent/prepared-context-artifact-graph.md`. `standard-required` uses the read-only structured writer by default; `assisted` requires a new explicit immutable cycle and is never an automatic fallback.

## `source-evidence.md`

Keep only scope-local evidence needed to understand the obligations:

- scope inclusion/exclusion;
- exact source rows/statements and locators;
- parity decisions and limitations;
- dictionary/oracle statements;
- coverage gaps and accepted risks.
- normalized source-to-package fidelity bindings when the workflow declares them.
- for v3, the bounded full source assertion basis plus its accepted exact-digest review receipt.
- `prepared-compiler-release-status-v1` with output mode, release eligibility,
  exact blocking gap ids, release-blocking finding codes and the full coverage
  accounting report.

Builder inputs use explicit selectors. Each selector must resolve to a Markdown heading block or a narrow line window; missing selectors block the package. Full-file inclusion is explicit and byte-capped. One evidence slice is capped by its declared `max_bytes`. Legacy/non-source-first fast evidence remains capped at 32768 bytes and standard routing evidence at 131072 bytes. Compiler-v3 full immutable source basis is a storage/authentication artifact with a separate 2 MiB cap; the whole source-first package is capped at 3 MiB. Writer and reviewer never receive that full basis by default: deterministic role projections are separately capped at 256 KiB each and must preserve the complete ready assertion/OBL set without semantic truncation.

Do not copy whole DOCX/PDF documents, unrelated sections, historical reports or generated TC. The file must name every `SRC-*`, requirement code and `GAP-*` used by `atomic-obligations.json`.

## `stage-instructions.md`

This is a short operational contract. It states role, scenario, allowed inputs, output path, sandbox, timeout, command budget, idle timeout and fallback rules. `simple-field-property` uses `writer.session_prepared_initial_draft`; `standard-required` uses `writer.session_initial_draft`. It must require the stage to:

1. use the prepared projection without rerunning source locator, scope analyzer or full source parity; fast packages use the compact fast runtime profile, while standard packages load the full standard instruction scenario;
2. for structured fast mode, return a complete schema-constrained draft for runner-owned materialization; standard and explicit legacy workspace modes write only inside the attempt root;
3. use `read_only` with command budget `0` for structured fast mode and `workspace_write` only for standard or explicit legacy execution;
4. access a registered full source only for one named obligation/source locator when package evidence is insufficient;
5. record a `targeted_source_fallback` event with reason, source path and locator;
6. stop as `blocked` rather than invent evidence.

Prepared writer output is absent at stage start. `runner-input/draft-seed.md` is a template, not an output placeholder. In structured fast mode the writer does not mutate it or create output; the runner validates the JSON contract and atomically materializes the draft. The first-mutation rule applies only to explicit legacy workspace mode.

## Prototype Budgets

Defaults for a small prepared-package smoke are configurable technical guardrails:

| budget | writer | reviewer |
| --- | ---: | ---: |
| package artifact bytes | 512000 | 512000 |
| hard timeout seconds | 180 | 90 |
| idle timeout seconds | disabled; hard deadline applies | disabled; hard deadline applies |
| command executions | 0 | 1 |
| first meaningful draft deadline seconds | n/a | n/a |

Structured fast writer and reviewer are bounded by hard terminal deadlines because their first semantic output may be the final schema-constrained object. Any writer command produces `blocked-command-budget`; timeout or malformed/partial JSON cannot be treated as progress. The explicit legacy workspace mode retains first-artifact and idle budgets. Increasing a budget is an explicit experiment decision, not automatic recovery.

Input budget is not output-capacity proof. Above the single-session TC limit, preflight must route complete `planned_test_case_id` groups to disjoint bounded shards or block before live. Each shard gets only its source-backed obligations and partial seed; the immutable package remains authoritative for merge gates and reviewer. The plan proves exact TC/OBL membership, digests, complete union and disjointness.

Targeted repair uses a new cycle and hash-bound inputs. Only per-TC `package_id` may change in non-target sections; record byte and normalized-semantic hashes. Any other change blocks. Prior drafts are not requirement evidence or sign-off.

## Recovery And Replay

- A package is bound to one exact cycle, writer attempt root and output path. It is never replayed against another attempt. `compile_prepared_stage_package.py --reuse-if-current` may return the same immutable package only when its v9 `input_fingerprint`, structured release status and registered source hashes still match; any input or attempt-binding change requires a new package id/output root.
- Structured interruption yields no progress because only a complete contract is materialized. Legacy workspace interruption is `completed-with-progress` only after all deterministic gates pass.
- Invalid/missing draft, drift or gate failure stops the cycle; recovery uses a fresh cycle and target-bound package.
- After a blocking source gap is clarified, rematerialize source assertions and
  compile a fresh immutable cycle; do not reuse or promote the prior unsigned
  draft package.
- Interrupted reviewer output is discarded; recovery uses fresh writer/reviewer sessions.
- Re-running a terminal or blocked cycle directory is rejected before LLM launch; existing state and evidence remain unchanged.

Targeted fallback is allowed only when a named obligation cannot be resolved from the capsule. It must be limited to an exact XHTML/DOCX locator. PDF remains structural evidence only. An unbounded source scan, full document re-analysis or external scratch path blocks the prepared-package run.

## Prepared Standard Route

A `standard-required` package keeps all immutable package, obligation, seed, structure and mutation gates, but loads `writer.session_initial_draft` and `reviewer.semantic_traceability_test_design`. Compact transport never makes an unsupported dimension fast-eligible.

Role-specific `stage-input.json` manifests must list the selected standard instruction files, compact source evidence, obligations and runner-owned gate artifacts. The runner enforces separate primary-context budgets before each LLM stage and writes `context-budget.json`; registered DOCX/XHTML/PDF sources are excluded from primary-context byte totals and remain fallback evidence.

Legacy reviewer schema v2 returns rich per-obligation rows. Source-first reviewer
contract v4 binds the draft, source-basis and obligation-set hashes, returns
exactly one compact `{obligation_id, verdict}` row for every bound obligation and
exactly one `dimension_reviews` row for every routed cross-cutting dimension. The
obligation id set must be exact and duplicate-free; a verdict must be compatible
with the obligation coverage status, and every non-passing verdict must have a
linked error finding. Compiler v3 derives a canonical
`reviewer-dimension-source-bindings-v1` map from the test-design applicability
rows and obligation property routing, then embeds it in the immutable,
package-hashed `source-evidence.md`. Each dimension receipt must repeat the
complete canonical sorted ref array from its own map entry exactly; omitting a
bound ref, reordering refs, or citing a ref bound only to another dimension is
invalid even when it occurs elsewhere in the obligation set. Missing, duplicate or unbound
dimension bindings block reviewer launch and post-hoc promotion. `accepted`
requires every testable obligation `covered`, every non-testable
obligation `gap-preserved`, every routed dimension `verified` and no error
finding. Source-model/dimension findings cannot be targeted-repair inputs.
Missing referenced dictionary values still block.

## Completion Gates

Before writer output can reach reviewer:

- required runner-materialized output exists under the attempt root;
- draft differs from the runner-owned seed and contains no seed sentinel/placeholders;
- structural validator passes;
- source-first production-runtime smell gate passes without magic setup, environment/package leakage, generic fixtures/actions/oracles or process-language leakage;
- every testable obligation is referenced by at least one `TC-*`;
- every TC traceability id exists in the package;
- `gap` and `unclear` obligations are not represented as executable coverage;
- source/package/input hashes remain unchanged;
- every exhaustive `dictionary_requirement` is materialized by the runner in its linked TC and passes exact group/leaf/path comparison;
- every non-empty `reference-only.fixture_values` contract is materialized by the runner in its linked TC and passes exact group/value/path comparison;
- no forbidden evidence root was used;
- structured fast writer is read-only and performs no workspace reads; explicit legacy workspace mode may read only its exact runner-declared current `stage-output` root for local self-checks;
- JSONL command evidence contains no broad repository scan or registered full-source access without a prior exact `targeted_source_fallback` authorization;
- command, idle and hard-time budgets were respected or the explicit timeout-with-progress policy passed all deterministic gates.
- the runner writes a non-blocking `semantic-overlap-diagnostic.json` after structural and obligation gates; exact normalized step/final-oracle matches are passed to reviewer for classification and are never cleared merely because titles differ.

Reviewer fast path receives the same package, writer output and deterministic gate report. It remains read-only and returns a structured outcome; only the runner persists findings and applies transitions.

Production promotion additionally requires a valid, non-empty compiler-v3
bounded source basis, its independently accepted source-assertion receipt, an
accepted source-first reviewer contract v4 receipt, strict obligation/runtime
gates, coverage accounting, `output_mode = release`, no blocking source gaps and
byte-identical draft publication. An accepted source receipt or reviewer receipt
does not make `draft-with-blocking-gaps` release-eligible. A marker without a parseable manifest/receipt is rejected before writer.

The runner persists `evidence-access-report.json` before reviewer handoff. A late fallback declaration cannot authorize an earlier source access.
