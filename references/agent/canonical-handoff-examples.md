# Canonical Reviewer-Loop Handoff Examples

Use these fixtures as minimal examples for completed legacy reviewer-loop states. For new work, prefer `session-based-review-cycle-format.md` and `work/review-cycles/<scope>/cycle-state.yaml`.

## Signed-Off

Fixture: `tests/fixtures/agent-artifacts/canonical-signed-off`

Required properties:

- `workflow-state.yaml` has `stage_status: signed-off` and `next_skill: ft-ui-automation-prep`;
- `latest_artifacts` includes `final_findings`, `final_traceability_matrix`, `final_traceability_matrix_xlsx`, `loop_summary`, and `signed_off_snapshot`;
- `loop-summary.md` has `Reviewer Sign-off Self-check` with `applicability_dimensions_checked: yes`, `test_case_grouping_checked: yes`, `test_case_numbering_checked: yes`, and `source_parity_checked: yes | not-applicable`;
- `prompt.reviewer-to-ui-prep.md` exists and points only to the signed-off baseline.

Validation:

```powershell
python scripts\validate_agent_artifacts.py --root tests\fixtures\agent-artifacts\canonical-signed-off --json --fail-on warning --final-alias-policy strict --reviewer-signoff-policy strict
```

## Round-Cap Reached

Fixture: `tests/fixtures/agent-artifacts/canonical-round-cap`

Required properties:

- `workflow-state.yaml` has `stage_status: round-cap-reached` and `next_skill: none`;
- `latest_artifacts` includes `final_findings`, `final_traceability_matrix`, `final_traceability_matrix_xlsx`, `final_writer_response`, `loop_summary`, and `round_cap_snapshot`;
- `loop-summary.md` has `Final Residual Risk`;
- residual `FINDING-*` and `ATOM-*` refs resolve to linked final artifacts and match their semantic status.

Validation:

```powershell
python scripts\validate_agent_artifacts.py --root tests\fixtures\agent-artifacts\canonical-round-cap --json --fail-on warning --final-alias-policy strict
```
