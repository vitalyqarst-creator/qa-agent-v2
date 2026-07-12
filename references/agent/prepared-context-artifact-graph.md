# Prepared Context And Artifact Graph

## Purpose

The immutable prepared package and the stage `stage-input.json` remain the canonical input contracts. `artifact-graph.json` is a runner-derived, digest-bound lifecycle view; it is not a second source of requirement truth.

## Lifecycle

Each graph node records path, kind, producer, consumer and one lifecycle value:

- `source` — source-backed evidence;
- `prepared` — compiler or runner materialized input;
- `generated` — unsigned stage/runner output;
- `reviewed` — deterministic or semantic review output.

The graph also records the stage input digest, context profile, sandbox, allowed write roots, forbidden production roots and fallback policy. The stage may consume only artifacts registered by its canonical `stage-input.json`.

## Context Profiles

The runner derives exactly one profile from package execution metadata:

- `simple-field-property`;
- `character-restriction-calibration`;
- `numeric-date-boundary`;
- `integration-persistence`;
- `conditional-state`;
- `general-standard`.

The profile selects a small embedded rule card. It does not remove or replace upstream QA policy: source selection, scope analysis and compiler validation must apply that policy before package creation.

## Writer Modes

- `structured` is the default for prepared fast and standard packages. The writer is read-only, has command budget zero, returns Markdown in a JSON contract, and the runner materializes the draft.
- `assisted` is an explicit standard-only fallback for a new immutable cycle. It may read only manifest-listed instructions and use one targeted registered-source fallback for a named unresolved OBL/ATOM.
- A failed structured attempt never switches mode or resumes inside the same cycle.

## Deterministic Gate Bundle

Before semantic review, the runner owns:

- structure and seed gates;
- obligation/ATOM traceability gate;
- semantic-overlap diagnostic;
- unique-title check;
- constraint-gap preservation check;
- UI-calibration marker check;
- evidence-access/contamination gate.

Reviewer input contains the gate summaries, immutable draft, obligation package, selected evidence and calibration lifecycle. Reviewer does not repeat repository discovery.

## UI Calibration Lifecycle

A testable obligation with UI-calibration constraint gaps produces an entry:

```text
awaiting-ui-calibration
  -> evidence-collected
  -> oracle-resolved
  -> reviewer-signed-off
  -> regression-ready
```

Until evidence and re-review exist, `regression_ready` remains false and the FT-first baseline is unchanged.

## Performance Evidence

The dispatcher report records stage duration/tokens plus context bytes, instruction count, command/file-change counts, test-case and obligation counts, uncached tokens per obligation and commands per test case. Cached and uncached inputs must remain separate.
