# Content Placement

This document defines canonical knowledge placement in the project.

## What Belongs in `AGENTS.md`

- agent role;
- global prohibitions;
- general result-quality criteria;
- routing between skills;
- single-source-of-truth rule.

## What Belongs in `skills/*/SKILL.md`

- phase-specific workflow;
- skill inputs and outputs;
- usage triggers;
- skill constraints;
- links to canonical references.

## What Belongs in `references/`

- stable reusable documents;
- canonical rules for writing and reviewing agent instructions;
- templates and formats;
- traceability rules;
- responsibility boundaries;
- architecture-audit checklists;
- instruction-context selection manifests, if they describe only which instructions to read for a scenario and not the QA/workflow rules themselves.

## What Belongs in `fts/<ft-slug>/AGENT-NOTES.md`

- package-specific notes for one FT package;
- local abbreviations and terms;
- package-specific cautions and requirement-reading nuances;
- links to helper artifacts for that package;
- instructions that must apply in every new session for that FT, but are not global project rules.

## What Belongs in `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`

- package-level operational notes only for `ft-ui-automation-prep`;
- runtime URL and entrypoints for UI runs;
- test credentials and authentication rules, if they may be stored in the repository;
- stable flows for creating test data and starting entities;
- package-specific UI pitfalls and reproducible setup rules that must survive separate UI sessions.

## What Belongs in `fts/<ft-slug>/work/test-design/<scope>/`

- table-heavy writer artifacts: `Source Row Inventory`, `Source Table Normalization`, `Test Design Decision Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, `Test Design Review`, `Coverage Gaps`, `Writer Quality Gate`, and related matrices;
- one canonical artifact per table type for the concrete scope;
- data that the reviewer/validator must treat as the source of truth before reading `TC-*`.

The canonical test-case file in `test-cases/` stores links, a short summary, and the `TC-*` cases themselves, but not full copies of those tables.

## What Belongs in Practical Source-First Handoff

- scope boundaries, source rows, coverage gaps, clarification requests, source
  parity, dictionaries, oracle inventories, and mockup inventory for the concrete
  scope;
- one active `prompt.scope-to-writer.md` for normal production TC writing.

## What Belongs in Strict Source-Contract Handoff

- `source-assertions.json` next to confirmed scope/source-row artifacts;
- a separate `source-assertion-review.json` created by an independent reviewer and bound to the exact manifest digest;
- source-model semantics only before the writer. Draft TC, promotion receipt, and runtime diagnostics remain in review-cycle outputs.

## What Belongs in Code

- technical implementation;
- APIs, models, and scripts;
- automated checks.

## What Not to Do

- do not copy the same procedural workflow into both `AGENTS.md` and a skill;
- do not store domain policy text in code;
- do not use a skill as another place for global rules that already belong in `AGENTS.md`;
- do not put package-specific nuances of a concrete FT into global `AGENTS.md` when `fts/<ft-slug>/AGENT-NOTES.md` is the right place;
- do not mix package-wide FT notes from `fts/<ft-slug>/AGENT-NOTES.md` with phase-specific UI operational notes when `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md` is the right place.
