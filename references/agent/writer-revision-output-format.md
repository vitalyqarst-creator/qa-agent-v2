# Writer Revision Output Format

Runtime reference for `revision_from_findings`. Full response field definitions remain in `references/qa/review-findings-format.md`.

## Inputs

Revision writer must read:

- existing canonical test-case file;
- confirmed scope artifacts;
- structured findings artifact;
- traceability matrix, if reviewer provided it;
- previous writer response, if this is round 2+.

Do not expand scope or add new sources unless reviewer finding explicitly requires a missing confirmed input to be restored.

## Output

Create or update:

- canonical test-case file;
- `round-N-writer-response.md`;
- updated traceability matrix only if writer changes coverage mapping or matrix was an input requiring update;
- `prompt.writer-to-reviewer.round-N.md`;
- `workflow-state.yaml` with `stage_status: ready-for-review`, if all blocking findings are addressed.

## Writer Response Rules

For each finding:

- preserve finding id;
- set resolution status;
- describe concrete change;
- list affected `TC-*`;
- for traceability findings, preserve `affected_traceability_refs` such as `ATOM-*` or `coverage_gap:<id>`.

Do not close a finding by saying it is handled elsewhere without an artifact link or explicit unchanged rationale.

## Hard Stops

Do not route to reviewer if:

- any blocking finding is ignored;
- a traceability finding changed atom split/merge without explaining new mapping;
- revision silently promotes `GAP-*` / `unclear` to covered without new source evidence;
- TC numbering changed but links in matrix/response were not updated.
