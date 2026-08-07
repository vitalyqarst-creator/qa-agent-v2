# Practical Review Finalization And Export

This conditional reference applies only after an independent practical
`matrix_review` or `tc_review` task has returned. It is controller-facing: a
reviewer creates only review evidence and must not update controller state.

## Controller ownership guard

The launch receipt produced by `practical_review_preflight.py` records SHA-256
hashes for the package summary and each active `workflow-state.yaml`. Before the
controller changes aliases, summary or workflow state, it must verify the
reviewer output:

```text
python scripts/practical_review_finalization_guard.py --repo-root . --ft-package-root <FT package root> --summary <practical-stage-summary.md> --scope-id <two-digit scope id> --review-mode <matrix_review|tc_review> --launch-receipt <review-launch-preflight.json> --review-artifact <review artifact> --independence-artifact <review-independence.md> --output <review-finalization.json>
```

The guard requires all of the following:

- original launch receipt has `allowed: true` and matches the selected scope/mode;
- controller-owned summary and active workflow files have not changed during
  review;
- review artifact has a canonical verdict for the selected mode;
- independence artifact records a durable separate Codex task/thread ID and
  `reviewer_execution_surface` equal to `codex-task` or `codex-thread`.

Only a packet with `allowed: true` may be followed by the controller's one
deterministic update of `workflow-state.yaml` and `practical-stage-summary.md`.
A blocked packet is a process-integrity failure: restore or repair controller
state, then rerun launch preflight. It is not evidence that test cases need a
new writer revision.

## Portable accepted baseline

When accepted package artifacts are ignored by Git, ordinary `git commit` does
not preserve them. The controller must either explicitly stage exactly those
files with `git add -f` or create a portable evidence bundle:

```text
python scripts/export_practical_baseline.py --ft-package-root <FT package root> --scope-id <two-digit scope id> --summary <practical-stage-summary.md> --output <destination>.zip
```

The exporter permits only a scope that records accepted independent TC review.
The ZIP contains a SHA-256 manifest plus exactly the canonical TC file, final
findings, independence receipt, active workflow state and practical summary.
It never modifies or stages package artifacts.
