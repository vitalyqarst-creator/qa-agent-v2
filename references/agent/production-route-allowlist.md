# Production Route Allowlist

This repository profile is optimized for operational FT test-case work, not for
benchmarking or route research.

## Allowed by default

- `ft-source-locator` for selecting an FT package and primary sources.
- `ft-scope-analyzer` for source-first scope boundaries, source rows, coverage
  gaps, clarification requests, dictionaries, mockup context, and production
  input materialization.
- `ft-test-case-writer` for a controlled FT-first baseline when the user needs
  test cases quickly and unresolved UI/data issues are represented as explicit
  statuses.
- `ft-test-case-reviewer` for manual-quality review of existing or newly written
  cases.
- `ft-test-case-iteration` only through `ft-agent run` with schema v2 and
  `writer_mode=model-runtime-prose`.
- `ft-ui-automation-prep` after baseline/sign-off when a real UI stand is
  available.

## Forbidden in this production profile

The agent must not start, suggest, or recover into these routes:

- full-process observation;
- benchmark or shadow-benchmark execution;
- overnight controller orchestration;
- semantic-design bridge materialization;
- semantic-design sharding;
- standard-production wrapper routes that invoke a semantic bridge;
- legacy deterministic-only writer/reviewer compatibility routes;
- old failed attempts, benchmark history, or previous generated test cases as
  writer/reviewer input.

If any of these appears necessary, the correct production behavior is to stop
with an explicit blocker and ask for a separate development/qualification
environment.

## Why this exists

The removed/default-disabled routes are useful for agent development, but they
create long repair loops and can block delivery of test cases on infrastructure
or artifact-contract details. Operational production work should prioritize:

1. source-bound scope extraction;
2. clear coverage gaps;
3. a controlled baseline with explicit statuses;
4. independent/manual review;
5. UI calibration as a separate phase.

## Runtime enforcement

Development-only scripts fail closed unless `FT_AGENT_ENABLE_DEV_ROUTES=1` is set
explicitly in a separate qualification repository. This opt-in must not be used
inside normal production test-case work.
