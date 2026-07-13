# Prompt: Prepared Dictionary Projection Remediation

## Goal

Устранить agent-layer причину F-001 без изменения FT-first baseline и без повторного запуска terminal V1 cycle.

## Skill Route

- Начать с `agent-architecture-auditor`, потому что проблема находится на границе compiler package -> structured writer seed/prompt -> deterministic draft gates.
- После bounded design decision реализовать изменение в runner/compiler/tests; writer/reviewer domain work не выполнять в основной сессии.

## Required Inputs

- `work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/live-result.v1.json`
- `work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/performance-analysis.v1.md`
- `work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/prepared-input/visual-assessment-medium-scope-benchmark-v1/source-evidence.md`
- `work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/attempts/writer-r1/attempt-001/stage-output/draft.md`
- `work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/attempts/writer-r1/attempt-001/runner-output/quality-gate-bundle.json`
- `work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/attempts/writer-r1/attempt-001/runner-output/calibration-lifecycle.json`
- `work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/attempts/reviewer-r1/attempt-001/runner-output/findings.md`
- `evals/candidates/2026-07-13-prepared-dictionary-values-not-materialized-visual-assessment.md`

## Required Work

1. Prove where full DICT leaf values are lost: seed, prompt instructions, structured writer output, materialization or deterministic gate.
2. Add a deterministic contract that rejects a draft claiming full dictionary/value-control coverage when required active leaf values are absent.
3. Prefer runner-owned projection/materialization over asking the LLM to repeat large dictionaries when this can preserve semantics more cheaply.
4. Audit why `covered_with_ui_calibration` produced candidate markers in the draft but zero lifecycle items without `constraint_gap_ids`.
5. Add focused positive/negative tests and run relevant regression suites.
6. Do not launch live. Prepare a new immutable package/cycle proposal only after the fix is green.

## Guardrails

- Do not edit V1 package, attempts, draft or findings.
- Do not modify `test-cases/section-18-visual-assessment-criteria.md` or create the absent promotion target.
- Do not treat prior test cases as requirement evidence.
- Preserve full current-source `DICT-001`; do not solve token cost by truncation.
- Keep V1 authorization consumed and terminal.

## Stop Conditions

- Stop if deterministic completeness cannot be defined from structured package data without domain guesses.
- Stop before any live dispatcher.
