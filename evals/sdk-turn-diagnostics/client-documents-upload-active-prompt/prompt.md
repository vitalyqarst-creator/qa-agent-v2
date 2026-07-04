# Prompt: Structure Preflight R1

Run `reviewer.structure_preflight` for `ft-2-OF_17` / `client-documents-upload-and-actuality`.

## Instruction Loading

Before review, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file before review decisions. If resolver fails or budget is not pass, do not advance the cycle.

## Inputs

- Canonical test cases: `test-cases/section-31-client-documents-upload-and-actuality.md`
- Test-design dir: `work/test-design/section-31-client-documents-upload-and-actuality/`
- Writer response: `work/review-cycles/client-documents-upload-and-actuality/outputs/writer-r1-response.md`
- Writer session log: `work/review-cycles/client-documents-upload-and-actuality/outputs/writer-session-log.writer-r1.md`
- Writer decision log: `work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.writer-r1.md`
- Scoped validator profile: `work/review-cycles/client-documents-upload-and-actuality/outputs/scoped-validator-profile.writer-r1.json`
- Scope contract: `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-contract.md`
- Source row inventory: `work/stage-handoffs/08-client-documents-upload-and-actuality/source-row-inventory.md`
- Coverage gaps: `work/stage-handoffs/08-client-documents-upload-and-actuality/scope-coverage-gaps.md`

## Review Mode

Use `structure_preflight` only: parseability, canonical TC runtime fields, continuous numbering, required split artifact headings/table columns, no duplicate wrapper headings, and current writer-stage scoped validator evidence.

Do not perform semantic coverage review in this stage.

## Expected Output

- `work/review-cycles/client-documents-upload-and-actuality/outputs/structure-preflight-r1-findings.md`
- `work/review-cycles/client-documents-upload-and-actuality/outputs/reviewer-session-log.structure-preflight-r1.md`
- `work/review-cycles/client-documents-upload-and-actuality/outputs/agent-decision-log.structure-preflight-r1.md`
- Updated `cycle-state.yaml` to `semantic-review-ready` if structure passes, or `structure-preflight-blocked` with a writer remediation prompt if blocked.
