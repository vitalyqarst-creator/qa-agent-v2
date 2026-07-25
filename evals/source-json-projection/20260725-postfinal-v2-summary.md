# PostFinal-v2 DOCX JSON Projection Evaluation

Date: 2026-07-25

Input:

- DOCX JSON projection built from `PostFinal-v2.docx`.
- XHTML baselines built from existing source-row extraction specs.
- Matching metric: exact/contains text match, then requirement-code-aware row match.

Result:

| Scope | XHTML candidates | Missing in DOCX JSON | Order preserved | Match summary |
| --- | ---: | ---: | --- | --- |
| `4-3-contact-persons` | 10 | 1 | yes | 1 exact, 8 requirement-code-exact |
| `application-card-client-addresses` | 44 | 12 | no | 5 exact, 2 contains, 24 requirement-code-exact, 1 requirement-code-contains |
| `application-card-passport-current-and-previous` | 35 | 12 | no | 7 exact, 2 contains, 14 requirement-code-exact |
| `employment-main-work` | 30 | 14 | no | 6 exact, 5 contains, 2 requirement-code-exact, 3 requirement-code-contains |

Conclusion:

DOCX JSON projection is promising as a compact diagnostic/source comparison
artifact, but it is not yet a safe production replacement for XHTML.

Observed positives:

- Much smaller than XHTML on the evaluated FT package.
- Can preserve physical table-row text.
- With numbering reconstruction, preserves BSR labels for the tested
  `contact-persons` rows.

Observed blockers for production replacement:

- Missing candidates remain on larger table-heavy scopes.
- Row order is not preserved on multiple existing extraction specs.
- Matching relies on requirement-code reconciliation rather than exact bounded
  row equality for many rows.

Decision:

Keep XHTML as mandatory primary machine-readable extraction source for now.
Use DOCX JSON projection as an experimental comparison/diagnostic artifact until
multi-scope parity reaches zero missing candidates and stable order.
