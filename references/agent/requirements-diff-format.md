# Requirements Diff Format

Requirements Diff is a machine-checkable artifact that compares two Requirements Registry JSONL files for two FT source versions.

It does not perform impact analysis, update test cases, or change writer/reviewer workflow.

## Required Files

For `<old-version>` and `<new-version>`, the builder writes:

- `requirements-diff.<old-version>-to-<new-version>.json`
- `requirements-diff-summary.<old-version>-to-<new-version>.json`

Recommended package location:

```text
fts/<ft-slug>/requirements/requirements-diff.<old-version>-to-<new-version>.json
fts/<ft-slug>/requirements/requirements-diff-summary.<old-version>-to-<new-version>.json
```

## Diff Entry Shape

```json
{
  "change_id": "CHG-000001",
  "change_type": "behavior_modified",
  "old_req_uid": "REQ-AUTOFIN-OLD",
  "new_req_uid": "REQ-AUTOFIN-NEW",
  "old_atom_id": "ATOM-000001",
  "new_atom_id": "ATOM-000001",
  "old_source_req_id": "BSR 115",
  "new_source_req_id": "BSR 115",
  "old_requirement_type": "requiredness",
  "new_requirement_type": "requiredness",
  "old_status": "active",
  "new_status": "active",
  "old_normalized_text": "Адрес регистрации обязателен.",
  "new_normalized_text": "Адрес регистрации обязателен для клиента.",
  "old_semantic_fingerprint": "requiredness|||адрес регистрации обязателен.",
  "new_semantic_fingerprint": "requiredness|||адрес регистрации обязателен для клиента.",
  "old_text_hash": "sha256:...",
  "new_text_hash": "sha256:...",
  "old_source_anchors": [],
  "new_source_anchors": [],
  "similarity_score": 0.86,
  "confidence": "low",
  "requires_manual_review": true,
  "reasons": ["same req_uid but text_hash changed"],
  "warnings": []
}
```

## Change Types

Allowed `change_type` values:

- `unchanged`
- `text_changed_no_behavior_change`
- `behavior_modified`
- `added`
- `deleted`
- `moved`
- `renumbered`
- `split`
- `merged`
- `source_anchor_changed`
- `unclear_match`

Stage 4 does not automatically resolve whether a modified requirement changes downstream test coverage. That belongs to a later impact-analysis step.

## Matching Rules

Matching is deterministic and conservative:

1. Exact `req_uid` match.
   - Same `req_uid` and same `text_hash` -> `unchanged`.
   - Same `req_uid`, same text, changed source anchor -> `source_anchor_changed`.
   - Same `req_uid`, changed text, same type/status/source id, and high similarity -> `text_changed_no_behavior_change`.
   - Otherwise changed text under the same `req_uid` -> `behavior_modified`.

2. Exact `semantic_fingerprint` match.
   - Same fingerprint with changed `source_req_id` -> `renumbered`.
   - Same fingerprint and text with changed anchor -> `source_anchor_changed`.
   - Same fingerprint with changed `req_uid` -> `renumbered`.

3. Exact `source_req_id` match.
   - Same source id with changed `requirement_type` -> `behavior_modified` and manual review.
   - Same source id with changed text -> `behavior_modified` or `text_changed_no_behavior_change`, depending on similarity.

4. Similarity fallback.
   - Similarity is deterministic and uses token overlap plus `SequenceMatcher` ratio.
   - `similarity_score >= 0.92` with same type/status -> `text_changed_no_behavior_change`.
   - `similarity_score >= 0.75` -> `behavior_modified` with manual review.
   - Lower similarity is not linked automatically.

5. Added/deleted.
   - Old entry without match -> `deleted`.
   - New entry without match -> `added`.

6. Conservative split/merge detection.
   - One old entry with similarity `>= 0.60` to several new entries -> `split`, manual review.
   - Several old entries with similarity `>= 0.60` to one new entry -> `merged`, manual review.
   - Stage 4 does not automatically treat split/merged candidates as unchanged.

## Risk Handling

If either side has `status` in `unclear`, `gap`, or `source_only`, confidence must not exceed `medium`.

If a change touches tracked deletion, hidden text, comment source, or aggregate-derived source, `requires_manual_review` must be `true`.

## Summary Shape

```json
{
  "old_registry_path": "fts/AutoFin/requirements/requirements.autofin-prefinal-v1.jsonl",
  "new_registry_path": "fts/AutoFin/requirements/requirements.autofin-final-v1.jsonl",
  "old_source_version": "autofin-prefinal-v1",
  "new_source_version": "autofin-final-v1",
  "diff_status": "pass-with-warnings",
  "old_entries_total": 100,
  "new_entries_total": 100,
  "old_diff_eligible_entries": 20,
  "new_diff_eligible_entries": 22,
  "old_diff_excluded_entries": 80,
  "new_diff_excluded_entries": 78,
  "old_duplicate_req_uid_diff_eligible_count": 0,
  "new_duplicate_req_uid_diff_eligible_count": 0,
  "entries_total": 5,
  "unchanged": 1,
  "text_changed_no_behavior_change": 1,
  "behavior_modified": 1,
  "added": 1,
  "deleted": 1,
  "moved": 0,
  "renumbered": 0,
  "split": 0,
  "merged": 0,
  "source_anchor_changed": 0,
  "unclear_match": 0,
  "requires_manual_review_count": 1,
  "warnings": [],
  "blocking_reasons": []
}
```

Allowed `diff_status` values:

- `pass`: diff was built without warnings or manual-review flags.
- `pass-with-warnings`: diff was built, but warnings or manual-review flags are present.
- `blocked`: diff entries were not produced because inputs are missing, blocked, invalid, or duplicate-unsafe.

## Blocking Rules

Stage 4 must block when:

- old registry file is missing;
- new registry file is missing;
- old summary has `registry_status=blocked`;
- new summary has `registry_status=blocked`;
- registry JSONL cannot be parsed;
- either registry contains duplicate `entry_uid`;
- either registry contains duplicate `req_uid` among `diff_eligible` entries and the caller did not pass `--allow-duplicate-req-uid`.

Diff uses `diff_eligible=true` registry entries by default. If an older registry entry has no `diff_eligible` field, Stage 4 uses the backward-compatible rule `status != source_only`.

`source_only` duplicates do not block Requirements Diff because they are excluded from diff by default. They remain available in the registry for audit.

Duplicate `req_uid` among diff-eligible entries can be allowed only through an explicit caller flag after manual review. Allowing duplicates does not make matching semantically safe; it only permits diff artifact creation with warnings.

Duplicate `entry_uid` always blocks because row/source identity is not unique.

## CLI

```bash
python scripts/build_requirements_diff.py \
  --old-registry fts/AutoFin/requirements/requirements.autofin-prefinal-v1.jsonl \
  --new-registry fts/AutoFin/requirements/requirements.autofin-final-v1.jsonl \
  --out-dir fts/AutoFin/requirements
```

Optional inputs:

```bash
--old-summary fts/AutoFin/requirements/requirements-summary.autofin-prefinal-v1.json
--new-summary fts/AutoFin/requirements/requirements-summary.autofin-final-v1.json
--allow-duplicate-req-uid
```

## Stage 4 Limits

- No test-case impact analysis.
- No automatic test-case update.
- No writer/reviewer workflow changes.
- No creation of new test cases.
- No LLM semantic equivalence claim; similarity fallback is deterministic and conservative.
