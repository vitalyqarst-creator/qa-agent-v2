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
- for a practical bounded TC revision:
  `work/practical/<scope>/tc-revision-summary.md`;
- updated traceability matrix only if writer changes coverage mapping or matrix was an input requiring update;
- `prompt.writer-to-reviewer.round-N.md`;
- `workflow-state.yaml` with `stage_status: ready-for-review`, if all blocking findings are addressed and the next stage is the final independent TC review.

## Practical Status Assertions

For a bounded revision under `practical_v0_8`, the revision summary must contain
the following exact section and table for every affected case:

```md
## Status Assertions

| tc_id | status_after_revision |
| --- | --- |
| TC-EXAMPLE-001 | needs-test-data |
```

`status_after_revision` must be the exact current status in the canonical test
case, not a planned status. A case may be `ready` only when it has no pending
confirmation and no unresolved fixture, test-data, access or observability
dependency. `Требуется подтверждение: Не требуется; ...` is valid only when the
suffix records already available evidence and does not introduce an unresolved
input. The writer must route this revision to a final independent
full-scope TC review; writer cannot sign off, release or start UI preparation.

## Contract-only Status Repair

Before the final independent review, one narrow repair is allowed only to resolve
a validator-detected inconsistency in execution status or confirmation metadata.
It does not create another writer round only when it changes no coverage, test
design, steps, expected results, traceability or source interpretation.

Record it in the same revision summary:

```md
## Contract-only Repair

| field | value |
| --- | --- |
| repair_type | `contract_only_status_repair` |
| semantic_change | `no` |
| affected_tc_ids | `TC-EXAMPLE-001` |
| evidence | `<validator finding id or exact inconsistency>` |
```

Refresh `## Status Assertions` and `practical-stage-summary.md`, including its
exact Code Version Gate commit, before the final review handoff.
For this repair, the package summary's `Current stage actions` must describe
only the contract repair; describe the earlier bounded writer revision under
`Prior state context`. Its canonical `validator_*_count` values must come from
the same latest validator result; do not leave conflicting duplicate counts in
another summary table.

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
- a `ready` case still contains a pending confirmation, unverified fixture,
  missing test data, access path or observable oracle;
- `tc-revision-summary.md` is missing required `## Status Assertions` or its
  declared statuses disagree with canonical cases.
