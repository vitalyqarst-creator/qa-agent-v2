# Canonical Handoff Evals

These evals prove that the minimal completed reviewer-loop examples satisfy strict runtime handoff gates.

## Eval: signed-off handoff

Command:

```powershell
python scripts\validate_agent_artifacts.py --root tests\fixtures\agent-artifacts\canonical-signed-off --json --fail-on warning --final-alias-policy strict --reviewer-signoff-policy strict
```

Expected result:

- exit code `0`;
- no `workflow-state-missing-final-artifact-aliases`;
- no `reviewer-signoff-self-check-missing`;
- no `reviewer-signoff-self-check-invalid`;
- no `workflow-state-ui-prep-without-signed-off`.

## Eval: round-cap handoff

Command:

```powershell
python scripts\validate_agent_artifacts.py --root tests\fixtures\agent-artifacts\canonical-round-cap --json --fail-on warning --final-alias-policy strict
```

Expected result:

- exit code `0`;
- no `workflow-state-missing-final-artifact-aliases`;
- no `workflow-state-round-cap-with-next-skill`;
- no `loop-summary-round-cap-missing-residual-risk`;
- no `loop-summary-round-cap-residual-risk-unknown-refs`;
- no `loop-summary-round-cap-residual-risk-semantic-mismatch`.
