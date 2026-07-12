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
- `test_case_agent/review_cycle/prepared_compiler.py`, `prepared_package.py`, exec runner and regression tests — process-gate extension points.
- V3–V6 cycle states, metrics, diagnostics and reviewer findings — second optimization iteration evidence.
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
- Added fixture preflight, overlap diagnostic and explicit multi-obligation grouping; retained full OBL/ATOM traceability.
- Accepted V6 only after deterministic overlap returned clean and reviewer independently accepted 12 TC / 15 obligations.

## Risks And Fallbacks

- Historical V1 fixture overhead remains evidence, but the new compiler preflight now catches this class before live exec.
- V3–V5 consumed development-run tokens while calibrating normalization, grouping and contiguous numbering; future steady-state uses the V6 path.

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
- 138 package/compiler/runner/dispatcher/obligation-gate regression tests after grouping: pass.
- Architecture audit after changes: 0 findings.
- V4 overlap diagnostic: 3/3 groups detected; reviewer returned `changes-required`.
- V5 structural validator: correctly blocked 12 non-contiguous TC ids before reviewer.
- V6: 12 unique contiguous TC, 15/15 obligations, overlap diagnostic clean, reviewer accepted, production target absent.

## Contamination Check

- Generated or production test cases were not used as requirement evidence.
- Old draft was accessed only after the v2 draft and reviewer decision existed, for count/title comparison.
- No production target, baseline, user untracked draft or SDK diagnostics were written.
- V3–V6 used the same prepared source scope; old/generated drafts were not requirement evidence.

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
| 8 | Added fixture preflight and overlap diagnostic | 108 targeted tests passed; architecture audit clean | compiler/runner/tests/references |
| 9 | Ran V3 and V4 | Reviewer and deterministic diagnostic confirmed three overlap groups | V3/V4 findings and diagnostic |
| 10 | Added optional planned TC grouping | 15 obligations compiled into 12 planned TC | package v5 compiler output |
| 11 | Ran V5 | Structural gate rejected non-contiguous ids | V5 validator |
| 12 | Renumbered plan and ran V6 | Accepted-not-promoted; 12 TC, 15/15 obligations, 0 overlap | V6 cycle state and findings |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Source and contamination boundary | pass | current FT4 artifacts only before generation | none |
| Compiler routing | pass | no unsupported dimensions | none |
| Concrete fixture completeness | pass | `input-fixture-required` regression and V6 compiler pass | none |
| Obligation coverage | pass | 15/15 gate | none |
| Unique titles and IDs | pass | V6 has 12 unique contiguous titles/IDs | retain validator gate |
| Semantic overlap | pass | V4 detects 3 groups; V6 clean after grouping | none |
| Production isolation | pass | final target absent | none |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| compiler input Markdown set | bounded eval artifacts, max 15 rows | targeted `apply_patch` | `yes` | `n/a` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | combined patch referenced lines from the wrong target file | one multi-file `apply_patch` | split into file-scoped `apply_patch` calls | `n/a` | `n/a` | `none; failed patch made no partial write` | validate both corrected files |
| `TF-002` | current multi-file patch mixed test content into runner-file context | one combined `apply_patch` | split runner and test patches by file | `n/a` | `n/a` | `none; failed patch made no partial write` | targeted overlap tests passed |
| `TF-003` | PowerShell pipeline parser rejected an empty pipe position | inline reporting pipeline | collect rows into an array before `ConvertTo-Json` | `n/a` | `n/a` | `none; reporting-only command` | contiguous ID inventory confirmed |

## Handoff Notes For Next Session

- Next scope should cover only character restrictions `BSR 48`, `BSR 51`, `BSR 54` through `standard-required`.
- Preserve UI-calibration gaps for unspecified rejection mechanics; do not infer exact messages/highlights/filtering.
- Do not promote the shadow draft or treat its 15 obligations as full coverage of section 4.3.
