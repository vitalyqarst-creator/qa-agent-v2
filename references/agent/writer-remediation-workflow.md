# Writer Remediation Workflow

Use this reference when validator, Writer Quality Gate or style review finds blocking issues.

## Style Remediation

For wording and formatting findings:

- use `test-case-format.md` and `test-case-style-examples.md`;
- preserve test meaning and traceability;
- do not change coverage or source interpretation just to improve wording;
- rerun the validator or focused test that detected the issue.

## Validator And Quality-Gate Remediation

When validator or Writer Quality Gate fails, load the deep references from `writer_validator_failure_deep` and fix the affected package before reviewer handoff.

Common blocking classes:

- missing or invalid Test Design Decision Table;
- metadata rows linked to `TC-*`;
- gap without real `GAP-*`;
- executable behavior hidden behind a gap;
- overbroad or false gap;
- value-type behavior converted into generic TC;
- placeholder validation data;
- dependency setup placeholder;
- generic rule oracle;
- source-dump or extraction-artifact oracle;
- nondeterministic alternative expected result;
- missing mask, numeric, dictionary or date-window coverage;
- negative transition without a valid fixture;
- linked TC that does not actually cover the applicability dimension.

Do not route to reviewer until the failed rule is rerun and passes, or the residual risk is explicitly recorded as a blocker.

## Process Contamination

If the writer process is contaminated by command limit failure, partial one-shot write, distorted source evidence or failed artifact strategy, do not treat the draft as ready. Rebuild the affected artifact through the approved helper or return to the proper prior stage.
