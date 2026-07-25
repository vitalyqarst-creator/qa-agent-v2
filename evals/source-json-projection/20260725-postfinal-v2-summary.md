# PostFinal-v2 DOCX JSON Projection Evaluation

Date: 2026-07-25

Input:

- DOCX JSON projection built from `PostFinal-v2.docx`.
- XHTML baselines built from existing source-row extraction specs.
- Matching metric: exact/contains text match, delimiter-normalized table-row
  text match, typography-spacing-normalized text match, then
  requirement-code-aware row match.

Result:

| Scope | XHTML candidates | Missing in DOCX JSON | Order preserved | Match summary |
| --- | ---: | ---: | --- | --- |
| `4-3-contact-persons` | 10 | 0 | yes | 1 exact, 7 normalized-exact, 2 requirement-code-exact |
| `application-card-client-addresses` | 44 | 0 | no | 6 exact, 1 contains, 34 normalized-exact, 2 requirement-code-exact, 1 requirement-code-contains |

Conclusion:

DOCX JSON projection is now strong enough as a compact diagnostic/source
comparison artifact for the checked scopes, but it is not yet a safe production
replacement for XHTML.

The initial comparison over-counted misses when DOCX JSON preserved table cell
boundaries as `|` delimiters and XHTML flattened the same row into whitespace.
After delimiter-normalized and typography-spacing-normalized comparison, parity
improved materially.  The checked `client-addresses` scope now has zero missing
XHTML candidates.  However, row-order instability still blocks production
replacement.

Observed positives:

- Much smaller than XHTML on the evaluated FT package.
- Can preserve physical table-row text.
- With numbering reconstruction, preserves BSR labels for the tested
  `contact-persons` rows.
- Delimiter-normalized matching gives exact text parity for many XHTML rows
  whose only difference is DOCX JSON table-cell boundary syntax.
- Empty numbered DOCX paragraphs inside table cells are now carried onto the
  following textual paragraph, so adjacent BSR labels are not silently dropped.
- XHTML whitespace noise around parentheses and punctuation no longer produces
  false missing diagnostics.

Observed blockers for production replacement:

- Row order is not preserved on multiple existing extraction specs.
- Matching relies on requirement-code reconciliation rather than exact bounded
  row equality for many rows.
- `passport` and `employment` were not re-run in this pass because their older
  source-row extraction specs are not present in the current clean-run package.
  They need fresh scope-analysis artifacts before a production replacement
  decision.

Decision:

Keep XHTML as mandatory primary machine-readable extraction source for now.
Use DOCX JSON projection as an experimental comparison/diagnostic artifact until
multi-scope parity reaches zero missing candidates and stable order.
