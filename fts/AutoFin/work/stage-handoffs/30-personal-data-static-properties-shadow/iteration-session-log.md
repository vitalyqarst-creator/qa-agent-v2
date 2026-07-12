# FT Test Case Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `fresh-eval-run` |
| ft_slug | `AutoFin` |
| scope_slug | `personal-data-static-properties-shadow` |
| started_from | `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/workflow-state.yaml` |
| status_after | `ready-for-next-stage` |

## Inputs Read

- `AGENT-NOTES.md` — mandatory package context.
- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md` — current FT family and XHTML availability.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md` — parent 4.3 boundary.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md` — DOCX/XHTML/PDF parity.
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md` and `final-bsr-evidence.json` — exact rows and BSR anchors.
- Prepared compiler and runner contracts — profile and immutable execution behavior.
- Previous `writer-r2-draft.md` — post-run structural comparison only, after independent generation.

## Inputs Not Used

- `test-cases/4.3-application-card-client-addresses-contacts.md` — untracked user draft; outside selected personal-data projection and not read.
- `test-cases/14-application-card-client-personal-data.md` — production baseline; not evidence and not modified.
- `evals/sdk-turn-diagnostics/**` — user-owned untracked diagnostics; not read or modified.
- `AutoFinPreFinal.*` and neighboring FT packages — stale or outside current source boundary.

## Key Decisions

- Selected 15 static obligations and excluded format, integration and dependency behavior; see `agent-decision-log.md`.
- Preserved the first blocked cycle, added explicit synthetic fixtures, and used a new v2 cycle.
- Kept promotion disabled and recorded semantic overlap as follow-up rather than claiming production readiness.

## Risks And Fallbacks

- First live cycle consumed 25 091 tokens before exposing missing fixtures; compiler preflight does not currently catch this class.
- Reviewer acceptance does not prove absence of redundant case bodies; three overlapping pairs remain.

## Validation

- Prepared compiler v2: built, 15 obligations, 0 gaps, `simple-field-property`.
- Runner validate-only: `prepared-fast`, writer read-only, command budget 0, final absent.
- V2 obligation gate: 15/15, pass.
- V2 structure validator: pass, 0 findings.
- V2 reviewer: accepted, 0 blocking findings.
- Title comparison: new 15/15 unique; old full draft 39/47 unique, 7 duplicate groups.
- Production target existence check after cycle: false.
- 36 targeted compiler/dispatcher unit tests: pass.
- Full AutoFin strict/audit validator: 0 findings scoped to handoff `30` and shadow cycles; inherited remainder is 78 errors, 2707 warnings, 131 info.

## Contamination Check

- Generated or production test cases were not used as requirement evidence.
- Old draft was accessed only after the v2 draft and reviewer decision existed, for count/title comparison.
- No production target, baseline, user untracked draft or SDK diagnostics were written.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Confirmed current FT and parent 4.3 boundary | XHTML available; parity passed | handoffs `20`, `29` |
| 2 | Compiled 15-obligation package | Fast profile selected | prepared package v1 |
| 3 | Ran immutable exec cycle | Writer blocked on missing concrete fixtures | first cycle state |
| 4 | Added source-compatible synthetic fixture and compiled new package | Fast profile retained | prepared package v2 |
| 5 | Ran separate writer/reviewer exec sessions | Accepted-not-promoted | v2 cycle state and findings |
| 6 | Performed post-run comparison | No duplicate titles in new draft; overlap finding retained | `iteration-summary.md` |
| 7 | Corrected one failed combined patch | Retried as file-scoped patches; no partial write remained | `workflow-state.yaml`; this log |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Source and contamination boundary | pass | current FT4 artifacts only before generation | none |
| Compiler routing | pass | no unsupported dimensions | none |
| Concrete fixture completeness | fail then pass | v1 blocked; v2 uses `Тест` | add compiler preflight |
| Obligation coverage | pass | 15/15 gate | none |
| Unique titles | pass | 15 unique titles | retain validator gate |
| Semantic overlap | needs-follow-up | three pairs share action/oracle | add diagnostic/policy |
| Production isolation | pass | final target absent | none |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| compiler input Markdown set | bounded eval artifacts, max 15 rows | targeted `apply_patch` | `yes` | `n/a` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | combined patch referenced lines from the wrong target file | one multi-file `apply_patch` | split into file-scoped `apply_patch` calls | `n/a` | `n/a` | `none; failed patch made no partial write` | validate both corrected files |

## Handoff Notes For Next Session

- Implement a compiler failure before live exec when input-based plans lack concrete fixtures.
- Add overlap detection based on normalized steps and final expected result, but keep it diagnostic until legitimate multi-obligation cases are classified.
- Do not promote the shadow draft or treat its 15 obligations as full coverage of section 4.3.
