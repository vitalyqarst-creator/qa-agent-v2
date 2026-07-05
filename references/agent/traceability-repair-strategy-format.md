# Traceability Repair Strategy Format

Stage 7E produces a read-only strategy/report from Stage 7D traceability mismatch diagnostics. It must not edit canonical test-case files, apply patches, run `--apply`, create new test cases, or change writer/reviewer workflow.

## Inputs

- `traceability-mismatch-diagnostics.<old>-to-<new>.json`
- one or more `writer-dry-run-proposal-<package-id>.json`
- `test-case-update-plan.<old>-to-<new>.json`
- `impact-report.<old>-to-<new>.json`
- `requirements-diff.<old>-to-<new>.json`
- old and new requirements registry JSONL files

The strategy builder uses already-produced artifacts only. It does not need to read canonical files under `fts/<ft-slug>/test-cases/`.

## Output Files

- `traceability-repair-strategy.<old>-to-<new>.json`
- `traceability-repair-strategy.<old>-to-<new>.md`

## Report Fields

The JSON root is an object with:

- `strategy_status`: `pass`, `pass-with-warnings`, or `blocked`.
- `recommended_strategy`: `no_auto_repair`, `source_req_id_fallback`, `req_uid_backfill_proposal`, `manual_review_only`, or `mixed`.
- `automatic_replacement_allowed`: always `false` when generated `REQ-*` old refs are absent from current TC traceability.
- `backfill_recommended`: `true` when at least one repair item is eligible for preview-only req_uid backfill.
- `source_req_id_fallback_recommended`: `true` when legacy `source_req_id` refs support the mismatch relation and should be used as explainability/fallback evidence.
- `affected_packages`: package ids covered by repair items.
- `affected_test_cases`: TC ids covered by repair items.
- `repair_items`: per-mismatch repair recommendations.
- `summary`: counts for repair items, confidence, allowed next actions, warnings, and blockers.
- `recommendations`: human-readable next-step guidance.
- `warnings`
- `blocking_reasons`

## Repair Item Fields

Each `repair_items[]` entry contains:

- `repair_item_id`
- `package_id`
- `test_case_id`
- `file_path`
- `mismatch_type`
- `current_traceability_line`
- `legacy_refs_present`
- `missing_req_uids`
- `candidate_req_uids_to_backfill`
- `source_req_ids_supporting_candidate`
- `confidence`: `high`, `medium`, or `low`.
- `requires_manual_validation`: always `true` for Stage 7E repair items.
- `allowed_next_action`: `create_backfill_proposal`, `use_source_req_id_fallback`, `manual_review_only`, or `no_action`.
- `rationale`
- `warnings`
- `plan_item_id`
- `impact_id`
- `change_id`

## Strategy Rules

- Automatic traceability replacement is not allowed when update plan old refs contain generated `REQ-*` ids that are absent from the TC traceability line.
- `candidate_req_uids_to_backfill` can be populated only when the mismatch has a concrete plan item, impact entry, and diff entry; the related writer proposal is file-bound and lists the TC; and a legacy `source_req_id` in the current traceability line supports the relation.
- Req_uid backfill is only a preview-only next step. Stage 7E never writes canonical TC files.
- Low-confidence mappings must remain `manual_review_only`.
- `source_req_id_fallback_recommended=true` means fallback is useful for explainability and planning. It is not permission to silently rewrite TC traceability.

## CLI

```bash
python scripts/build_traceability_repair_strategy.py \
  --diagnostics fts/AutoFin/work/.../traceability-mismatch-diagnostics.autofin-prefinal-to-autofin-final.json \
  --proposal fts/AutoFin/work/.../writer-dry-run-proposal-WPKG-000002.json \
  --proposal fts/AutoFin/work/.../writer-dry-run-proposal-WPKG-000003.json \
  --update-plan fts/AutoFin/work/.../test-case-update-plan.autofin-prefinal-to-autofin-final.json \
  --impact-report fts/AutoFin/work/.../impact-report.autofin-prefinal-to-autofin-final.json \
  --requirements-diff fts/AutoFin/work/.../requirements-diff.autofin-prefinal-to-autofin-final.json \
  --old-registry fts/AutoFin/work/.../requirements.autofin-prefinal.jsonl \
  --new-registry fts/AutoFin/work/.../requirements.autofin-final.jsonl \
  --out-dir fts/AutoFin/work/...
```

## Markdown

The Markdown report must include:

- summary counts;
- recommendations;
- repair item details;
- safety statements that canonical test-case files are not modified, patches are not applied, and `--apply` is not used.
