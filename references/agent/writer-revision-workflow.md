# Writer Revision Workflow

Use this workflow for `revision_from_findings`.

## Inputs

Required:

- existing canonical test-case file;
- structured reviewer findings;
- review round number;
- confirmed FT package and scope;
- `review_mode` from reviewer;
- traceability matrix when provided.

Do not add new source documents or expand scope during revision unless a separate scope/source task explicitly authorizes it.

## Flow

1. Read every finding and group by `review_mode`, severity, affected `TC-*`, affected `ATOM-*` and `GAP-*`.
2. For traceability findings, fix coverage by `traceability_ref = ATOM-*` or `coverage_gap:<id>`, not by similar source text.
3. For structure findings, fix template, grouping, numbering, field names and required sections without changing the tested meaning.
4. For test-design findings, update or add positive, negative, boundary, equivalence or dependency checks only when source-backed.
5. Keep existing stable `TC-*` ids where possible. If renumbering is unavoidable, update all references.
6. Create `round-N-writer-response.md` with canonical response fields, resolution status and affected refs.
7. Update the canonical test-case file and any required traceability matrix.
8. Create mandatory `.xlsx` duplicate if the writer creates or updates a traceability matrix.
9. Update workflow state, session log, decision log and reviewer prompt.

## Rules

- Do not ignore findings silently.
- Do not mark a finding resolved when only wording changed but coverage is still absent.
- Do not reopen closed findings without new evidence.
- Do not convert prior `gap` or `unclear` items to covered without new observable artifact or confirmed source.
- Do not use revision as a reason to rewrite the entire set from scratch.

If a finding cannot be fixed without new scope or source decisions, record it as unresolved and use the proper next-stage route instead of inventing behavior.
