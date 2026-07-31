# Lean Production Workflow

This document is retained only as a compatibility reference for historical
artifacts. It is not an active production route.

## Production profile status

The production agent profile must not route user work through the old standard
bridge, benchmark, full-process observation, sharding, overnight controller, or
legacy deterministic-only iteration paths.

Use the active allowlist instead:

- canonical policy: `references/agent/production-route-allowlist.md`;
- source/scope preparation: `ft-source-locator` and `ft-scope-analyzer`;
- manual FT-first baseline: `ft-test-case-writer` followed by
  `ft-test-case-reviewer`;
- source-qualified runner path: `ft-test-case-iteration` through `ft-agent run`
  with schema v2 and `writer_mode: model-runtime-prose`;
- UI evidence/calibration: `ft-ui-automation-prep`.

## Disabled historical entrypoints

The following entrypoints are development/qualification-only and must not be
suggested or launched for normal FT test-case production:

- `scripts/run_standard_production_iteration.py`;
- `scripts/run_standard_scope_bridge.py`;
- `scripts/start_full_process_observation.py`;
- `scripts/run_semantic_design_qualification.py`.

They fail closed unless `FT_AGENT_ENABLE_DEV_ROUTES=1` is set explicitly. Setting
that environment variable is not allowed during production test-case writing.

## Replacement rule

If an older artifact or prompt references this workflow, do not continue through
the bridge. Re-route to the source-first allowlist. If the required source-first
inputs are missing, stop with an honest blocker and name the missing inputs.
