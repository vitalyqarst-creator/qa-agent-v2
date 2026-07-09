# Scope Execution Options

## Recommended Path

- next_skill: `ft-test-case-iteration`
- runner: `scripts/run_cycle.ps1`
- state: `fts/AutoFin/work/review-cycles/iteration-smoke-widget-selection-types/cycle-state.yaml`

## Reason

The user requested a штатный writer/reviewer iteration workflow with max two revision loops. The scope is already selected and has the required handoff artifacts for a session-based cycle.

## Fallback

If the SDK runner is unavailable, do not write final test cases manually. Create or update `fts/AutoFin/work/iteration-smoke/iteration-process-report.md` with the exact blocking reason and stop before final TC generation.
