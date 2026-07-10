# Prepared Stage Package Format

This reference defines the compact, source-backed input used by fresh writer and reviewer sessions. It is a transport and verification format, not a replacement for DOCX as the authoritative FT source or XHTML as the mandatory machine-readable source.

## Ownership And Trust Chain

- The runner or an upstream source/scope preparation step builds the package before the LLM stage starts.
- A writer or reviewer must not rewrite its package.
- Full DOCX/XHTML/PDF files stay in the source registry with repository-relative paths and SHA-256 values; they are fallback evidence, not default stage inputs.
- The package contains scoped evidence already checked against DOCX/XHTML and, when available, source parity evidence for PDF.
- Every package artifact is immutable and covered by one package digest. The runner verifies both package artifacts and registered full-source hashes before and after a stage.
- Existing generated test cases, previous cycle outputs and canary artifacts must never enter the package as requirement evidence.

## Layout

```text
work/review-cycles/<cycle-id>/prepared-input/<package-id>/
  stage-package.json
  source-evidence.md
  atomic-obligations.json
  stage-instructions.md
```

The four files are the default writer/reviewer input capsule. Package-local paths are repository-relative POSIX paths. Unknown fields, missing files, stale hashes, duplicate ids and path traversal are blocking errors.

## `stage-package.json`

Required fields:

- `package_version`: currently `3`; versions `1` and `2` remain readable as legacy evidence but are not eligible for the optimized writer fast path;
- stable `package_id`, `ft_slug`, `scope_slug` and `section_id`;
- `created_at` with timezone;
- `source_registry`: full source path, role, SHA-256 and scope locator;
- `package_artifacts`: the other three package files with path, kind, SHA-256 and byte size;
- `execution_profile`: initially only `simple-field-property` is eligible for the optimized writer fast path;
- `unsupported_dimensions`: explicit dimensions that require the standard writer, for example table parity, numeric boundaries, integration/persistence or dependency/state design;
- `forbidden_evidence_roots`: generated TC, old cycle and canary roots that must not be read as source evidence;
- `fallback_policy`: `targeted-only`;
- `package_digest`: SHA-256 over the canonical payload without this field.

The package is rejected when registered full sources changed after preparation. Full source files are not copied into `prepared-input/`.

Version `3` fast-path packages must register both the authoritative `.docx` as `source-of-truth` and the mandatory `.xhtml`/`.html` extraction source as `machine-readable`. A package with only one representation is ineligible even when its selected evidence is otherwise well formed.

The runner must route to the standard writer when the package is legacy/unclassified, its profile is not `simple-field-property`, or `unsupported_dimensions` is non-empty. Fast-path rejection is a quality guard, not a reason to weaken the source package.

## `atomic-obligations.json`

Required top-level fields are `package_version`, `package_id`, `obligations`, `coverage_gaps` and `digest`.

Each obligation contains:

- unique `obligation_id` using `ATOM-*`;
- non-empty `source_refs` using exact requirement codes and/or `SRC-*` anchors;
- one independently checkable `atomic_statement`;
- `observable_oracle` or an explicit linked gap;
- `test_intent`;
- `coverage_status`: `testable | gap | unclear | not-applicable`;
- optional `dictionary_refs` and `notes`. In version `3`, a testable claim about dictionary/reference-list provenance must link exact `DICT-*` inventory evidence; otherwise that claim stays a linked gap. Every declared gap must be linked from at least one obligation, reference matching is token-exact, and a fast-path package cannot contain blocking gaps.

Each gap contains a stable `GAP-*` id, source refs, problem, handling and blocking flag. One source row may map to multiple obligations; the builder must not assume that one row equals one atom.

## `source-evidence.md`

Keep only scope-local evidence needed to understand the obligations:

- scope inclusion/exclusion;
- exact source rows/statements and locators;
- parity decisions and limitations;
- dictionary/oracle statements;
- coverage gaps and accepted risks.

Builder inputs use explicit selectors. Each selector must resolve to a Markdown heading block or a narrow line window; missing selectors block the package. Full-file inclusion is explicit and byte-capped. One evidence slice is capped by its declared `max_bytes`, and combined `source-evidence.md` is capped at 32768 bytes.

Do not copy whole DOCX/PDF documents, unrelated sections, historical reports or generated TC. The file must name every `SRC-*`, requirement code and `GAP-*` used by `atomic-obligations.json`.

## `stage-instructions.md`

This is a short operational contract. It states role, scenario, allowed inputs, output path, sandbox, timeout, command budget, idle timeout and fallback rules. It must require the stage to:

1. use the prepared package fast path without rerunning source locator, scope analyzer or full source parity;
2. write a structurally complete minimum output before optional refinement;
3. keep scratch and outputs inside the attempt root;
4. access a registered full source only for one named obligation/source locator when package evidence is insufficient;
5. record a `targeted_source_fallback` event with reason, source path and locator;
6. stop as `blocked` rather than invent evidence.

## Prototype Budgets

Defaults for a small prepared-package smoke are configurable technical guardrails:

| budget | writer | reviewer |
| --- | ---: | ---: |
| package artifact bytes | 512000 | 512000 |
| hard timeout seconds | 180 | 90 |
| idle timeout seconds | 60 | disabled; hard deadline applies |
| command executions | 12 | 8 |
| first meaningful draft deadline seconds | 90 | n/a |

Before the first meaningful draft write, the writer is governed by the first-artifact deadline rather than the post-write idle timeout. After a meaningful write, draft changes and JSONL events refresh the idle clock. Exceeding a hard technical budget produces `blocked-package-budget`, `blocked-command-budget`, `blocked-first-artifact-deadline`, `blocked-idle-timeout` or `blocked-timeout`. Increasing a budget is an explicit experiment decision, not automatic recovery.

## Fast Path And Fallback

The runner verifies the four package files and embeds a compact projection into the starting prompt. The optimized writer must not spend stage commands rereading package files, the full writer skill or general references. Package-level notes are included only through applicable scope-local selectors. A stage must not load document/PDF processing skills or scan full sources by default.

Targeted fallback is allowed only when a named obligation cannot be resolved from the capsule. It must be limited to an exact XHTML/DOCX locator. PDF remains structural evidence only. An unbounded source scan, full document re-analysis or external scratch path blocks the prepared-package run.

## Completion Gates

Before writer output can reach reviewer:

- required output exists under the attempt root;
- draft differs from the runner-owned seed and contains no seed sentinel/placeholders;
- structural validator passes;
- every testable obligation is referenced by at least one `TC-*`;
- every TC traceability id exists in the package;
- `gap` and `unclear` obligations are not represented as executable coverage;
- source/package/input hashes remain unchanged;
- no forbidden evidence root was used;
- JSONL command evidence contains no broad repository scan or registered full-source access without a prior exact `targeted_source_fallback` authorization;
- command, idle and hard-time budgets were respected or the explicit timeout-with-progress policy passed all deterministic gates.

Reviewer fast path receives the same package, writer output and deterministic gate report. It remains read-only and returns a structured outcome; only the runner persists findings and applies transitions.

The runner persists `evidence-access-report.json` before reviewer handoff. A late fallback declaration cannot authorize an earlier source access.
