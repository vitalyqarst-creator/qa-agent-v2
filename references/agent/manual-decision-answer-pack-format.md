# Manual Decision Answer Pack Format

Stage 9D.7a exports a reviewer-friendly answer pack and can import a filled CSV back into the Stage 9D.7 reviewer answers JSON format.

It is not Stage 9E. It does not validate business meaning, does not create revised drafts, and does not create or edit canonical test cases.

## Inputs

- `manual-decision-matrix-<package_id>.json`
- `manual-decision-answer-template-<package_id>.json`
- optional filled CSV: `manual-decision-reviewer-answer-pack-<package_id>.filled.csv`

## Export Outputs

- `manual-decision-reviewer-answer-pack-<package_id>.md`
- `manual-decision-reviewer-answer-pack-<package_id>.csv`
- `manual-decision-reviewer-answer-pack-<package_id>.schema.json`

XLSX is optional and not required. If generated, it should use `openpyxl`; LibreOffice must not be required.

## Import Outputs

When filled CSV is provided and has no mechanical blockers:

- `manual-decision-reviewer-answers-<package_id>.json`
- `manual-decision-reviewer-answers-<package_id>.import-report.json`
- `manual-decision-reviewer-answers-<package_id>.import-report.md`

If the filled CSV has blockers, only the import report is written and answers JSON is not created.

If filled CSV exists but has no selected options, import writes an empty answers JSON and returns `pass-with-warnings`. This keeps the operation machine-checkable without inventing answers.

## CSV Columns

CSV columns must appear exactly in this order:

```text
row_id
cluster_id
priority
reviewer_role
affected_drafts
affected_requirements
decision_required
evidence_summary
allowed_option_ids
allowed_option_labels
requires_source_evidence
requires_existing_tc_review
required_fields
selected_option_id
reviewer_rationale
source_evidence
existing_tc_review_notes
business_clarification
no_new_tc_rationale
defer_reason
split_guidance
answered_by
answered_at_utc
```

Fields before `selected_option_id` are read-only for the reviewer. Editable fields must be empty in exported CSV. Multi-value fields use `; ` as the separator.

## Export Rules

- Do not preselect options.
- Do not add hidden defaults.
- Preserve row ids and cluster ids exactly.
- Preserve allowed option ids per row.
- Include safety rules in Markdown and schema.
- Keep `canonical_write_allowed=false`.
- Keep `manual_review_required=true`.
- Keep `stage_9e_authorized=false`.

## Import Rules

Import from filled CSV should:

- preserve row order;
- reject unknown row ids;
- reject duplicate row ids;
- reject selected options not allowed for the row;
- reject rows missing required identity fields (`row_id`, `cluster_id`);
- trim editable fields;
- split `source_evidence` and `existing_tc_review_notes` by `;`;
- produce answers JSON only from rows with `selected_option_id`;
- avoid inventing missing answers;
- leave business/safety validation to Stage 9D.7.

Import never validates Stage 9E readiness and never authorizes canonical writes.

## Answers JSON Shape

The imported JSON must match Stage 9D.7:

- `package_id`
- `source_matrix_path`
- `answer_schema_version`
- `answers`
- `answered_by`
- `answered_at_utc`
- `review_notes`

Each answer:

- `row_id`
- `cluster_id`
- `selected_option_id`
- `reviewer_rationale`
- `source_evidence`
- `existing_tc_review_notes`
- `business_clarification`
- `no_new_tc_rationale`
- `defer_reason`
- `split_guidance`
- `answered_by`
- `answered_at_utc`

## Safety

Every exported/imported artifact must communicate:

- This artifact does not create or edit canonical test cases.
- Existing TC may be used only as coverage evidence.
- Stage 9E requires separate validation.
- `canonical_write_allowed=false`.
- `manual_review_required=true`.
- `stage_9e_authorized=false`.
