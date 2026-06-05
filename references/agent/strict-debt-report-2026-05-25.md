# Strict Validator Debt Report - 2026-05-25

## Scope

This report classifies warnings produced by the root artifact validator when all strict policies are enabled:

```powershell
python scripts\validate_agent_artifacts.py --root . --json --source-quality-policy strict --findings-policy strict --writer-response-policy strict --test-case-policy strict
```

Compatible mode remains clean: 0 errors, 0 warnings. Current compatible mode reports 65 info after adding reviewer sign-off migration checks; these are non-blocking legacy notes.

Strict mode currently reports 15 warnings. These warnings are legacy debt, not new failures introduced by the test-case reference-integrity layer.

## Summary

| Category | Warning count | Main cause | Recommended handling |
| --- | ---: | --- | --- |
| source-quality | 4 | Active DOCX extraction has oversized or weakly titled sections. | Keep documented until source extraction is improved or reviewed against rendered source. |
| review-findings | 8 | Historical findings use `coverage_gap` instead of canonical `traceability_ref`. | Migrate only during reviewer pass; do not blindly rewrite ambiguous `unclear` or malformed legacy refs. |
| writer-response | 3 | Historical writer responses omit canonical blocks or affected traceability refs. | Migrate only when replaying the reviewer-writer loop for the affected scope. |

## Source Quality Warnings

These warnings are about extraction reliability, not necessarily wrong test cases.

| Finding | Path | Evidence | Classification |
| --- | --- | --- | --- |
| `source-quality-many-untitled-sections` | `fts/5 - Выдача кредита/source/ФТ_5_Выдача кредита_(все разделы)_v8_согласовано_деперсонализировано_без_рисунков.docx` | `untitled=39`, `sections=39` | Parser/source-structure risk. |
| `source-quality-no-numeric-sections` | `fts/5 - Выдача кредита/source/ФТ_5_Выдача кредита_(все разделы)_v8_согласовано_деперсонализировано_без_рисунков.docx` | `section-1`, `section-2`, `section-3`, `section-4`, `section-6`, `section-9`, `section-10`, `section-11`, `section-13`, `section-14` | Parser/source-structure risk. |
| `source-quality-oversized-blocks` | `fts/5 - Выдача кредита/source/ФТ_5_Выдача кредита_(все разделы)_v8_согласовано_деперсонализировано_без_рисунков.docx` | `section-11:13915`, `section-41:16532` | Chunking risk for agent context. |
| `source-quality-oversized-blocks` | `fts/ft-2-obshchaya-funkcionalnost/source/ФТ 2 Общая функциональность (все разделы без БП)_v4_согласовано.docx` | `2.2.1.1:29192`, `2.2.2.1:15978`, `section-19:14759` | Chunking risk for agent context. |

Recommendation: do not edit generated test artifacts to silence these warnings. The right fix is source extraction hardening or a reviewer-confirmed source parsing baseline.

## Review Findings Warnings

These warnings are about historical finding format. The old artifacts often used `coverage_gap`; the newer contract requires stable `traceability_ref`.

| Path | Evidence | Classification |
| --- | --- | --- |
| `fts/5 - Выдача кредита/work/review-loops/pdd-detalizaciya-dohodov-obshchaya-logika/round-1-findings.md` | `FINDING-001:legacy coverage_gap=ATOM-038 / GSR 106` | Likely migratable, but reviewer should confirm the exact `ATOM-*`. |
| `fts/5 - Выдача кредита/work/review-loops/pdd-detalizaciya-dohodov-obshchaya-logika/round-2-findings.md` | `FINDING-INFO-001:legacy coverage_gap=unclear` | Not safely migratable without reviewer decision. |
| `fts/5 - Выдача кредита/work/review-loops/pdd-dokumenty-klienta/round-1-findings.md` | `FINDING-001:legacy coverage_gap=ATOM-090 / GSR 90`, `FINDING-002:legacy coverage_gap=ATOM-092 / GSR 92` | Likely migratable, but reviewer should confirm the exact `ATOM-*`. |
| `fts/5 - Выдача кредита/work/review-loops/pdd-dokumenty-klienta/round-2-findings.md` | `FINDING-INFO-001:legacy coverage_gap=unclear` | Not safely migratable without reviewer decision. |
| `fts/5 - Выдача кредита/work/review-loops/pdd-ostalnye-tipy-dpd/round-1-findings.md` | `FINDING-INFO-001:legacy coverage_gap=unclear`, `FINDING-INFO-002:legacy coverage_gap=unclear` | Not safely migratable without reviewer decision. |
| `fts/5 - Выдача кредита/work/review-loops/pdd-ostalnye-tipy-dpd/round-2-findings.md` | `FINDING-INFO-001:legacy coverage_gap=unclear`, `FINDING-INFO-002:legacy coverage_gap=unclear` | Not safely migratable without reviewer decision. |
| `fts/5 - Выдача кредита/work/review-loops/podgotovka-k-sdelke/round-1-findings.md` | `FINDING-001:legacy coverage_gap=UNCLEAR-001`, `FINDING-002:legacy coverage_gap=UNCLEAR-002` | Legacy unclear ids; needs reviewer pass before canonicalization. |
| `fts/5 - Выдача кредита/work/review-loops/podgotovka-k-sdelke/round-2-findings.md` | `FINDING-003:legacy coverage_gap=UNCLEAR-001`, `FINDING-004:legacy coverage_gap=UNCLEAR-002` | Legacy unclear ids; needs reviewer pass before canonicalization. |

Recommendation: migrate only the `ATOM-*` cases when the associated traceability matrix is the accepted baseline. Leave `unclear` and `UNCLEAR-*` entries as documented legacy debt until a reviewer assigns stable refs.

## Writer Response Warnings

| Finding | Path | Evidence | Classification |
| --- | --- | --- | --- |
| `writer-response-legacy-noncanonical` | `fts/5 - Выдача кредита/work/review-loops/podgotovka-k-sdelke/round-2-writer-response.md` | no canonical response blocks | Needs rewrite only if this loop is replayed or promoted. |
| `writer-response-missing-affected-traceability-refs` | `fts/5 - Выдача кредита/work/review-loops/pdd-detalizaciya-dohodov-obshchaya-logika/round-1-writer-response.md` | `FINDING-001:ATOM-038` | Likely migratable after confirming writer response really handled `ATOM-038`. |
| `writer-response-missing-affected-traceability-refs` | `fts/5 - Выдача кредита/work/review-loops/pdd-dokumenty-klienta/round-1-writer-response.md` | `FINDING-001:ATOM-090`, `FINDING-002:ATOM-092` | Likely migratable after confirming writer response really handled both refs. |

Recommendation: do not silently add refs to writer responses unless the response text supports that claim. A wrong traceability ref is worse than a visible strict warning.

## Decision

Strict mode should remain non-blocking for the current repository baseline. Use compatible mode as the default gate and strict mode as a migration/review signal.

Reviewer sign-off strict policy is tracked separately in `references/agent/reviewer-signoff-migration-report-2026-05-25.md` because it is a new contract added after the legacy UI-prep handoffs were created.

Promote strict mode to a blocking gate only after:

1. source extraction warnings are either fixed or explicitly waived;
2. migratable `ATOM-*` review findings are canonicalized;
3. writer responses with missing affected traceability refs are confirmed and updated;
4. ambiguous `unclear` / `UNCLEAR-*` findings are reviewed or preserved as intentional legacy records.
