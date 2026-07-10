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

- `package_version`: currently `1`;
- stable `package_id`, `ft_slug`, `scope_slug` and `section_id`;
- `created_at` with timezone;
- `source_registry`: full source path, role, SHA-256 and scope locator;
- `package_artifacts`: the other three package files with path, kind, SHA-256 and byte size;
- `forbidden_evidence_roots`: generated TC, old cycle and canary roots that must not be read as source evidence;
- `fallback_policy`: `targeted-only`;
- `package_digest`: SHA-256 over the canonical payload without this field.

The package is rejected when registered full sources changed after preparation. Full source files are not copied into `prepared-input/`.

## `atomic-obligations.json`

Required top-level fields are `package_version`, `package_id`, `obligations`, `coverage_gaps` and `digest`.

Each obligation contains:

- unique `obligation_id` using `ATOM-*`;
- non-empty `source_refs` using exact requirement codes and/or `SRC-*` anchors;
- one independently checkable `atomic_statement`;
- `observable_oracle` or an explicit linked gap;
- `test_intent`;
- `coverage_status`: `testable | gap | unclear | not-applicable`;
- optional `dictionary_refs` and `notes`.

Each gap contains a stable `GAP-*` id, source refs, problem, handling and blocking flag. One source row may map to multiple obligations; the builder must not assume that one row equals one atom.

## `source-evidence.md`

Keep only scope-local evidence needed to understand the obligations:

- scope inclusion/exclusion;
- exact source rows/statements and locators;
- parity decisions and limitations;
- dictionary/oracle statements;
- coverage gaps and accepted risks.

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
| hard timeout seconds | 180 | 120 |
| idle timeout seconds | 60 | 45 |
| command executions | 12 | 8 |
| first complete output target seconds | 90 | n/a |

Exceeding a hard technical budget produces `blocked-package-budget`, `blocked-command-budget`, `blocked-idle-timeout` or `blocked-timeout`. Increasing a budget is an explicit experiment decision, not automatic recovery.

## Fast Path And Fallback

Fast path reads only the four package files plus package-level `AGENT-NOTES.md` when declared. A stage must not load document/PDF processing skills or scan full sources by default.

Targeted fallback is allowed only when a named obligation cannot be resolved from the capsule. It must be limited to an exact XHTML/DOCX locator. PDF remains structural evidence only. An unbounded source scan, full document re-analysis or external scratch path blocks the prepared-package run.

## Completion Gates

Before writer output can reach reviewer:

- required output exists under the attempt root;
- structural validator passes;
- every testable obligation is referenced by at least one `TC-*`;
- every TC traceability id exists in the package;
- `gap` and `unclear` obligations are not represented as executable coverage;
- source/package/input hashes remain unchanged;
- no forbidden evidence root was used;
- command, idle and hard-time budgets were respected or the explicit timeout-with-progress policy passed all deterministic gates.

Reviewer fast path receives the same package, writer output and deterministic gate report. It remains read-only and returns a structured outcome; only the runner persists findings and applies transitions.
