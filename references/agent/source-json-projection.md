# DOCX JSON Source Projection

`docx-json-projection` is an experimental machine-readable projection built
directly from the authoritative DOCX.

It must not replace the mandatory XHTML extraction source in production until a
multi-scope parity check proves that it preserves:

- source row identity;
- requirement codes;
- table row order;
- physical cell boundaries;
- section context;
- dictionary/list text.

Use JSON projection for comparison, diagnostics and future extraction work:

```powershell
python scripts/build_docx_source_json.py `
  --repo-root <repo-root> `
  --docx <repo-root>\fts\<ft>\source\<main>.docx `
  --output <repo-root>\fts\<ft>\work\source-json-evaluation\<main>.source.json

python scripts/compare_docx_json_to_xhtml_baseline.py `
  --repo-root <repo-root> `
  --spec <source-row-extraction-spec.json> `
  --docx-json <main>.source.json `
  --selected-xhtml <repo-root>\fts\<ft>\source\<main>.xhtml `
  --output <scope>.json-compare.json

python scripts/evaluate_docx_json_projection.py `
  --repo-root <repo-root> `
  --docx <repo-root>\fts\<ft>\source\<main>.docx `
  --selected-xhtml <repo-root>\fts\<ft>\source\<main>.xhtml `
  --spec <scope-a>\source-row-extraction-spec.json `
  --spec <scope-b>\source-row-extraction-spec.json `
  --spec <scope-c>\source-row-extraction-spec.json `
  --output-json <work>\source-json-evaluation\summary.json `
  --output-md <work>\source-json-evaluation\summary.md
```

Comparison treats DOCX JSON table-cell delimiters (`|`) as transport syntax.
They are collapsed to whitespace before XHTML parity matching, because XHTML
bounded row text is already flattened.  The same diagnostic matcher ignores
typographic whitespace noise around parentheses and punctuation.

The DOCX projection reconstructs paragraph numbering from direct paragraph
numbering and paragraph-style numbering.  If a DOCX table cell contains an empty
numbered paragraph followed by the visible requirement text, the numbering label
is carried onto the following paragraph in that same cell.  This is required for
BSR labels that Word renders visually but `python-docx` exposes as a separate
empty paragraph.

These normalizations are diagnostic only; they do not prove source replacement
when row order is unstable, requirement codes are stale/shifted, or table content
is merged/reordered.

Production switch criteria:

- `missing_candidate_count = 0` for at least three materially different real
  scopes;
- `order_preserved = true` for table-heavy scopes;
- `weak_match_count = 0`, including ambiguous matches and requirement-code-only
  matches;
- no stale or shifted requirement codes;
- no duplicated merged-cell text in bounded source rows;
- source assertion review and production iteration still pass without weakening
  reviewer checks.

If these criteria fail, JSON may augment reviewer diagnostics but must not become
the primary machine-readable source.
