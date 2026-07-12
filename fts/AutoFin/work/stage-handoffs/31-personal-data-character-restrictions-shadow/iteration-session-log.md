# FT Test Case Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `agent-architecture-auditor -> ft-test-case-iteration` |
| mode | `fresh-standard-shadow-run` |
| ft_slug | `AutoFin` |
| scope_slug | `personal-data-character-restrictions-shadow` |
| status_after | `ready-for-process-optimization` |

## Inputs Read

- Package `AGENT-NOTES.md`, current source selection and parent scope/parity artifacts.
- XHTML/DOCX/PDF row evidence for `BSR 48`, `BSR 51`, `BSR 54`.
- Parent negative oracle inventory and `GAP-001`.
- Prepared compiler/package/runner contracts and relevant tests.

## Inputs Not Used

- Production test cases and generated drafts as requirement evidence.
- User-owned untracked `test-cases/4.3-application-card-client-addresses-contacts.md`.
- User-owned untracked `evals/sdk-turn-diagnostics/**`.
- DaData requirements and UI behavior outside the selected scope.

## Key Decisions

- Route character restrictions through `standard-required`, not through a forced fast profile.
- Preserve digits and non-hyphen special characters as separate calibration candidates per field.
- Keep accepted result unpromoted while GAP-001 is open.
- Route the next iteration to standard-context optimization.

## Validation

- Architecture audit before and after changes: 0 findings across 61 checks.
- 171 prepared compiler/package/runner/dispatcher/gate regression tests: pass.
- V6 historical package recompiled and validate-only routed without LLM: pass.
- Character-restriction compiler: 12 obligations, 1 gap, `standard-required`.
- V3 obligation gate: 12/12; structure: pass; semantic overlap: clean.
- Reviewer: accepted, 0 blocking findings.
- Production target existence after run: false.
- Full AutoFin validator: 0 findings in handoff `31` and character-restriction cycles; inherited remainder is 78 errors, 1270 warnings and 997 info.

## Risks And Fallbacks

- V1 and V2 stopped at configuration preflight before LLM due to command-budget floors.
- V3 writer performed one nonessential `git status` that failed under sandbox safe-directory ownership; draft and deterministic gates were already complete, so result integrity was unaffected.
- V3 used separate writer/reviewer backend session IDs and no SDK fallback.
- A guessed standalone architecture-audit script path did not exist; the canonical `scripts/run_tests.py --suite architecture` command was used and passed. No artifact was affected.
- A PowerShell reporting pipeline initially had an empty pipe position; collecting rows before `ConvertTo-Json` produced the intended size report. No artifact was affected.
- Standard V3 cost and command count are too high for steady-state use; see `iteration-summary.md`.

## Contamination Check

- Baseline was neither read as evidence nor modified.
- Old/generated TC content was not used to construct the shadow draft.
- Only ignored handoff/review-cycle artifacts and agent-layer code/tests were changed.
