# Incremental Update Iteration

This is the conditional `ft-test-case-iteration` mode for updating a signed-off
suite between two FT versions. It is deliberately absent from normal
`iteration.full_loop` instruction context.

## Entrypoint

```powershell
python scripts/run_incremental_update_iteration.py --config <config.json>
```

Implementation lives in `test_case_agent/incremental_update/`. Default
`release_mode` is `shadow`; publishing is permitted only after update review,
full-suite gates and compare-and-swap verification of the old canonical hash.

## Required inputs

- old and new DOCX, XHTML and PDF main FT files;
- old signed-off canonical suite, traceability matrix and source assertions;
- version IDs and the target canonical path;
- old/new support and mockup inventories when applicable.

DOCX remains source of truth, XHTML is mandatory for both normalized
projections, and PDF is a structural/code parity source. Missing new XHTML is a
scope-local `blocked-input`; do not infer requirements from PDF or mockups.

## Pipeline

1. Normalize stable entities by section path, requirement code,
   table/row/field identity, atomic statement, structural/semantic hash and
   source locator.
2. Classify `unchanged`, `editorial-only`, `moved`, `renumbered`,
   `modified-behavior`, `added`, `removed`, `dictionary-changed`,
   `support-changed`, `mockup-changed` or `ambiguous-match`. Movement and code
   renumbering alone are not behavioral changes.
3. Expand impact through assertion, obligation, test-case, dictionary and shared
   dependency links. Unknown impact expands review and never silently reuses a
   case.
4. Plan `reuse-byte-identical`, `modify`, `split`, `merge`, `retire`, `replace`
   or `new`. Preserve a `TC-ID` when intent is preserved; record explicit old/new
   mappings for split/merge/replace.
5. Give a writer only changed statements, affected cases, local dependencies,
   dictionaries and the update plan. Unaffected byte ranges are copied by the
   runner. A no-op update performs zero writer calls.
6. Independently review classification, impact, changed cases, change boundary,
   stale source references and unchanged hashes. Then run ordinary full-suite
   production gates and traceability checks.

Ambiguous matches, missing writer output for affected cases, stale old-version
references, changed supposedly unchanged regions, or failed gates prevent
publication. A failed shadow run never overwrites the canonical suite.

## Required artifacts

Each immutable run emits:

- `ft-version-diff.json` and `ft-version-diff.md`;
- `change-classification.json`;
- `change-impact-matrix.md`;
- `update-plan.md`;
- `tc-reuse-manifest.json`;
- `unchanged-region-manifest.json`;
- `test-case-changelog.md`;
- `update-review-result.json`;
- `release-manifest.json`;
- before-writer, after-writer and signed-off snapshots when reached.

`test-cases/` keeps one current canonical filename. Version history belongs to
immutable snapshots plus the release manifest, not competing `scope-v2.md` and
`scope-v3.md` files.
