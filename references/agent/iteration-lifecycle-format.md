# Iteration Lifecycle Format

This reference is compatibility-only for historical pre-SDK artifacts.

New writer/reviewer orchestration must use:

- `references/agent/session-based-review-cycle-format.md`
- `references/agent/codex-sdk-orchestration-format.md`
- `references/qa/test-case-versioning-policy.md`

## Status

The old in-session full-loop lifecycle is deprecated.

Do not use this file as the source of truth for new runs. Do not create new artifacts under `work/review-loops/` and do not require `loop-summary.md` for new session-based cycles.

## Compatibility Scope

This file may be used only when auditing or validating historical FT packages that already contain legacy reviewer-loop artifacts.

For new cycles:

- process status lives in `work/review-cycles/<scope-slug>/cycle-state.yaml`;
- SDK session metadata lives in `work/review-cycles/<scope-slug>/codex-session-map.yaml`;
- prompts live in `work/review-cycles/<scope-slug>/prompts/`;
- stage outputs live in `work/review-cycles/<scope-slug>/outputs/`;
- snapshots live in `work/review-cycles/<scope-slug>/versions/<snapshot-id>/`;
- terminal statuses are `signed-off`, `round-cap-reached`, `blocked-input` or another non-runnable status defined by `session-based-review-cycle-format.md`.
- все новые или обновленные строки traceability matrix имеют стабильный `atom_id`;
- все закрытые traceability findings проверены по `traceability_ref` / `atom_id`;
- traceability closure must be explicit before sign-off;
- unresolved coverage is listed as remaining `gap` refs as `ATOM-*` or `coverage_gap:<short-id>`;
- terminal handoff uses final aliases in `latest_artifacts`: `final_findings`, `final_traceability_matrix`, `final_traceability_matrix_xlsx`, `final_writer_response`, and terminal snapshot alias.

## Migration Rule

If a legacy package has only old artifacts, do not silently rewrite history. Treat `work/review-loops/` as read-only evidence, create a new `work/review-cycles/<scope-slug>/` state for continued work, and preserve canonical test cases in `test-cases/<section-id>-<scope-slug>.md`.
