# Prepared compiler input preparation

You are a dedicated compiler-input preparer. Work only inside this repository and follow root `AGENTS.md` plus `fts/AutoFin/AGENT-NOTES.md`.

## Goal

Prepare immutable compiler inputs for a shadow structured writer-reviewer run of the confirmed full scope `application-card-client-personal-data`. Do not write test cases and do not run writer/reviewer. Resolve the known mapping defects before the orchestrator compiles the package:

- `SEM-001`: `ATOM-025` must be linked to every date-boundary TC that evaluates a D-relative boundary, including `TC-ACPD-026`, `TC-ACPD-027`, `TC-ACPD-028`.
- `SEM-002`: decision-table mappings must exactly equal the current atomic ledger mappings; no off-by-one legacy numbering.

## Inputs

Read these as canonical scope/design inputs:

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- every required current-source scope artifact listed by `fts/AutoFin/work/stage-handoffs/37-personal-data-character-restrictions-gate-v3/prompt.scope-to-iteration.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/atomic-requirements-ledger.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/package-test-design-plan.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/test-design-applicability-matrix.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/test-design-decision-table.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/negative-oracle-inventory.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/requiredness-oracle-inventory.md`
- `fts/AutoFin/work/test-design/14-application-card-client-personal-data/dictionary-inventory.md`

Use `fts/AutoFin/work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r2-draft.md` and `round-2-findings.md` only as regression evidence for SEM-001/SEM-002. They are not requirement or oracle sources.

## Output boundary

Create or edit files only under:

`fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/compiler-inputs/application-card-client-personal-data/`

Required files:

- `compiler-input.yaml`
- `atomic-requirements-ledger.md`
- `coverage-obligation-table.md`
- `package-test-design-plan.md`
- `test-design-applicability-matrix.md`
- `test-design-decision-table.md`
- `coverage-gaps.md`
- `dictionary-inventory.md`
- `mapping-consistency-report.md`

Do not modify existing `work/test-design/**`, `test-cases/**`, review-cycle history, scripts, tests, or handoff 29/37.

## Compiler contract

- `prepared_compiler_contract_version: 2`.
- Canonical target path in `compiler-input.yaml`: `test-cases/14-prepared-shadow-application-card-client-personal-data.md`.
- `latest_artifacts` must point to source selection and every generated compiler input, including optional `test_design_decision_table`.
- Preserve all 42 atoms and the corrected intended mapping to `TC-ACPD-001` through `TC-ACPD-047`.
- Ledger column `constraint_gap_ids` carries non-blocking `GAP-001..GAP-003` on testable atoms.
- Create one coverage-obligation row per `(atom, planned TC)` pair. Each row links exactly one atom and exactly one TC.
- If one TC covers several atoms, create exactly one shared plan row for that TC whose `linked_atoms` set equals the obligation group. Add `grouping-justification:` for cross-field or cross-package groups.
- The union of TC ids per atom must be exactly equal across ledger `covered_by_tc`, obligations `planned_tc_or_gap`, plan `planned_tc_or_gap`, and decision table `planned_tc_or_gap`.
- Every plan row that performs input must include an explicit synthetic fixture through `input_class:<value>` or another accepted concrete fixture field.
- Every testable obligation needs a source-backed observable `required_behavior`. Preserve UI calibration qualifiers and gaps; do not invent rejection messages or DaData failure behavior.
- Preserve `DICT-001` and its complete active values from the canonical dictionary inventory.
- Applicability must route the full scope to `standard-required` and must honestly include conditional, date/input-boundary, dictionary, integration and requiredness dimensions.

## Self-check

In `mapping-consistency-report.md`, record:

- 42/42 atoms present;
- TC ids are exactly `TC-ACPD-001..TC-ACPD-047` with no gaps or extras;
- exact union equality across all four mapping artifacts;
- explicit SEM-001 and SEM-002 closure evidence;
- gaps and dictionary preservation;
- confirmation that prohibited paths were not modified.

Stop after preparing and self-checking inputs. Do not compile the package and do not start a live cycle.
